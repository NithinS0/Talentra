"""Gig Marketplace SQLAlchemy Models (Module M06).

Audited against:
- Talentra Database Blueprint 150+ Tables (Sheet: Column Dictionary, Module: M06 Gig Marketplace)
- Alembic Migration: 006_gig_marketplace.py
- Talentra Final Test Cases: FR-0084 through FR-0097, FR-0203
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class GigWorkerProfile(Base):
    """Separate profile for gig workers, distinct from permanent/temporary candidates (FR-0084)."""

    __tablename__ = "gig_worker_profile"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(String(3000), nullable=True)
    availability_status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: AVAILABLE, 2: BUSY, 3: UNAVAILABLE

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    applications = relationship("GigApplication", back_populates="gig_worker_profile")
    assignments = relationship("GigAssignment", back_populates="gig_worker_profile")
    availabilities = relationship("GigWorkerAvailability", back_populates="gig_worker_profile")


class GigRequest(Base):
    """Gig requisition created by employer or authorized requester (FR-0085, FR-0086, FR-0097)."""

    __tablename__ = "gig_request"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    requester_organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisation.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    created_by_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pricing_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1: FIXED, 2: HOURLY / RATE_BASED
    price_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO-4217 companion currency
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=2)  # 1: DRAFT, 2: OPEN, 3: IN_PROGRESS, 4: COMPLETED, 5: CANCELLED

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation = relationship("Organisation", foreign_keys=[requester_organisation_id])
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    applications = relationship("GigApplication", back_populates="gig_request")
    status_history = relationship("GigRequestStatusHistory", back_populates="gig_request")


class GigApplication(Base):
    """Gig worker application/bid for a gig request (FR-0087, FR-0088)."""

    __tablename__ = "gig_application"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    gig_worker_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: APPLIED, 2: ACCEPTED, 3: REJECTED, 4: WITHDRAWN
    decided_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("user.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    gig_request = relationship("GigRequest", back_populates="applications")
    gig_worker_profile = relationship("GigWorkerProfile", back_populates="applications")
    decided_by_user = relationship("User", foreign_keys=[decided_by_user_id])
    assignment = relationship("GigAssignment", back_populates="gig_application", uselist=False)


class GigAssignment(Base):
    """Confirmed engagement between requester organisation and gig worker (FR-0089, FR-0091)."""

    __tablename__ = "gig_assignment"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_application.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, unique=True
    )
    requester_organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisation.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    gig_worker_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: CONFIRMED, 2: ACTIVE, 3: COMPLETED, 4: CANCELLED

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    gig_application = relationship("GigApplication", back_populates="assignment")
    organisation = relationship("Organisation", foreign_keys=[requester_organisation_id])
    gig_worker_profile = relationship("GigWorkerProfile", back_populates="assignments")
    handoff_reference = relationship("GigHandoffReference", back_populates="gig_assignment", uselist=False)


class GigHandoffReference(Base):
    """External fulfilment system handoff tracking (FR-0091, FR-0096)."""

    __tablename__ = "gig_handoff_reference"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_assignment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_assignment.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False, unique=True
    )
    fulfilment_provider_code: Mapped[str] = mapped_column(String(80), nullable=False)
    external_handoff_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    handoff_status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: PENDING, 2: SYNCHRONIZED, 3: FAILED_RETRYABLE
    last_reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    gig_assignment = relationship("GigAssignment", back_populates="handoff_reference")


class GigEarningsReconciliation(Base):
    """Reconciled earnings originating from external system boundary (FR-0092)."""

    __tablename__ = "gig_earnings_reconciliation"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: ESTIMATED, 2: RECONCILED, 3: PAID
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    external_event_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigWorkerListEntry(Base):
    """Favourite or blacklist list entry for a gig worker by a requester (FR-0093, FR-0095)."""

    __tablename__ = "gig_worker_list_entry"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    requester_organisation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("organisation.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1: FAVOURITE, 2: BLACKLISTED
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    gig_worker_profile = relationship("GigWorkerProfile", foreign_keys=[gig_worker_profile_id])


class GigRating(Base):
    """Ratings for completed gigs (FR-0094)."""

    __tablename__ = "gig_rating"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: SUBMITTED
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)  # rating score e.g. 5.00

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigWorkerAvailability(Base):
    """Gig worker availability window and conflict detection (FR-0090)."""

    __tablename__ = "gig_worker_availability"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)  # 1: AVAILABLE, 2: BOOKED, 3: BLOCKED
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    gig_worker_profile = relationship("GigWorkerProfile", back_populates="availabilities")


class GigRequestStatusHistory(Base):
    """Lifecycle audit history for gig requests (FR-0097)."""

    __tablename__ = "gig_request_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    gig_request = relationship("GigRequest", back_populates="status_history")


class GigApplicationStatusHistory(Base):
    """Lifecycle audit history for gig applications (FR-0088)."""

    __tablename__ = "gig_application_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_application_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_application.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigAssignmentStatusHistory(Base):
    """Lifecycle audit history for gig assignments (FR-0089)."""

    __tablename__ = "gig_assignment_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_assignment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gig_assignment.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=False
    )
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigWorkerFavouriteHistory(Base):
    """Audit history for favourite / blacklist list transitions (FR-0093)."""

    __tablename__ = "gig_worker_favourite_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigServiceOffering(Base):
    """Gig worker service offering catalog (M06)."""

    __tablename__ = "gig_service_offering"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class GigWorkerSkill(Base):
    """Gig worker skill mapping (M06)."""

    __tablename__ = "gig_worker_skill"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    gig_request_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_request.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    gig_worker_profile_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("gig_worker_profile.id", onupdate="RESTRICT", ondelete="RESTRICT"), nullable=True
    )
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
