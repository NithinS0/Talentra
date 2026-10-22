"""Pydantic schemas for Sourcing & Consultant Requests, Shortlists, and Outreach."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, model_validator


# -------------------------------------------------------------------------
# Sourcing Requests
# -------------------------------------------------------------------------

class SourcingRequestCreate(BaseModel):
    """Payload to create a candidate sourcing request for a job requirement."""

    job_requirement_id: int = Field(..., description="Target job requirement ID")
    consultant_user_id: Optional[int] = Field(default=None, description="Optional target consultant user ID")


class SourcingRequestDecision(BaseModel):
    """Payload for a consultant or employer to accept/decline a sourcing request."""

    decision: str = Field(..., description="Decision outcome: 'ACCEPT' or 'DECLINE'")
    reason: Optional[str] = Field(default=None, max_length=500, description="Optional explanation or audit rationale")

    @model_validator(mode="after")
    def validate_decision(self) -> "SourcingRequestDecision":
        self.decision = self.decision.strip().upper()
        if self.decision not in {"ACCEPT", "DECLINE"}:
            raise ValueError("Decision must be either 'ACCEPT' or 'DECLINE'.")
        return self


class SourcingRequestCancel(BaseModel):
    """Payload to cancel an active sourcing request."""

    reason: Optional[str] = Field(default="Cancelled by employer", max_length=500)


class SourcingRequestResponse(BaseModel):
    """Sourcing request detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_requirement_id: int
    job_title: str
    organisation_id: int
    organisation_name: str
    requester_user_id: int
    consultant_user_id: Optional[int] = None
    consultant_name: Optional[str] = None
    status_code_id: int
    status: str
    open_to_consultants_snapshot: bool
    requested_at: datetime
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SourcingRequestListResponse(BaseModel):
    """Paginated list of sourcing requests."""

    items: List[SourcingRequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# -------------------------------------------------------------------------
# Sourcing Shortlist
# -------------------------------------------------------------------------

class CandidateShortlistCreate(BaseModel):
    """Payload to add a candidate to the sourcing shortlist."""

    candidate_profile_id: int = Field(..., description="Target candidate profile ID")
    sourcing_request_id: Optional[int] = Field(default=None, description="Optional associated sourcing request ID")
    title: Optional[str] = Field(default=None, max_length=180, description="Shortlist item title or note")
    description: Optional[str] = Field(default=None, max_length=4000, description="Detailed sourcing assessment notes")


class CandidateShortlistResponse(BaseModel):
    """Sourced candidate shortlist item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_profile_id: int
    candidate_actor_id: Optional[str] = None
    candidate_name: Optional[str] = None
    user_id: int
    status_code_id: int
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class CandidateShortlistListResponse(BaseModel):
    """Paginated candidate shortlist response."""

    items: List[CandidateShortlistResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# -------------------------------------------------------------------------
# Outreach Campaign & Delivery Callbacks
# -------------------------------------------------------------------------

class OutreachBatchCreate(BaseModel):
    """Payload to launch a bulk candidate outreach campaign."""

    organisation_id: int = Field(..., description="Employer organisation ID launching the outreach")
    job_requirement_id: Optional[int] = Field(default=None, description="Optional job requirement context")
    candidate_profile_ids: List[int] = Field(..., min_length=1, description="List of candidate profile IDs to contact")


class OutreachRecipientResponse(BaseModel):
    """Individual outreach recipient delivery status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    outreach_batch_id: int
    candidate_profile_id: int
    delivery_status_code_id: int
    delivery_status: str
    provider_message_reference: Optional[str] = None
    idempotency_key: str
    created_at: datetime


class OutreachBatchResponse(BaseModel):
    """Outreach batch response with recipient breakdown."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    job_requirement_id: Optional[int] = None
    created_by_user_id: int
    status_code_id: int
    status: str
    recipient_count: int
    suppressed_count: int = 0
    recipients: List[OutreachRecipientResponse] = []
    created_at: datetime


class OutreachDeliveryCallback(BaseModel):
    """Provider webhook callback payload for message delivery updates."""

    idempotency_key: str = Field(..., description="Delivery idempotency key corresponding to recipient")
    provider_message_reference: str = Field(..., description="External provider message ID")
    status: str = Field(..., description="DELIVERED or FAILED")
    error_message: Optional[str] = Field(default=None, description="Failure reason if failed")

    @model_validator(mode="after")
    def validate_status(self) -> "OutreachDeliveryCallback":
        self.status = self.status.strip().upper()
        if self.status not in {"DELIVERED", "FAILED"}:
            raise ValueError("Status must be either 'DELIVERED' or 'FAILED'.")
        return self


# -------------------------------------------------------------------------
# Privacy-Preserving Candidate Profile for Consultants
# -------------------------------------------------------------------------

class ConsultantCandidateProfileResponse(BaseModel):
    """Candidate profile viewed by consultants with sensitive fields masked."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_id: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    email_address_masked: Optional[str] = None
    phone_masked: Optional[str] = None
    completion_score: Decimal
    is_blocked: bool = False
