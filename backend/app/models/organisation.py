"""Organisation, Account, Location, and Verification Models.

Implements M05 Organisation & Account tables aligned to PostgreSQL migrations and blueprint.
"""

from typing import Optional, List
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary,
    JSON,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Organisation(Base):
    """Employer legal entity and organisation account."""

    __tablename__ = "organisation"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_type_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    parent_organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=True)
    primary_country_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("country.id"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    parent: Mapped[Optional["Organisation"]] = relationship("Organisation", remote_side=[id], back_populates="children")
    children: Mapped[List["Organisation"]] = relationship("Organisation", back_populates="parent")
    primary_country: Mapped[Optional["Country"]] = relationship("Country")  # noqa: F821
    recruiter_mappings: Mapped[List["OrganisationRecruiterMapping"]] = relationship(
        "OrganisationRecruiterMapping", back_populates="organisation"
    )
    job_requirements: Mapped[List["JobRequirement"]] = relationship(  # noqa: F821
        "JobRequirement", back_populates="organisation"
    )
    identifiers: Mapped[List["OrganisationIdentifier"]] = relationship(
        "OrganisationIdentifier", back_populates="organisation"
    )
    locations: Mapped[List["OrganisationLocation"]] = relationship(
        "OrganisationLocation", back_populates="organisation"
    )
    verifications: Mapped[List["OrganisationVerification"]] = relationship(
        "OrganisationVerification", back_populates="organisation"
    )
    status_history: Mapped[List["OrganisationStatusHistory"]] = relationship(
        "OrganisationStatusHistory", back_populates="organisation"
    )


class OrganisationIdentifier(Base):
    """Company tax, registration, or regulatory identifier."""

    __tablename__ = "organisation_identifier"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    country_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("country.id"), nullable=False, index=True)
    identifier_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    identifier_ciphertext: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    identifier_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    masked_identifier: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="identifiers")
    country: Mapped["Country"] = relationship("Country")  # noqa: F821


class OrganisationRecruiterMapping(Base):
    """Recruiter to company mapping defining authorized access boundary."""

    __tablename__ = "organisation_recruiter_mapping"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    recruiter_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="recruiter_mappings")
    recruiter_user: Mapped["User"] = relationship("User")  # noqa: F821


class Account(Base):
    """Customer account wrapping an organisation or group of organisations."""

    __tablename__ = "account"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    root_organisation_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    billing_currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AccountOrganisation(Base):
    """Bridge table connecting accounts to organisations."""

    __tablename__ = "account_organisation"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), default="Primary", nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AccountAdminAssignment(Base):
    """Assignment connecting Account Admin actors to organisations and accounts."""

    __tablename__ = "account_admin_assignment"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), default="Account Admin", nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)


class OrganisationLocation(Base):
    """Physical office or operating location for an organisation."""

    __tablename__ = "organisation_location"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="locations")


class OrganisationVerification(Base):
    """Organisation identity and regulatory verification record."""

    __tablename__ = "organisation_verification"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), default="Business Verification", nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=UNVERIFIED, 2=PENDING, 3=VERIFIED, 4=REJECTED
    valid_from: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    valid_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="verifications")
    events: Mapped[List["OrganisationVerificationEvent"]] = relationship(
        "OrganisationVerificationEvent", back_populates="verification"
    )


class OrganisationVerificationEvent(Base):
    """Audit event for organisation verification status changes and provider responses."""

    __tablename__ = "organisation_verification_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_verification_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisation_verification.id"), nullable=False, index=True
    )
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    verification: Mapped["OrganisationVerification"] = relationship("OrganisationVerification", back_populates="events")


class OrganisationStatusHistory(Base):
    """Append-only audit trail for organisation lifecycle status transitions."""

    __tablename__ = "organisation_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organisation: Mapped["Organisation"] = relationship("Organisation", back_populates="status_history")
