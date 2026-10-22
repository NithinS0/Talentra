"""Pydantic schemas for Administration, Role Governance, and Security Auditing."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator


class AdminUserRoleGrantRequest(BaseModel):
    """Payload for an administrator to grant a role to a user."""

    user_id: int = Field(..., description="Target user internal account ID")
    role_code: str = Field(..., description="Role code to grant (e.g. SUPER_ADMIN, ADMIN, ACCOUNT_ADMIN, EMPLOYER, RECRUITER, CONSULTANT, PLACEMENT_OFFICER)")
    organisation_id: Optional[int] = Field(default=None, description="Organisation scope for tenant/employer/recruiter roles")
    valid_from: Optional[datetime] = Field(default=None, description="Start date of role validity")
    valid_until: Optional[datetime] = Field(default=None, description="Expiration date of role validity")

    @model_validator(mode="after")
    def validate_dates_and_role(self) -> "AdminUserRoleGrantRequest":
        self.role_code = self.role_code.strip().upper()
        if self.valid_from and self.valid_until and self.valid_until < self.valid_from:
            raise ValueError("valid_until cannot be earlier than valid_from.")
        return self


class AdminUserRoleRevokeRequest(BaseModel):
    """Payload for an administrator to revoke a role assignment."""

    user_id: int = Field(..., description="Target user internal account ID")
    role_code: str = Field(..., description="Role code to revoke")
    organisation_id: Optional[int] = Field(default=None, description="Organisation scope if role is organisation-scoped")
    reason: Optional[str] = Field(default=None, max_length=500, description="Audit rationale for revocation")


class AdminUserStatusUpdateRequest(BaseModel):
    """Payload to activate, suspend, or update user account status."""

    account_status_code_id: int = Field(..., description="1=ACTIVE, 2=SUSPENDED, 3=DEACTIVATED/LOCKED")
    reason: str = Field(..., min_length=3, max_length=500, description="Mandatory audit reason for status change")


class AdminUserResponse(BaseModel):
    """Administrative view of a user account."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email_address: Optional[str] = None
    display_name: str
    account_status_code_id: int
    account_status: str
    roles: List[str]
    actor_ids: List[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class AdminUserListResponse(BaseModel):
    """Paginated list of users for administration."""

    items: List[AdminUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditEventResponse(BaseModel):
    """Audit log entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: Optional[int] = None
    action_code: str
    resource_type: str
    resource_id: Optional[str] = None
    occurred_at: datetime
    request_id: Optional[str] = None
    metadata_redacted: Optional[Dict[str, Any]] = None


class AuditEventListResponse(BaseModel):
    """Paginated list of audit events."""

    items: List[AuditEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SessionRevokeRequest(BaseModel):
    """Payload to revoke an active identity session."""

    session_id: int = Field(..., description="Session ID to revoke")
    reason: Optional[str] = Field(default="Administrative revocation", max_length=500)


class SessionResponse(BaseModel):
    """Identity session response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    started_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_revoked: bool


class ConsentWithdrawRequest(BaseModel):
    """Payload to record privacy or terms consent withdrawal."""

    consent_type_code_id: int = Field(..., description="1=TERMS_OF_SERVICE, 2=PRIVACY_POLICY, 3=DATA_PROCESSING")
    reason: Optional[str] = Field(default=None, max_length=500)


class ConsentRecordResponse(BaseModel):
    """Consent record response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    consent_type_code_id: int
    policy_version: str
    granted: bool
    captured_at: datetime
    withdrawn_at: Optional[datetime] = None


class AccessReviewReportResponse(BaseModel):
    """Privileged access governance and compliance review report."""

    generated_at: datetime
    reviewer_user_id: int
    privileged_users_count: int
    privileged_users: List[Dict[str, Any]]
    audit_correlation_id: str


class DataClassificationItem(BaseModel):
    """Catalog entry for database column data governance classification."""

    table_name: str
    column_name: str
    classification: str  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED_PII
    data_type: str


class DataClassificationResponse(BaseModel):
    """Data classification inventory response."""

    total_classified: int
    unclassified_count: int
    items: List[DataClassificationItem]
