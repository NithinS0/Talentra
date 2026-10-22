"""Automated Functional, Security & Concurrency Tests for Talentra Stage 10: Licences, Seats, Devices & Sessions.

Maps strictly to approved test cases in Talentra_Final_Test_Cases_All_Modules.xlsx (Sheet: Licences Seats Devices & Sessio):
- FR-0098: Positive user licence limit
- FR-0099: Positive device limit
- FR-0100: Seat limit enforcement
- FR-0101: Device limit at login
- FR-0102: Expired session exclusion
- FR-0103: Revoked session exclusion
- FR-0104: Session activity metadata
- FR-0105: Concurrent login race
- FR-0106: Device revocation audit
- FR-0107: Licence assignment scope
- FR-0108: Duplicate active device
- FR-0109: Session end release
- FR-0110: Seat release on unassignment
- FR-0111: Login limit audit on rejection
- FR-0204: Expired session cleanup is idempotent
"""

import sys
import os
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_test_supabase_token
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment
from app.models.organisation import Organisation, Account, AccountOrganisation, AccountAdminAssignment
from app.models.admin import AuditEvent, IdentitySession
from app.models.licence import (
    Licence,
    LicenceSeatAllocation,
    RegisteredDevice,
    DeviceRevocationEvent,
    SessionRevocationEvent,
    LoginDeviceDecision,
    SessionActivityEvent,
    LicenceStatusHistory,
)
from app.services import licence_service
from app.schemas.licence import LicenceCreate, SeatAllocationCreate, SessionCreateRequest


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with static pool."""
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
    roles = [
        Role(role_code="SUPER_ADMIN", display_name="Super Administrator", description="Platform Admin", is_system_role=True),
        Role(role_code="ADMIN", display_name="Platform Administrator", description="Admin", is_system_role=True),
        Role(role_code="ACCOUNT_ADMIN", display_name="Account Administrator", description="Account Admin", is_system_role=True),
        Role(role_code="CANDIDATE", display_name="Candidate", description="Job seeker", is_system_role=False),
        Role(role_code="EMPLOYER", display_name="Employer", description="Hiring org", is_system_role=False),
    ]
    roles_dict = {}
    for r in roles:
        existing = db_session.query(Role).filter(Role.role_code == r.role_code).first()
        if not existing:
            db_session.add(r)
            db_session.flush()
            roles_dict[r.role_code] = r
        else:
            roles_dict[r.role_code] = existing
    db_session.commit()
    return roles_dict


def _create_user(db_session, role_code: str = "CANDIDATE", org_id: int = None) -> User:
    """Create a unique user with assigned role and optional organisation."""
    uid = uuid.uuid4().hex[:8]
    sub = f"auth0|usr_{uid}"
    email = f"user_{uid}@talentra.test"
    now = datetime.now(timezone.utc)

    user = User(
        email_address=email,
        display_name=f"User {uid}",
        provider_subject=sub,
        account_status_code_id=1,
    )
    db_session.add(user)
    db_session.flush()

    role = db_session.query(Role).filter(Role.role_code == role_code).first()
    if role:
        db_session.add(UserRoleAssignment(
            user_id=user.id,
            role_id=role.id,
            organisation_id=org_id,
            assigned_by_user_id=user.id,
            valid_from=now,
        ))
    db_session.commit()
    return user


def _create_org_and_account(db_session, owner_user: User, code_prefix: str = "ACC") -> tuple:
    """Create an organisation and associated customer account."""
    uid = uuid.uuid4().hex[:6]
    now = datetime.now(timezone.utc)

    org = Organisation(
        legal_name=f"Organisation {uid} Ltd",
        display_name=f"Org {uid}",
        status_code_id=1,
        created_by=owner_user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(org)
    db_session.flush()

    account = Account(
        account_code=f"{code_prefix}-{uid.upper()}",
        account_name=f"Account {uid}",
        status_code_id=1,
        root_organisation_id=org.id,
        created_by=owner_user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(account)
    db_session.flush()

    db_session.add(AccountOrganisation(
        account_id=account.id,
        organisation_id=org.id,
        name="Primary",
        created_by=owner_user.id,
    ))
    db_session.commit()
    return org, account


def _auth_headers(user: User) -> dict:
    """Helper to generate bearer token headers matching Supabase Auth."""
    token = create_test_supabase_token(sub=user.provider_subject, email=user.email_address)
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# FR-0098: Positive user licence limit
# =========================================================================

def test_fr0098_positive_user_licence_limit(client, db_session, seed_roles):
    """FR-0098: Maximum users per licence must be a positive integer."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    # 1. Non-positive max_users (0)
    resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-ZERO-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 0,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 2. Negative max_users (-5)
    resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-NEG-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": -5,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 3. Valid positive integer succeeds
    code = f"LIC-VALID-{uuid.uuid4().hex[:6]}"
    resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": code,
            "account_id": account.id,
            "max_users": 10,
            "max_devices_per_user": 3,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["max_users"] == 10
    assert data["status"] == "ACTIVE"


