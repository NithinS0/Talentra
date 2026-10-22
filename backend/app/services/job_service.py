"""Job Management and Discovery Service.

Implements job requirement lifecycle, publisher transitions, recruiter company scoping,
and candidate search with blocking exclusion.
"""

from typing import Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_

from app.models.user import User, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Organisation, OrganisationRecruiterMapping
from app.models.job import JobRequirement, JobPosition, JobRole, EmploymentType, WorkType
from app.models.application import JobApplication, BlockListEntry
from app.models.candidate import CandidateProfile
from app.schemas.job import (
    JobCreateRequest,
    JobUpdateRequest,
    JobStatusUpdateRequest,
    JobResponse,
    JobListResponse,
    JobEligibilityResponse,
    CriterionResult,
)

# Status code mappings
STATUS_ID_TO_CODE = {1: "DRAFT", 2: "OPEN", 3: "CLOSED", 4: "CANCELLED"}
STATUS_CODE_TO_ID = {v: k for k, v in STATUS_ID_TO_CODE.items()}

PUBLISH_ID_TO_CODE = {1: "UNPUBLISHED", 2: "PUBLISHED", 3: "ARCHIVED"}
PUBLISH_CODE_TO_ID = {v: k for k, v in PUBLISH_ID_TO_CODE.items()}


class JobServiceError(Exception):
    """Base exception for job operations."""
    pass


class OrganisationAccessDeniedError(PermissionError):
    """Raised when an actor attempts cross-organisation job operations."""
    pass


class InvalidJobStatusTransitionError(ValueError):
    """Raised when an illegal status lifecycle transition is requested."""
    pass


class JobNotFoundError(ValueError):
    """Raised when a job requirement does not exist."""
    pass


def verify_user_organisation_access(
    db: Session,
    user: User,
    organisation_id: int,
) -> None:
    """Verify that the user is authorized to create/manage jobs for the specified organisation.
    
    Admins and Super Admins have global authority.
    Employers must have an active identity/assignment for the organisation.
    Recruiters must have a valid mapping in organisation_recruiter_mapping.
    """
    # Check for Admin or Super Admin
    is_admin = (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code.in_(["SUPER_ADMIN", "ADMIN"])),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if is_admin:
        return

    # Check Employer role for this organisation
    employer_assignment = (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code.in_(["EMPLOYER", "ACCOUNT_ADMIN"])),
            UserRoleAssignment.organisation_id == organisation_id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if employer_assignment:
        return

    # Check Recruiter company mapping
    now = datetime.now(timezone.utc)
    recruiter_mapping = (
        db.query(OrganisationRecruiterMapping)
        .filter(
            OrganisationRecruiterMapping.recruiter_user_id == user.id,
            OrganisationRecruiterMapping.organisation_id == organisation_id,
            OrganisationRecruiterMapping.valid_from <= now,
            or_(
                OrganisationRecruiterMapping.valid_until.is_(None),
                OrganisationRecruiterMapping.valid_until > now,
            ),
            OrganisationRecruiterMapping.deleted_at.is_(None),
        )
        .first()
    )
    if recruiter_mapping:
        return

    # Also check if actor identity holds this organisation
    actor_identity = (
        db.query(UserActorIdentity)
        .filter(
            UserActorIdentity.user_id == user.id,
            UserActorIdentity.organisation_id == organisation_id,
            UserActorIdentity.is_active.is_(True),
        )
        .first()
    )
    if actor_identity:
        return

    raise OrganisationAccessDeniedError(
        f"Access denied: User {user.id} is not mapped or authorized for organisation {organisation_id}."
    )


