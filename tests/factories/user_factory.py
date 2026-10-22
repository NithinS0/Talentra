"""User and Identity Model Factories."""

import itertools
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity

_user_counter = itertools.count(1)


def create_factory_user(
    db: Session,
    email: Optional[str] = None,
    display_name: str = "Factory User",
    provider_subject: Optional[str] = None,
    status_code_id: int = 1,
) -> User:
    """Create a synthetic test user account."""
    idx = next(_user_counter)
    email_addr = email or f"factory.user.{idx}@talentra.io"
    sub = provider_subject or f"sub-factory-user-{idx}"

    user = User(
        email_address=email_addr,
        display_name=display_name,
        account_status_code_id=status_code_id,
        identity_provider_code="SUPABASE",
        provider_subject=sub,
    )
    db.add(user)
    db.flush()
    return user


def assign_factory_role_and_actor_id(
    db: Session,
    user: User,
    role_code: str,
    prefix: str,
    organisation_id: Optional[int] = None,
) -> str:
    """Assign role and allocate a valid PPNNNNN actor ID."""
    from sqlalchemy import select
    from app.services.actor_id_service import allocate_actor_id

    role = db.execute(select(Role).where(Role.role_code == role_code)).scalar_one_or_none()
    if not role:
        role = Role(
            role_code=role_code,
            display_name=role_code.title(),
            description=f"Factory role {role_code}",
            is_system_role=True,
        )
        db.add(role)
        db.flush()

    actor_id = allocate_actor_id(db, prefix)

    db.add(UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        organisation_id=organisation_id,
        actor_id=actor_id,
        assigned_by_user_id=1,
    ))

    db.add(UserActorIdentity(
        user_id=user.id,
        role_id=role.id,
        role_code=role_code,
        actor_prefix=prefix,
        actor_id=actor_id,
        organisation_id=organisation_id,
        is_active=True,
    ))
    db.flush()
    return actor_id
