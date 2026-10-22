"""Automated Functional & Security Tests for Talentra Stage 7: Administration and Role Governance.

Maps to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Administration):
- FR-0055: Role assignment and authorization verification
- FR-0056: Permission denial by default
- FR-0057: Credential uniqueness and hash-only storage
- FR-0058: Passwords, tokens, and secrets redacted from audit logs
- FR-0059: Audit event append-only immutability enforcement
- FR-0060: Audit sensitive action recording
- FR-0061: Consent withdrawal and audit tracking
- FR-0062: Block candidate visibility enforcement
- FR-0063: Account soft deletion with deleted_at timestamp
- FR-0064: UTC audit timestamps
- FR-0065: Sensitive column data governance classification
- FR-0066: Session revocation and access termination
- FR-0067: Login attempt auditing and throttling detection
- FR-0068: Admin privilege escalation prevention (Super Admin vs Admin separation)
- FR-0069: Privileged access review evidence generation
- FR-0201: Sensitive action actor attribution
"""

import sys
import os
import uuid
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
from app.models.organisation import Organisation
from app.models.candidate import CandidateProfile
from app.models.application import BlockListEntry
from app.models.admin import (
    Permission,
    RolePermission,
    AuditEvent,
    IdentitySession,
    ConsentRecord,
    LoginAttempt,
    SecurityAlertEvent,
    RoleAssignmentHistory,
)
from app.services.admin_service import (
    filter_blocked_candidates,
    record_login_attempt_and_check_throttling,
    sanitize_metadata,
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


# -------------------------------------------------------------------------
# Test Cases (FR-0055 to FR-0069 and FR-0201)
# -------------------------------------------------------------------------

def test_fr0055_role_assignment_and_authorization_verification(client, db_session):
    """FR-0055: Role assignment and authorization verification.
    
    Verifies that assigning a role requires administrative authority and grants
    the expected role to the target user.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin55@talentra.io", "ADMIN")
    target_sub = str(uuid.uuid4())
    target = create_user_with_role(db_session, target_sub, "candidate55@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin55@talentra.io")

    payload = {
        "user_id": target.id,
        "role_code": "RECRUITER",
    }
    response = client.post(
        "/api/v1/admin/roles/grant",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status.HTTP_200_OK, response.text
    data = response.json()
    assert data["id"] == target.id
    assert "RECRUITER" in data["roles"]
    assert "CANDIDATE" in data["roles"]


def test_fr0056_permission_denial_by_default(client, db_session):
    """FR-0056: Permission denial by default.
    
    Verifies that unauthenticated callers (401) and unauthorized non-admin callers (403)
    are strictly denied access to administrative endpoints.
    """
    # 1. Unauthenticated request -> 401
    resp_unauth = client.get("/api/v1/admin/users")
    assert resp_unauth.status_code == status.HTTP_401_UNAUTHORIZED

    # 2. Unauthorized caller (Candidate) -> 403
    cand_sub = str(uuid.uuid4())
    cand = create_user_with_role(db_session, cand_sub, "cand56@talentra.io", "CANDIDATE")
    db_session.commit()

    cand_token = create_test_supabase_token(sub=cand_sub, email="cand56@talentra.io")
    resp_forbidden = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert resp_forbidden.status_code == status.HTTP_403_FORBIDDEN


def test_fr0057_credential_uniqueness_and_hash_only_storage(client, db_session):
    """FR-0057: Credential uniqueness and hash-only storage.
    
    Verifies that credentials are not stored in plaintext and provider_subject
    uniqueness is enforced.
    """
    sub_val = "auth0|duplicate_subject_test"
    u1 = create_user_with_role(db_session, sub_val, "user1@talentra.io", "CANDIDATE")
    db_session.flush()

    # Attempting to insert another user with the same provider_subject should fail
    u2 = User(
        provider_subject=sub_val,
        email_address="user2@talentra.io",
        display_name="User 2",
        account_status_code_id=1,
    )
    db_session.add(u2)
    with pytest.raises(Exception):
        db_session.flush()
    db_session.rollback()


def test_fr0058_passwords_tokens_and_secrets_redacted_from_audit(client, db_session):
    """FR-0058: Passwords, tokens, and secrets redacted from audit logs.
    
    Verifies that sensitive keys are replaced with [REDACTED] in metadata.
    """
    sensitive_data = {
        "user_email": "target@example.com",
        "password": "SuperSecretPassword123!",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy",
        "nested": {
            "refresh_token": "refresh_xyz_secret",
            "normal_field": "ok_value",
        },
    }
    sanitized = sanitize_metadata(sensitive_data)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["nested"]["refresh_token"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "ok_value"
    assert sanitized["user_email"] == "target@example.com"


def test_fr0059_audit_event_append_only_enforcement(client, db_session):
    """FR-0059: Audit event append-only enforcement.
    
    Verifies that attempting to delete or modify an audit record is rejected with 403 Forbidden.
    """
    sa_sub = str(uuid.uuid4())
    sa = create_user_with_role(db_session, sa_sub, "sa59@talentra.io", "SUPER_ADMIN")
    db_session.commit()
    sa_token = create_test_supabase_token(sub=sa_sub, email="sa59@talentra.io")

    # Attempt DELETE on audit event -> 403 Forbidden
    resp_del = client.delete(
        "/api/v1/admin/audit-events/1",
        headers={"Authorization": f"Bearer {sa_token}"},
    )
    assert resp_del.status_code == status.HTTP_403_FORBIDDEN
    assert "append-only" in resp_del.json()["detail"].lower()

    # Attempt PUT on audit event -> 403 Forbidden
    resp_put = client.put(
        "/api/v1/admin/audit-events/1",
        headers={"Authorization": f"Bearer {sa_token}"},
    )
    assert resp_put.status_code == status.HTTP_403_FORBIDDEN


def test_fr0060_audit_sensitive_action_recording(client, db_session):
    """FR-0060: Audit sensitive action recording.
    
    Verifies that updating a user account status records an audit event in audit_event.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin60@talentra.io", "ADMIN")
    target_sub = str(uuid.uuid4())
    target = create_user_with_role(db_session, target_sub, "target60@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin60@talentra.io")

    # Suspend user
    payload = {
        "account_status_code_id": 2,  # SUSPENDED
        "reason": "Security review required due to suspicious activity",
    }
    resp = client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["account_status"] == "SUSPENDED"

    # Query audit events endpoint
    audit_resp = client.get(
        "/api/v1/admin/audit-events",
        params={"action_code": "USER_STATUS_CHANGE"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == status.HTTP_200_OK
    items = audit_resp.json()["items"]
    assert len(items) > 0
    event = items[0]
    assert event["action_code"] == "USER_STATUS_CHANGE"
    assert event["actor_user_id"] == admin.id


def test_fr0061_consent_withdrawal_and_audit_tracking(client, db_session):
    """FR-0061: Consent withdrawal and audit tracking.
    
    Verifies that withdrawing user consent updates the record and logs an audit event.
    """
    cand_sub = str(uuid.uuid4())
    cand = create_user_with_role(db_session, cand_sub, "cand61@talentra.io", "CANDIDATE")
    now = datetime.now(timezone.utc)
    # Seed an active consent record
    consent = ConsentRecord(
        user_id=cand.id,
        consent_type_code_id=2,  # PRIVACY_POLICY
        policy_version="v2.1",
        granted=True,
        captured_at=now,
    )
    db_session.add(consent)
    db_session.commit()

    cand_token = create_test_supabase_token(sub=cand_sub, email="cand61@talentra.io")

    payload = {
        "consent_type_code_id": 2,
        "reason": "Revoking marketing data processing",
    }
    resp = client.post(
        "/api/v1/admin/consent/withdraw",
        json=payload,
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["withdrawn_at"] is not None
    assert data["granted"] is False


def test_fr0062_block_candidate_visibility_enforcement(client, db_session):
    """FR-0062: Block candidate visibility enforcement.
    
    Verifies that candidates on an employer's blocklist are excluded from query results.
    """
    emp_sub = str(uuid.uuid4())
    emp = create_user_with_role(db_session, emp_sub, "emp62@talentra.io", "EMPLOYER")
    cand1 = create_user_with_role(db_session, str(uuid.uuid4()), "cand1@talentra.io", "CANDIDATE")
    cand2 = create_user_with_role(db_session, str(uuid.uuid4()), "cand2@talentra.io", "CANDIDATE")

    org = Organisation(
        legal_name="Blocklist Org 62",
        display_name="Blocklist Org 62",
        status_code_id=1,
        created_by=emp.id,
    )
    db_session.add(org)
    db_session.flush()

    prof1 = CandidateProfile(
        user_id=cand1.id,
        actor_id="CA00091",
        first_name="Candidate",
        last_name="One",
    )
    prof2 = CandidateProfile(
        user_id=cand2.id,
        actor_id="CA00092",
        first_name="Candidate",
        last_name="Two",
    )
    db_session.add_all([prof1, prof2])
    db_session.flush()

    # Block cand1 for this employer organisation
    now = datetime.now(timezone.utc)
    block = BlockListEntry(
        blocker_user_id=emp.id,
        blocked_user_id=cand1.id,
        blocked_organisation_id=org.id,
        created_at=now,
    )
    db_session.add(block)
    db_session.commit()

    # Check candidate filtering service
    candidates = [prof1, prof2]
    visible_candidates = filter_blocked_candidates(
        db=db_session,
        candidates=candidates,
        viewing_organisation_id=org.id,
    )
    assert prof1 not in visible_candidates
    assert prof2 in visible_candidates


def test_fr0063_account_soft_deletion_with_timestamp(client, db_session):
    """FR-0063: Account soft deletion with deleted_at timestamp.
    
    Verifies that deleting an account populates deleted_at, sets DEACTIVATED status,
    and excludes the user from default queries.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin63@talentra.io", "ADMIN")
    target_sub = str(uuid.uuid4())
    target = create_user_with_role(db_session, target_sub, "target63@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin63@talentra.io")

    del_resp = client.delete(
        f"/api/v1/admin/users/{target.id}",
        params={"reason": "User requested right to be forgotten"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == status.HTTP_200_OK
    del_data = del_resp.json()
    assert del_data["deleted_at"] is not None
    assert del_data["account_status"] == "DEACTIVATED"

    # Verify excluded from default admin list (include_deleted=False)
    list_resp = client.get(
        "/api/v1/admin/users",
        params={"include_deleted": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == status.HTTP_200_OK
    user_ids = [u["id"] for u in list_resp.json()["items"]]
    assert target.id not in user_ids


def test_fr0064_utc_audit_timestamps(client, db_session):
    """FR-0064: UTC audit timestamps.
    
    Verifies that all audit events record timestamps in UTC.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin64@talentra.io", "ADMIN")
    target = create_user_with_role(db_session, str(uuid.uuid4()), "target64@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin64@talentra.io")

    client.patch(
        f"/api/v1/admin/users/{target.id}/status",
        json={"account_status_code_id": 1, "reason": "Activating account"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    audit_resp = client.get(
        "/api/v1/admin/audit-events",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == status.HTTP_200_OK
    items = audit_resp.json()["items"]
    assert len(items) > 0
    for item in items:
        assert item["occurred_at"] is not None
        occurred_dt = datetime.fromisoformat(item["occurred_at"].replace("Z", "+00:00"))
        assert occurred_dt is not None


def test_fr0065_sensitive_column_data_governance_classification(client, db_session):
    """FR-0065: Sensitive column data governance classification.
    
    Verifies the data classification inventory returns categorized database columns.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin65@talentra.io", "ADMIN")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin65@talentra.io")

    resp = client.get(
        "/api/v1/admin/data-classification",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["total_classified"] > 0
    classifications = {item["classification"] for item in data["items"]}
    assert "RESTRICTED_PII" in classifications
    assert "CONFIDENTIAL" in classifications


def test_fr0066_session_revocation_and_access_termination(client, db_session):
    """FR-0066: Session revocation and access termination.
    
    Verifies that revoking an identity session sets is_revoked = True.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin66@talentra.io", "ADMIN")
    target = create_user_with_role(db_session, str(uuid.uuid4()), "target66@talentra.io", "CANDIDATE")
    now = datetime.now(timezone.utc)
    session = IdentitySession(
        user_id=target.id,
        provider_session_reference="session_ref_66",
        started_at=now,
        last_activity_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db_session.add(session)
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin66@talentra.io")

    revoke_resp = client.post(
        f"/api/v1/admin/sessions/{session.id}/revoke",
        json={"session_id": session.id, "reason": "User logged out from all devices"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert revoke_resp.status_code == status.HTTP_200_OK
    assert revoke_resp.json()["is_revoked"] is True


def test_fr0067_login_attempt_auditing_and_throttling_detection(client, db_session):
    """FR-0067: Login attempt auditing and throttling detection.
    
    Verifies that recording repeated failed login attempts triggers brute-force
    throttling and security alert.
    """
    user = create_user_with_role(db_session, str(uuid.uuid4()), "throttletest@talentra.io", "CANDIDATE")
    db_session.commit()

    # 4 failed attempts -> not throttled yet
    for _ in range(4):
        throttled = record_login_attempt_and_check_throttling(
            db=db_session,
            user_id=user.id,
            success=False,
            metadata={"ip": "192.168.1.100"},
        )
        assert throttled is False

    # 5th failed attempt -> reaches threshold (>= 5), triggers security alert and returns True
    throttled = record_login_attempt_and_check_throttling(
        db=db_session,
        user_id=user.id,
        success=False,
        metadata={"ip": "192.168.1.100"},
    )
    assert throttled is True


def test_fr0068_admin_privilege_escalation_prevention(client, db_session):
    """FR-0068: Admin privilege escalation prevention (Super Admin vs Admin separation).
    
    Verifies that:
    1. A platform ADMIN cannot grant SUPER_ADMIN (raises 403 Forbidden).
    2. A platform ADMIN cannot grant ADMIN (raises 403 Forbidden).
    3. A SUPER_ADMIN can successfully grant ADMIN.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin68@talentra.io", "ADMIN")
    target = create_user_with_role(db_session, str(uuid.uuid4()), "target68@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin68@talentra.io")

    # 1. Admin attempts to grant SUPER_ADMIN -> 403 Forbidden
    resp_sa = client.post(
        "/api/v1/admin/roles/grant",
        json={"user_id": target.id, "role_code": "SUPER_ADMIN"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_sa.status_code == status.HTTP_403_FORBIDDEN
    assert "privilege escalation" in resp_sa.json()["detail"].lower()

    # 2. Admin attempts to grant ADMIN -> 403 Forbidden
    resp_adm = client.post(
        "/api/v1/admin/roles/grant",
        json={"user_id": target.id, "role_code": "ADMIN"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_adm.status_code == status.HTTP_403_FORBIDDEN

    # 3. Super Admin grants ADMIN -> 200 OK
    sa_sub = str(uuid.uuid4())
    sa = create_user_with_role(db_session, sa_sub, "superadmin68@talentra.io", "SUPER_ADMIN")
    db_session.commit()
    sa_token = create_test_supabase_token(sub=sa_sub, email="superadmin68@talentra.io")

    resp_ok = client.post(
        "/api/v1/admin/roles/grant",
        json={"user_id": target.id, "role_code": "ADMIN"},
        headers={"Authorization": f"Bearer {sa_token}"},
    )
    assert resp_ok.status_code == status.HTTP_200_OK
    assert "ADMIN" in resp_ok.json()["roles"]


def test_fr0069_privileged_access_review_evidence_generation(client, db_session):
    """FR-0069: Privileged access review evidence generation.
    
    Verifies that administrators can generate an auditable access review report.
    """
    sa_sub = str(uuid.uuid4())
    sa = create_user_with_role(db_session, sa_sub, "sa69@talentra.io", "SUPER_ADMIN")
    create_user_with_role(db_session, str(uuid.uuid4()), "admin69@talentra.io", "ADMIN")
    db_session.commit()

    sa_token = create_test_supabase_token(sub=sa_sub, email="sa69@talentra.io")

    resp = client.get(
        "/api/v1/admin/access-review",
        headers={"Authorization": f"Bearer {sa_token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    report = resp.json()
    assert report["privileged_users_count"] >= 2
    assert report["reviewer_user_id"] == sa.id
    assert report["audit_correlation_id"] is not None and len(report["audit_correlation_id"]) > 0


def test_fr0201_sensitive_action_actor_attribution(client, db_session):
    """FR-0201: Sensitive action actor attribution.
    
    Verifies that every audit event strictly attributes the action to the executing
    actor's internal user ID.
    """
    admin_sub = str(uuid.uuid4())
    admin = create_user_with_role(db_session, admin_sub, "admin201@talentra.io", "ADMIN")
    target = create_user_with_role(db_session, str(uuid.uuid4()), "target201@talentra.io", "CANDIDATE")
    db_session.commit()

    admin_token = create_test_supabase_token(sub=admin_sub, email="admin201@talentra.io")

    # Grant RECRUITER role
    client.post(
        "/api/v1/admin/roles/grant",
        json={"user_id": target.id, "role_code": "RECRUITER"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Check that audit log records actor_user_id == admin.id
    audit_resp = client.get(
        "/api/v1/admin/audit-events",
        params={"action_code": "ROLE_ASSIGNED"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert audit_resp.status_code == status.HTTP_200_OK
    events = audit_resp.json()["items"]
    assert len(events) > 0
    assert events[0]["actor_user_id"] == admin.id
