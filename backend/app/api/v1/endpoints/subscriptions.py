"""Subscriptions, Wallet & Payments FastAPI Endpoints (Module M09).

Audited against:
- Talentra Database Blueprint 150+ Tables (Module: M09 Subscriptions, Wallet, Payments & Downloads)
- Talentra Final Test Cases: FR-0124 through FR-0138, FR-0206
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionPlanResponse,
    PlanEntitlementResponse,
    SubscriptionCreate,
    SubscriptionCancelRequest,
    SubscriptionResponse,
    WalletResponse,
    WalletCreditRequest,
    WalletDebitRequest,
    WalletCorrectionRequest,
    WalletLedgerEntryResponse,
    PaymentOrderCreate,
    PaymentOrderResponse,
    PaymentTransactionResponse,
    PaymentWebhookPayload,
    RefundCreate,
    RefundResponse,
    InvoiceResponse,
    ProfileDownloadRequest,
    ProfileDownloadResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Subscriptions, Wallet & Payments"])


# =========================================================================
# 1. Plans & Subscriptions (FR-0124, FR-0135, FR-0137)
# =========================================================================

@router.get("/subscriptions/plans", response_model=List[SubscriptionPlanResponse])
def get_plans(
    db: Session = Depends(get_db),
):
    """Retrieve available public subscription plans with entitlements."""
    plans = SubscriptionService.get_subscription_plans(db)
    res = []
    for p in plans:
        entitlements_data = [
            PlanEntitlementResponse(
                id=e.id,
                plan_id=p.id,
                feature_key=e.code,
                entitlement_type="FEATURE",
                limit_value=None,
                is_unlimited=True,
                created_at=e.created_at,
            )
            for e in p.entitlements if e.deleted_at is None
        ]
        res.append(
            SubscriptionPlanResponse(
                id=p.id,
                plan_code=p.plan_code,
                plan_name=p.name,
                description=None,
                billing_cycle_code_id=p.billing_interval_code_id,
                price_amount=p.price_amount,
                currency_code=p.currency_code,
                max_seats=10,
                max_candidates_search=1000,
                profile_download_quota=50,
                is_active=p.active,
                is_public=True,
                display_order=1,
                created_at=p.created_at,
                updated_at=p.updated_at,
                entitlements=entitlements_data,
            )
        )
    return res


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0124: Create a subscription with period validity and licence non-overlap check."""
    try:
        sub = SubscriptionService.create_subscription(
            db=db,
            account_id=payload.account_id,
            plan_id=payload.plan_id,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            licence_id=payload.licence_id,
            auto_renew=payload.auto_renew,
            actor_user_id=current_user.id,
        )
        return SubscriptionResponse(
            id=sub.id,
            account_id=sub.account_id,
            plan_id=sub.subscription_plan_id,
            licence_id=sub.licence_id or 0,
            subscription_status_code_id=sub.status_code_id,
            starts_at=sub.starts_at,
            ends_at=sub.ends_at,
            auto_renew=sub.auto_renew,
            renewal_count=0,
            seats_allocated=payload.seats_allocated,
            cancelled_at=sub.cancelled_at,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    payload: SubscriptionCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0135: Cancel a subscription recording cancelled_at and preserving payment history."""
    try:
        sub = SubscriptionService.cancel_subscription(
            db=db,
            subscription_id=subscription_id,
            reason=payload.reason,
            actor_user_id=current_user.id,
        )
        return SubscriptionResponse(
            id=sub.id,
            account_id=sub.account_id,
            plan_id=sub.subscription_plan_id,
            licence_id=sub.licence_id or 0,
            subscription_status_code_id=sub.status_code_id,
            starts_at=sub.starts_at,
            ends_at=sub.ends_at,
            auto_renew=sub.auto_renew,
            renewal_count=0,
            seats_allocated=1,
            cancelled_at=sub.cancelled_at,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/subscriptions/entitlements/check")
def check_subscription_entitlement(
    account_id: int = Query(...),
    feature_key: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0137: Enforce active subscription entitlements for features."""
    has_entitlement = SubscriptionService.check_entitlement(db, account_id, feature_key)
    if not has_entitlement:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account {account_id} does not have an active entitlement for '{feature_key}' (FR-0137)",
        )
    return {"account_id": account_id, "feature_key": feature_key, "granted": True}


