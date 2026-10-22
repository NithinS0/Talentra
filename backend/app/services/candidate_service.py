"""Candidate Registration, Profile, Academic, Resume, Document, and Portfolio Service.

Enforces server-side identity allocation, multi-role assignment, ISO country linkage,
atomic database transactions, dynamic profile completeness auditing, and private file vault access.
"""

from decimal import Decimal
from typing import Optional, List, Tuple
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.candidate import (
    CandidateProfile,
    CandidateContact,
    CandidateEducation,
    CandidateEducationSemester,
    CandidateResume,
    ResumeVersion,
    CandidateDocument,
    CandidateSkill,
    CandidateProject,
    CandidateWorkExperience,
    CandidateCertification,
)
from app.models.country import Country
from app.models.job import JobRequirement
from app.models.application import JobApplication
from app.schemas.candidate import (
    CandidateRegisterRequest,
    CandidateProfileUpdateRequest,
    CandidateProfileResponse,
    ProfileCompletenessResponse,
    CompletenessItem,
    EducationCreateRequest,
    EducationUpdateRequest,
    EducationResponse,
    SemesterCreateUpdateRequest,
    SemesterResponse,
    CandidateResumeResponse,
    ResumeVersionResponse,
    CandidateDocumentResponse,
    SkillCreateRequest,
    SkillResponse,
    ProjectCreateRequest,
    ProjectResponse,
    CertificationCreateRequest,
    CertificationResponse,
    WorkExperienceCreateRequest,
    WorkExperienceResponse,
)
from app.schemas.auth import AuthClaims
from app.services.actor_id_service import allocate_actor_id
from app.services.country_service import get_country_by_code, validate_and_format_phone
from app.services.storage_service import storage_service, StorageError


class CandidateRegistrationError(Exception):
    """Base exception for candidate provisioning errors."""
    pass


class DuplicateCandidateProfileError(CandidateRegistrationError):
    """Raised when an account already possesses a candidate profile."""
    pass


class AccountEmailConflictError(CandidateRegistrationError):
    """Raised when an email is already associated with another provider identity."""
    pass


class CandidateNotFoundError(ValueError):
    """Raised when a candidate profile cannot be found."""
    pass


# -----------------------------------------------------------------------------
# Registration Workflow
# -----------------------------------------------------------------------------

def register_candidate_workflow(
    db: Session,
    claims: AuthClaims,
    request: CandidateRegisterRequest,
) -> CandidateProfileResponse:
    """Execute end-to-end atomic candidate registration and actor provisioning."""
    # 1. Validate country selection against country master
    country = get_country_by_code(db, request.country_code)

    # 2. Validate and format phone number if provided
    formatted_phone: Optional[str] = None
    if request.phone_number:
        formatted_phone = validate_and_format_phone(request.phone_number, country.country_code)

    # 3. Check existing user account by Supabase provider subject (sub)
    user = db.query(User).filter(User.provider_subject == claims.sub).first()

    if user:
        existing_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if existing_profile:
            raise DuplicateCandidateProfileError(
                f"A Candidate profile ({existing_profile.actor_id}) already exists for this account."
            )
    else:
        email_to_check = claims.email
        if email_to_check:
            conflict = db.query(User).filter(User.email_address == email_to_check).first()
            if conflict and conflict.provider_subject != claims.sub:
                raise AccountEmailConflictError(
                    f"An account with email '{email_to_check}' is already registered."
                )

        display_name = f"{request.first_name} {request.last_name}".strip()
        user = User(
            email_address=claims.email,
            phone_e164=formatted_phone,
            display_name=display_name,
            account_status_code_id=1,  # ACTIVE
            identity_provider_code="SUPABASE",
            provider_subject=claims.sub,
        )
        db.add(user)
        db.flush()

    # 4. Resolve CANDIDATE role
    role = db.query(Role).filter(Role.role_code == "CANDIDATE").first()
    if not role:
        role = Role(
            id=5,
            role_code="CANDIDATE",
            display_name="Candidate",
            description="Talentra Job Candidate",
            is_system_role=True,
        )
        db.add(role)
        db.flush()

    # 5. Allocate server-side formatted Actor ID
    allocated_actor_id = allocate_actor_id(db, "CANDIDATE")

    # 6. Assign role
    role_assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        actor_id=allocated_actor_id,
        assigned_by_user_id=user.id,
    )
    db.add(role_assignment)

    # 7. Record public actor identity
    actor_identity = UserActorIdentity(
        user_id=user.id,
        role_id=role.id,
        role_code="CANDIDATE",
        actor_prefix="CA",
        actor_id=allocated_actor_id,
        is_active=True,
    )
    db.add(actor_identity)

    # 8. Create candidate_profile record
    candidate_profile = CandidateProfile(
        user_id=user.id,
        actor_id=allocated_actor_id,
        first_name=request.first_name.strip(),
        middle_name=request.middle_name.strip() if request.middle_name else None,
        last_name=request.last_name.strip(),
        headline=request.headline.strip() if request.headline else None,
        summary=request.summary.strip() if request.summary else None,
        profile_status_code_id=1,  # ACTIVE
        profile_visibility_code_id=1,  # PUBLIC
        completion_score=Decimal("20.00"),
    )
    db.add(candidate_profile)
    db.flush()

    # 9. Create candidate_contact record
    candidate_contact = CandidateContact(
        candidate_profile_id=candidate_profile.id,
        email_address=user.email_address,
        phone_e164=formatted_phone,
        phone_country_id=country.id,
    )
    db.add(candidate_contact)

    candidate_profile.completion_score = Decimal("15.00")
    db.commit()
    db.refresh(candidate_profile)

    return build_candidate_profile_response(db, candidate_profile)


# -----------------------------------------------------------------------------
# Profile Completeness Calculation
# -----------------------------------------------------------------------------

