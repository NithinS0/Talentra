"""Automated Functional & Security Tests for Talentra Stage 9: Gig Marketplace.

Maps strictly to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Gig Marketplace):
- FR-0084: Gig worker profile separate from permanent candidates
- FR-0085: Gig request pricing decimal-safety and currency code
- FR-0086: Gig work date window (ends_at >= starts_at)
- FR-0087: Gig application direction (worker applies, requester decides)
- FR-0088: Gig application decision (only requester / authorized delegate)
- FR-0089: Overlapping worker assignments prevention
- FR-0090: Gig availability conflict detection
- FR-0091: Gig handoff external reference creation
- FR-0092: Gig earnings reconciliation and idempotent event handling
- FR-0093: Favourite and blacklist exclusivity
- FR-0094: Completed gig rating scale (1-5) and completion check
- FR-0095: Gig blacklist privacy protection
- FR-0096: External provider outage handling without false progression
- FR-0097: Gig cancellation lifecycle preservation
- FR-0203: Money amount uses companion ISO currency code
"""

import sys
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
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
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Organisation, OrganisationRecruiterMapping
from app.models.job import JobRole, EmploymentType, WorkType
from app.models.candidate import CandidateProfile
from app.models.admin import AuditEvent
from app.models.gig import (
    GigWorkerProfile,
    GigRequest,
    GigApplication,
    GigAssignment,
    GigHandoffReference,
    GigEarningsReconciliation,
    GigWorkerListEntry,
    GigRating,
    GigWorkerAvailability,
    GigRequestStatusHistory,
    GigApplicationStatusHistory,
    GigAssignmentStatusHistory,
    GigWorkerFavouriteHistory,
)


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with custom PostgreSQL function emulations."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    with engine.begin() as conn:
        Base.metadata.create_all(bind=conn)

    return engine


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Provide transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, expire_on_commit=False)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provide FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seed_roles(db_session):
    """Seed system roles."""
    roles_data = [
        ("SUPER_ADMIN", "Super Administrator", 1),
        ("ADMIN", "Platform Administrator", 2),
        ("ACCOUNT_ADMIN", "Account Administrator", 3),
        ("EMPLOYER", "Employer", 4),
        ("RECRUITER", "Recruiter", 5),
        ("CANDIDATE", "Candidate", 6),
        ("CONSULTANT", "External Consultant", 7),
        ("GIG_WORKER", "Gig Worker", 8),
    ]
    roles_dict = {}
    for code, name, rank in roles_data:
        r = db_session.query(Role).filter(Role.role_code == code).first()
        if not r:
            r = Role(role_code=code, display_name=name, description=name, is_system_role=True)
            db_session.add(r)
            db_session.flush()
        roles_dict[code] = r

    ind = db_session.query(Country).filter(Country.country_code == "IN").first()
    if not ind:
        ind = Country(country_code="IN", alpha3_code="IND", numeric_code="356", name="India", is_active=True)
        db_session.add(ind)
        db_session.flush()

    db_session.commit()
    return roles_dict


