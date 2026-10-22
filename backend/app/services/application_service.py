"""Job Application Service.

Implements candidate application submission, duplicate prevention, blocking enforcement,
status history auditing, and privacy-preserving retrieval.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.user import User, UserRoleAssignment
from app.models.job import JobRequirement
from app.models.candidate import CandidateProfile, CandidateResume, ResumeVersion
from app.models.application import JobApplication, ApplicationStatusHistory, BlockListEntry
from app.models.organisation import Organisation, OrganisationRecruiterMapping
from app.schemas.application import (
    ApplicationSubmitRequest,
    ApplicationStatusUpdateRequest,
    ApplicationResponse,
    ApplicationListResponse,
)
from app.services.job_service import (
    verify_user_organisation_access,
    OrganisationAccessDeniedError,
)

# Status code mappings for applications
APP_STATUS_ID_TO_CODE = {
    1: "APPLIED",
    2: "SCREENING",
    3: "INTERVIEW",
    4: "OFFERED",
    5: "HIRED",
    6: "REJECTED",
    7: "WITHDRAWN",
}
APP_STATUS_CODE_TO_ID = {v: k for k, v in APP_STATUS_ID_TO_CODE.items()}


class ApplicationServiceError(Exception):
    """Base exception for application errors."""
    pass


class DuplicateApplicationError(ApplicationServiceError):
    """Raised when a candidate attempts to apply twice to the same job."""
    pass


class JobNotOpenForApplicationsError(ApplicationServiceError):
    """Raised when applying to a draft, closed, or deadline-passed job."""
    pass


class CandidateBlockedFromJobError(ApplicationServiceError):
    """Raised when candidate-organisation blocking prevents application."""
    pass


class ApplicationNotFoundError(ApplicationServiceError):
    """Raised when an application is not found or inaccessible."""
    pass


class UnauthorizedApplicationAccessError(PermissionError):
    """Raised when an actor attempts to inspect another candidate's application."""
    pass


