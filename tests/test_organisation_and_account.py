"""Automated Functional & Security Tests for Talentra Stage 6: Organisation and Account Management.

Maps to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Organisation & Account):
- FR-0070: Organisation registration
- FR-0071: Company identifier uniqueness
- FR-0072: Identifier masking
- FR-0073: Organisation verification lifecycle
- FR-0074: Organisation hierarchy cycle
- FR-0075: Recruiter assignment effective dates
- FR-0076: Recruiter organisation scope
- FR-0077: Organisation location relationship
- FR-0078: Organisation deactivation
- FR-0079: Company verification provider outage
- FR-0080: Organisation audit fields
- FR-0081: Account administrator authorization
- FR-0082: Organisation identifier format
- FR-0083: Organisation duplicate detection
- FR-0202: Soft-deleted organisation excluded from default queries
"""

import sys
import os
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
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import (
    Organisation,
    OrganisationRecruiterMapping,
    OrganisationIdentifier,
    OrganisationLocation,
    OrganisationVerification,
    OrganisationVerificationEvent,
    OrganisationStatusHistory,
    Account,
    AccountOrganisation,
    AccountAdminAssignment,
)
from app.models.job import JobRequirement, JobPosition, JobRole, EmploymentType, WorkType


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
        conn.execute(
            text("""
            INSERT INTO country (id, country_code, alpha3_code, numeric_code, name, calling_code, is_active)
            VALUES 
                (1, 'IN', 'IND', '356', 'India', '+91', 1),
                (2, 'US', 'USA', '840', 'United States', '+1', 1),
                (3, 'GB', 'GBR', '826', 'United Kingdom', '+44', 1)
            """)
        )
        conn.execute(
            text("""
            INSERT INTO job_role (id, job_role_code, name)
            VALUES (1, 'SWE', 'Software Engineer')
            """)
        )
        conn.execute(
            text("""
            INSERT INTO employment_type (id, code, name, status_code_id, description)
            VALUES (1, 'FULL_TIME', 'Full-time', 1, 'Full-time employment')
            """)
        )
        conn.execute(
            text("""
            INSERT INTO work_type (id, code, name, status_code_id, description)
            VALUES (1, 'REMOTE', 'Remote', 1, 'Remote work')
            """)
        )
        conn.commit()

    return engine


@pytest.fixture
def db_session(test_engine):
    """Provide a transactional session for each test that rolls back cleanly."""
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionTest = sessionmaker(bind=connection, expire_on_commit=False)
    session = SessionTest()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Provide a FastAPI TestClient bound to the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# -------------------------------------------------------------------------
