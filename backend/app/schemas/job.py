"""Job Requisition, Position, and Eligibility Schemas."""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobCreateRequest(BaseModel):
    """Job requirement creation payload."""
    model_config = ConfigDict(extra="forbid")

    organisation_id: int = Field(description="Target Employer organisation ID")
    job_role_id: int = Field(description="Job role taxonomy ID")
    title: str = Field(min_length=3, max_length=180, description="Job title")
    description: str = Field(min_length=10, description="Full job description")
    employment_type_id: int = Field(description="Employment type ID (e.g. Full-time)")
    work_type_id: int = Field(description="Work type ID (e.g. Remote, Hybrid, On-site)")
    positions_count: int = Field(default=1, gt=0, description="Number of positions open (> 0)")
    salary_min: Optional[Decimal] = Field(default=None, ge=0, description="Minimum salary")
    salary_max: Optional[Decimal] = Field(default=None, ge=0, description="Maximum salary")
    salary_currency_code: Optional[str] = Field(default="INR", min_length=3, max_length=3, description="ISO 4217 currency code")
    application_deadline: Optional[datetime] = Field(default=None, description="Application deadline")
    open_to_consultants: bool = Field(default=False, description="Whether open to external sourcing consultants")
    publish_now: bool = Field(default=False, description="Publish immediately instead of saving as draft")

    # Structured requirements and eligibility criteria
    responsibilities: Optional[str] = Field(default=None, description="Key responsibilities")
    required_skills: Optional[str] = Field(default=None, description="Comma-separated required skills")
    preferred_skills: Optional[str] = Field(default=None, description="Comma-separated preferred skills")
    required_qualifications: Optional[str] = Field(default=None, description="e.g. B.Tech, B.E, MCA, Diploma")
    accepted_branches: Optional[str] = Field(default=None, description="e.g. Computer Science, Information Technology")
    min_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100, description="Minimum percentage required")
    min_cgpa: Optional[Decimal] = Field(default=None, ge=0, le=10, description="Minimum CGPA required (on 10.0 scale)")
    allow_backlogs: bool = Field(default=False, description="Whether active backlogs are allowed")
    max_active_backlogs: int = Field(default=0, ge=0, description="Maximum active backlogs allowed")
    min_experience_years: Optional[Decimal] = Field(default=None, ge=0, description="Minimum years of experience")
    max_experience_years: Optional[Decimal] = Field(default=None, ge=0, description="Maximum years of experience")
    location_city: Optional[str] = Field(default=None, max_length=100)
    location_country: Optional[str] = Field(default=None, max_length=100)
    required_documents: Optional[str] = Field(default=None, description="Comma-separated required documents")

    @model_validator(mode="after")
    def validate_salary_and_deadline(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max cannot be less than salary_min.")
        if self.application_deadline is not None:
            now = datetime.now(timezone.utc)
            dl = self.application_deadline if self.application_deadline.tzinfo else self.application_deadline.replace(tzinfo=timezone.utc)
            if dl < now:
                raise ValueError("application_deadline must be a future date.")
        return self


class JobUpdateRequest(BaseModel):
    """Job requirement update payload."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=3, max_length=180)
    description: Optional[str] = Field(default=None, min_length=10)
    employment_type_id: Optional[int] = None
    work_type_id: Optional[int] = None
    positions_count: Optional[int] = Field(default=None, gt=0)
    salary_min: Optional[Decimal] = Field(default=None, ge=0)
    salary_max: Optional[Decimal] = Field(default=None, ge=0)
    salary_currency_code: Optional[str] = Field(default=None, min_length=3, max_length=3)
    application_deadline: Optional[datetime] = None
    open_to_consultants: Optional[bool] = None

    # Structured requirements and eligibility criteria
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    preferred_skills: Optional[str] = None
    required_qualifications: Optional[str] = None
    accepted_branches: Optional[str] = None
    min_percentage: Optional[Decimal] = None
    min_cgpa: Optional[Decimal] = None
    allow_backlogs: Optional[bool] = None
    max_active_backlogs: Optional[int] = None
    min_experience_years: Optional[Decimal] = None
    max_experience_years: Optional[Decimal] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    required_documents: Optional[str] = None

    @model_validator(mode="after")
    def validate_salary_and_deadline(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_max < self.salary_min:
                raise ValueError("salary_max cannot be less than salary_min.")
        return self


class JobStatusUpdateRequest(BaseModel):
    """Change status and publish state of a job."""
    model_config = ConfigDict(extra="forbid")

    status: Optional[str] = Field(default=None, description="DRAFT, OPEN, CLOSED, or CANCELLED")
    publish_state: Optional[str] = Field(default=None, description="UNPUBLISHED, PUBLISHED, or ARCHIVED")


class JobResponse(BaseModel):
    """Job requirement details response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    organisation_name: str
    job_role_id: int
    job_role_name: str
    title: str
    description: str
    employment_type_id: int
    employment_type: str
    work_type_id: int
    work_type: str
    status: str
    publish_state: str
    open_to_consultants: bool
    positions_count: int
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency_code: Optional[str] = None
    application_deadline: Optional[datetime] = None
    applications_count: int = 0

    # Structured criteria
    responsibilities: Optional[str] = None
    required_skills: Optional[str] = None
    preferred_skills: Optional[str] = None
    required_qualifications: Optional[str] = None
    accepted_branches: Optional[str] = None
    min_percentage: Optional[float] = None
    min_cgpa: Optional[float] = None
    allow_backlogs: bool = False
    max_active_backlogs: int = 0
    min_experience_years: Optional[float] = None
    max_experience_years: Optional[float] = None
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    required_documents: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    """Paginated list of job requirements."""
    model_config = ConfigDict(from_attributes=True)

    items: List[JobResponse]
    total: int
    page: int
    page_size: int
    pages: int


class CriterionResult(BaseModel):
    """Evaluation result for an individual eligibility requirement."""
    criterion: str
    required_value: str
    candidate_value: Optional[str] = None
    status: str = Field(description="SATISFIED, UNSATISFIED, or UNABLE_TO_DETERMINE")
    explanation: str


class JobEligibilityResponse(BaseModel):
    """Complete candidate-to-job eligibility evaluation."""
    job_id: int
    candidate_id: int
    overall_status: str = Field(description="ELIGIBLE, NOT_ELIGIBLE, or UNABLE_TO_DETERMINE")
    can_apply: bool
    criteria: List[CriterionResult]
    missing_requirements: List[str]