def submit_job_application(
    db: Session,
    user: User,
    job_id: int,
    request: ApplicationSubmitRequest,
) -> ApplicationResponse:
    """Submit a new job application for the authenticated candidate."""
    # 1. Resolve candidate profile for this user
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise PermissionError("User does not have an active Candidate profile.")

    # 2. Verify job exists and is open for applications
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise ApplicationNotFoundError(f"Job requirement {job_id} not found.")

    # Check status and publish state (must be OPEN and PUBLISHED)
    if job.publish_state_code_id != 2 or job.status_code_id != 2:
        raise JobNotOpenForApplicationsError(
            f"Job #{job_id} is not currently open for applications (Status: {job.status_code_id}, Publish: {job.publish_state_code_id})."
        )

    # Check application deadline
    now = datetime.now(timezone.utc)
    if job.application_deadline:
        deadline = job.application_deadline if job.application_deadline.tzinfo else job.application_deadline.replace(tzinfo=timezone.utc)
        if deadline < now:
            raise JobNotOpenForApplicationsError(f"Application deadline for Job #{job_id} has expired.")

    # 3. Enforce candidate blocking rules (FR-0052)
    blocked_check = (
        db.query(BlockListEntry)
        .filter(
            BlockListEntry.revoked_at.is_(None),
            or_(
                and_(BlockListEntry.blocker_user_id == user.id, BlockListEntry.blocked_organisation_id == job.organisation_id),
                and_(BlockListEntry.blocked_user_id == user.id, BlockListEntry.blocked_organisation_id == job.organisation_id),
            ),
        )
        .first()
    )
    if blocked_check:
        raise CandidateBlockedFromJobError("Cannot apply: Active blocklist entry between candidate and employer organisation.")

    # 4. Enforce duplicate application prevention (FR-0044, FR-0200)
    existing_app = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_requirement_id == job.id,
            JobApplication.candidate_profile_id == candidate.id,
            JobApplication.deleted_at.is_(None),
            JobApplication.status_code_id != APP_STATUS_CODE_TO_ID["WITHDRAWN"],
        )
        .first()
    )
    if existing_app:
        raise DuplicateApplicationError(
            f"Candidate has already submitted an active application (ID: {existing_app.id}) to Job #{job_id}."
        )

    # 5. Resolve resume version snapshot
    resolved_resume_version_id = request.resume_version_id
    resume_snapshot_title: Optional[str] = None
    resume_snapshot_file_name: Optional[str] = None

    if resolved_resume_version_id:
        rv = (
            db.query(ResumeVersion)
            .join(CandidateResume)
            .filter(
                ResumeVersion.id == resolved_resume_version_id,
                CandidateResume.candidate_profile_id == candidate.id,
            )
            .first()
        )
        if rv:
            resume_snapshot_title = rv.candidate_resume.resume_title if rv.candidate_resume else "Resume"
            resume_snapshot_file_name = rv.file_name or f"resume_v{rv.version_number}.pdf"
    else:
        # Fallback to default resume
        default_resume = (
            db.query(CandidateResume)
            .filter(
                CandidateResume.candidate_profile_id == candidate.id,
                CandidateResume.is_default == True,
                CandidateResume.deleted_at.is_(None),
            )
            .first()
        )
        if default_resume:
            latest_version = (
                db.query(ResumeVersion)
                .filter(
                    ResumeVersion.candidate_resume_id == default_resume.id,
                    ResumeVersion.is_archived == False,
                )
                .order_by(ResumeVersion.version_number.desc())
                .first()
            )
            if latest_version:
                resolved_resume_version_id = latest_version.id
                resume_snapshot_title = default_resume.resume_title
                resume_snapshot_file_name = latest_version.file_name or f"{default_resume.resume_title}_v{latest_version.version_number}.pdf"

    # 6. Evaluate initial eligibility snapshot
    eligibility_status = "ELIGIBLE"
    eligibility_notes = None
    try:
        from app.services.job_service import evaluate_candidate_eligibility
        eval_result = evaluate_candidate_eligibility(db, job.id, candidate.id)
        eligibility_status = eval_result.overall_status
        if eval_result.missing_requirements:
            eligibility_notes = f"Missing: {', '.join(eval_result.missing_requirements)}"
    except Exception:
        pass

    # 7. Create application and initial history record atomically
    applied_status_id = APP_STATUS_CODE_TO_ID["APPLIED"]
    application = JobApplication(
        job_requirement_id=job.id,
        candidate_profile_id=candidate.id,
        applied_at=now,
        status_code_id=applied_status_id,
        resume_version_id=resolved_resume_version_id,
        resume_snapshot_title=resume_snapshot_title,
        resume_snapshot_file_name=resume_snapshot_file_name,
        eligibility_status=eligibility_status,
        eligibility_notes=eligibility_notes,
        cover_letter=request.cover_letter.strip() if request.cover_letter else None,
        last_status_changed_at=now,
        created_by=user.id,
    )
    db.add(application)
    db.flush()  # Generates application.id

    # Append status history audit record (FR-0046)
    history = ApplicationStatusHistory(
        job_application_id=application.id,
        from_status_code_id=None,
        to_status_code_id=applied_status_id,
        changed_by_user_id=user.id,
        changed_at=now,
        created_by=user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(application)

    return format_application_response(application, job, candidate)


def get_application_by_id(
    db: Session,
    user: User,
    application_id: int,
) -> ApplicationResponse:
    """Retrieve application details, verifying caller authorization (Candidate or mapped Recruiter/Employer)."""
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == application_id, JobApplication.deleted_at.is_(None))
        .first()
    )
    if not application:
        raise ApplicationNotFoundError(f"Application {application_id} not found.")

    job = application.job_requirement
    candidate = application.candidate_profile

    # Authorization Check:
    # Option A: Caller is the applicant candidate
    if candidate.user_id == user.id:
        return format_application_response(application, job, candidate)

    # Option B: Caller is an employer or mapped recruiter for the job's organisation
    try:
        verify_user_organisation_access(db, user, job.organisation_id)
        return format_application_response(application, job, candidate)
    except OrganisationAccessDeniedError:
        raise UnauthorizedApplicationAccessError(
            f"Access forbidden: User {user.id} is not authorized to view Application {application_id}."
        )


