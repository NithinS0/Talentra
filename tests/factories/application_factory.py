"""Job Application Model Factory."""

import itertools
from typing import Optional
from sqlalchemy.orm import Session
from app.models.application import JobApplication, ApplicationStatusHistory

_app_counter = itertools.count(1)


def create_factory_application(
    db: Session,
    job_requirement_id: int,
    candidate_profile_id: int,
    status_code_id: int = 1,  # APPLIED
    changed_by_user_id: Optional[int] = None,
) -> JobApplication:
    """Create a synthetic application and status history entry."""
    idx = next(_app_counter)
    app = JobApplication(
        job_requirement_id=job_requirement_id,
        candidate_profile_id=candidate_profile_id,
        status_code_id=status_code_id,
        cover_letter=f"Factory application submission #{idx}.",
    )
    db.add(app)
    db.flush()

    if changed_by_user_id:
        db.add(ApplicationStatusHistory(
            job_application_id=app.id,
            from_status_code_id=None,
            to_status_code_id=status_code_id,
            changed_by_user_id=changed_by_user_id,
        ))
        db.flush()

    return app
