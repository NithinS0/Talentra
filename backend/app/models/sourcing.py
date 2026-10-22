"""Sourcing, Consultant Requests, Outreach, and Shortlist Models.

Implements M08 Sourcing & External Consultants tables aligned to migration 008 and blueprint.
"""

from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SourcingRequest(Base):
    """Sourcing request linking a job requirement to external consultants or agency sourcers."""

    __tablename__ = "sourcing_request"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_requirement.id"), nullable=False, index=True)
    requester_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    consultant_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False, index=True)  # 1=REQUESTED/PENDING, 2=ACCEPTED, 3=DECLINED, 4=CANCELLED, 5=COMPLETED
    open_to_consultants_snapshot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requested_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    job_requirement: Mapped["JobRequirement"] = relationship("JobRequirement")  # noqa: F821
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_user_id])  # noqa: F821
    consultant: Mapped[Optional["User"]] = relationship("User", foreign_keys=[consultant_user_id])  # noqa: F821
    status_history: Mapped[List["SourcingRequestStatusHistory"]] = relationship("SourcingRequestStatusHistory", back_populates="sourcing_request", cascade="all, delete-orphan")


class SourcingRequestStatusHistory(Base):
    """Historical record of sourcing request state changes."""

    __tablename__ = "sourcing_request_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    sourcing_request_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sourcing_request.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=REQUESTED, 2=ACCEPTED, 3=DECLINED, 4=CANCELLED, 5=STATUS_CHANGE
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    sourcing_request: Mapped["SourcingRequest"] = relationship("SourcingRequest", back_populates="status_history")


class ConsultantRequestDecision(Base):
    """Reference taxonomy for consultant request decisions."""

    __tablename__ = "consultant_request_decision"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsultantRequestAssignmentHistory(Base):
    """Historical audit of consultant assignments and decisions."""

    __tablename__ = "consultant_request_assignment_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=ASSIGNED, 2=ACCEPTED, 3=DECLINED, 4=CANCELLED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CandidateSourcingShortlist(Base):
    """Shortlist of candidate profiles created by consultants or recruiters."""

    __tablename__ = "candidate_sourcing_shortlist"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=SHORTLISTED, 2=CONTACTED, 3=SCREENED, 4=REJECTED
    title: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile: Mapped[Optional["CandidateProfile"]] = relationship("CandidateProfile")  # noqa: F821
    user: Mapped[Optional["User"]] = relationship("User")  # noqa: F821


class OutreachBatch(Base):
    """Bulk candidate outreach campaign batch."""

    __tablename__ = "outreach_batch"
    __table_args__ = (
        CheckConstraint("recipient_count >= 0", name="ck_outreach_batch_recipient_count_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    job_requirement_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("job_requirement.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=DRAFT, 2=PROCESSING, 3=SENT, 4=CANCELLED
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation")  # noqa: F821
    creator: Mapped["User"] = relationship("User")  # noqa: F821
    job_requirement: Mapped[Optional["JobRequirement"]] = relationship("JobRequirement")  # noqa: F821
    recipients: Mapped[List["OutreachRecipient"]] = relationship("OutreachRecipient", back_populates="batch", cascade="all, delete-orphan")


class OutreachRecipient(Base):
    """Individual candidate recipient within a bulk outreach batch."""

    __tablename__ = "outreach_recipient"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    outreach_batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("outreach_batch.id"), nullable=False, index=True)
    candidate_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=False, index=True)
    delivery_status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PENDING, 2=DELIVERED, 3=FAILED, 4=SUPPRESSED
    provider_message_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    batch: Mapped["OutreachBatch"] = relationship("OutreachBatch", back_populates="recipients")
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")  # noqa: F821


class CandidateContactAttempt(Base):
    """Audit record of direct candidate contact attempts."""

    __tablename__ = "candidate_contact_attempt"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_contact_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("candidate_contact.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsultantProfile(Base):
    """Profile data for external sourcing consultants."""

    __tablename__ = "consultant_profile"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsultantSkill(Base):
    """Skills associated with sourcing consultants."""

    __tablename__ = "consultant_skill"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ConsultantRateCard(Base):
    """Consultant pricing and placement rate card taxonomy."""

    __tablename__ = "consultant_rate_card"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class OutreachConsentCheck(Base):
    """Verification rules and outcomes for candidate outreach consent."""

    __tablename__ = "outreach_consent_check"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
