"""Candidate Registration, Profile, Academic, Resume, and Document Schemas."""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CandidateRegisterRequest(BaseModel):
    """Candidate self-registration payload."""
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=150, description="Legal first name")
    last_name: str = Field(min_length=1, max_length=150, description="Legal last name")
    middle_name: Optional[str] = Field(default=None, max_length=150, description="Optional middle name")
    country_code: str = Field(min_length=2, max_length=2, description="2-letter ISO 3166-1 alpha-2 country code")
    phone_number: Optional[str] = Field(default=None, description="Contact phone number")
    headline: Optional[str] = Field(default=None, max_length=240, description="Professional headline")
    summary: Optional[str] = Field(default=None, description="Brief professional summary")


class CandidateProfileUpdateRequest(BaseModel):
    """Candidate profile edit payload."""
    model_config = ConfigDict(extra="forbid")

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    middle_name: Optional[str] = Field(default=None, max_length=150)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    headline: Optional[str] = Field(default=None, max_length=240)
    summary: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    country_code: Optional[str] = Field(default=None, min_length=2, max_length=2)
    current_city: Optional[str] = Field(default=None, max_length=100)
    current_state: Optional[str] = Field(default=None, max_length=100)
    linkedin_url: Optional[str] = Field(default=None, max_length=255)
    github_url: Optional[str] = Field(default=None, max_length=255)
    portfolio_url: Optional[str] = Field(default=None, max_length=255)
    preferred_roles: Optional[str] = Field(default=None)
    preferred_locations: Optional[str] = Field(default=None)
    preferred_employment_types: Optional[str] = Field(default=None)
    expected_graduation_date: Optional[date] = Field(default=None)
    availability_status: Optional[str] = Field(default="AVAILABLE", max_length=50)
    is_public_visible: Optional[bool] = Field(default=True)
    consent_placement_rules: Optional[bool] = Field(default=True)
    consent_share_with_employers: Optional[bool] = Field(default=True)


class CompletenessItem(BaseModel):
    """Checklist item for profile completeness."""
    key: str
    section: str
    title: str
    is_complete: bool
    weight: int
    missing_reason: Optional[str] = None
    deep_link: str


class ProfileCompletenessResponse(BaseModel):
    """Profile completeness score and missing items checklist."""
    overall_score: float = Field(description="Percentage from 0.0 to 100.0")
    is_placement_eligible: bool
    checklist_items: List[CompletenessItem]


class SemesterCreateUpdateRequest(BaseModel):
    """Create or update semester marksheet record."""
    model_config = ConfigDict(extra="forbid")

    semester_number: int = Field(ge=1, le=12, description="Semester number (1..12)")
    academic_term: Optional[str] = Field(default=None, max_length=50, description="e.g. Fall 2024 or Term 1")
    result_status: str = Field(default="PASS", description="PASS, FAIL, AWAITED, ARREAR, SUPPLEMENTARY")
    sgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    credits_registered: Optional[int] = Field(default=None, ge=0)
    credits_earned: Optional[int] = Field(default=None, ge=0)
    has_backlog: bool = Field(default=False)
    backlog_details: Optional[str] = Field(default=None)
    grade_sheet_storage_key: Optional[str] = Field(default=None, max_length=500)
    grade_sheet_name: Optional[str] = Field(default=None, max_length=255)
    grade_sheet_size_bytes: Optional[int] = Field(default=None)
    grade_sheet_mime_type: Optional[str] = Field(default=None, max_length=100)


class SemesterResponse(BaseModel):
    """Semester grade and marksheet response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_education_id: int
    semester_number: int
    academic_term: Optional[str] = None
    result_status: str
    sgpa: Optional[float] = None
    cgpa: Optional[float] = None
    credits_registered: Optional[int] = None
    credits_earned: Optional[int] = None
    has_backlog: bool
    backlog_details: Optional[str] = None
    grade_sheet_storage_key: Optional[str] = None
    grade_sheet_name: Optional[str] = None
    grade_sheet_size_bytes: Optional[int] = None
    grade_sheet_mime_type: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class EducationCreateRequest(BaseModel):
    """New education qualification record."""
    model_config = ConfigDict(extra="forbid")

    education_level: str = Field(description="CLASS_10, CLASS_12, DIPLOMA, UNDERGRADUATE, POSTGRADUATE")
    institution_name: str = Field(min_length=1, max_length=250)
    board_or_university: Optional[str] = Field(default=None, max_length=200)
    field_of_study: Optional[str] = Field(default=None, max_length=150)
    stream_specialization: Optional[str] = Field(default=None, max_length=150)
    status: str = Field(default="COMPLETED", description="COMPLETED, PURSUING, INCOMPLETE")
    start_year: Optional[int] = Field(default=None, ge=1970, le=2040)
    completion_year: Optional[int] = Field(default=None, ge=1970, le=2040)
    grading_system: str = Field(default="PERCENTAGE", description="PERCENTAGE, CGPA_10, CGPA_4, MARKS")
    score_value: Optional[float] = Field(default=None, ge=0.0)
    max_score: Optional[float] = Field(default=None, ge=0.0)
    percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    has_backlogs: bool = Field(default=False)
    active_backlogs_count: int = Field(default=0, ge=0)
    historical_backlogs_count: int = Field(default=0, ge=0)
    document_storage_key: Optional[str] = Field(default=None, max_length=500)
    document_name: Optional[str] = Field(default=None, max_length=255)
    document_size_bytes: Optional[int] = Field(default=None)
    document_mime_type: Optional[str] = Field(default=None, max_length=100)


class EducationUpdateRequest(BaseModel):
    """Update existing education record."""
    model_config = ConfigDict(extra="forbid")

    education_level: Optional[str] = None
    institution_name: Optional[str] = None
    board_or_university: Optional[str] = None
    field_of_study: Optional[str] = None
    stream_specialization: Optional[str] = None
    status: Optional[str] = None
    start_year: Optional[int] = None
    completion_year: Optional[int] = None
    grading_system: Optional[str] = None
    score_value: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    has_backlogs: Optional[bool] = None
    active_backlogs_count: Optional[int] = None
    historical_backlogs_count: Optional[int] = None
    document_storage_key: Optional[str] = None
    document_name: Optional[str] = None
    document_size_bytes: Optional[int] = None
    document_mime_type: Optional[str] = None


class EducationResponse(BaseModel):
    """Education qualification with attached semester grade sheets."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    education_level: str
    institution_name: str
    board_or_university: Optional[str] = None
    field_of_study: Optional[str] = None
    stream_specialization: Optional[str] = None
    status: str
    start_year: Optional[int] = None
    completion_year: Optional[int] = None
    grading_system: str
    score_value: Optional[float] = None
    max_score: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    has_backlogs: bool
    active_backlogs_count: int
    historical_backlogs_count: int
    document_storage_key: Optional[str] = None
    document_name: Optional[str] = None
    document_size_bytes: Optional[int] = None
    document_mime_type: Optional[str] = None
    semesters: List[SemesterResponse] = []
    created_at: datetime
    updated_at: datetime


