"""Licence, Seat Allocation, Device, and Session Domain Service (Module M07).

Implements and enforces all functional and security specifications for Stage 10:
- FR-0098: Positive user licence limit
- FR-0099: Positive device limit
- FR-0100: Seat limit enforcement under concurrency
- FR-0101: Device limit at login with audit of at-limit denial
- FR-0102: Expired session exclusion from device capacity
- FR-0103: Revoked session exclusion and capacity release
- FR-0104: Session activity metadata tracking (device, start, last activity, end)
- FR-0105: Concurrent login race protection
- FR-0106: Device revocation audit linking actor, target, timestamp, reason
- FR-0107: Licence assignment scope (cross-account rejection)
- FR-0108: Duplicate active device registration idempotency
- FR-0109: Session end / logout capacity release
- FR-0110: Seat release on unassignment with transactional capacity preservation
- FR-0111: Login limit audit on rejection without secret exposure
- FR-0204: Expired session cleanup idempotency
"""

import uuid
from typing import Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.models.licence import (
    Licence,
    LicenceSeatAllocation,
    RegisteredDevice,
    DeviceRevocationEvent,
    SessionRevocationEvent,
    LicenceUsageSnapshot,
    LoginDeviceDecision,
    SessionActivityEvent,
    LicenceStatusHistory,
    DeviceLoginCounter,
)
from app.models.admin import IdentitySession, AuditEvent
from app.models.user import User, UserRoleAssignment
from app.models.organisation import Account, AccountOrganisation, AccountAdminAssignment
from app.schemas.licence import (
    LicenceCreate,
    LicenceStatusUpdate,
    LicenceResponse,
    SeatAllocationCreate,
    SeatAllocationResponse,
    DeviceRegisterRequest,
    DeviceResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionCleanupResponse,
    LicenceUsageResponse,
)

LICENCE_STATUS_MAP = {
    1: "ACTIVE",
    2: "SUSPENDED",
    3: "REVOKED",
    4: "EXPIRED",
}

SEAT_STATUS_MAP = {
    1: "ACTIVE",
    2: "RELEASED",
    3: "EXPIRED",
}


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize datetime to timezone-aware UTC for cross-database consistency."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# =========================================================================
# 1. Licence Management (FR-0098, FR-0099, FR-0100)
# =========================================================================

def create_licence(db: Session, current_user: User, payload: LicenceCreate) -> Licence:
    """Create a subscription licence with positive user and device limits (FR-0098, FR-0099)."""
    # 1. Enforce positive integer limits
    if payload.max_users is None or payload.max_users <= 0:
        raise ValueError("Maximum users per licence must be a positive integer greater than 0 (FR-0098).")
    if payload.max_devices_per_user is None or payload.max_devices_per_user <= 0:
        raise ValueError("Maximum devices per user must be a positive integer greater than 0 (FR-0099).")

    # 2. Check date ordering
    if payload.valid_until <= payload.valid_from:
        raise ValueError("valid_until must be strictly after valid_from.")

    # 3. Check Account exists
    account = db.query(Account).filter(Account.id == payload.account_id, Account.deleted_at.is_(None)).first()
    if not account:
        raise ValueError(f"Account ID {payload.account_id} does not exist.")

    # 4. Check Unique Licence Code
    existing = db.query(Licence).filter(Licence.licence_code == payload.licence_code).first()
    if existing:
        raise ValueError(f"Licence with code '{payload.licence_code}' already exists.")

    now = datetime.now(timezone.utc)
    licence = Licence(
        licence_code=payload.licence_code,
        account_id=payload.account_id,
        max_users=payload.max_users,
        max_devices_per_user=payload.max_devices_per_user,
        valid_from=payload.valid_from,
        valid_until=payload.valid_until,
        status_code_id=1,  # ACTIVE
        created_by=current_user.id,
    )
    db.add(licence)
    db.flush()

    # Record Initial Status History
    status_history = LicenceStatusHistory(
        licence_id=licence.id,
        event_code_id=1,  # ACTIVE
        actor_user_id=current_user.id,
        occurred_at=now,
        metadata_redacted={"action": "CREATE", "licence_code": licence.licence_code},
        created_by=current_user.id,
    )
    db.add(status_history)

    # Record Audit Event
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="LICENCE_CREATED",
        resource_type="licence",
        resource_id=str(licence.id),
        occurred_at=now,
        metadata_redacted={
            "licence_code": licence.licence_code,
            "account_id": licence.account_id,
            "max_users": licence.max_users,
            "max_devices_per_user": licence.max_devices_per_user,
        },
        created_by=current_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(licence)
    return licence


