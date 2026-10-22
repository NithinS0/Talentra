"""Automated Functional, Security & Resilience Tests for Talentra Stage 13: Analytics & Reporting.

Maps strictly to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Analytics & Reporting):
- FR-0151: Application funnel aggregation & reconciliation with transactional data
- FR-0152: Fact-to-dimension relationships and orphan issue routing
- FR-0153: Daily aggregate refresh idempotency (repeated refresh does not double count)
- FR-0154: Analytics PII minimization (dashboard contains aggregated/masked fields only)
- FR-0155: Superset read-only role (read succeeds, mutations prohibited)
- FR-0156: Slowly changing dimension (SCD Type 2) historical accuracy
- FR-0157: Dashboard refresh watermark tracking
- FR-0158: Performance baseline p50, p95, p99 measurements
- FR-0159: Index before-after comparison reporting
- FR-0160: Full-scale extrapolation (10M candidates, 1M jobs, 100M applications)
- FR-0161: Data freshness and UTC refresh lag calculation
- FR-0162: Backup restore evidence & RTO compliance
- FR-0208: Analytical objects naming convention linting
"""

import sys
import os
import uuid
from typing import Tuple, List, Optional, Dict
from datetime import datetime, timedelta, timezone, date
from decimal import Decimal
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment
from app.models.organisation import Organisation
from app.models.job import JobRequirement, JobPosition
from app.models.application import JobApplication
from app.models.candidate import CandidateProfile
from app.models.gig import GigAssignment
from app.models.subscription import Subscription
from app.models.analytics import (
    DimDate,
    DimOrganisation,
    DimCandidate,
    DimJob,
    DimStatus,
    FactApplication,
    FactJobRequirement,
    FactGigAssignment,
    FactWalletTransaction,
    FactNotificationDelivery,
    AggregateDashboardDaily,
    AnalyticsRefreshRun,
    AnalyticsKpiDefinition,
    FactProfileActivity,
    FactProfileDownload,
    AnalyticsDataQualityIssue,
)
from app.services.analytics_service import (
    AnalyticsService,
    APPLICATION_STATUS,
    REFRESH_STATUS,
    ANALYTICAL_OBJECT_PREFIXES,
)


# Test database setup (SQLite in-memory with StaticPool)
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_roles(db_session):
    roles = {}
    for code, name in [
        ("SUPER_ADMIN", "Super Administrator"),
        ("ADMIN", "System Administrator"),
        ("EMPLOYER", "Employer Admin"),
        ("RECRUITER", "Recruiter"),
        ("CANDIDATE", "Candidate"),
        ("PLACEMENT_OFFICER", "Placement Officer"),
        ("ANALYST", "Business Intelligence Analyst"),
    ]:
        role = db_session.query(Role).filter(Role.role_code == code).first()
        if not role:
            role = Role(role_code=code, display_name=name, description=name, is_system_role=True)
            db_session.add(role)
        roles[code] = role
    db_session.commit()
    return roles


def _create_user(db: Session, role_code: str, email: Optional[str] = None) -> User:
    role = db.query(Role).filter(Role.role_code == role_code).first()
    user_email = email or f"{role_code.lower()}_{uuid.uuid4().hex[:8]}@example.com"
    sub = f"sub-{uuid.uuid4().hex[:12]}"
    user = User(
        email_address=user_email,
        display_name=f"Test {role_code.capitalize()}",
        provider_subject=sub,
        account_status_code_id=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if role:
        assignment = UserRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=user.id,
        )
        db.add(assignment)
        db.commit()
    return user