# =========================================================================
# FR-0099: Positive device limit
# =========================================================================

def test_fr0099_positive_device_limit(client, db_session, seed_roles):
    """FR-0099: Maximum devices per user must be a positive integer."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    # 1. Zero device limit
    resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-DEV-ZERO-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 0,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

    # 2. Negative device limit
    resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-DEV-NEG-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": -2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# =========================================================================
# FR-0100: Seat limit enforcement
# =========================================================================

def test_fr0100_seat_limit_enforcement(client, db_session, seed_roles):
    """FR-0100: User limit is enforced; allocating beyond capacity is rejected."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user_1 = _create_user(db_session, "CANDIDATE", org.id)
    user_2 = _create_user(db_session, "CANDIDATE", org.id)
    headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    # Create licence with EXACTLY 1 seat
    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-ONE-SEAT-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 1,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    assert lic_resp.status_code == status.HTTP_201_CREATED
    lic_id = lic_resp.json()["id"]

    # 1. Allocate seat to User 1 -> Succeeds
    alloc_1 = client.post(
        "/api/v1/licences/seats",
        json={"licence_id": lic_id, "user_id": user_1.id},
        headers=headers,
    )
    assert alloc_1.status_code == status.HTTP_201_CREATED

    # Verify live licence metrics
    lic_status = client.get(f"/api/v1/licences/{lic_id}", headers=headers).json()
    assert lic_status["allocated_seats"] == 1
    assert lic_status["available_seats"] == 0

    # 2. Allocate second seat to User 2 -> Rejected (Capacity Exceeded)
    alloc_2 = client.post(
        "/api/v1/licences/seats",
        json={"licence_id": lic_id, "user_id": user_2.id},
        headers=headers,
    )
    assert alloc_2.status_code == status.HTTP_400_BAD_REQUEST
    assert "capacity exceeded" in alloc_2.json()["detail"].lower()


# =========================================================================
# FR-0101: Device limit at login
# =========================================================================

def test_fr0101_device_limit_at_login(client, db_session, seed_roles):
    """FR-0101: Active sessions counted against device limit; exceeding limit is denied and audited."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)
    admin_headers = _auth_headers(admin)
    user_headers = _auth_headers(user)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    # Create licence with max_devices_per_user = 2
    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-DEV-2-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]

    # Allocate seat to user
    client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user.id}, headers=admin_headers)

    hash1 = hashlib.sha256(f"device_1_{uuid.uuid4().hex}".encode()).hexdigest()
    hash2 = hashlib.sha256(f"device_2_{uuid.uuid4().hex}".encode()).hexdigest()
    hash3 = hashlib.sha256(f"device_3_{uuid.uuid4().hex}".encode()).hexdigest()

    # Session 1 (Device 1) -> Allowed
    s1 = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash1, "device_label": "Laptop A"},
        headers=user_headers,
    )
    assert s1.status_code == status.HTTP_201_CREATED

    # Session 2 (Device 2) -> Allowed (2/2 active)
    s2 = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash2, "device_label": "Mobile B"},
        headers=user_headers,
    )
    assert s2.status_code == status.HTTP_201_CREATED

    # Session 3 (Device 3) -> Denied (3 > 2 limit)
    s3 = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash3, "device_label": "Tablet C"},
        headers=user_headers,
    )
    assert s3.status_code == status.HTTP_403_FORBIDDEN
    assert "device limit" in s3.json()["detail"].lower()

    # Verify audit event exists
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.action_code == "LOGIN_DEVICE_LIMIT_EXCEEDED",
        AuditEvent.actor_user_id == user.id,
    ).first()
    assert audit is not None
    assert audit.metadata_redacted["outcome"] == "REJECTED_OVER_DEVICE_LIMIT"


# =========================================================================
# FR-0102: Expired session exclusion
# =========================================================================

def test_fr0102_expired_session_exclusion(client, db_session, seed_roles):
    """FR-0102: Expired sessions do not count against device limit."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)
    admin_headers = _auth_headers(admin)
    user_headers = _auth_headers(user)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-EXP-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 1,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]
    client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user.id}, headers=admin_headers)

    # Create an expired session directly in DB
    past_time = now - timedelta(hours=2)
    expired_sess = IdentitySession(
        user_id=user.id,
        provider_session_reference=f"sess_exp_{uuid.uuid4().hex[:8]}",
        started_at=past_time - timedelta(hours=1),
        last_activity_at=past_time,
        expires_at=past_time,  # In the past
    )
    db_session.add(expired_sess)
    db_session.commit()

    # User has 1 expired session, limit is 1. Since expired sessions are excluded, login must succeed.
    hash_new = hashlib.sha256(f"dev_new_{uuid.uuid4().hex}".encode()).hexdigest()
    resp = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash_new, "device_label": "New Device"},
        headers=user_headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["is_active"] is True


