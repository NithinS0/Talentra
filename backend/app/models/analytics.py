"""SQLAlchemy models for Talentra Stage 13: Analytics Layer & Reporting Marts (Module M11: 16 Tables).

Matches Alembic Migration: 011_analytics_reporting_marts
Tables:
1. dim_date
2. dim_organisation
3. dim_candidate
4. dim_job
5. dim_status
6. fact_application
7. fact_job_requirement
8. fact_gig_assignment
9. fact_wallet_transaction
10. fact_notification_delivery
11. aggregate_dashboard_daily
12. analytics_refresh_run
13. analytics_kpi_definition
14. fact_profile_activity
15. fact_profile_download
16. analytics_data_quality_issue
"""

from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    SmallInteger,
    String,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class DimDate(Base):
    """Analytical date dimension table."""
    __tablename__ = "dim_date"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    date_key = Column(Integer, nullable=False, unique=True, index=True)  # YYYYMMDD
    calendar_date = Column(Date, nullable=False, unique=True, index=True)
    year_number = Column(SmallInteger, nullable=False)
    quarter_number = Column(SmallInteger, nullable=False)
    month_number = Column(SmallInteger, nullable=False)
    day_number = Column(SmallInteger, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class DimOrganisation(Base):
    """Organisation analytics dimension table (supports SCD Type 2)."""
    __tablename__ = "dim_organisation"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class DimCandidate(Base):
    """Restricted candidate analytics dimension (PII-minimized)."""
    __tablename__ = "dim_candidate"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class DimJob(Base):
    """Job requirement analytics dimension table."""
    __tablename__ = "dim_job"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class DimStatus(Base):
    """Application and workflow status analytics dimension."""
    __tablename__ = "dim_status"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactApplication(Base):
    """Fact table tracking job application progression and funnel events."""
    __tablename__ = "fact_application"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    date_key = Column(Integer, nullable=False, index=True)
    candidate_dimension_id = Column(BigInteger, nullable=False, index=True)
    job_dimension_id = Column(BigInteger, nullable=False, index=True)
    status_dimension_id = Column(BigInteger, nullable=False, index=True)
    application_count = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactJobRequirement(Base):
    """Fact table tracking job postings, requirement metrics and lifecycle."""
    __tablename__ = "fact_job_requirement"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactGigAssignment(Base):
    """Fact table tracking gig marketplace assignments and milestones."""
    __tablename__ = "fact_gig_assignment"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactWalletTransaction(Base):
    """Fact table tracking wallet financial transactions and credit deductions."""
    __tablename__ = "fact_wallet_transaction"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactNotificationDelivery(Base):
    """Fact table tracking multi-channel notification deliveries and outcomes."""
    __tablename__ = "fact_notification_delivery"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AggregateDashboardDaily(Base):
    """Pre-aggregated daily summary metrics per organisation/date."""
    __tablename__ = "aggregate_dashboard_daily"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)  # e.g., "ORG-12:2026-10-20"
    snapshot_at = Column(DateTime(timezone=True), nullable=False, index=True)
    measure_value = Column(Numeric(20, 4), nullable=True)  # Count or financial total
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AnalyticsRefreshRun(Base):
    """Audit log of analytics refresh/ETL jobs and watermark tracking."""
    __tablename__ = "analytics_refresh_run"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=True, index=True)  # e.g., "DAILY_REFRESH"
    name = Column(String(180), nullable=True)
    status_code_id = Column(BigInteger, nullable=False, default=1)  # 1=RUNNING, 2=SUCCESS, 3=FAILED
    description = Column(String(2000), nullable=True)  # JSON or text with watermark, row counts

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AnalyticsKpiDefinition(Base):
    """Central catalogue of approved business KPI formulas and definitions."""
    __tablename__ = "analytics_kpi_definition"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=True, unique=True, index=True)  # e.g., "FUNNEL_TIME_TO_HIRE"
    name = Column(String(180), nullable=True)
    status_code_id = Column(BigInteger, nullable=False, default=1)  # 1=ACTIVE, 2=DEPRECATED
    description = Column(String(2000), nullable=True)  # Formula definition, inclusion/exclusion rules

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactProfileActivity(Base):
    """Fact table tracking candidate profile views, updates, and interactions."""
    __tablename__ = "fact_profile_activity"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class FactProfileDownload(Base):
    """Fact table tracking recruiter profile downloads and credit charges."""
    __tablename__ = "fact_profile_download"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    source_business_key = Column(String(100), nullable=False, index=True)
    snapshot_at = Column(DateTime(timezone=True), nullable=False)
    measure_value = Column(Numeric(20, 4), nullable=True)
    source_watermark = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AnalyticsDataQualityIssue(Base):
    """Audit log of data quality anomalies, orphan keys, and reconciliation mismatches."""
    __tablename__ = "analytics_data_quality_issue"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=True, index=True)  # e.g., "ORPHAN_DIM_KEY"
    name = Column(String(180), nullable=True)
    status_code_id = Column(BigInteger, nullable=False, default=1)  # 1=OPEN, 2=RESOLVED
    description = Column(String(2000), nullable=True)  # Detailed anomaly payload

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    updated_by = Column(BigInteger, nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
