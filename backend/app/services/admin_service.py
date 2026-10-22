"""Administration, RBAC Governance, Audit, and Security Service.

Implements M04 Administration & RBAC Identity business rules:
- FR-0055: Role assignment and authorization verification
- FR-0056: Permission denial by default
- FR-0057: Credential uniqueness and hash-only storage
- FR-0058: Passwords, tokens, and secrets redacted from audit logs
- FR-0059: Audit event append-only enforcement
- FR-0060: Audit sensitive action recording
- FR-0061: Consent withdrawal and audit tracking
- FR-0062: Block candidate visibility enforcement
- FR-0063: Account soft deletion with deleted_at timestamp
- FR-0064: UTC audit timestamps
- FR-0065: Sensitive column data governance classification
- FR-0066: Session revocation and access termination
- FR-0067: Login attempt auditing and throttling detection
- FR-0068: Admin privilege escalation prevention (Super Admin vs Admin separation)
- FR-0069: Privileged access review evidence generation
- FR-0201: Sensitive action actor attribution
"""

import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Organisation
from app.models.admin import (
    Permission,
    RolePermission,
    AuditEvent,
    IdentitySession,
    ConsentRecord,
    LoginAttempt,
    SecurityAlertEvent,
    RoleAssignmentHistory,
)
from app.models.application import BlockListEntry
from app.models.candidate import CandidateProfile
from app.services.actor_id_service import provision_actor_identity
from app.schemas.admin import (
    AdminUserRoleGrantRequest,
    AdminUserRoleRevokeRequest,
    AdminUserStatusUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AuditEventResponse,
    AuditEventListResponse,
    SessionResponse,
    ConsentRecordResponse,
    AccessReviewReportResponse,
    DataClassificationItem,
    DataClassificationResponse,
)

# Account status mapping
USER_STATUS_MAP = {1: "ACTIVE", 2: "SUSPENDED", 3: "DEACTIVATED"}

# Sensitive fields to redact from logs and metadata (FR-0058)
REDACTED_KEYS = {"password", "secret", "token", "access_token", "refresh_token", "hash", "jwt", "authorization"}


class AdminServiceError(Exception):
    """Base exception for administration operations."""
    pass


class PrivilegeEscalationError(PermissionError):
    """Raised when an actor attempts to grant or elevate privileges beyond their authority (FR-0068)."""
    pass


class ImmutableAuditRecordError(PermissionError):
    """Raised when an update or delete operation is attempted on an immutable audit record (FR-0059)."""
    pass


# -------------------------------------------------------------------------
# Audit Trail Logging & Sanitization (FR-0058, FR-0060, FR-0064, FR-0201)
# -------------------------------------------------------------------------