def list_candidate_applications(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
) -> ApplicationListResponse:
    """List all job applications submitted by the authenticated candidate."""
    candidate = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
    if not candidate:
        raise PermissionError("User does not have an active Candidate profile.")

    query = (
        db.query(JobApplication)
        .filter(
            JobApplication.candidate_profile_id == candidate.id,
            JobApplication.deleted_at.is_(None),
        )
        .order_by(JobApplication.applied_at.desc())
    )

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    applications = query.offset((page - 1) * page_size).limit(page_size).all()
    items = [format_application_response(app, app.job_requirement, candidate) for app in applications]

    return ApplicationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages,
    )


def list_job_applications(
    db: Session,
    user: User,
    job_id: int,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> ApplicationListResponse:
    """List applications for a job requirement, enforcing recruiter company boundary."""
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise ApplicationNotFoundError(f"Job requirement {job_id} not found.")

    # Enforce organisation boundary (FR-0038)
    verify_user_organisation_access(db, user, job.organisation_id)

    query = (
        db.query(JobApplication)
        .filter(
            JobApplication.job_requirement_id == job.id,
            JobApplication.deleted_at.is_(None),
        )
    )

    if status_filter:
        normalized_status = status_filter.strip().upper()
        if normalized_status in APP_STATUS_CODE_TO_ID:
            query = query.filter(JobApplication.status_code_id == APP_STATUS_CODE_TO_ID[normalized_status])

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    applications = query.order_by(JobApplication.applied_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [format_application_response(app, job, app.candidate_profile) for app in applications]

    return ApplicationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages,
    )


def update_application_status(
    db: Session,
    user: User,
    application_id: int,
    request: ApplicationStatusUpdateRequest,
) -> ApplicationResponse:
    """Transition application pipeline status and record immutable status history audit record."""
    application = (
        db.query(JobApplication)
        .filter(JobApplication.id == application_id, JobApplication.deleted_at.is_(None))
        .first()
    )
    if not application:
        raise ApplicationNotFoundError(f"Application {application_id} not found.")

    job = application.job_requirement
    candidate = application.candidate_profile

    target_status = request.status.strip().upper()
    if target_status not in APP_STATUS_CODE_TO_ID:
        raise ValueError(f"Invalid application status '{target_status}'. Must be one of {list(APP_STATUS_CODE_TO_ID.keys())}")

    target_status_id = APP_STATUS_CODE_TO_ID[target_status]

    # Candidate can only WITHDRAW their own application
    if target_status == "WITHDRAWN":
        if candidate.user_id != user.id:
            raise PermissionError("Only the applicant candidate may withdraw their application.")
    else:
        # Recruiter / Employer boundary check
        verify_user_organisation_access(db, user, job.organisation_id)

    from_status_id = application.status_code_id
    now = datetime.now(timezone.utc)

    application.status_code_id = target_status_id
    application.last_status_changed_at = now
    application.updated_by = user.id

    # Append immutable status history
    history = ApplicationStatusHistory(
        job_application_id=application.id,
        from_status_code_id=from_status_id,
        to_status_code_id=target_status_id,
        changed_by_user_id=user.id,
        changed_at=now,
        created_by=user.id,
    )
    db.add(history)
    db.commit()
    db.refresh(application)

    return format_application_response(application, job, candidate)


def format_application_response(
    app: JobApplication,
    job: JobRequirement,
    candidate: CandidateProfile,
) -> ApplicationResponse:
    """Format SQLAlchemy JobApplication into a clean Pydantic response."""
    cand_name = f"{candidate.first_name} {candidate.last_name}".strip()
    status_name = APP_STATUS_ID_TO_CODE.get(app.status_code_id, "APPLIED")
    org_name = job.organisation.display_name if job.organisation else f"Organisation #{job.organisation_id}"

    return ApplicationResponse(
        id=app.id,
        job_requirement_id=job.id,
        job_title=job.title,
        organisation_id=job.organisation_id,
        organisation_name=org_name,
        candidate_profile_id=candidate.id,
        candidate_actor_id=candidate.actor_id,
        candidate_name=cand_name,
        candidate_headline=candidate.headline,
        status=status_name,
        resume_version_id=app.resume_version_id,
        resume_snapshot_title=app.resume_snapshot_title,
        resume_snapshot_file_name=app.resume_snapshot_file_name,
        eligibility_status=app.eligibility_status or "ELIGIBLE",
        eligibility_notes=app.eligibility_notes,
        cover_letter=app.cover_letter,
        applied_at=app.applied_at,
        last_status_changed_at=app.last_status_changed_at,
    )
