"""Gig Marketplace Model Factory."""

import itertools
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.models.gig import GigWorkerProfile, GigRequest, GigApplication, GigAssignment

_gig_counter = itertools.count(1)


def create_factory_gig_workflow(
    db: Session,
    requester_org_id: int,
    requester_user_id: int,
    worker_user_id: int,
    price_amount: Decimal = Decimal("2500.00"),
    currency_code: str = "USD",
) -> GigAssignment:
    """Creates complete gig workflow: WorkerProfile -> Request -> Application -> Assignment."""
    idx = next(_gig_counter)
    now_utc = datetime.now(timezone.utc)

    # 1. Worker Profile
    worker = GigWorkerProfile(
        user_id=worker_user_id,
        display_name=f"Factory Gig Worker #{idx}",
        availability_status_code_id=1,
    )
    db.add(worker)
    db.flush()

    # 2. Request
    request = GigRequest(
        requester_organisation_id=requester_org_id,
        created_by_user_id=requester_user_id,
        title=f"Factory Gig Project #{idx}",
        description="Delivery sprint for microservice components.",
        starts_at=now_utc + timedelta(days=2),
        ends_at=now_utc + timedelta(days=12),
        pricing_type_code_id=1,  # FIXED
        price_amount=price_amount,
        currency_code=currency_code,
        status_code_id=3,  # IN_PROGRESS
    )
    db.add(request)
    db.flush()

    # 3. Application
    app = GigApplication(
        gig_request_id=request.id,
        gig_worker_profile_id=worker.id,
        status_code_id=2,  # ACCEPTED
        decided_by_user_id=requester_user_id,
    )
    db.add(app)
    db.flush()

    # 4. Assignment
    assignment = GigAssignment(
        gig_application_id=app.id,
        requester_organisation_id=requester_org_id,
        gig_worker_profile_id=worker.id,
        starts_at=now_utc + timedelta(days=2),
        ends_at=now_utc + timedelta(days=12),
        status_code_id=2,  # ACTIVE
    )
    db.add(assignment)
    db.flush()
    return assignment