def create_job_requirement(
    db: Session,
    user: User,
    request: JobCreateRequest,
) -> JobResponse:
    """Create a new job requirement with authoring security verification."""
    # 1. Enforce organisation boundary
    verify_user_organisation_access(db, user, request.organisation_id)

    # 2. Verify organisation exists and is active
    org = db.query(Organisation).filter(Organisation.id == request.organisation_id).first()
    if not org:
        raise ValueError(f"Organisation {request.organisation_id} not found.")

    if org.status_code_id == 3 or org.deleted_at is not None:
        raise ValueError(f"Cannot create job requirement: Organisation {org.id} is deactivated or deleted.")

    # 3. Determine status and publish state
    status_id = STATUS_CODE_TO_ID["OPEN"] if request.publish_now else STATUS_CODE_TO_ID["DRAFT"]
    publish_id = PUBLISH_CODE_TO_ID["PUBLISHED"] if request.publish_now else PUBLISH_CODE_TO_ID["UNPUBLISHED"]

    job = JobRequirement(
        organisation_id=request.organisation_id,
        created_by_user_id=user.id,
        job_role_id=request.job_role_id,
        title=request.title.strip(),
        description=request.description.strip(),
        employment_type_id=request.employment_type_id,
        work_type_id=request.work_type_id,
        status_code_id=status_id,
        publish_state_code_id=publish_id,
        open_to_consultants=request.open_to_consultants,
        positions_count=request.positions_count,
        salary_min=request.salary_min,
        salary_max=request.salary_max,
        salary_currency_code=request.salary_currency_code.upper() if request.salary_currency_code else "INR",
        application_deadline=request.application_deadline,
        responsibilities=request.responsibilities.strip() if request.responsibilities else None,
        required_skills=request.required_skills.strip() if request.required_skills else None,
        preferred_skills=request.preferred_skills.strip() if request.preferred_skills else None,
        required_qualifications=request.required_qualifications.strip() if request.required_qualifications else None,
        accepted_branches=request.accepted_branches.strip() if request.accepted_branches else None,
        min_percentage=request.min_percentage,
        min_cgpa=request.min_cgpa,
        allow_backlogs=request.allow_backlogs,
        max_active_backlogs=request.max_active_backlogs,
        min_experience_years=request.min_experience_years,
        max_experience_years=request.max_experience_years,
        location_city=request.location_city.strip() if request.location_city else None,
        location_country=request.location_country.strip() if request.location_country else None,
        required_documents=request.required_documents.strip() if request.required_documents else None,
        created_by=user.id,
    )
    db.add(job)
    db.flush()

    # Create associated default position record
    pos = JobPosition(
        job_requirement_id=job.id,
        position_code=f"POS-{job.id}-01",
        title=job.title,
        headcount=job.positions_count,
        filled_count=0,
        created_by=user.id,
    )
    db.add(pos)
    db.commit()
    db.refresh(job)

    return format_job_response(db, job)


def update_job_requirement(
    db: Session,
    user: User,
    job_id: int,
    request: JobUpdateRequest,
) -> JobResponse:
    """Update job requirement attributes."""
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise JobNotFoundError(f"Job requirement {job_id} not found.")

    # Enforce organisation boundary
    verify_user_organisation_access(db, user, job.organisation_id)

    if request.title is not None:
        job.title = request.title.strip()
    if request.description is not None:
        job.description = request.description.strip()
    if request.employment_type_id is not None:
        job.employment_type_id = request.employment_type_id
    if request.work_type_id is not None:
        job.work_type_id = request.work_type_id
    if request.positions_count is not None:
        job.positions_count = request.positions_count
    if request.salary_min is not None:
        job.salary_min = request.salary_min
    if request.salary_max is not None:
        job.salary_max = request.salary_max
    if request.salary_currency_code is not None:
        job.salary_currency_code = request.salary_currency_code.upper()
    if request.application_deadline is not None:
        job.application_deadline = request.application_deadline
    if request.open_to_consultants is not None:
        job.open_to_consultants = request.open_to_consultants
    if request.responsibilities is not None:
        job.responsibilities = request.responsibilities.strip() if request.responsibilities else None
    if request.required_skills is not None:
        job.required_skills = request.required_skills.strip() if request.required_skills else None
    if request.preferred_skills is not None:
        job.preferred_skills = request.preferred_skills.strip() if request.preferred_skills else None
    if request.required_qualifications is not None:
        job.required_qualifications = request.required_qualifications.strip() if request.required_qualifications else None
    if request.accepted_branches is not None:
        job.accepted_branches = request.accepted_branches.strip() if request.accepted_branches else None
    if request.min_percentage is not None:
        job.min_percentage = request.min_percentage
    if request.min_cgpa is not None:
        job.min_cgpa = request.min_cgpa
    if request.allow_backlogs is not None:
        job.allow_backlogs = request.allow_backlogs
    if request.max_active_backlogs is not None:
        job.max_active_backlogs = request.max_active_backlogs
    if request.min_experience_years is not None:
        job.min_experience_years = request.min_experience_years
    if request.max_experience_years is not None:
        job.max_experience_years = request.max_experience_years
    if request.location_city is not None:
        job.location_city = request.location_city.strip() if request.location_city else None
    if request.location_country is not None:
        job.location_country = request.location_country.strip() if request.location_country else None
    if request.required_documents is not None:
        job.required_documents = request.required_documents.strip() if request.required_documents else None

    job.updated_by = user.id
    db.commit()
    db.refresh(job)
    return format_job_response(db, job)