def _create_user(db_session, email_prefix, role_obj):
    now = datetime.now(timezone.utc)
    sub = str(uuid.uuid4())
    email = f"{email_prefix}_{sub[:6]}@talentra.io"
    user = User(
        provider_subject=sub,
        email_address=email,
        display_name=f"User {sub[:6]}",
        account_status_code_id=1,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role_obj.id,
        assigned_by_user_id=user.id,
        valid_from=now,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db_session.add(assignment)
    db_session.flush()
    db_session.commit()

    # Convenience attributes for tests
    user.supabase_uid = sub
    user.email = email
    return user


def _create_org(db_session, owner_user, name="Acme Gig Corp"):
    now = datetime.now(timezone.utc)
    org_name = f"{name}_{uuid.uuid4().hex[:4]}"
    org = Organisation(
        legal_name=org_name,
        display_name=org_name,
        status_code_id=1,
        created_by=owner_user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()
    db_session.commit()
    return org



# =========================================================================
# FR-0084: Gig Worker Profile
# =========================================================================

def test_fr0084_gig_worker_profile_separate_from_candidate(client, db_session, seed_roles):
    """FR-0084: Gig workers have a separate profile from permanent/temporary candidates."""
    worker_user = _create_user(db_session, "gig_worker", seed_roles["GIG_WORKER"])
    token = create_test_supabase_token(worker_user.supabase_uid, worker_user.email)

    payload = {
        "display_name": "Maya Lin - Lead Cloud Architect",
        "bio": "Specialist in AWS/GCP high-concurrency microservices and Terraform deployments.",
        "availability_status_code_id": 1,
    }
    resp = client.post(
        "/api/v1/gig/workers/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["display_name"] == "Maya Lin - Lead Cloud Architect"
    assert data["availability_status"] == "AVAILABLE"
    assert data["user_id"] == worker_user.id

    # Verify that no candidate profile was forced into candidate_profiles
    cand_profile = db_session.query(CandidateProfile).filter(CandidateProfile.user_id == worker_user.id).first()
    assert cand_profile is None  # Separate profile confirmed!

    # Verify lookup of gig profile
    get_resp = client.get(
        "/api/v1/gig/workers/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["id"] == data["id"]


# =========================================================================
# FR-0085: Gig Request Pricing
# =========================================================================

def test_fr0085_gig_request_pricing(client, db_session, seed_roles):
    """FR-0085: Price must be fixed or rate-based, use fixed precision and include currency."""
    employer_user = _create_user(db_session, "gig_employer", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer_user)
    token = create_test_supabase_token(employer_user.supabase_uid, employer_user.email)

    now = datetime.now(timezone.utc)
    valid_payload = {
        "requester_organisation_id": org.id,
        "title": "Migrate Redis Cluster to ElastiCache",
        "description": "Short-term gig to perform zero-downtime Redis migration.",
        "starts_at": (now + timedelta(days=2)).isoformat(),
        "ends_at": (now + timedelta(days=10)).isoformat(),
        "pricing_type_code_id": 1,  # FIXED
        "price_amount": 3500.50,
        "currency_code": "USD",
    }
    resp = client.post(
        "/api/v1/gig/requests",
        json=valid_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert Decimal(str(data["price_amount"])) == Decimal("3500.50")
    assert data["currency_code"] == "USD"
    assert data["pricing_type"] == "FIXED"

    # Non-positive amount rejected (FR-0085)
    invalid_price = dict(valid_payload, price_amount=0.00)
    resp_zero = client.post(
        "/api/v1/gig/requests",
        json=invalid_price,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_zero.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# =========================================================================
# FR-0203: Money Amount Uses Currency Code
# =========================================================================

def test_fr0203_money_amount_uses_currency_code(client, db_session, seed_roles):
    """FR-0203: Every money field has a companion currency code; no floating-point money."""
    employer_user = _create_user(db_session, "gig_currency_check", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer_user)
    token = create_test_supabase_token(employer_user.supabase_uid, employer_user.email)

    now = datetime.now(timezone.utc)
    base_payload = {
        "requester_organisation_id": org.id,
        "title": "Currency Code Integrity Test",
        "description": "Validates companion currency code requirement.",
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=5)).isoformat(),
        "pricing_type_code_id": 1,
        "price_amount": 1500.00,
    }

    # Missing currency code rejected
    resp_missing = client.post(
        "/api/v1/gig/requests",
        json=dict(base_payload, currency_code=""),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_missing.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # Non-3-letter currency code rejected
    resp_invalid_len = client.post(
        "/api/v1/gig/requests",
        json=dict(base_payload, currency_code="US"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_invalid_len.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # Valid 3-letter currency code accepted
    resp_valid = client.post(
        "/api/v1/gig/requests",
        json=dict(base_payload, currency_code="USD"),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_valid.status_code == status.HTTP_201_CREATED
    assert resp_valid.json()["currency_code"] == "USD"



# =========================================================================
# FR-0086: Gig Work Date Window
# =========================================================================

def test_fr0086_gig_work_date_window_validation(client, db_session, seed_roles):
    """FR-0086: Start/end window is valid and end cannot precede start."""
    employer_user = _create_user(db_session, "gig_employer_dates", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer_user)
    token = create_test_supabase_token(employer_user.supabase_uid, employer_user.email)

    now = datetime.now(timezone.utc)
    # End precedes start (Invalid)
    invalid_window = {
        "requester_organisation_id": org.id,
        "title": "Invalid Window Gig",
        "description": "This request has ends_at before starts_at.",
        "starts_at": (now + timedelta(days=10)).isoformat(),
        "ends_at": (now + timedelta(days=2)).isoformat(),  # Precedes start
        "pricing_type_code_id": 2,  # HOURLY
        "price_amount": 85.00,
        "currency_code": "INR",
    }
    resp = client.post(
        "/api/v1/gig/requests",
        json=invalid_window,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    assert "precede" in resp.text.lower() or "window" in resp.text.lower()


# =========================================================================
# FR-0087: Gig Application Direction
# =========================================================================

def test_fr0087_gig_application_direction_worker_to_request(client, db_session, seed_roles):
    """FR-0087: Gig workers apply to requests; bids do not flow in reverse direction."""
    employer_user = _create_user(db_session, "gig_emp_dir", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer_user)
    emp_token = create_test_supabase_token(employer_user.supabase_uid, employer_user.email)

    worker_user = _create_user(db_session, "gig_worker_dir", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker_user.supabase_uid, worker_user.email)

    # Worker creates profile
    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Dave", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    req_resp = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "Flutter Cross-Platform Build",
            "description": "Build mobile UI screens in Flutter.",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=5)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 1200.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    request_id = req_resp.json()["id"]

    # 1. Employer attempts to apply to their own gig (Prohibited reverse flow)
    emp_apply_resp = client.post(
        f"/api/v1/gig/requests/{request_id}/apply",
        json={"notes": "Employer applying"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert emp_apply_resp.status_code == status.HTTP_403_FORBIDDEN or "prohibited" in emp_apply_resp.text.lower()

    # 2. Worker applies to gig (Valid application direction)
    worker_apply_resp = client.post(
        f"/api/v1/gig/requests/{request_id}/apply",
        json={"notes": "Available immediately, 5 years Flutter experience."},
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert worker_apply_resp.status_code == status.HTTP_201_CREATED
    assert worker_apply_resp.json()["status"] == "APPLIED"


# =========================================================================
# FR-0088: Gig Application Decision
# =========================================================================

def test_fr0088_gig_application_decision_authorization(client, db_session, seed_roles):
    """FR-0088: Only requester or authorized delegate can accept/reject an application."""
    employer_user = _create_user(db_session, "gig_owner_dec", seed_roles["EMPLOYER"])
    unauthorized_user = _create_user(db_session, "unauth_user_dec", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer_user)

    emp_token = create_test_supabase_token(employer_user.supabase_uid, employer_user.email)
    unauth_token = create_test_supabase_token(unauthorized_user.supabase_uid, unauthorized_user.email)

    worker_user = _create_user(db_session, "gig_worker_dec", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker_user.supabase_uid, worker_user.email)

    # Worker profile
    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Sam", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    req_resp = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "Audit Smart Contracts",
            "description": "Perform security review on Solidity code.",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=7)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 4000.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    request_id = req_resp.json()["id"]

    # Worker applies
    apply_resp = client.post(
        f"/api/v1/gig/requests/{request_id}/apply",
        json={"notes": "Experienced Solidity auditor."},
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    application_id = apply_resp.json()["id"]

    # 1. Unauthorized actor attempts to decide application (Denied 403)
    unauth_resp = client.post(
        f"/api/v1/gig/applications/{application_id}/decision",
        json={"decision": "ACCEPTED", "reason": "Unauthorized acceptance"},
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert unauth_resp.status_code == status.HTTP_403_FORBIDDEN

    # 2. Authorized requester decides application (Success)
    auth_resp = client.post(
        f"/api/v1/gig/applications/{application_id}/decision",
        json={"decision": "ACCEPTED", "reason": "Portfolio approved"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert auth_resp.status_code == status.HTTP_200_OK
    assert auth_resp.json()["status"] == "ACCEPTED"
    assert auth_resp.json()["decided_by_user_id"] == employer_user.id


# =========================================================================
# FR-0089: Overlapping Worker Assignments
# =========================================================================

def test_fr0089_overlapping_worker_assignments_prevented(client, db_session, seed_roles):
    """FR-0089: Confirmed work windows must not overlap for the same gig worker."""
    employer_1 = _create_user(db_session, "emp_overlap_1", seed_roles["EMPLOYER"])
    org_1 = _create_org(db_session, employer_1, name="Org One")
    emp1_token = create_test_supabase_token(employer_1.supabase_uid, employer_1.email)

    employer_2 = _create_user(db_session, "emp_overlap_2", seed_roles["EMPLOYER"])
    org_2 = _create_org(db_session, employer_2, name="Org Two")
    emp2_token = create_test_supabase_token(employer_2.supabase_uid, employer_2.email)

    worker = _create_user(db_session, "worker_overlap", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Overlap Test", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    # Gig 1: Day 3 to Day 10
    gig1_resp = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org_1.id,
            "title": "Gig 1 - DevOps Sprint",
            "description": "DevOps infrastructure sprint.",
            "starts_at": (now + timedelta(days=3)).isoformat(),
            "ends_at": (now + timedelta(days=10)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 2000.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp1_token}"},
    )
    # Gig 2: Day 5 to Day 12 (Overlaps with Gig 1!)
    gig2_resp = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org_2.id,
            "title": "Gig 2 - Data Pipeline",
            "description": "ETL pipeline migration.",
            "starts_at": (now + timedelta(days=5)).isoformat(),
            "ends_at": (now + timedelta(days=12)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 2500.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp2_token}"},
    )

    gig1_id = gig1_resp.json()["id"]
    gig2_id = gig2_resp.json()["id"]

    # Worker applies to both
    app1 = client.post(f"/api/v1/gig/requests/{gig1_id}/apply", json={}, headers={"Authorization": f"Bearer {worker_token}"}).json()["id"]
    app2 = client.post(f"/api/v1/gig/requests/{gig2_id}/apply", json={}, headers={"Authorization": f"Bearer {worker_token}"}).json()["id"]

    # Employer 1 accepts Gig 1 -> Confirmed assignment created
    resp_accept_1 = client.post(
        f"/api/v1/gig/applications/{app1}/decision",
        json={"decision": "ACCEPTED"},
        headers={"Authorization": f"Bearer {emp1_token}"},
    )
    assert resp_accept_1.status_code == status.HTTP_200_OK

    # Employer 2 attempts to accept Gig 2 for the same worker -> Must be rejected due to overlap!
    resp_accept_2 = client.post(
        f"/api/v1/gig/applications/{app2}/decision",
        json={"decision": "ACCEPTED"},
        headers={"Authorization": f"Bearer {emp2_token}"},
    )
    assert resp_accept_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "overlapping" in resp_accept_2.text.lower() or "conflicting" in resp_accept_2.text.lower()


# =========================================================================
# FR-0090: Gig Availability Conflict
# =========================================================================

def test_fr0090_gig_availability_conflict_detection(client, db_session, seed_roles):
    """FR-0090: Availability records must have valid dates and detect assignment conflicts."""
    worker = _create_user(db_session, "worker_avail", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Avail", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    # 1. Invalid date range (ends_at < starts_at) rejected
    invalid_avail = {
        "starts_at": (now + timedelta(days=10)).isoformat(),
        "ends_at": (now + timedelta(days=2)).isoformat(),
        "status_code_id": 1,
    }
    resp_inv = client.post(
        "/api/v1/gig/workers/availability",
        json=invalid_avail,
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp_inv.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 2. Valid availability window saves
    valid_avail = {
        "starts_at": (now + timedelta(days=1)).isoformat(),
        "ends_at": (now + timedelta(days=5)).isoformat(),
        "status_code_id": 1,
        "currency_code": "USD",
        "amount": 75.00,
    }
    resp_val = client.post(
        "/api/v1/gig/workers/availability",
        json=valid_avail,
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp_val.status_code == status.HTTP_201_CREATED
    assert resp_val.json()["status"] == "AVAILABLE"


# =========================================================================
# FR-0091: Gig Handoff External Reference
# =========================================================================

def test_fr0091_gig_handoff_external_reference(client, db_session, seed_roles):
    """FR-0091: Accepted assignment creates external fulfilment handoff reference."""
    employer = _create_user(db_session, "emp_handoff", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    worker = _create_user(db_session, "worker_handoff", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Handoff", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    gig_resp = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "React UI Component Sprint",
            "description": "Component sprint.",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=3)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 1000.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    gig_id = gig_resp.json()["id"]

    app_id = client.post(f"/api/v1/gig/requests/{gig_id}/apply", json={}, headers={"Authorization": f"Bearer {worker_token}"}).json()["id"]

    # Accept assignment
    accept_resp = client.post(
        f"/api/v1/gig/applications/{app_id}/decision",
        json={"decision": "ACCEPTED"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert accept_resp.status_code == status.HTTP_200_OK

    asg = db_session.query(GigAssignment).filter(GigAssignment.gig_application_id == app_id).first()
    assert asg is not None
    handoff = db_session.query(GigHandoffReference).filter(GigHandoffReference.gig_assignment_id == asg.id).first()
    assert handoff is not None
    assert handoff.fulfilment_provider_code == "EXT_FULFILMENT_PARTNER_V1"
    assert "EXT-HANDOFF" in handoff.external_handoff_reference
    assert handoff.handoff_status_code_id == 1  # PENDING


# =========================================================================
# FR-0092: Gig Earnings Reconciliation
# =========================================================================

def test_fr0092_gig_earnings_reconciliation_idempotency(client, db_session, seed_roles):
    """FR-0092: Reconcile earnings originating from external boundary; repeated events are not double-counted."""
    worker = _create_user(db_session, "worker_reconcile", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    wp = client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Reconcile", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    ).json()

    event_payload = {
        "gig_worker_profile_id": wp["id"],
        "external_event_reference": "STRIPE-PAY-EVT-998877",
        "amount": 1500.00,
        "currency_code": "USD",
        "status_code_id": 2,  # RECONCILED
    }

    # First event ingestion
    resp1 = client.post(
        "/api/v1/gig/earnings/reconciliation",
        json=event_payload,
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp1.status_code == status.HTTP_200_OK
    assert Decimal(str(resp1.json()["amount"])) == Decimal("1500.00")
    assert resp1.json()["external_event_reference"] == "STRIPE-PAY-EVT-998877"

    # Second event ingestion with identical reference (Idempotent replay)
    resp2 = client.post(
        "/api/v1/gig/earnings/reconciliation",
        json=event_payload,
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.json()["id"] == resp1.json()["id"]

    # Verify exactly one record exists in database
    records = db_session.query(GigEarningsReconciliation).filter(
        GigEarningsReconciliation.external_event_reference == "STRIPE-PAY-EVT-998877"
    ).all()
    assert len(records) == 1  # No double counting!


# =========================================================================
# FR-0093: Favourite and Blacklist Exclusivity
# =========================================================================

def test_fr0093_favourite_and_blacklist_exclusivity(client, db_session, seed_roles):
    """FR-0093: Same requester-worker pair cannot have conflicting active list states."""
    employer = _create_user(db_session, "emp_lists", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    worker = _create_user(db_session, "worker_lists", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    wp = client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Lists", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    ).json()

    # 1. Add worker to Blacklist
    resp_bl = client.post(
        f"/api/v1/gig/organisations/{org.id}/worker-lists",
        json={"gig_worker_profile_id": wp["id"], "list_type": "BLACKLISTED"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_bl.status_code == status.HTTP_201_CREATED
    assert resp_bl.json()["list_type"] == "BLACKLISTED"

    # 2. Attempt to add the same worker to Favourite list -> Contradictory conflict rejected!
    resp_fav = client.post(
        f"/api/v1/gig/organisations/{org.id}/worker-lists",
        json={"gig_worker_profile_id": wp["id"], "list_type": "FAVOURITE"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_fav.status_code == status.HTTP_400_BAD_REQUEST
    assert "exclusivity" in resp_fav.text.lower() or "conflict" in resp_fav.text.lower()


# =========================================================================
# FR-0094: Completed Gig Rating
# =========================================================================

def test_fr0094_completed_gig_rating_validation(client, db_session, seed_roles):
    """FR-0094: Ratings are allowed only for completed gigs and within defined scale (1.00 - 5.00)."""
    employer = _create_user(db_session, "emp_rate", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    worker = _create_user(db_session, "worker_rate", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    wp = client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Rating Test", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    ).json()

    now = datetime.now(timezone.utc)
    gig = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "Security Penetration Test",
            "description": "Black-box pentest.",
            "starts_at": (now - timedelta(days=5)).isoformat(),
            "ends_at": (now - timedelta(days=1)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 3000.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    ).json()

    app_id = client.post(f"/api/v1/gig/requests/{gig['id']}/apply", json={}, headers={"Authorization": f"Bearer {worker_token}"}).json()["id"]

    client.post(f"/api/v1/gig/applications/{app_id}/decision", json={"decision": "ACCEPTED"}, headers={"Authorization": f"Bearer {emp_token}"})

    assignment = db_session.query(GigAssignment).filter(GigAssignment.gig_application_id == app_id).first()
    assert assignment is not None

    # 1. Attempt to rate while assignment is still CONFIRMED/INCOMPLETE (Rejected)
    resp_incomplete = client.post(
        "/api/v1/gig/ratings",
        json={"gig_assignment_id": assignment.id, "rating_score": 5.00},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_incomplete.status_code == status.HTTP_400_BAD_REQUEST
    assert "completed" in resp_incomplete.text.lower()

    # Mark assignment as COMPLETED
    assignment.status_code_id = 3  # COMPLETED
    db_session.commit()

    # 2. Out of scale rating (e.g. 6.00 or 0.50) rejected
    resp_out_of_scale = client.post(
        "/api/v1/gig/ratings",
        json={"gig_assignment_id": assignment.id, "rating_score": 6.00},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_out_of_scale.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 3. Valid rating (5.00) on completed gig succeeds
    resp_valid = client.post(
        "/api/v1/gig/ratings",
        json={"gig_assignment_id": assignment.id, "rating_score": 5.00, "feedback_notes": "Flawless security audit."},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_valid.status_code == status.HTTP_201_CREATED
    assert Decimal(str(resp_valid.json()["rating_score"])) == Decimal("5.00")


# =========================================================================
# FR-0095: Gig Blacklist Privacy
# =========================================================================

def test_fr0095_gig_blacklist_privacy(client, db_session, seed_roles):
    """FR-0095: Unauthorized gig workers cannot inspect requester private blacklist."""
    employer = _create_user(db_session, "emp_bl_priv", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    worker = _create_user(db_session, "worker_bl_priv", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    wp = client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Blacklist", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    ).json()

    # Employer blacklists worker
    client.post(
        f"/api/v1/gig/organisations/{org.id}/worker-lists",
        json={"gig_worker_profile_id": wp["id"], "list_type": "BLACKLISTED"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )

    # 1. Unauthorized worker attempts to view requester's blacklist (Denied 403)
    resp_worker = client.get(
        f"/api/v1/gig/organisations/{org.id}/blacklisted-workers",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert resp_worker.status_code == status.HTTP_403_FORBIDDEN

    # 2. Authorized employer views their blacklist (Allowed 200)
    resp_emp = client.get(
        f"/api/v1/gig/organisations/{org.id}/blacklisted-workers",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp_emp.status_code == status.HTTP_200_OK
    assert len(resp_emp.json()) == 1
    assert resp_emp.json()[0]["gig_worker_profile_id"] == wp["id"]


# =========================================================================
# FR-0096: Gig External Provider Outage Resilience
# =========================================================================

def test_fr0096_external_provider_outage_state_retention(client, db_session, seed_roles):
    """FR-0096: External outage must not falsely advance assignment state."""
    employer = _create_user(db_session, "emp_outage", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    worker = _create_user(db_session, "worker_outage", seed_roles["GIG_WORKER"])
    worker_token = create_test_supabase_token(worker.supabase_uid, worker.email)

    client.post(
        "/api/v1/gig/workers/profile",
        json={"display_name": "Worker Outage", "availability_status_code_id": 1},
        headers={"Authorization": f"Bearer {worker_token}"},
    )

    now = datetime.now(timezone.utc)
    gig = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "Backend Performance Tuning",
            "description": "SQL optimization.",
            "starts_at": (now + timedelta(days=2)).isoformat(),
            "ends_at": (now + timedelta(days=5)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 1800.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    ).json()

    app_id = client.post(f"/api/v1/gig/requests/{gig['id']}/apply", json={}, headers={"Authorization": f"Bearer {worker_token}"}).json()["id"]
    client.post(f"/api/v1/gig/applications/{app_id}/decision", json={"decision": "ACCEPTED"}, headers={"Authorization": f"Bearer {emp_token}"})

    assignment = db_session.query(GigAssignment).filter(GigAssignment.gig_application_id == app_id).first()
    assert assignment is not None
    assert assignment.status_code_id == 1  # CONFIRMED

    # Simulate external provider outage
    outage_resp = client.post(
        f"/api/v1/gig/assignments/{assignment.id}/outage-test?error_message=Third-party+fulfilment+service+unavailable",
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert outage_resp.status_code == status.HTTP_200_OK
    data = outage_resp.json()
    # Assignment state has NOT falsely advanced to COMPLETED or ACTIVE
    assert data["status"] == "CONFIRMED"
    assert data["handoff_status"] == "FAILED_RETRYABLE"

    # Audit history contains the recorded integration error
    audit = db_session.query(AuditEvent).filter(AuditEvent.action_code == "GIG_FULFILMENT_OUTAGE_LOGGED").first()
    assert audit is not None
    assert audit.metadata_redacted["retryable"] is True


# =========================================================================
# FR-0097: Gig Cancellation Lifecycle
# =========================================================================

def test_fr0097_gig_cancellation_lifecycle(client, db_session, seed_roles):
    """FR-0097: Cancellation is allowed only in permitted states and is recorded."""
    employer = _create_user(db_session, "emp_cancel", seed_roles["EMPLOYER"])
    org = _create_org(db_session, employer)
    emp_token = create_test_supabase_token(employer.supabase_uid, employer.email)

    now = datetime.now(timezone.utc)
    gig = client.post(
        "/api/v1/gig/requests",
        json={
            "requester_organisation_id": org.id,
            "title": "Cancelled Gig Request",
            "description": "To be cancelled before assignment.",
            "starts_at": (now + timedelta(days=2)).isoformat(),
            "ends_at": (now + timedelta(days=5)).isoformat(),
            "pricing_type_code_id": 1,
            "price_amount": 900.00,
            "currency_code": "USD",
        },
        headers={"Authorization": f"Bearer {emp_token}"},
    ).json()

    # 1. Cancel OPEN gig request (Valid)
    cancel_resp = client.post(
        f"/api/v1/gig/requests/{gig['id']}/cancel",
        json={"cancellation_reason": "Project budget reallocated."},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert cancel_resp.status_code == status.HTTP_200_OK
    assert cancel_resp.json()["status"] == "CANCELLED"

    # 2. Attempt to cancel already CANCELLED request (Illegal transition rejected)
    cancel_again = client.post(
        f"/api/v1/gig/requests/{gig['id']}/cancel",
        json={"cancellation_reason": "Trying to cancel again."},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert cancel_again.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Status history entry recorded
    history = db_session.query(GigRequestStatusHistory).filter(
        GigRequestStatusHistory.gig_request_id == gig["id"],
        GigRequestStatusHistory.event_code_id == 5,  # CANCELLED
    ).first()
    assert history is not None
    assert history.metadata_redacted["reason"] == "Project budget reallocated."
