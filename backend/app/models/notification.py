"""Notifications, User Preferences, Community, Support & FAQ Models.

Implements M10 Notifications, Preferences & Community tables aligned to PostgreSQL migration 010 and blueprint:
- notification_preference
- job_alert_preference
- privacy_preference
- notification
- notification_delivery
- notification_template
- community_post
- community_reaction
- community_comment
- support_ticket
- support_ticket_message
- faq
- referral_event
- social_share_event
- notification_delivery_attempt
- notification_preference_history
- support_ticket_status_history
- community_moderation_event
- language (master reference)
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    CheckConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Language(Base):
    """Supported language reference adhering to ISO 639 codes (FR-0143)."""

    __tablename__ = "language"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    language_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base):
    """User delivery preferences by category and channel (FR-0139, FR-0150)."""

    __tablename__ = "notification_preference"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    notification_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=JOB_ALERT, 2=APPLICATION_UPDATE, 3=SECURITY, 4=MARKETING, 5=SYSTEM
    channel_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=IN_APP, 2=EMAIL, 3=SMS, 4=PUSH
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    history = relationship("NotificationPreferenceHistory", back_populates="preference", cascade="all, delete-orphan")


class JobAlertPreference(Base):
    """Candidate job search filter preferences and alerting criteria (FR-0140)."""

    __tablename__ = "job_alert_preference"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    setting_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=JOB_ALERT_FILTER
    setting_value: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")


class PrivacyPreference(Base):
    """User privacy and visibility settings (FR-0150)."""

    __tablename__ = "privacy_preference"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    setting_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PRIVACY_SETTING
    setting_value: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")


class Notification(Base):
    """In-app and channel notifications with read tracking and retention policy (FR-0141, FR-0142, FR-0207)."""

    __tablename__ = "notification"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    setting_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=UNREAD, 2=READ, 3=ARCHIVED
    setting_value: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    deliveries = relationship("NotificationDelivery", back_populates="notification", cascade="all, delete-orphan")


class NotificationDelivery(Base):
    """External delivery dispatch and retry records (FR-0141, FR-0149)."""

    __tablename__ = "notification_delivery"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    notification_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notification.id"), nullable=False, index=True)
    channel_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=IN_APP, 2=EMAIL, 3=SMS, 4=PUSH
    provider_code: Mapped[str] = mapped_column(String(80), nullable=False)
    delivery_status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PENDING, 2=DELIVERED, 3=FAILED
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_message_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("attempt_count >= 0", name="ck_notification_delivery_attempt_count_positive"),
    )

    # Relationships
    notification = relationship("Notification", back_populates="deliveries")
    attempts = relationship("NotificationDeliveryAttempt", back_populates="delivery", cascade="all, delete-orphan")


class NotificationTemplate(Base):
    """Catalog of notification message templates."""

    __tablename__ = "notification_template"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    setting_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    setting_value: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CommunityPost(Base):
    """Community discussion post with character boundary and UTF-8 support (FR-0144)."""

    __tablename__ = "community_post"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    author_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(String(10000), nullable=False)
    language_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("language.id"), nullable=True)
    moderation_status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PUBLISHED, 2=PENDING, 3=FLAGGED, 4=REMOVED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    author = relationship("User")
    language = relationship("Language")


class CommunityReaction(Base):
    """Unique user reactions to community posts (FR-0145)."""

    __tablename__ = "community_reaction"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)  # post_id:user_id:reaction_type
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)  # LIKE, HELPFUL, INSIGHTFUL
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=REMOVED
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # user metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CommunityComment(Base):
    """Comments on community posts."""

    __tablename__ = "community_comment"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)  # post_id reference
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)  # author identifier
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PUBLISHED, 2=PENDING, 3=REMOVED
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # comment body
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportTicket(Base):
    """Customer and candidate support tickets with strict ownership isolation (FR-0146)."""

    __tablename__ = "support_ticket"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    requester_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    ticket_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(8000), nullable=False)
    priority_code_id: Mapped[int] = mapped_column(BigInteger, default=2, nullable=False)  # 1=LOW, 2=MEDIUM, 3=HIGH, 4=URGENT
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=OPEN, 2=IN_PROGRESS, 3=RESOLVED, 4=CLOSED
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requester_user_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    status_history = relationship("SupportTicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketMessage(Base):
    """Messages and replies within a support ticket thread."""

    __tablename__ = "support_ticket_message"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)  # ticket_id reference
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)  # sender label
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Faq(Base):
    """Help center and public knowledge base articles (FR-0147)."""

    __tablename__ = "faq"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)  # category code
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)  # Question title
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PUBLISHED, 2=DRAFT, 3=ARCHIVED
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)  # Answer content
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ReferralEvent(Base):
    """User invitation and referral tracking events (FR-0148)."""

    __tablename__ = "referral_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=SIGNUP, 2=QUALIFIED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SocialShareEvent(Base):
    """Social share telemetry logs."""

    __tablename__ = "social_share_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationDeliveryAttempt(Base):
    """Individual external delivery attempt log with provider response and errors (FR-0149)."""

    __tablename__ = "notification_delivery_attempt"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    notification_delivery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notification_delivery.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=SUCCESS, 2=FAILED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    delivery = relationship("NotificationDelivery", back_populates="attempts")


class NotificationPreferenceHistory(Base):
    """Auditable log of preference adjustments (FR-0150)."""

    __tablename__ = "notification_preference_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    notification_preference_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notification_preference.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=UPDATED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    preference = relationship("NotificationPreference", back_populates="history")


class SupportTicketStatusHistory(Base):
    """Lifecycle audit trail for support ticket status transitions."""

    __tablename__ = "support_ticket_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    support_ticket_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("support_ticket.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=OPEN, 2=IN_PROGRESS, 3=RESOLVED, 4=CLOSED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    ticket = relationship("SupportTicket", back_populates="status_history")


class CommunityModerationEvent(Base):
    """Audit log of moderation actions on community posts or comments."""

    __tablename__ = "community_moderation_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=FLAGGED, 2=APPROVED, 3=REMOVED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
