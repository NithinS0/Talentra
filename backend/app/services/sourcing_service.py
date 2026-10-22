"""Sourcing & Consultant Requests Domain Service.

Implements M08 Sourcing & External Consultants business logic:
- FR-0112: Create sourcing request
- FR-0113: Consultant openness enforcement
- FR-0114: Consultant accept decision
- FR-0115: Employer decline consultant
- FR-0116: Sourcing shortlist references candidate
- FR-0117: Blocked candidate outreach
- FR-0118: Bulk outreach batch count
- FR-0119: Outreach delivery status
- FR-0120: Recruiter company assignment
- FR-0121: Consultant candidate privacy
- FR-0122: Sourcing request cancellation
- FR-0123: Duplicate consultant assignment
- FR-0205: Bulk outreach suppression after consent withdrawal
"""

import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from app.models.user import User, Role, UserRoleAssignment
from app.models.organisation import Organisation, OrganisationRecruiterMapping, AccountAdminAssignment
from app.models.job import JobRequirement
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.application import BlockListEntry
from app.models.admin import ConsentRecord, AuditEvent
from app.models.sourcing import (
    SourcingRequest,
    SourcingRequestStatusHistory,
    ConsultantRequestDecision,
    ConsultantRequestAssignmentHistory,
    CandidateSourcingShortlist,
    OutreachBatch,
    OutreachRecipient,
    CandidateContactAttempt,
    ConsultantProfile,
)
from app.services.admin_service import record_audit_event, sanitize_metadata
from app.schemas.sourcing import (
    SourcingRequestCreate,
    SourcingRequestDecision,
    SourcingRequestCancel,
    SourcingRequestResponse,
    SourcingRequestListResponse,
    CandidateShortlistCreate,
    CandidateShortlistResponse,
    CandidateShortlistListResponse,
    OutreachBatchCreate,
    OutreachRecipientResponse,
    OutreachBatchResponse,
    OutreachDeliveryCallback,
    ConsultantCandidateProfileResponse,
)

# Status code mappings
SOURCING_STATUS_MAP = {1: "PENDING", 2: "ACCEPTED", 3: "DECLINED", 4: "CANCELLED", 5: "COMPLETED"}
DELIVERY_STATUS_MAP = {1: "PENDING", 2: "DELIVERED", 3: "FAILED", 4: "SUPPRESSED"}
SHORTLIST_STATUS_MAP = {1: "SHORTLISTED", 2: "CONTACTED", 3: "SCREENED", 4: "REJECTED"}


class SourcingServiceError(Exception):
    """Base exception for sourcing service errors."""
    pass


# -------------------------------------------------------------------------
# Authorization & Scope Helpers
# -------------------------------------------------------------------------

