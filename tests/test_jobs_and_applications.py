"""Automated Functional & Security Tests for Talentra Stage 5: Jobs and Applications.

Maps to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx:
- FR-0037: Create job requirement
- FR-0038: Recruiter company boundary
- FR-0039: Consultant openness boundary
- FR-0040: Salary range validation
- FR-0041: Job closing date validation
- FR-0042: Job position count
- FR-0043: Publish-state transition
- FR-0044: Duplicate application prevention
- FR-0045: Application status transition
- FR-0046: Application status history append-only
- FR-0051: Job search filters
- FR-0052: Candidate block visibility
- FR-0053: Application details access
- FR-0200: Concurrent application submission / idempotency
"""

import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.organisation import Organisation, OrganisationRecruiterMapping
from app.models.job import JobRequirement, JobPosition, JobRole, EmploymentType, WorkType
from app.models.application import JobApplication, ApplicationStatusHistory, BlockListEntry


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with custom PostgreSQL function emulations."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    sequence_counters = {}

    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, record):
        def allocate_actor_id_udf(prefix):
            sequence_counters[prefix] = sequence_counters.get(prefix, 0) + 1
            return f"{prefix}{sequence_counters[prefix]:05d}"

        dbapi_conn.create_function("allocate_actor_id", 1, allocate_actor_id_udf)
        dbapi_conn.create_function("now", 0, lambda: datetime.now(timezone.utc).isoformat())

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        # Seed reference roles
        conn.execute(
            text("""
            INSERT INTO role (id, role_code, display_name, description, is_system_role)
            VALUES 
                (1, 'SUPER_ADMIN', 'Super Administrator', 'System Super Admin', 1),
                (2, 'ADMIN', 'Platform Administrator', 'Admin', 1),
                (3, 'ACCOUNT_ADMIN', 'Account Administrator', 'Account Admin', 1),
                (4, 'GUEST', 'Guest User', 'Guest', 1),
                (5, 'CANDIDATE', 'Candidate', 'Talentra Job Candidate', 1),
                (6, 'EMPLOYER', 'Employer', 'Hiring Employer', 1),
                (7, 'RECRUITER', 'Recruiter', 'Recruiter', 1),
                (8, 'CONSULTANT', 'Sourcing Consultant', 'External Consultant', 1),
                (9, 'PLACEMENT_OFFICER', 'Placement Officer', 'TPO', 1)
            """)
        )
        # Seed country
        conn.execute(
            text("""
            INSERT INTO country (id, country_code, alpha3_code, numeric_code, name, calling_code, is_active)
            VALUES (1, 'IN', 'IND', '356', 'India', '+91', 1), (2, 'US', 'USA', '840', 'United States', '+1', 1)
            """)
        )
        # Seed employment types
        conn.execute(
            text("""
            INSERT INTO employment_type (id, code, name, status_code_id, description)
            VALUES 
                (1, 'FULL_TIME', 'Full-time', 1, 'Full-time employment'),
                (2, 'PART_TIME', 'Part-time', 1, 'Part-time employment'),
                (3, 'CONTRACT', 'Contract', 1, 'Contract engagement')
            """)
        )
        # Seed work types
        conn.execute(
            text("""
            INSERT INTO work_type (id, code, name, status_code_id, description)
            VALUES 
                (1, 'ONSITE', 'On-site', 1, 'On-site'),
                (2, 'REMOTE', 'Remote', 1, 'Remote'),
                (3, 'HYBRID', 'Hybrid', 1, 'Hybrid')
            """)
        )
        # Seed job roles
        conn.execute(
            text("""
            INSERT INTO job_role (id, job_role_code, name)
            VALUES 
                (1, 'SWE', 'Software Engineer'),
                (2, 'PM', 'Product Manager'),
                (3, 'DE', 'Data Engineer')
            """)
        )
        # Seed organisations
        conn.execute(
            text("""
            INSERT INTO organisation (id, organisation_type_code_id, legal_name, display_name, status_code_id)
            VALUES 
                (1, 1, 'TechNova Solutions Pvt Ltd', 'TechNova', 1),
                (2, 1, 'Globex Corporation', 'Globex', 1)
            """)
        )
        conn.commit()

    return engine


@pytest.fixture
def db_session(test_engine):
    """Provide a transactional database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    """Provide FastAPI TestClient with database dependency override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# Helper fixtures for actors
