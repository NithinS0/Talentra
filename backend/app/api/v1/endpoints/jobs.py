"""Job Requisition and Management Endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobStatusUpdateRequest,
    JobResponse,
    JobListResponse,
    JobEligibilityResponse,
)
from app.models.candidate import CandidateProfile
from app.schemas.application import ApplicationListResponse
from app.services.job_service import (
    create_job_requirement,
    update_job_requirement,
    update_job_status,
    get_job_by_id,
    list_jobs,
    evaluate_candidate_eligibility,
    JobNotFoundError,
    OrganisationAccessDeniedError,
    InvalidJobStatusTransitionError,
)
from app.services.application_service import list_job_applications

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Jobs & Requirements"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Job Requirement",
    description="Creates a new job requirement. Caller must be an authorized Employer or Recruiter mapped to the organisation.",
)
def create_job(
    request: JobCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create job requirement endpoint."""
    try:
        job = create_job_requirement(db, current_user, request)
        return job
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error creating job: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create job requirement.")


@router.get(
    "",
    response_model=JobListResponse,
    summary="List and Search Job Requirements",
    description="Public and candidate job discovery. Supports full-text search, filtering by role, employment type, work type, and organisation. Excludes unpublished and blocked jobs.",
)
def get_jobs(
    search: Optional[str] = Query(default=None, description="Keywords to match in title or description"),
    organisation_id: Optional[int] = Query(default=None, description="Filter by organisation ID"),
    job_role_id: Optional[int] = Query(default=None, description="Filter by job role ID"),
    employment_type_id: Optional[int] = Query(default=None, description="Filter by employment type ID"),
    work_type_id: Optional[int] = Query(default=None, description="Filter by work type ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List and search jobs endpoint."""
    return list_jobs(
        db=db,
        current_user=None,
        organisation_id=organisation_id,
        job_role_id=job_role_id,
        employment_type_id=employment_type_id,
        work_type_id=work_type_id,
        search=search,
        only_published=True,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get Job Requirement Details",
    description="Returns detailed job requirement data.",
)
def get_job_details(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get single job requirement details."""
    try:
        return get_job_by_id(db, job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update Job Requirement",
    description="Update job details. Caller must be an authorized Employer or mapped Recruiter.",
)
def update_job(
    job_id: int,
    request: JobUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update job requirement endpoint."""
    try:
        return update_job_requirement(db, current_user, job_id, request)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch(
    "/{job_id}/status",
    response_model=JobResponse,
    summary="Change Job Status / Publish State",
    description="Transition job status (DRAFT, OPEN, CLOSED, CANCELLED) or publish state (PUBLISHED, ARCHIVED).",
)
def change_job_status(
    job_id: int,
    request: JobStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change job status endpoint."""
    try:
        return update_job_status(db, current_user, job_id, request)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidJobStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{job_id}/applications",
    response_model=ApplicationListResponse,
    summary="List Applications for a Job",
    description="Returns submitted applications for a specific job requirement. Restricted to the employer organisation and its mapped recruiters.",
)
def get_job_applications(
    job_id: int,
    status: Optional[str] = Query(default=None, description="Optional status filter"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List applications for a job endpoint."""
    try:
        return list_job_applications(db, current_user, job_id, status_filter=status, page=page, page_size=page_size)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/{job_id}/eligibility",
    response_model=JobEligibilityResponse,
    summary="Evaluate Candidate Eligibility",
    description="Evaluates a candidate against the structured requirements of this job requisition.",
)
def get_job_eligibility(
    job_id: int,
    candidate_id: Optional[int] = Query(default=None, description="Optional candidate profile ID for recruiter/employer review"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Evaluate candidate eligibility endpoint."""
    target_candidate_id = candidate_id
    if target_candidate_id is None:
        # Check if caller is candidate
        cand = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()
        if not cand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No candidate profile associated with current user. Please provide candidate_id query parameter.",
            )
        target_candidate_id = cand.id

    try:
        return evaluate_candidate_eligibility(db, job_id, target_candidate_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

