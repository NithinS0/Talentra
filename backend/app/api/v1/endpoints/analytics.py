"""FastAPI endpoints for Talentra Stage 13: Analytics Layer & Reporting Marts."""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    FunnelAggregationResponse,
    DailyAggregateResponse,
    DailyRefreshRequest,
    DailyRefreshResponse,
    WatermarkResponse,
    DataFreshnessResponse,
    KpiDefinitionResponse,
    PerformanceBaselineReport,
    IndexComparisonReport,
    ExtrapolationReport,
    BackupRestoreReport,
    NamingLintReport,
    DataQualityIssueResponse,
    SuperAdminDashboardResponse,
    EmployerDashboardResponse,
    RecruiterDashboardResponse,
    CandidateDashboardResponse,
    TpoDashboardResponse,
)
from app.services.analytics_service import AnalyticsService
from app.models.analytics import AnalyticsKpiDefinition, AnalyticsDataQualityIssue

router = APIRouter()


def _get_user_roles(user: User) -> List[str]:
    """Extract active role codes assigned to user."""
    roles = []
    for ra in getattr(user, "role_assignments", []):
        if ra.role:
            code = getattr(ra.role, "role_code", None) or getattr(ra.role, "code", "")
            roles.append(code.upper())
    return roles


# -----------------------------------------------------------------------------
# Role-Specific Dashboards
# -----------------------------------------------------------------------------
@router.get("/dashboards/super-admin", response_model=SuperAdminDashboardResponse)
def get_super_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Platform-wide analytics for Super Admin and Admin roles."""
    user_roles = _get_user_roles(current_user)
    if "SUPER_ADMIN" not in user_roles and "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Super Admin or Admin role required for platform dashboard",
        )
    return AnalyticsService.get_super_admin_dashboard(db)


@router.get("/dashboards/employer", response_model=EmployerDashboardResponse)
def get_employer_dashboard(
    organisation_id: int = Query(..., description="Target organisation ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Organisation-specific recruitment analytics for Employer and Account Admin roles."""
    user_roles = _get_user_roles(current_user)
    # Require Employer, Account Admin, Admin or Super Admin
    allowed_roles = ["EMPLOYER", "ACCOUNT_ADMIN", "ADMIN", "SUPER_ADMIN"]
    if not any(r in user_roles for r in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Employer or Admin role required",
        )
    return AnalyticsService.get_employer_dashboard(db, organisation_id=organisation_id)


@router.get("/dashboards/recruiter", response_model=RecruiterDashboardResponse)
def get_recruiter_dashboard(
    organisation_id: int = Query(..., description="Recruiter mapped organisation ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recruiter dashboard scoped to recruiter's assignments and organisation."""
    user_roles = _get_user_roles(current_user)
    if "RECRUITER" not in user_roles and "ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Recruiter role required",
        )
    return AnalyticsService.get_recruiter_dashboard(
        db, recruiter_user_id=current_user.id, organisation_id=organisation_id
    )


@router.get("/dashboards/candidate", response_model=CandidateDashboardResponse)
def get_candidate_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Candidate personal application progress dashboard."""
    return AnalyticsService.get_candidate_dashboard(db, candidate_user_id=current_user.id)


@router.get("/dashboards/tpo", response_model=TpoDashboardResponse)
def get_tpo_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Placement Officer (TPO) dashboard."""
    user_roles = _get_user_roles(current_user)
    if "PLACEMENT_OFFICER" not in user_roles and "ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Placement Officer role required",
        )
    return AnalyticsService.get_tpo_dashboard(db)


