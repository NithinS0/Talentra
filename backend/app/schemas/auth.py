"""Authentication and Account Schemas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AuthClaims(BaseModel):
    """Verified claims extracted from Supabase Auth JWT."""
    sub: str = Field(description="Supabase Auth subject UUID")
    email: Optional[str] = Field(default=None, description="User email address")
    role: Optional[str] = Field(default=None, description="Supabase auth role (e.g. authenticated)")
    aud: Optional[str] = Field(default=None, description="Audience claim")
    exp: Optional[int] = Field(default=None, description="Expiration UNIX timestamp")
    iat: Optional[int] = Field(default=None, description="Issued-at UNIX timestamp")
    app_metadata: Dict[str, Any] = Field(default_factory=dict)
    user_metadata: Dict[str, Any] = Field(default_factory=dict)


class ActorIdentityItem(BaseModel):
    """Public actor identity associated with user."""
    model_config = ConfigDict(from_attributes=True)

    role_code: str = Field(description="Role code e.g. CANDIDATE, EMPLOYER")
    actor_prefix: str = Field(description="2-letter prefix e.g. CA, EM")
    actor_id: str = Field(description="Formatted 7-char public identifier e.g. CA00001")
    organisation_id: Optional[int] = Field(default=None, description="Organisation ID if scoped")
    is_active: bool = Field(default=True, description="Identity active status")


class RoleAssignmentItem(BaseModel):
    """Assigned role details."""
    model_config = ConfigDict(from_attributes=True)

    role_code: str
    display_name: str
    actor_id: Optional[str] = None
    organisation_id: Optional[int] = None
    valid_from: datetime


class UserProfileResponse(BaseModel):
    """Authenticated user profile with assigned roles and public actor IDs."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int = Field(description="Talentra internal canonical account ID")
    display_name: str = Field(description="Display name")
    email_address: Optional[str] = Field(default=None, description="Verified email address")
    phone_e164: Optional[str] = Field(default=None, description="E.164 formatted phone number")
    provider_subject: str = Field(description="Supabase Auth subject UUID")
    roles: List[str] = Field(default_factory=list, description="List of active role codes")
    actor_identities: List[ActorIdentityItem] = Field(default_factory=list, description="Public actor identities")
    created_at: datetime
