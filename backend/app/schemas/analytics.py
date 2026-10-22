"""Pydantic schemas for Talentra Stage 13: Analytics Layer & Reporting Marts."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FunnelStageCount(BaseModel):
    """Funnel stage metrics."""
    stage_name: str
    status_code_id: int
    count: int
    conversion_rate_percent: float


class FunnelAggregationResponse(BaseModel):
    """Application funnel progression aggregation (FR-0151)."""
    organisation_id: Optional[int] = None
    job_requirement_id: Optional[int] = None
    as_of_date: str
    total_applications: int
    total_hired: int
    overall_conversion_rate_percent: float
    stages: List[FunnelStageCount]


class DailyAggregateResponse(BaseModel):
    """Pre-aggregated daily metric entry (FR-0153)."""
    id: int
    source_business_key: str
    snapshot_at: datetime
    measure_value: Optional[Decimal] = None
    source_watermark: Optional[str] = None

    model_config = {"from_attributes": True}


class DailyRefreshRequest(BaseModel):
    """Request to refresh daily aggregates."""
    organisation_id: Optional[int] = None
    refresh_date: Optional[date] = None


class DailyRefreshResponse(BaseModel):
    """Result of daily aggregate refresh (FR-0153, FR-0157)."""
    status: str
    refresh_date: str
    records_processed: int
    source_watermark: str
    run_id: int


class WatermarkResponse(BaseModel):
    """Dashboard refresh watermark status (FR-0157)."""
    last_watermark: Optional[str] = None
    last_successful_run_at: Optional[datetime] = None
    status_code_id: int
    status_name: str
    refresh_lag_seconds: float


class DataFreshnessResponse(BaseModel):
    """Data freshness and UTC lag calculation (FR-0161)."""
    watermark_timestamp_utc: Optional[str] = None
    current_timestamp_utc: str
    lag_seconds: float
    is_fresh: bool


class KpiDefinitionResponse(BaseModel):
    """Business KPI catalogue entry."""
    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    status_code_id: int
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class PerformanceBaselineItem(BaseModel):
    """Performance measurement for a single query (FR-0158)."""
    query_name: str
    sample_runs: int
    p50_ms: float
    p95_ms: float
    p99_ms: float


class PerformanceBaselineReport(BaseModel):
    """Performance baseline report with hardware and dataset size (FR-0158)."""
    hardware_environment: str
    dataset_size: str
    executed_at_utc: str
    queries: List[PerformanceBaselineItem]


class IndexComparisonReport(BaseModel):
    """Before/after index comparison report (FR-0159)."""
    table_name: str
    index_name: str
    indexed_columns: List[str]
    query_description: str
    without_index_plan: str
    with_index_plan: str
    execution_time_before_ms: float
    execution_time_after_ms: float
    speedup_factor: float


class ExtrapolationReport(BaseModel):
    """Full-scale extrapolation report projecting 10M candidate workload (FR-0160)."""
    laptop_scale_dataset: Dict[str, Any]
    target_scale_dataset: Dict[str, Any]
    projected_storage_gb: Dict[str, float]
    projected_index_growth_gb: Dict[str, float]
    first_degrading_query: str
    bottleneck_analysis: str
    mitigation_strategy: str


class BackupRestoreReport(BaseModel):
    """Backup restore verification report against RTO (FR-0162)."""
    backup_file_reference: str
    tested_at_utc: str
    target_rto_minutes: int
    actual_restore_duration_seconds: float
    is_rto_compliant: bool
    status: str
    verification_checksum: str


class NamingLintReport(BaseModel):
    """Analytical objects naming convention lint report (FR-0208)."""
    total_objects: int
    compliant_objects: List[str]
    non_compliant_objects: List[str]
    is_compliant: bool
    allowed_prefixes: List[str]


class DataQualityIssueResponse(BaseModel):
    """Data quality issue record (FR-0152)."""
    id: int
    code: Optional[str] = None
    name: Optional[str] = None
    status_code_id: int
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Role-Specific Dashboards
class SuperAdminDashboardResponse(BaseModel):
    """Platform-wide analytics for Super Admin / Admin."""
    total_organisations: int
    total_jobs: int
    total_applications: int
    total_gig_assignments: int
    active_subscriptions_count: int
    watermark: Optional[str] = None
    refresh_lag_seconds: float


class EmployerDashboardResponse(BaseModel):
    """Organisation-specific recruitment analytics for Employer / Account Admin."""
    organisation_id: int
    organisation_name: str
    open_jobs_count: int
    total_applications_received: int
    interviews_scheduled: int
    offers_extended: int
    hires_count: int
    funnel: FunnelAggregationResponse


class RecruiterDashboardResponse(BaseModel):
    """Recruiter dashboard scoped to recruiter's assignments."""
    recruiter_user_id: int
    organisation_id: int
    assigned_jobs_count: int
    total_candidates_in_pipeline: int
    interviews_conducted: int
    hires_this_month: int


class CandidateDashboardResponse(BaseModel):
    """Candidate personal application progress dashboard."""
    candidate_user_id: int
    applications_submitted: int
    under_review_count: int
    interviews_scheduled: int
    offers_received: int
    profile_views_count: int


class TpoDashboardResponse(BaseModel):
    """Placement Officer (TPO) dashboard."""
    registered_students_count: int
    total_applications_sent: int
    offers_received: int
    placement_rate_percent: float