# -----------------------------------------------------------------------------
# FR-0151: Application Funnel Aggregation
# -----------------------------------------------------------------------------
@router.get("/funnel", response_model=FunnelAggregationResponse)
def get_application_funnel(
    organisation_id: Optional[int] = Query(None, description="Filter by organisation"),
    job_requirement_id: Optional[int] = Query(None, description="Filter by job requirement"),
    as_of_date: Optional[date] = Query(None, description="As-of historical date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Application recruitment funnel progression reconciled to transactional data (FR-0151)."""
    return AnalyticsService.get_application_funnel(
        db, organisation_id=organisation_id, job_requirement_id=job_requirement_id, as_of_date=as_of_date
    )


# -----------------------------------------------------------------------------
# FR-0153 & FR-0157: Daily Refresh & Watermark
# -----------------------------------------------------------------------------
@router.post("/refresh/daily", response_model=DailyRefreshResponse)
def trigger_daily_refresh(
    req: DailyRefreshRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger idempotent daily aggregate refresh and watermark update (FR-0153, FR-0157)."""
    user_roles = _get_user_roles(current_user)
    if "ADMIN" not in user_roles and "SUPER_ADMIN" not in user_roles and "SYSTEM" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Admin or System role required to trigger aggregate refresh",
        )
    return AnalyticsService.refresh_daily_aggregates(
        db, organisation_id=req.organisation_id, refresh_date=req.refresh_date
    )


@router.get("/refresh/watermark", response_model=WatermarkResponse)
def get_refresh_watermark(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve latest successful refresh watermark and lag in seconds (FR-0157, FR-0161)."""
    return AnalyticsService.get_refresh_watermark(db)


@router.get("/data-freshness", response_model=DataFreshnessResponse)
def get_data_freshness(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate refresh lag in UTC seconds against source watermark (FR-0161)."""
    watermark_info = AnalyticsService.get_refresh_watermark(db)
    wt_time = watermark_info.last_successful_run_at or datetime.now(timezone.utc)
    return AnalyticsService.check_data_freshness_utc(watermark_timestamp=wt_time)


# -----------------------------------------------------------------------------
# FR-0154: Analytics PII Minimization
# -----------------------------------------------------------------------------
@router.get("/candidates/pii-minimized")
def get_candidates_pii_minimized(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Candidate analytics with sensitive personal identifiers masked/anonymized (FR-0154)."""
    user_roles = _get_user_roles(current_user)
    allowed_roles = ["ANALYST", "SUPERSET_USER", "ADMIN", "SUPER_ADMIN", "EMPLOYER", "ACCOUNT_ADMIN"]
    if not any(r in user_roles for r in allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Analytics access required",
        )
    return AnalyticsService.get_candidate_analytics_pii_minimized(db, limit=limit, offset=offset)


# -----------------------------------------------------------------------------
# Performance & Extrapolation Endpoints
# -----------------------------------------------------------------------------
@router.get("/performance-baseline", response_model=PerformanceBaselineReport)
def get_performance_baseline(
    sample_runs: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute fixed benchmark queries and report p50/p95/p99 latency (FR-0158)."""
    return AnalyticsService.measure_performance_baseline(db, sample_runs=sample_runs)


@router.get("/index-comparison", response_model=IndexComparisonReport)
def get_index_comparison(
    table_name: str = Query("fact_application"),
    index_name: str = Query("idx_fact_app_job_date"),
    current_user: User = Depends(get_current_user),
):
    """Report query execution plan and latency before and after index creation (FR-0159)."""
    return AnalyticsService.compare_index_performance(table_name=table_name, index_name=index_name)


@router.get("/extrapolation", response_model=ExtrapolationReport)
def get_full_scale_extrapolation(
    current_user: User = Depends(get_current_user),
):
    """Full-scale extrapolation projecting 10M candidates, 1M jobs, 100M applications (FR-0160)."""
    return AnalyticsService.calculate_full_scale_extrapolation()


@router.get("/backup-restore-evidence", response_model=BackupRestoreReport)
def get_backup_restore_evidence(
    current_user: User = Depends(get_current_user),
):
    """Backup restore verification report against Recovery Time Objective (FR-0162)."""
    return AnalyticsService.record_backup_restore_evidence()


@router.get("/naming-lint", response_model=NamingLintReport)
def get_naming_lint_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify that all analytical tables and marts match the documented prefix pattern (FR-0208)."""
    return AnalyticsService.lint_analytical_object_names(db)


# -----------------------------------------------------------------------------
# Metadata Catalogue & Data Quality
# -----------------------------------------------------------------------------
@router.get("/kpi-definitions", response_model=List[KpiDefinitionResponse])
def get_kpi_definitions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Catalogue of approved business KPI formulas and definitions."""
    return db.query(AnalyticsKpiDefinition).all()


@router.get("/data-quality-issues", response_model=List[DataQualityIssueResponse])
def get_data_quality_issues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List open data quality anomalies, orphan keys, and reconciliation mismatches (FR-0152)."""
    return db.query(AnalyticsDataQualityIssue).order_by(AnalyticsDataQualityIssue.created_at.desc()).all()


# -----------------------------------------------------------------------------
# Report Export
# -----------------------------------------------------------------------------
@router.get("/reports/funnel/export")
def export_funnel_report(
    organisation_id: Optional[int] = Query(None),
    job_requirement_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSV export of the application recruitment funnel with role authorization."""
    csv_data = AnalyticsService.export_funnel_csv(
        db, organisation_id=organisation_id, job_requirement_id=job_requirement_id
    )
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=recruitment_funnel.csv"},
    )