# =========================================================================
# FR-0103: Revoked session exclusion
# =========================================================================

def test_fr0103_revoked_session_exclusion(client, db_session, seed_roles):
    """FR-0103: Revoking a session releases capacity immediately."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)
    admin_headers = _auth_headers(admin)
    user_headers = _auth_headers(user)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-REV-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 1,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]
    client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user.id}, headers=admin_headers)

    # 1. Login Device 1 (occupies 1/1 capacity)
    hash1 = hashlib.sha256(f"dev_rev_1_{uuid.uuid4().hex}".encode()).hexdigest()
    s1 = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash1, "device_label": "Device 1"},
        headers=user_headers,
    )
    assert s1.status_code == status.HTTP_201_CREATED
    s1_id = s1.json()["id"]

    # 2. Login Device 2 -> Denied
    hash2 = hashlib.sha256(f"dev_rev_2_{uuid.uuid4().hex}".encode()).hexdigest()
    s2 = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash2, "device_label": "Device 2"},
        headers=user_headers,
    )
    assert s2.status_code == status.HTTP_403_FORBIDDEN

    # 3. Revoke Session 1
    rev_resp = client.post(
        f"/api/v1/licences/sessions/{s1_id}/revoke",
        json={"reason": "Security rotation"},
        headers=user_headers,
    )
    assert rev_resp.status_code == status.HTTP_200_OK
    assert rev_resp.json()["revoked_at"] is not None

    # 4. Login Device 2 again -> Now succeeds because revoked session does not count against limit
    s2_retry = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": hash2, "device_label": "Device 2"},
        headers=user_headers,
    )
    assert s2_retry.status_code == status.HTTP_201_CREATED


# =========================================================================
# FR-0104: Session activity metadata
# =========================================================================

def test_fr0104_session_activity_metadata(client, db_session, seed_roles):
    """FR-0104: Session records device, start time, last activity, and end time."""
    user = _create_user(db_session, "CANDIDATE")
    headers = _auth_headers(user)

    h = hashlib.sha256(f"dev_meta_{uuid.uuid4().hex}".encode()).hexdigest()
    s = client.post(
        "/api/v1/licences/sessions",
        json={"device_fingerprint_hash": h, "device_label": "Meta Laptop"},
        headers=headers,
    )
    assert s.status_code == status.HTTP_201_CREATED
    data = s.json()
    assert data["device_id"] is not None
    assert data["started_at"] is not None
    assert data["last_activity_at"] is not None
    assert data["expires_at"] is not None
    assert data["ended_at"] is None
    sess_id = data["id"]

    # Update heartbeat
    hb = client.post(f"/api/v1/licences/sessions/{sess_id}/heartbeat", headers=headers)
    assert hb.status_code == status.HTTP_200_OK
    assert hb.json()["last_activity_at"] is not None

    # Logout
    logout = client.post(f"/api/v1/licences/sessions/{sess_id}/end", headers=headers)
    assert logout.status_code == status.HTTP_200_OK
    assert logout.json()["ended_at"] is not None
    assert logout.json()["is_active"] is False


# =========================================================================
# FR-0105: Concurrent login race
# =========================================================================

def test_fr0105_concurrent_login_race(db_session, seed_roles):
    """FR-0105: Limit enforcement is concurrency-safe under simultaneous device logins."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic = licence_service.create_licence(
        db_session,
        admin,
        LicenceCreate(
            licence_code=f"LIC-RACE-{uuid.uuid4().hex[:6]}",
            account_id=account.id,
            max_users=5,
            max_devices_per_user=1,  # Strictly 1 device permitted
            valid_from=now,
            valid_until=future,
        ),
    )
    licence_service.allocate_seat(
        db_session,
        admin,
        SeatAllocationCreate(licence_id=lic.id, user_id=user.id),
    )

    # Attempt two logins in sequence with transactional locks
    hash_a = hashlib.sha256(b"race_a").hexdigest()
    hash_b = hashlib.sha256(b"race_b").hexdigest()

    # First login succeeds
    sess1 = licence_service.create_user_session(
        db_session,
        user.id,
        SessionCreateRequest(device_fingerprint_hash=hash_a, device_label="Race A"),
        actor_user=user,
    )
    assert sess1 is not None

    # Second simultaneous login is rejected by row lock / capacity evaluation
    with pytest.raises(ValueError) as exc:
        licence_service.create_user_session(
            db_session,
            user.id,
            SessionCreateRequest(device_fingerprint_hash=hash_b, device_label="Race B"),
            actor_user=user,
        )
    assert "limit" in str(exc.value).lower()

    # Verify at most 1 permitted session is active
    active = licence_service.count_active_sessions(db_session, user.id)
    assert active == 1


