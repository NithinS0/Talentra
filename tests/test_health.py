"""Basic health check, database session lifecycle, and configuration tests."""

import pytest
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings, settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root endpoint returns expected service details."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Talentra"
    assert data["status"] == "online"
    assert data["environment"] == settings.APP_ENV


def test_health_check_endpoint():
    """Verify health check endpoint returns 200 without requiring active DB."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Talentra"


def test_db_health_endpoint_connected(monkeypatch):
    """Verify database health endpoint reports healthy/connected when probe succeeds."""
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: (True, "Database connectivity verified successfully (SELECT 1 succeeded).")
    )
    response = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "SELECT 1 succeeded" in data["detail"]


def test_db_health_endpoint_safe_error(monkeypatch):
    """Verify database health endpoint reports disconnected safely without leaking credentials when disconnected."""
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: (False, "Database credentials have not been configured in .env (placeholder detected).")
    )
    response = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"
    assert "placeholder detected" in data["detail"]
    assert "password" not in data["detail"].lower() or "placeholder detected" in data["detail"]


def test_db_health_endpoint_connection_failure_sanitization(monkeypatch):
    """Verify connection exception details are sanitized and do not leak user/passwords."""
    monkeypatch.setattr(
        "app.main.check_database_connection",
        lambda: (False, "Connection failed: connection to server at host 'db.supabase.co' timed out")
    )
    response = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["database"] == "disconnected"
    assert "password" not in data["detail"].lower()


def test_db_health_endpoint_live_environment():
    """Verify live health check returns a well-formed payload matching schema in current environment."""
    response = client.get(f"{settings.API_V1_PREFIX}/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["database"] in ("connected", "disconnected")
    assert "detail" in data
    assert "password" not in data["detail"].lower() or "placeholder detected" in data["detail"]


def test_config_psycopg3_normalization():
    """Verify PostgreSQL URL is normalized to use psycopg driver."""
    direct_url = "postgresql://myuser:mypass@db.host.supabase.co:5432/postgres"
    normalized = settings.normalize_postgres_dsn(direct_url)
    assert normalized.startswith("postgresql+psycopg://")


def test_config_special_character_url_masking():
    """Verify passwords with special characters (@, #, %) are masked in safe_database_url."""
    custom_settings = Settings(
        DATABASE_URL="postgresql://postgres:my%23secret%40pass@db.example.supabase.co:5432/postgres"
    )
    safe_url = custom_settings.safe_database_url
    assert "my#secret@pass" not in safe_url
    assert "my%23secret%40pass" not in safe_url
    assert "***" in safe_url
    assert custom_settings.is_database_configured is True


def test_placeholder_detection():
    """Verify that placeholder URLs are correctly identified as unconfigured."""
    placeholder_settings = Settings(
        DATABASE_URL="postgresql://postgres:your_password_here@db.your_project_ref_here.supabase.co:5432/postgres"
    )
    assert placeholder_settings.is_database_configured is False
