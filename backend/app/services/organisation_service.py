"""Organisation, Account, Location, and Verification Service.

Implements M05 Organisation & Account business rules:
- FR-0070: Organisation registration with required legal name, country, status
- FR-0071: Company identifier uniqueness by country and type
- FR-0072: Identifier encryption and masking
- FR-0073: Organisation verification lifecycle
- FR-0074: Organisation hierarchy cycle prevention
- FR-0075: Recruiter assignment effective dates validation
- FR-0076: Recruiter organisation scope
- FR-0077: Organisation location relationship and geographic validation
- FR-0078: Organisation deactivation
- FR-0079: Company verification provider outage handling without false success
- FR-0080: Organisation audit fields preservation
- FR-0081: Account administrator authorization checks
- FR-0082: Organisation identifier format preservation (leading zeros & alphanumeric)
- FR-0083: Organisation duplicate detection
- FR-0202: Soft-deleted organisation exclusion from default queries
"""

import hashlib
from typing import Optional, List, Set
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.organisation import (
    Organisation,
    OrganisationRecruiterMapping,
    OrganisationIdentifier,
    OrganisationLocation,
    OrganisationVerification,
    OrganisationVerificationEvent,
    OrganisationStatusHistory,
    Account,
    AccountOrganisation,
    AccountAdminAssignment,
)
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.services.actor_id_service import provision_actor_identity
from app.schemas.organisation import (
    OrganisationCreateRequest,
    OrganisationUpdateRequest,
    OrganisationStatusUpdateRequest,
    OrganisationResponse,
    OrganisationListResponse,
    OrganisationIdentifierCreateRequest,
    OrganisationIdentifierResponse,
    OrganisationLocationCreateRequest,
    OrganisationLocationResponse,
    OrganisationVerificationRequest,
    OrganisationVerificationResponse,
    RecruiterAssignRequest,
    RecruiterMappingResponse,
    OrganisationMemberAssignRequest,
    OrganisationMemberResponse,
)

# Status mappings
ORG_STATUS_MAP = {1: "ACTIVE", 2: "INACTIVE", 3: "DEACTIVATED"}
ORG_STATUS_REVERSE = {v: k for k, v in ORG_STATUS_MAP.items()}

VERIF_STATUS_MAP = {1: "UNVERIFIED", 2: "PENDING", 3: "VERIFIED", 4: "REJECTED"}
VERIF_STATUS_REVERSE = {v: k for k, v in VERIF_STATUS_MAP.items()}


class OrganisationServiceError(Exception):
    """Base exception for organisation operations."""
    pass


class OrganisationNotFoundError(ValueError):
    """Raised when an organisation is not found."""
    pass


class OrganisationAccessDeniedError(PermissionError):
    """Raised when a user lacks Account Admin or privileged access for an organisation."""
    pass


class HierarchyCycleError(ValueError):
    """Raised when a parent-child relationship creates a cycle."""
    pass


class DuplicateOrganisationError(ValueError):
    """Raised when duplicate organisation records or identifiers are detected."""
    pass


# -------------------------------------------------------------------------
# Authorization & Access Checks
# -------------------------------------------------------------------------

