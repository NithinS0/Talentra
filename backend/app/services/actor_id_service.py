"""Talentra Actor ID Allocation Service.

Implements database-backed, concurrency-safe, formatted public identifiers
for all 9 Talentra actor types in format PPNNNNN (2-letter prefix + 5-digit zero-padded number).
"""

import re
from enum import Enum
from typing import Optional, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session


class ActorType(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    ACCOUNT_ADMIN = "ACCOUNT_ADMIN"
    GUEST = "GUEST"
    CANDIDATE = "CANDIDATE"
    EMPLOYER = "EMPLOYER"
    RECRUITER = "RECRUITER"
    CONSULTANT = "CONSULTANT"
    PLACEMENT_OFFICER = "PLACEMENT_OFFICER"


# Official prefix mapping per Talentra Stage 3B Specification
ACTOR_PREFIX_MAP: Dict[str, str] = {
    ActorType.SUPER_ADMIN.value: "SA",
    ActorType.ADMIN.value: "AD",
    ActorType.ACCOUNT_ADMIN.value: "AA",
    ActorType.GUEST.value: "GU",
    ActorType.CANDIDATE.value: "CA",
    ActorType.EMPLOYER.value: "EM",
    ActorType.RECRUITER.value: "RE",
    ActorType.CONSULTANT.value: "CO",
    ActorType.PLACEMENT_OFFICER.value: "PO",
}

# Reverse prefix mapping
PREFIX_TO_ACTOR_TYPE: Dict[str, str] = {v: k for k, v in ACTOR_PREFIX_MAP.items()}

# Validation regex: exactly 2 uppercase letters + 5 digits = 7 chars
ACTOR_ID_REGEX = re.compile(r"^[A-Z]{2}[0-9]{5}$")


class ActorIDAllocationError(Exception):
    """Raised when an actor ID cannot be allocated or capacity is exhausted."""
    pass


class InvalidActorPrefixError(ValueError):
    """Raised when an unapproved actor prefix is requested."""
    pass


class ClientIDAssignmentProhibitedError(PermissionError):
    """Raised when a client attempts to supply a spoofed public actor ID."""
    pass


def get_prefix_for_role(role_code: str) -> str:
    """Resolve the authoritative 2-letter prefix for a role code."""
    normalized = role_code.strip().upper()
    if normalized not in ACTOR_PREFIX_MAP:
        raise InvalidActorPrefixError(
            f"Unknown actor role code '{role_code}'. Must be one of: {list(ACTOR_PREFIX_MAP.keys())}"
        )
    return ACTOR_PREFIX_MAP[normalized]


def validate_actor_id(actor_id: str) -> bool:
    """Validate that an actor ID matches the PPNNNNN specification and valid prefix."""
    if not actor_id or not isinstance(actor_id, str):
        return False
    if len(actor_id) != 7:
        return False
    if not ACTOR_ID_REGEX.match(actor_id):
        return False
    prefix = actor_id[:2]
    return prefix in PREFIX_TO_ACTOR_TYPE


def allocate_actor_id(db: Session, actor_type: str) -> str:
    """Allocate an atomic, concurrency-safe formatted actor ID from the database sequence.
    
    Args:
        db: SQLAlchemy database session.
        actor_type: Role code (e.g. 'CANDIDATE', 'EMPLOYER', 'SUPER_ADMIN') or 2-letter prefix.
        
    Returns:
        Formatted 7-character string: PPNNNNN (e.g. 'CA00001').
        
    Raises:
        InvalidActorPrefixError: If prefix is not in the 9 approved prefixes.
        ActorIDAllocationError: If sequence capacity (99,999) is exhausted or allocation fails.
    """
    prefix = actor_type.strip().upper()
    if len(prefix) > 2:
        prefix = get_prefix_for_role(prefix)
    elif prefix not in PREFIX_TO_ACTOR_TYPE:
        raise InvalidActorPrefixError(
            f"Invalid actor prefix '{prefix}'. Must be one of: {list(PREFIX_TO_ACTOR_TYPE.keys())}"
        )

    try:
        result = db.execute(
            text("SELECT allocate_actor_id(:prefix) AS actor_id"),
            {"prefix": prefix}
        ).scalar()
        if not result or not validate_actor_id(result):
            raise ActorIDAllocationError(f"Database returned invalid formatted ID: {result}")
        return result
    except Exception as e:
        err_msg = str(e)
        if "capacity exhausted" in err_msg.lower() or "limit 99999" in err_msg.lower() or "reached maximum value" in err_msg.lower():
            raise ActorIDAllocationError(
                f"Actor ID capacity exhausted for prefix '{prefix}' (maximum 99,999 reached). "
                "Capacity expansion or key migration required."
            ) from e
        raise ActorIDAllocationError(f"Failed to allocate actor ID for prefix '{prefix}': {e}") from e


def provision_actor_identity(
    db: Session,
    user_id: int,
    role_id: int,
    role_code: str,
    organisation_id: Optional[int] = None,
    client_supplied_id: Optional[str] = None
) -> str:
    """Trusted server-side provisioning of an actor identity.
    
    Rejects any client-supplied actor ID to prevent spoofing.
    Allocates an authoritative ID via the database sequence and records it in user_actor_identity.
    
    Args:
        db: SQLAlchemy database session.
        user_id: Canonical user account ID.
        role_id: Assigned role internal ID.
        role_code: Role code string (e.g. 'CANDIDATE', 'RECRUITER').
        organisation_id: Optional organisation ID for scoped roles (e.g. Recruiter, Employer).
        client_supplied_id: Optional client-provided value, strictly prohibited.
        
    Returns:
        The newly allocated immutable public actor ID.
    """
    if client_supplied_id is not None:
        raise ClientIDAssignmentProhibitedError(
            "Client-supplied actor IDs are strictly prohibited. Actor IDs are server-allocated."
        )

    prefix = get_prefix_for_role(role_code)
    allocated_id = allocate_actor_id(db, prefix)

    db.execute(
        text("""
        INSERT INTO "user_actor_identity" (
            "user_id", "role_id", "role_code", "actor_prefix", "actor_id", "organisation_id", "is_active"
        ) VALUES (
            :user_id, :role_id, :role_code, :prefix, :actor_id, :org_id, :is_active
        )
        """),
        {
            "user_id": user_id,
            "role_id": role_id,
            "role_code": role_code.strip().upper(),
            "prefix": prefix,
            "actor_id": allocated_id,
            "org_id": organisation_id,
            "is_active": True,
        }
    )
    return allocated_id
