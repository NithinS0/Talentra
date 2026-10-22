"""Government ID Verification & Optional Reference Extensions Models.

Implements M12 & M13 tables aligned to PostgreSQL migration 012_government_id_and_extensions.py.
Covers:
- Identity verification workflows (case, provider, reference, event, review, access log, consent purpose, retention job)
- Reference extensions (salary benchmark, trending job snapshot, feature flag, dashboard config, org rating aggregate)
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    JSON,
    LargeBinary,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class IdentityVerificationCase(Base):
    """Core identity verification case tracking."""

    __tablename__ = "identity_verification_case"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    document_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    provider_case_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=REQUESTED, 2=IN_REVIEW, 3=VERIFIED, 4=REJECTED, 5=EXPIRED, 6=RETRYABLE_TIMEOUT
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("consent_record.id"), nullable=False, index=True)
    provider_token_ciphertext: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # noqa: F821
    consent_record: Mapped["ConsentRecord"] = relationship("ConsentRecord")  # noqa: F821


class GovernmentDocumentReference(Base):
    """Masked document metadata and cryptographic token reference."""

    __tablename__ = "government_document_reference"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    verification_case_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    document_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    masked_identifier: Mapped[str] = mapped_column(String(80), nullable=False)
    identifier_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    encrypted_identifier_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    issuing_country_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")  # noqa: F821


class IdentityVerificationProvider(Base):
    """External verification provider registry."""

    __tablename__ = "identity_verification_provider"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    provider_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configuration_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class IdentityVerificationEvent(Base):
    """Audit log of verification events."""

    __tablename__ = "identity_verification_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class VerificationReview(Base):
    """Authorized reviewer decisions and override log."""

    __tablename__ = "verification_review"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    masked_identifier: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User")  # noqa: F821


class VerificationAccessLog(Base):
    """Access log recording reviewer queries and inspections of verification evidence."""

    __tablename__ = "verification_access_log"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    verification_case_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    action_code: Mapped[str] = mapped_column(String(100), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    outcome_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class VerificationConsentPurpose(Base):
    """Records permitted purpose and scope boundary for each verification."""

    __tablename__ = "verification_consent_purpose"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    masked_identifier: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User")  # noqa: F821


class VerificationProviderEvent(Base):
    """Inbound and outbound integration event trail with third-party providers."""

    __tablename__ = "verification_provider_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class VerificationRetentionJob(Base):
    """Tracks document retention schedule and automated purge execution."""

    __tablename__ = "verification_retention_job"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    provider_code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    masked_identifier: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User")  # noqa: F821


class SalaryBenchmark(Base):
    """Optional reference salary benchmark definitions."""

    __tablename__ = "salary_benchmark"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class TrendingJobSnapshot(Base):
    """Periodic snapshots of popular and trending job opportunities."""

    __tablename__ = "trending_job_snapshot"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    job_requirement_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("job_requirement.id"), nullable=True)
    job_application_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("job_application.id"), nullable=True)
    candidate_profile_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class FeatureFlag(Base):
    """Dynamic platform feature flag definitions and scope toggles."""

    __tablename__ = "feature_flag"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, unique=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class DashboardAggregateConfig(Base):
    """Dynamic configuration and snapshot for analytical dashboard tiles."""

    __tablename__ = "dashboard_aggregate_config"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    measure_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    source_watermark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class OrganisationRatingAggregate(Base):
    """Aggregated ratings and reviews summary per organisation."""

    __tablename__ = "organisation_rating_aggregate"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key: Mapped[str] = mapped_column(String(100), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    measure_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    source_watermark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