# Test Data Fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def employer_user(db_session):
    """Create an Employer user."""
    user = User(
        email_address="employer@acme.com",
        display_name="Acme Hiring Lead",
        account_status_code_id=1,
        provider_subject="auth0|employer-acme-sub",
    )
    db_session.add(user)
    db_session.flush()

    employer_role = db_session.query(Role).filter(Role.role_code == "EMPLOYER").first()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=employer_role.id,
        assigned_by_user_id=user.id,
        valid_from=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create a Platform Admin user."""
    user = User(
        email_address="admin@talentra.io",
        display_name="Global Administrator",
        account_status_code_id=1,
        provider_subject="auth0|admin-global-sub",
    )
    db_session.add(user)
    db_session.flush()

    admin_role = db_session.query(Role).filter(Role.role_code == "ADMIN").first()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=admin_role.id,
        assigned_by_user_id=user.id,
        valid_from=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.flush()
    return user


@pytest.fixture
def recruiter_user(db_session):
    """Create a Recruiter user."""
    user = User(
        email_address="recruiter@acme.com",
        display_name="Acme Primary Recruiter",
        account_status_code_id=1,
        provider_subject="auth0|recruiter-acme-sub",
    )
    db_session.add(user)
    db_session.flush()

    recruiter_role = db_session.query(Role).filter(Role.role_code == "RECRUITER").first()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=recruiter_role.id,
        assigned_by_user_id=user.id,
        valid_from=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.flush()
    return user


@pytest.fixture
def candidate_user(db_session):
    """Create a Candidate user."""
    user = User(
        email_address="applicant@example.com",
        display_name="Jane Jobseeker",
        account_status_code_id=1,
        provider_subject="auth0|candidate-applicant-sub",
    )
    db_session.add(user)
    db_session.flush()

    candidate_role = db_session.query(Role).filter(Role.role_code == "CANDIDATE").first()
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=candidate_role.id,
        assigned_by_user_id=user.id,
        valid_from=datetime.now(timezone.utc),
    )
    db_session.add(assignment)
    db_session.flush()
    return user


# -------------------------------------------------------------------------
# Test Cases Mapped to Talentra Test Workbook
# -------------------------------------------------------------------------

def test_fr0070_organisation_registration_success(client, employer_user, db_session):
    """FR-0070: Validate organisation registration generates ID, required legal fields, and Account Admin mapping."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "legal_name": "Apex Global Innovations Private Limited",
        "display_name": "Apex Innovations",
        "primary_country_id": 1,  # India
        "organisation_type_code_id": 1,
        "initial_identifier": "U72200KA2026PTC123456",
        "identifier_type_code_id": 2,  # Company Number (CIN)
    }

    response = client.post("/api/v1/organisations", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()

    assert data["id"] is not None
    assert data["legal_name"] == "Apex Global Innovations Private Limited"
    assert data["display_name"] == "Apex Innovations"
    assert data["status_code"] == "ACTIVE"
    assert data["primary_country_id"] == 1
    assert data["primary_country_name"] == "India"
    assert data["created_by"] == employer_user.id

    # Verify Account Admin role assignment and public actor ID (AA00001)
    assignment = (
        db_session.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == employer_user.id,
            UserRoleAssignment.organisation_id == data["id"],
        )
        .first()
    )
    assert assignment is not None
    assert assignment.role.role_code == "ACCOUNT_ADMIN"

    actor_ident = (
        db_session.query(UserActorIdentity)
        .filter(
            UserActorIdentity.user_id == employer_user.id,
            UserActorIdentity.organisation_id == data["id"],
        )
        .first()
    )
    assert actor_ident is not None
    assert actor_ident.actor_id.startswith("AA")


def test_fr0071_company_identifier_uniqueness(client, employer_user):
    """FR-0071: Validate composite uniqueness for company identifiers (country, type, fingerprint)."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    # Register first org with tax identifier
    payload1 = {
        "legal_name": "Zenith Financial Services Ltd",
        "display_name": "Zenith Financial",
        "primary_country_id": 2,  # US
        "initial_identifier": "12-3456789",  # US EIN
        "identifier_type_code_id": 4,
    }
    resp1 = client.post("/api/v1/organisations", json=payload1, headers=headers)
    assert resp1.status_code == status.HTTP_201_CREATED

    # Attempting to register another org with the exact same identifier in the same country must fail with 409
    payload2 = {
        "legal_name": "Zenith Holdings Inc",
        "display_name": "Zenith Holdings",
        "primary_country_id": 2,  # US
        "initial_identifier": "12-3456789",  # Duplicate EIN
        "identifier_type_code_id": 4,
    }
    resp2 = client.post("/api/v1/organisations", json=payload2, headers=headers)
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "already registered" in resp2.json()["detail"]


def test_fr0072_identifier_masking(client, employer_user):
    """FR-0072: Validate sensitive tax/registration identifiers are masked and never exposed in cleartext."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_resp = client.post(
        "/api/v1/organisations",
        json={
            "legal_name": "SecureCorp Cyber Systems Pvt Ltd",
            "display_name": "SecureCorp",
            "primary_country_id": 1,
        },
        headers=headers,
    )
    org_id = org_resp.json()["id"]

    # Add tax identifier
    ident_payload = {
        "country_id": 1,
        "identifier_type_code_id": 1,
        "identifier_value": "ABCDE1234F",  # Indian PAN
    }
    ident_resp = client.post(f"/api/v1/organisations/{org_id}/identifiers", json=ident_payload, headers=headers)
    assert ident_resp.status_code == status.HTTP_201_CREATED
    data = ident_resp.json()

    # Raw value must NOT appear; masked value must preserve only suffix
    assert data["masked_identifier"] == "******234F"
    assert "ABCDE1234F" not in str(data)

    # Listing identifiers also returns only masked identifiers
    list_resp = client.get(f"/api/v1/organisations/{org_id}/identifiers", headers=headers)
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()[0]["masked_identifier"] == "******234F"


