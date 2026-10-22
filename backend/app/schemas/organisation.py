"""Pydantic schemas for Organisation, Account, and Membership management."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class OrganisationCreateRequest(BaseModel):
    """Payload to register a new organisation."""

    legal_name: str = Field(..., min_length=2, max_length=200, description="Full registered legal business name")
    display_name: str = Field(..., min_length=2, max_length=200, description="Public display / trade name")
    primary_country_id: int = Field(..., description="Country ID referencing country master table")
    organisation_type_code_id: int = Field(default=1, description="1=Commercial, 2=Educational/Academic, 3=Staffing Agency")
    parent_organisation_id: Optional[int] = Field(default=None, description="Optional parent organisation ID in enterprise hierarchy")
    initial_identifier: Optional[str] = Field(default=None, max_length=80, description="Optional tax or registration identifier")
    identifier_type_code_id: Optional[int] = Field(default=1, description="1=Tax ID, 2=Company Number, 3=VAT/GST")

    @model_validator(mode="after")
    def strip_strings(self) -> "OrganisationCreateRequest":
        self.legal_name = self.legal_name.strip()
        self.display_name = self.display_name.strip()
        if self.initial_identifier:
            self.initial_identifier = self.initial_identifier.strip()
        return self


class OrganisationUpdateRequest(BaseModel):
    """Payload to update an organisation profile."""

    legal_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    display_name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    primary_country_id: Optional[int] = Field(default=None)
    organisation_type_code_id: Optional[int] = Field(default=None)
    parent_organisation_id: Optional[int] = Field(default=None)


class OrganisationStatusUpdateRequest(BaseModel):
    """Payload to update organisation status (e.g., active, suspended, deactivated)."""

    status_code_id: int = Field(..., description="1=ACTIVE, 2=INACTIVE/SUSPENDED, 3=DEACTIVATED")
    reason: Optional[str] = Field(default=None, max_length=500, description="Audit reason for status change")


class OrganisationResponse(BaseModel):
    """Detailed organisation response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    legal_name: str
    display_name: str
    organisation_type_code_id: int
    status_code_id: int
    status_code: str
    parent_organisation_id: Optional[int] = None
    primary_country_id: Optional[int] = None
    primary_country_name: Optional[str] = None
    created_at: datetime
    created_by: Optional[int] = None
    updated_at: datetime
    updated_by: Optional[int] = None
    deleted_at: Optional[datetime] = None


class OrganisationListResponse(BaseModel):
    """Paginated list of organisations."""

    items: List[OrganisationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrganisationIdentifierCreateRequest(BaseModel):
    """Payload to add a tax or registration identifier to an organisation."""

    country_id: int = Field(..., description="Country ID for which this tax/registration ID is issued")
    identifier_type_code_id: int = Field(..., description="1=Tax ID, 2=Company Number, 3=VAT, 4=EIN, 5=PAN")
    identifier_value: str = Field(..., min_length=2, max_length=80, description="Raw identifier string preserving leading zeros")

    @model_validator(mode="after")
    def validate_identifier(self) -> "OrganisationIdentifierCreateRequest":
        self.identifier_value = self.identifier_value.strip()
        if not self.identifier_value:
            raise ValueError("Identifier value cannot be empty.")
        return self


class OrganisationIdentifierResponse(BaseModel):
    """Masked identifier response (raw numbers are never exposed in lists)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    country_id: int
    identifier_type_code_id: int
    masked_identifier: str
    created_at: datetime


class OrganisationLocationCreateRequest(BaseModel):
    """Payload to add an operational location."""

    name: str = Field(..., min_length=2, max_length=200, description="Office / Site name or City, Country")
    country_id: int = Field(..., description="Geographic country ID")


class OrganisationLocationResponse(BaseModel):
    """Location response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    name: str
    status_code_id: int
    created_at: datetime


class OrganisationVerificationRequest(BaseModel):
    """Payload to trigger verification for an organisation."""

    name: Optional[str] = Field(default="Corporate Entity Verification", max_length=200)
    simulate_outage: bool = Field(default=False, description="For testing provider outage handling")


class OrganisationVerificationResponse(BaseModel):
    """Verification outcome response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    status_code_id: int
    status: str
    name: str
    message: str
    created_at: datetime


class RecruiterAssignRequest(BaseModel):
    """Payload to map a recruiter to an organisation."""

    recruiter_user_id: int = Field(..., description="User ID of the recruiter")
    valid_from: Optional[datetime] = Field(default=None, description="Start of mapping validity")
    valid_until: Optional[datetime] = Field(default=None, description="End of mapping validity (must be >= valid_from)")

    @model_validator(mode="after")
    def validate_dates(self) -> "RecruiterAssignRequest":
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from.")
        return self


class RecruiterMappingResponse(BaseModel):
    """Recruiter mapping response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organisation_id: int
    recruiter_user_id: int
    recruiter_actor_id: Optional[str] = None
    recruiter_name: Optional[str] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    assigned_by_user_id: int
    created_at: datetime


class OrganisationMemberAssignRequest(BaseModel):
    """Payload to assign a member/role to an organisation."""

    user_id: int = Field(..., description="User ID to assign")
    role_code: str = Field(..., description="Target role: ACCOUNT_ADMIN, EMPLOYER, RECRUITER, PLACEMENT_OFFICER")
    valid_from: Optional[datetime] = Field(default=None)
    valid_until: Optional[datetime] = Field(default=None)

    @model_validator(mode="after")
    def validate_dates(self) -> "OrganisationMemberAssignRequest":
        self.role_code = self.role_code.strip().upper()
        allowed = {"ACCOUNT_ADMIN", "EMPLOYER", "RECRUITER", "PLACEMENT_OFFICER"}
        if self.role_code not in allowed:
            raise ValueError(f"Role '{self.role_code}' cannot be assigned as an organisation member. Must be one of: {sorted(allowed)}")
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from.")
        return self


class OrganisationMemberResponse(BaseModel):
    """Organisation member assignment response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    organisation_id: int
    role_code: str
    actor_id: Optional[str] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    assigned_by_user_id: int