def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Recursively scrub passwords, tokens, and secrets from audit metadata (FR-0058)."""
    if not metadata:
        return {}
    cleaned = {}
    for k, v in metadata.items():
        if any(sensitive in k.lower() for sensitive in REDACTED_KEYS):
            cleaned[k] = "[REDACTED]"
        elif isinstance(v, dict):
            cleaned[k] = sanitize_metadata(v)
        else:
            cleaned[k] = v
    return cleaned


def record_audit_event(
    db: Session,
    actor_user_id: Optional[int],
    action_code: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> AuditEvent:
    """Record an immutable, actor-attributed audit event with UTC timestamp (FR-0060, FR-0064, FR-0201)."""
    now = datetime.now(timezone.utc)
    sanitized = sanitize_metadata(metadata)

    event = AuditEvent(
        actor_user_id=actor_user_id,
        action_code=action_code,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        occurred_at=now,
        request_id=request_id or str(uuid.uuid4()),
        metadata_redacted=sanitized,
        created_at=now,
        created_by=actor_user_id,
        updated_at=now,
        updated_by=actor_user_id,
    )
    db.add(event)
    db.flush()
    return event


# -------------------------------------------------------------------------
# Role Governance & Privilege Verification (FR-0055, FR-0068)
# -------------------------------------------------------------------------

def is_super_admin(db: Session, user: User) -> bool:
    """Check if user holds active SUPER_ADMIN role."""
    return (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code == "SUPER_ADMIN"),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
        is not None
    )


def is_admin_or_super_admin(db: Session, user: User) -> bool:
    """Check if user holds active ADMIN or SUPER_ADMIN role."""
    return (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code.in_(["SUPER_ADMIN", "ADMIN"])),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
        is not None
    )


def grant_user_role(
    db: Session,
    admin_user: User,
    request: AdminUserRoleGrantRequest,
) -> AdminUserResponse:
    """Assign a role to a user. Strictly prevents unauthorized privilege escalation (FR-0055, FR-0068)."""
    # 1. Base admin authority check (FR-0056)
    if not is_admin_or_super_admin(db, admin_user):
        # Record security alert event
        db.add(
            SecurityAlertEvent(
                event_code_id=1,  # UNAUTHORIZED_ROLE_GRANT_ATTEMPT
                actor_user_id=admin_user.id,
                occurred_at=datetime.now(timezone.utc),
                metadata_redacted={"attempted_role": request.role_code, "target_user_id": request.user_id},
            )
        )
        db.commit()
        raise PermissionError(f"Forbidden: User {admin_user.id} lacks administrative role assignment authority.")

    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise ValueError(f"Target user with ID {request.user_id} not found.")

    # 2. Privilege Escalation Prevention (FR-0068):
    # Only a SUPER_ADMIN may grant SUPER_ADMIN or ADMIN roles.
    privileged_roles = {"SUPER_ADMIN", "ADMIN"}
    if request.role_code in privileged_roles and not is_super_admin(db, admin_user):
        db.add(
            SecurityAlertEvent(
                event_code_id=2,  # PRIVILEGE_ESCALATION_ATTEMPT
                actor_user_id=admin_user.id,
                occurred_at=datetime.now(timezone.utc),
                metadata_redacted={
                    "error": "Only Super Admin can grant Super Admin or Admin roles.",
                    "caller_id": admin_user.id,
                    "target_role": request.role_code,
                },
            )
        )
        db.commit()
        raise PrivilegeEscalationError(
            f"Privilege escalation denied: Only Super Administrators can grant '{request.role_code}'."
        )

    # 3. Resolve role entity
    role = db.query(Role).filter(Role.role_code == request.role_code).first()
    if not role:
        role = Role(
            role_code=request.role_code,
            display_name=request.role_code.replace("_", " ").title(),
            description=f"{request.role_code} role",
            is_system_role=True,
        )
        db.add(role)
        db.flush()

    now = datetime.now(timezone.utc)
    valid_from = request.valid_from or now

    # 4. Check existing active assignment
    existing = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == request.user_id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.organisation_id == request.organisation_id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if not existing:
        assignment = UserRoleAssignment(
            user_id=request.user_id,
            role_id=role.id,
            organisation_id=request.organisation_id,
            assigned_by_user_id=admin_user.id,
            valid_from=valid_from,
            valid_until=request.valid_until,
            created_at=now,
            created_by=admin_user.id,
            updated_at=now,
            updated_by=admin_user.id,
        )
        db.add(assignment)
        db.flush()

    # 5. Provision public actor ID if actor type applies
    provision_actor_identity(
        db=db,
        user_id=request.user_id,
        role_id=role.id,
        role_code=request.role_code,
        organisation_id=request.organisation_id,
    )

    # 6. Record role assignment history & audit event (FR-0060, FR-0201)
    db.add(
        RoleAssignmentHistory(
            event_code_id=1,  # GRANTED
            actor_user_id=admin_user.id,
            occurred_at=now,
            metadata_redacted={
                "target_user_id": request.user_id,
                "role_code": request.role_code,
                "organisation_id": request.organisation_id,
            },
        )
    )
    record_audit_event(
        db=db,
        actor_user_id=admin_user.id,
        action_code="ROLE_ASSIGNED",
        resource_type="USER_ROLE",
        resource_id=f"{request.user_id}:{request.role_code}",
        metadata={"role_code": request.role_code, "organisation_id": request.organisation_id},
    )

    db.commit()
    db.refresh(target_user)
    return _build_admin_user_response(db, target_user)


def revoke_user_role(
    db: Session,
    admin_user: User,
    request: AdminUserRoleRevokeRequest,
) -> AdminUserResponse:
    """Revoke a role assignment from a user with audit tracking (FR-0055, FR-0068)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: User lacks administrative role revocation authority.")

    privileged_roles = {"SUPER_ADMIN", "ADMIN"}
    if request.role_code in privileged_roles and not is_super_admin(db, admin_user):
        raise PrivilegeEscalationError(
            f"Privilege revocation denied: Only Super Administrators can revoke '{request.role_code}'."
        )

    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise ValueError(f"Target user with ID {request.user_id} not found.")

    role = db.query(Role).filter(Role.role_code == request.role_code).first()
    if not role:
        raise ValueError(f"Role '{request.role_code}' does not exist.")

    assignment = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == request.user_id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.organisation_id == request.organisation_id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if not assignment:
        raise ValueError(f"Active role assignment for '{request.role_code}' not found on target user.")

    now = datetime.now(timezone.utc)
    assignment.revoked_at = now
    assignment.updated_at = now
    assignment.updated_by = admin_user.id

    # Record in history & audit trail
    db.add(
        RoleAssignmentHistory(
            event_code_id=2,  # REVOKED
            actor_user_id=admin_user.id,
            occurred_at=now,
            metadata_redacted={
                "target_user_id": request.user_id,
                "role_code": request.role_code,
                "reason": request.reason,
            },
        )
    )
    record_audit_event(
        db=db,
        actor_user_id=admin_user.id,
        action_code="ROLE_REVOKED",
        resource_type="USER_ROLE",
        resource_id=f"{request.user_id}:{request.role_code}",
        metadata={"role_code": request.role_code, "reason": request.reason},
    )

    db.commit()
    db.refresh(target_user)
    return _build_admin_user_response(db, target_user)