def test_fr0073_organisation_verification_lifecycle(client, employer_user, db_session):
    """FR-0073: Validate organisation verification follows controlled status lifecycle with audit events."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_resp = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Verified Logistics International Ltd", "display_name": "Verified Logistics", "primary_country_id": 1},
        headers=headers,
    )
    org_id = org_resp.json()["id"]

    # Trigger verification
    verif_resp = client.post(
        f"/api/v1/organisations/{org_id}/verify",
        json={"name": "Ministry of Corporate Affairs Verification", "simulate_outage": False},
        headers=headers,
    )
    assert verif_resp.status_code == status.HTTP_200_OK
    verif_data = verif_resp.json()
    assert verif_data["status"] == "VERIFIED"
    assert verif_data["status_code_id"] == 3

    # Check verification event recorded in DB
    event_row = (
        db_session.query(OrganisationVerificationEvent)
        .filter(OrganisationVerificationEvent.organisation_verification_id == verif_data["id"])
        .first()
    )
    assert event_row is not None
    assert event_row.metadata_redacted.get("verified") is True


def test_fr0074_organisation_hierarchy_cycle_rejected(client, employer_user):
    """FR-0074: Validate that circular parent relationships (A->A, A->B->A, A->B->C->A) are rejected."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    # Org A
    org_a = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Parent Corp A", "display_name": "Corp A", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # Org B (Child of A)
    org_b = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Child Corp B", "display_name": "Corp B", "primary_country_id": 1, "parent_organisation_id": org_a},
        headers=headers,
    ).json()["id"]

    # Org C (Child of B)
    org_c = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Grandchild Corp C", "display_name": "Corp C", "primary_country_id": 1, "parent_organisation_id": org_b},
        headers=headers,
    ).json()["id"]

    # Attempt 1: A cannot be parent of A
    resp_self = client.put(f"/api/v1/organisations/{org_a}", json={"parent_organisation_id": org_a}, headers=headers)
    assert resp_self.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot be its own parent" in resp_self.json()["detail"]

    # Attempt 2: Setting A's parent to B (creates cycle A -> B -> A)
    resp_cycle_b = client.put(f"/api/v1/organisations/{org_a}", json={"parent_organisation_id": org_b}, headers=headers)
    assert resp_cycle_b.status_code == status.HTTP_400_BAD_REQUEST
    assert "circular ancestry loop" in resp_cycle_b.json()["detail"]

    # Attempt 3: Setting A's parent to C (creates cycle A -> B -> C -> A)
    resp_cycle_c = client.put(f"/api/v1/organisations/{org_a}", json={"parent_organisation_id": org_c}, headers=headers)
    assert resp_cycle_c.status_code == status.HTTP_400_BAD_REQUEST
    assert "circular ancestry loop" in resp_cycle_c.json()["detail"]


def test_fr0075_recruiter_assignment_effective_dates(client, employer_user, recruiter_user):
    """FR-0075: Validate recruiter mapping effective dates (valid_until >= valid_from) and expired access rejection."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "TalentBridge Staffing Services", "display_name": "TalentBridge", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    now = datetime.now(timezone.utc)

    # 1. Negative: End date before start date rejected with 422
    invalid_dates = {
        "recruiter_user_id": recruiter_user.id,
        "valid_from": (now + timedelta(days=10)).isoformat(),
        "valid_until": (now + timedelta(days=2)).isoformat(),
    }
    resp_invalid = client.post(f"/api/v1/organisations/{org_id}/recruiters", json=invalid_dates, headers=headers)
    assert resp_invalid.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Positive: Valid date range succeeds
    valid_dates = {
        "recruiter_user_id": recruiter_user.id,
        "valid_from": now.isoformat(),
        "valid_until": (now + timedelta(days=90)).isoformat(),
    }
    resp_valid = client.post(f"/api/v1/organisations/{org_id}/recruiters", json=valid_dates, headers=headers)
    assert resp_valid.status_code == status.HTTP_201_CREATED
    data = resp_valid.json()
    assert data["recruiter_user_id"] == recruiter_user.id
    assert data["recruiter_actor_id"].startswith("RE")


def test_fr0076_recruiter_organisation_scope(client, employer_user, recruiter_user):
    """FR-0076: Validate recruiter can only view/action requirements and details within mapped company boundary."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org1_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Alpha Technologies Ltd", "display_name": "AlphaTech", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    org2_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Beta Interactive Corp", "display_name": "BetaCorp", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # Map recruiter ONLY to Org 1
    client.post(
        f"/api/v1/organisations/{org1_id}/recruiters",
        json={"recruiter_user_id": recruiter_user.id},
        headers=headers,
    )

    recruiter_token = create_test_supabase_token(sub=recruiter_user.provider_subject, email=recruiter_user.email_address)
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # Recruiter accessing Org 1 recruiters succeeds
    resp_org1 = client.get(f"/api/v1/organisations/{org1_id}/recruiters", headers=recruiter_headers)
    assert resp_org1.status_code == status.HTTP_200_OK

    # Recruiter attempting to access Org 2 recruiters is denied with 403 Forbidden
    resp_org2 = client.get(f"/api/v1/organisations/{org2_id}/recruiters", headers=recruiter_headers)
    assert resp_org2.status_code == status.HTTP_403_FORBIDDEN