class ResumeVersionResponse(BaseModel):
    """Resume version metadata."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_resume_id: int
    version_number: int
    storage_object_key: str
    file_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    mime_type: str
    target_role: Optional[str] = None
    is_archived: bool
    created_at: datetime


class CandidateResumeResponse(BaseModel):
    """Candidate resume container with versions."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    resume_title: str
    is_default: bool
    versions: List[ResumeVersionResponse] = []
    created_at: datetime
    updated_at: datetime


class CandidateDocumentResponse(BaseModel):
    """Candidate uploaded document metadata."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    document_category: str
    title: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    storage_path: str
    content_sha256: str
    is_verified: bool
    is_archived: bool
    linked_entity_type: Optional[str] = None
    linked_entity_id: Optional[int] = None
    created_at: datetime


class SkillCreateRequest(BaseModel):
    """Add a skill."""
    model_config = ConfigDict(extra="forbid")

    skill_name: str = Field(min_length=1, max_length=100)
    proficiency_level: str = Field(default="INTERMEDIATE", description="BEGINNER, INTERMEDIATE, EXPERT")
    years_experience: Optional[float] = Field(default=None, ge=0.0)
    is_primary: bool = Field(default=False)


class SkillResponse(BaseModel):
    """Skill details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    skill_name: Optional[str] = None
    proficiency_level: str
    years_experience: Optional[float] = None
    is_primary: bool


class ProjectCreateRequest(BaseModel):
    """Add a project."""
    model_config = ConfigDict(extra="forbid")

    project_name: str = Field(min_length=1, max_length=180)
    role_description: str = Field(min_length=1, max_length=240)
    technologies: Optional[str] = Field(default=None, max_length=255)
    project_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    outcome: Optional[str] = Field(default=None, max_length=255)


class ProjectResponse(BaseModel):
    """Project details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    project_name: str
    role_description: str
    technologies: Optional[str] = None
    project_url: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    outcome: Optional[str] = None


class CertificationCreateRequest(BaseModel):
    """Add a certification."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    issuing_organisation: str = Field(min_length=1, max_length=200)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(default=None, max_length=100)
    credential_url: Optional[str] = Field(default=None, max_length=500)
    document_storage_key: Optional[str] = Field(default=None, max_length=500)
    document_name: Optional[str] = Field(default=None, max_length=255)
    document_size_bytes: Optional[int] = None


class CertificationResponse(BaseModel):
    """Certification details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    name: str
    issuing_organisation: str
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    document_storage_key: Optional[str] = None
    document_name: Optional[str] = None
    document_size_bytes: Optional[int] = None


class WorkExperienceCreateRequest(BaseModel):
    """Add work experience."""
    model_config = ConfigDict(extra="forbid")

    employer_name: str = Field(min_length=1, max_length=180)
    job_title: str = Field(min_length=1, max_length=180)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = Field(default=False)
    description: Optional[str] = Field(default=None)


class WorkExperienceResponse(BaseModel):
    """Work experience details."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    employer_name: str
    job_title: str
    start_date: date
    end_date: Optional[date] = None
    is_current: bool
    description: Optional[str] = None


class CandidateProfileResponse(BaseModel):
    """Complete Candidate profile details including server-allocated actor ID and nested sections."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int = Field(description="Talentra internal account ID")
    actor_id: str = Field(description="Allocated public Candidate ID (CAxxxxx)")
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    display_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    profile_photo_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    email_address: Optional[str] = None
    phone_e164: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    preferred_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    preferred_employment_types: Optional[str] = None
    expected_graduation_date: Optional[date] = None
    availability_status: str
    is_public_visible: bool
    consent_placement_rules: bool
    consent_share_with_employers: bool
    completion_score: float = Field(description="Profile completeness percentage (0.0 to 100.0)")
    education_records: List[EducationResponse] = []
    resumes: List[CandidateResumeResponse] = []
    documents: List[CandidateDocumentResponse] = []
    skills: List[SkillResponse] = []
    projects: List[ProjectResponse] = []
    work_experiences: List[WorkExperienceResponse] = []
    certifications: List[CertificationResponse] = []
    created_at: datetime
    updated_at: datetime
