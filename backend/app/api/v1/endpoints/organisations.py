"""Organisation & Account Management API Endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
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
from app.services.organisation_service import (
    create_organisation,
    get_organisation_by_id,
    list_organisations,
    update_organisation,
    update_organisation_status,
    soft_delete_organisation,
    add_organisation_identifier,
    list_organisation_identifiers,
    add_organisation_location,
    list_organisation_locations,
    verify_organisation,
    assign_recruiter_to_organisation,
    list_organisation_recruiters,
    revoke_recruiter_mapping,
    assign_organisation_member,
    OrganisationNotFoundError,
    OrganisationAccessDeniedError,
    HierarchyCycleError,
    DuplicateOrganisationError,
)

router = APIRouter(prefix="/organisations", tags=["Organisations & Accounts"])


@router.post(
    "",
    response_model=OrganisationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new organisation",
)
def register_organisation_endpoint(
    request: OrganisationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register a new employer legal entity and root account."""
    try:
        return create_organisation(db=db, user=current_user, request=request)
    except DuplicateOrganisationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (ValueError, HierarchyCycleError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "",
    response_model=OrganisationListResponse,
    summary="List and search organisations",
)
def list_organisations_endpoint(
    q: Optional[str] = Query(None, description="Search query matching legal or display name"),
    country_id: Optional[int] = Query(None, description="Filter by primary country ID"),
    status_code_id: Optional[int] = Query(None, description="Filter by status (1=ACTIVE, 2=INACTIVE, 3=DEACTIVATED)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_deleted: bool = Query(False, description="Include soft-deleted records (Admin only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List active organisations with pagination, search, and filters. Excludes soft-deleted entities by default (FR-0202)."""
    return list_organisations(
        db=db,
        q=q,
        country_id=country_id,
        status_code_id=status_code_id,
        page=page,
        page_size=page_size,
        include_deleted=include_deleted,
    )


@router.get(
    "/{organisation_id}",
    response_model=OrganisationResponse,
    summary="Get organisation details",
)
def get_organisation_endpoint(
    organisation_id: int,
    include_deleted: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details of an organisation."""
    try:
        return get_organisation_by_id(db=db, organisation_id=organisation_id, include_deleted=include_deleted)
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{organisation_id}",
    response_model=OrganisationResponse,
    summary="Update organisation profile",
)
def update_organisation_endpoint(
    organisation_id: int,
    request: OrganisationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update organisation profile. Enforces Account Admin authorization and hierarchy cycle prevention (FR-0074, FR-0081)."""
    try:
        return update_organisation(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HierarchyCycleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.patch(
    "/{organisation_id}/status",
    response_model=OrganisationResponse,
    summary="Update organisation status",
)
def update_organisation_status_endpoint(
    organisation_id: int,
    request: OrganisationStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update organisation status (e.g. ACTIVE, DEACTIVATED). Enforces audit logging and deactivation rules (FR-0078)."""
    try:
        return update_organisation_status(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete(
    "/{organisation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an organisation",
)
def delete_organisation_endpoint(
    organisation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-delete an organisation (FR-0202). Excludes from future default queries."""
    try:
        soft_delete_organisation(db=db, user=current_user, organisation_id=organisation_id)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{organisation_id}/identifiers",
    response_model=OrganisationIdentifierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add organisation tax/registration identifier",
)
def add_organisation_identifier_endpoint(
    organisation_id: int,
    request: OrganisationIdentifierCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a regulatory/tax identifier with format preservation and masking (FR-0071, FR-0072, FR-0082)."""
    try:
        return add_organisation_identifier(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DuplicateOrganisationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{organisation_id}/identifiers",
    response_model=List[OrganisationIdentifierResponse],
    summary="List organisation identifiers",
)
def list_organisation_identifiers_endpoint(
    organisation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List organisation identifiers with masked numbers (FR-0072)."""
    try:
        return list_organisation_identifiers(db=db, user=current_user, organisation_id=organisation_id)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post(
    "/{organisation_id}/locations",
    response_model=OrganisationLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an operational location",
)
def add_organisation_location_endpoint(
    organisation_id: int,
    request: OrganisationLocationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an operational location referencing geographic master data (FR-0077)."""
    try:
        return add_organisation_location(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{organisation_id}/locations",
    response_model=List[OrganisationLocationResponse],
    summary="List organisation locations",
)
def list_organisation_locations_endpoint(
    organisation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List operational locations for an organisation."""
    return list_organisation_locations(db=db, organisation_id=organisation_id)


@router.post(
    "/{organisation_id}/verify",
    response_model=OrganisationVerificationResponse,
    summary="Trigger organisation verification",
)
def verify_organisation_endpoint(
    organisation_id: int,
    request: OrganisationVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger organisation verification with graceful provider outage handling (FR-0073, FR-0079)."""
    try:
        return verify_organisation(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{organisation_id}/recruiters",
    response_model=RecruiterMappingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Map a recruiter to an organisation",
)
def assign_recruiter_endpoint(
    organisation_id: int,
    request: RecruiterAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign recruiter to organisation with effective dates validation and RE actor ID allocation (FR-0075, FR-0076, FR-0081)."""
    try:
        return assign_recruiter_to_organisation(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get(
    "/{organisation_id}/recruiters",
    response_model=List[RecruiterMappingResponse],
    summary="List mapped recruiters for an organisation",
)
def list_recruiters_endpoint(
    organisation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recruiters mapped to an organisation (FR-0076)."""
    try:
        return list_organisation_recruiters(db=db, user=current_user, organisation_id=organisation_id)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/{organisation_id}/recruiters/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke recruiter mapping",
)
def revoke_recruiter_endpoint(
    organisation_id: int,
    mapping_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke a recruiter's mapping to an organisation (FR-0075, FR-0076)."""
    try:
        revoke_recruiter_mapping(db=db, user=current_user, organisation_id=organisation_id, mapping_id=mapping_id)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/{organisation_id}/members",
    response_model=OrganisationMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a member role to an organisation",
)
def assign_member_endpoint(
    organisation_id: int,
    request: OrganisationMemberAssignRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign an account role (ACCOUNT_ADMIN, EMPLOYER, PLACEMENT_OFFICER) to a user (FR-0081)."""
    try:
        return assign_organisation_member(db=db, user=current_user, organisation_id=organisation_id, request=request)
    except OrganisationAccessDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrganisationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
