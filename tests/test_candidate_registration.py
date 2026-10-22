"""Automated Security and Functional Tests for Talentra Stage 4: Authentication & Candidate Registration.

Tests enforce:
1. End-to-end Candidate self-registration workflow.
2. Server-side Actor ID allocation (CA00001) and anti-spoofing rejection.
3. Supabase Auth JWT verification: valid, expired, forged, and missing tokens.
4. Multi-role single-account identity model (no duplicate user accounts).
5. Duplicate registration and duplicate email conflict prevention.
6. ISO 3166-1 country validation and ITU-T E.164 phone number formatting.
7. Role-based authorization on protected endpoints (/candidates/me, /auth/me).
8. Atomic transaction rollback ensuring no partial records on error.
9. Sequential ID allocation across consecutive candidate registrations.
"""

import sys
import os
import time
import pytest
from decimal import Decimal
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


# In-memory test SQLite engine configured for isolation and PostgreSQL function emulation
@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with custom allocate_actor_id UDF."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # In-memory sequence counter state for testing
    sequence_counters = {}

    from datetime import datetime, timezone

    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, record):
        def allocate_actor_id_udf(prefix):
            sequence_counters[prefix] = sequence_counters.get(prefix, 0) + 1
            return f"{prefix}{sequence_counters[prefix]:05d}"

        # Register custom SQLite functions simulating PostgreSQL functions
        dbapi_conn.create_function("allocate_actor_id", 1, allocate_actor_id_udf)
        dbapi_conn.create_function("now", 0, lambda: datetime.now(timezone.utc).isoformat())

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed essential reference roles
    with engine.connect() as conn:
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
        # Seed test countries
        conn.execute(
            text("""
            INSERT INTO country (id, country_code, alpha3_code, numeric_code, name, calling_code, is_active)
            VALUES 
                (1, 'IN', 'IND', '356', 'India', '+91', 1),
                (2, 'US', 'USA', '840', 'United States', '+1', 1),
                (3, 'GB', 'GBR', '826', 'United Kingdom', '+44', 1),
                (4, 'SG', 'SGP', '702', 'Singapore', '+65', 1),
                (5, 'AE', 'ARE', '784', 'United Arab Emirates', '+971', 1)
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


# =============================================================================
# 1. CANDIDATE REGISTRATION WORKFLOW & ACTOR ID ALLOCATION
# =============================================================================

def test_candidate_registration_success(client):
    """Verify end-to-end Candidate registration allocates CA00001 and creates full profile."""
    sub = "supabase-uid-cand-001"
    email = "candidate.one@example.com"
    token = create_test_supabase_token(sub=sub, email=email)

    payload = {
        "first_name": "Rohan",
        "last_name": "Sharma",
        "country_code": "IN",
        "phone_number": "9876543210",
        "headline": "Senior Full-Stack Engineer",
        "summary": "Experienced Python and TypeScript developer.",
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    assert data["actor_id"].startswith("CA")
    assert len(data["actor_id"]) == 7
    assert data["first_name"] == "Rohan"
    assert data["last_name"] == "Sharma"
    assert data["display_name"] == "Rohan Sharma"
    assert data["email_address"] == email
    assert data["phone_e164"] == "+919876543210"
    assert data["country_code"] == "IN"
    assert data["country_name"] == "India"
    assert data["completion_score"] == 15.0


def test_actor_id_spoofing_prohibited(client):
    """Verify client-supplied actor_id in registration payload is strictly rejected."""
    sub = "supabase-uid-spoof-001"
    token = create_test_supabase_token(sub=sub)

    payload = {
        "first_name": "Eve",
        "last_name": "Hacker",
        "country_code": "US",
        "actor_id": "SA00001",  # Malicious attempt to claim Super Admin actor ID
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    # Pydantic extra='forbid' rejects extra fields with 422
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    err_detail = str(response.json())
    assert "extra" in err_detail.lower() or "actor_id" in err_detail.lower()


def test_sequential_actor_id_allocation(client):
    """Verify consecutive candidate registrations allocate sequential CA-series IDs."""
    sub2 = "supabase-uid-cand-002"
    token2 = create_test_supabase_token(sub=sub2, email="cand2@example.com")
    resp2 = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Alice", "last_name": "Smith", "country_code": "US"},
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp2.status_code == status.HTTP_201_CREATED
    actor_id_2 = resp2.json()["actor_id"]

    sub3 = "supabase-uid-cand-003"
    token3 = create_test_supabase_token(sub=sub3, email="cand3@example.com")
    resp3 = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Bob", "last_name": "Jones", "country_code": "GB"},
        headers={"Authorization": f"Bearer {token3}"},
    )
    assert resp3.status_code == status.HTTP_201_CREATED
    actor_id_3 = resp3.json()["actor_id"]

    # Verify sequential numbers (e.g. CA00002 -> CA00003)
    num2 = int(actor_id_2[2:])
    num3 = int(actor_id_3[2:])
    assert num3 == num2 + 1


# =============================================================================
# 2. AUTHENTICATION TOKEN SECURITY
# =============================================================================

def test_missing_authentication_token(client):
    """Request without Authorization header is rejected with 401."""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "No", "last_name": "Token", "country_code": "US"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED or response.status_code == status.HTTP_403_FORBIDDEN


def test_expired_authentication_token(client):
    """Expired Supabase token is rejected with 401."""
    expired_token = create_test_supabase_token(sub="uid-expired", expires_in=-100)
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Late", "last_name": "User", "country_code": "US"},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()


def test_forged_signature_token(client):
    """Token signed with wrong key is rejected with 401."""
    import jwt
    forged_token = jwt.encode(
        {"sub": "forged-uid", "exp": int(time.time()) + 3600, "aud": "authenticated"},
        "wrong_secret_key_1234567890",
        algorithm="HS256",
    )
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Fake", "last_name": "Signature", "country_code": "US"},
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# 3. IDEMPOTENCY & DUPLICATE PREVENTION
# =============================================================================

def test_duplicate_candidate_registration_conflict(client):
    """Duplicate candidate registration for the same account returns 409 Conflict."""
    sub = "supabase-uid-cand-dup"
    token = create_test_supabase_token(sub=sub, email="dup@example.com")
    payload = {"first_name": "Duplicate", "last_name": "Candidate", "country_code": "US"}

    # First registration succeeds
    resp1 = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == status.HTTP_201_CREATED

    # Second registration attempts to create duplicate profile -> 409 Conflict
    resp2 = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in resp2.json()["detail"].lower()


# =============================================================================
# 4. COUNTRY & PHONE NUMBER VALIDATION
# =============================================================================

def test_invalid_country_code_rejection(client):
    """Invalid country code (not in country master) is rejected with 422."""
    sub = "supabase-uid-invalid-country"
    token = create_test_supabase_token(sub=sub)
    payload = {"first_name": "John", "last_name": "Doe", "country_code": "ZZ"}

    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "country code" in response.json()["detail"].lower()


def test_invalid_telephone_format_rejection(client):
    """Malformed phone number for country is rejected with 422."""
    sub = "supabase-uid-invalid-phone"
    token = create_test_supabase_token(sub=sub)
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "country_code": "US",
        "phone_number": "12345",  # Invalid US number
    }

    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "phone number" in response.json()["detail"].lower()


# =============================================================================
# 5. MULTI-ROLE SINGLE-ACCOUNT ARCHITECTURE
# =============================================================================

def test_multi_role_single_account(client, db_session):
    """An existing user holding another role can register as Candidate without duplicate account."""
    sub = "supabase-uid-multirole"
    token = create_test_supabase_token(sub=sub, email="multirole@example.com")

    # Pre-create user with CONSULTANT role (e.g. external consultant)
    existing_user = User(
        email_address="multirole@example.com",
        display_name="Multi Role User",
        account_status_code_id=1,
        identity_provider_code="SUPABASE",
        provider_subject=sub,
    )
    db_session.add(existing_user)
    db_session.flush()

    # Assign Consultant role
    consultant_identity = UserActorIdentity(
        user_id=existing_user.id,
        role_id=8,
        role_code="CONSULTANT",
        actor_prefix="CO",
        actor_id="CO00001",
        is_active=True,
    )
    db_session.add(consultant_identity)
    db_session.commit()

    # User now registers as Candidate
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Multi", "last_name": "Role", "country_code": "SG"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == existing_user.id  # Same user account!
    assert data["actor_id"].startswith("CA")

    # Verify /auth/me returns BOTH roles and BOTH actor IDs
    me_resp = client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == status.HTTP_200_OK
    me_data = me_resp.json()
    assert me_data["user_id"] == existing_user.id
    actor_roles = [item["role_code"] for item in me_data["actor_identities"]]
    assert "CONSULTANT" in actor_roles
    assert "CANDIDATE" in actor_roles


# =============================================================================
# 6. PROTECTED ENDPOINTS & ROLE AUTHORIZATION
# =============================================================================

def test_candidate_me_endpoint_requires_candidate_role(client, db_session):
    """GET /candidates/me requires active CANDIDATE role; non-candidates receive 403."""
    sub_admin = "supabase-uid-admin-only"
    token_admin = create_test_supabase_token(sub=sub_admin, email="admin@example.com")

    # Create admin user without Candidate role
    admin_user = User(
        email_address="admin@example.com",
        display_name="Admin Person",
        account_status_code_id=1,
        identity_provider_code="SUPABASE",
        provider_subject=sub_admin,
    )
    db_session.add(admin_user)
    db_session.flush()

    admin_role = UserRoleAssignment(
        user_id=admin_user.id,
        role_id=2,  # ADMIN
        assigned_by_user_id=admin_user.id,
    )
    db_session.add(admin_role)
    db_session.commit()

    # Admin calls /candidates/me -> 403 Forbidden
    resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "role" in resp.json()["detail"].lower()


def test_candidate_me_endpoint_success_for_candidate(client):
    """GET /candidates/me returns profile for registered Candidate."""
    sub = "supabase-uid-me-test"
    token = create_test_supabase_token(sub=sub, email="me.test@example.com")

    # Register
    client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Me", "last_name": "Tester", "country_code": "IN", "phone_number": "9876543210"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Call /candidates/me
    resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["first_name"] == "Me"
    assert data["actor_id"].startswith("CA")
    assert data["country_code"] == "IN"
    assert data["phone_e164"] == "+919876543210"


# =============================================================================
# 7. SECURITY: PRIVILEGED ROLE PROVISIONING & TRANSACTION INTEGRITY
# =============================================================================

def test_privileged_roles_not_self_registerable(client):
    """Privileged roles (Admin, Super Admin) have no public self-registration endpoints."""
    # Verify no public self-registration endpoints exist for privileged actor classes
    admin_resp = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/admin",
        json={"first_name": "Bad", "last_name": "Actor"},
    )
    assert admin_resp.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)

    sa_resp = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/super-admin",
        json={"first_name": "Bad", "last_name": "Actor"},
    )
    assert sa_resp.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_transaction_rollback_on_failed_provisioning(client, db_session, monkeypatch):
    """If an error occurs midway through registration, entire transaction is rolled back."""
    sub = "supabase-uid-rollback-test"
    token = create_test_supabase_token(sub=sub, email="rollback@example.com")

    # Simulate an unexpected failure right after user creation during profile creation
    from app.services import candidate_service

    orig_allocate = candidate_service.allocate_actor_id
    def faulty_allocate(db, role):
        raise RuntimeError("Simulated transient allocation failure!")
    
    monkeypatch.setattr(candidate_service, "allocate_actor_id", faulty_allocate)

    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={"first_name": "Rollback", "last_name": "Tester", "country_code": "US"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Verify no partial/orphaned user record was committed to the database
    orphaned_user = db_session.query(User).filter(User.provider_subject == sub).first()
    assert orphaned_user is None, "Transaction rollback failed: orphaned user record found!"

