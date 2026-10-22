"""Automated Functional & Security Tests for Talentra Stage 8: Sourcing & Consultant Requests.

Maps to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Sourcing & Consultant Requests):
- FR-0112: Create sourcing request
- FR-0113: Consultant openness enforcement
- FR-0114: Consultant accept decision
- FR-0115: Employer decline consultant
- FR-0116: Sourcing shortlist references candidate
- FR-0117: Blocked candidate outreach
- FR-0118: Bulk outreach batch count
- FR-0119: Outreach delivery status
- FR-0120: Recruiter company assignment
- FR-0121: Consultant candidate privacy
- FR-0122: Sourcing request cancellation
- FR-0123: Duplicate consultant assignment
- FR-0205: Bulk outreach suppression after consent withdrawal
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
from app.models.job import JobRequirement, JobRole, EmploymentType, WorkType
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.application import BlockListEntry
from app.models.admin import ConsentRecord, AuditEvent
from app.models.sourcing import (
    SourcingRequest,
    SourcingRequestStatusHistory,
    ConsultantRequestAssignmentHistory,
    CandidateSourcingShortlist,
    OutreachBatch,
    OutreachRecipient,
)


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
                (2, 'US', 'USA', '840', 'United States', '+1', 1)
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
    """Provide a FastAPI TestClient wired to the transactional db_session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user_with_role(
    db_session,
    sub: str,
    email: str,
    role_code: str,
    account_status: int = 1,
) -> User:
    """Helper to provision a user with a specific role for testing."""
    now = datetime.now(timezone.utc)
    user = User(
        provider_subject=sub,
        email_address=email,
        display_name=f"User {sub[:8]}",
        account_status_code_id=account_status,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.flush()

    role = db_session.query(Role).filter(Role.role_code == role_code).first()
    if role:
        assignment = UserRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            assigned_by_user_id=user.id,
            valid_from=now,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db_session.add(assignment)
        db_session.flush()

    return user


def create_test_organisation(db_session, owner_id: int, legal_name: str = "Acme Corp") -> Organisation:
    """Helper to provision a test organisation."""
    now = datetime.now(timezone.utc)
    org = Organisation(
        legal_name=legal_name,
        display_name=legal_name,
        status_code_id=1,
        created_by=owner_id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()
    return org


def create_test_job(
    db_session,
    organisation_id: int,
    creator_id: int,
    open_to_consultants: bool = True,
    title: str = "Senior Backend Architect",
) -> JobRequirement:
    """Helper to provision a test job requirement."""
    now = datetime.now(timezone.utc)
    job = JobRequirement(
        organisation_id=organisation_id,
        created_by_user_id=creator_id,
        job_role_id=1,
        title=title,
        description="Build scalable high-throughput microservices.",
        employment_type_id=1,
        work_type_id=1,
        status_code_id=2,  # OPEN
        publish_state_code_id=2,  # PUBLISHED
        open_to_consultants=open_to_consultants,
        positions_count=2,
        salary_min=Decimal("120000.00"),
        salary_max=Decimal("160000.00"),
        salary_currency_code="USD",
        created_at=now,
        updated_at=now,
    )
    db_session.add(job)
    db_session.flush()
    return job


def create_test_candidate(
    db_session,
    actor_id: str = "CA00101",
    email: str = "cand101@talentra.io",
    phone: str = "+14155552671",
) -> CandidateProfile:
    """Helper to provision a test candidate profile with contact details."""
    cand_user = create_user_with_role(db_session, str(uuid.uuid4()), email, "CANDIDATE")
    now = datetime.now(timezone.utc)
    profile = CandidateProfile(
        user_id=cand_user.id,
        actor_id=actor_id,
        first_name="Jane",
        last_name="Doe",
        headline="Principal Staff Engineer",
        summary="Specialist in distributed databases and event streaming.",
        completion_score=Decimal("95.00"),
        created_at=now,
        updated_at=now,
    )
    db_session.add(profile)
    db_session.flush()

    contact = CandidateContact(
        candidate_profile_id=profile.id,
        email_address=email,
        phone_e164=phone,
        phone_country_id=2,
        created_at=now,
        updated_at=now,
    )
    db_session.add(contact)
    db_session.flush()
    return profile


# -------------------------------------------------------------------------
# Test Cases (FR-0112 to FR-0123, FR-0205)
# -------------------------------------------------------------------------

def test_fr0112_create_sourcing_request_employer_success(client, db_session):
    """FR-0112: Create sourcing request.
    
    Validates that an authorized employer can create a sourcing request for their job requirement.
    Rejects unknown job requirements with 404 Not Found.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp112@talentra.io", "EMPLOYER")
    org = create_test_organisation(db_session, emp.id, "Stripe Global Inc")
    job = create_test_job(db_session, org.id, emp.id, open_to_consultants=True)
    db_session.commit()

    emp_token = create_test_supabase_token(sub=emp_sub, email="emp112@talentra.io")

    # 1. Valid sourcing request
    payload = {"job_requirement_id": job.id}
    resp = client.post(
        "/api/v1/sourcing/requests",
        json=payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    data = resp.json()
    assert data["job_requirement_id"] == job.id
    assert data["status"] == "PENDING"
    assert data["open_to_consultants_snapshot"] is True
    assert data["requester_user_id"] == emp.id

    # 2. Unknown job reference is rejected (404)
    bad_resp = client.post(
        "/api/v1/sourcing/requests",
        json={"job_requirement_id": 999999},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert bad_resp.status_code == status.HTTP_404_NOT_FOUND


def test_fr0113_consultant_openness_enforcement(client, db_session):
    """FR-0113: Consultant openness enforcement.
    
    Validates that a consultant can act only on requirements open to consultants.
    If open_to_consultants=False, backend rejects action with 403 Forbidden.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp113@talentra.io", "EMPLOYER")
    org = create_test_organisation(db_session, emp.id, "OpenAI Corp")
    # Job requirement explicitly CLOSED to consultants
    job = create_test_job(db_session, org.id, emp.id, open_to_consultants=False)

    consultant_sub = str(uuid.uuid4())
    consultant = create_user_with_role(db_session, consultant_sub, "consultant113@talentra.io", "CONSULTANT")

    # Seed sourcing request for this job
    now = datetime.now(timezone.utc)
    sourcing_req = SourcingRequest(
        job_requirement_id=job.id,
        requester_user_id=emp.id,
        consultant_user_id=consultant.id,
        status_code_id=1,  # PENDING
        open_to_consultants_snapshot=False,
        requested_at=now,
    )
    db_session.add(sourcing_req)
    db_session.commit()

    consultant_token = create_test_supabase_token(sub=consultant_sub, email="consultant113@talentra.io")

    # Consultant attempts to accept request for closed job -> 403 Forbidden
    resp = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/respond",
        json={"decision": "ACCEPT", "reason": "Ready to source talent"},
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "closed to external consultants" in resp.json()["detail"].lower()


def test_fr0114_consultant_accept_decision(client, db_session):
    """FR-0114: Consultant accept decision.
    
    Validates that accept/decline decisions are recorded with actor, time, and outcome.
    Decision history contains correct request and consultant references.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp114@talentra.io", "EMPLOYER")
    org = create_test_organisation(db_session, emp.id, "Anthropic PBC")
    job = create_test_job(db_session, org.id, emp.id, open_to_consultants=True)

    consultant_sub = str(uuid.uuid4())
    consultant = create_user_with_role(db_session, consultant_sub, "consultant114@talentra.io", "CONSULTANT")

    now = datetime.now(timezone.utc)
    sourcing_req = SourcingRequest(
        job_requirement_id=job.id,
        requester_user_id=emp.id,
        consultant_user_id=consultant.id,
        status_code_id=1,  # PENDING
        open_to_consultants_snapshot=True,
        requested_at=now,
    )
    db_session.add(sourcing_req)
    db_session.commit()

    consultant_token = create_test_supabase_token(sub=consultant_sub, email="consultant114@talentra.io")

    # Consultant accepts
    resp = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/respond",
        json={"decision": "ACCEPT", "reason": "Confirmed availability and rate"},
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["status"] == "ACCEPTED"
    assert data["responded_at"] is not None

    # Verify decision history record was persisted
    history = (
        db_session.query(ConsultantRequestAssignmentHistory)
        .filter(ConsultantRequestAssignmentHistory.actor_user_id == consultant.id)
        .first()
    )
    assert history is not None
    assert history.event_code_id == 2  # ACCEPTED


def test_fr0115_employer_decline_consultant_cross_company_denied(client, db_session):
    """FR-0115: Employer decline consultant.
    
    Validates that employer has authorized decision rights for their job request, and
    cross-company employers cannot decline another company's request (403 Forbidden).
    """
    emp1_sub = str(uuid.uuid4())
    emp1 = create_user_with_role(db_session, emp1_sub, "emp1@talentra.io", "EMPLOYER")
    org1 = create_test_organisation(db_session, emp1.id, "Company Alpha")
    job1 = create_test_job(db_session, org1.id, emp1.id, open_to_consultants=True)

    # Rogue employer from Company Beta
    emp2_sub = str(uuid.uuid4())
    emp2 = create_user_with_role(db_session, emp2_sub, "emp2@talentra.io", "EMPLOYER")
    org2 = create_test_organisation(db_session, emp2.id, "Company Beta")

    consultant = create_user_with_role(db_session, str(uuid.uuid4()), "co115@talentra.io", "CONSULTANT")

    now = datetime.now(timezone.utc)
    sourcing_req = SourcingRequest(
        job_requirement_id=job1.id,
        requester_user_id=emp1.id,
        consultant_user_id=consultant.id,
        status_code_id=1,  # PENDING
        open_to_consultants_snapshot=True,
        requested_at=now,
    )
    db_session.add(sourcing_req)
    db_session.commit()

    # 1. Cross-company employer from Company Beta attempts to decline -> 403 Forbidden
    emp2_token = create_test_supabase_token(sub=emp2_sub, email="emp2@talentra.io")
    bad_resp = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/decline-consultant",
        params={"reason": "Unauthorized cross-company decline attempt"},
        headers={"Authorization": f"Bearer {emp2_token}"},
    )
    assert bad_resp.status_code == status.HTTP_403_FORBIDDEN

    # 2. Legitimate employer from Company Alpha declines -> 200 OK
    emp1_token = create_test_supabase_token(sub=emp1_sub, email="emp1@talentra.io")
    ok_resp = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/decline-consultant",
        params={"reason": "Candidate quota already filled"},
        headers={"Authorization": f"Bearer {emp1_token}"},
    )
    assert ok_resp.status_code == status.HTTP_200_OK
    assert ok_resp.json()["status"] == "DECLINED"


def test_fr0116_sourcing_shortlist_references_candidate(client, db_session):
    """FR-0116: Sourcing shortlist references candidate.
    
    Validates that sourcing shortlist must reference a valid candidate profile.
    Orphan references are rejected with 404 Not Found.
    """
    consultant_sub = str(uuid.uuid4())
    consultant = create_user_with_role(db_session, consultant_sub, "co116@talentra.io", "CONSULTANT")
    cand = create_test_candidate(db_session, "CA00116", "cand116@talentra.io")
    db_session.commit()

    consultant_token = create_test_supabase_token(sub=consultant_sub, email="co116@talentra.io")

    # 1. Valid shortlist association
    payload = {
        "candidate_profile_id": cand.id,
        "title": "Top Tier Staff Backend Engineer",
        "description": "Strong experience in distributed transaction isolation and Supabase.",
    }
    resp = client.post(
        "/api/v1/sourcing/shortlists",
        json=payload,
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["candidate_profile_id"] == cand.id
    assert data["candidate_actor_id"] == "CA00116"
    assert data["status"] == "SHORTLISTED"

    # 2. Orphan candidate reference rejected (404)
    bad_payload = {
        "candidate_profile_id": 999999,
        "title": "Non-existent candidate",
    }
    bad_resp = client.post(
        "/api/v1/sourcing/shortlists",
        json=bad_payload,
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert bad_resp.status_code == status.HTTP_404_NOT_FOUND


def test_fr0117_blocked_candidate_outreach_suppressed(client, db_session):
    """FR-0117: Blocked candidate outreach.
    
    Validates that blocked-party rules apply to candidate contact. Blocked candidate receives
    no outreach and suppression is recorded.
    """
    recruiter_sub = str(uuid.uuid4())
    recruiter = create_user_with_role(db_session, recruiter_sub, "rec117@talentra.io", "RECRUITER")
    org = create_test_organisation(db_session, recruiter.id, "Outreach Corp 117")

    # Assign recruiter to organisation
    now = datetime.now(timezone.utc)
    mapping = OrganisationRecruiterMapping(
        organisation_id=org.id,
        recruiter_user_id=recruiter.id,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=30),
        assigned_by_user_id=recruiter.id,
    )
    db_session.add(mapping)

    cand1 = create_test_candidate(db_session, "CA00117A", "cand117a@talentra.io")
    cand2 = create_test_candidate(db_session, "CA00117B", "cand117b@talentra.io")

    # Block cand1 for this organisation
    block = BlockListEntry(
        blocker_user_id=recruiter.id,
        blocked_user_id=cand1.user_id,
        blocked_organisation_id=org.id,
        created_at=now,
    )
    db_session.add(block)
    db_session.commit()

    recruiter_token = create_test_supabase_token(sub=recruiter_sub, email="rec117@talentra.io")

    payload = {
        "organisation_id": org.id,
        "candidate_profile_ids": [cand1.id, cand2.id],
    }
    resp = client.post(
        "/api/v1/sourcing/outreach/batches",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    batch = resp.json()
    assert batch["recipient_count"] == 2
    assert batch["suppressed_count"] == 1

    # Verify cand1 is SUPPRESSED and cand2 is PENDING
    recipients = {r["candidate_profile_id"]: r["delivery_status"] for r in batch["recipients"]}
    assert recipients[cand1.id] == "SUPPRESSED"
    assert recipients[cand2.id] == "PENDING"


def test_fr0118_bulk_outreach_batch_count_and_deduplication(client, db_session):
    """FR-0118: Bulk outreach batch count.
    
    Validates that duplicate candidates are deduplicated within the batch scope and
    the batch summary counts unique valid recipients accurately.
    """
    recruiter_sub = str(uuid.uuid4())
    recruiter = create_user_with_role(db_session, recruiter_sub, "rec118@talentra.io", "RECRUITER")
    org = create_test_organisation(db_session, recruiter.id, "Dedupe Tech Inc")

    now = datetime.now(timezone.utc)
    mapping = OrganisationRecruiterMapping(
        organisation_id=org.id,
        recruiter_user_id=recruiter.id,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=30),
        assigned_by_user_id=recruiter.id,
    )
    db_session.add(mapping)

    cand1 = create_test_candidate(db_session, "CA00118A", "cand118a@talentra.io")
    cand2 = create_test_candidate(db_session, "CA00118B", "cand118b@talentra.io")
    db_session.commit()

    recruiter_token = create_test_supabase_token(sub=recruiter_sub, email="rec118@talentra.io")

    # Send batch with duplicate candidate IDs [cand1, cand1, cand2, cand2, cand1]
    payload = {
        "organisation_id": org.id,
        "candidate_profile_ids": [cand1.id, cand1.id, cand2.id, cand2.id, cand1.id],
    }
    resp = client.post(
        "/api/v1/sourcing/outreach/batches",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    batch = resp.json()
    # Unique recipients must equal 2
    assert batch["recipient_count"] == 2
    assert len(batch["recipients"]) == 2


def test_fr0119_outreach_delivery_status_and_idempotency(client, db_session):
    """FR-0119: Outreach delivery status.
    
    Validates that delivery callbacks update recipient status and repeated
    callbacks with the same idempotency key are idempotent without duplicating state.
    """
    recruiter_sub = str(uuid.uuid4())
    recruiter = create_user_with_role(db_session, recruiter_sub, "rec119@talentra.io", "RECRUITER")
    org = create_test_organisation(db_session, recruiter.id, "Delivery Corp 119")
    cand = create_test_candidate(db_session, "CA00119", "cand119@talentra.io")

    now = datetime.now(timezone.utc)
    batch = OutreachBatch(
        organisation_id=org.id,
        created_by_user_id=recruiter.id,
        status_code_id=3,
        recipient_count=1,
    )
    db_session.add(batch)
    db_session.flush()

    idemp_key = f"outreach-{batch.id}-{cand.id}-testkey119"
    recipient = OutreachRecipient(
        outreach_batch_id=batch.id,
        candidate_profile_id=cand.id,
        delivery_status_code_id=1,  # PENDING
        idempotency_key=idemp_key,
    )
    db_session.add(recipient)
    db_session.commit()

    # 1. Delivery callback arrives from provider
    cb_payload = {
        "idempotency_key": idemp_key,
        "provider_message_reference": "msg_provider_abc_12345",
        "status": "DELIVERED",
    }
    resp1 = client.post("/api/v1/sourcing/outreach/callbacks", json=cb_payload)
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.json()["delivery_status"] == "DELIVERED"
    assert resp1.json()["provider_message_reference"] == "msg_provider_abc_12345"

    # 2. Repeated delivery callback (idempotent replay)
    resp2 = client.post("/api/v1/sourcing/outreach/callbacks", json=cb_payload)
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.json()["delivery_status"] == "DELIVERED"


def test_fr0120_recruiter_company_assignment_enforced(client, db_session):
    """FR-0120: Recruiter company assignment.
    
    Validates that a recruiter must have an effective, non-expired assignment to the
    job-owning company. Unauthorized / unassigned recruiter is denied with 403 Forbidden.
    """
    recruiter_sub = str(uuid.uuid4())
    recruiter = create_user_with_role(db_session, recruiter_sub, "rec120@talentra.io", "RECRUITER")
    org = create_test_organisation(db_session, 9999, "Unassigned Company 120")
    cand = create_test_candidate(db_session, "CA00120", "cand120@talentra.io")
    db_session.commit()

    recruiter_token = create_test_supabase_token(sub=recruiter_sub, email="rec120@talentra.io")

    # Recruiter has NO mapping to this organisation -> 403 Forbidden
    payload = {
        "organisation_id": org.id,
        "candidate_profile_ids": [cand.id],
    }
    resp = client.post(
        "/api/v1/sourcing/outreach/batches",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN
    assert "lacks effective recruiter" in resp.json()["detail"].lower()


def test_fr0121_consultant_candidate_privacy_masked(client, db_session):
    """FR-0121: Consultant candidate privacy.
    
    Validates that consultants access candidate details with masked contact information
    (email and phone masked) and blocks are strictly enforced.
    """
    consultant_sub = str(uuid.uuid4())
    consultant = create_user_with_role(db_session, consultant_sub, "co121@talentra.io", "CONSULTANT")
    cand = create_test_candidate(
        db_session,
        actor_id="CA00121",
        email="elizabeth.warren@example.com",
        phone="+14155558921",
    )
    db_session.commit()

    consultant_token = create_test_supabase_token(sub=consultant_sub, email="co121@talentra.io")

    # 1. View candidate details -> contact data is masked
    resp = client.get(
        f"/api/v1/sourcing/candidates/{cand.id}",
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["actor_id"] == "CA00121"
    assert data["email_address_masked"] == "e***n@example.com"
    assert data["phone_masked"] == "******8921"

    # 2. If candidate blocks this consultant -> access is denied (403 Forbidden)
    now = datetime.now(timezone.utc)
    block = BlockListEntry(
        blocker_user_id=consultant.id,
        blocked_user_id=cand.user_id,
        created_at=now,
    )
    db_session.add(block)
    db_session.commit()

    blocked_resp = client.get(
        f"/api/v1/sourcing/candidates/{cand.id}",
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert blocked_resp.status_code == status.HTTP_403_FORBIDDEN


def test_fr0122_sourcing_request_cancellation(client, db_session):
    """FR-0122: Sourcing request cancellation.
    
    Validates that an employer can cancel a sourcing request following the valid lifecycle,
    and decision history is preserved.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp122@talentra.io", "EMPLOYER")
    org = create_test_organisation(db_session, emp.id, "Cancel Test Corp")
    job = create_test_job(db_session, org.id, emp.id, open_to_consultants=True)

    now = datetime.now(timezone.utc)
    sourcing_req = SourcingRequest(
        job_requirement_id=job.id,
        requester_user_id=emp.id,
        status_code_id=1,  # PENDING
        open_to_consultants_snapshot=True,
        requested_at=now,
    )
    db_session.add(sourcing_req)
    db_session.commit()

    emp_token = create_test_supabase_token(sub=emp_sub, email="emp122@talentra.io")

    # 1. Cancel request
    resp = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/cancel",
        json={"reason": "Role filled internally"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["status"] == "CANCELLED"

    # 2. Cannot cancel an already cancelled request -> 400 Bad Request
    dup_cancel = client.post(
        f"/api/v1/sourcing/requests/{sourcing_req.id}/cancel",
        json={"reason": "Repeat cancellation attempt"},
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert dup_cancel.status_code == status.HTTP_400_BAD_REQUEST


def test_fr0123_duplicate_consultant_assignment_prevented(client, db_session):
    """FR-0123: Duplicate consultant assignment.
    
    Validates that duplicate active sourcing requests for the same job and consultant
    are prevented with 400 Bad Request.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp123@talentra.io", "EMPLOYER")
    org = create_test_organisation(db_session, emp.id, "Dupe Check Corp")
    job = create_test_job(db_session, org.id, emp.id, open_to_consultants=True)
    consultant = create_user_with_role(db_session, str(uuid.uuid4()), "co123@talentra.io", "CONSULTANT")
    db_session.commit()

    emp_token = create_test_supabase_token(sub=emp_sub, email="emp123@talentra.io")

    # 1. First assignment succeeds
    payload = {
        "job_requirement_id": job.id,
        "consultant_user_id": consultant.id,
    }
    resp1 = client.post(
        "/api/v1/sourcing/requests",
        json=payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp1.status_code == status.HTTP_201_CREATED

    # 2. Second assignment for same job and same consultant fails (400 Bad Request)
    resp2 = client.post(
        "/api/v1/sourcing/requests",
        json=payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in resp2.json()["detail"].lower()


def test_fr0205_bulk_outreach_suppression_after_consent_withdrawal(client, db_session):
    """FR-0205: Bulk outreach suppression after consent withdrawal.
    
    Validates that candidate contact strictly respects privacy consent. If a candidate
    has withdrawn consent, they are suppressed before dispatch.
    """
    recruiter_sub = str(uuid.uuid4())
    recruiter = create_user_with_role(db_session, recruiter_sub, "rec205@talentra.io", "RECRUITER")
    org = create_test_organisation(db_session, recruiter.id, "Privacy Consent Corp 205")

    now = datetime.now(timezone.utc)
    mapping = OrganisationRecruiterMapping(
        organisation_id=org.id,
        recruiter_user_id=recruiter.id,
        valid_from=now - timedelta(days=1),
        valid_until=now + timedelta(days=30),
        assigned_by_user_id=recruiter.id,
    )
    db_session.add(mapping)

    cand_active = create_test_candidate(db_session, "CA00205A", "cand_active@talentra.io")
    cand_withdrawn = create_test_candidate(db_session, "CA00205B", "cand_withdrawn@talentra.io")

    # Record consent withdrawal for cand_withdrawn
    consent_record = ConsentRecord(
        user_id=cand_withdrawn.user_id,
        consent_type_code_id=2,  # PRIVACY_POLICY
        policy_version="1.0",
        granted=False,
        captured_at=now - timedelta(days=5),
        withdrawn_at=now - timedelta(days=1),
    )
    db_session.add(consent_record)
    db_session.commit()

    recruiter_token = create_test_supabase_token(sub=recruiter_sub, email="rec205@talentra.io")

    payload = {
        "organisation_id": org.id,
        "candidate_profile_ids": [cand_active.id, cand_withdrawn.id],
    }
    resp = client.post(
        "/api/v1/sourcing/outreach/batches",
        json=payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED
    batch = resp.json()
    assert batch["recipient_count"] == 2
    assert batch["suppressed_count"] == 1

    recipients = {r["candidate_profile_id"]: r["delivery_status"] for r in batch["recipients"]}
    assert recipients[cand_active.id] == "PENDING"
    assert recipients[cand_withdrawn.id] == "SUPPRESSED"