def test_fr0077_organisation_location_relationship(client, employer_user):
    """FR-0077: Validate location references existing organisation and valid geographic country master data."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Global Retail Hub India Pvt Ltd", "display_name": "Global Retail", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # 1. Invalid country ID rejected with 422
    resp_bad_country = client.post(
        f"/api/v1/organisations/{org_id}/locations",
        json={"name": "Bengaluru Tech Park", "country_id": 99999},
        headers=headers,
    )
    assert resp_bad_country.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 2. Valid country succeeds
    resp_good = client.post(
        f"/api/v1/organisations/{org_id}/locations",
        json={"name": "Bengaluru Innovation Hub", "country_id": 1},
        headers=headers,
    )
    assert resp_good.status_code == status.HTTP_201_CREATED
    assert resp_good.json()["name"] == "Bengaluru Innovation Hub"


def test_fr0078_organisation_deactivation(client, employer_user, db_session):
    """FR-0078: Validate deactivation blocks new job postings while preserving historical records."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Legacy Engineering Works Ltd", "display_name": "Legacy Works", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # 1. Create a job while active -> succeeds
    job_payload = {
        "organisation_id": org_id,
        "title": "Principal Architect",
        "description": "Lead distributed systems development",
        "job_role_id": 1,
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 2,
        "publish_now": True,
    }
    resp_job = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert resp_job.status_code == status.HTTP_201_CREATED

    # 2. Deactivate organisation (status_code_id: 3 = DEACTIVATED)
    deact_resp = client.patch(
        f"/api/v1/organisations/{org_id}/status",
        json={"status_code_id": 3, "reason": "Corporate restructuring and hiring freeze"},
        headers=headers,
    )
    assert deact_resp.status_code == status.HTTP_200_OK
    assert deact_resp.json()["status_code"] == "DEACTIVATED"

    # 3. New job posting attempt must be blocked
    resp_new_job = client.post(
        "/api/v1/jobs",
        json={**job_payload, "title": "Staff Engineer"},
        headers=headers,
    )
    assert resp_new_job.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY)
    assert "deactivated" in resp_new_job.json()["detail"].lower()


def test_fr0079_company_verification_provider_outage(client, employer_user):
    """FR-0079: Validate verification provider timeout handles failure gracefully without false success."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Resilient Systems Ltd", "display_name": "Resilient Systems", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # Trigger verification with simulated outage
    resp = client.post(
        f"/api/v1/organisations/{org_id}/verify",
        json={"name": "Govt Registrar API", "simulate_outage": True},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    # Must NOT be marked as VERIFIED
    assert data["status"] == "PENDING"
    assert data["status_code_id"] == 2
    assert "without false success" in data["message"]


def test_fr0080_organisation_audit_fields(client, employer_user, admin_user):
    """FR-0080: Validate created audit metadata remains stable while updated metadata changes."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Audited Dynamics Corp", "display_name": "Audited Dynamics", "primary_country_id": 1},
        headers=headers,
    ).json()

    org_id = create_resp["id"]
    initial_created_at = create_resp["created_at"]
    initial_created_by = create_resp["created_by"]

    # Admin updates display name
    admin_token = create_test_supabase_token(sub=admin_user.provider_subject, email=admin_user.email_address)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    update_resp = client.put(
        f"/api/v1/organisations/{org_id}",
        json={"display_name": "Audited Dynamics Global"},
        headers=admin_headers,
    ).json()

    # Created fields must remain unchanged
    assert update_resp["created_at"] == initial_created_at
    assert update_resp["created_by"] == initial_created_by
    # Updated by must reflect the updater (Admin user)
    assert update_resp["updated_by"] == admin_user.id