def update_licence_status(db: Session, current_user: User, licence_id: int, payload: LicenceStatusUpdate) -> Licence:
    """Update licence lifecycle state following docket-approved state machine."""
    licence = db.query(Licence).filter(Licence.id == licence_id, Licence.deleted_at.is_(None)).with_for_update().first()
    if not licence:
        raise ValueError(f"Licence ID {licence_id} not found.")

    if payload.status_code_id not in LICENCE_STATUS_MAP:
        raise ValueError(f"Invalid status_code_id {payload.status_code_id}. Allowed: {LICENCE_STATUS_MAP}")

    old_status = licence.status_code_id
    new_status = payload.status_code_id

    if old_status == new_status:
        return licence

    # Valid transitions:
    # ACTIVE (1) -> SUSPENDED (2), REVOKED (3), EXPIRED (4)
    # SUSPENDED (2) -> ACTIVE (1), REVOKED (3), EXPIRED (4)
    # REVOKED (3) -> terminal
    # EXPIRED (4) -> terminal / requires renewed dates
    if old_status == 3:
        raise ValueError("Cannot transition a REVOKED licence; REVOKED is terminal.")
    if old_status == 4 and new_status == 1:
        # Check that dates are valid
        now = datetime.now(timezone.utc)
        if _ensure_utc(licence.valid_until) <= now:
            raise ValueError("Cannot reactivate an EXPIRED licence without extending valid_until.")

    licence.status_code_id = new_status
    licence.updated_by = current_user.id
    now = datetime.now(timezone.utc)

    # Record history
    history = LicenceStatusHistory(
        licence_id=licence.id,
        event_code_id=new_status,
        actor_user_id=current_user.id,
        occurred_at=now,
        metadata_redacted={
            "old_status": LICENCE_STATUS_MAP.get(old_status),
            "new_status": LICENCE_STATUS_MAP.get(new_status),
            "reason": payload.reason,
        },
        created_by=current_user.id,
    )
    db.add(history)

    # Audit
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="LICENCE_STATUS_UPDATED",
        resource_type="licence",
        resource_id=str(licence.id),
        occurred_at=now,
        metadata_redacted={
            "licence_code": licence.licence_code,
            "old_status_code_id": old_status,
            "new_status_code_id": new_status,
            "reason": payload.reason,
        },
        created_by=current_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(licence)
    return licence


