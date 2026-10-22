"""Licence, Seat Allocation, and Device Model Factory."""

import itertools
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.licence import Licence, LicenceSeatAllocation, RegisteredDevice

_lic_counter = itertools.count(1)


def create_factory_licence(
    db: Session,
    account_id: int,
    max_users: int = 5,
    max_devices_per_user: int = 2,
    licence_code: Optional[str] = None,
) -> Licence:
    """Create a subscription licence."""
    idx = next(_lic_counter)
    now_utc = datetime.now(timezone.utc)
    code = licence_code or f"LIC_FAC_{idx:04d}"

    lic = Licence(
        licence_code=code,
        account_id=account_id,
        max_users=max_users,
        max_devices_per_user=max_devices_per_user,
        valid_from=now_utc - timedelta(days=1),
        valid_until=now_utc + timedelta(days=365),
        status_code_id=1,  # ACTIVE
    )
    db.add(lic)
    db.flush()
    return lic


def allocate_factory_seat(
    db: Session,
    licence_id: int,
    user_id: int,
    allocated_by_user_id: int,
) -> LicenceSeatAllocation:
    """Allocate a licence seat to a user."""
    alloc = LicenceSeatAllocation(
        licence_id=licence_id,
        user_id=user_id,
        status_code_id=1,
        created_by=allocated_by_user_id,
    )
    db.add(alloc)
    db.flush()
    return alloc
