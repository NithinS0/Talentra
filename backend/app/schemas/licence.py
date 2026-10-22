"""Pydantic Schemas for Module M07: Licences, Seats, Devices & Sessions.

Compliant with:
- FR-0098: Positive user licence limit
- FR-0099: Positive device limit
- FR-0100: Seat limit enforcement
- FR-0101: Device limit at login
- FR-0102: Expired session exclusion
- FR-0103: Revoked session exclusion
- FR-0104: Session activity metadata
- FR-0105: Concurrent login race
- FR-0106: Device revocation audit
- FR-0107: Licence assignment scope
- FR-0108: Duplicate active device
- FR-0109: Session end release
- FR-0110: Seat release on unassignment
- FR-0111: Login limit audit on rejection
- FR-0204: Expired session cleanup idempotent
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. Licence Schemas
# ==========================================

class LicenceCreate(BaseModel):
    """Schema for creating a new subscription licence."""

    licence_code: str = Field(..., min_length=3, max_length=80, description="Unique alphanumeric licence code")
    account_id: int = Field(..., description="ID of the customer account")
    max_users: int = Field(..., description="Positive integer seat capacity limit (FR-0098)")
    max_devices_per_user: int = Field(..., description="Positive integer device limit per user (FR-0099)")
    valid_from: datetime = Field(..., description="Start of validity window")
    valid_until: datetime = Field(..., description="End of validity window")

    @field_validator("max_users")
    @classmethod
    def validate_positive_max_users(cls, v: int) -> int:
        if v is None or v <= 0:
            raise ValueError("max_users must be a positive integer greater than 0")
        return v

    @field_validator("max_devices_per_user")
    @classmethod
    def validate_positive_max_devices(cls, v: int) -> int:
        if v is None or v <= 0:
            raise ValueError("max_devices_per_user must be a positive integer greater than 0")
        return v

    @field_validator("valid_until")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        valid_from = info.data.get("valid_from")
        if valid_from and v <= valid_from:
            raise ValueError("valid_until must be after valid_from")
        return v


class LicenceStatusUpdate(BaseModel):
    """Schema for updating licence lifecycle state."""

    status_code_id: int = Field(..., description="1=ACTIVE, 2=SUSPENDED, 3=REVOKED, 4=EXPIRED")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for lifecycle transition")


class LicenceResponse(BaseModel):
    """Detailed licence response with capacity metrics."""

    id: int
    licence_code: str
    account_id: int
    max_users: int
    max_devices_per_user: int
    valid_from: datetime
    valid_until: datetime
    status_code_id: int
    status: str
    allocated_seats: int
    available_seats: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Seat Allocation Schemas
# ==========================================

class SeatAllocationCreate(BaseModel):
    """Schema for assigning a user to a licence seat."""

    licence_id: int = Field(..., description="Target licence ID")
    user_id: int = Field(..., description="Target user ID to allocate seat to")
    expires_at: Optional[datetime] = Field(None, description="Optional seat expiration timestamp")


class SeatAllocationResponse(BaseModel):
    """Detailed seat allocation response."""

    id: int
    licence_id: int
    user_id: int
    status_code_id: int
    status: str
    occurred_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. Device Registration & Revocation Schemas
# ==========================================

class DeviceRegisterRequest(BaseModel):
    """Schema for registering a user device using SHA-256 fingerprint hash."""

    device_fingerprint_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 fingerprint hash of client device (FR-0108)",
    )
    device_label: Optional[str] = Field(None, max_length=150, description="Human-readable label (e.g. Chrome on Windows)")

    @field_validator("device_fingerprint_hash")
    @classmethod
    def validate_hash_hex(cls, v: str) -> str:
        if len(v) != 64:
            raise ValueError("device_fingerprint_hash must be exactly 64 characters")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("device_fingerprint_hash must be a valid hex string")
        return v.lower()


class DeviceRevocationRequest(BaseModel):
    """Schema for revoking a device and its linked active sessions."""

    reason: str = Field(..., min_length=3, max_length=500, description="Reason for revocation (FR-0106)")


class DeviceResponse(BaseModel):
    """Registered device response representation."""

    id: int
    user_id: int
    device_fingerprint_hash: str
    device_label: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    revoked_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. Session Schemas
# ==========================================

class SessionCreateRequest(BaseModel):
    """Schema for creating a new authenticated session (FR-0101, FR-0104)."""

    device_id: Optional[int] = Field(None, description="ID of registered device, if pre-registered")
    device_fingerprint_hash: Optional[str] = Field(None, min_length=64, max_length=64, description="Fingerprint hash")
    device_label: Optional[str] = Field(None, max_length=150, description="Label for new device auto-registration")
    provider_session_reference: Optional[str] = Field(None, max_length=255, description="Supabase auth session ref")
    duration_seconds: int = Field(default=86400, ge=60, le=2592000, description="Session lifespan in seconds")


class SessionRevocationRequest(BaseModel):
    """Schema for explicit session revocation."""

    reason: str = Field(..., min_length=3, max_length=500, description="Reason for session revocation")


class SessionResponse(BaseModel):
    """Session representation with activity metadata."""

    id: int
    user_id: int
    device_id: Optional[int] = None
    device_label: Optional[str] = None
    provider_session_reference: Optional[str] = None
    started_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Cleanup & Monitoring Schemas
# ==========================================

class SessionCleanupResponse(BaseModel):
    """Result of idempotent expired session cleanup (FR-0204)."""

    cleaned_count: int
    timestamp: datetime
    status: str = "COMPLETED"


class LicenceUsageResponse(BaseModel):
    """Summary of licence capacity and utilisation."""

    licence_id: int
    licence_code: str
    account_id: int
    max_users: int
    allocated_seats: int
    available_seats: int
    max_devices_per_user: int
    status: str