def get_licence_details(db: Session, licence_id: int) -> LicenceResponse:
    """Retrieve licence details with live seat allocation counts."""
    licence = db.query(Licence).filter(Licence.id == licence_id, Licence.deleted_at.is_(None)).first()
    if not licence:
        raise ValueError(f"Licence ID {licence_id} not found.")

    allocated_seats = (
        db.query(func.count(LicenceSeatAllocation.id))
        .filter(
            LicenceSeatAllocation.licence_id == licence.id,
            LicenceSeatAllocation.status_code_id == 1,
            LicenceSeatAllocation.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )
    available_seats = max(0, licence.max_users - allocated_seats)

    return LicenceResponse(
        id=licence.id,
        licence_code=licence.licence_code,
        account_id=licence.account_id,
        max_users=licence.max_users,
        max_devices_per_user=licence.max_devices_per_user,
        valid_from=licence.valid_from,
        valid_until=licence.valid_until,
        status_code_id=licence.status_code_id,
        status=LICENCE_STATUS_MAP.get(licence.status_code_id, "UNKNOWN"),
        allocated_seats=allocated_seats,
        available_seats=available_seats,
        created_at=licence.created_at,
        updated_at=licence.updated_at,
    )


# =========================================================================
# 2. Seat Allocation (FR-0100, FR-0107, FR-0110)
# =========================================================================

def _validate_user_account_scope(db: Session, user_id: int, account_id: int) -> bool:
    """Validate that target user belongs to the eligible account/organisation scope (FR-0107)."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return False

    # 1. Direct AccountAdminAssignment
    admin_match = db.query(AccountAdminAssignment).filter(
        AccountAdminAssignment.account_id == account_id,
        AccountAdminAssignment.status_code_id == 1,
        AccountAdminAssignment.deleted_at.is_(None),
    ).first()
    # If this account has admin assignments for this user or user matches created_by
    if admin_match and admin_match.created_by == user_id:
        return True

    # 2. Organisations associated with this account
    account_org_ids = [account.root_organisation_id] if account.root_organisation_id else []
    bridge_orgs = (
        db.query(AccountOrganisation.organisation_id)
        .filter(AccountOrganisation.account_id == account_id, AccountOrganisation.deleted_at.is_(None))
        .all()
    )
    for b in bridge_orgs:
        if b[0]:
            account_org_ids.append(b[0])

    if not account_org_ids:
        # Fallback: check if user exists and has account match
        return False

    # 3. Check if target user has role assignment in any of these organisations
    role_match = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.organisation_id.in_(account_org_ids),
            UserRoleAssignment.deleted_at.is_(None),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    return role_match is not None


def allocate_seat(db: Session, current_user: User, payload: SeatAllocationCreate) -> LicenceSeatAllocation:
    """Transaction-safe seat allocation under row lock with capacity check (FR-0100, FR-0107)."""
    now = datetime.now(timezone.utc)

    # 1. Lock Licence row to serialize concurrent allocations
    licence = (
        db.query(Licence)
        .filter(Licence.id == payload.licence_id, Licence.deleted_at.is_(None))
        .with_for_update()
        .first()
    )
    if not licence:
        raise ValueError(f"Licence ID {payload.licence_id} not found.")

    # 2. Check Licence status
    if licence.status_code_id != 1:  # ACTIVE
        status_name = LICENCE_STATUS_MAP.get(licence.status_code_id, "INACTIVE")
        raise ValueError(f"Cannot allocate seat on a licence in '{status_name}' status.")

    # 3. Check Licence validity period
    if _ensure_utc(licence.valid_until) <= now or _ensure_utc(licence.valid_from) > now:
        raise ValueError("Licence is outside its valid active time window.")

    # 4. Check Target User exists
    target_user = db.query(User).filter(User.id == payload.user_id, User.deleted_at.is_(None)).first()
    if not target_user:
        raise ValueError(f"Target user ID {payload.user_id} not found.")

    # 5. Enforce Account / Organisation Scope (FR-0107)
    if not _validate_user_account_scope(db, payload.user_id, licence.account_id):
        raise ValueError(
            f"User ID {payload.user_id} does not belong to the eligible account/organisation scope of Licence ID {licence.id} (FR-0107)."
        )

    # 6. Prevent Duplicate Active Seat Allocation
    existing_seat = (
        db.query(LicenceSeatAllocation)
        .filter(
            LicenceSeatAllocation.licence_id == licence.id,
            LicenceSeatAllocation.user_id == payload.user_id,
            LicenceSeatAllocation.status_code_id == 1,  # ACTIVE
            LicenceSeatAllocation.deleted_at.is_(None),
        )
        .first()
    )
    if existing_seat:
        raise ValueError(f"User ID {payload.user_id} already has an active seat allocation on licence '{licence.licence_code}'.")

    # 7. Count active allocations under lock (FR-0100)
    active_count = (
        db.query(func.count(LicenceSeatAllocation.id))
        .filter(
            LicenceSeatAllocation.licence_id == licence.id,
            LicenceSeatAllocation.status_code_id == 1,
            LicenceSeatAllocation.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )

    if active_count >= licence.max_users:
        raise ValueError(f"Licence seat capacity exceeded: {active_count}/{licence.max_users} seats occupied (FR-0100).")

    # 8. Create Seat Allocation
    allocation = LicenceSeatAllocation(
        user_id=payload.user_id,
        licence_id=licence.id,
        status_code_id=1,  # ACTIVE
        occurred_at=now,
        expires_at=payload.expires_at,
        created_by=current_user.id,
    )
    db.add(allocation)
    db.flush()

    # Record Snapshot
    snapshot = LicenceUsageSnapshot(
        user_id=payload.user_id,
        licence_id=licence.id,
        status_code_id=1,
        occurred_at=now,
        created_by=current_user.id,
    )
    db.add(snapshot)

    # Audit Log
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="SEAT_ALLOCATED",
        resource_type="licence_seat_allocation",
        resource_id=str(allocation.id),
        occurred_at=now,
        metadata_redacted={
            "licence_id": licence.id,
            "licence_code": licence.licence_code,
            "target_user_id": payload.user_id,
            "remaining_seats": licence.max_users - (active_count + 1),
        },
        created_by=current_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(allocation)
    return allocation


def release_seat(db: Session, current_user: User, allocation_id: int, reason: Optional[str] = None) -> LicenceSeatAllocation:
    """Transactionally release an allocated seat, restoring capacity immediately (FR-0110)."""
    now = datetime.now(timezone.utc)

    allocation = (
        db.query(LicenceSeatAllocation)
        .filter(LicenceSeatAllocation.id == allocation_id, LicenceSeatAllocation.deleted_at.is_(None))
        .with_for_update()
        .first()
    )
    if not allocation:
        raise ValueError(f"Seat allocation ID {allocation_id} not found.")

    if allocation.status_code_id != 1:  # ACTIVE
        raise ValueError("Seat allocation is not in ACTIVE status; cannot release.")

    allocation.status_code_id = 2  # RELEASED
    allocation.occurred_at = now
    allocation.updated_by = current_user.id

    # Record Snapshot
    snapshot = LicenceUsageSnapshot(
        user_id=allocation.user_id,
        licence_id=allocation.licence_id,
        status_code_id=2,  # RELEASED
        occurred_at=now,
        created_by=current_user.id,
    )
    db.add(snapshot)

    # Audit Log
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="SEAT_RELEASED",
        resource_type="licence_seat_allocation",
        resource_id=str(allocation.id),
        occurred_at=now,
        metadata_redacted={
            "licence_id": allocation.licence_id,
            "target_user_id": allocation.user_id,
            "reason": reason,
        },
        created_by=current_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(allocation)
    return allocation


# =========================================================================
# 3. Device Management (FR-0101, FR-0106, FR-0108)
# =========================================================================

def register_device(db: Session, user_id: int, payload: DeviceRegisterRequest, actor_id: Optional[int] = None) -> RegisteredDevice:
    """Register client device using SHA-256 fingerprint hash with idempotency (FR-0108)."""
    now = datetime.now(timezone.utc)
    fingerprint = payload.device_fingerprint_hash.lower()

    # Query existing device for this user
    existing = (
        db.query(RegisteredDevice)
        .filter(
            RegisteredDevice.user_id == user_id,
            RegisteredDevice.device_fingerprint_hash == fingerprint,
            RegisteredDevice.deleted_at.is_(None),
        )
        .first()
    )

    if existing:
        # Idempotent registration: update last seen timestamp and label without creating new slots
        existing.last_seen_at = now
        if payload.device_label:
            existing.device_label = payload.device_label
        db.commit()
        db.refresh(existing)
        return existing

    # Create new registration
    device = RegisteredDevice(
        user_id=user_id,
        device_fingerprint_hash=fingerprint,
        device_label=payload.device_label,
        first_seen_at=now,
        last_seen_at=now,
        created_by=actor_id or user_id,
    )
    db.add(device)
    db.flush()

    audit = AuditEvent(
        actor_user_id=actor_id or user_id,
        action_code="DEVICE_REGISTERED",
        resource_type="registered_device",
        resource_id=str(device.id),
        occurred_at=now,
        metadata_redacted={"device_label": payload.device_label},
        created_by=actor_id or user_id,
    )
    db.add(audit)
    db.commit()
    db.refresh(device)
    return device


def revoke_device(db: Session, current_user: User, device_id: int, reason: str) -> RegisteredDevice:
    """Revoke a registered device and terminate all its linked active sessions (FR-0106)."""
    now = datetime.now(timezone.utc)

    device = (
        db.query(RegisteredDevice)
        .filter(RegisteredDevice.id == device_id, RegisteredDevice.deleted_at.is_(None))
        .with_for_update()
        .first()
    )
    if not device:
        raise ValueError(f"Device ID {device_id} not found.")

    if device.revoked_at is not None:
        return device  # Already revoked

    device.revoked_at = now
    device.updated_by = current_user.id

    # Cascade revocation to all active sessions on this device
    active_sessions = (
        db.query(IdentitySession)
        .filter(
            IdentitySession.device_id == device.id,
            IdentitySession.ended_at.is_(None),
            IdentitySession.revoked_at.is_(None),
        )
        .all()
    )
    for s in active_sessions:
        s.revoked_at = now
        s.updated_by = current_user.id
        session_event = SessionRevocationEvent(
            event_code_id=1,  # REVOKED
            actor_user_id=current_user.id,
            occurred_at=now,
            metadata_redacted={"session_id": s.id, "reason": f"Device revocation: {reason}"},
            created_by=current_user.id,
        )
        db.add(session_event)

    # Record DeviceRevocationEvent (FR-0106)
    dev_event = DeviceRevocationEvent(
        event_code_id=1,  # REVOKED
        actor_user_id=current_user.id,
        occurred_at=now,
        metadata_redacted={
            "device_id": device.id,
            "target_user_id": device.user_id,
            "device_label": device.device_label,
            "reason": reason,
        },
        created_by=current_user.id,
    )
    db.add(dev_event)

    # Record Audit Event
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="DEVICE_REVOKED",
        resource_type="registered_device",
        resource_id=str(device.id),
        occurred_at=now,
        metadata_redacted={
            "target_user_id": device.user_id,
            "device_label": device.device_label,
            "terminated_sessions_count": len(active_sessions),
            "reason": reason,
        },
        created_by=current_user.id,
    )
    db.add(audit)
    db.commit()
    db.refresh(device)
    return device


# =========================================================================
# 4. Session Management & Login Device Limits (FR-0101 to FR-0105, FR-0109, FR-0111, FR-0204)
# =========================================================================

def get_user_max_devices(db: Session, user_id: int) -> int:
    """Retrieve the maximum permitted active devices for a user from their active licence seat."""
    allocation = (
        db.query(LicenceSeatAllocation)
        .join(Licence, LicenceSeatAllocation.licence_id == Licence.id)
        .filter(
            LicenceSeatAllocation.user_id == user_id,
            LicenceSeatAllocation.status_code_id == 1,  # ACTIVE
            Licence.status_code_id == 1,  # ACTIVE
            LicenceSeatAllocation.deleted_at.is_(None),
            Licence.deleted_at.is_(None),
        )
        .order_by(Licence.max_devices_per_user.desc())
        .first()
    )
    if allocation and allocation.licence:
        return allocation.licence.max_devices_per_user
    # Default system baseline if no specific licence seat allocated
    return 2


def count_active_sessions(db: Session, user_id: int) -> int:
    """Count active non-expired, non-revoked, non-ended sessions (FR-0101, FR-0102, FR-0103, FR-0109)."""
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(IdentitySession)
        .filter(
            IdentitySession.user_id == user_id,
            IdentitySession.ended_at.is_(None),
            IdentitySession.revoked_at.is_(None),
            IdentitySession.deleted_at.is_(None),
        )
        .all()
    )
    return sum(1 for s in sessions if _ensure_utc(s.expires_at) > now)


def create_user_session(
    db: Session,
    user_id: int,
    payload: SessionCreateRequest,
    actor_user: Optional[User] = None,
) -> IdentitySession:
    """Create a new user session enforcing device limits under transactional row lock (FR-0101, FR-0104, FR-0105)."""
    now = datetime.now(timezone.utc)

    # 1. Acquire concurrency row lock on User row to prevent concurrent login race (FR-0105)
    user = db.query(User).filter(User.id == user_id).with_for_update().first()
    if not user:
        raise ValueError(f"User ID {user_id} not found.")

    # 2. Register or fetch device if fingerprint hash provided
    device_id = payload.device_id
    if payload.device_fingerprint_hash:
        dev_reg = register_device(
            db,
            user_id=user_id,
            payload=DeviceRegisterRequest(
                device_fingerprint_hash=payload.device_fingerprint_hash,
                device_label=payload.device_label,
            ),
            actor_id=actor_user.id if actor_user else user_id,
        )
        device_id = dev_reg.id

    # 3. Check if target device is revoked
    if device_id:
        dev = db.query(RegisteredDevice).filter(RegisteredDevice.id == device_id).first()
        if dev and dev.revoked_at is not None:
            raise ValueError(f"Device ID {device_id} has been revoked; session creation denied.")

    # 4. Check device limits (FR-0101)
    max_devices = get_user_max_devices(db, user_id)
    active_count = count_active_sessions(db, user_id)

    if active_count >= max_devices:
        # Rejection handling: Record decision and audit trail WITHOUT exposing secrets (FR-0111)
        decision = LoginDeviceDecision(
            user_id=user_id,
            status_code_id=2,  # REJECTED
            occurred_at=now,
            created_by=actor_user.id if actor_user else user_id,
        )
        db.add(decision)

        audit = AuditEvent(
            actor_user_id=actor_user.id if actor_user else user_id,
            action_code="LOGIN_DEVICE_LIMIT_EXCEEDED",
            resource_type="registered_device",
            resource_id=str(device_id) if device_id else None,
            occurred_at=now,
            metadata_redacted={
                "target_user_id": user_id,
                "active_sessions_count": active_count,
                "max_devices_permitted": max_devices,
                "outcome": "REJECTED_OVER_DEVICE_LIMIT",
            },
            created_by=actor_user.id if actor_user else user_id,
        )
        db.add(audit)
        db.commit()
        raise ValueError(
            f"Active device limit ({max_devices}) reached for user ID {user_id}. Login denied (FR-0101, FR-0111)."
        )

    # 5. Session Permitted: Record decision and create session
    decision = LoginDeviceDecision(
        user_id=user_id,
        status_code_id=1,  # ALLOWED
        occurred_at=now,
        created_by=actor_user.id if actor_user else user_id,
    )
    db.add(decision)

    session_ref = payload.provider_session_reference or f"sess_{uuid.uuid4().hex}"
    expires_at = now + timedelta(seconds=payload.duration_seconds)

    session = IdentitySession(
        user_id=user_id,
        provider_session_reference=session_ref,
        device_id=device_id,
        started_at=now,
        last_activity_at=now,
        expires_at=expires_at,
        created_by=actor_user.id if actor_user else user_id,
    )
    db.add(session)
    db.flush()

    # Session activity event (FR-0104)
    activity = SessionActivityEvent(
        event_code_id=1,  # LOGIN / CREATED
        actor_user_id=actor_user.id if actor_user else user_id,
        occurred_at=now,
        metadata_redacted={
            "session_id": session.id,
            "device_id": device_id,
            "duration_seconds": payload.duration_seconds,
        },
        created_by=actor_user.id if actor_user else user_id,
    )
    db.add(activity)

    db.commit()
    db.refresh(session)
    return session


def end_user_session(db: Session, current_user: User, session_id: int) -> IdentitySession:
    """Logout / terminate session, immediately releasing active capacity (FR-0109)."""
    now = datetime.now(timezone.utc)

    session = (
        db.query(IdentitySession)
        .filter(IdentitySession.id == session_id, IdentitySession.deleted_at.is_(None))
        .with_for_update()
        .first()
    )
    if not session:
        raise ValueError(f"Session ID {session_id} not found.")

    if session.ended_at is not None:
        return session  # Already ended (idempotent)

    session.ended_at = now
    session.updated_by = current_user.id

    # Record logout activity event
    activity = SessionActivityEvent(
        event_code_id=2,  # LOGOUT / TERMINATED
        actor_user_id=current_user.id,
        occurred_at=now,
        metadata_redacted={"session_id": session.id, "device_id": session.device_id},
        created_by=current_user.id,
    )
    db.add(activity)

    db.commit()
    db.refresh(session)
    return session


def revoke_user_session(db: Session, current_user: User, session_id: int, reason: str) -> IdentitySession:
    """Explicitly revoke a session, invalidating token and releasing capacity (FR-0103)."""
    now = datetime.now(timezone.utc)

    session = (
        db.query(IdentitySession)
        .filter(IdentitySession.id == session_id, IdentitySession.deleted_at.is_(None))
        .with_for_update()
        .first()
    )
    if not session:
        raise ValueError(f"Session ID {session_id} not found.")

    if session.revoked_at is not None:
        return session  # Already revoked (idempotent)

    session.revoked_at = now
    session.updated_by = current_user.id

    # Record SessionRevocationEvent
    rev_event = SessionRevocationEvent(
        event_code_id=1,  # REVOKED
        actor_user_id=current_user.id,
        occurred_at=now,
        metadata_redacted={"session_id": session.id, "reason": reason},
        created_by=current_user.id,
    )
    db.add(rev_event)

    # Record Audit Event
    audit = AuditEvent(
        actor_user_id=current_user.id,
        action_code="SESSION_REVOKED",
        resource_type="identity_session",
        resource_id=str(session.id),
        occurred_at=now,
        metadata_redacted={"target_user_id": session.user_id, "reason": reason},
        created_by=current_user.id,
    )
    db.add(audit)

    db.commit()
    db.refresh(session)
    return session


def update_session_heartbeat(db: Session, session_id: int) -> IdentitySession:
    """Update session last activity timestamp (FR-0104)."""
    now = datetime.now(timezone.utc)
    session = db.query(IdentitySession).filter(IdentitySession.id == session_id).first()
    if not session:
        raise ValueError(f"Session ID {session_id} not found.")
    if session.ended_at is not None or session.revoked_at is not None:
        raise ValueError("Cannot update activity on ended or revoked session.")
    if _ensure_utc(session.expires_at) <= now:
        raise ValueError("Cannot update activity on expired session.")

    session.last_activity_at = now
    db.commit()
    db.refresh(session)
    return session


def cleanup_expired_sessions(db: Session) -> SessionCleanupResponse:
    """Idempotently cleanup expired sessions without corrupting completed ones (FR-0204)."""
    now = datetime.now(timezone.utc)

    # Find expired sessions that have not yet had ended_at set
    candidates = (
        db.query(IdentitySession)
        .filter(
            IdentitySession.ended_at.is_(None),
            IdentitySession.deleted_at.is_(None),
        )
        .all()
    )

    expired_sessions = [s for s in candidates if _ensure_utc(s.expires_at) <= now]
    cleaned_count = len(expired_sessions)
    for s in expired_sessions:
        s.ended_at = s.expires_at

    db.commit()
    return SessionCleanupResponse(
        cleaned_count=cleaned_count,
        timestamp=now,
        status="COMPLETED",
    )