def calculate_profile_completeness(
    db: Session,
    candidate_profile_id: int,
) -> ProfileCompletenessResponse:
    """Dynamically compute profile completeness score and missing items checklist."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
    if not profile:
        raise CandidateNotFoundError(f"Candidate profile {candidate_profile_id} not found.")

    contact = db.query(CandidateContact).filter(CandidateContact.candidate_profile_id == profile.id).first()

    checklist: List[CompletenessItem] = []
    total_score = 0.0

    # 1. Personal & Professional Details (weight 15)
    has_personal = bool(
        profile.first_name
        and profile.last_name
        and profile.headline
        and profile.summary
        and profile.current_city
    )
    weight_personal = 15
    if has_personal:
        total_score += weight_personal
    checklist.append(CompletenessItem(
        key="personal_info",
        section="Personal",
        title="Personal & Professional Summary",
        is_complete=has_personal,
        weight=weight_personal,
        missing_reason="Add headline, professional summary, and current city." if not has_personal else None,
        deep_link="/portal/candidate#personal",
    ))

    # 2. Profile Photo (weight 10)
    has_photo = bool(profile.profile_photo_url or profile.profile_photo_storage_key)
    weight_photo = 10
    if has_photo:
        total_score += weight_photo
    checklist.append(CompletenessItem(
        key="profile_photo",
        section="Personal",
        title="Professional Profile Photo",
        is_complete=has_photo,
        weight=weight_photo,
        missing_reason="Upload a professional profile photo." if not has_photo else None,
        deep_link="/portal/candidate#photo",
    ))

    # 3. Verified Contact Information (weight 10)
    has_contact = bool(contact and contact.phone_e164 and contact.phone_country_id)
    weight_contact = 10
    if has_contact:
        total_score += weight_contact
    checklist.append(CompletenessItem(
        key="contact_info",
        section="Contact",
        title="Contact Phone & Country Verification",
        is_complete=has_contact,
        weight=weight_contact,
        missing_reason="Provide verified phone number with country code." if not has_contact else None,
        deep_link="/portal/candidate#contact",
    ))

    # 4. Academic History (weight 20)
    edu_count = db.query(func.count(CandidateEducation.id)).filter(
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).scalar() or 0
    has_edu = edu_count > 0
    weight_edu = 20
    if has_edu:
        total_score += weight_edu
    checklist.append(CompletenessItem(
        key="academic_history",
        section="Academics",
        title="Academic History & Qualifications",
        is_complete=has_edu,
        weight=weight_edu,
        missing_reason="Add at least one completed or pursuing education qualification." if not has_edu else None,
        deep_link="/portal/candidate#academics",
    ))

    # 5. Academic Documents / Semester Grade Sheets (weight 10)
    has_academic_docs = (
        db.query(CandidateDocument)
        .filter(
            CandidateDocument.candidate_profile_id == profile.id,
            CandidateDocument.document_category.in_([
                "CLASS_10_MARKSHEET",
                "CLASS_12_MARKSHEET",
                "DIPLOMA_CERTIFICATE",
                "SEMESTER_GRADESHEET",
                "TRANSCRIPT",
            ]),
            CandidateDocument.is_archived == False,
        )
        .first()
        is not None
    )
    weight_docs = 10
    if has_academic_docs:
        total_score += weight_docs
    checklist.append(CompletenessItem(
        key="academic_documents",
        section="Documents",
        title="Academic Marksheets / Semester Grade Sheets",
        is_complete=has_academic_docs,
        weight=weight_docs,
        missing_reason="Upload at least one verified marksheet or semester grade sheet." if not has_academic_docs else None,
        deep_link="/portal/candidate#documents",
    ))

    # 6. Resume Management (weight 15)
    resume_with_version = (
        db.query(ResumeVersion)
        .join(CandidateResume)
        .filter(
            CandidateResume.candidate_profile_id == profile.id,
            CandidateResume.deleted_at.is_(None),
            ResumeVersion.is_archived == False,
        )
        .first()
    )
    has_resume = resume_with_version is not None
    weight_resume = 15
    if has_resume:
        total_score += weight_resume
    checklist.append(CompletenessItem(
        key="resume",
        section="Documents",
        title="Uploaded Resume / CV",
        is_complete=has_resume,
        weight=weight_resume,
        missing_reason="Upload a PDF or Word resume." if not has_resume else None,
        deep_link="/portal/candidate#resume",
    ))

    # 7. Technical & Professional Skills (weight 10)
    skill_count = db.query(func.count(CandidateSkill.id)).filter(
        CandidateSkill.candidate_profile_id == profile.id,
    ).scalar() or 0
    has_skills = skill_count >= 2
    weight_skills = 10
    if has_skills:
        total_score += weight_skills
    checklist.append(CompletenessItem(
        key="skills",
        section="Skills",
        title="Technical & Core Skills (at least 2)",
        is_complete=has_skills,
        weight=weight_skills,
        missing_reason="Add at least two technical or functional skills." if not has_skills else None,
        deep_link="/portal/candidate#skills",
    ))

    # 8. Placement & Career Preferences (weight 10)
    has_prefs = bool(
        profile.preferred_roles
        and profile.preferred_locations
        and profile.preferred_employment_types
    )
    weight_prefs = 10
    if has_prefs:
        total_score += weight_prefs
    checklist.append(CompletenessItem(
        key="placement_preferences",
        section="Preferences",
        title="Placement & Work Preferences",
        is_complete=has_prefs,
        weight=weight_prefs,
        missing_reason="Specify preferred roles, work locations, and employment types." if not has_prefs else None,
        deep_link="/portal/candidate#preferences",
    ))

    # Persist updated score
    profile.completion_score = Decimal(str(round(total_score, 2)))
    db.commit()

    is_eligible = total_score >= 60.0 and has_edu and has_resume

    return ProfileCompletenessResponse(
        overall_score=round(total_score, 1),
        is_placement_eligible=is_eligible,
        checklist_items=checklist,
    )


# -----------------------------------------------------------------------------
# Response Formatter
# -----------------------------------------------------------------------------

def build_candidate_profile_response(
    db: Session,
    profile: CandidateProfile,
) -> CandidateProfileResponse:
    """Build complete Pydantic CandidateProfileResponse from ORM model."""
    user = db.query(User).filter(User.id == profile.user_id).first()
    contact = db.query(CandidateContact).filter(CandidateContact.candidate_profile_id == profile.id).first()

    country_code = None
    country_name = None
    if contact and contact.phone_country_id:
        country = db.query(Country).filter(Country.id == contact.phone_country_id).first()
        if country:
            country_code = country.country_code
            country_name = country.name

    # Format Education records with Semesters
    education_responses: List[EducationResponse] = []
    for edu in profile.education_records:
        if edu.deleted_at is not None:
            continue
        sem_list = [
            SemesterResponse.model_validate(s)
            for s in sorted(edu.semesters, key=lambda s: s.semester_number)
        ]
        edu_resp = EducationResponse(
            id=edu.id,
            candidate_profile_id=edu.candidate_profile_id,
            education_level=edu.education_level or "UNDERGRADUATE",
            institution_name=edu.institution_name,
            board_or_university=edu.board_or_university,
            field_of_study=edu.field_of_study,
            stream_specialization=edu.stream_specialization,
            status=edu.status or "COMPLETED",
            start_year=edu.start_year,
            completion_year=edu.completion_year,
            grading_system=edu.grading_system or "PERCENTAGE",
            score_value=float(edu.score_value) if edu.score_value is not None else None,
            max_score=float(edu.max_score) if edu.max_score is not None else None,
            percentage=float(edu.percentage) if edu.percentage is not None else None,
            cgpa=float(edu.cgpa) if edu.cgpa is not None else None,
            has_backlogs=edu.has_backlogs if edu.has_backlogs is not None else False,
            active_backlogs_count=edu.active_backlogs_count or 0,
            historical_backlogs_count=edu.historical_backlogs_count or 0,
            document_storage_key=edu.document_storage_key,
            document_name=edu.document_name,
            document_size_bytes=edu.document_size_bytes,
            document_mime_type=edu.document_mime_type,
            semesters=sem_list,
            created_at=edu.created_at,
            updated_at=edu.updated_at,
        )
        education_responses.append(edu_resp)

    # Format Resumes
    resume_responses: List[CandidateResumeResponse] = []
    for cr in profile.resumes:
        if cr.deleted_at is not None:
            continue
        v_list = [
            ResumeVersionResponse.model_validate(v)
            for v in sorted(cr.versions, key=lambda v: v.version_number, reverse=True)
            if not v.is_archived
        ]
        resume_responses.append(CandidateResumeResponse(
            id=cr.id,
            candidate_profile_id=cr.candidate_profile_id,
            resume_title=cr.resume_title,
            is_default=cr.is_default,
            versions=v_list,
            created_at=cr.created_at,
            updated_at=cr.updated_at,
        ))

    # Format Documents
    doc_responses = [
        CandidateDocumentResponse.model_validate(d)
        for d in profile.documents
        if not d.is_archived
    ]

    # Format Skills
    skill_responses = [
        SkillResponse(
            id=s.id,
            candidate_profile_id=s.candidate_profile_id,
            skill_name=s.skill_name or f"Skill #{s.skill_id}",
            proficiency_level=s.proficiency_level or "INTERMEDIATE",
            years_experience=float(s.years_experience) if s.years_experience is not None else None,
            is_primary=s.is_primary if s.is_primary is not None else False,
        )
        for s in profile.skills
    ]

    # Format Projects
    project_responses = [
        ProjectResponse.model_validate(p) for p in profile.projects
    ]

    # Format Work Experiences
    work_responses = [
        WorkExperienceResponse.model_validate(w) for w in profile.work_experiences
    ]

    # Format Certifications
    cert_responses = [
        CertificationResponse.model_validate(c) for c in profile.certifications
    ]

    disp_name = user.display_name if user else f"{profile.first_name} {profile.last_name}"
    email_addr = user.email_address if user else (contact.email_address if contact else None)

    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        actor_id=profile.actor_id,
        first_name=profile.first_name,
        middle_name=profile.middle_name,
        last_name=profile.last_name,
        display_name=disp_name,
        headline=profile.headline,
        summary=profile.summary,
        profile_photo_url=profile.profile_photo_url,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        portfolio_url=profile.portfolio_url,
        current_city=profile.current_city,
        current_state=profile.current_state,
        email_address=email_addr,
        phone_e164=contact.phone_e164 if contact else None,
        country_code=country_code,
        country_name=country_name,
        preferred_roles=profile.preferred_roles,
        preferred_locations=profile.preferred_locations,
        preferred_employment_types=profile.preferred_employment_types,
        expected_graduation_date=profile.expected_graduation_date,
        availability_status=profile.availability_status or "AVAILABLE",
        is_public_visible=profile.is_public_visible if profile.is_public_visible is not None else True,
        consent_placement_rules=profile.consent_placement_rules if profile.consent_placement_rules is not None else True,
        consent_share_with_employers=profile.consent_share_with_employers if profile.consent_share_with_employers is not None else True,
        completion_score=float(profile.completion_score),
        education_records=education_responses,
        resumes=resume_responses,
        documents=doc_responses,
        skills=skill_responses,
        projects=project_responses,
        work_experiences=work_responses,
        certifications=cert_responses,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def get_candidate_profile_by_user_id(
    db: Session,
    user_id: int,
) -> Optional[CandidateProfileResponse]:
    """Retrieve full Candidate profile for an authenticated user."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        return None
    return build_candidate_profile_response(db, profile)


