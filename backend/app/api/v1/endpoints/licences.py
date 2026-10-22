"""Licences, Seats, Devices & Sessions FastAPI Endpoints (Module M07).

Audited against:
- Talentra Database Blueprint 150+ Tables (Module: M07 Licences, Seats, Devices and Sessions)
- Talentra Final Test Cases: FR-0098 through FR-0111, FR-0204
"""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.licence import (
    LicenceCreate,
    LicenceStatusUpdate,
    LicenceResponse,
    SeatAllocationCreate,
    SeatAllocationResponse,
    DeviceRegisterRequest,
    DeviceRevocationRequest,
    DeviceResponse,
    SessionCreateRequest,
    SessionRevocationRequest,
    SessionResponse,
    SessionCleanupResponse,
    LicenceUsageResponse,
)
from app.services import licence_service

router = APIRouter(prefix="/licences", tags=["Licences, Seats, Devices & Sessions"])


# =========================================================================
# 1. Licence Lifecycle (FR-0098, FR-0099)
# =========================================================================

@router.post("", response_model=LicenceResponse, status_code=status.HTTP_201_CREATED)
def create_licence(
    payload: LicenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0098, FR-0099: Create a subscription licence with positive user and device limits."""
    try:
        licence = licence_service.create_licence(db, current_user, payload)
        return licence_service.get_licence_details(db, licence.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{licence_id}", response_model=LicenceResponse)
def get_licence(
    licence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed licence metrics and seat capacity."""
    try:
        return licence_service.get_licence_details(db, licence_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{licence_id}/status", response_model=LicenceResponse)
def update_licence_status(
    licence_id: int,
    payload: LicenceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update licence lifecycle status (ACTIVE, SUSPENDED, REVOKED, EXPIRED)."""
    try:
        licence = licence_service.update_licence_status(db, current_user, licence_id, payload)
        return licence_service.get_licence_details(db, licence.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 2. Seat Allocation (FR-0100, FR-0107, FR-0110)
# =========================================================================

@router.post("/seats", response_model=SeatAllocationResponse, status_code=status.HTTP_201_CREATED)
def allocate_seat(
    payload: SeatAllocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0100, FR-0107: Concurrency-safe seat allocation under transactional lock and scope check."""
    try:
        allocation = licence_service.allocate_seat(db, current_user, payload)
        return SeatAllocationResponse(
            id=allocation.id,
            licence_id=allocation.licence_id,
            user_id=allocation.user_id,
            status_code_id=allocation.status_code_id,
            status=licence_service.SEAT_STATUS_MAP.get(allocation.status_code_id, "UNKNOWN"),
            occurred_at=allocation.occurred_at,
            expires_at=allocation.expires_at,
            created_at=allocation.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/seats/{allocation_id}", response_model=SeatAllocationResponse)
def release_seat(
    allocation_id: int,
    reason: Optional[str] = Query(None, description="Reason for seat release"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0110: Transactionally release seat, restoring licence capacity immediately."""
    try:
        allocation = licence_service.release_seat(db, current_user, allocation_id, reason)
        return SeatAllocationResponse(
            id=allocation.id,
            licence_id=allocation.licence_id,
            user_id=allocation.user_id,
            status_code_id=allocation.status_code_id,
            status=licence_service.SEAT_STATUS_MAP.get(allocation.status_code_id, "UNKNOWN"),
            occurred_at=allocation.occurred_at,
            expires_at=allocation.expires_at,
            created_at=allocation.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 3. Device Registration & Revocation (FR-0101, FR-0106, FR-0108)
# =========================================================================

@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0108: Idempotent device registration using SHA-256 fingerprint hash."""
    try:
        device = licence_service.register_device(db, current_user.id, payload)
        return DeviceResponse(
            id=device.id,
            user_id=device.user_id,
            device_fingerprint_hash=device.device_fingerprint_hash,
            device_label=device.device_label,
            first_seen_at=device.first_seen_at,
            last_seen_at=device.last_seen_at,
            revoked_at=device.revoked_at,
            is_active=device.revoked_at is None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/devices/{device_id}/revoke", response_model=DeviceResponse)
def revoke_device(
    device_id: int,
    payload: DeviceRevocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0106: Revoke registered device and terminate all its linked active sessions."""
    try:
        device = licence_service.revoke_device(db, current_user, device_id, payload.reason)
        return DeviceResponse(
            id=device.id,
            user_id=device.user_id,
            device_fingerprint_hash=device.device_fingerprint_hash,
            device_label=device.device_label,
            first_seen_at=device.first_seen_at,
            last_seen_at=device.last_seen_at,
            revoked_at=device.revoked_at,
            is_active=device.revoked_at is None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 4. Session Governance (FR-0101 to FR-0105, FR-0109, FR-0111, FR-0204)
# =========================================================================

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0101, FR-0104, FR-0105: Create session with concurrency-safe device limit check."""
    try:
        session = licence_service.create_user_session(db, current_user.id, payload, actor_user=current_user)
        now = datetime.now(timezone.utc)
        is_active = session.ended_at is None and session.revoked_at is None and licence_service._ensure_utc(session.expires_at) > now
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            device_label=payload.device_label,
            provider_session_reference=session.provider_session_reference,
            started_at=session.started_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ended_at=session.ended_at,
            revoked_at=session.revoked_at,
            is_active=is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/sessions/{session_id}/heartbeat", response_model=SessionResponse)
def session_heartbeat(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0104: Record heartbeat activity updating last_activity_at."""
    try:
        session = licence_service.update_session_heartbeat(db, session_id)
        now = datetime.now(timezone.utc)
        is_active = session.ended_at is None and session.revoked_at is None and licence_service._ensure_utc(session.expires_at) > now
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            provider_session_reference=session.provider_session_reference,
            started_at=session.started_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ended_at=session.ended_at,
            revoked_at=session.revoked_at,
            is_active=is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0109: Logout / end session, releasing active session capacity."""
    try:
        session = licence_service.end_user_session(db, current_user, session_id)
        now = datetime.now(timezone.utc)
        is_active = session.ended_at is None and session.revoked_at is None and licence_service._ensure_utc(session.expires_at) > now
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            provider_session_reference=session.provider_session_reference,
            started_at=session.started_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ended_at=session.ended_at,
            revoked_at=session.revoked_at,
            is_active=is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sessions/{session_id}/revoke", response_model=SessionResponse)
def revoke_session(
    session_id: int,
    payload: SessionRevocationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0103: Revoke session, invalidating token and releasing device capacity."""
    try:
        session = licence_service.revoke_user_session(db, current_user, session_id, payload.reason)
        now = datetime.now(timezone.utc)
        is_active = session.ended_at is None and session.revoked_at is None and licence_service._ensure_utc(session.expires_at) > now
        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            device_id=session.device_id,
            provider_session_reference=session.provider_session_reference,
            started_at=session.started_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ended_at=session.ended_at,
            revoked_at=session.revoked_at,
            is_active=is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sessions/cleanup", response_model=SessionCleanupResponse)
def cleanup_expired_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0204: Idempotently clean up expired sessions."""
    return licence_service.cleanup_expired_sessions(db)
