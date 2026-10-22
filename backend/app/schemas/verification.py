"""Pydantic schemas for Government ID Verification, Integrations, Audit & Retention (Stage 14)."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


# --- Government Document Verification Schemas ---

class VerificationConsentRequest(BaseModel):
    user_id: int
    consent_type_code_id: int = 1
    policy_version: str = "v1.0"
    permitted_purpose: str = Field(..., description="Documented purpose: KYC_ONBOARDING, EMPLOYMENT_BACKGROUND_CHECK, GIG_PAYOUT_COMPLIANCE")
    granted: bool = True

    model_config = ConfigDict(from_attributes=True)


class VerificationInitiateRequest(BaseModel):
    user_id: int
    document_type: str = Field(..., description="AADHAAR, PAN, PASSPORT, VOTER_ID")
    file_name: str
    file_mime_type: str = Field(..., description="application/pdf, image/png, image/jpeg")
    file_content_base64: Optional[str] = None
    consent_record_id: int
    purpose: str = "KYC_ONBOARDING"
    raw_identifier_for_masking_only: Optional[str] = Field(
        None, description="Transient raw ID passed ONLY for tokenization/masking; NEVER stored in DB"
    )

    model_config = ConfigDict(from_attributes=True)


class VerificationCaseResponse(BaseModel):
    case_id: int
    user_id: int
    document_type: str
    provider_code: str
    provider_case_reference: Optional[str] = None
    status: str
    requested_at: datetime
    completed_at: Optional[datetime] = None
    masked_identifier: Optional[str] = None
    identifier_fingerprint: Optional[str] = None
    name_match_score: Optional[int] = None
    name_match_status: Optional[str] = None
    malware_scan_status: str
    consent_record_id: int
    purpose: str

    model_config = ConfigDict(from_attributes=True)


class VerificationReviewRequest(BaseModel):
    decision: str = Field(..., description="VERIFIED, REJECTED, ESCALATED_FOR_DUAL_CONTROL")
    reason: str
    reviewer_user_id: int
    second_approver_user_id: Optional[int] = None
    is_high_risk_override: bool = False

    model_config = ConfigDict(from_attributes=True)


class DocumentAccessUrlResponse(BaseModel):
    case_id: int
    presigned_url: str
    expires_at: datetime
    access_token: str

    model_config = ConfigDict(from_attributes=True)


# --- Integrations Schemas ---

class WebhookPayload(BaseModel):
    event_id: str
    provider_code: str
    event_type: str
    case_reference: str
    timestamp: datetime
    payload_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class IntegrationBoundaryEntry(BaseModel):
    provider_code: str
    display_name: str
    purpose: str
    source_of_truth: str
    stored_vs_reference_data: str
    timeout_seconds: int
    retry_policy: str
    idempotency_policy: str
    audit_behavior: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class IdempotencyCheckRequest(BaseModel):
    idempotency_key: str
    scope: str
    payload_hash: str
    operation: str

    model_config = ConfigDict(from_attributes=True)


class LegacySyncRequest(BaseModel):
    candidate_id: int
    field_name: str
    incoming_value: Any
    incoming_timestamp: datetime
    sync_direction: str = "BIDIRECTIONAL"

    model_config = ConfigDict(from_attributes=True)


# --- Retention Schemas ---

class RetentionJobRunRequest(BaseModel):
    dry_run: bool = True
    target_data_class: str = Field(..., description="KYC_DOCUMENTS, INACTIVE_SESSIONS, PROCESSED_WEBHOOKS")
    retention_days: int = 2555  # 7 years default for KYC

    model_config = ConfigDict(from_attributes=True)


class RetentionJobSummaryResponse(BaseModel):
    job_id: int
    data_class: str
    dry_run: bool
    evaluated_records: int
    eligible_for_purge: int
    purged_records: int
    skipped_due_to_legal_hold: int
    executed_at: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Optional Reference Extensions Schemas ---

class SalaryBenchmarkCreate(BaseModel):
    code: str
    job_role: str
    currency: str = "INR"
    min_amount: Decimal
    max_amount: Decimal
    median_amount: Decimal
    source: str
    freshness_date: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagEvaluationRequest(BaseModel):
    flag_code: str
    subject_key: str
    tenant_id: Optional[str] = None
    environment: str = "production"

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagResponse(BaseModel):
    flag_code: str
    enabled: bool
    subject_key: str
    rollout_percentage: int
    evaluation_reason: str

    model_config = ConfigDict(from_attributes=True)