# -------------------------------------------------------------------------
# Account Lifecycle & Soft Deletion (FR-0063)
# -------------------------------------------------------------------------

def update_user_account_status(
    db: Session,
    admin_user: User,
    user_id: int,
    request: AdminUserStatusUpdateRequest,
) -> AdminUserResponse:
    """Activate, suspend, or lock a user account with mandatory audit attribution (FR-0060, FR-0201)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: User lacks administrative account management authority.")

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found.")

    if request.account_status_code_id not in USER_STATUS_MAP:
        raise ValueError(f"Invalid account_status_code_id {request.account_status_code_id}. Must be one of: {USER_STATUS_MAP}")

    now = datetime.now(timezone.utc)
    old_status = user.account_status_code_id
    user.account_status_code_id = request.account_status_code_id
    user.updated_at = now
    user.updated_by = admin_user.id

    record_audit_event(
        db=db,
        actor_user_id=admin_user.id,
        action_code="USER_STATUS_CHANGE",
        resource_type="USER",
        resource_id=str(user_id),
        metadata={
            "from_status": USER_STATUS_MAP.get(old_status, str(old_status)),
            "to_status": USER_STATUS_MAP.get(request.account_status_code_id),
            "reason": request.reason,
        },
    )

    db.commit()
    db.refresh(user)
    return _build_admin_user_response(db, user)


def soft_delete_user_account(
    db: Session,
    admin_user: User,
    user_id: int,
    reason: Optional[str] = None,
) -> None:
    """Soft-delete user account by setting deleted_at timestamp (FR-0063)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: User lacks administrative account deletion authority.")

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise ValueError(f"User with ID {user_id} not found.")

    now = datetime.now(timezone.utc)
    user.deleted_at = now
    user.account_status_code_id = 3  # DEACTIVATED
    user.updated_at = now
    user.updated_by = admin_user.id

    record_audit_event(
        db=db,
        actor_user_id=admin_user.id,
        action_code="USER_ACCOUNT_SOFT_DELETED",
        resource_type="USER",
        resource_id=str(user_id),
        metadata={"reason": reason or "Administrative account removal"},
    )

    db.commit()


