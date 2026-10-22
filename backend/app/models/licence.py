"""Licences, Seats, Devices, and Sessions Models.

Implements M07 Licences, Seats, Devices & Sessions tables aligned to PostgreSQL migration 007 and blueprint:
- licence
- licence_seat_allocation
- registered_device
- device_revocation_event
- session_revocation_event
- licence_usage_snapshot
- login_device_decision
- session_activity_event
- licence_entitlement
- licence_status_history
- device_login_counter
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    CheckConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Licence(Base):
    """Subscription licence defining user seat limits and device allowances per account."""

    __tablename__ = "licence"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    licence_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False)
    max_devices_per_user: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=SUSPENDED, 3=REVOKED, 4=EXPIRED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("max_users > 0", name="ck_licence_max_users_positive"),
        CheckConstraint("max_devices_per_user > 0", name="ck_licence_max_devices_per_user_positive"),
    )

    # Relationships
    account = relationship("Account", backref="licences")
    seat_allocations = relationship("LicenceSeatAllocation", back_populates="licence", cascade="all, delete-orphan")
    status_history = relationship("LicenceStatusHistory", back_populates="licence", cascade="all, delete-orphan")


class LicenceSeatAllocation(Base):
    """Allocation of a licence seat to an authorized user within the account scope."""

    __tablename__ = "licence_seat_allocation"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    licence_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=False, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=RELEASED, 3=EXPIRED
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    licence = relationship("Licence", back_populates="seat_allocations")


class RegisteredDevice(Base):
    """User device registered using cryptographic fingerprint hash (never raw invasive data)."""

    __tablename__ = "registered_device"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    device_fingerprint_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    device_label: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")


class DeviceRevocationEvent(Base):
    """Append-only audit event capturing device revocation with actor, target, timestamp, and reason."""

    __tablename__ = "device_revocation_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=REVOKED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SessionRevocationEvent(Base):
    """Append-only audit event capturing session revocation and token invalidation."""

    __tablename__ = "session_revocation_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=REVOKED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class LicenceUsageSnapshot(Base):
    """Historical snapshot of licence capacity utilisation and seat allocation metrics."""

    __tablename__ = "licence_usage_snapshot"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    licence_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    licence = relationship("Licence")


class LoginDeviceDecision(Base):
    """Auditable decision record when evaluating login capacity against device limit."""

    __tablename__ = "login_device_decision"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    licence_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=ALLOWED, 2=REJECTED
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    licence = relationship("Licence")


class SessionActivityEvent(Base):
    """Audit of session activity events (login, heartbeat, refresh, termination)."""

    __tablename__ = "session_activity_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class LicenceEntitlement(Base):
    """Specific feature/entitlement flags associated with a subscription licence."""

    __tablename__ = "licence_entitlement"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    licence_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    licence = relationship("Licence")


class LicenceStatusHistory(Base):
    """Append-only lifecycle state transitions for licences (ACTIVE, SUSPENDED, REVOKED, EXPIRED)."""

    __tablename__ = "licence_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    licence_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # New status_code_id
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    licence = relationship("Licence", back_populates="status_history")


class DeviceLoginCounter(Base):
    """Counter tracker for concurrency-safe login evaluation."""

    __tablename__ = "device_login_counter"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    licence_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    licence = relationship("Licence")