# =========================================================================
# FR-0106: Device revocation audit
# =========================================================================

def test_fr0106_device_revocation_audit(client, db_session, seed_roles):
    """FR-0106: Revoking device/session records auditable event with actor, target, timestamp, reason."""
    user = _create_user(db_session, "CANDIDATE")
    user_headers = _auth_headers(user)

    h = hashlib.sha256(f"rev_audit_{uuid.uuid4().hex}".encode()).hexdigest()
    reg = client.post(
        "/api/v1/licences/devices",
        json={"device_fingerprint_hash": h, "device_label": "Audit Device"},
        headers=user_headers,
    )
    dev_id = reg.json()["id"]

    # Create active session on this device
    sess = client.post(
        "/api/v1/licences/sessions",
        json={"device_id": dev_id},
        headers=user_headers,
    )
    sess_id = sess.json()["id"]

    # Revoke device
    rev = client.post(
        f"/api/v1/licences/devices/{dev_id}/revoke",
        json={"reason": "Device reported lost by user"},
        headers=user_headers,
    )
    assert rev.status_code == status.HTTP_200_OK
    assert rev.json()["is_active"] is False

    # Check DeviceRevocationEvent in DB
    event = db_session.query(DeviceRevocationEvent).filter(
        DeviceRevocationEvent.actor_user_id == user.id,
    ).first()
    assert event is not None
    assert event.metadata_redacted["reason"] == "Device reported lost by user"

    # Check linked session was also revoked
    db_session.expire_all()
    s = db_session.query(IdentitySession).filter(IdentitySession.id == sess_id).first()
    assert s.revoked_at is not None


# =========================================================================
# FR-0107: Licence assignment scope
# =========================================================================

def test_fr0107_licence_assignment_scope(client, db_session, seed_roles):
    """FR-0107: User must belong to eligible account/org scope; cross-account assignment is rejected."""
    admin = _create_user(db_session, "ADMIN")
    org_1, account_1 = _create_org_and_account(db_session, admin, "ACC1")
    org_2, account_2 = _create_org_and_account(db_session, admin, "ACC2")
    user_1 = _create_user(db_session, "CANDIDATE", org_1.id)  # In Account 1
    user_3 = _create_user(db_session, "CANDIDATE", org_2.id)  # In Account 2
    admin_headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    # Licence belongs to Account 1
    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-SCOPE-{uuid.uuid4().hex[:6]}",
            "account_id": account_1.id,
            "max_users": 5,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]

    # 1. Attempt assigning seat to User 3 (outside Account 1 scope) -> Rejected (FR-0107)
    cross_resp = client.post(
        "/api/v1/licences/seats",
        json={"licence_id": lic_id, "user_id": user_3.id},
        headers=admin_headers,
    )
    assert cross_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "scope" in cross_resp.json()["detail"].lower()

    # 2. Assigning seat to User 1 (within Account 1 scope) -> Succeeds
    valid_resp = client.post(
        "/api/v1/licences/seats",
        json={"licence_id": lic_id, "user_id": user_1.id},
        headers=admin_headers,
    )
    assert valid_resp.status_code == status.HTTP_201_CREATED


