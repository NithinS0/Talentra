"""Application settings using Pydantic Settings."""

import os
from typing import Optional
from urllib.parse import quote_plus
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    """Central configuration for Talentra application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Talentra"
    APP_ENV: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
        description="Application environment (development, staging, production)",
    )
    APP_DEBUG: bool = Field(
        default=False,
        validation_alias=AliasChoices("APP_DEBUG", "DEBUG"),
        description="Enable debug mode and verbose tracebacks",
    )
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # Database Configuration (Supabase PostgreSQL)
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:your_password_here@db.your_project_ref_here.supabase.co:5432/postgres",
        description="PostgreSQL connection string (supports direct or session pooler)",
    )
    MIGRATION_DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Direct connection string for Alembic migrations when DATABASE_URL is a pooler",
    )

    # Engine Connection Pool Settings
    DB_POOL_SIZE: int = Field(default=10, description="Maximum number of persistent connections in the pool")
    DB_MAX_OVERFLOW: int = Field(default=5, description="Maximum number of connections that can be created beyond pool_size")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Seconds to wait before giving up on getting a connection from the pool")
    DB_CONNECT_TIMEOUT: int = Field(default=10, description="PostgreSQL client connection timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=1800, description="Seconds after which a connection is recycled (default 30 min)")
    DB_ECHO: bool = Field(default=False, description="Log all executed SQL queries (do not enable in production)")

    # Supabase Client Settings (Auth & Verification)
    SUPABASE_URL: str = Field(
        default="https://ewexpzauzoqfjdwrzpmg.supabase.co",
        description="Supabase project URL",
    )
    SUPABASE_ANON_KEY: Optional[str] = Field(
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV3ZXhwemF1em9xZmpkd3J6cG1nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIzMDI4NTEsImV4cCI6MjEwNzg3ODg1MX0.YAsnT3r5oc0FtkQDVGAFJithZHMJjWZOJ_L8ef3Xy14",
        description="Supabase anon public key",
    )
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        default=None,
        description="Supabase service role secret key (NEVER expose to frontend or client)",
    )
    SUPABASE_JWT_SECRET: str = Field(
        default="kfm9KFjcdflHMaSePXGxx7KT6h6qFV8hKlI/eVelu5mW3abGFYHhgCXOvfpflkjr/j1xbx8KnqNaxaLSqnv/9Q==",
        description="Supabase project JWT secret for verifying access tokens",
    )
    SUPABASE_JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used by Supabase Auth JWTs",
    )

    @classmethod
    def normalize_postgres_dsn(cls, dsn: str) -> str:
        """Ensure the DSN uses the psycopg (Psycopg 3) driver prefix for SQLAlchemy 2.x."""
        if not dsn:
            return dsn
        dsn_clean = dsn.strip()
        if dsn_clean.startswith("postgres://"):
            return "postgresql+psycopg://" + dsn_clean[len("postgres://") :]
        if dsn_clean.startswith("postgresql://") and not dsn_clean.startswith("postgresql+"):
            return "postgresql+psycopg://" + dsn_clean[len("postgresql://") :]
        return dsn_clean

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the normalized SQLAlchemy database URL with psycopg driver."""
        return self.normalize_postgres_dsn(self.DATABASE_URL)

    @property
    def sqlalchemy_migration_url(self) -> str:
        """Return the URL to be used by Alembic migrations (direct connection preferred)."""
        target = self.MIGRATION_DATABASE_URL or self.DATABASE_URL
        return self.normalize_postgres_dsn(target)

    @property
    def safe_database_url(self) -> str:
        """Return database URL with password masked (safe for logs and diagnostics)."""
        try:
            url = make_url(self.sqlalchemy_database_url)
            return url.render_as_string(hide_password=True)
        except Exception:
            return "postgresql+psycopg://***@***"

    @property
    def is_database_configured(self) -> bool:
        """Check whether real database credentials have been configured rather than placeholders."""
        if not self.DATABASE_URL:
            return False
        placeholders = [
            "your_password_here",
            "your_project_ref_here",
            "db.your_project_ref_here",
            "[YOUR-PASSWORD]",
            "[YOUR-PROJECT-REF]",
            "example.com",
        ]
        return not any(p in self.DATABASE_URL for p in placeholders)

    @property
    def is_production(self) -> bool:
        """Check if environment is set to production."""
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def cors_origins_list(self) -> list[str]:
        """Return list of allowed CORS origin strings."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
