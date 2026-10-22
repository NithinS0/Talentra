"""Identity Verification Model Factory."""

import itertools
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.verification import IdentityVerificationProvider, IdentityVerificationCase, GovernmentDocumentReference
from app.models.admin import ConsentRecord

_verif_counter = itertools.count(1)


def create_factory_verification_case(
    db: Session,
    user_id: int,
    doc_type_id: int = 1,
    status_code_id: int = 3,  # 3=VERIFIED
) -> IdentityVerificationCase:
    """Create a synthetic identity verification case and masked document reference."""
    idx = next(_verif_counter)
    now_utc = datetime.now(timezone.utc)

    provider = db.execute(select(IdentityVerificationProvider).where(IdentityVerificationProvider.provider_code == "SANDBOX_VERIFY_PROVIDER")).scalar_one_or_none()
    if not provider:
        provider = IdentityVerificationProvider(
            provider_code="SANDBOX_VERIFY_PROVIDER",
            display_name="Talentra Mock Government Verification Sandbox",
            enabled=True,
        )
        db.add(provider)
        db.flush()

    consent = db.execute(select(ConsentRecord).where(ConsentRecord.user_id == user_id)).scalar_one_or_none()
    if not consent:
        consent = ConsentRecord(
            user_id=user_id,
            consent_type_code_id=1,
            policy_version="v1.0",
            granted=True,
        )
        db.add(consent)
        db.flush()

    case = IdentityVerificationCase(
        user_id=user_id,
        document_type_code_id=doc_type_id,
        provider_code=f"SANDBOX_FAC_{idx:05d}",
        status_code_id=status_code_id,
        requested_at=now_utc,
        completed_at=now_utc if status_code_id == 3 else None,
        consent_record_id=consent.id,
    )
    db.add(case)
    db.flush()

    db.add(GovernmentDocumentReference(
        user_id=user_id,
        verification_case_id=case.id,
        document_type_code_id=doc_type_id,
        masked_identifier=f"XXXX-XXXX-{idx:04d}",
        issuing_country_id=1,
        status_code_id=1,
    ))
    db.flush()
    return case