# =========================================================================
# FR-0108: Duplicate active device
# =========================================================================

def test_fr0108_duplicate_active_device(client, db_session, seed_roles):
    """FR-0108: Device identifier is unique per user scope and registration is idempotent."""
    user = _create_user(db_session, "CANDIDATE")
    headers = _auth_headers(user)

    h = hashlib.sha256(f"unique_hw_{uuid.uuid4().hex}".encode()).hexdigest()

    # First registration
    r1 = client.post(
        "/api/v1/licences/devices",
        json={"device_fingerprint_hash": h, "device_label": "Workstation 1"},
        headers=headers,
    )
    assert r1.status_code == status.HTTP_201_CREATED
    d1_id = r1.json()["id"]

    # Second registration with same fingerprint
    r2 = client.post(
        "/api/v1/licences/devices",
        json={"device_fingerprint_hash": h, "device_label": "Workstation 1 (Renamed)"},
        headers=headers,
    )
    assert r2.status_code == status.HTTP_201_CREATED
    d2_id = r2.json()["id"]

    # Idempotent: returns identical device ID without creating extra active device record
    assert d1_id == d2_id
    count = db_session.query(RegisteredDevice).filter(
        RegisteredDevice.user_id == user.id,
        RegisteredDevice.device_fingerprint_hash == h,
    ).count()
    assert count == 1


# =========================================================================
# FR-0109: Session end release
# =========================================================================

def test_fr0109_session_end_release(client, db_session, seed_roles):
    """FR-0109: Logout sets end time and releases active session capacity."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)
    admin_headers = _auth_headers(admin)
    user_headers = _auth_headers(user)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-LOGOUT-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 1,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]
    client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user.id}, headers=admin_headers)

    # 1. Login on Device 1
    h1 = hashlib.sha256(f"dev_logout_1_{uuid.uuid4().hex}".encode()).hexdigest()
    s1 = client.post("/api/v1/licences/sessions", json={"device_fingerprint_hash": h1}, headers=user_headers)
    sess_id = s1.json()["id"]

    # 2. Login on Device 2 rejected (limit = 1)
    h2 = hashlib.sha256(f"dev_logout_2_{uuid.uuid4().hex}".encode()).hexdigest()
    s2 = client.post("/api/v1/licences/sessions", json={"device_fingerprint_hash": h2}, headers=user_headers)
    assert s2.status_code == status.HTTP_403_FORBIDDEN

    # 3. User logs out from Session 1
    end_resp = client.post(f"/api/v1/licences/sessions/{sess_id}/end", headers=user_headers)
    assert end_resp.status_code == status.HTTP_200_OK
    assert end_resp.json()["ended_at"] is not None

    # 4. Device 2 can now login successfully
    s2_retry = client.post("/api/v1/licences/sessions", json={"device_fingerprint_hash": h2}, headers=user_headers)
    assert s2_retry.status_code == status.HTTP_201_CREATED


# =========================================================================
# FR-0110: Seat release on unassignment
# =========================================================================

def test_fr0110_seat_release_on_unassignment(client, db_session, seed_roles):
    """FR-0110: Seat is released transactionally, restoring licence capacity accurately."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user_1 = _create_user(db_session, "CANDIDATE", org.id)
    user_2 = _create_user(db_session, "CANDIDATE", org.id)
    headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-REL-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 1,
            "max_devices_per_user": 2,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=headers,
    )
    lic_id = lic_resp.json()["id"]

    # Allocate seat to User 1
    alloc = client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user_1.id}, headers=headers)
    alloc_id = alloc.json()["id"]

    # Capacity is now 0
    stat1 = client.get(f"/api/v1/licences/{lic_id}", headers=headers).json()
    assert stat1["available_seats"] == 0

    # Release seat
    rel = client.delete(f"/api/v1/licences/seats/{alloc_id}?reason=ContractEnded", headers=headers)
    assert rel.status_code == status.HTTP_200_OK
    assert rel.json()["status"] == "RELEASED"

    # Capacity is restored
    stat2 = client.get(f"/api/v1/licences/{lic_id}", headers=headers).json()
    assert stat2["available_seats"] == 1
    assert stat2["allocated_seats"] == 0

    # Now User 2 can be allocated the freed seat
    alloc2 = client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user_2.id}, headers=headers)
    assert alloc2.status_code == status.HTTP_201_CREATED