def update_job_status(
    db: Session,
    user: User,
    job_id: int,
    request: JobStatusUpdateRequest,
) -> JobResponse:
    """Transition job status and publish state."""
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise JobNotFoundError(f"Job requirement {job_id} not found.")

    verify_user_organisation_access(db, user, job.organisation_id)

    if request.status:
        target_status = request.status.strip().upper()
        if target_status not in STATUS_CODE_TO_ID:
            raise InvalidJobStatusTransitionError(f"Invalid status '{target_status}'. Must be one of {list(STATUS_CODE_TO_ID.keys())}")
        job.status_code_id = STATUS_CODE_TO_ID[target_status]

    if request.publish_state:
        target_publish = request.publish_state.strip().upper()
        if target_publish not in PUBLISH_CODE_TO_ID:
            raise InvalidJobStatusTransitionError(f"Invalid publish state '{target_publish}'. Must be one of {list(PUBLISH_CODE_TO_ID.keys())}")
        job.publish_state_code_id = PUBLISH_CODE_TO_ID[target_publish]

    job.updated_by = user.id
    db.commit()
    db.refresh(job)
    return format_job_response(db, job)


def get_job_by_id(
    db: Session,
    job_id: int,
    current_user: Optional[User] = None,
) -> JobResponse:
    """Retrieve details for a single job requirement, respecting candidate blocking."""
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise JobNotFoundError(f"Job requirement {job_id} not found.")

    # Check candidate block visibility if caller is a candidate
    if current_user:
        is_blocked = (
            db.query(BlockListEntry)
            .filter(
                BlockListEntry.revoked_at.is_(None),
                or_(
                    and_(BlockListEntry.blocker_user_id == current_user.id, BlockListEntry.blocked_organisation_id == job.organisation_id),
                    and_(BlockListEntry.blocked_user_id == current_user.id, BlockListEntry.blocked_organisation_id == job.organisation_id),
                )
            )
            .first()
        )
        if is_blocked:
            raise JobNotFoundError("Job requirement not found or inaccessible.")

    return format_job_response(db, job)