def get_candidate_profile_by_id(
    db: Session,
    profile_id: int,
) -> Optional[CandidateProfileResponse]:
    """Retrieve Candidate profile by internal ID."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    if not profile:
        return None
    return build_candidate_profile_response(db, profile)


# -----------------------------------------------------------------------------
# Profile Updates
# -----------------------------------------------------------------------------

def update_candidate_profile(
    db: Session,
    user_id: int,
    request: CandidateProfileUpdateRequest,
) -> CandidateProfileResponse:
    """Update editable candidate profile attributes and contact details."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError(f"Candidate profile for user {user_id} not found.")

    if request.first_name is not None:
        profile.first_name = request.first_name.strip()
    if request.middle_name is not None:
        profile.middle_name = request.middle_name.strip() if request.middle_name else None
    if request.last_name is not None:
        profile.last_name = request.last_name.strip()
    if request.headline is not None:
        profile.headline = request.headline.strip() if request.headline else None
    if request.summary is not None:
        profile.summary = request.summary.strip() if request.summary else None
    if request.current_city is not None:
        profile.current_city = request.current_city.strip() if request.current_city else None
    if request.current_state is not None:
        profile.current_state = request.current_state.strip() if request.current_state else None
    if request.linkedin_url is not None:
        profile.linkedin_url = request.linkedin_url.strip() if request.linkedin_url else None
    if request.github_url is not None:
        profile.github_url = request.github_url.strip() if request.github_url else None
    if request.portfolio_url is not None:
        profile.portfolio_url = request.portfolio_url.strip() if request.portfolio_url else None
    if request.preferred_roles is not None:
        profile.preferred_roles = request.preferred_roles.strip() if request.preferred_roles else None
    if request.preferred_locations is not None:
        profile.preferred_locations = request.preferred_locations.strip() if request.preferred_locations else None
    if request.preferred_employment_types is not None:
        profile.preferred_employment_types = request.preferred_employment_types.strip() if request.preferred_employment_types else None
    if request.expected_graduation_date is not None:
        profile.expected_graduation_date = request.expected_graduation_date
    if request.availability_status is not None:
        profile.availability_status = request.availability_status
    if request.is_public_visible is not None:
        profile.is_public_visible = request.is_public_visible
    if request.consent_placement_rules is not None:
        profile.consent_placement_rules = request.consent_placement_rules
    if request.consent_share_with_employers is not None:
        profile.consent_share_with_employers = request.consent_share_with_employers

    # Update contact phone / country if provided
    contact = db.query(CandidateContact).filter(CandidateContact.candidate_profile_id == profile.id).first()
    if contact and (request.phone_number is not None or request.country_code is not None):
        code_to_use = request.country_code or "IN"
        country = get_country_by_code(db, code_to_use)
        if request.phone_number is not None:
            formatted_phone = validate_and_format_phone(request.phone_number, country.country_code)
            contact.phone_e164 = formatted_phone
        contact.phone_country_id = country.id

    db.commit()
    db.refresh(profile)

    calculate_profile_completeness(db, profile.id)
    return build_candidate_profile_response(db, profile)


