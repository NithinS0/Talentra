"""Administration, RBAC Governance, Audit, and Security Models.

Implements M04 Administration & RBAC Identity tables aligned to PostgreSQL migrations and blueprint.
"""

from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Permission(Base):
    """Fine-grained permission definition."""

    __tablename__ = "permission"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    resource_code: Mapped[str] = mapped_column(String(80), nullable=False)
    action_code: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="permission")


class RolePermission(Base):
    """Mapping table connecting roles to permissions with effect (ALLOW/DENY)."""

    __tablename__ = "role_permission"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id"), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("permission.id"), nullable=False, index=True)
    effect_code: Mapped[str] = mapped_column(String(10), default="ALLOW", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    role: Mapped["Role"] = relationship("Role")  # noqa: F821
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")


class AuditEvent(Base):
    """Immutable, append-only security and administration audit log."""

    __tablename__ = "audit_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(Uuid(as_uuid=False).with_variant(String(36), "sqlite"), nullable=True)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class IdentitySession(Base):
    """Active identity sessions for session governance and revocation."""

    __tablename__ = "identity_session"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    provider_session_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # noqa: F821


class ConsentRecord(Base):
    """User privacy and terms consent records with withdrawal tracking."""

    __tablename__ = "consent_record"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    consent_type_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(80), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    captured_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    withdrawn_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # noqa: F821


class LoginAttempt(Base):
    """Audit of authentication attempts for brute-force detection and throttling."""

    __tablename__ = "login_attempt"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=SUCCESS, 2=FAILED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SecurityAlertEvent(Base):
    """Security events and unauthorized privilege escalation alerts."""

    __tablename__ = "security_alert_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class RoleAssignmentHistory(Base):
    """Append-only history of role grants and revocations."""

    __tablename__ = "role_assignment_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=GRANTED, 2=REVOKED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
