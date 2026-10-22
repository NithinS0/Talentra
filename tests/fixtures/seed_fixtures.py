"""Reusable Pytest Fixtures for Seeded Database States."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from scripts.seed.profiles import (
    run_profile_a,
    run_profile_b,
    run_profile_c,
    run_profile_d,
)


@pytest.fixture(scope="function")
def seed_db():
    """Isolated SQLite in-memory test database with allocate_actor_id UDF."""
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

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def seeded_reference_data(seed_db):
    """Database fixture pre-seeded with Profile A Reference Data."""
    run_profile_a(seed_db)
    return seed_db


@pytest.fixture(scope="function")
def seeded_system_config(seeded_reference_data):
    """Database fixture pre-seeded with Profile B System Configuration."""
    run_profile_b(seeded_reference_data)
    return seeded_reference_data


@pytest.fixture(scope="function")
def seeded_demo_ecosystem(seeded_system_config):
    """Database fixture pre-seeded with Profile C Minimal Development Demo."""
    run_profile_c(seeded_system_config)
    return seeded_system_config


@pytest.fixture(scope="function")
def seeded_functional_test_data(seeded_demo_ecosystem):
    """Database fixture pre-seeded with Profile D Comprehensive Functional Test Data."""
    run_profile_d(seeded_demo_ecosystem)
    return seeded_demo_ecosystem