# -----------------------------------------------------------------------------
# Profile Photo
# -----------------------------------------------------------------------------

def upload_profile_photo(
    db: Session,
    user_id: int,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> str:
    """Store candidate profile photo in private vault and link to profile."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    res = storage_service.store_file(
        file_bytes=file_bytes,
        category="photo",
        original_filename=filename,
        content_type=content_type,
        owner_id=user_id,
    )

    profile.profile_photo_storage_key = res.storage_key
    profile.profile_photo_url = f"/api/v1/candidates/{profile.id}/photo"
    db.commit()

    calculate_profile_completeness(db, profile.id)
    return profile.profile_photo_url


def delete_profile_photo(db: Session, user_id: int) -> None:
    """Remove candidate profile photo."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    if profile.profile_photo_storage_key:
        storage_service.delete_file(profile.profile_photo_storage_key)
        profile.profile_photo_storage_key = None
        profile.profile_photo_url = None
        db.commit()
        calculate_profile_completeness(db, profile.id)


def get_profile_photo_file(db: Session, profile_id: int) -> Tuple[bytes, str, str]:
    """Retrieve profile photo binary content."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    if not profile or not profile.profile_photo_storage_key:
        raise CandidateNotFoundError("Profile photo not found.")

    return storage_service.retrieve_file(profile.profile_photo_storage_key)


# -----------------------------------------------------------------------------
# Academic Education History
# -----------------------------------------------------------------------------

def add_education(
    db: Session,
    user_id: int,
    request: EducationCreateRequest,
) -> EducationResponse:
    """Add an academic qualification to candidate's history."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    # Enforce uniqueness for secondary qualifications (only one Class 10 and Class 12 record)
    if request.education_level in ("CLASS_10", "CLASS_12"):
        existing = db.query(CandidateEducation).filter(
            CandidateEducation.candidate_profile_id == profile.id,
            CandidateEducation.education_level == request.education_level,
            CandidateEducation.deleted_at.is_(None),
        ).first()
        if existing:
            raise ValueError(f"A record for {request.education_level} already exists. Please edit the existing record.")

    edu = CandidateEducation(
        candidate_profile_id=profile.id,
        education_level=request.education_level,
        institution_name=request.institution_name.strip(),
        board_or_university=request.board_or_university.strip() if request.board_or_university else None,
        field_of_study=request.field_of_study.strip() if request.field_of_study else None,
        stream_specialization=request.stream_specialization.strip() if request.stream_specialization else None,
        status=request.status,
        start_year=request.start_year,
        completion_year=request.completion_year,
        grading_system=request.grading_system,
        score_value=Decimal(str(request.score_value)) if request.score_value is not None else None,
        max_score=Decimal(str(request.max_score)) if request.max_score is not None else None,
        percentage=Decimal(str(request.percentage)) if request.percentage is not None else None,
        cgpa=Decimal(str(request.cgpa)) if request.cgpa is not None else None,
        has_backlogs=request.has_backlogs,
        active_backlogs_count=request.active_backlogs_count,
        historical_backlogs_count=request.historical_backlogs_count,
        document_storage_key=request.document_storage_key,
        document_name=request.document_name,
        document_size_bytes=request.document_size_bytes,
        document_mime_type=request.document_mime_type,
        created_by=user_id,
    )
    db.add(edu)
    db.commit()
    db.refresh(edu)

    calculate_profile_completeness(db, profile.id)
    return EducationResponse.model_validate(edu)


def update_education(
    db: Session,
    user_id: int,
    education_id: int,
    request: EducationUpdateRequest,
) -> EducationResponse:
    """Update an existing academic qualification record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu:
        raise ValueError(f"Education record {education_id} not found.")

    if request.education_level is not None:
        edu.education_level = request.education_level
    if request.institution_name is not None:
        edu.institution_name = request.institution_name.strip()
    if request.board_or_university is not None:
        edu.board_or_university = request.board_or_university.strip() if request.board_or_university else None
    if request.field_of_study is not None:
        edu.field_of_study = request.field_of_study.strip() if request.field_of_study else None
    if request.stream_specialization is not None:
        edu.stream_specialization = request.stream_specialization.strip() if request.stream_specialization else None
    if request.status is not None:
        edu.status = request.status
    if request.start_year is not None:
        edu.start_year = request.start_year
    if request.completion_year is not None:
        edu.completion_year = request.completion_year
    if request.grading_system is not None:
        edu.grading_system = request.grading_system
    if request.score_value is not None:
        edu.score_value = Decimal(str(request.score_value))
    if request.max_score is not None:
        edu.max_score = Decimal(str(request.max_score))
    if request.percentage is not None:
        edu.percentage = Decimal(str(request.percentage))
    if request.cgpa is not None:
        edu.cgpa = Decimal(str(request.cgpa))
    if request.has_backlogs is not None:
        edu.has_backlogs = request.has_backlogs
    if request.active_backlogs_count is not None:
        edu.active_backlogs_count = request.active_backlogs_count
    if request.historical_backlogs_count is not None:
        edu.historical_backlogs_count = request.historical_backlogs_count

    edu.updated_by = user_id
    db.commit()
    db.refresh(edu)

    calculate_profile_completeness(db, profile.id)
    return EducationResponse.model_validate(edu)


def delete_education(db: Session, user_id: int, education_id: int) -> bool:
    """Soft-delete an education record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu:
        raise ValueError(f"Education record {education_id} not found.")

    edu.deleted_at = datetime.now(timezone.utc)
    edu.updated_by = user_id
    db.commit()

    calculate_profile_completeness(db, profile.id)
    return True


def upload_education_document(
    db: Session,
    user_id: int,
    education_id: int,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> EducationResponse:
    """Upload marksheet or certificate attached to an education record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu:
        raise ValueError(f"Education record {education_id} not found.")

    category = "CLASS_10_MARKSHEET" if edu.education_level == "CLASS_10" else (
        "CLASS_12_MARKSHEET" if edu.education_level == "CLASS_12" else (
            "DIPLOMA_CERTIFICATE" if edu.education_level == "DIPLOMA" else "DEGREE_CERTIFICATE"
        )
    )

    res = storage_service.store_file(
        file_bytes=file_bytes,
        category="marksheet",
        original_filename=filename,
        content_type=content_type,
        owner_id=user_id,
    )

    edu.document_storage_key = res.storage_key
    edu.document_name = filename
    edu.document_size_bytes = res.size_bytes
    edu.document_mime_type = res.mime_type
    edu.updated_by = user_id

    # Add candidate_document audit entry
    doc = CandidateDocument(
        candidate_profile_id=profile.id,
        document_category=category,
        title=f"{edu.education_level.replace('_', ' ')} Document",
        file_name=filename,
        file_size_bytes=res.size_bytes,
        mime_type=res.mime_type,
        storage_path=res.storage_key,
        content_sha256=res.content_sha256,
        linked_entity_type="candidate_education",
        linked_entity_id=edu.id,
        created_by=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(edu)

    calculate_profile_completeness(db, profile.id)
    return EducationResponse.model_validate(edu)


def _authorize_candidate_document_access(
    db: Session,
    candidate_profile_id: int,
    requesting_user_id: int,
) -> bool:
    """Verify requesting user is the candidate owner OR an authorized employer/recruiter with an active application."""
    # 1. Check if requesting user is the candidate owner
    candidate = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
    if not candidate:
        return False
    if candidate.user_id == requesting_user_id:
        return True

    # 2. Check if requesting user has administrative or employer review authority
    user = db.query(User).filter(User.id == requesting_user_id).first()
    if not user:
        return False

    user_roles = [ura.role.role_code for ura in user.role_assignments if ura.role]
    if "SUPER_ADMIN" in user_roles or "ADMIN" in user_roles:
        return True

    # Check employer / recruiter org mapping with submitted application
    user_org_ids = [
        ura.organisation_id for ura in user.role_assignments
        if ura.organisation_id is not None
    ]
    if user_org_ids:
        has_app = (
            db.query(JobApplication)
            .join(JobRequirement, JobApplication.job_requirement_id == JobRequirement.id)
            .filter(
                JobApplication.candidate_profile_id == candidate_profile_id,
                JobApplication.deleted_at.is_(None),
                JobRequirement.organisation_id.in_(user_org_ids),
            )
            .first()
        )
        if has_app:
            return True

    return False


def get_education_document_file(
    db: Session,
    education_id: int,
    requesting_user_id: int,
) -> Tuple[bytes, str, str]:
    """Retrieve document file associated with education record with authorization check."""
    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu or not edu.document_storage_key:
        raise ValueError("Education document not found.")

    if not _authorize_candidate_document_access(db, edu.candidate_profile_id, requesting_user_id):
        raise ValueError("Access denied to requested education document.")

    return storage_service.retrieve_file(edu.document_storage_key)


# -----------------------------------------------------------------------------
# Semester-wise Grade Sheets
# -----------------------------------------------------------------------------

def add_or_update_semester(
    db: Session,
    user_id: int,
    education_id: int,
    request: SemesterCreateUpdateRequest,
) -> SemesterResponse:
    """Create or update a semester marksheet record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu:
        raise ValueError(f"Education record {education_id} not found.")

    sem = db.query(CandidateEducationSemester).filter(
        CandidateEducationSemester.candidate_education_id == edu.id,
        CandidateEducationSemester.semester_number == request.semester_number,
    ).first()

    if sem:
        # Update existing semester
        sem.academic_term = request.academic_term
        sem.result_status = request.result_status
        sem.sgpa = Decimal(str(request.sgpa)) if request.sgpa is not None else None
        sem.cgpa = Decimal(str(request.cgpa)) if request.cgpa is not None else None
        sem.credits_registered = request.credits_registered
        sem.credits_earned = request.credits_earned
        sem.has_backlog = request.has_backlog
        sem.backlog_details = request.backlog_details
        if request.grade_sheet_storage_key:
            sem.grade_sheet_storage_key = request.grade_sheet_storage_key
            sem.grade_sheet_name = request.grade_sheet_name
            sem.grade_sheet_size_bytes = request.grade_sheet_size_bytes
            sem.grade_sheet_mime_type = request.grade_sheet_mime_type
            sem.uploaded_at = datetime.now(timezone.utc)
        sem.updated_by = user_id
    else:
        # Create new semester record
        sem = CandidateEducationSemester(
            candidate_education_id=edu.id,
            candidate_profile_id=profile.id,
            semester_number=request.semester_number,
            academic_term=request.academic_term,
            result_status=request.result_status,
            sgpa=Decimal(str(request.sgpa)) if request.sgpa is not None else None,
            cgpa=Decimal(str(request.cgpa)) if request.cgpa is not None else None,
            credits_registered=request.credits_registered,
            credits_earned=request.credits_earned,
            has_backlog=request.has_backlog,
            backlog_details=request.backlog_details,
            grade_sheet_storage_key=request.grade_sheet_storage_key,
            grade_sheet_name=request.grade_sheet_name,
            grade_sheet_size_bytes=request.grade_sheet_size_bytes,
            grade_sheet_mime_type=request.grade_sheet_mime_type,
            uploaded_at=datetime.now(timezone.utc) if request.grade_sheet_storage_key else None,
            created_by=user_id,
        )
        db.add(sem)

    db.commit()
    db.refresh(sem)

    calculate_profile_completeness(db, profile.id)
    return SemesterResponse.model_validate(sem)


def delete_semester(
    db: Session,
    user_id: int,
    education_id: int,
    semester_id: int,
) -> bool:
    """Delete a semester record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    sem = (
        db.query(CandidateEducationSemester)
        .join(CandidateEducation)
        .filter(
            CandidateEducationSemester.id == semester_id,
            CandidateEducation.id == education_id,
            CandidateEducation.candidate_profile_id == profile.id,
        )
        .first()
    )
    if not sem:
        raise ValueError("Semester record not found.")

    db.delete(sem)
    db.commit()

    calculate_profile_completeness(db, profile.id)
    return True


def upload_semester_gradesheet(
    db: Session,
    user_id: int,
    education_id: int,
    semester_number: int,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> SemesterResponse:
    """Upload and attach a grade sheet document to a specific semester."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    edu = db.query(CandidateEducation).filter(
        CandidateEducation.id == education_id,
        CandidateEducation.candidate_profile_id == profile.id,
        CandidateEducation.deleted_at.is_(None),
    ).first()
    if not edu:
        raise ValueError(f"Education record {education_id} not found.")

    res = storage_service.store_file(
        file_bytes=file_bytes,
        category="gradesheet",
        original_filename=filename,
        content_type=content_type,
        owner_id=user_id,
    )

    sem = db.query(CandidateEducationSemester).filter(
        CandidateEducationSemester.candidate_education_id == edu.id,
        CandidateEducationSemester.semester_number == semester_number,
    ).first()

    if not sem:
        sem = CandidateEducationSemester(
            candidate_education_id=edu.id,
            candidate_profile_id=profile.id,
            semester_number=semester_number,
            result_status="PASS",
            grade_sheet_storage_key=res.storage_key,
            grade_sheet_name=filename,
            grade_sheet_size_bytes=res.size_bytes,
            grade_sheet_mime_type=res.mime_type,
            uploaded_at=datetime.now(timezone.utc),
            created_by=user_id,
        )
        db.add(sem)
    else:
        sem.grade_sheet_storage_key = res.storage_key
        sem.grade_sheet_name = filename
        sem.grade_sheet_size_bytes = res.size_bytes
        sem.grade_sheet_mime_type = res.mime_type
        sem.uploaded_at = datetime.now(timezone.utc)
        sem.updated_by = user_id

    # Create candidate_document record
    doc = CandidateDocument(
        candidate_profile_id=profile.id,
        document_category="SEMESTER_GRADESHEET",
        title=f"Semester {semester_number} Grade Sheet",
        file_name=filename,
        file_size_bytes=res.size_bytes,
        mime_type=res.mime_type,
        storage_path=res.storage_key,
        content_sha256=res.content_sha256,
        linked_entity_type="candidate_education_semester",
        linked_entity_id=sem.id if sem.id else None,
        created_by=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(sem)

    calculate_profile_completeness(db, profile.id)
    return SemesterResponse.model_validate(sem)


def get_semester_gradesheet_file(
    db: Session,
    education_id: int,
    semester_number: int,
    requesting_user_id: int,
) -> Tuple[bytes, str, str]:
    """Retrieve gradesheet binary file with authorization check."""
    sem = db.query(CandidateEducationSemester).filter(
        CandidateEducationSemester.candidate_education_id == education_id,
        CandidateEducationSemester.semester_number == semester_number,
    ).first()
    if not sem or not sem.grade_sheet_storage_key:
        raise ValueError("Semester grade sheet not found.")

    if not _authorize_candidate_document_access(db, sem.candidate_profile_id, requesting_user_id):
        raise ValueError("Access denied to requested semester grade sheet.")

    return storage_service.retrieve_file(sem.grade_sheet_storage_key)


# -----------------------------------------------------------------------------
# Resume Management
# -----------------------------------------------------------------------------

def upload_resume(
    db: Session,
    user_id: int,
    resume_title: str,
    target_role: Optional[str],
    is_default: bool,
    file_bytes: bytes,
    filename: str,
    content_type: str,
) -> CandidateResumeResponse:
    """Upload a resume file, manage multi-versioning, and maintain default flag."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    res = storage_service.store_file(
        file_bytes=file_bytes,
        category="resume",
        original_filename=filename,
        content_type=content_type,
        owner_id=user_id,
    )

    # Check existing resume containers for this title
    clean_title = resume_title.strip() if resume_title else "Primary Resume"
    cand_resume = db.query(CandidateResume).filter(
        CandidateResume.candidate_profile_id == profile.id,
        CandidateResume.resume_title == clean_title,
        CandidateResume.deleted_at.is_(None),
    ).first()

    if not cand_resume:
        # Check if first resume overall
        existing_any = db.query(CandidateResume).filter(
            CandidateResume.candidate_profile_id == profile.id,
            CandidateResume.deleted_at.is_(None),
        ).first()
        should_be_default = is_default or (existing_any is None)

        if should_be_default:
            db.query(CandidateResume).filter(
                CandidateResume.candidate_profile_id == profile.id,
            ).update({"is_default": False})

        cand_resume = CandidateResume(
            candidate_profile_id=profile.id,
            resume_title=clean_title,
            is_default=should_be_default,
            created_by=user_id,
        )
        db.add(cand_resume)
        db.flush()

    # Determine next version number
    highest_v = (
        db.query(func.max(ResumeVersion.version_number))
        .filter(ResumeVersion.candidate_resume_id == cand_resume.id)
        .scalar()
        or 0
    )
    next_v = highest_v + 1

    rv = ResumeVersion(
        candidate_resume_id=cand_resume.id,
        version_number=next_v,
        storage_object_key=res.storage_key,
        content_sha256=res.content_sha256,
        file_name=filename,
        file_size_bytes=res.size_bytes,
        mime_type=res.mime_type,
        target_role=target_role.strip() if target_role else None,
        is_archived=False,
        created_by=user_id,
    )
    db.add(rv)

    # Also log in candidate_document table
    doc = CandidateDocument(
        candidate_profile_id=profile.id,
        document_category="RESUME",
        title=f"{cand_resume.resume_title} (v{next_v})",
        file_name=filename,
        file_size_bytes=res.size_bytes,
        mime_type=res.mime_type,
        storage_path=res.storage_key,
        content_sha256=res.content_sha256,
        linked_entity_type="resume_version",
        linked_entity_id=rv.id,
        created_by=user_id,
    )
    db.add(doc)

    db.commit()
    db.refresh(cand_resume)

    calculate_profile_completeness(db, profile.id)

    versions = [
        ResumeVersionResponse.model_validate(v)
        for v in sorted(cand_resume.versions, key=lambda v: v.version_number, reverse=True)
        if not v.is_archived
    ]
    return CandidateResumeResponse(
        id=cand_resume.id,
        candidate_profile_id=cand_resume.candidate_profile_id,
        resume_title=cand_resume.resume_title,
        is_default=cand_resume.is_default,
        versions=versions,
        created_at=cand_resume.created_at,
        updated_at=cand_resume.updated_at,
    )


def set_default_resume(
    db: Session,
    user_id: int,
    resume_id: int,
) -> CandidateResumeResponse:
    """Set a specific resume container as the candidate default."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    target = db.query(CandidateResume).filter(
        CandidateResume.id == resume_id,
        CandidateResume.candidate_profile_id == profile.id,
        CandidateResume.deleted_at.is_(None),
    ).first()
    if not target:
        raise ValueError(f"Resume {resume_id} not found.")

    # Unset other defaults
    db.query(CandidateResume).filter(
        CandidateResume.candidate_profile_id == profile.id,
    ).update({"is_default": False})

    target.is_default = True
    target.updated_by = user_id
    db.commit()
    db.refresh(target)

    versions = [
        ResumeVersionResponse.model_validate(v)
        for v in sorted(target.versions, key=lambda v: v.version_number, reverse=True)
        if not v.is_archived
    ]
    return CandidateResumeResponse(
        id=target.id,
        candidate_profile_id=target.candidate_profile_id,
        resume_title=target.resume_title,
        is_default=target.is_default,
        versions=versions,
        created_at=target.created_at,
        updated_at=target.updated_at,
    )


def delete_resume(db: Session, user_id: int, resume_id: int) -> bool:
    """Soft-delete a resume container and archive its versions."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    target = db.query(CandidateResume).filter(
        CandidateResume.id == resume_id,
        CandidateResume.candidate_profile_id == profile.id,
        CandidateResume.deleted_at.is_(None),
    ).first()
    if not target:
        raise ValueError(f"Resume {resume_id} not found.")

    target.deleted_at = datetime.now(timezone.utc)
    target.is_default = False
    target.updated_by = user_id

    for v in target.versions:
        v.is_archived = True

    db.commit()
    calculate_profile_completeness(db, profile.id)
    return True


def get_resume_version_file(
    db: Session,
    version_id: int,
    requesting_user_id: int,
) -> Tuple[bytes, str, str]:
    """Retrieve resume version binary content with authorization check."""
    rv = (
        db.query(ResumeVersion)
        .join(CandidateResume, ResumeVersion.candidate_resume_id == CandidateResume.id)
        .filter(ResumeVersion.id == version_id)
        .first()
    )
    if not rv:
        raise ValueError("Resume version not found.")

    cand_id = rv.candidate_resume.candidate_profile_id if rv.candidate_resume else None
    if cand_id and not _authorize_candidate_document_access(db, cand_id, requesting_user_id):
        raise ValueError("Access denied to requested resume version.")

    return storage_service.retrieve_file(rv.storage_object_key)


# -----------------------------------------------------------------------------
# Document Vault Management
# -----------------------------------------------------------------------------

def upload_candidate_document(
    db: Session,
    user_id: int,
    category: str,
    title: str,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    linked_entity_type: Optional[str] = None,
    linked_entity_id: Optional[int] = None,
) -> CandidateDocumentResponse:
    """Upload any supporting candidate document into private vault."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    res = storage_service.store_file(
        file_bytes=file_bytes,
        category="certificate" if "CERT" in category else "marksheet",
        original_filename=filename,
        content_type=content_type,
        owner_id=user_id,
    )

    doc = CandidateDocument(
        candidate_profile_id=profile.id,
        document_category=category.upper(),
        title=title.strip(),
        file_name=filename,
        file_size_bytes=res.size_bytes,
        mime_type=res.mime_type,
        storage_path=res.storage_key,
        content_sha256=res.content_sha256,
        linked_entity_type=linked_entity_type,
        linked_entity_id=linked_entity_id,
        created_by=user_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    calculate_profile_completeness(db, profile.id)
    return CandidateDocumentResponse.model_validate(doc)


def list_candidate_documents(
    db: Session,
    user_id: int,
    category: Optional[str] = None,
) -> List[CandidateDocumentResponse]:
    """List private documents belonging to candidate."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    q = db.query(CandidateDocument).filter(
        CandidateDocument.candidate_profile_id == profile.id,
        CandidateDocument.is_archived == False,
    )
    if category:
        q = q.filter(CandidateDocument.document_category == category.upper())

    docs = q.order_by(CandidateDocument.id.desc()).all()
    return [CandidateDocumentResponse.model_validate(d) for d in docs]


def delete_candidate_document(db: Session, user_id: int, document_id: int) -> bool:
    """Archive / soft delete a document."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    doc = db.query(CandidateDocument).filter(
        CandidateDocument.id == document_id,
        CandidateDocument.candidate_profile_id == profile.id,
    ).first()
    if not doc:
        raise ValueError(f"Document {document_id} not found.")

    doc.is_archived = True
    doc.updated_by = user_id
    db.commit()

    calculate_profile_completeness(db, profile.id)
    return True


