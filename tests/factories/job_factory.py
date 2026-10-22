"""Job Requirements and Positions Factories."""

import itertools
from decimal import Decimal
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.job import JobRole, EmploymentType, WorkType, JobRequirement, JobPosition

_job_counter = itertools.count(1)


def create_factory_job(
    db: Session,
    organisation_id: int,
    created_by_user_id: int,
    title: Optional[str] = None,
    positions_count: int = 1,
    status_code_id: int = 2,  # OPEN
) -> JobRequirement:
    """Create a synthetic job requirement and linked position."""
    idx = next(_job_counter)
    job_title = title or f"Factory Job Requisition #{idx}"

    emp_t = db.execute(select(EmploymentType)).scalars().first()
    work_t = db.execute(select(WorkType)).scalars().first()
    role_j = db.execute(select(JobRole)).scalars().first()

    emp_id = emp_t.id if emp_t else 1
    work_id = work_t.id if work_t else 1
    role_id = role_j.id if role_j else 1

    job = JobRequirement(
        organisation_id=organisation_id,
        created_by_user_id=created_by_user_id,
        job_role_id=role_id,
        title=job_title[:180],
        description="Factory requisition specification description.",
        employment_type_id=emp_id,
        work_type_id=work_id,
        status_code_id=status_code_id,
        publish_state_code_id=2,  # PUBLISHED
        positions_count=positions_count,
        salary_min=Decimal("1200000.00"),
        salary_max=Decimal("1800000.00"),
        salary_currency_code="INR",
    )
    db.add(job)
    db.flush()

    db.add(JobPosition(
        job_requirement_id=job.id,
        position_code=f"POS_FAC_{idx:04d}",
        title=job.title,
        headcount=1,
        filled_count=0,
    ))
    db.flush()
    return job
