"""Authentication and Registration Endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_auth_subject, get_current_user, AuthClaims
from app.models.user import User, UserActorIdentity, UserRoleAssignment, Role
from app.schemas.auth import UserProfileResponse, ActorIdentityItem
from app.schemas.candidate import CandidateRegisterRequest, CandidateProfileResponse
from app.services.candidate_service import (
    register_candidate_workflow,
    DuplicateCandidateProfileError,
    AccountEmailConflictError,
)
from app.services.country_service import (
    InvalidCountryCodeError,
    InvalidPhoneNumberError,
)
from app.services.actor_id_service import (
    ClientIDAssignmentProhibitedError,
    ActorIDAllocationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Registration"])


@router.post(
    "/register/candidate",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Candidate Profile",
    description="""
    Performs atomic Candidate self-registration:
    - Validates caller's verified Supabase Auth JWT (never trusts client user ID).
    - Validates country selection against ISO 3166-1 country master data.
    - Validates and formats contact phone number via ITU-T E.164.
    - Allocates an immutable, sequential public CA-series actor ID (CAxxxxx).
    - Creates canonical account, role assignment, actor identity, and profile atomically.
    """,
)
def register_candidate(
    request: CandidateRegisterRequest,
    claims: AuthClaims = Depends(get_current_auth_subject),
    db: Session = Depends(get_db),
):
    """Register Candidate endpoint."""
    try:
        profile_response = register_candidate_workflow(db, claims, request)
        return profile_response
    except DuplicateCandidateProfileError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except AccountEmailConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except InvalidCountryCodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except InvalidPhoneNumberError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ClientIDAssignmentProhibitedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ActorIDAllocationError as e:
        logger.error("Actor ID allocation error during candidate registration: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to allocate sequential public actor ID. Please contact support.",
        )
    except Exception as e:
        logger.error("Unexpected candidate registration error: %s", str(e), exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an unexpected internal error.",
        )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get Authenticated User Identity",
    description="Returns the authenticated user's canonical account details, active roles, and assigned actor IDs.",
)
def get_authenticated_user_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user profile and actor identities."""
    # Query active role codes
    role_assignments = (
        db.query(Role.role_code)
        .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
        .filter(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.revoked_at.is_(None),
        )
        .all()
    )
    roles = [r[0] for r in role_assignments]

    # Query public actor identities
    identities = (
        db.query(UserActorIdentity)
        .filter(
            UserActorIdentity.user_id == user.id,
            UserActorIdentity.is_active.is_(True),
        )
        .all()
    )
    actor_items = [
        ActorIdentityItem(
            role_code=ident.role_code,
            actor_prefix=ident.actor_prefix,
            actor_id=ident.actor_id,
            organisation_id=ident.organisation_id,
            is_active=ident.is_active,
        )
        for ident in identities
    ]

    return UserProfileResponse(
        user_id=user.id,
        display_name=user.display_name,
        email_address=user.email_address,
        phone_e164=user.phone_e164,
        provider_subject=user.provider_subject,
        roles=roles,
        actor_identities=actor_items,
        created_at=user.created_at,
    )
