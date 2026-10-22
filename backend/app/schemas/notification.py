"""Pydantic Schemas for Module M10: Notifications, Preferences & Community.

Compliant with:
- FR-0139: Notification preference persistence (channel/category explicit values)
- FR-0140: Job alert filters (criteria reference valid skills/location and alert preferences)
- FR-0141: Notification delivery idempotency (duplicate provider callback yields one logical delivery state)
- FR-0142: Message retention (expired body purged/redacted while metadata remains)
- FR-0143: Language preference fallback (unsupported preference resolves to configured fallback)
- FR-0144: Community post length (within-limit free text saves; oversized rejected, UTF-8 supported)
- FR-0145: Reaction uniqueness (one reaction per user/post/type toggled idempotently)
- FR-0146: Support ticket ownership (ticket access limited to requester and authorized support staff)
- FR-0147: FAQ publication state (only active/published FAQ entries appear in public queries)
- FR-0148: Referral event attribution (valid referral recorded once without duplicate credit)
- FR-0149: Notification provider outage (failure recorded, retry strategy does not lose or duplicate deliveries)
- FR-0150: Preference change audit (auditable history recording actor, timestamp, before/after values)
- FR-0207: Notification body retention expiry (expired message bodies purged/redacted)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. Notification & Channel Preferences
# ==========================================

class NotificationPreferenceCreate(BaseModel):
    notification_type_code_id: int = Field(..., description="1=JOB_ALERT, 2=APPLICATION_UPDATE, 3=SECURITY, 4=MARKETING, 5=SYSTEM")
    channel_code_id: int = Field(..., description="1=IN_APP, 2=EMAIL, 3=SMS, 4=PUSH")
    enabled: bool = Field(default=True)


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    notification_type_code_id: int
    channel_code_id: int
    enabled: bool
    created_at: datetime
    updated_at: datetime


class JobAlertPreferenceCreate(BaseModel):
    setting_code_id: int = Field(default=1)
    setting_value: Dict[str, Any] = Field(..., description="Job alert criteria: keywords, skills, locations, salary_min, etc.")
    enabled: bool = Field(default=True)


class JobAlertPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    setting_code_id: int
    setting_value: Optional[Dict[str, Any]] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime


class PrivacyPreferenceCreate(BaseModel):
    setting_code_id: int = Field(default=1)
    setting_value: Dict[str, Any] = Field(..., description="Privacy settings: profile_public, show_activity, etc.")
    enabled: bool = Field(default=True)


class PrivacyPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    setting_code_id: int
    setting_value: Optional[Dict[str, Any]] = None
    enabled: bool
    created_at: datetime
    updated_at: datetime


# ==========================================
# 2. Notifications & Delivery
# ==========================================

class NotificationCreate(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=5000)
    category_id: int = Field(default=1, description="1=JOB_ALERT, 2=APPLICATION_UPDATE, 3=SECURITY, 4=MARKETING, 5=SYSTEM")
    channel_id: int = Field(default=1, description="1=IN_APP, 2=EMAIL, 3=SMS, 4=PUSH")
    priority: str = Field(default="NORMAL")
    link: Optional[str] = Field(None, max_length=500)
    retention_days: int = Field(default=90, ge=1, le=365)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    setting_code_id: int
    setting_value: Optional[Dict[str, Any]] = None
    enabled: bool
    is_read: bool = False
    title: Optional[str] = None
    body: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotificationBulkReadRequest(BaseModel):
    notification_ids: List[int] = Field(..., min_length=1)


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_id: int
    channel_code_id: int
    provider_code: str
    delivery_status_code_id: int
    attempt_count: int
    provider_message_reference: Optional[str] = None
    idempotency_key: str
    created_at: datetime


class NotificationDeliveryCallback(BaseModel):
    provider_code: str = Field(..., max_length=80)
    provider_message_reference: str = Field(..., max_length=255)
    delivery_status: str = Field(..., description="DELIVERED, FAILED, BOUNCED")
    idempotency_key: str = Field(..., min_length=8, max_length=255)
    error_message: Optional[str] = None


# ==========================================
# 3. Community Posts & Reactions
# ==========================================

class CommunityPostCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    body: str = Field(..., min_length=1, max_length=10000, description="Post content max 10000 chars UTF-8 (FR-0144)")
    language_code: Optional[str] = Field(default="en", max_length=10)


class CommunityPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_user_id: int
    title: str
    body: str
    language_id: Optional[int] = None
    moderation_status_code_id: int
    created_at: datetime
    updated_at: datetime


class CommunityReactionCreate(BaseModel):
    post_id: int
    reaction_type: str = Field(..., min_length=1, max_length=50, description="LIKE, HELPFUL, INSIGHTFUL")


class CommunityReactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    status_code_id: int
    created_at: datetime


class CommunityCommentCreate(BaseModel):
    post_id: int
    content: str = Field(..., min_length=1, max_length=2000)


class CommunityCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    status_code_id: int
    description: Optional[str] = None
    created_at: datetime


# ==========================================
# 4. Support Tickets & FAQ
# ==========================================

class SupportTicketCreate(BaseModel):
    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=8000)
    priority_code_id: int = Field(default=2, ge=1, le=4)


class SupportTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requester_user_id: int
    ticket_number: str
    subject: str
    description: str
    priority_code_id: int
    status_code_id: int
    assigned_to_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class SupportTicketStatusUpdate(BaseModel):
    status_code_id: int = Field(..., ge=1, le=4, description="1=OPEN, 2=IN_PROGRESS, 3=RESOLVED, 4=CLOSED")
    assigned_to_user_id: Optional[int] = None


class FaqCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=5, max_length=180, description="Question title")
    description: str = Field(..., min_length=10, max_length=2000, description="Answer content")
    status_code_id: int = Field(default=1, description="1=PUBLISHED, 2=DRAFT, 3=ARCHIVED (FR-0147)")


class FaqResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    status_code_id: int
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 5. Referrals
# ==========================================

class ReferralEventCreate(BaseModel):
    referrer_user_id: int
    referee_user_id: int
    referral_code: str = Field(..., min_length=4, max_length=80)
    event_type: str = Field(default="SIGNUP")


class ReferralEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_code_id: int
    actor_user_id: Optional[int] = None
    occurred_at: datetime
    metadata_redacted: Optional[Dict[str, Any]] = None
    created_at: datetime
