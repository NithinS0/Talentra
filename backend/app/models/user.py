"""Identity, Account, and Role Assignment Models."""

from typing import Optional, List
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    """Canonical Talentra user account mapped to Supabase Auth identity."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    email_address: Mapped[Optional[str]] = mapped_column(String(254), nullable=True, index=True)
    phone_e164: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    identity_provider_code: Mapped[str] = mapped_column(String(60), default="SUPABASE", nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    role_assignments: Mapped[List["UserRoleAssignment"]] = relationship(
        "UserRoleAssignment", back_populates="user", cascade="all, delete-orphan"
    )
    actor_identities: Mapped[List["UserActorIdentity"]] = relationship(
        "UserActorIdentity", back_populates="user", cascade="all, delete-orphan"
    )
    candidate_profile: Mapped[Optional["CandidateProfile"]] = relationship(  # noqa: F821
        "CandidateProfile", back_populates="user", uselist=False
    )


class Role(Base):
    """Role definition table (Super Admin, Admin, Candidate, Employer, etc.)."""

    __tablename__ = "role"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class UserRoleAssignment(Base):
    """Assignment of roles to user accounts, supporting multiple roles per user."""

    __tablename__ = "user_role_assignment"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id"), nullable=False, index=True)
    organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(7), nullable=True, index=True)
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    revoked_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="role_assignments")
    role: Mapped["Role"] = relationship("Role")


class UserActorIdentity(Base):
    """Central mapping connecting user accounts to role-specific public actor IDs."""

    __tablename__ = "user_actor_identity"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role.id"), nullable=False)
    role_code: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_prefix: Mapped[str] = mapped_column(String(2), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(7), unique=True, nullable=False, index=True)
    organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="actor_identities")
    role: Mapped["Role"] = relationship("Role")