def get_candidate_document_file(
    db: Session,
    document_id: int,
    requesting_user_id: int,
) -> Tuple[bytes, str, str]:
    """Retrieve candidate document file content with authorization check."""
    doc = db.query(CandidateDocument).filter(
        CandidateDocument.id == document_id,
        CandidateDocument.is_archived == False,
    ).first()
    if not doc:
        raise ValueError("Document not found.")

    if not _authorize_candidate_document_access(db, doc.candidate_profile_id, requesting_user_id):
        raise ValueError("Access denied to requested candidate document.")

    return storage_service.retrieve_file(doc.storage_path)


# -----------------------------------------------------------------------------
# Skills CRUD
# -----------------------------------------------------------------------------

def add_skill(db: Session, user_id: int, request: SkillCreateRequest) -> SkillResponse:
    """Add a technical or soft skill."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    # Check for duplicate skill name
    existing = db.query(CandidateSkill).filter(
        CandidateSkill.candidate_profile_id == profile.id,
        func.lower(CandidateSkill.skill_name) == request.skill_name.strip().lower(),
    ).first()
    if existing:
        raise ValueError(f"Skill '{request.skill_name}' is already present on your profile.")

    skill = CandidateSkill(
        candidate_profile_id=profile.id,
        skill_id=1,  # default taxonomy placeholder
        skill_name=request.skill_name.strip(),
        proficiency_level=request.proficiency_level,
        years_experience=Decimal(str(request.years_experience)) if request.years_experience is not None else None,
        is_primary=request.is_primary,
        created_by=user_id,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)

    calculate_profile_completeness(db, profile.id)
    return SkillResponse(
        id=skill.id,
        candidate_profile_id=skill.candidate_profile_id,
        skill_name=skill.skill_name,
        proficiency_level=skill.proficiency_level or "INTERMEDIATE",
        years_experience=float(skill.years_experience) if skill.years_experience is not None else None,
        is_primary=skill.is_primary if skill.is_primary is not None else False,
    )


def delete_skill(db: Session, user_id: int, skill_id: int) -> bool:
    """Delete a skill from profile."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    skill = db.query(CandidateSkill).filter(
        CandidateSkill.id == skill_id,
        CandidateSkill.candidate_profile_id == profile.id,
    ).first()
    if not skill:
        raise ValueError(f"Skill {skill_id} not found.")

    db.delete(skill)
    db.commit()

    calculate_profile_completeness(db, profile.id)
    return True