def is_super_or_platform_admin(db: Session, user: User) -> bool:
    """Check if user has platform SUPER_ADMIN or ADMIN role."""
    assignment = (
        db.query(UserRoleAssignment)
        .join(Role, UserRoleAssignment.role_id == Role.id)
        .filter(
            UserRoleAssignment.user_id == user.id,
            Role.role_code.in_(["SUPER_ADMIN", "ADMIN"]),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    return assignment is not None


def has_employer_or_admin_access_to_org(db: Session, user: User, organisation_id: int) -> bool:
    """Verify that user is an authorized employer or account admin for the organisation."""
    if is_super_or_platform_admin(db, user):
        return True

    # Check organisation creator / employer
    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if org and org.created_by == user.id:
        return True

    # Check role assignment scoped to this organisation
    emp_role = (
        db.query(UserRoleAssignment)
        .join(Role, UserRoleAssignment.role_id == Role.id)
        .filter(
            UserRoleAssignment.user_id == user.id,
            Role.role_code.in_(["EMPLOYER", "ACCOUNT_ADMIN"]),
            UserRoleAssignment.organisation_id == organisation_id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    return emp_role is not None


def verify_recruiter_effective_assignment(db: Session, user: User, organisation_id: int) -> bool:
    """FR-0120: Verify that recruiter has an active, non-expired mapping to the job-owning organisation."""
    if is_super_or_platform_admin(db, user):
        return True

    now = datetime.now(timezone.utc)
    mapping = (
        db.query(OrganisationRecruiterMapping)
        .filter(
            OrganisationRecruiterMapping.recruiter_user_id == user.id,
            OrganisationRecruiterMapping.organisation_id == organisation_id,
            OrganisationRecruiterMapping.deleted_at.is_(None),
            OrganisationRecruiterMapping.valid_from <= now,
            or_(
                OrganisationRecruiterMapping.valid_until.is_(None),
                OrganisationRecruiterMapping.valid_until >= now,
            ),
        )
        .first()
    )
    return mapping is not None


# -------------------------------------------------------------------------
# Sourcing Requests Workflows (FR-0112 to FR-0115, FR-0122, FR-0123)
# -------------------------------------------------------------------------

def create_sourcing_request(
    db: Session,
    user: User,
    request: SourcingRequestCreate,
) -> SourcingRequestResponse:
    """FR-0112 & FR-0123: Create a candidate sourcing request with duplicate assignment prevention."""
    # 1. Resolve target job requirement
    job = (
        db.query(JobRequirement)
        .filter(JobRequirement.id == request.job_requirement_id, JobRequirement.deleted_at.is_(None))
        .first()
    )
    if not job:
        raise ValueError(f"Job requirement with ID {request.job_requirement_id} not found.")

    # 2. Authorization check: Requester must be authorized for this job's organisation
    if not has_employer_or_admin_access_to_org(db, user, job.organisation_id):
        # Also check if recruiter is mapped
        if not verify_recruiter_effective_assignment(db, user, job.organisation_id):
            raise PermissionError(f"Forbidden: You are not authorized to request sourcing for organisation {job.organisation_id}.")

    # 3. Duplicate consultant assignment check (FR-0123)
    if request.consultant_user_id is not None:
        existing_active = (
            db.query(SourcingRequest)
            .filter(
                SourcingRequest.job_requirement_id == request.job_requirement_id,
                SourcingRequest.consultant_user_id == request.consultant_user_id,
                SourcingRequest.status_code_id.in_([1, 2]),  # PENDING or ACCEPTED
                SourcingRequest.deleted_at.is_(None),
            )
            .first()
        )
        if existing_active:
            raise ValueError(
                f"An active sourcing request for job {request.job_requirement_id} and consultant {request.consultant_user_id} already exists."
            )

    now = datetime.now(timezone.utc)
    sourcing_req = SourcingRequest(
        job_requirement_id=job.id,
        requester_user_id=user.id,
        consultant_user_id=request.consultant_user_id,
        status_code_id=1,  # PENDING / REQUESTED
        open_to_consultants_snapshot=job.open_to_consultants,
        requested_at=now,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(sourcing_req)
    db.flush()

    # Record status history
    db.add(
        SourcingRequestStatusHistory(
            sourcing_request_id=sourcing_req.id,
            event_code_id=1,  # REQUESTED
            actor_user_id=user.id,
            occurred_at=now,
            metadata_redacted={
                "action": "SOURCING_REQUESTED",
                "consultant_user_id": request.consultant_user_id,
                "open_to_consultants": job.open_to_consultants,
            },
        )
    )

    # Record audit event
    record_audit_event(
        db=db,
        actor_user_id=user.id,
        action_code="SOURCING_REQUEST_CREATED",
        resource_type="SOURCING_REQUEST",
        resource_id=str(sourcing_req.id),
        metadata={"job_requirement_id": job.id, "consultant_user_id": request.consultant_user_id},
    )

    db.commit()
    db.refresh(sourcing_req)
    return _build_sourcing_request_response(db, sourcing_req)


def consultant_respond_to_request(
    db: Session,
    consultant_user: User,
    request_id: int,
    decision_payload: SourcingRequestDecision,
) -> SourcingRequestResponse:
    """FR-0113 & FR-0114: Consultant accepts or declines sourcing request with openness enforcement."""
    sourcing_req = (
        db.query(SourcingRequest)
        .filter(SourcingRequest.id == request_id, SourcingRequest.deleted_at.is_(None))
        .first()
    )
    if not sourcing_req:
        raise ValueError(f"Sourcing request with ID {request_id} not found.")

    # Authorization: Must be the designated consultant or platform admin
    if sourcing_req.consultant_user_id and sourcing_req.consultant_user_id != consultant_user.id:
        if not is_super_or_platform_admin(db, consultant_user):
            raise PermissionError("Forbidden: You are not the designated consultant for this request.")

    # FR-0113: Consultant openness enforcement
    job = sourcing_req.job_requirement
    if not job or not job.open_to_consultants:
        raise PermissionError("Forbidden: Job requirement is closed to external consultants.")

    # Status validation: Can only respond to PENDING requests
    if sourcing_req.status_code_id != 1:
        raise ValueError(
            f"Cannot respond to request in '{SOURCING_STATUS_MAP.get(sourcing_req.status_code_id)}' status."
        )

    now = datetime.now(timezone.utc)
    new_status = 2 if decision_payload.decision == "ACCEPT" else 3  # 2=ACCEPTED, 3=DECLINED
    event_code = 2 if decision_payload.decision == "ACCEPT" else 3

    sourcing_req.status_code_id = new_status
    sourcing_req.responded_at = now
    sourcing_req.updated_at = now
    sourcing_req.updated_by = consultant_user.id
    if sourcing_req.consultant_user_id is None:
        sourcing_req.consultant_user_id = consultant_user.id

    # Record status history
    db.add(
        SourcingRequestStatusHistory(
            sourcing_request_id=sourcing_req.id,
            event_code_id=event_code,
            actor_user_id=consultant_user.id,
            occurred_at=now,
            metadata_redacted={"decision": decision_payload.decision, "reason": decision_payload.reason},
        )
    )

    # Record consultant request assignment history
    db.add(
        ConsultantRequestAssignmentHistory(
            event_code_id=event_code,
            actor_user_id=consultant_user.id,
            occurred_at=now,
            metadata_redacted={
                "sourcing_request_id": sourcing_req.id,
                "job_requirement_id": sourcing_req.job_requirement_id,
                "decision": decision_payload.decision,
            },
        )
    )

    record_audit_event(
        db=db,
        actor_user_id=consultant_user.id,
        action_code=f"CONSULTANT_REQUEST_{decision_payload.decision}ED",
        resource_type="SOURCING_REQUEST",
        resource_id=str(sourcing_req.id),
        metadata={"decision": decision_payload.decision, "reason": decision_payload.reason},
    )

    db.commit()
    db.refresh(sourcing_req)
    return _build_sourcing_request_response(db, sourcing_req)


def employer_decline_consultant(
    db: Session,
    employer_user: User,
    request_id: int,
    reason: Optional[str] = None,
) -> SourcingRequestResponse:
    """FR-0115: Employer declines consultant request; strictly rejects cross-company unauthorized actors."""
    sourcing_req = (
        db.query(SourcingRequest)
        .filter(SourcingRequest.id == request_id, SourcingRequest.deleted_at.is_(None))
        .first()
    )
    if not sourcing_req:
        raise ValueError(f"Sourcing request with ID {request_id} not found.")

    job = sourcing_req.job_requirement
    if not job:
        raise ValueError("Associated job requirement not found.")

    # Strict company boundary check (FR-0115)
    if not has_employer_or_admin_access_to_org(db, employer_user, job.organisation_id):
        raise PermissionError(
            f"Forbidden: User {employer_user.id} does not have authority to decline requests for organisation {job.organisation_id}."
        )

    now = datetime.now(timezone.utc)
    sourcing_req.status_code_id = 3  # DECLINED
    sourcing_req.responded_at = now
    sourcing_req.updated_at = now
    sourcing_req.updated_by = employer_user.id

    db.add(
        SourcingRequestStatusHistory(
            sourcing_request_id=sourcing_req.id,
            event_code_id=3,  # DECLINED
            actor_user_id=employer_user.id,
            occurred_at=now,
            metadata_redacted={"action": "EMPLOYER_DECLINED_CONSULTANT", "reason": reason},
        )
    )

    record_audit_event(
        db=db,
        actor_user_id=employer_user.id,
        action_code="SOURCING_REQUEST_DECLINED_BY_EMPLOYER",
        resource_type="SOURCING_REQUEST",
        resource_id=str(sourcing_req.id),
        metadata={"reason": reason},
    )

    db.commit()
    db.refresh(sourcing_req)
    return _build_sourcing_request_response(db, sourcing_req)


def cancel_sourcing_request(
    db: Session,
    user: User,
    request_id: int,
    cancel_payload: SourcingRequestCancel,
) -> SourcingRequestResponse:
    """FR-0122: Cancel sourcing request following valid lifecycle without erasing history."""
    sourcing_req = (
        db.query(SourcingRequest)
        .filter(SourcingRequest.id == request_id, SourcingRequest.deleted_at.is_(None))
        .first()
    )
    if not sourcing_req:
        raise ValueError(f"Sourcing request with ID {request_id} not found.")

    job = sourcing_req.job_requirement
    if not job:
        raise ValueError("Associated job requirement not found.")

    if not has_employer_or_admin_access_to_org(db, user, job.organisation_id):
        raise PermissionError("Forbidden: Unauthorized to cancel this sourcing request.")

    # Status validation: Can only cancel active / pending / accepted requests
    if sourcing_req.status_code_id in [4, 5]:  # Already CANCELLED or COMPLETED
        raise ValueError(
            f"Cannot cancel request in '{SOURCING_STATUS_MAP.get(sourcing_req.status_code_id)}' status."
        )

    now = datetime.now(timezone.utc)
    sourcing_req.status_code_id = 4  # CANCELLED
    sourcing_req.updated_at = now
    sourcing_req.updated_by = user.id

    db.add(
        SourcingRequestStatusHistory(
            sourcing_request_id=sourcing_req.id,
            event_code_id=4,  # CANCELLED
            actor_user_id=user.id,
            occurred_at=now,
            metadata_redacted={"reason": cancel_payload.reason},
        )
    )

    record_audit_event(
        db=db,
        actor_user_id=user.id,
        action_code="SOURCING_REQUEST_CANCELLED",
        resource_type="SOURCING_REQUEST",
        resource_id=str(sourcing_req.id),
        metadata={"reason": cancel_payload.reason},
    )

    db.commit()
    db.refresh(sourcing_req)
    return _build_sourcing_request_response(db, sourcing_req)


def list_sourcing_requests(
    db: Session,
    user: User,
    job_requirement_id: Optional[int] = None,
    organisation_id: Optional[int] = None,
    status_code_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> SourcingRequestListResponse:
    """List sourcing requests scoped to the authenticated user's permissions."""
    query = db.query(SourcingRequest).filter(SourcingRequest.deleted_at.is_(None))

    if not is_super_or_platform_admin(db, user):
        # Scoped to requests where user is requester, consultant, or belongs to organisation
        query = query.join(SourcingRequest.job_requirement).filter(
            or_(
                SourcingRequest.requester_user_id == user.id,
                SourcingRequest.consultant_user_id == user.id,
                JobRequirement.created_by_user_id == user.id,
            )
        )

    if job_requirement_id:
        query = query.filter(SourcingRequest.job_requirement_id == job_requirement_id)
    if status_code_id:
        query = query.filter(SourcingRequest.status_code_id == status_code_id)
    if organisation_id:
        query = query.join(SourcingRequest.job_requirement).filter(JobRequirement.organisation_id == organisation_id)

    total = query.count()
    items_raw = (
        query.order_by(desc(SourcingRequest.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_build_sourcing_request_response(db, item) for item in items_raw]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return SourcingRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# -------------------------------------------------------------------------
# Candidate Shortlist Workflows (FR-0116)
# -------------------------------------------------------------------------

def add_candidate_to_shortlist(
    db: Session,
    user: User,
    payload: CandidateShortlistCreate,
) -> CandidateShortlistResponse:
    """FR-0116: Add a candidate to the sourcing shortlist; rejects orphan references."""
    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == payload.candidate_profile_id, CandidateProfile.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise ValueError(f"Candidate profile with ID {payload.candidate_profile_id} not found.")

    if payload.sourcing_request_id:
        sourcing_req = (
            db.query(SourcingRequest)
            .filter(SourcingRequest.id == payload.sourcing_request_id, SourcingRequest.deleted_at.is_(None))
            .first()
        )
        if not sourcing_req:
            raise ValueError(f"Sourcing request with ID {payload.sourcing_request_id} not found.")

    now = datetime.now(timezone.utc)
    shortlist_item = CandidateSourcingShortlist(
        candidate_profile_id=candidate.id,
        user_id=user.id,
        status_code_id=1,  # SHORTLISTED
        title=payload.title,
        description=payload.description,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(shortlist_item)
    db.commit()
    db.refresh(shortlist_item)

    return _build_shortlist_response(db, shortlist_item)


def list_candidate_shortlists(
    db: Session,
    user: User,
    status_code_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> CandidateShortlistListResponse:
    """List candidate shortlists created by the current user or accessible to admin."""
    query = db.query(CandidateSourcingShortlist).filter(CandidateSourcingShortlist.deleted_at.is_(None))

    if not is_super_or_platform_admin(db, user):
        query = query.filter(CandidateSourcingShortlist.user_id == user.id)

    if status_code_id:
        query = query.filter(CandidateSourcingShortlist.status_code_id == status_code_id)

    total = query.count()
    items_raw = (
        query.order_by(desc(CandidateSourcingShortlist.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_build_shortlist_response(db, item) for item in items_raw]
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return CandidateShortlistListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# -------------------------------------------------------------------------
# Bulk Outreach Campaigns & Delivery (FR-0117, FR-0118, FR-0119, FR-0120, FR-0205)
# -------------------------------------------------------------------------

def create_outreach_batch(
    db: Session,
    user: User,
    payload: OutreachBatchCreate,
) -> OutreachBatchResponse:
    """Launch bulk candidate outreach campaign with recruiter assignment, blocklist, and consent suppression."""
    # 1. Recruiter company assignment verification (FR-0120)
    if not verify_recruiter_effective_assignment(db, user, payload.organisation_id):
        if not has_employer_or_admin_access_to_org(db, user, payload.organisation_id):
            raise PermissionError(
                f"Forbidden: User {user.id} lacks effective recruiter or employer assignment to organisation {payload.organisation_id}."
            )

    # 2. Validate job requirement reference if provided
    if payload.job_requirement_id:
        job = db.query(JobRequirement).filter(
            JobRequirement.id == payload.job_requirement_id,
            JobRequirement.organisation_id == payload.organisation_id,
            JobRequirement.deleted_at.is_(None),
        ).first()
        if not job:
            raise ValueError(f"Job requirement {payload.job_requirement_id} not found under organisation {payload.organisation_id}.")

    # 3. Deduplicate candidate profile IDs within batch scope (FR-0118)
    unique_candidate_ids = list(dict.fromkeys(payload.candidate_profile_ids))

    now = datetime.now(timezone.utc)
    batch = OutreachBatch(
        organisation_id=payload.organisation_id,
        created_by_user_id=user.id,
        job_requirement_id=payload.job_requirement_id,
        status_code_id=2,  # PROCESSING
        recipient_count=len(unique_candidate_ids),
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(batch)
    db.flush()

    # 4. Process each candidate for blocking (FR-0117) and consent withdrawal (FR-0205)
    recipients_out = []
    suppressed_count = 0

    for cand_id in unique_candidate_ids:
        candidate = db.query(CandidateProfile).filter(
            CandidateProfile.id == cand_id,
            CandidateProfile.deleted_at.is_(None),
        ).first()
        if not candidate:
            continue

        # Check blocklist for this organisation (FR-0117)
        is_blocked = (
            db.query(BlockListEntry)
            .filter(
                BlockListEntry.blocked_organisation_id == payload.organisation_id,
                BlockListEntry.blocked_user_id == candidate.user_id,
                BlockListEntry.revoked_at.is_(None),
                BlockListEntry.deleted_at.is_(None),
            )
            .first()
            is not None
        )

        # Check consent withdrawal (FR-0205)
        consent_withdrawn = (
            db.query(ConsentRecord)
            .filter(
                ConsentRecord.user_id == candidate.user_id,
                or_(
                    ConsentRecord.withdrawn_at.is_not(None),
                    ConsentRecord.granted.is_(False),
                ),
            )
            .first()
            is not None
        )

        idempotency_key = f"outreach-{batch.id}-{candidate.id}-{uuid.uuid4().hex[:10]}"

        if is_blocked or consent_withdrawn:
            # Recipient is suppressed before dispatch; no outbound send occurs (FR-0117, FR-0205)
            status_code = 4  # SUPPRESSED
            suppressed_count += 1
        else:
            status_code = 1  # PENDING for delivery

        recipient = OutreachRecipient(
            outreach_batch_id=batch.id,
            candidate_profile_id=candidate.id,
            delivery_status_code_id=status_code,
            provider_message_reference=None,
            idempotency_key=idempotency_key,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(recipient)
        db.flush()

        recipients_out.append(
            OutreachRecipientResponse(
                id=recipient.id,
                outreach_batch_id=batch.id,
                candidate_profile_id=candidate.id,
                delivery_status_code_id=status_code,
                delivery_status=DELIVERY_STATUS_MAP.get(status_code, "UNKNOWN"),
                provider_message_reference=None,
                idempotency_key=idempotency_key,
                created_at=now,
            )
        )

    batch.status_code_id = 3  # SENT / COMPLETED
    db.commit()
    db.refresh(batch)

    return OutreachBatchResponse(
        id=batch.id,
        organisation_id=batch.organisation_id,
        job_requirement_id=batch.job_requirement_id,
        created_by_user_id=batch.created_by_user_id,
        status_code_id=batch.status_code_id,
        status="SENT",
        recipient_count=len(recipients_out),
        suppressed_count=suppressed_count,
        recipients=recipients_out,
        created_at=batch.created_at,
    )


def process_delivery_callback(
    db: Session,
    callback: OutreachDeliveryCallback,
) -> OutreachRecipientResponse:
    """FR-0119: Process provider delivery callback idempotently without duplicating events."""
    recipient = (
        db.query(OutreachRecipient)
        .filter(OutreachRecipient.idempotency_key == callback.idempotency_key)
        .first()
    )
    if not recipient:
        raise ValueError(f"Outreach recipient with idempotency key '{callback.idempotency_key}' not found.")

    # Idempotency check: If already marked DELIVERED with matching reference, return existing
    if (
        recipient.delivery_status_code_id == 2
        and recipient.provider_message_reference == callback.provider_message_reference
    ):
        return OutreachRecipientResponse(
            id=recipient.id,
            outreach_batch_id=recipient.outreach_batch_id,
            candidate_profile_id=recipient.candidate_profile_id,
            delivery_status_code_id=recipient.delivery_status_code_id,
            delivery_status=DELIVERY_STATUS_MAP.get(recipient.delivery_status_code_id, "DELIVERED"),
            provider_message_reference=recipient.provider_message_reference,
            idempotency_key=recipient.idempotency_key,
            created_at=recipient.created_at,
        )

    now = datetime.now(timezone.utc)
    new_status = 2 if callback.status == "DELIVERED" else 3  # 2=DELIVERED, 3=FAILED
    recipient.delivery_status_code_id = new_status
    recipient.provider_message_reference = callback.provider_message_reference
    recipient.updated_at = now

    db.commit()
    db.refresh(recipient)

    return OutreachRecipientResponse(
        id=recipient.id,
        outreach_batch_id=recipient.outreach_batch_id,
        candidate_profile_id=recipient.candidate_profile_id,
        delivery_status_code_id=recipient.delivery_status_code_id,
        delivery_status=DELIVERY_STATUS_MAP.get(recipient.delivery_status_code_id, "UNKNOWN"),
        provider_message_reference=recipient.provider_message_reference,
        idempotency_key=recipient.idempotency_key,
        created_at=recipient.created_at,
    )


# -------------------------------------------------------------------------
# Consultant Candidate Privacy (FR-0121)
# -------------------------------------------------------------------------

def get_candidate_for_consultant(
    db: Session,
    consultant_user: User,
    candidate_profile_id: int,
) -> ConsultantCandidateProfileResponse:
    """FR-0121: Return privacy-preserving candidate profile with masked contact details and block enforcement."""
    candidate = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.id == candidate_profile_id, CandidateProfile.deleted_at.is_(None))
        .first()
    )
    if not candidate:
        raise ValueError(f"Candidate profile with ID {candidate_profile_id} not found.")

    # Check if candidate blocked consultant's user ID
    is_blocked = (
        db.query(BlockListEntry)
        .filter(
            BlockListEntry.blocked_user_id == candidate.user_id,
            BlockListEntry.blocker_user_id == consultant_user.id,
            BlockListEntry.revoked_at.is_(None),
            BlockListEntry.deleted_at.is_(None),
        )
        .first()
        is not None
    )
    if is_blocked:
        raise PermissionError("Access forbidden: Candidate privacy settings restrict access.")

    # Retrieve contact and apply privacy masking
    contact = db.query(CandidateContact).filter(CandidateContact.candidate_profile_id == candidate.id).first()
    masked_email = None
    masked_phone = None

    if contact:
        if contact.email_address and "@" in contact.email_address:
            local, domain = contact.email_address.split("@", 1)
            masked_local = local[0] + "***" + (local[-1] if len(local) > 1 else "")
            masked_email = f"{masked_local}@{domain}"
        if contact.phone_e164:
            masked_phone = "******" + contact.phone_e164[-4:]

    return ConsultantCandidateProfileResponse(
        id=candidate.id,
        actor_id=candidate.actor_id,
        first_name=candidate.first_name,
        last_name=candidate.last_name[:1] + "." if candidate.last_name else "",
        headline=candidate.headline,
        summary=candidate.summary,
        email_address_masked=masked_email,
        phone_masked=masked_phone,
        completion_score=candidate.completion_score,
        is_blocked=False,
    )


# -------------------------------------------------------------------------
# Response Builders
# -------------------------------------------------------------------------

def _build_sourcing_request_response(db: Session, req: SourcingRequest) -> SourcingRequestResponse:
    job = req.job_requirement
    org_name = job.organisation.display_name if job and job.organisation else "Unknown"
    consultant_name = req.consultant.display_name if req.consultant else None

    return SourcingRequestResponse(
        id=req.id,
        job_requirement_id=req.job_requirement_id,
        job_title=job.title if job else "Unknown",
        organisation_id=job.organisation_id if job else 0,
        organisation_name=org_name,
        requester_user_id=req.requester_user_id,
        consultant_user_id=req.consultant_user_id,
        consultant_name=consultant_name,
        status_code_id=req.status_code_id,
        status=SOURCING_STATUS_MAP.get(req.status_code_id, "UNKNOWN"),
        open_to_consultants_snapshot=req.open_to_consultants_snapshot,
        requested_at=req.requested_at,
        responded_at=req.responded_at,
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


def _build_shortlist_response(db: Session, item: CandidateSourcingShortlist) -> CandidateShortlistResponse:
    cand = item.candidate_profile
    cand_name = f"{cand.first_name} {cand.last_name}" if cand else None
    actor_id = cand.actor_id if cand else None

    return CandidateShortlistResponse(
        id=item.id,
        candidate_profile_id=item.candidate_profile_id or 0,
        candidate_actor_id=actor_id,
        candidate_name=cand_name,
        user_id=item.user_id or 0,
        status_code_id=item.status_code_id,
        status=SHORTLIST_STATUS_MAP.get(item.status_code_id, "UNKNOWN"),
        title=item.title,
        description=item.description,
        created_at=item.created_at,
    )