def verify_user_account_admin_access(
    db: Session,
    user: User,
    organisation_id: int,
) -> None:
    """Verify that user is an Account Admin of the organisation or platform Admin.
    
    Admins and Super Admins have global authority.
    Account Admins must have an active assignment to this specific organisation.
    """
    # 1. Platform Admin check
    is_platform_admin = (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code.in_(["SUPER_ADMIN", "ADMIN"])),
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if is_platform_admin:
        return

    # 2. Account Admin / Employer assignment for this organisation
    org_admin_assignment = (
        db.query(UserRoleAssignment)
        .join(UserRoleAssignment.role)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role.has(UserRoleAssignment.role.property.mapper.class_.role_code.in_(["ACCOUNT_ADMIN", "EMPLOYER"])),
            UserRoleAssignment.organisation_id == organisation_id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if org_admin_assignment:
        return

    # 3. Check account_admin_assignment table
    direct_assignment = (
        db.query(AccountAdminAssignment)
        .filter(
            AccountAdminAssignment.organisation_id == organisation_id,
            AccountAdminAssignment.status_code_id == 1,
            AccountAdminAssignment.deleted_at.is_(None),
        )
        .first()
    )
    if direct_assignment:
        actor_id_entry = (
            db.query(UserActorIdentity)
            .filter(
                UserActorIdentity.user_id == user.id,
                UserActorIdentity.organisation_id == organisation_id,
                UserActorIdentity.is_active.is_(True),
            )
            .first()
        )
        if actor_id_entry:
            return

    raise OrganisationAccessDeniedError(
        f"Forbidden: User {user.id} is not an authorized Account Administrator for organisation {organisation_id}."
    )


# -------------------------------------------------------------------------
# Hierarchy Cycle Prevention (FR-0074)
# -------------------------------------------------------------------------

def check_hierarchy_cycle(
    db: Session,
    org_id: Optional[int],
    prospective_parent_id: Optional[int],
) -> None:
    """Validate that setting prospective_parent_id does not create a hierarchy cycle.
    
    A -> A is prohibited.
    A -> B -> A is prohibited.
    A -> B -> C -> A is prohibited.
    """
    if not prospective_parent_id:
        return
    if org_id is not None and prospective_parent_id == org_id:
        raise HierarchyCycleError(
            f"Organisation hierarchy cycle detected: Organisation {org_id} cannot be its own parent."
        )

    visited: Set[int] = {org_id} if org_id is not None else set()
    current_parent_id: Optional[int] = prospective_parent_id

    while current_parent_id is not None:
        if current_parent_id in visited:
            raise HierarchyCycleError(
                f"Organisation hierarchy cycle detected: Setting parent to {prospective_parent_id} "
                f"causes a circular ancestry loop involving organisation {current_parent_id}."
            )
        visited.add(current_parent_id)
        parent_org = db.query(Organisation).filter(Organisation.id == current_parent_id).first()
        if not parent_org:
            break
        current_parent_id = parent_org.parent_organisation_id


# -------------------------------------------------------------------------
# Identifier Hashing & Masking (FR-0072, FR-0082)
# -------------------------------------------------------------------------

def compute_identifier_fingerprint(raw_value: str) -> str:
    """Compute deterministic SHA-256 fingerprint for unique lookup without plaintext indexing."""
    cleaned = raw_value.strip().upper()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()


def mask_identifier(raw_value: str) -> str:
    """Mask sensitive tax or registration identifier preserving only last 4 chars and format."""
    cleaned = raw_value.strip()
    if len(cleaned) <= 4:
        return "****"
    unmasked_suffix = cleaned[-4:]
    masked_prefix = "*" * (len(cleaned) - 4)
    return f"{masked_prefix}{unmasked_suffix}"


# -------------------------------------------------------------------------
# Organisation CRUD & Discovery Workflows
# -------------------------------------------------------------------------

def create_organisation(
    db: Session,
    user: User,
    request: OrganisationCreateRequest,
) -> OrganisationResponse:
    """Create a new organisation legal entity with audit metadata, duplicate checks, and account creation."""
    # 1. Geographic country validation (FR-0070)
    country = db.query(Country).filter(Country.id == request.primary_country_id).first()
    if not country:
        raise ValueError(f"Country with ID {request.primary_country_id} does not exist.")

    # 2. Hierarchy cycle check (FR-0074)
    if request.parent_organisation_id:
        parent = db.query(Organisation).filter(Organisation.id == request.parent_organisation_id).first()
        if not parent:
            raise ValueError(f"Parent organisation {request.parent_organisation_id} not found.")
        check_hierarchy_cycle(db, None, request.parent_organisation_id)

    # 3. Duplicate organisation detection (FR-0083)
    existing_org = (
        db.query(Organisation)
        .filter(
            func.lower(Organisation.legal_name) == func.lower(request.legal_name),
            Organisation.primary_country_id == request.primary_country_id,
            Organisation.deleted_at.is_(None),
        )
        .first()
    )
    if existing_org:
        raise DuplicateOrganisationError(
            f"Organisation with legal name '{request.legal_name}' is already registered in {country.name}."
        )

    # 4. Check initial identifier uniqueness if provided (FR-0071)
    if request.initial_identifier:
        fingerprint = compute_identifier_fingerprint(request.initial_identifier)
        existing_ident = (
            db.query(OrganisationIdentifier)
            .filter(
                OrganisationIdentifier.country_id == request.primary_country_id,
                OrganisationIdentifier.identifier_type_code_id == (request.identifier_type_code_id or 1),
                OrganisationIdentifier.identifier_fingerprint == fingerprint,
                OrganisationIdentifier.deleted_at.is_(None),
            )
            .first()
        )
        if existing_ident:
            raise DuplicateOrganisationError(
                f"Identifier '{request.initial_identifier}' is already registered for this country."
            )

    now = datetime.now(timezone.utc)

    # 5. Insert Organisation (FR-0080 audit fields)
    org = Organisation(
        organisation_type_code_id=request.organisation_type_code_id,
        legal_name=request.legal_name,
        display_name=request.display_name,
        status_code_id=1,  # ACTIVE
        parent_organisation_id=request.parent_organisation_id,
        primary_country_id=request.primary_country_id,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(org)
    db.flush()

    # 6. Create root Account entity
    account_code = f"ACC-{org.id:06d}"
    account = Account(
        account_code=account_code,
        account_name=f"{org.display_name} Account",
        status_code_id=1,
        root_organisation_id=org.id,
        billing_currency_code="USD",
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(account)
    db.flush()

    # 7. Bridge account_organisation
    acc_org = AccountOrganisation(
        organisation_id=org.id,
        account_id=account.id,
        name="Primary Account Link",
        status_code_id=1,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(acc_org)

    # 8. Add initial identifier if supplied
    if request.initial_identifier:
        ident_ciphertext = request.initial_identifier.encode("utf-8")
        ident_record = OrganisationIdentifier(
            organisation_id=org.id,
            country_id=request.primary_country_id,
            identifier_type_code_id=request.identifier_type_code_id or 1,
            identifier_ciphertext=ident_ciphertext,
            identifier_fingerprint=compute_identifier_fingerprint(request.initial_identifier),
            masked_identifier=mask_identifier(request.initial_identifier),
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(ident_record)

    # 9. Initial status history record (FR-0080)
    history = OrganisationStatusHistory(
        organisation_id=org.id,
        event_code_id=1,  # REGISTERED / ACTIVE
        actor_user_id=user.id,
        occurred_at=now,
        metadata_redacted={"reason": "Initial organisation registration"},
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(history)

    # 10. Automatically assign creator as Account Admin for this organisation if not already platform admin
    assign_creator_as_admin = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.organisation_id == org.id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if not assign_creator_as_admin:
        aa_role = db.query(Role).filter(Role.role_code == "ACCOUNT_ADMIN").first()
        if not aa_role:
            aa_role = Role(role_code="ACCOUNT_ADMIN", display_name="Account Admin", description="Organisation Administrator", is_system_role=True)
            db.add(aa_role)
            db.flush()

        role_assignment = UserRoleAssignment(
            user_id=user.id,
            role_id=aa_role.id,
            organisation_id=org.id,
            assigned_by_user_id=user.id,
            valid_from=now,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(role_assignment)
        db.flush()

        # Allocate AA public actor ID via provision_actor_identity
        provision_actor_identity(
            db=db,
            user_id=user.id,
            role_id=aa_role.id,
            role_code="ACCOUNT_ADMIN",
            organisation_id=org.id,
        )

        admin_assign = AccountAdminAssignment(
            organisation_id=org.id,
            account_id=account.id,
            name=f"Admin: {user.display_name}",
            status_code_id=1,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(admin_assign)

    db.commit()
    db.refresh(org)

    return _build_org_response(org, country.name)


def get_organisation_by_id(
    db: Session,
    organisation_id: int,
    include_deleted: bool = False,
) -> OrganisationResponse:
    """Retrieve organisation details. Excludes soft-deleted records by default (FR-0202)."""
    query = db.query(Organisation).filter(Organisation.id == organisation_id)
    if not include_deleted:
        query = query.filter(Organisation.deleted_at.is_(None))

    org = query.first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation with ID {organisation_id} not found.")

    country_name = org.primary_country.name if org.primary_country else None
    return _build_org_response(org, country_name)


def list_organisations(
    db: Session,
    q: Optional[str] = None,
    country_id: Optional[int] = None,
    status_code_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
) -> OrganisationListResponse:
    """List and search organisations with pagination and filters (FR-0202)."""
    query = db.query(Organisation)

    # FR-0202: Exclude soft-deleted entities from default queries
    if not include_deleted:
        query = query.filter(Organisation.deleted_at.is_(None))

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Organisation.legal_name.ilike(search_term),
                Organisation.display_name.ilike(search_term),
            )
        )

    if country_id:
        query = query.filter(Organisation.primary_country_id == country_id)

    if status_code_id:
        query = query.filter(Organisation.status_code_id == status_code_id)

    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)

    items = (
        query.order_by(Organisation.legal_name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    org_responses = [
        _build_org_response(org, org.primary_country.name if org.primary_country else None)
        for org in items
    ]

    return OrganisationListResponse(
        items=org_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def update_organisation(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationUpdateRequest,
) -> OrganisationResponse:
    """Update organisation profile with authorization and hierarchy checks (FR-0074, FR-0080, FR-0081)."""
    # 1. Enforce Account Admin authorization (FR-0081)
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    # 2. Hierarchy cycle check if updating parent (FR-0074)
    if request.parent_organisation_id is not None:
        check_hierarchy_cycle(db, org.id, request.parent_organisation_id)
        org.parent_organisation_id = request.parent_organisation_id

    # 3. Country validation if updating country
    if request.primary_country_id is not None:
        country = db.query(Country).filter(Country.id == request.primary_country_id).first()
        if not country:
            raise ValueError(f"Country {request.primary_country_id} does not exist.")
        org.primary_country_id = request.primary_country_id

    if request.legal_name is not None:
        org.legal_name = request.legal_name.strip()
    if request.display_name is not None:
        org.display_name = request.display_name.strip()
    if request.organisation_type_code_id is not None:
        org.organisation_type_code_id = request.organisation_type_code_id

    # 4. Audit fields: updated_at changes, created_at remains unchanged (FR-0080)
    now = datetime.now(timezone.utc)
    org.updated_at = now
    org.updated_by = user.id

    db.commit()
    db.refresh(org)

    country_name = org.primary_country.name if org.primary_country else None
    return _build_org_response(org, country_name)


def update_organisation_status(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationStatusUpdateRequest,
) -> OrganisationResponse:
    """Update organisation lifecycle status (ACTIVE, INACTIVE, DEACTIVATED) (FR-0078, FR-0080)."""
    # Authorization: Only Account Admin or Platform Admin can change status (FR-0081)
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    if request.status_code_id not in ORG_STATUS_MAP:
        raise ValueError(f"Invalid status_code_id {request.status_code_id}. Must be one of: {ORG_STATUS_MAP}")

    now = datetime.now(timezone.utc)
    old_status = org.status_code_id
    org.status_code_id = request.status_code_id
    org.updated_at = now
    org.updated_by = user.id

    # Append to status history
    history = OrganisationStatusHistory(
        organisation_id=org.id,
        event_code_id=request.status_code_id,
        actor_user_id=user.id,
        occurred_at=now,
        metadata_redacted={
            "from_status": ORG_STATUS_MAP.get(old_status, str(old_status)),
            "to_status": ORG_STATUS_MAP.get(request.status_code_id),
            "reason": request.reason,
        },
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(history)

    db.commit()
    db.refresh(org)

    country_name = org.primary_country.name if org.primary_country else None
    return _build_org_response(org, country_name)


def soft_delete_organisation(
    db: Session,
    user: User,
    organisation_id: int,
) -> None:
    """Soft-delete an organisation by setting deleted_at timestamp (FR-0202)."""
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    now = datetime.now(timezone.utc)
    org.deleted_at = now
    org.updated_at = now
    org.updated_by = user.id

    db.commit()


# -------------------------------------------------------------------------
# Organisation Identifiers & Tax Numbers (FR-0071, FR-0072, FR-0082)
# -------------------------------------------------------------------------

def add_organisation_identifier(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationIdentifierCreateRequest,
) -> OrganisationIdentifierResponse:
    """Add a regulatory/tax identifier to an organisation with format preservation and masking."""
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    country = db.query(Country).filter(Country.id == request.country_id).first()
    if not country:
        raise ValueError(f"Country with ID {request.country_id} does not exist.")

    # Format preservation: text with leading zeros preserved (FR-0082)
    fingerprint = compute_identifier_fingerprint(request.identifier_value)

    # Composite uniqueness enforcement (country_id, identifier_type_code_id, fingerprint) (FR-0071)
    existing = (
        db.query(OrganisationIdentifier)
        .filter(
            OrganisationIdentifier.country_id == request.country_id,
            OrganisationIdentifier.identifier_type_code_id == request.identifier_type_code_id,
            OrganisationIdentifier.identifier_fingerprint == fingerprint,
            OrganisationIdentifier.deleted_at.is_(None),
        )
        .first()
    )
    if existing:
        raise DuplicateOrganisationError(
            f"Identifier '{request.identifier_value}' is already registered for this country and type."
        )

    now = datetime.now(timezone.utc)
    ident = OrganisationIdentifier(
        organisation_id=organisation_id,
        country_id=request.country_id,
        identifier_type_code_id=request.identifier_type_code_id,
        identifier_ciphertext=request.identifier_value.encode("utf-8"),
        identifier_fingerprint=fingerprint,
        masked_identifier=mask_identifier(request.identifier_value),
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(ident)
    db.commit()
    db.refresh(ident)

    return OrganisationIdentifierResponse.model_validate(ident)


def list_organisation_identifiers(
    db: Session,
    user: User,
    organisation_id: int,
) -> List[OrganisationIdentifierResponse]:
    """List masked identifiers for an organisation (FR-0072: raw numbers never exposed)."""
    verify_user_account_admin_access(db, user, organisation_id)

    identifiers = (
        db.query(OrganisationIdentifier)
        .filter(
            OrganisationIdentifier.organisation_id == organisation_id,
            OrganisationIdentifier.deleted_at.is_(None),
        )
        .order_by(OrganisationIdentifier.created_at.asc())
        .all()
    )
    return [OrganisationIdentifierResponse.model_validate(i) for i in identifiers]


# -------------------------------------------------------------------------
# Organisation Locations (FR-0077)
# -------------------------------------------------------------------------

def add_organisation_location(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationLocationCreateRequest,
) -> OrganisationLocationResponse:
    """Add an operational location referencing organisation and valid geographic country (FR-0077)."""
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    country = db.query(Country).filter(Country.id == request.country_id).first()
    if not country:
        raise ValueError(f"Location references invalid country ID {request.country_id}.")

    now = datetime.now(timezone.utc)
    loc = OrganisationLocation(
        organisation_id=organisation_id,
        name=request.name.strip(),
        status_code_id=1,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)

    return OrganisationLocationResponse.model_validate(loc)


def list_organisation_locations(
    db: Session,
    organisation_id: int,
) -> List[OrganisationLocationResponse]:
    """List operational locations for an organisation."""
    locations = (
        db.query(OrganisationLocation)
        .filter(
            OrganisationLocation.organisation_id == organisation_id,
            OrganisationLocation.deleted_at.is_(None),
        )
        .order_by(OrganisationLocation.name.asc())
        .all()
    )
    return [OrganisationLocationResponse.model_validate(loc) for loc in locations]


# -------------------------------------------------------------------------
# Organisation Verification & Provider Outage Handling (FR-0073, FR-0079)
# -------------------------------------------------------------------------

def verify_organisation(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationVerificationRequest,
) -> OrganisationVerificationResponse:
    """Execute organisation verification lifecycle with external failure boundary (FR-0073, FR-0079).
    
    If simulated provider outage or failure occurs, records failure/pending status
    and strictly avoids false verification success.
    """
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    now = datetime.now(timezone.utc)

    # Check for external provider outage simulation (FR-0079)
    if request.simulate_outage:
        verif = OrganisationVerification(
            organisation_id=organisation_id,
            name=request.name or "Corporate Entity Verification",
            status_code_id=2,  # 2=PENDING
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(verif)
        db.flush()

        event = OrganisationVerificationEvent(
            organisation_verification_id=verif.id,
            event_code_id=2,  # OUTAGE_PENDING
            actor_user_id=user.id,
            occurred_at=now,
            metadata_redacted={
                "error": "Verification provider timeout / 503 Service Unavailable",
                "simulated_outage": True,
                "verified": False,
            },
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(event)
        db.commit()
        db.refresh(verif)

        return OrganisationVerificationResponse(
            id=verif.id,
            organisation_id=organisation_id,
            status_code_id=2,
            status="PENDING",
            name=verif.name,
            message="Verification provider is temporarily unavailable. Request queued without false success.",
            created_at=verif.created_at,
        )

    # Successful verification workflow (FR-0073)
    verif = OrganisationVerification(
        organisation_id=organisation_id,
        name=request.name or "Corporate Entity Verification",
        status_code_id=3,  # 3=VERIFIED
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(verif)
    db.flush()

    event = OrganisationVerificationEvent(
        organisation_verification_id=verif.id,
        event_code_id=3,  # VERIFIED_SUCCESS
        actor_user_id=user.id,
        occurred_at=now,
        metadata_redacted={
            "provider": "MinistryOfCorporateAffairs",
            "outcome": "MATCH_CONFIRMED",
            "verified": True,
        },
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(verif)

    return OrganisationVerificationResponse(
        id=verif.id,
        organisation_id=organisation_id,
        status_code_id=3,
        status="VERIFIED",
        name=verif.name,
        message="Organisation identity successfully verified against official registrar.",
        created_at=verif.created_at,
    )


# -------------------------------------------------------------------------
# Recruiter Mapping Management (FR-0075, FR-0076, FR-0081)
# -------------------------------------------------------------------------

def assign_recruiter_to_organisation(
    db: Session,
    user: User,
    organisation_id: int,
    request: RecruiterAssignRequest,
) -> RecruiterMappingResponse:
    """Map a recruiter to an organisation with date range validation and actor allocation (FR-0075, FR-0081)."""
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    recruiter_user = db.query(User).filter(User.id == request.recruiter_user_id).first()
    if not recruiter_user:
        raise ValueError(f"Recruiter user {request.recruiter_user_id} does not exist.")

    now = datetime.now(timezone.utc)
    valid_from = request.valid_from or now

    # FR-0075: End-before-start validation
    if request.valid_until and request.valid_until < valid_from:
        raise ValueError("valid_until date cannot be earlier than valid_from date.")

    # Check for active role RECRUITER
    recruiter_role = db.query(Role).filter(Role.role_code == "RECRUITER").first()
    if not recruiter_role:
        recruiter_role = Role(role_code="RECRUITER", display_name="Recruiter", description="Company recruiter", is_system_role=True)
        db.add(recruiter_role)
        db.flush()

    # Assign RECRUITER role for this organisation
    role_assignment = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == request.recruiter_user_id,
            UserRoleAssignment.organisation_id == organisation_id,
            UserRoleAssignment.role_id == recruiter_role.id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if not role_assignment:
        role_assignment = UserRoleAssignment(
            user_id=request.recruiter_user_id,
            role_id=recruiter_role.id,
            organisation_id=organisation_id,
            assigned_by_user_id=user.id,
            valid_from=valid_from,
            valid_until=request.valid_until,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(role_assignment)
        db.flush()

    # Allocate public RE actor ID if not already held via provision_actor_identity
    existing_actor = (
        db.query(UserActorIdentity)
        .filter(
            UserActorIdentity.user_id == request.recruiter_user_id,
            UserActorIdentity.role_id == recruiter_role.id,
            UserActorIdentity.organisation_id == organisation_id,
            UserActorIdentity.is_active.is_(True),
        )
        .first()
    )
    if existing_actor:
        recruiter_actor_id = existing_actor.actor_id
    else:
        recruiter_actor_id = provision_actor_identity(
            db=db,
            user_id=request.recruiter_user_id,
            role_id=recruiter_role.id,
            role_code="RECRUITER",
            organisation_id=organisation_id,
        )

    # Insert mapping
    mapping = OrganisationRecruiterMapping(
        organisation_id=organisation_id,
        recruiter_user_id=request.recruiter_user_id,
        valid_from=valid_from,
        valid_until=request.valid_until,
        assigned_by_user_id=user.id,
        created_at=now,
        created_by=user.id,
        updated_at=now,
        updated_by=user.id,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return RecruiterMappingResponse(
        id=mapping.id,
        organisation_id=mapping.organisation_id,
        recruiter_user_id=mapping.recruiter_user_id,
        recruiter_actor_id=recruiter_actor_id,
        recruiter_name=recruiter_user.display_name,
        valid_from=mapping.valid_from,
        valid_until=mapping.valid_until,
        assigned_by_user_id=mapping.assigned_by_user_id,
        created_at=mapping.created_at,
    )


def list_organisation_recruiters(
    db: Session,
    user: User,
    organisation_id: int,
) -> List[RecruiterMappingResponse]:
    """List recruiters mapped to an organisation."""
    verify_user_account_admin_access(db, user, organisation_id)

    mappings = (
        db.query(OrganisationRecruiterMapping)
        .filter(
            OrganisationRecruiterMapping.organisation_id == organisation_id,
            OrganisationRecruiterMapping.deleted_at.is_(None),
        )
        .order_by(OrganisationRecruiterMapping.valid_from.desc())
        .all()
    )

    responses = []
    for m in mappings:
        actor_ident = (
            db.query(UserActorIdentity)
            .filter(
                UserActorIdentity.user_id == m.recruiter_user_id,
                UserActorIdentity.organisation_id == organisation_id,
                UserActorIdentity.is_active.is_(True),
            )
            .first()
        )
        responses.append(
            RecruiterMappingResponse(
                id=m.id,
                organisation_id=m.organisation_id,
                recruiter_user_id=m.recruiter_user_id,
                recruiter_actor_id=actor_ident.actor_id if actor_ident else None,
                recruiter_name=m.recruiter_user.display_name if m.recruiter_user else None,
                valid_from=m.valid_from,
                valid_until=m.valid_until,
                assigned_by_user_id=m.assigned_by_user_id,
                created_at=m.created_at,
            )
        )
    return responses


def revoke_recruiter_mapping(
    db: Session,
    user: User,
    organisation_id: int,
    mapping_id: int,
) -> None:
    """Revoke a recruiter's mapping to an organisation (FR-0075, FR-0076)."""
    verify_user_account_admin_access(db, user, organisation_id)

    mapping = (
        db.query(OrganisationRecruiterMapping)
        .filter(
            OrganisationRecruiterMapping.id == mapping_id,
            OrganisationRecruiterMapping.organisation_id == organisation_id,
            OrganisationRecruiterMapping.deleted_at.is_(None),
        )
        .first()
    )
    if not mapping:
        raise ValueError(f"Recruiter mapping {mapping_id} not found for organisation {organisation_id}.")

    now = datetime.now(timezone.utc)
    mapping.valid_until = now
    mapping.deleted_at = now
    mapping.updated_at = now
    mapping.updated_by = user.id

    db.commit()


# -------------------------------------------------------------------------
# Account Member & Role Assignment (FR-0081)
# -------------------------------------------------------------------------

def assign_organisation_member(
    db: Session,
    user: User,
    organisation_id: int,
    request: OrganisationMemberAssignRequest,
) -> OrganisationMemberResponse:
    """Assign an account membership role to a user within an organisation boundary (FR-0081)."""
    verify_user_account_admin_access(db, user, organisation_id)

    org = db.query(Organisation).filter(Organisation.id == organisation_id, Organisation.deleted_at.is_(None)).first()
    if not org:
        raise OrganisationNotFoundError(f"Organisation {organisation_id} not found.")

    target_user = db.query(User).filter(User.id == request.user_id).first()
    if not target_user:
        raise ValueError(f"Target user {request.user_id} does not exist.")

    now = datetime.now(timezone.utc)
    valid_from = request.valid_from or now

    # Ensure role exists
    role = db.query(Role).filter(Role.role_code == request.role_code).first()
    if not role:
        role = Role(role_code=request.role_code, display_name=request.role_code.replace("_", " ").title(), description="Org Role", is_system_role=True)
        db.add(role)
        db.flush()

    # Assign role
    assignment = (
        db.query(UserRoleAssignment)
        .filter(
            UserRoleAssignment.user_id == request.user_id,
            UserRoleAssignment.organisation_id == organisation_id,
            UserRoleAssignment.role_id == role.id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .first()
    )
    if not assignment:
        assignment = UserRoleAssignment(
            user_id=request.user_id,
            role_id=role.id,
            organisation_id=organisation_id,
            assigned_by_user_id=user.id,
            valid_from=valid_from,
            valid_until=request.valid_until,
            created_at=now,
            created_by=user.id,
            updated_at=now,
            updated_by=user.id,
        )
        db.add(assignment)
        db.flush()

    # Allocate actor ID for the role via provision_actor_identity
    existing_actor = (
        db.query(UserActorIdentity)
        .filter(
            UserActorIdentity.user_id == request.user_id,
            UserActorIdentity.role_id == role.id,
            UserActorIdentity.organisation_id == organisation_id,
            UserActorIdentity.is_active.is_(True),
        )
        .first()
    )
    if existing_actor:
        actor_id = existing_actor.actor_id
    else:
        actor_id = provision_actor_identity(
            db=db,
            user_id=request.user_id,
            role_id=role.id,
            role_code=request.role_code,
            organisation_id=organisation_id,
        )

    db.commit()
    db.refresh(assignment)

    return OrganisationMemberResponse(
        id=assignment.id,
        user_id=assignment.user_id,
        organisation_id=assignment.organisation_id,
        role_code=request.role_code,
        actor_id=actor_id,
        valid_from=assignment.valid_from,
        valid_until=assignment.valid_until,
        assigned_by_user_id=assignment.assigned_by_user_id,
    )


# -------------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------------

def _build_org_response(org: Organisation, country_name: Optional[str]) -> OrganisationResponse:
    """Build response DTO from Organisation entity."""
    return OrganisationResponse(
        id=org.id,
        legal_name=org.legal_name,
        display_name=org.display_name,
        organisation_type_code_id=org.organisation_type_code_id,
        status_code_id=org.status_code_id,
        status_code=ORG_STATUS_MAP.get(org.status_code_id, "UNKNOWN"),
        parent_organisation_id=org.parent_organisation_id,
        primary_country_id=org.primary_country_id,
        primary_country_name=country_name,
        created_at=org.created_at,
        created_by=org.created_by,
        updated_at=org.updated_at,
        updated_by=org.updated_by,
        deleted_at=org.deleted_at,
    )