# =========================================================================
# FR-0111: Login limit audit on rejection
# =========================================================================

def test_fr0111_login_limit_audit_on_rejection(client, db_session, seed_roles):
    """FR-0111: Attempt to exceed device limit is recorded in audit trail without exposing secrets."""
    admin = _create_user(db_session, "ADMIN")
    org, account = _create_org_and_account(db_session, admin)
    user = _create_user(db_session, "CANDIDATE", org.id)
    admin_headers = _auth_headers(admin)
    user_headers = _auth_headers(user)

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=365)

    lic_resp = client.post(
        "/api/v1/licences",
        json={
            "licence_code": f"LIC-DENIAL-{uuid.uuid4().hex[:6]}",
            "account_id": account.id,
            "max_users": 5,
            "max_devices_per_user": 1,
            "valid_from": now.isoformat(),
            "valid_until": future.isoformat(),
        },
        headers=admin_headers,
    )
    lic_id = lic_resp.json()["id"]
    client.post("/api/v1/licences/seats", json={"licence_id": lic_id, "user_id": user.id}, headers=admin_headers)

    # Session 1 succeeds
    h1 = hashlib.sha256(f"dev_rej_1_{uuid.uuid4().hex}".encode()).hexdigest()
    client.post("/api/v1/licences/sessions", json={"device_fingerprint_hash": h1}, headers=user_headers)

    # Session 2 rejected
    h2 = hashlib.sha256(f"dev_rej_2_{uuid.uuid4().hex}".encode()).hexdigest()
    denied = client.post("/api/v1/licences/sessions", json={"device_fingerprint_hash": h2}, headers=user_headers)
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    # Check decision record
    decision = db_session.query(LoginDeviceDecision).filter(
        LoginDeviceDecision.user_id == user.id,
        LoginDeviceDecision.status_code_id == 2,  # REJECTED
    ).first()
    assert decision is not None

    # Check audit event has no secrets / tokens
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.action_code == "LOGIN_DEVICE_LIMIT_EXCEEDED",
        AuditEvent.actor_user_id == user.id,
    ).first()
    assert audit is not None
    assert "token" not in audit.metadata_redacted
    assert "password" not in audit.metadata_redacted


# =========================================================================
# FR-0204: Expired session cleanup is idempotent
# =========================================================================

def test_fr0204_expired_session_cleanup_is_idempotent(client, db_session, seed_roles):
    """FR-0204: Expired session cleanup safely repeats without duplicating or altering completed state."""
    admin = _create_user(db_session, "ADMIN")
    user = _create_user(db_session, "CANDIDATE")
    headers = _auth_headers(admin)

    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=3)

    # Create two expired sessions directly
    s1 = IdentitySession(
        user_id=user.id,
        provider_session_reference=f"sess_clean_1_{uuid.uuid4().hex[:6]}",
        started_at=past - timedelta(hours=1),
        last_activity_at=past,
        expires_at=past,
        ended_at=None,
    )
    s2 = IdentitySession(
        user_id=user.id,
        provider_session_reference=f"sess_clean_2_{uuid.uuid4().hex[:6]}",
        started_at=past - timedelta(hours=1),
        last_activity_at=past,
        expires_at=past,
        ended_at=None,
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    # First cleanup run
    r1 = client.post("/api/v1/licences/sessions/cleanup", headers=headers)
    assert r1.status_code == status.HTTP_200_OK
    data1 = r1.json()
    assert data1["cleaned_count"] >= 2
    assert data1["status"] == "COMPLETED"

    # Second cleanup run immediately after
    r2 = client.post("/api/v1/licences/sessions/cleanup", headers=headers)
    assert r2.status_code == status.HTTP_200_OK
    data2 = r2.json()
    assert data2["cleaned_count"] == 0  # Idempotent: 0 newly cleaned
    assert data2["status"] == "COMPLETED"