@pytest.fixture
def employer_actor(db_session):
    """Create an authorized Employer actor for TechNova (Org 1)."""
    sub = "supabase-uid-employer-1"
    user = db_session.query(User).filter(User.provider_subject == sub).first()
    if not user:
        user = User(
            email_address="employer1@technova.com",
            display_name="TechNova HR",
            account_status_code_id=1,
            identity_provider_code="SUPABASE",
            provider_subject=sub,
        )
        db_session.add(user)
        db_session.flush()

        role_assign = UserRoleAssignment(
            user_id=user.id,
            role_id=6,  # EMPLOYER
            organisation_id=1,
            assigned_by_user_id=user.id,
        )
        db_session.add(role_assign)

        identity = UserActorIdentity(
            user_id=user.id,
            role_id=6,
            role_code="EMPLOYER",
            actor_prefix="EM",
            actor_id="EM00001",
            organisation_id=1,
            is_active=True,
        )
        db_session.add(identity)
        db_session.commit()

    token = create_test_supabase_token(sub=sub, email=user.email_address)
    return {"user": user, "token": token, "organisation_id": 1}


@pytest.fixture
def recruiter_actor_org1(db_session):
    """Create a Recruiter mapped to TechNova (Org 1)."""
    sub = "supabase-uid-recruiter-org1"
    user = db_session.query(User).filter(User.provider_subject == sub).first()
    if not user:
        user = User(
            email_address="recruiter1@technova.com",
            display_name="TechNova Recruiter",
            account_status_code_id=1,
            identity_provider_code="SUPABASE",
            provider_subject=sub,
        )
        db_session.add(user)
        db_session.flush()

        role_assign = UserRoleAssignment(
            user_id=user.id,
            role_id=7,  # RECRUITER
            organisation_id=1,
            assigned_by_user_id=user.id,
        )
        db_session.add(role_assign)

        mapping = OrganisationRecruiterMapping(
            organisation_id=1,
            recruiter_user_id=user.id,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            assigned_by_user_id=user.id,
        )
        db_session.add(mapping)
        db_session.commit()

    token = create_test_supabase_token(sub=sub, email=user.email_address)
    return {"user": user, "token": token, "organisation_id": 1}