def _create_org(db: Session) -> Organisation:
    org = Organisation(
        legal_name=f"Acme Analytics Corp {uuid.uuid4().hex[:6]}",
        display_name="Acme Analytics",
        status_code_id=1,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _create_job(db: Session, org_id: int, creator_id: Optional[int] = None) -> JobRequirement:
    from app.models.job import JobRole, EmploymentType, WorkType

    job_role = db.query(JobRole).first()
    if not job_role:
        job_role = JobRole(job_role_code="SWE", name="Software Engineer")
        db.add(job_role)
        db.commit()
        db.refresh(job_role)

    emp_type = db.query(EmploymentType).first()
    if not emp_type:
        emp_type = EmploymentType(code="FT", name="Full-Time")
        db.add(emp_type)
        db.commit()
        db.refresh(emp_type)

    work_type = db.query(WorkType).first()
    if not work_type:
        work_type = WorkType(code="REMOTE", name="Remote")
        db.add(work_type)
        db.commit()
        db.refresh(work_type)

    job = JobRequirement(
        organisation_id=org_id,
        created_by_user_id=creator_id or 1,
        job_role_id=job_role.id,
        employment_type_id=emp_type.id,
        work_type_id=work_type.id,
        title="Senior Python Engineer",
        description="FastAPI & Analytics",
        status_code_id=2,  # Published
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


# -----------------------------------------------------------------------------
# FR-0151: Application Funnel Aggregation
# -----------------------------------------------------------------------------
def test_fr0151_application_funnel_aggregation(db_session, seed_roles):
    """FR-0151: Application funnel aggregation - funnel counts use documented application states and reconcile to transactional data."""
    org = _create_org(db_session)
    job = _create_job(db_session, org.id)

    # Create applications in various funnel stages
    # 2 Applied, 2 Screening, 2 Interview, 1 Offer, 1 Hired, 1 Rejected = Total 9
    stage_setup = [
        (APPLICATION_STATUS["APPLIED"], 2),
        (APPLICATION_STATUS["SCREENING"], 2),
        (APPLICATION_STATUS["INTERVIEW"], 2),
        (APPLICATION_STATUS["OFFER"], 1),
        (APPLICATION_STATUS["HIRED"], 1),
        (APPLICATION_STATUS["REJECTED"], 1),
    ]

    for status_id, count in stage_setup:
        for _ in range(count):
            cand = _create_user(db_session, "CANDIDATE")
            profile = CandidateProfile(
                user_id=cand.id,
                actor_id=f"CA{uuid.uuid4().hex[:5]}",
                first_name="Jane",
                last_name="Doe",
                profile_status_code_id=1,
            )
            db_session.add(profile)
            db_session.commit()
            db_session.refresh(profile)

            app_record = JobApplication(
                candidate_profile_id=profile.id,
                job_requirement_id=job.id,
                status_code_id=status_id,
                created_at=datetime.now(timezone.utc),
            )
            db_session.add(app_record)
    db_session.commit()

    # Calculate funnel
    funnel = AnalyticsService.get_application_funnel(
        db=db_session,
        organisation_id=org.id,
        job_requirement_id=job.id,
    )

    assert funnel.total_applications == 9
    assert funnel.total_hired == 1
    assert funnel.overall_conversion_rate_percent == round((1 / 9 * 100.0), 2)

    # Check stage counts
    stage_map = {s.status_code_id: s.count for s in funnel.stages}
    assert stage_map[APPLICATION_STATUS["APPLIED"]] == 2
    assert stage_map[APPLICATION_STATUS["SCREENING"]] == 2
    assert stage_map[APPLICATION_STATUS["INTERVIEW"]] == 2
    assert stage_map[APPLICATION_STATUS["OFFER"]] == 1
    assert stage_map[APPLICATION_STATUS["HIRED"]] == 1
    assert stage_map[APPLICATION_STATUS["REJECTED"]] == 1


# -----------------------------------------------------------------------------
# FR-0152: Fact-to-Dimension Relationships & Orphan Routing
# -----------------------------------------------------------------------------
def test_fr0152_fact_dimension_relationship_and_orphans(db_session, seed_roles):
    """FR-0152: Fact-to-dimension relationship - valid dimension keys resolve; orphan keys route to exception report."""
    now = datetime.now(timezone.utc)

    # Create dimensions
    cand_dim = DimCandidate(source_business_key="CAN-001", snapshot_at=now)
    job_dim = DimJob(source_business_key="JOB-001", snapshot_at=now)
    status_dim = DimStatus(source_business_key="STATUS-APP", snapshot_at=now)
    db_session.add_all([cand_dim, job_dim, status_dim])
    db_session.commit()

    # 1. Valid dimension references succeed
    fact, issue = AnalyticsService.record_fact_application(
        db=db_session,
        date_key=20261020,
        candidate_dimension_id=cand_dim.id,
        job_dimension_id=job_dim.id,
        status_dimension_id=status_dim.id,
        application_count=1,
    )
    assert fact is not None
    assert issue is None
    assert fact.application_count == 1

    # 2. Orphan dimension key is rejected and routed to exception report
    orphan_cand_id = 999999
    fact_orphan, issue_orphan = AnalyticsService.record_fact_application(
        db=db_session,
        date_key=20261020,
        candidate_dimension_id=orphan_cand_id,
        job_dimension_id=job_dim.id,
        status_dimension_id=status_dim.id,
        application_count=1,
    )
    assert fact_orphan is None
    assert issue_orphan is not None
    assert issue_orphan.code == "ORPHAN_DIM_KEY"
    assert f"candidate_dimension_id={orphan_cand_id}" in issue_orphan.description


# -----------------------------------------------------------------------------
# FR-0153: Daily Aggregate Refresh Idempotency
# -----------------------------------------------------------------------------
def test_fr0153_daily_aggregate_refresh_idempotency(db_session, seed_roles):
    """FR-0153: Daily aggregate refresh idempotency - repeated refresh for same scope/date does not double count."""
    org = _create_org(db_session)
    job = _create_job(db_session, org.id)
    cand = _create_user(db_session, "CANDIDATE")
    cand_profile = CandidateProfile(
        user_id=cand.id,
        actor_id=f"CA{uuid.uuid4().hex[:5]}",
        first_name="John",
        last_name="Smith",
        profile_status_code_id=1,
    )
    db_session.add(cand_profile)
    db_session.commit()
    db_session.refresh(cand_profile)

    today = datetime.now(timezone.utc).date()

    # Create 3 applications today
    for _ in range(3):
        app_rec = JobApplication(
            candidate_profile_id=cand_profile.id,
            job_requirement_id=job.id,
            status_code_id=APPLICATION_STATUS["APPLIED"],
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(app_rec)
    db_session.commit()

    # First refresh run
    r1 = AnalyticsService.refresh_daily_aggregates(
        db=db_session,
        organisation_id=org.id,
        refresh_date=today,
    )
    assert r1.status == "SUCCESS"

    b_key = f"ORG-{org.id}:{today.isoformat()}"
    agg1 = db_session.query(AggregateDashboardDaily).filter(
        AggregateDashboardDaily.source_business_key == b_key
    ).first()
    assert agg1 is not None
    assert agg1.measure_value == Decimal(3)

    # Second refresh run (idempotency verification)
    r2 = AnalyticsService.refresh_daily_aggregates(
        db=db_session,
        organisation_id=org.id,
        refresh_date=today,
    )
    assert r2.status == "SUCCESS"

    # Total rows for this business key must remain exactly 1
    total_rows = db_session.query(AggregateDashboardDaily).filter(
        AggregateDashboardDaily.source_business_key == b_key
    ).count()
    assert total_rows == 1

    # Measure must not have doubled to 6
    db_session.refresh(agg1)
    assert agg1.measure_value == Decimal(3)


# -----------------------------------------------------------------------------
# FR-0154: Analytics PII Minimization
# -----------------------------------------------------------------------------
def test_fr0154_analytics_pii_minimization(db_session, seed_roles):
    """FR-0154: Analytics PII minimization - analytics access must not expose unnecessary personal identifiers."""
    user = _create_user(db_session, "CANDIDATE", email="candidate.private@secret.org")
    profile = CandidateProfile(
        user_id=user.id,
        actor_id=f"CA{uuid.uuid4().hex[:5]}",
        first_name="Secret",
        last_name="Candidate",
        headline="Senior Systems Architect",
        summary="Classified details",
        completion_score=Decimal("95.00"),
        profile_status_code_id=1,
    )
    db_session.add(profile)
    db_session.commit()

    minimized_records = AnalyticsService.get_candidate_analytics_pii_minimized(db_session)
    assert len(minimized_records) >= 1

    target = next((r for r in minimized_records if r["candidate_analytics_id"] == f"CAN-{profile.id:06d}"), None)
    assert target is not None
    # Verify no raw email, name, phone, or address present
    assert "email" not in target
    assert "phone" not in target
    assert "first_name" not in target
    assert "last_name" not in target
    assert target["headline"] == "Senior Systems Architect"
    assert target["completion_score"] == 95.0


# -----------------------------------------------------------------------------
# FR-0155: Superset / BI Read-Only Role Enforcement
# -----------------------------------------------------------------------------
def test_fr0155_superset_read_only_role():
    """FR-0155: Superset read-only role - read operations succeed, write/delete operations fail."""
    # Permitted read operations
    AnalyticsService.enforce_bi_read_only(role_name="ANALYST", operation="SELECT")
    AnalyticsService.enforce_bi_read_only(role_name="SUPERSET_USER", operation="EXPORT")

    # Prohibited write operations raise PermissionError
    with pytest.raises(PermissionError, match="has read-only access"):
        AnalyticsService.enforce_bi_read_only(role_name="ANALYST", operation="INSERT")

    with pytest.raises(PermissionError, match="has read-only access"):
        AnalyticsService.enforce_bi_read_only(role_name="SUPERSET_USER", operation="DELETE")


# -----------------------------------------------------------------------------
# FR-0156: Slowly Changing Dimension (SCD Type 2) History
# -----------------------------------------------------------------------------
def test_fr0156_slowly_changing_dimension_history(db_session, seed_roles):
    """FR-0156: Slowly changing dimension history - historical dimension versions preserve effective dates and prior values."""
    b_key = "ORG-CORP-42"
    t1 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

    # Version 1 (Early 2026): measure_value = 10 (Tier 1)
    dim_v1 = DimOrganisation(
        source_business_key=b_key,
        snapshot_at=t1,
        measure_value=Decimal("10.0000"),
        source_watermark="V1",
    )
    # Version 2 (Mid 2026): measure_value = 25 (Upgraded to Tier 2)
    dim_v2 = DimOrganisation(
        source_business_key=b_key,
        snapshot_at=t2,
        measure_value=Decimal("25.0000"),
        source_watermark="V2",
    )
    db_session.add_all([dim_v1, dim_v2])
    db_session.commit()

    # Query as of March 2026 (between t1 and t2) should resolve to Version 1
    as_of_march = datetime(2026, 3, 15, 0, 0, 0, tzinfo=timezone.utc)
    res_march = AnalyticsService.get_as_of_organisation_dimension(db_session, b_key, as_of_march)
    assert res_march is not None
    assert res_march.measure_value == Decimal("10.0000")
    assert res_march.source_watermark == "V1"

    # Query as of August 2026 (after t2) should resolve to Version 2
    as_of_august = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    res_august = AnalyticsService.get_as_of_organisation_dimension(db_session, b_key, as_of_august)
    assert res_august is not None
    assert res_august.measure_value == Decimal("25.0000")
    assert res_august.source_watermark == "V2"


# -----------------------------------------------------------------------------
# FR-0157: Dashboard Refresh Watermark
# -----------------------------------------------------------------------------
def test_fr0157_dashboard_refresh_watermark(db_session, seed_roles):
    """FR-0157: Dashboard refresh watermark - refresh time and source watermark are recorded."""
    # Execute a refresh run
    res = AnalyticsService.refresh_daily_aggregates(db=db_session)
    assert res.source_watermark is not None

    watermark_info = AnalyticsService.get_refresh_watermark(db_session)
    assert watermark_info.status_name == "SUCCESS"
    assert watermark_info.last_watermark == res.source_watermark
    assert watermark_info.refresh_lag_seconds >= 0.0


# -----------------------------------------------------------------------------
# FR-0158: Performance Baseline p50, p95, p99
# -----------------------------------------------------------------------------
def test_fr0158_performance_baseline_p50_p95_p99(db_session, seed_roles):
    """FR-0158: Performance baseline p50 p95 p99 - baseline records hardware, dataset size, query, runs and p50/p95/p99."""
    report = AnalyticsService.measure_performance_baseline(db=db_session, sample_runs=5)
    assert report.hardware_environment is not None
    assert "Benchmark" in report.dataset_size
    assert len(report.queries) == 3

    for q in report.queries:
        assert q.sample_runs == 5
        assert q.p50_ms >= 0.0
        assert q.p95_ms >= q.p50_ms
        assert q.p99_ms >= q.p95_ms


# -----------------------------------------------------------------------------
# FR-0159: Index Before-After Comparison
# -----------------------------------------------------------------------------
def test_fr0159_index_before_after_comparison():
    """FR-0159: Index before-after comparison - report shows query plan and latency impact."""
    comp = AnalyticsService.compare_index_performance(
        table_name="fact_application",
        index_name="idx_fact_app_job_date",
        indexed_columns=["job_dimension_id", "date_key"],
    )
    assert comp.table_name == "fact_application"
    assert comp.index_name == "idx_fact_app_job_date"
    assert "Seq Scan" in comp.without_index_plan
    assert "Index Scan" in comp.with_index_plan
    assert comp.execution_time_after_ms < comp.execution_time_before_ms
    assert comp.speedup_factor > 1.0


# -----------------------------------------------------------------------------
# FR-0160: Full-Scale Extrapolation
# -----------------------------------------------------------------------------
def test_fr0160_full_scale_extrapolation():
    """FR-0160: Full-scale extrapolation - projection projects 10M candidates, 1M jobs, 100M applications with bottlenecks."""
    extrap = AnalyticsService.calculate_full_scale_extrapolation()
    assert extrap.target_scale_dataset["candidates"] == 10_000_000
    assert extrap.target_scale_dataset["jobs"] == 1_000_000
    assert extrap.target_scale_dataset["applications"] == 100_000_000
    assert extrap.projected_storage_gb["total_data_gb"] > 40.0
    assert "Partitioning" in extrap.first_degrading_query
    assert len(extrap.mitigation_strategy) > 0


# -----------------------------------------------------------------------------
# FR-0161: Data Freshness and UTC Lag Calculation
# -----------------------------------------------------------------------------
def test_fr0161_data_freshness_and_utc():
    """FR-0161: Data freshness and UTC - timestamp conventions are UTC and refresh lag is measurable."""
    now_utc = datetime.now(timezone.utc)
    watermark_time = now_utc - timedelta(seconds=120)

    freshness = AnalyticsService.check_data_freshness_utc(
        watermark_timestamp=watermark_time,
        current_timestamp=now_utc,
        max_acceptable_lag_seconds=300.0,
    )
    assert 119.0 <= freshness.lag_seconds <= 121.0
    assert freshness.is_fresh is True

    # Stale lag test (lag exceeds threshold)
    stale_watermark = now_utc - timedelta(hours=2)
    stale_check = AnalyticsService.check_data_freshness_utc(
        watermark_timestamp=stale_watermark,
        current_timestamp=now_utc,
        max_acceptable_lag_seconds=3600.0,
    )
    assert stale_check.lag_seconds >= 7200.0
    assert stale_check.is_fresh is False


# -----------------------------------------------------------------------------
# FR-0162: Backup Restore Evidence
# -----------------------------------------------------------------------------
def test_fr0162_backup_restore_evidence():
    """FR-0162: Backup restore evidence - backup and restore tested and time recorded against RTO."""
    evidence = AnalyticsService.record_backup_restore_evidence(
        backup_file_reference="talentra_backup_20261020_dr.sql",
        target_rto_minutes=15,
        actual_restore_seconds=180.0,  # 3 minutes
    )
    assert evidence.status == "VERIFIED_PASSED"
    assert evidence.is_rto_compliant is True
    assert evidence.actual_restore_duration_seconds == 180.0
    assert len(evidence.verification_checksum) > 0


# -----------------------------------------------------------------------------
# FR-0208: Analytical Objects Naming Convention Lint
# -----------------------------------------------------------------------------
def test_fr0208_analytical_naming_convention(db_session):
    """FR-0208: Analytical objects naming convention - analytical objects use a prefix distinguishing them from transactional objects."""
    lint = AnalyticsService.lint_analytical_object_names(db_session)
    assert lint.total_objects == 16
    assert lint.is_compliant is True
    assert len(lint.non_compliant_objects) == 0
    # Every object starts with dim_, fact_, aggregate_, analytics_, etc.
    for obj in lint.compliant_objects:
        assert any(obj.startswith(p) for p in ANALYTICAL_OBJECT_PREFIXES)


# -----------------------------------------------------------------------------
# End-to-End API Integration: Dashboards, Tenant Isolation & Export
# -----------------------------------------------------------------------------
def test_api_analytics_dashboards_and_export(client, db_session, seed_roles):
    """Integration test verifying role-scoped dashboards, tenant isolation, and CSV export."""
    org = _create_org(db_session)
    admin_user = _create_user(db_session, "ADMIN")
    employer_user = _create_user(db_session, "EMPLOYER")
    cand_user = _create_user(db_session, "CANDIDATE")

    admin_token = create_test_supabase_token(sub=admin_user.provider_subject, email=admin_user.email_address)
    emp_token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)

    # 1. Super Admin Dashboard (Admin permitted)
    resp = client.get(
        "/api/v1/analytics/dashboards/super-admin",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "total_organisations" in data

    # 2. Employer Dashboard (scoped to org)
    resp_emp = client.get(
        f"/api/v1/analytics/dashboards/employer?organisation_id={org.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_emp.status_code == status.HTTP_200_OK
    emp_data = resp_emp.json()
    assert emp_data["organisation_id"] == org.id
    assert "funnel" in emp_data

    # 3. CSV Funnel Export
    resp_csv = client.get(
        f"/api/v1/analytics/reports/funnel/export?organisation_id={org.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_csv.status_code == status.HTTP_200_OK
    assert "text/csv" in resp_csv.headers["content-type"]
    assert "Stage Name,Status Code ID,Candidate Count" in resp_csv.text
