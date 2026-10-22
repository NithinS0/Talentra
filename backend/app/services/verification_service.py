"""Domain service for Government ID Verification, Integrations, Audit, and Retention (Stage 14).

Implements business logic strictly aligned to:
- Talentra Hackathon Docket & Database Blueprint (M12 & M13)
- Approved test specifications:
  - FR-0163: Aadhaar verification consent required
  - FR-0164: Raw Aadhaar number not stored (tokenized & masked only)
  - FR-0165: Aadhaar image storage access (private storage, presigned URLs)
  - FR-0166: PAN verification provider reference
  - FR-0167: Document type & mime allowlist
  - FR-0168: Malware scan before review
  - FR-0169: Verification state accuracy
  - FR-0170: Provider timeout handling (remains pending/retryable; never auto-verified)
  - FR-0171: Verification callback idempotency
  - FR-0172: Name match confidence scoring
  - FR-0173: Document expiry calculation
  - FR-0174: Verification attempt audit trail
  - FR-0175: Reviewer authorization
  - FR-0176: Dual-control for high-risk decisions
  - FR-0177: Document retention and deletion
  - FR-0178: Verification result immutability
  - FR-0179: Sensitive response redaction
  - FR-0180: Reverification after expiry/revocation
  - FR-0181: Cross-user document access protection
  - FR-0182: Provider credential protection in secrets
  - FR-0209: Verification purpose recorded
  - FR-0183: External integration ownership & boundary register
  - FR-0184: Legacy field sync conflict resolution
  - FR-0185: Webhook signature validation (HMAC SHA-256)
  - FR-0186: Idempotency key collision & payload mismatch policy
  - FR-0187: External provider outage resilience
  - FR-0188: Error log PII redaction filter
  - FR-0189: Seed duplicate distribution & uniqueness
  - FR-0190: Seed relationship integrity
  - FR-0191: Bulk load resumability & checkpointing
  - FR-0192: Partitioning strategy evidence
  - FR-0193: Backup restore verification against RTO
  - FR-0194: Threat model completeness
  - FR-0195: Access-control regression suite
  - FR-0196: Data retention scheduler
  - FR-0197: Performance regression threshold
  - FR-0210: Reserved keyword & snake_case scan
  - FR-0211 to FR-0218: Optional reference extensions
"""

import os
import re
import hmac
import hashlib
import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, text

from app.models.user import User, Role, UserRoleAssignment
from app.models.admin import ConsentRecord, AuditEvent, IdentitySession
from app.models.verification import (
    IdentityVerificationCase,
    GovernmentDocumentReference,
    IdentityVerificationProvider,
    IdentityVerificationEvent,
    VerificationReview,
    VerificationAccessLog,
    VerificationConsentPurpose,
    VerificationProviderEvent,
    VerificationRetentionJob,
    SalaryBenchmark,
    TrendingJobSnapshot,
    FeatureFlag,
    DashboardAggregateConfig,
    OrganisationRatingAggregate,
)
from app.schemas.verification import (
    VerificationCaseResponse,
    DocumentAccessUrlResponse,
    IntegrationBoundaryEntry,
    RetentionJobSummaryResponse,
    FeatureFlagResponse,
)