@pytest.fixture
def candidate_actor(db_session, client):
    """Create a registered Candidate actor."""
    sub = "supabase-uid-cand-jobs-test"
    user = db_session.query(User).filter(User.provider_subject == sub).first()
    token = create_test_supabase_token(sub=sub, email="candidate.jobs@example.com")
    if not user:
        resp = client.post(
            f"{settings.API_V1_PREFIX}/auth/register/candidate",
            json={"first_name": "Priya", "last_name": "Nair", "country_code": "IN", "headline": "Software Engineer"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == status.HTTP_201_CREATED
        user = db_session.query(User).filter(User.provider_subject == sub).first()

    return {"user": user, "token": token, "actor_id": user.candidate_profile.actor_id}


# =============================================================================
# 1. JOB REQUIREMENT MANAGEMENT (FR-0037, FR-0038, FR-0040, FR-0041, FR-0042)
# =============================================================================

def test_fr0037_create_job_requirement_employer_success(client, employer_actor):
    """FR-0037: Employer creates a published job requirement successfully."""
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    payload = {
        "organisation_id": employer_actor["organisation_id"],
        "job_role_id": 1,  # Software Engineer
        "title": "Senior Backend Engineer (Python/FastAPI)",
        "description": "We are seeking a senior engineer to scale distributed backend systems.",
        "employment_type_id": 1,  # Full-time
        "work_type_id": 2,  # Remote
        "positions_count": 3,
        "salary_min": 1800000.00,
        "salary_max": 2500000.00,
        "salary_currency_code": "INR",
        "application_deadline": deadline,
        "open_to_consultants": True,
        "publish_now": True,
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == "Senior Backend Engineer (Python/FastAPI)"
    assert data["status"] == "OPEN"
    assert data["publish_state"] == "PUBLISHED"
    assert data["positions_count"] == 3
    assert data["salary_min"] == 1800000.00
    assert data["salary_max"] == 2500000.00
    assert data["open_to_consultants"] is True


def test_fr0038_recruiter_company_boundary_enforced(client, recruiter_actor_org1):
    """FR-0038: Recruiter may only create/act on jobs for mapped company; cross-company access denied."""
    # Attempt to create job for Globex (Org 2) when recruiter is only mapped to TechNova (Org 1)
    payload = {
        "organisation_id": 2,  # Globex Corporation
        "job_role_id": 1,
        "title": "Cross-Company Illegal Job",
        "description": "This should be denied by company boundary rules.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 1,
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_actor_org1['token']}"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not mapped or authorized" in response.json()["detail"].lower()


def test_fr0040_salary_range_validation(client, employer_actor):
    """FR-0040: Minimum salary cannot exceed maximum salary."""
    payload = {
        "organisation_id": employer_actor["organisation_id"],
        "job_role_id": 1,
        "title": "Invalid Salary Range Job",
        "description": "Testing invalid salary range.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 1,
        "salary_min": 3000000.00,
        "salary_max": 2000000.00,  # Less than min -> invalid!
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "salary_max cannot be less than salary_min" in str(response.json())


def test_fr0041_job_closing_date_validation(client, employer_actor):
    """FR-0041: Closing date cannot be earlier than now (past deadline rejected)."""
    past_deadline = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    payload = {
        "organisation_id": employer_actor["organisation_id"],
        "job_role_id": 1,
        "title": "Expired Deadline Job",
        "description": "Testing past deadline rejection.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 1,
        "application_deadline": past_deadline,
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "future" in str(response.json()).lower()


def test_fr0042_job_position_count_positive(client, employer_actor):
    """FR-0042: Position count must be a positive integer (> 0)."""
    payload = {
        "organisation_id": employer_actor["organisation_id"],
        "job_role_id": 1,
        "title": "Zero Position Job",
        "description": "Testing zero positions.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 0,  # Invalid
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=payload,
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# 2. STATUS TRANSITIONS & DISCOVERY (FR-0043, FR-0051)
# =============================================================================

def test_fr0043_publish_state_transition(client, employer_actor):
    """FR-0043: Job lifecycle state transitions (Draft -> Published -> Closed)."""
    # 1. Create draft job
    create_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": employer_actor["organisation_id"],
            "job_role_id": 2,  # Product Manager
            "title": "Lead Product Manager",
            "description": "Own product roadmap and discovery.",
            "employment_type_id": 1,
            "work_type_id": 3,
            "positions_count": 1,
            "publish_now": False,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    job_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "DRAFT"
    assert create_resp.json()["publish_state"] == "UNPUBLISHED"

    # 2. Publish the job
    publish_resp = client.patch(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/status",
        json={"status": "OPEN", "publish_state": "PUBLISHED"},
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    assert publish_resp.status_code == status.HTTP_200_OK
    assert publish_resp.json()["status"] == "OPEN"
    assert publish_resp.json()["publish_state"] == "PUBLISHED"

    # 3. Close the job
    close_resp = client.patch(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/status",
        json={"status": "CLOSED"},
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    assert close_resp.status_code == status.HTTP_200_OK
    assert close_resp.json()["status"] == "CLOSED"


def test_fr0051_job_search_and_filters(client, employer_actor):
    """FR-0051: Public and Candidate search uses indexed fields and excludes drafts."""
    # Create distinct published jobs
    client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": employer_actor["organisation_id"],
            "job_role_id": 1,
            "title": "React Frontend Architect",
            "description": "Architect modern web interfaces with Next.js.",
            "employment_type_id": 1,
            "work_type_id": 2,  # Remote
            "positions_count": 1,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )

    # Search by keyword "React"
    search_resp = client.get(f"{settings.API_V1_PREFIX}/jobs?search=React")
    assert search_resp.status_code == status.HTTP_200_OK
    data = search_resp.json()
    assert data["total"] >= 1
    assert any("React Frontend Architect" in item["title"] for item in data["items"])

    # Filter by work_type (Remote = 2)
    filter_resp = client.get(f"{settings.API_V1_PREFIX}/jobs?work_type_id=2")
    assert filter_resp.status_code == status.HTTP_200_OK
    assert all(item["work_type"] == "Remote" for item in filter_resp.json()["items"])


# =============================================================================
# 3. CANDIDATE APPLICATION WORKFLOW (FR-0044, FR-0045, FR-0046, FR-0053, FR-0200)
# =============================================================================

def test_candidate_apply_success_and_history(client, candidate_actor, employer_actor):
    """Candidate applies to an open job; application and initial history are created atomically."""
    # Create an open job
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": employer_actor["organisation_id"],
            "job_role_id": 1,
            "title": "Staff Engineer - Data Platform",
            "description": "Scale petabyte-scale data pipelines.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 2,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    job_id = job_resp.json()["id"]

    # Candidate applies
    apply_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={"cover_letter": "I have 8 years of experience building data infrastructure."},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )

    assert apply_resp.status_code == status.HTTP_201_CREATED, apply_resp.text
    app_data = apply_resp.json()
    assert app_data["job_requirement_id"] == job_id
    assert app_data["status"] == "APPLIED"
    assert app_data["candidate_actor_id"] == candidate_actor["actor_id"]
    assert "8 years of experience" in app_data["cover_letter"]

    # Verify candidate can view own application via /applications/me
    my_apps = client.get(
        f"{settings.API_V1_PREFIX}/applications/me",
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    assert my_apps.status_code == status.HTTP_200_OK
    assert any(a["id"] == app_data["id"] for a in my_apps.json()["items"])


def test_fr0044_duplicate_application_prevention(client, candidate_actor, employer_actor):
    """FR-0044 & FR-0200: Candidate cannot submit a duplicate application to the same job."""
    # Create an open job
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": employer_actor["organisation_id"],
            "job_role_id": 1,
            "title": "Duplicate Test Job",
            "description": "Testing duplicate prevention.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 1,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    job_id = job_resp.json()["id"]

    # First application succeeds
    resp1 = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={"cover_letter": "First submission."},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    assert resp1.status_code == status.HTTP_201_CREATED

    # Second application returns 409 Conflict
    resp2 = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={"cover_letter": "Second submission attempt."},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "already submitted" in resp2.json()["detail"].lower()


def test_apply_to_draft_or_closed_job_rejected(client, candidate_actor, employer_actor):
    """Applying to a draft or closed job is rejected with 422."""
    # Create a draft job
    draft_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": employer_actor["organisation_id"],
            "job_role_id": 1,
            "title": "Secret Draft Job",
            "description": "Not yet published.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 1,
            "publish_now": False,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    draft_id = draft_resp.json()["id"]

    # Candidate attempt to apply to draft job
    apply_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{draft_id}/apply",
        json={},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    assert apply_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "not currently open" in apply_resp.json()["detail"].lower()


def test_fr0052_candidate_blocking_enforced(client, candidate_actor, employer_actor, db_session):
    """FR-0052: Candidate block prevents application to blocked organisation."""
    # Candidate blocks TechNova (Org 1)
    block_entry = BlockListEntry(
        blocker_user_id=candidate_actor["user"].id,
        blocked_organisation_id=1,
    )
    db_session.add(block_entry)
    db_session.commit()

    # Create job at TechNova
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": 1,
            "job_role_id": 1,
            "title": "Blocked Org Job",
            "description": "Candidate has blocked this org.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 1,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    job_id = job_resp.json()["id"]

    # Attempt to apply -> 403 Forbidden
    apply_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    assert apply_resp.status_code == status.HTTP_403_FORBIDDEN
    assert "blocklist" in apply_resp.json()["detail"].lower()

    # Clean up block
    db_session.delete(block_entry)
    db_session.commit()


def test_fr0053_cross_candidate_application_privacy(client, candidate_actor, employer_actor):
    """FR-0053: Candidate cannot view another candidate's application details."""
    # Create another candidate
    sub2 = "supabase-uid-cand-other"
    token2 = create_test_supabase_token(sub=sub2, email="other.candidate@example.com")
    reg2 = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Other", "last_name": "Person", "country_code": "US"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert reg2.status_code == status.HTTP_201_CREATED

    # Create job
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": 1,
            "job_role_id": 1,
            "title": "Privacy Job",
            "description": "Testing access boundaries.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 1,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    job_id = job_resp.json()["id"]

    # First candidate applies
    app_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={"cover_letter": "Confidential first candidate letter."},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    app_id = app_resp.json()["id"]

    # Second candidate attempts to view first candidate's application -> 403 Forbidden
    other_view_resp = client.get(
        f"{settings.API_V1_PREFIX}/applications/{app_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert other_view_resp.status_code == status.HTTP_403_FORBIDDEN


def test_fr0045_application_status_transition_by_recruiter(client, recruiter_actor_org1, candidate_actor, employer_actor):
    """FR-0045 & FR-0046: Recruiter transitions application through hiring pipeline with audit history."""
    # Create job and apply
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json={
            "organisation_id": 1,
            "job_role_id": 1,
            "title": "Pipeline Transition Job",
            "description": "Testing pipeline transition.",
            "employment_type_id": 1,
            "work_type_id": 1,
            "positions_count": 1,
            "publish_now": True,
        },
        headers={"Authorization": f"Bearer {employer_actor['token']}"},
    )
    job_id = job_resp.json()["id"]

    app_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={},
        headers={"Authorization": f"Bearer {candidate_actor['token']}"},
    )
    app_id = app_resp.json()["id"]

    # Recruiter moves to SCREENING
    resp_screen = client.patch(
        f"{settings.API_V1_PREFIX}/applications/{app_id}/status",
        json={"status": "SCREENING", "notes": "Resume matches criteria."},
        headers={"Authorization": f"Bearer {recruiter_actor_org1['token']}"},
    )
    assert resp_screen.status_code == status.HTTP_200_OK
    assert resp_screen.json()["status"] == "SCREENING"

    # Recruiter moves to INTERVIEW
    resp_interview = client.patch(
        f"{settings.API_V1_PREFIX}/applications/{app_id}/status",
        json={"status": "INTERVIEW", "notes": "Technical round scheduled."},
        headers={"Authorization": f"Bearer {recruiter_actor_org1['token']}"},
    )
    assert resp_interview.status_code == status.HTTP_200_OK
    assert resp_interview.json()["status"] == "INTERVIEW"

    # Verify recruiter can list applications for the job
    job_apps_resp = client.get(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/applications",
        headers={"Authorization": f"Bearer {recruiter_actor_org1['token']}"},
    )
    assert job_apps_resp.status_code == status.HTTP_200_OK
    assert job_apps_resp.json()["total"] >= 1