# -----------------------------------------------------------------------------
# Projects CRUD
# -----------------------------------------------------------------------------

def add_project(db: Session, user_id: int, request: ProjectCreateRequest) -> ProjectResponse:
    """Add a project to candidate profile."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    proj = CandidateProject(
        candidate_profile_id=profile.id,
        project_name=request.project_name.strip(),
        role_description=request.role_description.strip(),
        technologies=request.technologies.strip() if request.technologies else None,
        project_url=request.project_url.strip() if request.project_url else None,
        description=request.description.strip() if request.description else None,
        start_date=request.start_date,
        end_date=request.end_date,
        outcome=request.outcome.strip() if request.outcome else None,
        created_by=user_id,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectResponse.model_validate(proj)


def delete_project(db: Session, user_id: int, project_id: int) -> bool:
    """Delete a project."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    proj = db.query(CandidateProject).filter(
        CandidateProject.id == project_id,
        CandidateProject.candidate_profile_id == profile.id,
    ).first()
    if not proj:
        raise ValueError(f"Project {project_id} not found.")

    db.delete(proj)
    db.commit()
    return True


# -----------------------------------------------------------------------------
# Certifications CRUD
# -----------------------------------------------------------------------------

def add_certification(db: Session, user_id: int, request: CertificationCreateRequest) -> CertificationResponse:
    """Add a certification."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    cert = CandidateCertification(
        candidate_profile_id=profile.id,
        name=request.name.strip(),
        issuing_organisation=request.issuing_organisation.strip(),
        issue_date=request.issue_date,
        expiry_date=request.expiry_date,
        credential_id=request.credential_id.strip() if request.credential_id else None,
        credential_url=request.credential_url.strip() if request.credential_url else None,
        document_storage_key=request.document_storage_key,
        document_name=request.document_name,
        document_size_bytes=request.document_size_bytes,
        created_by=user_id,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)
    return CertificationResponse.model_validate(cert)


def delete_certification(db: Session, user_id: int, cert_id: int) -> bool:
    """Delete a certification."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    cert = db.query(CandidateCertification).filter(
        CandidateCertification.id == cert_id,
        CandidateCertification.candidate_profile_id == profile.id,
    ).first()
    if not cert:
        raise ValueError(f"Certification {cert_id} not found.")

    db.delete(cert)
    db.commit()
    return True


# -----------------------------------------------------------------------------
# Work Experience CRUD
# -----------------------------------------------------------------------------

def add_work_experience(db: Session, user_id: int, request: WorkExperienceCreateRequest) -> WorkExperienceResponse:
    """Add an internship or employment experience."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    we = CandidateWorkExperience(
        candidate_profile_id=profile.id,
        employer_name=request.employer_name.strip(),
        job_title=request.job_title.strip(),
        start_date=request.start_date,
        end_date=request.end_date,
        is_current=request.is_current,
        description=request.description.strip() if request.description else None,
        created_by=user_id,
    )
    db.add(we)
    db.commit()
    db.refresh(we)
    return WorkExperienceResponse.model_validate(we)


def delete_work_experience(db: Session, user_id: int, experience_id: int) -> bool:
    """Delete a work experience record."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
    if not profile:
        raise CandidateNotFoundError("Candidate profile not found.")

    we = db.query(CandidateWorkExperience).filter(
        CandidateWorkExperience.id == experience_id,
        CandidateWorkExperience.candidate_profile_id == profile.id,
    ).first()
    if not we:
        raise ValueError(f"Work experience {experience_id} not found.")

    db.delete(we)
    db.commit()
    return True
