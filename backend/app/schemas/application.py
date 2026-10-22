"""Job Application and Status Schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ApplicationSubmitRequest(BaseModel):
    """Candidate job application submission payload."""
    model_config = ConfigDict(extra="forbid")

    cover_letter: Optional[str] = Field(default=None, max_length=8000, description="Optional cover letter")
    resume_version_id: Optional[int] = Field(default=None, description="Optional attached resume version ID")


class ApplicationStatusUpdateRequest(BaseModel):
    """Recruiter / Employer status change payload."""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Target status: SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN")
    notes: Optional[str] = Field(default=None, description="Optional transition notes")


class ApplicationResponse(BaseModel):
    """Job application details response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_requirement_id: int
    job_title: str
    organisation_id: int
    organisation_name: str
    candidate_profile_id: int
    candidate_actor_id: str
    candidate_name: str
    candidate_headline: Optional[str] = None
    status: str
    resume_version_id: Optional[int] = None
    resume_snapshot_title: Optional[str] = None
    resume_snapshot_file_name: Optional[str] = None
    eligibility_status: Optional[str] = None
    eligibility_notes: Optional[str] = None
    cover_letter: Optional[str] = None
    applied_at: datetime
    last_status_changed_at: datetime


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""
    model_config = ConfigDict(from_attributes=True)

    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    pages: int
