"""Gig Marketplace Domain Service (Module M06).

Implements business logic, validation, and security enforcement for:
- FR-0084: Gig worker profile separate from permanent candidates
- FR-0085: Gig request pricing decimal-safety and currency code
- FR-0086: Gig work date window (ends_at >= starts_at)
- FR-0087: Gig application direction (worker applies, requester decides)
- FR-0088: Gig application decision (only requester / authorized delegate)
- FR-0089: Overlapping worker assignments prevention under concurrency
- FR-0090: Gig availability conflict detection
- FR-0091: Gig handoff external reference creation
- FR-0092: Gig earnings reconciliation and idempotent event handling
- FR-0093: Favourite and blacklist exclusivity
- FR-0094: Completed gig rating scale (1-5) and completion check
- FR-0095: Gig blacklist privacy protection
- FR-0096: External provider outage handling without false progression
- FR-0097: Gig cancellation lifecycle preservation
- FR-0203: Money amount uses companion ISO currency code
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.user import User, Role, UserRoleAssignment
from app.models.organisation import Organisation, OrganisationRecruiterMapping
from app.models.admin import AuditEvent
from app.models.gig import (
    GigWorkerProfile,
    GigRequest,
    GigApplication,
    GigAssignment,
    GigHandoffReference,
    GigEarningsReconciliation,
    GigWorkerListEntry,
    GigRating,
    GigWorkerAvailability,
    GigRequestStatusHistory,
    GigApplicationStatusHistory,
    GigAssignmentStatusHistory,
    GigWorkerFavouriteHistory,
)
from app.schemas.gig import (
    GigWorkerProfileCreate,
    GigWorkerProfileUpdate,
    GigWorkerProfileResponse,
    GigRequestCreate,
    GigRequestCancel,
    GigRequestResponse,
    GigRequestListResponse,
    GigApplicationCreate,
    GigApplicationDecision,
    GigApplicationResponse,
    GigApplicationListResponse,
    GigAssignmentResponse,
    GigAssignmentListResponse,
    GigWorkerAvailabilityCreate,
    GigWorkerAvailabilityResponse,
    GigEarningsEventCreate,
    GigEarningsResponse,
    GigWorkerListEntryCreate,
    GigWorkerListEntryResponse,
    GigRatingCreate,
    GigRatingResponse,
)

# Status code mappings
GIG_AVAILABILITY_MAP = {1: "AVAILABLE", 2: "BUSY", 3: "UNAVAILABLE"}
GIG_PRICING_TYPE_MAP = {1: "FIXED", 2: "HOURLY"}
GIG_REQUEST_STATUS_MAP = {1: "DRAFT", 2: "OPEN", 3: "IN_PROGRESS", 4: "COMPLETED", 5: "CANCELLED"}
GIG_APPLICATION_STATUS_MAP = {1: "APPLIED", 2: "ACCEPTED", 3: "REJECTED", 4: "WITHDRAWN"}
GIG_ASSIGNMENT_STATUS_MAP = {1: "CONFIRMED", 2: "ACTIVE", 3: "COMPLETED", 4: "CANCELLED"}
GIG_HANDOFF_STATUS_MAP = {1: "PENDING", 2: "SYNCHRONIZED", 3: "FAILED_RETRYABLE"}
GIG_EARNINGS_STATUS_MAP = {1: "ESTIMATED", 2: "RECONCILED", 3: "PAID"}
GIG_LIST_ENTRY_MAP = {1: "FAVOURITE", 2: "BLACKLISTED"}


class GigServiceError(Exception):
    """Base exception for gig service errors."""


# ==========================================
# Helper Permissions & Scoping
# ==========================================

def _is_user_authorized_for_organisation(db: Session, user: User, organisation_id: int) -> bool:
    """Check if user is Super Admin, Admin, owner, or account admin for organisation."""
    user_roles = [ura.role.role_code for ura in user.role_assignments if ura.deleted_at is None and ura.role]
    if "SUPER_ADMIN" in user_roles or "ADMIN" in user_roles:
        return True

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        return False

    if org.created_by == user.id:
        return True

    # Account Admin role assignment
    has_admin_assignment = any(
        ura.role.role_code in ["EMPLOYER", "ACCOUNT_ADMIN"] and ura.organisation_id == organisation_id
        for ura in user.role_assignments
        if ura.deleted_at is None and ura.role
    )
    if has_admin_assignment:
        return True

    # Active recruiter mapping
    now_utc = datetime.now(timezone.utc)
    recruiter_mapping = (
        db.query(OrganisationRecruiterMapping)
        .filter(
            OrganisationRecruiterMapping.organisation_id == organisation_id,
            OrganisationRecruiterMapping.recruiter_user_id == user.id,
            OrganisationRecruiterMapping.deleted_at.is_(None),
            OrganisationRecruiterMapping.valid_from <= now_utc,
            or_(
                OrganisationRecruiterMapping.valid_until.is_(None),
                OrganisationRecruiterMapping.valid_until >= now_utc,
            ),
        )
        .first()
    )
    return recruiter_mapping is not None


def _log_audit_event(
    db: Session,
    actor_user_id: Optional[int],
    action_code: str,
    resource_type: str,
    resource_id: str,
    payload_clean: Optional[dict] = None,
):
    audit = AuditEvent(
        actor_user_id=actor_user_id,
        action_code=action_code,
        resource_type=resource_type,
        resource_id=str(resource_id),
        metadata_redacted=payload_clean or {},
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(audit)


# ==========================================
# 1. Gig Worker Profile (FR-0084)
# ==========================================

def create_gig_worker_profile(
    db: Session, user: User, data: GigWorkerProfileCreate
) -> GigWorkerProfileResponse:
    """FR-0084: Create separate profile for gig worker, distinct from permanent/temporary candidates."""
    existing = db.query(GigWorkerProfile).filter(
        GigWorkerProfile.user_id == user.id,
        GigWorkerProfile.deleted_at.is_(None),
    ).first()
    if existing:
        raise ValueError(f"Gig worker profile already exists for user {user.id}.")

    profile = GigWorkerProfile(
        user_id=user.id,
        display_name=data.display_name,
        bio=data.bio,
        availability_status_code_id=data.availability_status_code_id,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(profile)
    db.flush()

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code="GIG_WORKER_PROFILE_CREATED",
        resource_type="GIG_WORKER_PROFILE",
        resource_id=str(profile.id),
        payload_clean={"display_name": profile.display_name},
    )
    db.commit()
    db.refresh(profile)

    return GigWorkerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        availability_status_code_id=profile.availability_status_code_id,
        availability_status=GIG_AVAILABILITY_MAP.get(profile.availability_status_code_id, "AVAILABLE"),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def get_gig_worker_profile(db: Session, user: User) -> GigWorkerProfileResponse:
    profile = db.query(GigWorkerProfile).filter(
        GigWorkerProfile.user_id == user.id,
        GigWorkerProfile.deleted_at.is_(None),
    ).first()
    if not profile:
        raise ValueError(f"Gig worker profile not found for user {user.id}.")

    return GigWorkerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        availability_status_code_id=profile.availability_status_code_id,
        availability_status=GIG_AVAILABILITY_MAP.get(profile.availability_status_code_id, "AVAILABLE"),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


# ==========================================
# 2. Gig Request Management (FR-0085, FR-0086, FR-0097, FR-0203)
# ==========================================

def create_gig_request(
    db: Session, user: User, data: GigRequestCreate
) -> GigRequestResponse:
    """FR-0085, FR-0086, FR-0203: Create gig request with validated pricing, currency, and date range."""
    # Organization authorization
    if not _is_user_authorized_for_organisation(db, user, data.requester_organisation_id):
        raise PermissionError(f"Forbidden: You are not authorized to create gig requests for organisation {data.requester_organisation_id}.")

    # FR-0085 & FR-0203: Price amount must be positive, decimal safe, with companion currency
    if data.price_amount <= Decimal("0.00"):
        raise ValueError("Price amount must be greater than zero.")
    if not data.currency_code or len(data.currency_code) != 3:
        raise ValueError("Currency code must be a valid 3-letter ISO code.")

    # FR-0086: Date window validation
    if data.ends_at < data.starts_at:
        raise ValueError("Gig work window end date cannot precede start date.")

    org = db.query(Organisation).filter(Organisation.id == data.requester_organisation_id).first()
    if not org:
        raise ValueError(f"Organisation with ID {data.requester_organisation_id} not found.")

    gig_req = GigRequest(
        requester_organisation_id=data.requester_organisation_id,
        created_by_user_id=user.id,
        title=data.title,
        description=data.description,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        pricing_type_code_id=data.pricing_type_code_id,
        price_amount=data.price_amount,
        currency_code=data.currency_code,
        status_code_id=2,  # OPEN
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(gig_req)
    db.flush()

    # Status history entry
    history = GigRequestStatusHistory(
        gig_request_id=gig_req.id,
        event_code_id=2,  # OPEN
        actor_user_id=user.id,
        occurred_at=datetime.now(timezone.utc),
        metadata_redacted={"action": "GIG_REQUEST_OPENED", "pricing": str(data.price_amount), "currency": data.currency_code},
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(history)

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code="GIG_REQUEST_CREATED",
        resource_type="GIG_REQUEST",
        resource_id=str(gig_req.id),
        payload_clean={"title": gig_req.title, "amount": str(gig_req.price_amount), "currency": gig_req.currency_code},
    )
    db.commit()
    db.refresh(gig_req)

    return _build_gig_request_response(gig_req, org.legal_name or org.display_name)


def cancel_gig_request(
    db: Session, request_id: int, user: User, cancel_data: GigRequestCancel
) -> GigRequestResponse:
    """FR-0097: Cancel gig request in permitted states and retain status history."""
    gig_req = db.query(GigRequest).filter(
        GigRequest.id == request_id,
        GigRequest.deleted_at.is_(None),
    ).first()
    if not gig_req:
        raise ValueError(f"Gig request with ID {request_id} not found.")

    if not _is_user_authorized_for_organisation(db, user, gig_req.requester_organisation_id):
        raise PermissionError(f"Forbidden: You are not authorized to cancel requests for organisation {gig_req.requester_organisation_id}.")

    # Check allowed cancellation states: allowed in DRAFT (1) or OPEN (2)
    if gig_req.status_code_id in [4, 5]:  # COMPLETED or already CANCELLED
        raise ValueError(f"Cannot cancel gig request in status '{GIG_REQUEST_STATUS_MAP.get(gig_req.status_code_id)}'.")

    # Check if there are active assignments
    active_assignments = db.query(GigAssignment).filter(
        GigAssignment.gig_application_id.in_(
            db.query(GigApplication.id).filter(GigApplication.gig_request_id == gig_req.id)
        ),
        GigAssignment.status_code_id.in_([1, 2]),  # CONFIRMED or ACTIVE
        GigAssignment.deleted_at.is_(None),
    ).count()
    if active_assignments > 0:
        raise ValueError("Cannot cancel gig request with active confirmed assignments.")

    gig_req.status_code_id = 5  # CANCELLED
    gig_req.updated_at = datetime.now(timezone.utc)
    gig_req.updated_by = user.id

    history = GigRequestStatusHistory(
        gig_request_id=gig_req.id,
        event_code_id=5,  # CANCELLED
        actor_user_id=user.id,
        occurred_at=datetime.now(timezone.utc),
        metadata_redacted={"action": "GIG_REQUEST_CANCELLED", "reason": cancel_data.cancellation_reason},
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(history)

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code="GIG_REQUEST_CANCELLED",
        resource_type="GIG_REQUEST",
        resource_id=str(gig_req.id),
        payload_clean={"reason": cancel_data.cancellation_reason},
    )
    db.commit()
    db.refresh(gig_req)

    org_name = (gig_req.organisation.legal_name or gig_req.organisation.display_name) if gig_req.organisation else None
    return _build_gig_request_response(gig_req, org_name)


def list_gig_requests(
    db: Session,
    organisation_id: Optional[int] = None,
    status_code_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> GigRequestListResponse:
    query = db.query(GigRequest).filter(GigRequest.deleted_at.is_(None))
    if organisation_id:
        query = query.filter(GigRequest.requester_organisation_id == organisation_id)
    if status_code_id:
        query = query.filter(GigRequest.status_code_id == status_code_id)

    total = query.count()
    items = query.order_by(GigRequest.created_at.desc()).offset(skip).limit(limit).all()

    return GigRequestListResponse(
        total=total,
        items=[_build_gig_request_response(item, (item.organisation.legal_name or item.organisation.display_name) if item.organisation else None) for item in items],
    )


def _build_gig_request_response(req: GigRequest, org_name: Optional[str]) -> GigRequestResponse:
    return GigRequestResponse(
        id=req.id,
        requester_organisation_id=req.requester_organisation_id,
        organisation_name=org_name,
        created_by_user_id=req.created_by_user_id,
        title=req.title,
        description=req.description,
        starts_at=req.starts_at,
        ends_at=req.ends_at,
        pricing_type_code_id=req.pricing_type_code_id,
        pricing_type=GIG_PRICING_TYPE_MAP.get(req.pricing_type_code_id, "FIXED"),
        price_amount=req.price_amount,
        currency_code=req.currency_code,
        status_code_id=req.status_code_id,
        status=GIG_REQUEST_STATUS_MAP.get(req.status_code_id, "OPEN"),
        created_at=req.created_at,
        updated_at=req.updated_at,
    )


# ==========================================
# 3. Gig Application & Direction (FR-0087, FR-0088)
# ==========================================

def apply_to_gig_request(
    db: Session, request_id: int, user: User, data: GigApplicationCreate
) -> GigApplicationResponse:
    """FR-0087: Gig worker applies to request; bids do not flow in reverse."""
    worker_profile = db.query(GigWorkerProfile).filter(
        GigWorkerProfile.user_id == user.id,
        GigWorkerProfile.deleted_at.is_(None),
    ).first()
    if not worker_profile:
        raise PermissionError("Only registered gig workers can apply to gig requests. Create a gig worker profile first.")

    gig_req = db.query(GigRequest).filter(
        GigRequest.id == request_id,
        GigRequest.deleted_at.is_(None),
    ).first()
    if not gig_req:
        raise ValueError(f"Gig request with ID {request_id} not found.")

    if gig_req.status_code_id != 2:  # OPEN
        raise ValueError(f"Cannot apply to gig request in status '{GIG_REQUEST_STATUS_MAP.get(gig_req.status_code_id)}'. Must be OPEN.")

    # Requester cannot apply to their own gig
    if gig_req.created_by_user_id == user.id:
        raise ValueError("Requesters cannot apply to their own gig requests. Bids do not flow in prohibited direction.")

    # Duplicate application check
    existing = db.query(GigApplication).filter(
        GigApplication.gig_request_id == request_id,
        GigApplication.gig_worker_profile_id == worker_profile.id,
        GigApplication.deleted_at.is_(None),
    ).first()
    if existing:
        raise ValueError(f"Gig worker has already applied to gig request {request_id}.")

    app = GigApplication(
        gig_request_id=request_id,
        gig_worker_profile_id=worker_profile.id,
        applied_at=datetime.now(timezone.utc),
        status_code_id=1,  # APPLIED
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(app)
    db.flush()

    history = GigApplicationStatusHistory(
        gig_application_id=app.id,
        event_code_id=1,  # APPLIED
        actor_user_id=user.id,
        occurred_at=datetime.now(timezone.utc),
        metadata_redacted={"action": "GIG_APPLIED", "notes": data.notes},
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(history)

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code="GIG_APPLICATION_SUBMITTED",
        resource_type="GIG_APPLICATION",
        resource_id=str(app.id),
        payload_clean={"gig_request_id": request_id, "worker_id": worker_profile.id},
    )
    db.commit()
    db.refresh(app)

    return _build_gig_application_response(app, gig_req.title, worker_profile.display_name)


def decide_gig_application(
    db: Session, application_id: int, user: User, decision_data: GigApplicationDecision
) -> Tuple[GigApplicationResponse, Optional[GigAssignmentResponse]]:
    """FR-0088, FR-0089, FR-0091: Requester decides gig application and creates assignment with handoff reference."""
    app = db.query(GigApplication).filter(
        GigApplication.id == application_id,
        GigApplication.deleted_at.is_(None),
    ).first()
    if not app:
        raise ValueError(f"Gig application with ID {application_id} not found.")

    gig_req = app.gig_request
    if not _is_user_authorized_for_organisation(db, user, gig_req.requester_organisation_id):
        raise PermissionError(f"Forbidden: Only authorized requester can decide gig applications for organisation {gig_req.requester_organisation_id}.")

    if app.status_code_id != 1:  # APPLIED
        raise ValueError(f"Cannot decide application already in status '{GIG_APPLICATION_STATUS_MAP.get(app.status_code_id)}'.")

    now_utc = datetime.now(timezone.utc)
    assignment_res = None

    if decision_data.decision == "ACCEPTED":
        # FR-0089: Check for overlapping worker assignments
        overlap = db.query(GigAssignment).filter(
            GigAssignment.gig_worker_profile_id == app.gig_worker_profile_id,
            GigAssignment.status_code_id.in_([1, 2]),  # CONFIRMED or ACTIVE
            GigAssignment.deleted_at.is_(None),
            # Overlap condition: starts_at < existing.ends_at AND ends_at > existing.starts_at
            gig_req.starts_at < GigAssignment.ends_at,
            gig_req.ends_at > GigAssignment.starts_at,
        ).first()

        if overlap:
            raise ValueError(
                f"Conflicting assignment detected for worker {app.gig_worker_profile_id}: "
                f"Worker already has confirmed assignment {overlap.id} overlapping {gig_req.starts_at.isoformat()} - {gig_req.ends_at.isoformat()}."
            )

        app.status_code_id = 2  # ACCEPTED
        app.decided_by_user_id = user.id
        app.decided_at = now_utc
        app.updated_at = now_utc
        app.updated_by = user.id

        # Create GigAssignment
        assignment = GigAssignment(
            gig_application_id=app.id,
            requester_organisation_id=gig_req.requester_organisation_id,
            gig_worker_profile_id=app.gig_worker_profile_id,
            starts_at=gig_req.starts_at,
            ends_at=gig_req.ends_at,
            status_code_id=1,  # CONFIRMED
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(assignment)
        db.flush()

        # FR-0091: Create idempotent handoff reference record
        handoff_ref = f"EXT-HANDOFF-{assignment.id}-{uuid.uuid4().hex[:8].upper()}"
        handoff = GigHandoffReference(
            gig_assignment_id=assignment.id,
            fulfilment_provider_code="EXT_FULFILMENT_PARTNER_V1",
            external_handoff_reference=handoff_ref,
            handoff_status_code_id=1,  # PENDING
            last_reconciled_at=now_utc,
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(handoff)

        # Assignment status history
        asg_hist = GigAssignmentStatusHistory(
            gig_assignment_id=assignment.id,
            event_code_id=1,  # CONFIRMED
            actor_user_id=user.id,
            occurred_at=now_utc,
            metadata_redacted={"action": "ASSIGNMENT_CONFIRMED", "handoff_reference": handoff_ref},
            created_by=user.id,
            updated_by=user.id,
        )
        db.add(asg_hist)

        assignment_res = GigAssignmentResponse(
            id=assignment.id,
            gig_application_id=assignment.gig_application_id,
            requester_organisation_id=assignment.requester_organisation_id,
            gig_worker_profile_id=assignment.gig_worker_profile_id,
            starts_at=assignment.starts_at,
            ends_at=assignment.ends_at,
            status_code_id=assignment.status_code_id,
            status=GIG_ASSIGNMENT_STATUS_MAP.get(assignment.status_code_id, "CONFIRMED"),
            handoff_reference=handoff_ref,
            fulfilment_provider_code=handoff.fulfilment_provider_code,
            handoff_status=GIG_HANDOFF_STATUS_MAP.get(handoff.handoff_status_code_id, "PENDING"),
            created_at=assignment.created_at,
        )

    elif decision_data.decision == "REJECTED":
        app.status_code_id = 3  # REJECTED
        app.decided_by_user_id = user.id
        app.decided_at = now_utc
        app.updated_at = now_utc
        app.updated_by = user.id

    # Record Application status history
    app_hist = GigApplicationStatusHistory(
        gig_application_id=app.id,
        event_code_id=app.status_code_id,
        actor_user_id=user.id,
        occurred_at=now_utc,
        metadata_redacted={"action": f"APPLICATION_{decision_data.decision}", "reason": decision_data.reason},
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(app_hist)

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code=f"GIG_APPLICATION_{decision_data.decision}",
        resource_type="GIG_APPLICATION",
        resource_id=str(app.id),
        payload_clean={"decision": decision_data.decision, "reason": decision_data.reason},
    )
    db.commit()
    db.refresh(app)

    worker_name = app.gig_worker_profile.display_name if app.gig_worker_profile else None
    return _build_gig_application_response(app, gig_req.title, worker_name), assignment_res


def _build_gig_application_response(app: GigApplication, req_title: Optional[str], worker_name: Optional[str]) -> GigApplicationResponse:
    return GigApplicationResponse(
        id=app.id,
        gig_request_id=app.gig_request_id,
        gig_request_title=req_title,
        gig_worker_profile_id=app.gig_worker_profile_id,
        gig_worker_name=worker_name,
        applied_at=app.applied_at,
        status_code_id=app.status_code_id,
        status=GIG_APPLICATION_STATUS_MAP.get(app.status_code_id, "APPLIED"),
        decided_by_user_id=app.decided_by_user_id,
        decided_at=app.decided_at,
        created_at=app.created_at,
    )


# ==========================================
# 4. Gig Worker Availability (FR-0090)
# ==========================================

def set_worker_availability(
    db: Session, user: User, data: GigWorkerAvailabilityCreate
) -> GigWorkerAvailabilityResponse:
    """FR-0090: Manage worker availability with valid dates and conflict detection."""
    worker_profile = db.query(GigWorkerProfile).filter(
        GigWorkerProfile.user_id == user.id,
        GigWorkerProfile.deleted_at.is_(None),
    ).first()
    if not worker_profile:
        raise PermissionError("Only registered gig workers can set availability windows.")

    if data.ends_at < data.starts_at:
        raise ValueError("Availability end date cannot precede start date.")

    # Check for conflicts with confirmed assignments
    assignment_conflict = db.query(GigAssignment).filter(
        GigAssignment.gig_worker_profile_id == worker_profile.id,
        GigAssignment.status_code_id.in_([1, 2]),  # CONFIRMED or ACTIVE
        GigAssignment.deleted_at.is_(None),
        data.starts_at < GigAssignment.ends_at,
        data.ends_at > GigAssignment.starts_at,
    ).first()

    if assignment_conflict and data.status_code_id == 1:  # Cannot mark AVAILABLE when already confirmed
        raise ValueError(
            f"Availability conflict: Worker has confirmed gig assignment {assignment_conflict.id} "
            f"during {data.starts_at.isoformat()} - {data.ends_at.isoformat()}."
        )

    avail = GigWorkerAvailability(
        gig_worker_profile_id=worker_profile.id,
        status_code_id=data.status_code_id,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        currency_code=data.currency_code,
        amount=data.amount,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(avail)
    db.commit()
    db.refresh(avail)

    return GigWorkerAvailabilityResponse(
        id=avail.id,
        gig_worker_profile_id=avail.gig_worker_profile_id,
        status_code_id=avail.status_code_id,
        status=GIG_AVAILABILITY_MAP.get(avail.status_code_id, "AVAILABLE"),
        starts_at=avail.starts_at,
        ends_at=avail.ends_at,
        currency_code=avail.currency_code,
        amount=avail.amount,
        created_at=avail.created_at,
    )


# ==========================================
# 5. External Earnings Reconciliation (FR-0092)
# ==========================================

def reconcile_gig_earnings(
    db: Session, event_data: GigEarningsEventCreate
) -> GigEarningsResponse:
    """FR-0092: Reconcile earnings originating from external boundary; repeated events are not double-counted."""
    # Idempotency check on external_event_reference
    existing = db.query(GigEarningsReconciliation).filter(
        GigEarningsReconciliation.external_event_reference == event_data.external_event_reference,
        GigEarningsReconciliation.deleted_at.is_(None),
    ).first()
    if existing:
        return GigEarningsResponse(
            id=existing.id,
            gig_request_id=existing.gig_request_id,
            gig_worker_profile_id=existing.gig_worker_profile_id,
            external_event_reference=existing.external_event_reference,
            amount=existing.amount,
            currency_code=existing.currency_code,
            status_code_id=existing.status_code_id,
            status=GIG_EARNINGS_STATUS_MAP.get(existing.status_code_id, "RECONCILED"),
            created_at=existing.created_at,
        )

    rec = GigEarningsReconciliation(
        gig_request_id=event_data.gig_request_id,
        gig_worker_profile_id=event_data.gig_worker_profile_id,
        status_code_id=event_data.status_code_id,
        amount=event_data.amount,
        currency_code=event_data.currency_code,
        external_event_reference=event_data.external_event_reference,
    )
    db.add(rec)
    db.flush()

    _log_audit_event(
        db,
        actor_user_id=None,
        action_code="GIG_EARNINGS_RECONCILED",
        resource_type="GIG_EARNINGS_RECONCILIATION",
        resource_id=str(rec.id),
        payload_clean={"amount": str(rec.amount), "currency": rec.currency_code, "ref": rec.external_event_reference},
    )
    db.commit()
    db.refresh(rec)

    return GigEarningsResponse(
        id=rec.id,
        gig_request_id=rec.gig_request_id,
        gig_worker_profile_id=rec.gig_worker_profile_id,
        external_event_reference=rec.external_event_reference,
        amount=rec.amount,
        currency_code=rec.currency_code,
        status_code_id=rec.status_code_id,
        status=GIG_EARNINGS_STATUS_MAP.get(rec.status_code_id, "RECONCILED"),
        created_at=rec.created_at,
    )


# ==========================================
# 6. Favourite & Blacklist Exclusivity (FR-0093, FR-0095)
# ==========================================

def manage_worker_list_entry(
    db: Session, user: User, organisation_id: int, data: GigWorkerListEntryCreate
) -> GigWorkerListEntryResponse:
    """FR-0093: Favourite and blacklist exclusivity. Contradictory active states are blocked."""
    if not _is_user_authorized_for_organisation(db, user, organisation_id):
        raise PermissionError(f"Forbidden: You are not authorized to manage worker lists for organisation {organisation_id}.")

    worker = db.query(GigWorkerProfile).filter(
        GigWorkerProfile.id == data.gig_worker_profile_id,
        GigWorkerProfile.deleted_at.is_(None),
    ).first()
    if not worker:
        raise ValueError(f"Gig worker with ID {data.gig_worker_profile_id} not found.")

    target_code_id = 1 if data.list_type == "FAVOURITE" else 2
    opposite_code_id = 2 if target_code_id == 1 else 1

    # Check if contradictory entry exists
    conflicting = db.query(GigWorkerListEntry).filter(
        GigWorkerListEntry.requester_organisation_id == organisation_id,
        GigWorkerListEntry.gig_worker_profile_id == data.gig_worker_profile_id,
        GigWorkerListEntry.status_code_id == opposite_code_id,
        GigWorkerListEntry.deleted_at.is_(None),
    ).first()

    if conflicting:
        opp_name = GIG_LIST_ENTRY_MAP.get(opposite_code_id)
        raise ValueError(
            f"Exclusivity conflict: Worker {data.gig_worker_profile_id} is already on the {opp_name} list. "
            f"A worker cannot simultaneously be active on both favourite and blacklist."
        )

    # Check if target already active
    existing = db.query(GigWorkerListEntry).filter(
        GigWorkerListEntry.requester_organisation_id == organisation_id,
        GigWorkerListEntry.gig_worker_profile_id == data.gig_worker_profile_id,
        GigWorkerListEntry.status_code_id == target_code_id,
        GigWorkerListEntry.deleted_at.is_(None),
    ).first()

    if existing:
        return GigWorkerListEntryResponse(
            id=existing.id,
            requester_organisation_id=existing.requester_organisation_id,
            gig_worker_profile_id=existing.gig_worker_profile_id,
            gig_worker_name=worker.display_name,
            status_code_id=existing.status_code_id,
            list_type=GIG_LIST_ENTRY_MAP.get(existing.status_code_id, "FAVOURITE"),
            created_at=existing.created_at,
        )

    entry = GigWorkerListEntry(
        requester_organisation_id=organisation_id,
        gig_worker_profile_id=data.gig_worker_profile_id,
        status_code_id=target_code_id,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(entry)
    db.flush()

    fav_hist = GigWorkerFavouriteHistory(
        event_code_id=target_code_id,
        actor_user_id=user.id,
        occurred_at=datetime.now(timezone.utc),
        metadata_redacted={"action": f"WORKER_{data.list_type}", "worker_id": data.gig_worker_profile_id},
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(fav_hist)

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code=f"GIG_WORKER_{data.list_type}",
        resource_type="GIG_WORKER_LIST_ENTRY",
        resource_id=str(entry.id),
        payload_clean={"organisation_id": organisation_id, "worker_id": data.gig_worker_profile_id},
    )
    db.commit()
    db.refresh(entry)

    return GigWorkerListEntryResponse(
        id=entry.id,
        requester_organisation_id=entry.requester_organisation_id,
        gig_worker_profile_id=entry.gig_worker_profile_id,
        gig_worker_name=worker.display_name,
        status_code_id=entry.status_code_id,
        list_type=GIG_LIST_ENTRY_MAP.get(entry.status_code_id, "FAVOURITE"),
        created_at=entry.created_at,
    )


def list_requester_blacklisted_workers(
    db: Session, user: User, organisation_id: int
) -> List[GigWorkerListEntryResponse]:
    """FR-0095: Blacklists are restricted to authorized owner/admin workflows."""
    if not _is_user_authorized_for_organisation(db, user, organisation_id):
        raise PermissionError(f"Forbidden: Unauthorized actor cannot view requester private blacklist for organisation {organisation_id}.")

    entries = db.query(GigWorkerListEntry).filter(
        GigWorkerListEntry.requester_organisation_id == organisation_id,
        GigWorkerListEntry.status_code_id == 2,  # BLACKLISTED
        GigWorkerListEntry.deleted_at.is_(None),
    ).all()

    return [
        GigWorkerListEntryResponse(
            id=e.id,
            requester_organisation_id=e.requester_organisation_id,
            gig_worker_profile_id=e.gig_worker_profile_id,
            gig_worker_name=e.gig_worker_profile.display_name if e.gig_worker_profile else None,
            status_code_id=e.status_code_id,
            list_type="BLACKLISTED",
            created_at=e.created_at,
        )
        for e in entries
    ]


# ==========================================
# 7. Completed Gig Rating (FR-0094)
# ==========================================

def rate_completed_gig(
    db: Session, user: User, data: GigRatingCreate
) -> GigRatingResponse:
    """FR-0094: Ratings are allowed only for completed gigs and within defined scale (1.00 - 5.00)."""
    assignment = db.query(GigAssignment).filter(
        GigAssignment.id == data.gig_assignment_id,
        GigAssignment.deleted_at.is_(None),
    ).first()
    if not assignment:
        raise ValueError(f"Gig assignment with ID {data.gig_assignment_id} not found.")

    if not _is_user_authorized_for_organisation(db, user, assignment.requester_organisation_id):
        raise PermissionError("Forbidden: Only authorized requester can rate gig assignments.")

    # Rating validation scale (1 to 5)
    if data.rating_score < Decimal("1.00") or data.rating_score > Decimal("5.00"):
        raise ValueError("Rating score must be within the defined scale of 1.00 to 5.00.")

    # Incomplete gig check
    if assignment.status_code_id != 3:  # COMPLETED
        raise ValueError(f"Ratings are allowed only for completed gigs. Current assignment status is '{GIG_ASSIGNMENT_STATUS_MAP.get(assignment.status_code_id)}'.")

    # Check for existing rating
    existing = db.query(GigRating).filter(
        GigRating.gig_request_id == assignment.gig_application.gig_request_id,
        GigRating.gig_worker_profile_id == assignment.gig_worker_profile_id,
        GigRating.deleted_at.is_(None),
    ).first()
    if existing:
        raise ValueError(f"Gig assignment has already been rated.")

    rating = GigRating(
        gig_request_id=assignment.gig_application.gig_request_id,
        gig_worker_profile_id=assignment.gig_worker_profile_id,
        status_code_id=1,  # SUBMITTED
        amount=data.rating_score,
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(rating)
    db.flush()

    _log_audit_event(
        db,
        actor_user_id=user.id,
        action_code="GIG_RATING_SUBMITTED",
        resource_type="GIG_RATING",
        resource_id=str(rating.id),
        payload_clean={"score": str(data.rating_score), "assignment_id": assignment.id},
    )
    db.commit()
    db.refresh(rating)

    return GigRatingResponse(
        id=rating.id,
        gig_request_id=rating.gig_request_id,
        gig_worker_profile_id=rating.gig_worker_profile_id,
        rating_score=rating.amount,
        status="SUBMITTED",
        created_at=rating.created_at,
    )


# ==========================================
# 8. External Provider Outage Resilience (FR-0096)
# ==========================================

def handle_external_provider_outage(
    db: Session, assignment_id: int, error_message: str
) -> GigAssignmentResponse:
    """FR-0096: External outage must not falsely advance assignment state. State remains retryable with recorded error."""
    assignment = db.query(GigAssignment).filter(
        GigAssignment.id == assignment_id,
        GigAssignment.deleted_at.is_(None),
    ).first()
    if not assignment:
        raise ValueError(f"Gig assignment with ID {assignment_id} not found.")

    handoff = assignment.handoff_reference
    if handoff:
        handoff.handoff_status_code_id = 3  # FAILED_RETRYABLE
        handoff.last_reconciled_at = datetime.now(timezone.utc)

    # Note: Assignment state remains unchanged (e.g. CONFIRMED), NOT falsely marked completed or active
    asg_hist = GigAssignmentStatusHistory(
        gig_assignment_id=assignment.id,
        event_code_id=3,  # FAILED_RETRYABLE
        actor_user_id=None,
        occurred_at=datetime.now(timezone.utc),
        metadata_redacted={"action": "FULFILMENT_PROVIDER_OUTAGE", "error": error_message, "retryable": True},
    )
    db.add(asg_hist)

    _log_audit_event(
        db,
        actor_user_id=None,
        action_code="GIG_FULFILMENT_OUTAGE_LOGGED",
        resource_type="GIG_ASSIGNMENT",
        resource_id=str(assignment.id),
        payload_clean={"error": error_message, "retryable": True},
    )
    db.commit()
    db.refresh(assignment)

    return GigAssignmentResponse(
        id=assignment.id,
        gig_application_id=assignment.gig_application_id,
        requester_organisation_id=assignment.requester_organisation_id,
        gig_worker_profile_id=assignment.gig_worker_profile_id,
        starts_at=assignment.starts_at,
        ends_at=assignment.ends_at,
        status_code_id=assignment.status_code_id,
        status=GIG_ASSIGNMENT_STATUS_MAP.get(assignment.status_code_id, "CONFIRMED"),
        handoff_reference=handoff.external_handoff_reference if handoff else None,
        fulfilment_provider_code=handoff.fulfilment_provider_code if handoff else None,
        handoff_status=GIG_HANDOFF_STATUS_MAP.get(handoff.handoff_status_code_id, "FAILED_RETRYABLE") if handoff else None,
        created_at=assignment.created_at,
    )