# =========================================================================
# 2. Wallet & Ledger (FR-0127, FR-0128, FR-0129, FR-0130, FR-0131, FR-0138, FR-0206)
# =========================================================================

@router.get("/wallet/{account_id}", response_model=WalletResponse)
def get_account_wallet(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0128: Get wallet with balance calculated as the algebraic sum of ledger entries."""
    wallet = SubscriptionService.get_or_create_wallet(db, account_id, actor_user_id=current_user.id)
    calculated_balance = SubscriptionService.get_wallet_balance(db, wallet.id)
    return WalletResponse(
        id=wallet.id,
        account_id=wallet.account_id,
        balance_amount=calculated_balance,
        currency_code=wallet.currency_code,
        wallet_status_code_id=wallet.status_code_id,
        is_locked=False,
        overdraft_limit=Decimal("0.00"),
        created_at=wallet.created_at,
        updated_at=wallet.updated_at,
    )


@router.post("/wallet/{wallet_id}/credit", response_model=WalletLedgerEntryResponse)
def credit_wallet(
    wallet_id: int,
    payload: WalletCreditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0125, FR-0127, FR-0128, FR-0129: Post an append-only credit entry to the wallet."""
    try:
        entry = SubscriptionService.credit_wallet(
            db=db,
            wallet_id=wallet_id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            source_type=payload.source_reference or "MANUAL_CREDIT",
            source_id="1",
            currency_code=payload.currency_code,
            actor_user_id=current_user.id,
        )
        balance = SubscriptionService.get_wallet_balance(db, wallet_id)
        return WalletLedgerEntryResponse(
            id=entry.id,
            wallet_id=entry.wallet_id,
            entry_type_code_id=entry.entry_type_code_id,
            direction_code_id=1,  # CREDIT
            amount=entry.amount,
            balance_after=balance,
            currency_code=entry.currency_code,
            idempotency_key=entry.idempotency_key,
            reference_type=entry.source_type,
            reference_id=entry.source_id,
            description=payload.description,
            original_entry_id=entry.original_entry_id,
            created_at=entry.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/wallet/{wallet_id}/debit", response_model=WalletLedgerEntryResponse)
def debit_wallet(
    wallet_id: int,
    payload: WalletDebitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0130, FR-0131: Concurrency-safe atomic debit enforcing credit minimums."""
    try:
        entry = SubscriptionService.debit_wallet(
            db=db,
            wallet_id=wallet_id,
            amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            source_type=payload.source_reference or "USAGE",
            source_id="1",
            currency_code=payload.currency_code,
            actor_user_id=current_user.id,
        )
        balance = SubscriptionService.get_wallet_balance(db, wallet_id)
        return WalletLedgerEntryResponse(
            id=entry.id,
            wallet_id=entry.wallet_id,
            entry_type_code_id=entry.entry_type_code_id,
            direction_code_id=2,  # DEBIT
            amount=entry.amount,
            balance_after=balance,
            currency_code=entry.currency_code,
            idempotency_key=entry.idempotency_key,
            reference_type=entry.source_type,
            reference_id=entry.source_id,
            description=payload.description,
            original_entry_id=entry.original_entry_id,
            created_at=entry.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/wallet/ledger/correction", response_model=WalletLedgerEntryResponse)
def correct_wallet_ledger(
    payload: WalletCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0129, FR-0138, FR-0206: Post a compensating correction entry referencing original without modifying it."""
    try:
        entry = SubscriptionService.correct_wallet_ledger(
            db=db,
            original_entry_id=payload.original_entry_id,
            adjustment_amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            reason=payload.reason,
            actor_user_id=current_user.id,
        )
        balance = SubscriptionService.get_wallet_balance(db, entry.wallet_id)
        return WalletLedgerEntryResponse(
            id=entry.id,
            wallet_id=entry.wallet_id,
            entry_type_code_id=entry.entry_type_code_id,
            direction_code_id=1 if entry.amount >= 0 else 2,
            amount=entry.amount,
            balance_after=balance,
            currency_code=entry.currency_code,
            idempotency_key=entry.idempotency_key,
            reference_type=entry.source_type,
            reference_id=entry.source_id,
            description=payload.reason,
            original_entry_id=entry.original_entry_id,
            created_at=entry.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/wallet/download-profile", response_model=ProfileDownloadResponse)
def download_candidate_profile(
    payload: ProfileDownloadRequest,
    account_id: int = Query(...),
    organisation_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0130, FR-0132: Deduct credits and log append-only profile download history."""
    try:
        history, consumption = SubscriptionService.download_candidate_profile(
            db=db,
            account_id=account_id,
            recruiter_user_id=current_user.id,
            candidate_profile_id=payload.candidate_id,
            organisation_id=organisation_id,
            credits_cost=Decimal("1.00"),
        )
        return ProfileDownloadResponse(
            id=history.id,
            account_id=account_id,
            user_id=current_user.id,
            candidate_id=payload.candidate_id,
            credits_consumed=1,
            download_format=payload.download_format,
            purpose=payload.purpose,
            downloaded_at=history.downloaded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# 3. Payments & Invoices (FR-0125, FR-0126, FR-0127, FR-0133, FR-0134, FR-0136)
# =========================================================================

@router.post("/payments/orders", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_payment_order(
    payload: PaymentOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0125, FR-0126, FR-0127: Create payment order with durable idempotency."""
    order = SubscriptionService.create_payment_order(
        db=db,
        account_id=payload.account_id,
        amount=payload.amount,
        currency_code=payload.currency_code,
        idempotency_key=payload.idempotency_key,
        provider_code=payload.provider_code,
        actor_user_id=current_user.id,
    )
    return PaymentOrderResponse(
        id=order.id,
        order_reference=order.provider_order_reference or f"ord_{order.id}",
        account_id=order.account_id,
        subscription_id=payload.subscription_id,
        provider_order_id=order.provider_order_reference,
        amount=order.amount,
        currency_code=order.currency_code,
        order_status_code_id=order.status_code_id,
        idempotency_key=order.idempotency_key,
        description=payload.description,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("/payments/webhook")
def process_payment_webhook(
    payload: PaymentWebhookPayload,
    db: Session = Depends(get_db),
):
    """FR-0125, FR-0126, FR-0136: Ingest payment gateway webhooks idempotently without sensitive card storage."""
    try:
        trans = SubscriptionService.process_payment_webhook(
            db=db,
            event_id=payload.event_id,
            provider_order_reference=payload.order_reference,
            provider_transaction_reference=payload.gateway_transaction_id,
            status=payload.status,
            amount=payload.amount,
            currency_code=payload.currency_code,
            idempotency_key=f"wh-{payload.event_id}",
        )
        return {
            "status": "processed",
            "transaction_id": trans.id,
            "status_code_id": trans.status_code_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/refund", response_model=RefundResponse)
def process_refund(
    payload: RefundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0133: Issue refund referencing original payment transaction bounded by remaining refundable amount."""
    try:
        ref = SubscriptionService.process_refund(
            db=db,
            payment_transaction_id=payload.payment_transaction_id,
            refund_amount=payload.amount,
            idempotency_key=payload.idempotency_key,
            reason=payload.reason,
            actor_user_id=current_user.id,
        )
        return RefundResponse(
            id=ref.id,
            payment_transaction_id=ref.payment_transaction_id or 0,
            refund_reference=f"ref_{ref.id}",
            amount=ref.amount,
            currency_code=ref.currency_code,
            status_code_id=ref.status_code_id,
            reason=ref.reason,
            idempotency_key=ref.idempotency_key,
            created_at=ref.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/payments/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    account_id: int = Query(...),
    subtotal: Decimal = Query(...),
    tax_rate: Decimal = Query(Decimal("0.10")),
    subscription_id: Optional[int] = Query(None),
    currency_code: str = Query("USD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """FR-0134: Generate invoice where subtotal + tax = total with decimal rounding."""
    invoice = SubscriptionService.generate_invoice(
        db=db,
        account_id=account_id,
        subtotal=subtotal,
        tax_rate=tax_rate,
        subscription_id=subscription_id,
        currency_code=currency_code,
        actor_user_id=current_user.id,
    )
    return InvoiceResponse(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        account_id=invoice.account_id,
        subscription_id=invoice.subscription_id,
        order_id=None,
        subtotal_amount=invoice.subtotal_amount,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        currency_code=invoice.currency_code,
        invoice_status_code_id=1,
        due_date=datetime.combine(invoice.due_on, datetime.min.time()) if invoice.due_on else None,
        paid_at=None,
        invoice_pdf_url=None,
        created_at=invoice.created_at,
        lines=[],
    )
