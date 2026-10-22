"""Candidate Model Factories."""

import itertools
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.candidate import CandidateProfile, CandidateContact
from tests.factories.user_factory import create_factory_user, assign_factory_role_and_actor_id

_cand_counter = itertools.count(1)


def create_factory_candidate(
    db: Session,
    user: Optional[User] = None,
    first_name: str = "Candidate",
    last_name: str = "Test",
    status_code_id: int = 1,
) -> CandidateProfile:
    """Create a candidate user, profile, contact, and CA actor ID."""
    idx = next(_cand_counter)
    if not user:
        user = create_factory_user(db, email=f"candidate.factory.{idx}@talentra.io", display_name=f"{first_name} {last_name}")

    actor_id = assign_factory_role_and_actor_id(db, user, role_code="CANDIDATE", prefix="CA")

    profile = CandidateProfile(
        user_id=user.id,
        actor_id=actor_id,
        first_name=first_name,
        last_name=f"{last_name}_{idx}",
        summary="Factory candidate profile summary.",
        profile_status_code_id=status_code_id,
        profile_visibility_code_id=1,
    )
    db.add(profile)
    db.flush()

    db.add(CandidateContact(
        candidate_profile_id=profile.id,
        email_address=user.email_address,
        phone_e164="+919876543210",
        phone_country_id=1,
    ))
    db.flush()
    return profile