def test_fr0081_account_administrator_authorization(client, employer_user, recruiter_user, candidate_user):
    """FR-0081: Validate only assigned Account Administrators or platform Admins can administer organisation."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Enterprise Shield Ltd", "display_name": "Enterprise Shield", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # Candidate attempting administrative update receives 403 Forbidden
    candidate_token = create_test_supabase_token(sub=candidate_user.provider_subject, email=candidate_user.email_address)
    cand_headers = {"Authorization": f"Bearer {candidate_token}"}
    resp_cand = client.put(f"/api/v1/organisations/{org_id}", json={"display_name": "Hacked Name"}, headers=cand_headers)
    assert resp_cand.status_code == status.HTTP_403_FORBIDDEN

    # Recruiter of another company attempting administrative change receives 403 Forbidden
    recruiter_token = create_test_supabase_token(sub=recruiter_user.provider_subject, email=recruiter_user.email_address)
    rec_headers = {"Authorization": f"Bearer {recruiter_token}"}
    resp_rec = client.put(f"/api/v1/organisations/{org_id}", json={"display_name": "Unauthorized Edit"}, headers=rec_headers)
    assert resp_rec.status_code == status.HTTP_403_FORBIDDEN


def test_fr0082_organisation_identifier_format_preservation(client, employer_user):
    """FR-0082: Validate identifier preserves leading zeros and alphanumeric text without numeric truncation."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Numeric Precision Services Ltd", "display_name": "Numeric Precision", "primary_country_id": 2},
        headers=headers,
    ).json()["id"]

    # Identifier with leading zeros: "0012345"
    resp = client.post(
        f"/api/v1/organisations/{org_id}/identifiers",
        json={"country_id": 2, "identifier_type_code_id": 1, "identifier_value": "0012345"},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    # Masked identifier must retain correct length and suffix without dropping leading zeros
    assert resp.json()["masked_identifier"] == "***2345"


def test_fr0083_organisation_duplicate_detection(client, employer_user):
    """FR-0083: Validate duplicate organisation legal name in the same country is rejected with 409 Conflict."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "legal_name": "Unique Vision Technologies Private Limited",
        "display_name": "Unique Vision",
        "primary_country_id": 1,  # India
    }

    # First registration succeeds
    resp1 = client.post("/api/v1/organisations", json=payload, headers=headers)
    assert resp1.status_code == status.HTTP_201_CREATED

    # Exact duplicate legal name in same country is rejected with 409
    resp2 = client.post("/api/v1/organisations", json=payload, headers=headers)
    assert resp2.status_code == status.HTTP_409_CONFLICT
    assert "already registered" in resp2.json()["detail"]


def test_fr0202_soft_deleted_organisation_excluded_from_default_queries(client, employer_user, admin_user):
    """FR-0202: Validate soft-deleted organisation carries deleted_at and is excluded from default queries."""
    token = create_test_supabase_token(sub=employer_user.provider_subject, email=employer_user.email_address)
    headers = {"Authorization": f"Bearer {token}"}

    org_id = client.post(
        "/api/v1/organisations",
        json={"legal_name": "Ephemeral Labs Private Limited", "display_name": "Ephemeral Labs", "primary_country_id": 1},
        headers=headers,
    ).json()["id"]

    # Verify present in list
    list_before = client.get("/api/v1/organisations?q=Ephemeral", headers=headers).json()
    assert any(o["id"] == org_id for o in list_before["items"])

    # Soft-delete organisation
    del_resp = client.delete(f"/api/v1/organisations/{org_id}", headers=headers)
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify excluded from default list queries
    list_after = client.get("/api/v1/organisations?q=Ephemeral", headers=headers).json()
    assert not any(o["id"] == org_id for o in list_after["items"])

    # Default GET by ID returns 404
    get_resp = client.get(f"/api/v1/organisations/{org_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND

    # Admin querying with include_deleted=True can view the archived record
    admin_token = create_test_supabase_token(sub=admin_user.provider_subject, email=admin_user.email_address)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_get = client.get(f"/api/v1/organisations/{org_id}?include_deleted=true", headers=admin_headers)
    assert admin_get.status_code == status.HTTP_200_OK
    assert admin_get.json()["deleted_at"] is not None