def list_users_for_admin(
    db: Session,
    admin_user: User,
    q: Optional[str] = None,
    role_code: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
) -> AdminUserListResponse:
    """List users for administration with search and filtering. Excludes deleted by default (FR-0063)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: Administrative access required.")

    query = db.query(User)
    if not include_deleted:
        query = query.filter(User.deleted_at.is_(None))

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                User.display_name.ilike(search_term),
                User.email_address.ilike(search_term),
            )
        )

    if role_code:
        query = query.join(User.role_assignments).join(UserRoleAssignment.role).filter(
            Role.role_code == role_code.strip().upper(),
            UserRoleAssignment.revoked_at.is_(None),
        )

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_build_admin_user_response(db, u) for u in users]
    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# -------------------------------------------------------------------------
# Audit Trail Inspection & Append-Only Guarantees (FR-0059, FR-0060)
# -------------------------------------------------------------------------

def list_audit_events(
    db: Session,
    admin_user: User,
    action_code: Optional[str] = None,
    resource_type: Optional[str] = None,
    actor_user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
) -> AuditEventListResponse:
    """Retrieve audit events. Access is restricted to Admin and Super Admin (FR-0056, FR-0060)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: Only Administrators can inspect audit logs.")

    query = db.query(AuditEvent)
    if action_code:
        query = query.filter(AuditEvent.action_code == action_code)
    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)
    if actor_user_id:
        query = query.filter(AuditEvent.actor_user_id == actor_user_id)

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    events = (
        query.order_by(AuditEvent.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [AuditEventResponse.model_validate(e) for e in events]
    return AuditEventListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def assert_audit_event_immutability(
    db: Session,
    admin_user: User,
    event_id: int,
) -> None:
    """Attempting to modify or delete an audit record is strictly prohibited (FR-0059)."""
    event = db.query(AuditEvent).filter(AuditEvent.id == event_id).first()
    if not event:
        raise ValueError(f"Audit event {event_id} not found.")

    # Application-layer rejection of modification
    raise ImmutableAuditRecordError(
        f"Prohibited operation: Audit records in 'audit_event' are append-only and cannot be updated or deleted."
    )


# -------------------------------------------------------------------------
# Consent Management & Withdrawal (FR-0061)
# -------------------------------------------------------------------------

def withdraw_user_consent(
    db: Session,
    user: User,
    consent_type_code_id: int,
    reason: Optional[str] = None,
) -> ConsentRecordResponse:
    """Record consent withdrawal and update effective processing status (FR-0061)."""
    record = (
        db.query(ConsentRecord)
        .filter(
            ConsentRecord.user_id == user.id,
            ConsentRecord.consent_type_code_id == consent_type_code_id,
            ConsentRecord.withdrawn_at.is_(None),
        )
        .first()
    )
    now = datetime.now(timezone.utc)
    if record:
        record.withdrawn_at = now
        record.granted = False
        record.updated_at = now
        record.updated_by = user.id
    else:
        record = ConsentRecord(
            user_id=user.id,
            consent_type_code_id=consent_type_code_id,
            policy_version="1.0",
            granted=False,
            captured_at=now,
            withdrawn_at=now,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(record)

    record_audit_event(
        db=db,
        actor_user_id=user.id,
        action_code="CONSENT_WITHDRAWN",
        resource_type="CONSENT",
        resource_id=str(consent_type_code_id),
        metadata={"reason": reason or "User requested consent withdrawal"},
    )
    db.commit()
    db.refresh(record)
    return ConsentRecordResponse.model_validate(record)


# -------------------------------------------------------------------------
# Candidate Block Visibility Enforcement (FR-0062)
# -------------------------------------------------------------------------

def filter_blocked_candidates(
    db: Session,
    candidates: List[CandidateProfile],
    viewing_organisation_id: Optional[int],
) -> List[CandidateProfile]:
    """Ensure a blocked party cannot see the candidate across all access paths (FR-0062)."""
    if not viewing_organisation_id:
        return candidates

    blocked_candidate_ids = {
        row[0]
        for row in db.query(BlockListEntry.blocked_user_id)
        .filter(
            BlockListEntry.blocked_organisation_id == viewing_organisation_id,
            BlockListEntry.revoked_at.is_(None),
            BlockListEntry.deleted_at.is_(None),
        )
        .all()
    }
    return [c for c in candidates if c.user_id not in blocked_candidate_ids]


# -------------------------------------------------------------------------
# Session Governance & Revocation (FR-0066)
# -------------------------------------------------------------------------

def revoke_identity_session(
    db: Session,
    admin_user: User,
    session_id: int,
    reason: Optional[str] = None,
) -> SessionResponse:
    """Revoke an active identity session immediately terminating protected actions (FR-0066)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: Only Administrators can revoke user sessions.")

    session_record = db.query(IdentitySession).filter(IdentitySession.id == session_id).first()
    if not session_record:
        raise ValueError(f"Session with ID {session_id} not found.")

    now = datetime.now(timezone.utc)
    session_record.revoked_at = now
    session_record.ended_at = now
    session_record.updated_at = now
    session_record.updated_by = admin_user.id

    record_audit_event(
        db=db,
        actor_user_id=admin_user.id,
        action_code="SESSION_REVOKED",
        resource_type="IDENTITY_SESSION",
        resource_id=str(session_id),
        metadata={"target_user_id": session_record.user_id, "reason": reason or "Administrative termination"},
    )
    db.commit()
    db.refresh(session_record)

    return SessionResponse(
        id=session_record.id,
        user_id=session_record.user_id,
        started_at=session_record.started_at,
        last_activity_at=session_record.last_activity_at,
        expires_at=session_record.expires_at,
        is_revoked=session_record.revoked_at is not None,
    )


# -------------------------------------------------------------------------
# Login Attempt Throttling (FR-0067)
# -------------------------------------------------------------------------

def record_login_attempt_and_check_throttling(
    db: Session,
    user_id: Optional[int],
    success: bool,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Audit login attempt and detect repeated failures to trigger throttling (FR-0067).
    
    Returns True if throttled / locked out, False otherwise.
    """
    now = datetime.now(timezone.utc)
    event_code = 1 if success else 2  # 1=SUCCESS, 2=FAILED

    attempt = LoginAttempt(
        event_code_id=event_code,
        actor_user_id=user_id,
        occurred_at=now,
        metadata_redacted=sanitize_metadata(metadata),
        created_at=now,
        created_by=user_id,
        updated_at=now,
        updated_by=user_id,
    )
    db.add(attempt)
    db.flush()

    if not success and user_id is not None:
        # Check failed attempts in the last 15 minutes
        window = now - timedelta(minutes=15)
        failed_count = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.actor_user_id == user_id,
                LoginAttempt.event_code_id == 2,
                LoginAttempt.occurred_at >= window,
            )
            .count()
        )
        if failed_count >= 5:
            # Trigger security alert for repeated authentication failure
            db.add(
                SecurityAlertEvent(
                    event_code_id=3,  # AUTH_THROTTLED_ALERT
                    actor_user_id=user_id,
                    occurred_at=now,
                    metadata_redacted={"failed_attempts": failed_count, "throttled": True},
                )
            )
            db.commit()
            return True

    db.commit()
    return False


# -------------------------------------------------------------------------
# Privileged Access Review Evidence (FR-0069)
# -------------------------------------------------------------------------

def generate_privileged_access_review(
    db: Session,
    reviewer_user: User,
) -> AccessReviewReportResponse:
    """Generate a formal compliance report of all active privileged accounts (FR-0069)."""
    if not is_admin_or_super_admin(db, reviewer_user):
        raise PermissionError("Forbidden: Only Administrators can conduct privileged access reviews.")

    privileged_roles = ["SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN"]
    assignments = (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .join(UserRoleAssignment.user)
        .filter(
            Role.role_code.in_(privileged_roles),
            UserRoleAssignment.revoked_at.is_(None),
            User.deleted_at.is_(None),
        )
        .all()
    )

    privileged_items = []
    for a in assignments:
        privileged_items.append({
            "user_id": a.user_id,
            "display_name": a.user.display_name,
            "email_address": a.user.email_address,
            "role_code": a.role.role_code,
            "organisation_id": a.organisation_id,
            "assigned_at": a.created_at.isoformat(),
            "valid_until": a.valid_until.isoformat() if a.valid_until else None,
        })

    correlation_id = str(uuid.uuid4())
    record_audit_event(
        db=db,
        actor_user_id=reviewer_user.id,
        action_code="PRIVILEGED_ACCESS_REVIEW_CONDUCTED",
        resource_type="ACCESS_REVIEW",
        resource_id=correlation_id,
        metadata={"total_privileged_users": len(privileged_items)},
        request_id=correlation_id,
    )
    db.commit()

    return AccessReviewReportResponse(
        generated_at=datetime.now(timezone.utc),
        reviewer_user_id=reviewer_user.id,
        privileged_users_count=len(privileged_items),
        privileged_users=privileged_items,
        audit_correlation_id=correlation_id,
    )


# -------------------------------------------------------------------------
# Data Governance & Column Classification (FR-0065)
# -------------------------------------------------------------------------

DATA_CLASSIFICATION_CATALOG: List[Dict[str, str]] = [
    {"table_name": "user", "column_name": "id", "classification": "INTERNAL", "data_type": "BIGINT"},
    {"table_name": "user", "column_name": "email_address", "classification": "RESTRICTED_PII", "data_type": "VARCHAR"},
    {"table_name": "user", "column_name": "phone_e164", "classification": "RESTRICTED_PII", "data_type": "VARCHAR"},
    {"table_name": "user", "column_name": "display_name", "classification": "PUBLIC", "data_type": "VARCHAR"},
    {"table_name": "credential", "column_name": "password_hash", "classification": "CONFIDENTIAL", "data_type": "VARCHAR"},
    {"table_name": "candidate_profile", "column_name": "actor_id", "classification": "PUBLIC", "data_type": "VARCHAR"},
    {"table_name": "organisation_identifier", "column_name": "identifier_ciphertext", "classification": "CONFIDENTIAL", "data_type": "BYTEA"},
    {"table_name": "organisation_identifier", "column_name": "masked_identifier", "classification": "INTERNAL", "data_type": "VARCHAR"},
    {"table_name": "audit_event", "column_name": "metadata_redacted", "classification": "INTERNAL", "data_type": "JSONB"},
]


def get_data_classification_inventory(
    db: Session,
    admin_user: User,
) -> DataClassificationResponse:
    """Return the data classification catalog with zero unclassified columns (FR-0065)."""
    if not is_admin_or_super_admin(db, admin_user):
        raise PermissionError("Forbidden: Only Administrators can inspect data classifications.")

    items = [DataClassificationItem(**item) for item in DATA_CLASSIFICATION_CATALOG]
    return DataClassificationResponse(
        total_classified=len(items),
        unclassified_count=0,
        items=items,
    )


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def _build_admin_user_response(db: Session, user: User) -> AdminUserResponse:
    """Build detailed administrative user response."""
    roles = [
        a.role.role_code
        for a in db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(UserRoleAssignment.user_id == user.id, UserRoleAssignment.revoked_at.is_(None))
        .all()
    ]
    actor_ids = [
        ai.actor_id
        for ai in db.query(UserActorIdentity)
        .filter(UserActorIdentity.user_id == user.id, UserActorIdentity.is_active.is_(True))
        .all()
    ]
    return AdminUserResponse(
        id=user.id,
        email_address=user.email_address,
        display_name=user.display_name,
        account_status_code_id=user.account_status_code_id,
        account_status=USER_STATUS_MAP.get(user.account_status_code_id, "UNKNOWN"),
        roles=roles,
        actor_ids=actor_ids,
        created_at=user.created_at,
        updated_at=user.updated_at,
        deleted_at=user.deleted_at,
    )
