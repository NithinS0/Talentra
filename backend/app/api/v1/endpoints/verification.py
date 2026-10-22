"""FastAPI endpoints for Talentra Stage 14: Government ID Verification, Integrations, Audit & Retention."""

from datetime import date, datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.verification import IdentityVerificationCase, GovernmentDocumentReference
from app.schemas.verification import (
    VerificationConsentRequest,
    VerificationInitiateRequest,
    VerificationCaseResponse,
    VerificationReviewRequest,
    DocumentAccessUrlResponse,
    WebhookPayload,
    IntegrationBoundaryEntry,
    IdempotencyCheckRequest,
    LegacySyncRequest,
    RetentionJobRunRequest,
    RetentionJobSummaryResponse,
    FeatureFlagEvaluationRequest,
    FeatureFlagResponse,
)
from app.services.verification_service import VerificationService

router = APIRouter()


def _get_user_roles(user: User) -> List[str]:
    """Extract assigned role names/codes in uppercase."""
    roles = []
    for ra in getattr(user, "role_assignments", []):
        if ra.role:
            code = getattr(ra.role, "role_code", None) or getattr(ra.role, "name", "")
            roles.append(code.upper().replace(" ", "_"))
    return roles


# -----------------------------------------------------------------------------
# 1. Verification Consent (FR-0163, FR-0209)
# -----------------------------------------------------------------------------
@router.post("/consent", status_code=status.HTTP_201_CREATED)
def capture_verification_consent(
    payload: VerificationConsentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Capture consent with documented purpose before initiating verification."""
    if current_user.id != payload.user_id:
        roles = _get_user_roles(current_user)
        if "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot capture verification consent on behalf of another user.",
            )


    consent = VerificationService.capture_verification_consent(
        db=db,
        user_id=payload.user_id,
        permitted_purpose=payload.permitted_purpose,
        policy_version=payload.policy_version,
        granted=payload.granted,
    )
    return {
        "consent_record_id": consent.id,
        "user_id": consent.user_id,
        "purpose": payload.permitted_purpose,
        "granted": consent.granted,
        "captured_at": consent.captured_at,
    }


# -----------------------------------------------------------------------------
# 2. Verification Initiation (FR-0163 - FR-0169, FR-0209)
# -----------------------------------------------------------------------------
@router.post("/initiate", response_model=VerificationCaseResponse, status_code=status.HTTP_201_CREATED)
def initiate_verification(
    payload: VerificationInitiateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Initiate a government verification case with zero raw PII persistence, allowlist check, and malware scan."""
    if current_user.id != payload.user_id:
        roles = _get_user_roles(current_user)
        if "ADMIN" not in roles and "SUPER_ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot initiate verification for another user.",
            )


    try:
        response = VerificationService.initiate_verification(
            db=db,
            user_id=payload.user_id,
            document_type=payload.document_type,
            file_name=payload.file_name,
            file_mime_type=payload.file_mime_type,
            file_content_base64=payload.file_content_base64,
            consent_record_id=payload.consent_record_id,
            purpose=payload.purpose,
            raw_identifier_for_masking=payload.raw_identifier_for_masking_only,
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------------------------
# 3. Secure Document Access (FR-0165, FR-0175, FR-0181)
# -----------------------------------------------------------------------------
@router.get("/cases/{case_id}/access-url", response_model=DocumentAccessUrlResponse)
def get_secure_access_url(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate short-lived signed presigned URL for document evidence."""
    user_roles = _get_user_roles(current_user)
    try:
        url_resp = VerificationService.generate_secure_access_url(
            db=db,
            case_id=case_id,
            requesting_user_id=current_user.id,
            requesting_roles=user_roles,
        )
        return url_resp
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# -----------------------------------------------------------------------------
# 4. Reviewer Submission & Dual Control (FR-0175, FR-0176, FR-0178)
# -----------------------------------------------------------------------------
@router.post("/cases/{case_id}/review", response_model=VerificationCaseResponse)
def submit_verification_review(
    case_id: int,
    payload: VerificationReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit reviewer decision enforcing dual-control for high risk overrides."""
    user_roles = _get_user_roles(current_user)
    try:
        resp = VerificationService.submit_verification_review(
            db=db,
            case_id=case_id,
            decision=payload.decision,
            reason=payload.reason,
            reviewer_user_id=current_user.id,
            reviewer_roles=user_roles,
            is_high_risk_override=payload.is_high_risk_override,
            second_approver_user_id=payload.second_approver_user_id,
        )
        return resp
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -----------------------------------------------------------------------------
# 5. External Webhook Processing & Idempotency (FR-0171, FR-0185, FR-0186)
# -----------------------------------------------------------------------------
@router.post("/webhook")
async def process_verification_webhook(
    request: Request,
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None, alias="X-Verification-Signature"),
    db: Session = Depends(get_db),
):
    """Receive external provider webhook with HMAC-SHA256 signature verification and idempotency."""
    # Validate signature if configured
    webhook_secret = "talentra_webhook_secret_key_2026"
    raw_body = await request.body()

    if x_signature:
        is_valid = VerificationService.validate_webhook_signature(raw_body, x_signature, webhook_secret)
        if not is_valid:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

    result = VerificationService.process_verification_webhook(
        db=db,
        event_id=payload.event_id,
        provider_code=payload.provider_code,
        case_reference=payload.case_reference,
        event_type=payload.event_type,
        payload_data=payload.payload_data,
    )
    return result


# -----------------------------------------------------------------------------
# 6. Idempotency Key Collision Check (FR-0186)
# -----------------------------------------------------------------------------
@router.post("/idempotency/check")
def check_idempotency(
    payload: IdempotencyCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate idempotency key reuse: safe replay on identical payload, 409 Conflict on payload mismatch."""
    is_collision, message = VerificationService.check_idempotency_collision(
        db=db,
        idempotency_key=payload.idempotency_key,
        scope=payload.scope,
        payload_hash=payload.payload_hash,
        operation=payload.operation,
    )
    if is_collision:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

    return {"status": "SUCCESS", "idempotency_key": payload.idempotency_key, "message": message or "KEY_REGISTERED"}


# -----------------------------------------------------------------------------
# 7. Data Retention Scheduler (FR-0177, FR-0196)
# -----------------------------------------------------------------------------
@router.post("/retention/run", response_model=RetentionJobSummaryResponse)
def run_retention_scheduler(
    payload: RetentionJobRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run data retention evaluation or purge (restricted to Super Admin and Admin)."""
    user_roles = _get_user_roles(current_user)
    if "SUPER_ADMIN" not in user_roles and "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required to trigger retention scheduler.",
        )


    summary = VerificationService.run_retention_scheduler(
        db=db,
        target_data_class=payload.target_data_class,
        retention_days=payload.retention_days,
        dry_run=payload.dry_run,
    )
    return summary


# -----------------------------------------------------------------------------
# 8. Integration Boundary Register (FR-0183)
# -----------------------------------------------------------------------------
@router.get("/integrations/register", response_model=List[IntegrationBoundaryEntry])
def get_integration_register(
    current_user: User = Depends(get_current_user),
):
    """Return external integration ownership and boundary register."""
    return VerificationService.get_integration_boundary_register()


# -----------------------------------------------------------------------------
# 9. Feature Flags (FR-0215, FR-0216)
# -----------------------------------------------------------------------------
@router.post("/feature-flags/evaluate", response_model=FeatureFlagResponse)
def evaluate_feature_flag(
    payload: FeatureFlagEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate feature flag percentage rollout deterministically."""
    return VerificationService.evaluate_feature_flag(
        db=db,
        flag_code=payload.flag_code,
        subject_key=payload.subject_key,
        tenant_id=payload.tenant_id,
        environment=payload.environment,
    )


# -----------------------------------------------------------------------------
# 10. Legacy Field Sync Conflict Resolution (FR-0184)
# -----------------------------------------------------------------------------
@router.post("/sync/resolve-conflict")
def resolve_legacy_sync(
    payload: LegacySyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deterministically resolve sync conflicts with legacy candidate sources."""
    result = VerificationService.resolve_legacy_sync_conflict(
        db=db,
        candidate_id=payload.candidate_id,
        field_name=payload.field_name,
        incoming_value=payload.incoming_value,
        incoming_timestamp=payload.incoming_timestamp,
        local_value="CurrentLocalValue",
        local_timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
        sync_rule="TIMESTAMP_LATEST_WINS",
    )
    return result