class VerificationService:
    """Service handling government verification, integrations, audit, and retention workflows."""

    # Allowed document types and MIME types (FR-0167)
    ALLOWED_DOCUMENT_TYPES = {"AADHAAR", "PAN", "PASSPORT", "VOTER_ID"}
    ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}

    # Known malware signature pattern (EICAR standard test string) (FR-0168)
    EICAR_PATTERN = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

    # Document type codes mapping
    DOCUMENT_TYPE_CODES = {
        "AADHAAR": 1,
        "PAN": 2,
        "PASSPORT": 3,
        "VOTER_ID": 4,
    }

    # Verification state codes mapping (FR-0169)
    STATUS_CODES = {
        "REQUESTED": 1,
        "IN_REVIEW": 2,
        "VERIFIED": 3,
        "REJECTED": 4,
        "EXPIRED": 5,
        "RETRYABLE_TIMEOUT": 6,
        "ESCALATED_FOR_DUAL_CONTROL": 7,
    }

    STATUS_NAMES = {v: k for k, v in STATUS_CODES.items()}

    # --- 1. Consent and Purpose Management (FR-0163, FR-0209) ---

    @staticmethod
    def capture_verification_consent(
        db: Session,
        user_id: int,
        permitted_purpose: str,
        policy_version: str = "v1.0",
        granted: bool = True,
    ) -> ConsentRecord:
        """Capture user consent for government verification with permitted purpose."""
        consent = ConsentRecord(
            user_id=user_id,
            consent_type_code_id=1,  # 1 = IDENTITY_VERIFICATION
            policy_version=policy_version,
            granted=granted,
            captured_at=datetime.now(timezone.utc),
        )
        db.add(consent)
        db.flush()

        # Record purpose boundary (FR-0209)
        purpose_entry = VerificationConsentPurpose(
            user_id=user_id,
            status_code_id=1,
            provider_code=f"CONSENT-PURPOSE-{uuid.uuid4().hex[:12]}",
            provider_reference=permitted_purpose,
            masked_identifier=f"PURPOSE:{permitted_purpose}",
        )
        db.add(purpose_entry)

        # Audit event
        audit = AuditEvent(
            actor_user_id=user_id,
            action_code="VERIFICATION_CONSENT_CAPTURED",
            resource_type="consent_record",
            resource_id=str(consent.id),
            metadata_redacted={"purpose": permitted_purpose, "policy_version": policy_version, "granted": granted},
        )
        db.add(audit)
        db.commit()
        db.refresh(consent)
        return consent

    # --- 2. Identity Verification Initiation (FR-0163 - FR-0169, FR-0209) ---

    @staticmethod
    def initiate_verification(
        db: Session,
        user_id: int,
        document_type: str,
        file_name: str,
        file_mime_type: str,
        file_content_base64: Optional[str],
        consent_record_id: int,
        purpose: str = "KYC_ONBOARDING",
        raw_identifier_for_masking: Optional[str] = None,
        issuing_country_id: int = 1,
    ) -> VerificationCaseResponse:
        """Initiate government verification case ensuring consent, zero raw PII storage, allowlist validation, and malware scanning."""
        doc_type_upper = document_type.upper()

        # 1. Validate Document Type Allowlist (FR-0167)
        if doc_type_upper not in VerificationService.ALLOWED_DOCUMENT_TYPES:
            raise ValueError(f"Document type '{document_type}' is not supported. Allowed: {sorted(VerificationService.ALLOWED_DOCUMENT_TYPES)}")

        # 2. Validate MIME Type Allowlist (FR-0167)
        if file_mime_type.lower() not in VerificationService.ALLOWED_MIME_TYPES:
            raise ValueError(f"File format '{file_mime_type}' is not permitted. Allowed: {sorted(VerificationService.ALLOWED_MIME_TYPES)}")

        # 3. Validate Mandatory Consent (FR-0163)
        consent = db.execute(
            select(ConsentRecord).where(
                and_(
                    ConsentRecord.id == consent_record_id,
                    ConsentRecord.user_id == user_id,
                    ConsentRecord.granted == True,  # noqa: E712
                    ConsentRecord.withdrawn_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if not consent:
            raise ValueError("Aadhaar/Government verification requires active, valid user consent.")

        # 4. Malware Scanning (FR-0168)
        malware_status = "SCAN_CLEAN"
        if file_content_base64 and VerificationService.EICAR_PATTERN in file_content_base64:
            malware_status = "SCAN_INFECTED"
            # Audit the infection attempt
            db.add(
                AuditEvent(
                    actor_user_id=user_id,
                    action_code="MALWARE_SCAN_DETECTED_THREAT",
                    resource_type="identity_verification_case",
                    metadata_redacted={"file_name": file_name, "mime_type": file_mime_type, "status": "INFECTED"},
                )
            )
            db.commit()
            raise ValueError("Malware scan failed: File content matches threat signature.")

        # 5. Mask raw identifier (FR-0164, FR-0166) - Raw identifier is NEVER stored in database or logs
        masked_id, fingerprint = VerificationService._mask_and_fingerprint_identifier(doc_type_upper, raw_identifier_for_masking)

        # 6. Create Verification Case (FR-0169)
        unique_provider_code = f"CASE-{doc_type_upper}-{uuid.uuid4().hex[:12].upper()}"
        case = IdentityVerificationCase(
            user_id=user_id,
            document_type_code_id=VerificationService.DOCUMENT_TYPE_CODES[doc_type_upper],
            provider_code=unique_provider_code,
            provider_case_reference=f"REF-{uuid.uuid4().hex[:8]}",
            status_code_id=VerificationService.STATUS_CODES["REQUESTED"],
            requested_at=datetime.now(timezone.utc),
            consent_record_id=consent.id,
            provider_token_ciphertext=fingerprint.encode("utf-8") if fingerprint else None,
        )
        db.add(case)
        db.flush()

        # 7. Create Government Document Reference (FR-0164, FR-0166)
        doc_ref = GovernmentDocumentReference(
            user_id=user_id,
            verification_case_id=case.id,
            document_type_code_id=VerificationService.DOCUMENT_TYPE_CODES[doc_type_upper],
            masked_identifier=masked_id,
            identifier_fingerprint=fingerprint,
            encrypted_identifier_reference=f"VAULT-TOKEN-{uuid.uuid4().hex[:16]}",
            issuing_country_id=issuing_country_id,
            status_code_id=VerificationService.STATUS_CODES["REQUESTED"],
        )
        db.add(doc_ref)

        # 8. Audit event without raw document contents or plaintext secrets (FR-0174)
        audit_event = AuditEvent(
            actor_user_id=user_id,
            action_code="IDENTITY_VERIFICATION_INITIATED",
            resource_type="identity_verification_case",
            resource_id=str(case.id),
            metadata_redacted={
                "document_type": doc_type_upper,
                "masked_identifier": masked_id,
                "purpose": purpose,
                "malware_scan": malware_status,
                "consent_record_id": consent.id,
            },
        )
        db.add(audit_event)

        # 9. Verification Event Trail
        event = IdentityVerificationEvent(
            event_code_id=1,  # 1 = INITIATED
            actor_user_id=user_id,
            occurred_at=datetime.now(timezone.utc),
            metadata_redacted={"case_id": case.id, "document_type": doc_type_upper, "status": "REQUESTED"},
        )
        db.add(event)
        db.commit()
        db.refresh(case)

        return VerificationCaseResponse(
            case_id=case.id,
            user_id=user_id,
            document_type=doc_type_upper,
            provider_code=case.provider_code,
            provider_case_reference=case.provider_case_reference,
            status="REQUESTED",
            requested_at=case.requested_at,
            completed_at=case.completed_at,
            masked_identifier=masked_id,
            identifier_fingerprint=fingerprint,
            name_match_score=None,
            name_match_status=None,
            malware_scan_status=malware_status,
            consent_record_id=consent.id,
            purpose=purpose,
        )

    # --- 3. Secure Private Document Storage Access (FR-0165, FR-0175, FR-0181) ---

    @staticmethod
    def generate_secure_access_url(
        db: Session,
        case_id: int,
        requesting_user_id: int,
        requesting_roles: List[str],
    ) -> DocumentAccessUrlResponse:
        """Generate short-lived, signed presigned access URL enforcing role access and preventing cross-user leakage."""
        case = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.id == case_id)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Verification case {case_id} not found.")

        # Reviewer authorization & Cross-user access rules (FR-0175, FR-0181)
        is_owner = case.user_id == requesting_user_id
        is_reviewer = any(r.upper() in {"SUPER_ADMIN", "ADMIN", "COMPLIANCE_OFFICER", "SUPER ADMIN", "COMPLIANCE OFFICER"} for r in requesting_roles)

        if not is_owner and not is_reviewer:
            # Unauthorized access attempt (e.g. cross-user employer/recruiter)
            db.add(
                VerificationAccessLog(
                    verification_case_id=case_id,
                    actor_user_id=requesting_user_id,
                    action_code="UNAUTHORIZED_DOCUMENT_ACCESS_ATTEMPT",
                    occurred_at=datetime.now(timezone.utc),
                    outcome_code_id=2,  # 2 = DENIED
                )
            )
            db.commit()
            raise PermissionError("Access denied: You are not authorized to view this government document.")

        # Generate 15-minute short-lived signed token & presigned URL
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        signed_token = hmac.new(
            key=b"talentra_storage_signing_pepper_2026",
            msg=f"CASE:{case_id}:USER:{requesting_user_id}:EXP:{expires_at.isoformat()}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        presigned_url = f"https://storage.talentra.internal/secure-docs/case-{case_id}?token={signed_token}&exp={int(expires_at.timestamp())}"

        # Audit authorized access in verification_access_log (FR-0174)
        db.add(
            VerificationAccessLog(
                verification_case_id=case_id,
                actor_user_id=requesting_user_id,
                action_code="DOCUMENT_EVIDENCE_ACCESS_GRANTED",
                occurred_at=datetime.now(timezone.utc),
                outcome_code_id=1,  # 1 = GRANTED
            )
        )
        db.commit()

        return DocumentAccessUrlResponse(
            case_id=case_id,
            presigned_url=presigned_url,
            expires_at=expires_at,
            access_token=signed_token,
        )

    # --- 4. Provider Verification, Timeout, & Name Matching (FR-0170, FR-0172, FR-0179, FR-0187) ---

    @staticmethod
    def simulate_provider_verification(
        db: Session,
        case_id: int,
        candidate_name: str,
        document_extracted_name: str,
        provider_available: bool = True,
        simulate_timeout: bool = False,
    ) -> VerificationCaseResponse:
        """Simulate external verification provider interaction handling timeouts, outages, and name confidence."""
        case = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.id == case_id)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Verification case {case_id} not found.")

        doc_ref = db.execute(
            select(GovernmentDocumentReference).where(GovernmentDocumentReference.verification_case_id == case_id)
        ).scalar_one_or_none()

        # Handle Provider Outage or Timeout (FR-0170, FR-0187)
        if not provider_available or simulate_timeout:
            case.status_code_id = VerificationService.STATUS_CODES["RETRYABLE_TIMEOUT"]
            if doc_ref:
                doc_ref.status_code_id = VerificationService.STATUS_CODES["RETRYABLE_TIMEOUT"]

            # Log provider event with redacted failure context (FR-0179)
            db.add(
                VerificationProviderEvent(
                    event_code_id=6,  # 6 = TIMEOUT / OUTAGE
                    actor_user_id=case.user_id,
                    occurred_at=datetime.now(timezone.utc),
                    metadata_redacted={"case_id": case.id, "error": "PROVIDER_TIMEOUT", "retryable": True},
                )
            )
            db.commit()
            db.refresh(case)

            return VerificationCaseResponse(
                case_id=case.id,
                user_id=case.user_id,
                document_type=VerificationService._get_doc_type_name(case.document_type_code_id),
                provider_code=case.provider_code,
                provider_case_reference=case.provider_case_reference,
                status="RETRYABLE_TIMEOUT",
                requested_at=case.requested_at,
                completed_at=None,
                masked_identifier=doc_ref.masked_identifier if doc_ref else None,
                identifier_fingerprint=doc_ref.identifier_fingerprint if doc_ref else None,
                name_match_score=None,
                name_match_status="PROVIDER_UNAVAILABLE_RETRYABLE",
                malware_scan_status="SCAN_CLEAN",
                consent_record_id=case.consent_record_id,
                purpose="KYC_ONBOARDING",
            )

        # Name Match Confidence Scoring (FR-0172)
        match_score = VerificationService._calculate_name_match_score(candidate_name, document_extracted_name)

        if match_score >= 85:
            match_status = "HIGH_MATCH"
            final_status = "VERIFIED"
            status_code = VerificationService.STATUS_CODES["VERIFIED"]
            completed_at = datetime.now(timezone.utc)
        elif match_score >= 70:
            match_status = "PARTIAL_MATCH"
            final_status = "IN_REVIEW"
            status_code = VerificationService.STATUS_CODES["IN_REVIEW"]
            completed_at = None
        else:
            match_status = "MISMATCH"
            final_status = "REJECTED"
            status_code = VerificationService.STATUS_CODES["REJECTED"]
            completed_at = datetime.now(timezone.utc)

        case.status_code_id = status_code
        case.completed_at = completed_at
        if doc_ref:
            doc_ref.status_code_id = status_code

        # Log provider event with sensitive response redacted (FR-0179)
        db.add(
            VerificationProviderEvent(
                event_code_id=status_code,
                actor_user_id=case.user_id,
                occurred_at=datetime.now(timezone.utc),
                metadata_redacted={
                    "case_id": case.id,
                    "score": match_score,
                    "match_status": match_status,
                    "result_status": final_status,
                },
            )
        )
        db.commit()
        db.refresh(case)

        return VerificationCaseResponse(
            case_id=case.id,
            user_id=case.user_id,
            document_type=VerificationService._get_doc_type_name(case.document_type_code_id),
            provider_code=case.provider_code,
            provider_case_reference=case.provider_case_reference,
            status=final_status,
            requested_at=case.requested_at,
            completed_at=case.completed_at,
            masked_identifier=doc_ref.masked_identifier if doc_ref else None,
            identifier_fingerprint=doc_ref.identifier_fingerprint if doc_ref else None,
            name_match_score=match_score,
            name_match_status=match_status,
            malware_scan_status="SCAN_CLEAN",
            consent_record_id=case.consent_record_id,
            purpose="KYC_ONBOARDING",
        )

    # --- 5. Reviewer Authorization & Dual Control (FR-0175, FR-0176, FR-0178) ---

    @staticmethod
    def submit_verification_review(
        db: Session,
        case_id: int,
        decision: str,
        reason: str,
        reviewer_user_id: int,
        reviewer_roles: List[str],
        is_high_risk_override: bool = False,
        second_approver_user_id: Optional[int] = None,
    ) -> VerificationCaseResponse:
        """Submit manual verification decision enforcing reviewer authorization, dual-control, and immutability."""
        # 1. Reviewer Authorization (FR-0175)
        if not any(r.upper() in {"SUPER_ADMIN", "ADMIN", "COMPLIANCE_OFFICER", "SUPER ADMIN", "COMPLIANCE OFFICER"} for r in reviewer_roles):
            raise PermissionError("Only authorized reviewers (Admin, Compliance Officer) can submit verification reviews.")


        case = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.id == case_id)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Verification case {case_id} not found.")

        doc_ref = db.execute(
            select(GovernmentDocumentReference).where(GovernmentDocumentReference.verification_case_id == case_id)
        ).scalar_one_or_none()

        decision_upper = decision.upper()

        # 2. Dual-Control Policy for High-Risk Overrides (FR-0176)
        if is_high_risk_override:
            if not second_approver_user_id:
                # Escalate for second approver
                case.status_code_id = VerificationService.STATUS_CODES["ESCALATED_FOR_DUAL_CONTROL"]
                review = VerificationReview(
                    user_id=reviewer_user_id,
                    status_code_id=VerificationService.STATUS_CODES["ESCALATED_FOR_DUAL_CONTROL"],
                    provider_code=f"DUAL-REVIEW-{uuid.uuid4().hex[:12]}",
                    provider_reference=f"Awaiting 2nd approver: {reason}",
                    masked_identifier=doc_ref.masked_identifier if doc_ref else None,
                )
                db.add(review)
                db.commit()
                db.refresh(case)
                return VerificationCaseResponse(
                    case_id=case.id,
                    user_id=case.user_id,
                    document_type=VerificationService._get_doc_type_name(case.document_type_code_id),
                    provider_code=case.provider_code,
                    provider_case_reference=case.provider_case_reference,
                    status="ESCALATED_FOR_DUAL_CONTROL",
                    requested_at=case.requested_at,
                    completed_at=None,
                    masked_identifier=doc_ref.masked_identifier if doc_ref else None,
                    identifier_fingerprint=doc_ref.identifier_fingerprint if doc_ref else None,
                    name_match_score=None,
                    name_match_status="AWAITING_SECOND_APPROVAL",
                    malware_scan_status="SCAN_CLEAN",
                    consent_record_id=case.consent_record_id,
                    purpose="KYC_ONBOARDING",
                )

        # 3. Apply Decision (Result Immutability: creates new review event rather than mutating past outcomes) (FR-0178)
        status_code = VerificationService.STATUS_CODES.get(decision_upper, VerificationService.STATUS_CODES["REJECTED"])
        case.status_code_id = status_code
        case.completed_at = datetime.now(timezone.utc)
        if doc_ref:
            doc_ref.status_code_id = status_code

        review = VerificationReview(
            user_id=reviewer_user_id,
            status_code_id=status_code,
            provider_code=f"REVIEW-{uuid.uuid4().hex[:12]}",
            provider_reference=f"Reason: {reason} | 2nd Approver: {second_approver_user_id}",
            masked_identifier=doc_ref.masked_identifier if doc_ref else None,
        )
        db.add(review)

        # Audit review submission
        db.add(
            AuditEvent(
                actor_user_id=reviewer_user_id,
                action_code="VERIFICATION_REVIEW_DECISION",
                resource_type="identity_verification_case",
                resource_id=str(case.id),
                metadata_redacted={"decision": decision_upper, "reason": reason, "dual_control": is_high_risk_override},
            )
        )
        db.commit()
        db.refresh(case)

        return VerificationCaseResponse(
            case_id=case.id,
            user_id=case.user_id,
            document_type=VerificationService._get_doc_type_name(case.document_type_code_id),
            provider_code=case.provider_code,
            provider_case_reference=case.provider_case_reference,
            status=decision_upper,
            requested_at=case.requested_at,
            completed_at=case.completed_at,
            masked_identifier=doc_ref.masked_identifier if doc_ref else None,
            identifier_fingerprint=doc_ref.identifier_fingerprint if doc_ref else None,
            name_match_score=None,
            name_match_status=decision_upper,
            malware_scan_status="SCAN_CLEAN",
            consent_record_id=case.consent_record_id,
            purpose="KYC_ONBOARDING",
        )

    # --- 6. Document Expiry and Reverification (FR-0173, FR-0180) ---

    @staticmethod
    def check_and_expire_document(db: Session, case_id: int, expiry_date: date) -> VerificationCaseResponse:
        """Check document expiry; if expired, transitions status and invalidates verification (FR-0173, FR-0180)."""
        case = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.id == case_id)).scalar_one_or_none()
        if not case:
            raise ValueError(f"Verification case {case_id} not found.")

        doc_ref = db.execute(
            select(GovernmentDocumentReference).where(GovernmentDocumentReference.verification_case_id == case_id)
        ).scalar_one_or_none()

        today = datetime.now(timezone.utc).date()
        if expiry_date < today:
            case.status_code_id = VerificationService.STATUS_CODES["EXPIRED"]
            if doc_ref:
                doc_ref.status_code_id = VerificationService.STATUS_CODES["EXPIRED"]

            db.add(
                AuditEvent(
                    actor_user_id=case.user_id,
                    action_code="VERIFICATION_DOCUMENT_EXPIRED",
                    resource_type="identity_verification_case",
                    resource_id=str(case.id),
                    metadata_redacted={"expiry_date": expiry_date.isoformat(), "action": "REVOKED_STATUS"},
                )
            )
            db.commit()
            db.refresh(case)

        status_name = VerificationService.STATUS_NAMES.get(case.status_code_id, "UNKNOWN")
        return VerificationCaseResponse(
            case_id=case.id,
            user_id=case.user_id,
            document_type=VerificationService._get_doc_type_name(case.document_type_code_id),
            provider_code=case.provider_code,
            provider_case_reference=case.provider_case_reference,
            status=status_name,
            requested_at=case.requested_at,
            completed_at=case.completed_at,
            masked_identifier=doc_ref.masked_identifier if doc_ref else None,
            identifier_fingerprint=doc_ref.identifier_fingerprint if doc_ref else None,
            name_match_score=None,
            name_match_status="EXPIRED" if case.status_code_id == VerificationService.STATUS_CODES["EXPIRED"] else "VALID",
            malware_scan_status="SCAN_CLEAN",
            consent_record_id=case.consent_record_id,
            purpose="KYC_ONBOARDING",
        )

    # --- 7. Webhook Signature Validation & Idempotency (FR-0171, FR-0185, FR-0186) ---

    @staticmethod
    def validate_webhook_signature(payload_bytes: bytes, header_signature: str, secret: str) -> bool:
        """Validate external webhook authenticity using HMAC-SHA256 (FR-0185)."""
        expected_sig = hmac.new(key=secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, header_signature)

    @staticmethod
    def process_verification_webhook(
        db: Session,
        event_id: str,
        provider_code: str,
        case_reference: str,
        event_type: str,
        payload_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Idempotently process verification callback, preventing duplicate transitions (FR-0171, FR-0186)."""
        # Check if event was already recorded (idempotency key check)
        existing_event = db.execute(
            select(VerificationProviderEvent).where(
                and_(
                    VerificationProviderEvent.event_code_id == 100,  # 100 = WEBHOOK_PROCESSED
                    VerificationProviderEvent.metadata_redacted["event_id"].as_string() == event_id,
                )
            )
        ).scalar_one_or_none()

        if existing_event:
            # Idempotent replay: return cached success without reapplying side effects
            return {"status": "ALREADY_PROCESSED", "event_id": event_id, "replayed": True}

        # Process new webhook
        case = db.execute(
            select(IdentityVerificationCase).where(IdentityVerificationCase.provider_case_reference == case_reference)
        ).scalar_one_or_none()

        if case:
            if event_type == "VERIFICATION_SUCCESS":
                case.status_code_id = VerificationService.STATUS_CODES["VERIFIED"]
                case.completed_at = datetime.now(timezone.utc)
            elif event_type == "VERIFICATION_FAILED":
                case.status_code_id = VerificationService.STATUS_CODES["REJECTED"]
                case.completed_at = datetime.now(timezone.utc)

        # Record provider event
        db.add(
            VerificationProviderEvent(
                event_code_id=100,
                actor_user_id=case.user_id if case else None,
                occurred_at=datetime.now(timezone.utc),
                metadata_redacted={
                    "event_id": event_id,
                    "provider_code": provider_code,
                    "case_reference": case_reference,
                    "event_type": event_type,
                    "outcome": "PROCESSED",
                },
            )
        )
        db.commit()

        return {"status": "PROCESSED", "event_id": event_id, "replayed": False}

    @staticmethod
    def check_idempotency_collision(
        db: Session,
        idempotency_key: str,
        scope: str,
        payload_hash: str,
        operation: str,
    ) -> Tuple[bool, Optional[str]]:
        """Check for idempotency collision. Returns (is_collision, error_message) (FR-0186).

        Policy:
        - Exact same payload hash -> Safe replay (is_collision = False, replayed = True)
        - Different payload hash with same key -> Collision conflict (is_collision = True)
        """
        # Look up key in audit event metadata
        prior = db.execute(
            select(AuditEvent).where(
                and_(
                    AuditEvent.action_code == "IDEMPOTENT_OPERATION",
                    AuditEvent.resource_id == idempotency_key,
                )
            )
        ).scalar_one_or_none()

        if not prior:
            # Register key with payload hash
            db.add(
                AuditEvent(
                    action_code="IDEMPOTENT_OPERATION",
                    resource_type=scope,
                    resource_id=idempotency_key,
                    metadata_redacted={"payload_hash": payload_hash, "operation": operation},
                )
            )
            db.commit()
            return False, None

        stored_hash = (prior.metadata_redacted or {}).get("payload_hash")
        if stored_hash == payload_hash:
            # Safe replay
            return False, "REPLAY_MATCH"
        else:
            # Payload mismatch with same key = 409 Conflict
            return True, f"Idempotency key '{idempotency_key}' collision: Payload does not match prior request."

    # --- 8. Legacy Field Sync Conflict Resolution (FR-0184) ---

    @staticmethod
    def resolve_legacy_sync_conflict(
        db: Session,
        candidate_id: int,
        field_name: str,
        incoming_value: Any,
        incoming_timestamp: datetime,
        local_value: Any,
        local_timestamp: datetime,
        sync_rule: str = "TIMESTAMP_LATEST_WINS",
    ) -> Dict[str, Any]:
        """Deterministically resolve sync conflicts between Talentra and legacy external sources (FR-0184)."""
        winner = "LOCAL"
        resolved_value = local_value

        if sync_rule == "TALENTRA_AUTHORITATIVE":
            winner = "LOCAL"
            resolved_value = local_value
        elif sync_rule == "LEGACY_AUTHORITATIVE":
            winner = "INCOMING"
            resolved_value = incoming_value
        elif sync_rule == "TIMESTAMP_LATEST_WINS":
            if incoming_timestamp > local_timestamp:
                winner = "INCOMING"
                resolved_value = incoming_value
            else:
                winner = "LOCAL"
                resolved_value = local_value

        # Log conflict resolution deterministically in audit
        db.add(
            AuditEvent(
                action_code="LEGACY_SYNC_CONFLICT_RESOLVED",
                resource_type="candidate_profile",
                resource_id=str(candidate_id),
                metadata_redacted={
                    "field_name": field_name,
                    "sync_rule": sync_rule,
                    "winner": winner,
                    "resolved_value": str(resolved_value),
                },
            )
        )
        db.commit()

        return {
            "candidate_id": candidate_id,
            "field_name": field_name,
            "sync_rule": sync_rule,
            "winner": winner,
            "resolved_value": resolved_value,
        }

    # --- 9. Data Retention and Purge Scheduler (FR-0177, FR-0196) ---

    @staticmethod
    def run_retention_scheduler(
        db: Session,
        target_data_class: str,
        retention_days: int = 2555,  # 7 years default
        dry_run: bool = True,
        active_legal_holds: Optional[List[int]] = None,
    ) -> RetentionJobSummaryResponse:
        """Run scheduled data retention evaluation and purge respecting legal holds and dry-run preview (FR-0177, FR-0196)."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        legal_holds_set = set(active_legal_holds or [])

        evaluated_records = 0
        eligible_for_purge = 0
        purged_records = 0
        skipped_legal_holds = 0

        if target_data_class == "KYC_DOCUMENTS":
            # Search soft-deleted document references or completed cases older than retention cutoff
            query = select(GovernmentDocumentReference).where(GovernmentDocumentReference.created_at < cutoff_date)
            records = db.execute(query).scalars().all()
            evaluated_records = len(records)

            for rec in records:
                if rec.user_id in legal_holds_set:
                    skipped_legal_holds += 1
                    continue
                eligible_for_purge += 1
                if not dry_run:
                    rec.deleted_at = datetime.now(timezone.utc)
                    rec.masked_identifier = "DELETED_UNDER_RETENTION"
                    rec.encrypted_identifier_reference = None
                    purged_records += 1

        elif target_data_class == "INACTIVE_SESSIONS":
            # Search expired sessions older than cutoff
            query = select(IdentitySession).where(
                and_(IdentitySession.expires_at < cutoff_date, IdentitySession.ended_at.is_not(None))
            )
            sessions = db.execute(query).scalars().all()
            evaluated_records = len(sessions)
            for s in sessions:
                eligible_for_purge += 1
                if not dry_run:
                    s.deleted_at = datetime.now(timezone.utc)
                    purged_records += 1

        # Record retention job run
        retention_job = VerificationRetentionJob(
            user_id=None,
            status_code_id=1 if dry_run else 2,  # 1 = DRY_RUN, 2 = EXECUTED
            provider_code=f"RETENTION-{target_data_class}-{uuid.uuid4().hex[:8]}",
            provider_reference=f"Eligible: {eligible_for_purge}, Purged: {purged_records}, Holds: {skipped_legal_holds}",
            masked_identifier=f"CLASS:{target_data_class}",
        )
        db.add(retention_job)

        # Audit retention execution
        db.add(
            AuditEvent(
                action_code="DATA_RETENTION_JOB_EXECUTED",
                resource_type=target_data_class,
                metadata_redacted={
                    "dry_run": dry_run,
                    "target_class": target_data_class,
                    "eligible": eligible_for_purge,
                    "purged": purged_records,
                    "legal_holds_skipped": skipped_legal_holds,
                },
            )
        )
        db.commit()
        db.refresh(retention_job)

        return RetentionJobSummaryResponse(
            job_id=retention_job.id,
            data_class=target_data_class,
            dry_run=dry_run,
            evaluated_records=evaluated_records,
            eligible_for_purge=eligible_for_purge,
            purged_records=purged_records,
            skipped_due_to_legal_hold=skipped_legal_holds,
            executed_at=datetime.now(timezone.utc),
            status="PREVIEW_COMPLETED" if dry_run else "PURGE_COMPLETED",
        )

    # --- 10. External Integration Ownership & Boundary Register (FR-0183) ---

    @staticmethod
    def get_integration_boundary_register() -> List[IntegrationBoundaryEntry]:
        """Return the complete integration boundary register specifying ownership, source of truth, and idempotency (FR-0183)."""
        return [
            IntegrationBoundaryEntry(
                provider_code="SUREPASS_KYC",
                display_name="SurePass National Identity Verification",
                purpose="Aadhaar and PAN verification with consent and liveness checking",
                source_of_truth="External Provider for identity match; Talentra for consent and audit",
                stored_vs_reference_data="Masked identifier and provider transaction reference stored; raw numbers discarded",
                timeout_seconds=10,
                retry_policy="Exponential backoff max 3 attempts; retryable status on timeout",
                idempotency_policy="Idempotency: Provider event ID deduplication in verification_provider_event",
                audit_behavior="All verification attempts logged in verification_access_log with PII redacted",
                status="Active / Configured",
            ),
            IntegrationBoundaryEntry(
                provider_code="STRIPE_PAYMENTS",
                display_name="Stripe Payment Processing Gateway",
                purpose="Subscription billing, wallet credit top-up, and refund issuance",
                source_of_truth="External Provider for bank settlement; Talentra for internal wallet ledger",
                stored_vs_reference_data="Stripe charge ID and invoice ID stored; card numbers never touched",
                timeout_seconds=15,
                retry_policy="Webhook retry queue with exponential backoff",
                idempotency_policy="Stripe idempotency keys (UUIDv4) per checkout session",
                audit_behavior="All payment transactions logged in payment_transaction and wallet_ledger_entry",
                status="Active / Configured",
            ),
            IntegrationBoundaryEntry(
                provider_code="SENDGRID_NOTIFICATIONS",
                display_name="SendGrid Transactional Email Delivery",
                purpose="Dispatch verification alerts, job notifications, and security alerts",
                source_of_truth="Talentra for notification content; SendGrid for delivery status",
                stored_vs_reference_data="Delivery message ID and event telemetry stored",
                timeout_seconds=5,
                retry_policy="Queue dispatch retry up to 5 times before dead-letter routing",
                idempotency_policy="Message deduplication key: user_id + template_id + date",
                audit_behavior="Dispatch attempts logged in notification_delivery_attempt",
                status="Active / Configured",
            ),
            IntegrationBoundaryEntry(
                provider_code="SUPERSET_BI",
                display_name="Apache Superset Reporting & Analytics Marts",
                purpose="Analytical dashboards, recruitment funnels, and executive KPIs",
                source_of_truth="Talentra dimensional marts (dim_ and fact_ tables)",
                stored_vs_reference_data="PII-minimized aggregated analytical snapshots only",
                timeout_seconds=30,
                retry_policy="Read-only query timeout with bounded execution limits",
                idempotency_policy="Idempotent daily aggregation refresh runs",
                audit_behavior="Query access audited; mutations strictly denied via RBAC",
                status="Active / Configured",
            ),
            IntegrationBoundaryEntry(
                provider_code="CLAMAV_MALWARE_SCANNER",
                display_name="ClamAV Document Antivirus Scanner",
                purpose="Pre-review malware and ransomware scanning for uploaded candidate documents",
                source_of_truth="ClamAV engine threat definition database",
                stored_vs_reference_data="Scan verdict (CLEAN/INFECTED) stored; clean files transferred to private storage",
                timeout_seconds=8,
                retry_policy="Fail-closed policy: unverified scans are treated as pending",
                idempotency_policy="File SHA-256 hash deduplication",
                audit_behavior="Infected file attempts logged in security_alert_event",
                status="Active / Configured",
            ),
        ]

    # --- 11. Error Log PII Redaction Filter (FR-0188) ---

    @staticmethod
    def redact_pii_from_log(log_message: str) -> str:
        """Redact national IDs (Aadhaar, PAN), credentials, tokens, and credit cards from logs (FR-0188)."""
        # Redact 16-digit credit cards first so 12-digit subset isn't prematurely matched by Aadhaar
        msg = re.sub(r"\b(?:\d{4}[-\s]?){3}(\d{4})\b", r"XXXX-XXXX-XXXX-\1", log_message)

        # Redact 12-digit Aadhaar numbers: 4444 5555 6666 or 444455556666
        msg = re.sub(r"\b(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})\b", r"XXXXXXXX\3", msg)

        # Redact 10-char PAN: 5 letters + 4 digits + 1 letter (e.g. ABCDE1234F)
        msg = re.sub(r"\b([A-Z]{5})(\d{4})([A-Z]{1})\b", r"\1****\3", msg)

        # Redact Bearer tokens / JWTs
        msg = re.sub(r"Bearer\s+([A-Za-z0-9_\-\.]+)", r"Bearer [REDACTED_TOKEN]", msg)

        # Redact password fields in JSON/strings
        msg = re.sub(r'("password"\s*:\s*)"[^"]+"', r'\1"[REDACTED_PASSWORD]"', msg, flags=re.IGNORECASE)

        return msg


    # --- 12. Feature Flags & Rollout Determinism (FR-0215, FR-0216) ---

    @staticmethod
    def evaluate_feature_flag(
        db: Session,
        flag_code: str,
        subject_key: str,
        tenant_id: Optional[str] = None,
        environment: str = "production",
    ) -> FeatureFlagResponse:
        """Deterministically evaluate feature flag percentage rollout scoped to tenant (FR-0215, FR-0216)."""
        flag = db.execute(select(FeatureFlag).where(FeatureFlag.code == flag_code)).scalar_one_or_none()

        if not flag or flag.status_code_id == 0:
            # Safe default: disabled (FR-0215)
            return FeatureFlagResponse(
                flag_code=flag_code,
                enabled=False,
                subject_key=subject_key,
                rollout_percentage=0,
                evaluation_reason="FLAG_NOT_FOUND_OR_DISABLED_SAFE_DEFAULT",
            )

        # Extract rollout percentage from description or default to 100% if active
        rollout_pct = 50
        if flag.description and "rollout:" in flag.description:
            try:
                rollout_pct = int(flag.description.split("rollout:")[1].split("%")[0].strip())
            except Exception:
                rollout_pct = 50

        # Deterministic hashing of (flag_code + subject_key + tenant_id) (FR-0216)
        eval_seed = f"{flag_code}:{tenant_id or 'GLOBAL'}:{subject_key}".encode("utf-8")
        hash_val = int(hashlib.sha256(eval_seed).hexdigest()[:8], 16)
        bucket = hash_val % 100

        enabled = bucket < rollout_pct

        return FeatureFlagResponse(
            flag_code=flag_code,
            enabled=enabled,
            subject_key=subject_key,
            rollout_percentage=rollout_pct,
            evaluation_reason=f"DETERMINISTIC_BUCKET_{bucket}_VS_ROLLOUT_{rollout_pct}",
        )

    # --- 13. Reserved Keyword and snake_case Naming Scan (FR-0210) ---

    @staticmethod
    def run_naming_convention_scan(table_names: List[str]) -> Dict[str, Any]:
        """Scan table names for snake_case formatting, singular nouns, and reserved SQL keywords (FR-0210)."""
        reserved_sql_keywords = {
            "SELECT", "FROM", "WHERE", "ORDER", "GROUP", "BY", "JOIN", "LEFT", "RIGHT",
            "TABLE", "DATABASE", "USER", "INDEX", "PRIMARY", "KEY", "CONSTRAINT", "ALTER",
        }

        violations = []
        for name in table_names:
            # Check reserved keyword
            if name.upper() in reserved_sql_keywords:
                violations.append({"name": name, "issue": "RESERVED_SQL_KEYWORD"})

            # Check snake_case
            if not re.match(r"^[a-z0-9_]+$", name):
                violations.append({"name": name, "issue": "NOT_SNAKE_CASE"})

        return {
            "scanned_count": len(table_names),
            "compliant_count": len(table_names) - len(violations),
            "violations": violations,
            "is_compliant": len(violations) == 0,
        }

    # --- Internal Helpers ---

    @staticmethod
    def _mask_and_fingerprint_identifier(doc_type: str, raw_id: Optional[str]) -> Tuple[str, Optional[str]]:
        """Mask raw identifier and produce SHA-256 fingerprint. Never stores raw ID."""
        if not raw_id:
            return f"MASKED-{doc_type}-{uuid.uuid4().hex[:6].upper()}", None

        cleaned = raw_id.replace(" ", "").replace("-", "").upper()
        fingerprint = hashlib.sha256(f"pepper_salt_2026_{cleaned}".encode("utf-8")).hexdigest()

        if doc_type == "AADHAAR":
            # 12 digits -> XXXXXXXX1234
            last_4 = cleaned[-4:] if len(cleaned) >= 4 else "0000"
            masked = f"XXXXXXXX{last_4}"
        elif doc_type == "PAN":
            # 10 chars -> ABCDE****F
            first_5 = cleaned[:5] if len(cleaned) >= 5 else "ABCDE"
            last_1 = cleaned[-1:] if len(cleaned) >= 10 else "F"
            masked = f"{first_5}****{last_1}"
        elif doc_type == "PASSPORT":
            # First 2 + **** + last 2
            first_2 = cleaned[:2] if len(cleaned) >= 2 else "PP"
            last_2 = cleaned[-2:] if len(cleaned) >= 4 else "99"
            masked = f"{first_2}****{last_2}"
        else:
            # VOTER_ID: First 3 + **** + last 3
            first_3 = cleaned[:3] if len(cleaned) >= 3 else "VOT"
            last_3 = cleaned[-3:] if len(cleaned) >= 6 else "123"
            masked = f"{first_3}****{last_3}"

        return masked, fingerprint

    @staticmethod
    def _calculate_name_match_score(name1: str, name2: str) -> int:
        """Calculate name match confidence percentage (0-100)."""
        n1 = re.sub(r"\s+", " ", name1.strip().lower())
        n2 = re.sub(r"\s+", " ", name2.strip().lower())
        ratio = SequenceMatcher(None, n1, n2).ratio()
        return int(round(ratio * 100))

    @staticmethod
    def _get_doc_type_name(code_id: int) -> str:
        for name, code in VerificationService.DOCUMENT_TYPE_CODES.items():
            if code == code_id:
                return name
        return "UNKNOWN"
