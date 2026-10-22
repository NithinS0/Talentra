"""Sourcing and Consultant Requests API Endpoints.

Implements M08 Sourcing & External Consultants:
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

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
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
from app.services.sourcing_service import (
    create_sourcing_request,
    consultant_respond_to_request,
    employer_decline_consultant,
    cancel_sourcing_request,
    list_sourcing_requests,
    add_candidate_to_shortlist,
    list_candidate_shortlists,
    create_outreach_batch,
    process_delivery_callback,
    get_candidate_for_consultant,
    SourcingServiceError,
)

router = APIRouter(prefix="/sourcing", tags=["Sourcing & Consultant Requests"])


@router.post(
    "/requests",
    response_model=SourcingRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sourcing request (FR-0112, FR-0123)",
)
def create_sourcing_request_endpoint(
    request: SourcingRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a candidate sourcing request linked to a job requirement."""
    try:
        return create_sourcing_request(db=db, user=current_user, request=request)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except SourcingServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/requests",
    response_model=SourcingRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="List sourcing requests",
)
def list_sourcing_requests_endpoint(
    job_requirement_id: Optional[int] = Query(default=None),
    organisation_id: Optional[int] = Query(default=None),
    status_code_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sourcing requests scoped to the authenticated caller."""
    try:
        return list_sourcing_requests(
            db=db,
            user=current_user,
            job_requirement_id=job_requirement_id,
            organisation_id=organisation_id,
            status_code_id=status_code_id,
            page=page,
            page_size=page_size,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/requests/{request_id}/respond",
    response_model=SourcingRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultant respond to request (Accept/Decline) (FR-0113, FR-0114)",
)
def consultant_respond_endpoint(
    request_id: int,
    decision: SourcingRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Consultant accepts or declines sourcing request subject to openness verification."""
    try:
        return consultant_respond_to_request(
            db=db,
            consultant_user=current_user,
            request_id=request_id,
            decision_payload=decision,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post(
    "/requests/{request_id}/decline-consultant",
    response_model=SourcingRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Employer decline consultant request (FR-0115)",
)
def employer_decline_consultant_endpoint(
    request_id: int,
    reason: Optional[str] = Query(default=None, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer declines consultant request within company boundaries."""
    try:
        return employer_decline_consultant(
            db=db,
            employer_user=current_user,
            request_id=request_id,
            reason=reason,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post(
    "/requests/{request_id}/cancel",
    response_model=SourcingRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel sourcing request (FR-0122)",
)
def cancel_sourcing_request_endpoint(
    request_id: int,
    cancel_payload: Optional[SourcingRequestCancel] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Employer cancels active sourcing request without erasing decision history."""
    payload = cancel_payload or SourcingRequestCancel()
    try:
        return cancel_sourcing_request(
            db=db,
            user=current_user,
            request_id=request_id,
            cancel_payload=payload,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post(
    "/shortlists",
    response_model=CandidateShortlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add candidate to shortlist (FR-0116)",
)
def add_to_shortlist_endpoint(
    payload: CandidateShortlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a candidate to the sourcing shortlist."""
    try:
        return add_candidate_to_shortlist(db=db, user=current_user, payload=payload)
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/shortlists",
    response_model=CandidateShortlistListResponse,
    status_code=status.HTTP_200_OK,
    summary="List candidate shortlists",
)
def list_shortlists_endpoint(
    status_code_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List shortlists for current user."""
    return list_candidate_shortlists(
        db=db,
        user=current_user,
        status_code_id=status_code_id,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/outreach/batches",
    response_model=OutreachBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Launch bulk outreach batch (FR-0117, FR-0118, FR-0120, FR-0205)",
)
def create_outreach_batch_endpoint(
    payload: OutreachBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Launch bulk candidate outreach campaign with recruiter assignment, blocklist, and consent suppression."""
    try:
        return create_outreach_batch(db=db, user=current_user, payload=payload)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post(
    "/outreach/callbacks",
    response_model=OutreachRecipientResponse,
    status_code=status.HTTP_200_OK,
    summary="Provider delivery callback (FR-0119)",
)
def delivery_callback_endpoint(
    callback: OutreachDeliveryCallback,
    db: Session = Depends(get_db),
):
    """Process provider webhook delivery callback idempotently."""
    try:
        return process_delivery_callback(db=db, callback=callback)
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/candidates/{candidate_profile_id}",
    response_model=ConsultantCandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultant privacy-preserving candidate profile view (FR-0121)",
)
def get_candidate_profile_consultant_endpoint(
    candidate_profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View candidate profile with sensitive contact fields masked and blocklist checked."""
    try:
        return get_candidate_for_consultant(
            db=db,
            consultant_user=current_user,
            candidate_profile_id=candidate_profile_id,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
