"""Gig Marketplace FastAPI Endpoints (Module M06).

Audited against:
- Talentra Database Blueprint 150+ Tables (Module: M06 Gig Marketplace)
- Talentra Final Test Cases: FR-0084 through FR-0097, FR-0203
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.gig import (
    GigWorkerProfileCreate,
    GigWorkerProfileResponse,
    GigRequestCreate,
    GigRequestCancel,
    GigRequestResponse,
    GigRequestListResponse,
    GigApplicationCreate,
    GigApplicationDecision,
    GigApplicationResponse,
    GigAssignmentResponse,
    GigWorkerAvailabilityCreate,
    GigWorkerAvailabilityResponse,
    GigEarningsEventCreate,
    GigEarningsResponse,
    GigWorkerListEntryCreate,
    GigWorkerListEntryResponse,
    GigRatingCreate,
    GigRatingResponse,
)
from app.services import gig_service

router = APIRouter(prefix="/gig", tags=["Gig Marketplace"])


# ==========================================
# 1. Gig Worker Profile (FR-0084)
# ==========================================

@router.post("/workers/profile", response_model=GigWorkerProfileResponse, status_code=status.HTTP_201_CREATED)
def create_gig_worker_profile(
    payload: GigWorkerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0084: Create separate gig worker profile distinct from permanent candidates."""
    try:
        return gig_service.create_gig_worker_profile(db, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/workers/profile", response_model=GigWorkerProfileResponse)
def get_current_gig_worker_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the current user's gig worker profile."""
    try:
        return gig_service.get_gig_worker_profile(db, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==========================================
# 2. Gig Worker Availability (FR-0090)
# ==========================================

@router.post("/workers/availability", response_model=GigWorkerAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def set_gig_worker_availability(
    payload: GigWorkerAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0090: Set availability window with date and overlap conflict validation."""
    try:
        return gig_service.set_worker_availability(db, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# 3. Gig Requests (FR-0085, FR-0086, FR-0097, FR-0203)
# ==========================================

@router.post("/requests", response_model=GigRequestResponse, status_code=status.HTTP_201_CREATED)
def create_gig_request(
    payload: GigRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0085, FR-0086, FR-0203: Create gig request with validated pricing, currency, and date window."""
    try:
        return gig_service.create_gig_request(db, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/requests", response_model=GigRequestListResponse)
def list_gig_requests(
    organisation_id: Optional[int] = Query(None),
    status_code_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List gig requests with optional organisation and status filtering."""
    return gig_service.list_gig_requests(db, organisation_id, status_code_id, skip, limit)


@router.post("/requests/{request_id}/cancel", response_model=GigRequestResponse)
def cancel_gig_request(
    request_id: int,
    payload: GigRequestCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0097: Cancel gig request in permitted states and retain status history."""
    try:
        return gig_service.cancel_gig_request(db, request_id, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# 4. Gig Applications & Decisions (FR-0087, FR-0088, FR-0089, FR-0091)
# ==========================================

@router.post("/requests/{request_id}/apply", response_model=GigApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_gig_request(
    request_id: int,
    payload: GigApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0087: Gig worker applies to request; bids do not flow in reverse."""
    try:
        return gig_service.apply_to_gig_request(db, request_id, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/applications/{application_id}/decision", response_model=GigApplicationResponse)
def decide_gig_application(
    application_id: int,
    payload: GigApplicationDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0088, FR-0089, FR-0091: Requester decides gig application with overlapping assignment prevention."""
    try:
        app_res, _ = gig_service.decide_gig_application(db, application_id, current_user, payload)
        return app_res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# 5. External Earnings Reconciliation (FR-0092)
# ==========================================

@router.post("/earnings/reconciliation", response_model=GigEarningsResponse)
def reconcile_gig_earnings(
    payload: GigEarningsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0092: Reconcile earnings originating from external system boundary idempotently."""
    try:
        return gig_service.reconcile_gig_earnings(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ==========================================
# 6. Favourite & Blacklist Exclusivity (FR-0093, FR-0095)
# ==========================================

@router.post("/organisations/{organisation_id}/worker-lists", response_model=GigWorkerListEntryResponse, status_code=status.HTTP_201_CREATED)
def manage_worker_list_entry(
    organisation_id: int,
    payload: GigWorkerListEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0093: Manage favourite or blacklist entry enforcing mutual exclusivity."""
    try:
        return gig_service.manage_worker_list_entry(db, current_user, organisation_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/organisations/{organisation_id}/blacklisted-workers", response_model=List[GigWorkerListEntryResponse])
def list_blacklisted_workers(
    organisation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0095: Blacklists are restricted to authorized owner/admin workflows."""
    try:
        return gig_service.list_requester_blacklisted_workers(db, current_user, organisation_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# 7. Completed Gig Rating (FR-0094)
# ==========================================

@router.post("/ratings", response_model=GigRatingResponse, status_code=status.HTTP_201_CREATED)
def rate_completed_gig(
    payload: GigRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0094: Ratings are allowed only for completed gigs within defined scale (1.00 - 5.00)."""
    try:
        return gig_service.rate_completed_gig(db, current_user, payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# 8. External Provider Outage Resilience (FR-0096)
# ==========================================

@router.post("/assignments/{assignment_id}/outage-test", response_model=GigAssignmentResponse)
def handle_provider_outage_simulation(
    assignment_id: int,
    error_message: str = Query("External fulfilment gateway connection timed out (HTTP 503)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0096: External outage must not falsely advance assignment state."""
    try:
        return gig_service.handle_external_provider_outage(db, assignment_id, error_message)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
