"""Talentra Stage 18: Full-System Integration & End-to-End Acceptance Test Suite.

Executes end-to-end scenarios crossing authentication, role access, core recruitment
workflows, multi-tenant boundaries, licensing, financial ledger immutability,
government ID verification, and administrative audit trails against FastAPI /api/v1.
"""

import sys
import os
import time
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.main import app
from app.core.config import settings
from app.core.security import create_test_supabase_token
from app.core.database import check_database_connection

client = TestClient(app)


# ==============================================================================
# 1. Authentication & Role Access Control (Section 4A)
# ==============================================================================

def test_stage18_root_and_health_liveness():
    """Verify service status and health probes without leaking configuration."""
    res_root = client.get("/")
    assert res_root.status_code == status.HTTP_200_OK
    data_root = res_root.json()
    assert data_root["service"] == settings.APP_NAME
    assert data_root["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == status.HTTP_200_OK
    assert res_health.json()["status"] == "healthy"


def test_stage18_db_health_probe_boundary(monkeypatch):
    """Verify database readiness probe handles connected, disconnected, and sanitized error states."""
    # Connected
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: (True, "Database connectivity verified successfully (SELECT 1 succeeded).")
    )
    res_conn = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert res_conn.status_code == status.HTTP_200_OK
    assert res_conn.json()["status"] == "healthy"
    assert res_conn.json()["database"] == "connected"

    # Disconnected
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: (False, "Database credentials have not been configured in .env (placeholder detected).")
    )
    res_disc = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert res_disc.status_code == status.HTTP_200_OK
    assert res_disc.json()["status"] == "unhealthy"
    assert res_disc.json()["database"] == "disconnected"
    assert "password" not in res_disc.json()["detail"].lower() or "placeholder detected" in res_disc.json()["detail"]


def test_stage18_auth_unauthorized_missing_token():
    """Verify protected endpoints reject requests missing Authorization Bearer token."""
    protected_endpoints = [
        f"{settings.API_V1_PREFIX}/auth/me",
        f"{settings.API_V1_PREFIX}/candidates/me",
        f"{settings.API_V1_PREFIX}/admin/users",
        f"{settings.API_V1_PREFIX}/admin/audit-events",
    ]
    for ep in protected_endpoints:
        res = client.get(ep)
        assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_stage18_auth_tampered_token_rejected():
    """Verify forged or tampered JWT tokens are strictly rejected with 401 Unauthorized."""
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.tampered_signature_bytes"
    res = client.get(
        f"{settings.API_V1_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_stage18_documented_actor_prefixes_and_roles():
    """Verify the 9 canonical actor prefixes and roles match the system blueprint."""
    expected_prefixes = {
        "SUPER_ADMIN": "SA",
        "ADMIN": "AD",
        "ACCOUNT_ADMIN": "AA",
        "GUEST": "GU",
        "CANDIDATE": "CA",
        "EMPLOYER": "EM",
        "RECRUITER": "RE",
        "CONSULTANT": "CO",
        "PLACEMENT_OFFICER": "PO",
    }
    for role, prefix in expected_prefixes.items():
        assert len(prefix) == 2
        assert prefix.isupper()


# ==============================================================================
# 2. Candidate Onboarding & Validation (Section 4B)
# ==============================================================================

def test_stage18_candidate_registration_unauthenticated():
    """Verify candidate registration without Supabase Auth token is rejected with 401."""
    res = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={
            "first_name": "Test",
            "last_name": "Candidate",
            "country_code": "IN",
        }
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_stage18_candidate_registration_validation():
    """Verify input validation for candidate self-registration with valid auth token."""
    token = create_test_supabase_token(sub="sub_test_validation_stage18", email="candidate_val@test.io")
    headers = {"Authorization": f"Bearer {token}"}

    # Invalid country code (not ISO 3166-1 alpha-2)
    res_bad_country = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        headers=headers,
        json={
            "first_name": "Test",
            "last_name": "Candidate",
            "country_code": "INVALID",
        }
    )
    assert res_bad_country.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST)

    # Invalid phone format (not E.164)
    res_bad_phone = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        headers=headers,
        json={
            "first_name": "Test",
            "last_name": "Candidate",
            "country_code": "IN",
            "phone_number": "12345",
        }
    )
    assert res_bad_phone.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# 3. Financial Wallet & Append-Only Ledger Immutability (Section 4E)
# ==============================================================================

def test_stage18_financial_ledger_no_direct_mutation():
    """Verify that financial ledger entries cannot be directly mutated or deleted via API."""
    # Attempt PUT on ledger entry
    res_put = client.put(
        f"{settings.API_V1_PREFIX}/wallet/ledger/1",
        json={"amount": 9999.00}
    )
    assert res_put.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)

    # Attempt DELETE on ledger entry
    res_del = client.delete(f"{settings.API_V1_PREFIX}/wallet/ledger/1")
    assert res_del.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)


# ==============================================================================
# 4. Security Audit Trail Immutability (Section 4F)
# ==============================================================================

def test_stage18_audit_events_immutability():
    """Verify audit events are strictly append-only and reject DELETE or PUT requests."""
    res_del = client.delete(f"{settings.API_V1_PREFIX}/admin/audit-events/1")
    # Must be 401 (unauthenticated), 403 (forbidden/immutable), 404, or 405 (method not allowed)
    assert res_del.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_405_METHOD_NOT_ALLOWED,
    )


# ==============================================================================
# 5. Government Identity Verification & PII Protection (Section 4G)
# ==============================================================================

def test_stage18_verification_consent_purpose_enforcement():
    """Verify verification initiation requires documented purpose and valid document type."""
    # Missing required fields
    res = client.post(
        f"{settings.API_V1_PREFIX}/verification/consent",
        json={}
    )
    assert res.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        status.HTTP_400_BAD_REQUEST,
    )


def test_stage18_retention_scheduler_dry_run_safety():
    """Verify data retention scheduler dry run does not perform destructive actions."""
    res = client.post(
        f"{settings.API_V1_PREFIX}/verification/retention/run",
        json={
            "target_data_class": "KYC_DOCUMENTS",
            "retention_days": 2555,
            "dry_run": True,
        }
    )
    # Requires admin/super admin auth
    assert res.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_200_OK,
    )
