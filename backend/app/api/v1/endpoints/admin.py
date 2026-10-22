"""Administration & Role Governance API Endpoints.

Implements M04 Administration & RBAC Identity:
- FR-0055: Role assignment and authorization verification
- FR-0056: Permission denial by default
- FR-0057: Credential uniqueness and hash-only storage
- FR-0058: Passwords, tokens, and secrets redacted from audit logs
- FR-0059: Audit event append-only immutability enforcement
- FR-0060: Audit sensitive action recording
- FR-0061: Consent withdrawal and audit tracking
- FR-0062: Block candidate visibility enforcement
- FR-0063: Account soft deletion with deleted_at timestamp
- FR-0064: UTC audit timestamps
- FR-0065: Sensitive column data governance classification
- FR-0066: Session revocation and access termination
- FR-0067: Login attempt auditing and throttling detection
- FR-0068: Admin privilege escalation prevention (Super Admin vs Admin separation)
- FR-0069: Privileged access review evidence generation
- FR-0201: Sensitive action actor attribution
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.admin import (
    AdminUserRoleGrantRequest,
    AdminUserRoleRevokeRequest,
    AdminUserStatusUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AuditEventResponse,
    AuditEventListResponse,
    SessionRevokeRequest,
    SessionResponse,
    ConsentWithdrawRequest,
    ConsentRecordResponse,
    AccessReviewReportResponse,
    DataClassificationResponse,
)
from app.services.admin_service import (
    grant_user_role,
    revoke_user_role,
    update_user_account_status,
    soft_delete_user_account,
    list_users_for_admin,
    list_audit_events,
    assert_audit_event_immutability,
    withdraw_user_consent,
    revoke_identity_session,
    generate_privileged_access_review,
    get_data_classification_inventory,
    _build_admin_user_response,
    PrivilegeEscalationError,
    ImmutableAuditRecordError,
    AdminServiceError,
)

router = APIRouter(prefix="/admin", tags=["Administration & Role Governance"])


@router.post(
    "/roles/grant",
    response_model=AdminUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign a role to a user (FR-0055, FR-0068)",
)
def grant_role_endpoint(
    request: AdminUserRoleGrantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant an actor role to a user. Prevents privilege escalation (FR-0068)."""
    try:
        return grant_user_role(db=db, admin_user=current_user, request=request)
    except PrivilegeEscalationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except AdminServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/roles/revoke",
    response_model=AdminUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke a role from a user (FR-0055, FR-0068)",
)
def revoke_role_endpoint(
    request: AdminUserRoleRevokeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke an actor role from a user. Prevents privilege escalation (FR-0068)."""
    try:
        return revoke_user_role(db=db, admin_user=current_user, request=request)
    except PrivilegeEscalationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))
    except AdminServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user account status (Activate / Suspend) (FR-0060, FR-0201)",
)
def update_user_status_endpoint(
    user_id: int,
    request: AdminUserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user account status to ACTIVE, SUSPENDED, or DEACTIVATED."""
    try:
        return update_user_account_status(
            db=db,
            admin_user=current_user,
            user_id=user_id,
            request=request,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete(
    "/users/{user_id}",
    response_model=AdminUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete user account (FR-0063)",
)
def soft_delete_user_endpoint(
    user_id: int,
    reason: Optional[str] = Query(default="Administrative soft deletion", max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a user account by populating deleted_at timestamp (FR-0063)."""
    try:
        soft_delete_user_account(
            db=db,
            admin_user=current_user,
            user_id=user_id,
            reason=reason,
        )
        user = db.query(User).filter(User.id == user_id).first()
        return _build_admin_user_response(db, user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List users for administrative governance",
)
def list_users_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: Optional[str] = Query(default=None),
    role_code: Optional[str] = Query(default=None),
    include_deleted: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List and filter users for administrative review."""
    try:
        return list_users_for_admin(
            db=db,
            admin_user=current_user,
            q=q,
            role_code=role_code,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/audit-events",
    response_model=AuditEventListResponse,
    status_code=status.HTTP_200_OK,
    summary="List audit events (FR-0060, FR-0064, FR-0201)",
)
def list_audit_events_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    actor_user_id: Optional[int] = Query(default=None),
    action_code: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List audit events with sanitized metadata and UTC timestamps."""
    try:
        return list_audit_events(
            db=db,
            admin_user=current_user,
            page=page,
            page_size=page_size,
            actor_user_id=actor_user_id,
            action_code=action_code,
            resource_type=resource_type,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/audit-events/{event_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Attempt to delete audit event (Strictly rejected: FR-0059)",
)
def delete_audit_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejects any attempt to delete audit logs with HTTP 403 Forbidden (FR-0059)."""
    try:
        assert_audit_event_immutability(db=db, admin_user=current_user, event_id=event_id)
    except (ImmutableAuditRecordError, PermissionError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Prohibited operation: Audit records in 'audit_event' are append-only and cannot be updated or deleted.",
        )


@router.put(
    "/audit-events/{event_id}",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Attempt to update audit event (Strictly rejected: FR-0059)",
)
def update_audit_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rejects any attempt to modify audit logs with HTTP 403 Forbidden (FR-0059)."""
    try:
        assert_audit_event_immutability(db=db, admin_user=current_user, event_id=event_id)
    except (ImmutableAuditRecordError, PermissionError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Prohibited operation: Audit records in 'audit_event' are append-only and cannot be updated or deleted.",
        )


@router.post(
    "/sessions/{session_id}/revoke",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke an active identity session (FR-0066)",
)
def revoke_session_endpoint(
    session_id: int,
    request: Optional[SessionRevokeRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke an active identity session and terminate access."""
    reason = request.reason if request and request.reason else "Administrative revocation"
    try:
        return revoke_identity_session(
            db=db,
            admin_user=current_user,
            session_id=session_id,
            reason=reason,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.post(
    "/consent/withdraw",
    response_model=ConsentRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Record consent withdrawal (FR-0061)",
)
def withdraw_consent_endpoint(
    request: ConsentWithdrawRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Withdraw terms of service, privacy policy, or data processing consent."""
    try:
        return withdraw_user_consent(
            db=db,
            user=current_user,
            consent_type_code_id=request.consent_type_code_id,
            reason=request.reason,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/access-review",
    response_model=AccessReviewReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate privileged access review evidence report (FR-0069)",
)
def access_review_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate privileged access review report documenting active role assignments."""
    try:
        return generate_privileged_access_review(db=db, reviewer_user=current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get(
    "/data-classification",
    response_model=DataClassificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sensitive column data governance classification inventory (FR-0065)",
)
def data_classification_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve catalog of classified sensitive columns and governance classifications."""
    try:
        return get_data_classification_inventory(db=db, admin_user=current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
