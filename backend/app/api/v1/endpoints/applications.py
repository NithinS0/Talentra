"""Job Application and Candidate Pipeline Endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.application import (
    ApplicationSubmitRequest,
    ApplicationStatusUpdateRequest,
    ApplicationResponse,
    ApplicationListResponse,
)
from app.services.application_service import (
    submit_job_application,
    get_application_by_id,
    list_candidate_applications,
    update_application_status,
    DuplicateApplicationError,
    JobNotOpenForApplicationsError,
    CandidateBlockedFromJobError,
    ApplicationNotFoundError,
    UnauthorizedApplicationAccessError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Applications & Pipeline"])


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a Job Requirement",
    description="Submits a job application for the authenticated Candidate. Enforces availability, duplicate prevention, and blocking checks.",
)
def apply_to_job(
    job_id: int,
    request: ApplicationSubmitRequest,
    current_user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """Candidate job application submission endpoint."""
    try:
        return submit_job_application(db, current_user, job_id, request)
    except DuplicateApplicationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except JobNotOpenForApplicationsError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except CandidateBlockedFromJobError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error applying to job: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit application.")


@router.get(
    "/applications/me",
    response_model=ApplicationListResponse,
    summary="List My Applications",
    description="Returns all job applications submitted by the authenticated Candidate.",
)
def get_my_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_role("CANDIDATE")),
    db: Session = Depends(get_db),
):
    """List current candidate's submitted applications."""
    try:
        return list_candidate_applications(db, current_user, page=page, page_size=page_size)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/applications/{application_id}",
    response_model=ApplicationResponse,
    summary="Get Application Details",
    description="Retrieves a specific application. Caller must be the candidate or an authorized employer/recruiter for the job.",
)
def get_single_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single application details endpoint."""
    try:
        return get_application_by_id(db, current_user, application_id)
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedApplicationAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update Application Status",
    description="Transitions an application's status (SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN) and records an immutable audit history record.",
)
def change_application_status(
    application_id: int,
    request: ApplicationStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update application pipeline status endpoint."""
    try:
        return update_application_status(db, current_user, application_id, request)
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedApplicationAccessError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