def list_jobs(
    db: Session,
    current_user: Optional[User] = None,
    organisation_id: Optional[int] = None,
    job_role_id: Optional[int] = None,
    employment_type_id: Optional[int] = None,
    work_type_id: Optional[int] = None,
    search: Optional[str] = None,
    only_published: bool = True,
    page: int = 1,
    page_size: int = 20,
) -> JobListResponse:
    """Search and list job requirements with pagination, filtering, and candidate blocking exclusion."""
    query = db.query(JobRequirement).filter(JobRequirement.deleted_at.is_(None))

    # Candidate / Public view filters to published and open jobs
    if only_published:
        now = datetime.now(timezone.utc)
        query = query.filter(
            JobRequirement.publish_state_code_id == PUBLISH_CODE_TO_ID["PUBLISHED"],
            JobRequirement.status_code_id == STATUS_CODE_TO_ID["OPEN"],
            or_(
                JobRequirement.application_deadline.is_(None),
                JobRequirement.application_deadline > now,
            )
        )

    # Filter by organisation
    if organisation_id:
        query = query.filter(JobRequirement.organisation_id == organisation_id)

    # Filter by job role
    if job_role_id:
        query = query.filter(JobRequirement.job_role_id == job_role_id)

    # Filter by employment type
    if employment_type_id:
        query = query.filter(JobRequirement.employment_type_id == employment_type_id)

    # Filter by work type
    if work_type_id:
        query = query.filter(JobRequirement.work_type_id == work_type_id)

    # Text search on title or description
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                JobRequirement.title.ilike(search_pattern),
                JobRequirement.description.ilike(search_pattern),
            )
        )

    # Candidate Blocking: exclude organisations blocked by or blocking the current candidate
    if current_user:
        blocked_org_ids = (
            db.query(BlockListEntry.blocked_organisation_id)
            .filter(
                BlockListEntry.blocker_user_id == current_user.id,
                BlockListEntry.blocked_organisation_id.isnot(None),
                BlockListEntry.revoked_at.is_(None),
            )
            .all()
        )
        blocked_ids = [b[0] for b in blocked_org_ids if b[0] is not None]
        if blocked_ids:
            query = query.filter(JobRequirement.organisation_id.notin_(blocked_ids))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    jobs = (
        query.order_by(JobRequirement.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [format_job_response(db, j) for j in jobs]
    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages,
    )


def format_job_response(db: Session, job: JobRequirement) -> JobResponse:
    """Format SQLAlchemy JobRequirement into a clean Pydantic response."""
    org_name = job.organisation.display_name if job.organisation else f"Organisation #{job.organisation_id}"
    role_name = job.job_role.name if job.job_role else f"Role #{job.job_role_id}"
    emp_type = job.employment_type.name if job.employment_type else "Full-time"
    work_type = job.work_type.name if job.work_type else "On-site"

    app_count = db.query(func.count(JobApplication.id)).filter(
        JobApplication.job_requirement_id == job.id,
        JobApplication.deleted_at.is_(None)
    ).scalar() or 0

    return JobResponse(
        id=job.id,
        organisation_id=job.organisation_id,
        organisation_name=org_name,
        job_role_id=job.job_role_id,
        job_role_name=role_name,
        title=job.title,
        description=job.description,
        employment_type_id=job.employment_type_id,
        employment_type=emp_type,
        work_type_id=job.work_type_id,
        work_type=work_type,
        status=STATUS_ID_TO_CODE.get(job.status_code_id, "DRAFT"),
        publish_state=PUBLISH_ID_TO_CODE.get(job.publish_state_code_id, "UNPUBLISHED"),
        open_to_consultants=job.open_to_consultants,
        positions_count=job.positions_count,
        salary_min=float(job.salary_min) if job.salary_min is not None else None,
        salary_max=float(job.salary_max) if job.salary_max is not None else None,
        salary_currency_code=job.salary_currency_code,
        application_deadline=job.application_deadline,
        applications_count=app_count,
        responsibilities=job.responsibilities,
        required_skills=job.required_skills,
        preferred_skills=job.preferred_skills,
        required_qualifications=job.required_qualifications,
        accepted_branches=job.accepted_branches,
        min_percentage=float(job.min_percentage) if job.min_percentage is not None else None,
        min_cgpa=float(job.min_cgpa) if job.min_cgpa is not None else None,
        allow_backlogs=job.allow_backlogs if job.allow_backlogs is not None else False,
        max_active_backlogs=job.max_active_backlogs if job.max_active_backlogs is not None else 0,
        min_experience_years=float(job.min_experience_years) if job.min_experience_years is not None else None,
        max_experience_years=float(job.max_experience_years) if job.max_experience_years is not None else None,
        location_city=job.location_city,
        location_country=job.location_country,
        required_documents=job.required_documents,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def evaluate_candidate_eligibility(
    db: Session,
    job_id: int,
    candidate_profile_id: int,
) -> JobEligibilityResponse:
    """Evaluate candidate eligibility against structured job requirements."""
    job = db.query(JobRequirement).filter(JobRequirement.id == job_id, JobRequirement.deleted_at.is_(None)).first()
    if not job:
        raise JobNotFoundError(f"Job requirement {job_id} not found.")

    candidate = db.query(CandidateProfile).filter(
        CandidateProfile.id == candidate_profile_id,
        CandidateProfile.deleted_at.is_(None)
    ).first()
    if not candidate:
        raise ValueError(f"Candidate profile {candidate_profile_id} not found.")

    criteria: List[CriterionResult] = []
    missing_requirements: List[str] = []

    # 1. Required Qualifications
    if job.required_qualifications:
        req_quals = [q.strip().lower() for q in job.required_qualifications.split(",") if q.strip()]
        if not candidate.education_records:
            criteria.append(CriterionResult(
                criterion="Required Qualification",
                required_value=job.required_qualifications,
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No academic qualifications recorded on candidate profile."
            ))
            missing_requirements.append(f"Add academic records matching {job.required_qualifications}.")
        else:
            cand_levels = [e.education_level.lower() for e in candidate.education_records if e.education_level]
            cand_studies = [e.field_of_study.lower() for e in candidate.education_records if e.field_of_study]
            cand_streams = [e.stream_specialization.lower() for e in candidate.education_records if e.stream_specialization]
            cand_quals_text = " ".join(cand_levels + cand_studies + cand_streams)

            matched_qual = None
            for rq in req_quals:
                if rq in cand_quals_text:
                    matched_qual = rq
                    break
                # Handle common degree aliases
                if rq in ("b.tech", "btech", "b.e", "be", "bachelor") and any(lvl in ("undergraduate", "bachelor") for lvl in cand_levels):
                    matched_qual = rq
                    break
                if rq in ("mca", "m.tech", "mtech", "master") and any(lvl in ("postgraduate", "master") for lvl in cand_levels):
                    matched_qual = rq
                    break
                if rq == "diploma" and any(lvl == "diploma" for lvl in cand_levels):
                    matched_qual = rq
                    break

            if matched_qual:
                criteria.append(CriterionResult(
                    criterion="Required Qualification",
                    required_value=job.required_qualifications,
                    candidate_value=", ".join(set(cand_levels)),
                    status="SATISFIED",
                    explanation=f"Candidate qualification satisfies required qualification ({matched_qual.upper()})."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Required Qualification",
                    required_value=job.required_qualifications,
                    candidate_value=", ".join(set(cand_levels)) if cand_levels else "None",
                    status="UNSATISFIED",
                    explanation=f"Profile qualifications do not match required: {job.required_qualifications}."
                ))

    # 2. Accepted Branches / Specializations
    if job.accepted_branches:
        branches = [b.strip().lower() for b in job.accepted_branches.split(",") if b.strip()]
        cand_branches = [
            (e.stream_specialization or e.field_of_study or "").strip().lower()
            for e in candidate.education_records
            if (e.stream_specialization or e.field_of_study)
        ]
        if not candidate.education_records or not cand_branches:
            criteria.append(CriterionResult(
                criterion="Accepted Branches",
                required_value=job.accepted_branches,
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No branch or specialization recorded on education records."
            ))
            missing_requirements.append("Specify branch / stream specialization in education records.")
        else:
            matched = any(
                any(b in cb or cb in b for b in branches)
                for cb in cand_branches
            )
            if matched:
                criteria.append(CriterionResult(
                    criterion="Accepted Branches",
                    required_value=job.accepted_branches,
                    candidate_value=", ".join(cand_branches),
                    status="SATISFIED",
                    explanation=f"Specialization matches accepted branches: {job.accepted_branches}."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Accepted Branches",
                    required_value=job.accepted_branches,
                    candidate_value=", ".join(cand_branches),
                    status="UNSATISFIED",
                    explanation=f"Specialization ({', '.join(cand_branches)}) is not among accepted branches: {job.accepted_branches}."
                ))

    # 3. Minimum Percentage
    if job.min_percentage is not None and job.min_percentage > 0:
        percentages = [float(e.percentage) for e in candidate.education_records if e.percentage is not None]
        min_pct_val = float(job.min_percentage)
        if not percentages:
            criteria.append(CriterionResult(
                criterion="Minimum Academic Percentage",
                required_value=f"{min_pct_val:.1f}%",
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No percentage or marks recorded on academic records."
            ))
            missing_requirements.append(f"Add academic percentage (minimum required: {min_pct_val:.1f}%).")
        else:
            best_pct = max(percentages)
            if best_pct >= min_pct_val:
                criteria.append(CriterionResult(
                    criterion="Minimum Academic Percentage",
                    required_value=f"{min_pct_val:.1f}%",
                    candidate_value=f"{best_pct:.1f}%",
                    status="SATISFIED",
                    explanation=f"Candidate percentage ({best_pct:.1f}%) meets minimum requirement of {min_pct_val:.1f}%."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Minimum Academic Percentage",
                    required_value=f"{min_pct_val:.1f}%",
                    candidate_value=f"{best_pct:.1f}%",
                    status="UNSATISFIED",
                    explanation=f"Candidate percentage ({best_pct:.1f}%) is below minimum requirement of {min_pct_val:.1f}%."
                ))

    # 4. Minimum CGPA
    if job.min_cgpa is not None and job.min_cgpa > 0:
        cgpas = [float(e.cgpa) for e in candidate.education_records if e.cgpa is not None]
        min_cgpa_val = float(job.min_cgpa)
        if not cgpas:
            criteria.append(CriterionResult(
                criterion="Minimum CGPA",
                required_value=f"{min_cgpa_val:.2f}",
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No CGPA recorded on academic records."
            ))
            missing_requirements.append(f"Add CGPA to education records (minimum required: {min_cgpa_val:.2f}).")
        else:
            best_cgpa = max(cgpas)
            if best_cgpa >= min_cgpa_val:
                criteria.append(CriterionResult(
                    criterion="Minimum CGPA",
                    required_value=f"{min_cgpa_val:.2f}",
                    candidate_value=f"{best_cgpa:.2f}",
                    status="SATISFIED",
                    explanation=f"Candidate CGPA ({best_cgpa:.2f}) meets minimum requirement of {min_cgpa_val:.2f}."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Minimum CGPA",
                    required_value=f"{min_cgpa_val:.2f}",
                    candidate_value=f"{best_cgpa:.2f}",
                    status="UNSATISFIED",
                    explanation=f"Candidate CGPA ({best_cgpa:.2f}) is below minimum requirement of {min_cgpa_val:.2f}."
                ))

    # 5. Backlogs / Arrears Policy
    if not job.allow_backlogs or (job.max_active_backlogs is not None and job.max_active_backlogs >= 0):
        if not candidate.education_records:
            criteria.append(CriterionResult(
                criterion="Backlogs Policy",
                required_value="No backlogs" if not job.allow_backlogs else f"Max {job.max_active_backlogs} backlogs",
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No education records to verify backlog status."
            ))
            missing_requirements.append("Add education details to confirm backlog status.")
        else:
            total_active_backlogs = sum(e.active_backlogs_count for e in candidate.education_records)
            max_allowed = job.max_active_backlogs if job.max_active_backlogs is not None else 0
            if not job.allow_backlogs and total_active_backlogs > 0:
                criteria.append(CriterionResult(
                    criterion="Backlogs Policy",
                    required_value="0 active backlogs allowed",
                    candidate_value=f"{total_active_backlogs} active backlogs",
                    status="UNSATISFIED",
                    explanation=f"Employer policy prohibits backlogs. Candidate has {total_active_backlogs} active backlogs."
                ))
            elif total_active_backlogs > max_allowed:
                criteria.append(CriterionResult(
                    criterion="Backlogs Policy",
                    required_value=f"Max {max_allowed} active backlogs",
                    candidate_value=f"{total_active_backlogs} active backlogs",
                    status="UNSATISFIED",
                    explanation=f"Candidate active backlogs ({total_active_backlogs}) exceed limit ({max_allowed})."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Backlogs Policy",
                    required_value="No backlogs" if not job.allow_backlogs else f"Max {max_allowed} backlogs",
                    candidate_value=f"{total_active_backlogs} active backlogs",
                    status="SATISFIED",
                    explanation=f"Backlog criteria satisfied ({total_active_backlogs} active backlogs)."
                ))

    # 6. Required Skills
    if job.required_skills:
        req_skills = [s.strip().lower() for s in job.required_skills.split(",") if s.strip()]
        cand_skills = [s.skill_name.strip().lower() for s in candidate.skills if s.skill_name]
        if not cand_skills:
            criteria.append(CriterionResult(
                criterion="Required Skills",
                required_value=job.required_skills,
                candidate_value=None,
                status="UNABLE_TO_DETERMINE",
                explanation="No skills recorded on candidate profile."
            ))
            missing_requirements.append(f"Add skills to profile: {job.required_skills}.")
        else:
            matched = [s for s in req_skills if any(s in cs or cs in s for cs in cand_skills)]
            unmatched = [s for s in req_skills if not any(s in cs or cs in s for cs in cand_skills)]
            if not unmatched:
                criteria.append(CriterionResult(
                    criterion="Required Skills",
                    required_value=job.required_skills,
                    candidate_value=", ".join(matched),
                    status="SATISFIED",
                    explanation=f"All required skills satisfied ({', '.join(matched)})."
                ))
            else:
                criteria.append(CriterionResult(
                    criterion="Required Skills",
                    required_value=job.required_skills,
                    candidate_value=", ".join(matched) if matched else "None",
                    status="UNSATISFIED",
                    explanation=f"Missing required skills: {', '.join(unmatched)}."
                ))

    # 7. Required Documents
    if job.required_documents:
        req_docs = [d.strip().lower() for d in job.required_documents.split(",") if d.strip()]
        has_resume = any(len(r.versions) > 0 for r in candidate.resumes)
        doc_categories = [d.document_category.lower() for d in candidate.documents]

        for rd in req_docs:
            if "resume" in rd:
                if has_resume:
                    criteria.append(CriterionResult(
                        criterion="Required Document: Resume",
                        required_value="Resume",
                        candidate_value="Uploaded",
                        status="SATISFIED",
                        explanation="Resume is uploaded on profile."
                    ))
                else:
                    criteria.append(CriterionResult(
                        criterion="Required Document: Resume",
                        required_value="Resume",
                        candidate_value="Missing",
                        status="UNSATISFIED",
                        explanation="A resume must be uploaded before applying."
                    ))
                    missing_requirements.append("Upload a resume to your profile.")
            else:
                found = any(rd in cat for cat in doc_categories)
                if found:
                    criteria.append(CriterionResult(
                        criterion=f"Required Document: {rd.title()}",
                        required_value=rd.title(),
                        candidate_value="Uploaded",
                        status="SATISFIED",
                        explanation=f"{rd.title()} document is available."
                    ))
                else:
                    criteria.append(CriterionResult(
                        criterion=f"Required Document: {rd.title()}",
                        required_value=rd.title(),
                        candidate_value="Missing",
                        status="UNSATISFIED",
                        explanation=f"Required document {rd.title()} is missing from profile."
                    ))
                    missing_requirements.append(f"Upload required document: {rd.title()}.")

    # Evaluate Overall Status
    if any(c.status == "UNSATISFIED" for c in criteria):
        overall_status = "NOT_ELIGIBLE"
        can_apply = False
    elif any(c.status == "UNABLE_TO_DETERMINE" for c in criteria):
        overall_status = "UNABLE_TO_DETERMINE"
        can_apply = False
    else:
        overall_status = "ELIGIBLE"
        can_apply = True

    return JobEligibilityResponse(
        job_id=job.id,
        candidate_id=candidate.id,
        overall_status=overall_status,
        can_apply=can_apply,
        criteria=criteria,
        missing_requirements=missing_requirements,
    )
