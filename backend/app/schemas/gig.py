"""Gig Marketplace Pydantic Schemas (Module M06).

Defines validation, data contracts, and serialization for:
- Gig worker profile management (FR-0084)
- Gig request creation, pricing and date ranges (FR-0085, FR-0086, FR-0097, FR-0203)
- Gig worker application submissions and decisions (FR-0087, FR-0088)
- Gig worker availability management (FR-0090)
- Assignment, handoff and external fulfilment references (FR-0089, FR-0091, FR-0096)
- External earnings reconciliation (FR-0092)
- Favourite and blacklist management with exclusivity (FR-0093, FR-0095)
- Completed gig rating (FR-0094)
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator


# ==========================================
# Gig Worker Profile Schemas (FR-0084)
# ==========================================

class GigWorkerProfileCreate(BaseModel):
    display_name: str = Field(..., min_length=2, max_length=150)
    bio: Optional[str] = Field(None, max_length=3000)
    availability_status_code_id: int = Field(default=1, ge=1, le=3)  # 1: AVAILABLE, 2: BUSY, 3: UNAVAILABLE


class GigWorkerProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=150)
    bio: Optional[str] = Field(None, max_length=3000)
    availability_status_code_id: Optional[int] = Field(None, ge=1, le=3)


class GigWorkerProfileResponse(BaseModel):
    id: int
    user_id: int
    display_name: str
    bio: Optional[str] = None
    availability_status_code_id: int
    availability_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Gig Request Schemas (FR-0085, FR-0086, FR-0097, FR-0203)
# ==========================================

class GigRequestCreate(BaseModel):
    requester_organisation_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=3, max_length=180)
    description: str = Field(..., min_length=10)
    starts_at: datetime
    ends_at: datetime
    pricing_type_code_id: int = Field(..., ge=1, le=2)  # 1: FIXED, 2: HOURLY / RATE_BASED
    price_amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    currency_code: str = Field(..., min_length=3, max_length=3)

    @field_validator("currency_code")
    def validate_currency(cls, v: str) -> str:
        if not v or len(v.strip()) != 3:
            raise ValueError("Currency code must be a valid 3-letter ISO code.")
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_date_range(self) -> "GigRequestCreate":
        if self.ends_at < self.starts_at:
            raise ValueError("Gig work window end date cannot precede start date.")
        return self


class GigRequestCancel(BaseModel):
    cancellation_reason: str = Field(..., min_length=3, max_length=500)


class GigRequestResponse(BaseModel):
    id: int
    requester_organisation_id: int
    organisation_name: Optional[str] = None
    created_by_user_id: int
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime
    pricing_type_code_id: int
    pricing_type: str
    price_amount: Decimal
    currency_code: str
    status_code_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GigRequestListResponse(BaseModel):
    total: int
    items: List[GigRequestResponse]


# ==========================================
# Gig Application Schemas (FR-0087, FR-0088)
# ==========================================

class GigApplicationCreate(BaseModel):
    notes: Optional[str] = Field(None, max_length=1000)


class GigApplicationDecision(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPTED|REJECTED)$")
    reason: Optional[str] = Field(None, max_length=500)


class GigApplicationResponse(BaseModel):
    id: int
    gig_request_id: int
    gig_request_title: Optional[str] = None
    gig_worker_profile_id: int
    gig_worker_name: Optional[str] = None
    applied_at: datetime
    status_code_id: int
    status: str
    decided_by_user_id: Optional[int] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GigApplicationListResponse(BaseModel):
    total: int
    items: List[GigApplicationResponse]


# ==========================================
# Gig Assignment Schemas (FR-0089, FR-0091, FR-0096)
# ==========================================

class GigAssignmentResponse(BaseModel):
    id: int
    gig_application_id: int
    requester_organisation_id: int
    gig_worker_profile_id: int
    starts_at: datetime
    ends_at: datetime
    status_code_id: int
    status: str
    handoff_reference: Optional[str] = None
    fulfilment_provider_code: Optional[str] = None
    handoff_status: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GigAssignmentListResponse(BaseModel):
    total: int
    items: List[GigAssignmentResponse]


# ==========================================
# Gig Availability Schemas (FR-0090)
# ==========================================

class GigWorkerAvailabilityCreate(BaseModel):
    starts_at: datetime
    ends_at: datetime
    status_code_id: int = Field(default=1, ge=1, le=3)  # 1: AVAILABLE, 2: BOOKED, 3: BLOCKED
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    amount: Optional[Decimal] = Field(None, ge=Decimal("0.00"), decimal_places=2)

    @field_validator("currency_code")
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or len(v.strip()) != 3:
                raise ValueError("Currency code must be a valid 3-letter ISO code.")
            return v.strip().upper()
        return None

    @model_validator(mode="after")
    def validate_date_range(self) -> "GigWorkerAvailabilityCreate":
        if self.ends_at < self.starts_at:
            raise ValueError("Availability end date cannot precede start date.")
        return self


class GigWorkerAvailabilityResponse(BaseModel):
    id: int
    gig_worker_profile_id: int
    status_code_id: int
    status: str
    starts_at: datetime
    ends_at: datetime
    currency_code: Optional[str] = None
    amount: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Gig Earnings Reconciliation Schemas (FR-0092)
# ==========================================

class GigEarningsEventCreate(BaseModel):
    gig_request_id: Optional[int] = None
    gig_worker_profile_id: int
    external_event_reference: str = Field(..., min_length=3, max_length=255)
    amount: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    currency_code: str = Field(..., min_length=3, max_length=3)
    status_code_id: int = Field(default=2, ge=1, le=3)  # 1: ESTIMATED, 2: RECONCILED, 3: PAID

    @field_validator("currency_code")
    def validate_currency(cls, v: str) -> str:
        if not v or len(v.strip()) != 3:
            raise ValueError("Currency code must be a valid 3-letter ISO code.")
        return v.strip().upper()


class GigEarningsResponse(BaseModel):
    id: int
    gig_request_id: Optional[int] = None
    gig_worker_profile_id: int
    external_event_reference: Optional[str] = None
    amount: Decimal
    currency_code: str
    status_code_id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Favourite & Blacklist Exclusivity Schemas (FR-0093, FR-0095)
# ==========================================

class GigWorkerListEntryCreate(BaseModel):
    gig_worker_profile_id: int = Field(..., gt=0)
    list_type: str = Field(..., pattern="^(FAVOURITE|BLACKLISTED)$")


class GigWorkerListEntryResponse(BaseModel):
    id: int
    requester_organisation_id: Optional[int] = None
    gig_worker_profile_id: int
    gig_worker_name: Optional[str] = None
    status_code_id: int
    list_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Completed Gig Rating Schemas (FR-0094)
# ==========================================

class GigRatingCreate(BaseModel):
    gig_assignment_id: int = Field(..., gt=0)
    rating_score: Decimal = Field(..., ge=Decimal("1.00"), le=Decimal("5.00"), decimal_places=2)
    feedback_notes: Optional[str] = Field(None, max_length=1000)


class GigRatingResponse(BaseModel):
    id: int
    gig_request_id: Optional[int] = None
    gig_worker_profile_id: int
    rating_score: Decimal
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
