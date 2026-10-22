"""Database engine and session management for SQLAlchemy 2.x and Psycopg 3."""

import logging
from typing import Generator, Tuple, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import QueuePool, NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


# Engine Configuration
# When using Supabase transaction pooler (port 6543), NullPool avoids client-side connection hoarding.
# For direct (port 5432) or session pooler connections, QueuePool with pre-ping is recommended.
engine_kwargs = {
    "echo": settings.DB_ECHO,
    "pool_pre_ping": True,
    "connect_args": {
        "connect_timeout": settings.DB_CONNECT_TIMEOUT,
    },
}

if "pooler.supabase.com:6543" in settings.sqlalchemy_database_url:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    })

engine = create_engine(
    settings.sqlalchemy_database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI request-scoped dependency for database sessions.
    
    Yields:
        Session: Active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> Tuple[bool, str]:
    """Perform a safe database connectivity verification without leaking credentials.
    
    Returns:
        Tuple[bool, str]: (is_connected, safe_message)
    """
    if not settings.is_database_configured:
        return False, "Database credentials have not been configured in .env (placeholder detected)."

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;")).scalar()
            if result == 1:
                return True, "Database connectivity verified successfully (SELECT 1 succeeded)."
            return False, "Unexpected query response from database."
    except Exception as e:
        # Sanitize exception message to ensure no connection URLs or passwords leak
        err_str = str(e)
        if "@" in err_str:
            sanitized = err_str.split("@")[-1]
        else:
            sanitized = err_str[:120]
        logger.error("Database connection attempt failed: %s", sanitized)
        return False, f"Connection failed: {sanitized}"
