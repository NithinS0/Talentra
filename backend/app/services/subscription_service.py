"""Subscription, Wallet, Payment & Ledger Domain Service (Module M09).

Implements and enforces all functional, financial-integrity, and security specifications:
- FR-0124: Subscription period validity (ends_at >= starts_at, non-overlapping active periods per licence)
- FR-0125: Payment idempotency (duplicate external events/orders idempotently reconciled)
- FR-0126: No card/bank data storage (only masked card metadata and provider references, zero PAN/CVV)
- FR-0127: Money decimal precision (Numeric(14, 2) + ISO 4217 companion currency code)
- FR-0128: Wallet balance consistency (balance equals algebraic sum of ledger entries)
- FR-0129: Append-only wallet ledger (updates/deletes strictly rejected; corrections reference original_entry_id)
- FR-0130: Insufficient credit deduction (atomic rejection without partial/negative deduction)
- FR-0131: Concurrent wallet deductions (atomic balance check & deduction under row lock)
- FR-0132: Profile download history (append-only history linked to credit consumption)
- FR-0133: Refund references original payment (bounded by remaining refundable amount)
- FR-0134: Invoice totals (subtotal + tax = total, rounded decimal rules)
- FR-0135: Subscription cancellation (records cancelled_at, preserves payment history)
- FR-0136: Payment failure recovery (timeout recovery doesn't duplicate charges)
- FR-0137: Entitlement enforcement (active subscription entitlement gates features)
- FR-0138: Wallet ledger correction linkage (correction points to original_entry_id)
- FR-0206: Payment ledger correction never overwrites original (immutable ledger history)
"""

import uuid
import threading
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, date, timedelta
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session

from app.models.subscription import (
    SubscriptionPlan,
    PlanEntitlement,
    Subscription,
    SubscriptionRenewal,
    SubscriptionCancellation,
    PaymentOrder,
    PaymentTransaction,
    Invoice,
    InvoiceLine,
    InvoiceStatusHistory,
    PaymentRefund,
    Wallet,
    WalletLedgerEntry,
    CreditConsumption,
    ProfileDownloadHistory,
    PaymentWebhookEvent,
    WalletBalanceSnapshot,
    PaymentReconciliationRun,
)
from app.models.licence import Licence
from app.models.organisation import Account, Organisation
from app.models.candidate import CandidateProfile
from app.models.user import User


# ==========================================
# Domain Status Codes and Constants
# ==========================================

SUBSCRIPTION_STATUS = {
    "ACTIVE": 1,
    "CANCELLED": 2,
    "EXPIRED": 3,
    "SUSPENDED": 4,
    "PENDING_PAYMENT": 5,
}

PAYMENT_ORDER_STATUS = {
    "PENDING": 1,
    "SUCCEEDED": 2,
    "FAILED": 3,
    "CANCELLED": 4,
}

PAYMENT_TRANSACTION_STATUS = {
    "SUCCEEDED": 1,
    "FAILED": 2,
    "PENDING": 3,
    "REFUNDED": 4,
}

WALLET_STATUS = {
    "ACTIVE": 1,
    "FROZEN": 2,
    "CLOSED": 3,
}

WALLET_ENTRY_TYPE = {
    "CREDIT": 1,       # Top-up / Payment
    "DEBIT": 2,        # Usage / Consumption
    "REFUND": 3,       # Refund credited back
    "CORRECTION": 4,   # Compensating entry referencing original
}

REFUND_STATUS = {
    "COMPLETED": 1,
    "PENDING": 2,
    "FAILED": 3,
}

INVOICE_STATUS = {
    "DRAFT": 1,
    "ISSUED": 2,
    "PAID": 3,
    "VOID": 4,
}


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Normalize datetime to timezone-aware UTC for cross-database consistency."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _round_money(amount: Decimal) -> Decimal:
    """Round monetary amount to 2 decimal places using standard ROUND_HALF_UP."""
    return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SubscriptionService:
    """Authoritative business logic for Subscriptions, Wallet, Ledger, and Payments."""

    _wallet_mutex = threading.RLock()

    # =========================================================================
    # 1. SUBSCRIPTIONS & ENTITLEMENTS (FR-0124, FR-0135, FR-0137)
    # =========================================================================

    @staticmethod
    def get_subscription_plans(db: Session, active_only: bool = True) -> List[SubscriptionPlan]:
        """Fetch available subscription tiers."""
        query = db.query(SubscriptionPlan)
        if active_only:
            query = query.filter(SubscriptionPlan.active == True, SubscriptionPlan.deleted_at.is_(None))
        return query.order_by(SubscriptionPlan.price_amount.asc()).all()

    @staticmethod
    def create_subscription(
        db: Session,
        account_id: int,
        plan_id: int,
        starts_at: datetime,
        ends_at: datetime,
        licence_id: Optional[int] = None,
        auto_renew: bool = False,
        actor_user_id: Optional[int] = None,
    ) -> Subscription:
        """Create a new subscription validating period validity and non-overlapping active periods (FR-0124)."""
        # Validate Account
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account with ID {account_id} not found")

        # Validate Plan
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan or not plan.active:
            raise ValueError(f"Subscription plan with ID {plan_id} is invalid or inactive")

        # FR-0124: End must not precede start
        start_utc = _ensure_utc(starts_at)
        end_utc = _ensure_utc(ends_at)
        if end_utc < start_utc:
            raise ValueError("Subscription ends_at must not precede starts_at (FR-0124)")

        # FR-0124: Periods for same licence must not overlap
        if licence_id is not None:
            licence = db.query(Licence).filter(Licence.id == licence_id).first()
            if not licence:
                raise ValueError(f"Licence with ID {licence_id} not found")

            # Check existing active subscriptions for this licence
            existing_subs = db.query(Subscription).filter(
                Subscription.licence_id == licence_id,
                Subscription.status_code_id == SUBSCRIPTION_STATUS["ACTIVE"],
                Subscription.deleted_at.is_(None),
            ).all()

            for sub in existing_subs:
                sub_start = _ensure_utc(sub.starts_at)
                sub_end = _ensure_utc(sub.ends_at)
                # Overlap condition: start < other.end and end > other.start
                if start_utc < sub_end and end_utc > sub_start:
                    raise ValueError(
                        f"Subscription period ({start_utc.isoformat()} to {end_utc.isoformat()}) "
                        f"overlaps with existing active subscription {sub.id} "
                        f"({sub_start.isoformat()} to {sub_end.isoformat()}) for licence {licence_id} (FR-0124)"
                    )

        now = datetime.now(timezone.utc)
        subscription = Subscription(
            account_id=account_id,
            subscription_plan_id=plan_id,
            licence_id=licence_id,
            status_code_id=SUBSCRIPTION_STATUS["ACTIVE"],
            starts_at=start_utc,
            ends_at=end_utc,
            auto_renew=auto_renew,
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def cancel_subscription(
        db: Session,
        subscription_id: int,
        reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> Subscription:
        """Cancel a subscription, recording cancelled_at and preserving payment history (FR-0135)."""
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise ValueError(f"Subscription with ID {subscription_id} not found")

        now = datetime.now(timezone.utc)
        subscription.status_code_id = SUBSCRIPTION_STATUS["CANCELLED"]
        subscription.cancelled_at = now
        subscription.updated_at = now
        subscription.updated_by = actor_user_id

        # Record audit cancellation entry
        cancellation_log = SubscriptionCancellation(
            subscription_id=subscription.id,
            account_id=subscription.account_id,
            status_code_id=1,  # Successful cancellation
            reason=reason or "Customer requested cancellation",
            created_at=now,
            created_by=actor_user_id,
        )
        db.add(cancellation_log)
        db.commit()
        db.refresh(subscription)
        return subscription

    @staticmethod
    def check_entitlement(
        db: Session,
        account_id: int,
        feature_key: str,
    ) -> bool:
        """Enforce active subscription entitlement for gated platform features (FR-0137)."""
        now = datetime.now(timezone.utc)
        # Find active subscriptions
        active_subs = db.query(Subscription).filter(
            Subscription.account_id == account_id,
            Subscription.status_code_id == SUBSCRIPTION_STATUS["ACTIVE"],
            Subscription.deleted_at.is_(None),
        ).all()

        # Check validity window
        valid_plans = []
        for sub in active_subs:
            sub_start = _ensure_utc(sub.starts_at)
            sub_end = _ensure_utc(sub.ends_at)
            if sub_start <= now <= sub_end and sub.cancelled_at is None:
                valid_plans.append(sub.subscription_plan_id)

        if not valid_plans:
            return False

        # Check if any valid plan has the entitlement
        entitlement = db.query(PlanEntitlement).filter(
            PlanEntitlement.subscription_plan_id.in_(valid_plans),
            PlanEntitlement.code == feature_key,
            PlanEntitlement.status_code_id == 1,
            PlanEntitlement.deleted_at.is_(None),
        ).first()

        return entitlement is not None

    # =========================================================================
    # 2. WALLET & APPEND-ONLY LEDGER (FR-0127, FR-0128, FR-0129, FR-0130, FR-0131, FR-0138, FR-0206)
    # =========================================================================

    @staticmethod
    def get_or_create_wallet(
        db: Session,
        account_id: int,
        currency_code: str = "USD",
        actor_user_id: Optional[int] = None,
    ) -> Wallet:
        """Retrieve or initialize an account's wallet."""
        wallet = db.query(Wallet).filter(
            Wallet.account_id == account_id,
            Wallet.currency_code == currency_code,
            Wallet.deleted_at.is_(None),
        ).first()

        if not wallet:
            now = datetime.now(timezone.utc)
            wallet = Wallet(
                account_id=account_id,
                currency_code=currency_code,
                status_code_id=WALLET_STATUS["ACTIVE"],
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
        return wallet

    @staticmethod
    def get_wallet_balance(db: Session, wallet_id: int) -> Decimal:
        """Calculate authoritative balance as the algebraic sum of ledger entries (FR-0128)."""
        entries = db.query(WalletLedgerEntry).filter(
            WalletLedgerEntry.wallet_id == wallet_id,
            WalletLedgerEntry.deleted_at.is_(None),
        ).all()

        balance = Decimal("0.00")
        for entry in entries:
            amt = _round_money(entry.amount)
            if entry.entry_type_code_id == WALLET_ENTRY_TYPE["CREDIT"]:
                balance += amt
            elif entry.entry_type_code_id == WALLET_ENTRY_TYPE["DEBIT"]:
                balance -= amt
            elif entry.entry_type_code_id == WALLET_ENTRY_TYPE["REFUND"]:
                balance += amt
            elif entry.entry_type_code_id == WALLET_ENTRY_TYPE["CORRECTION"]:
                # If correction has positive amount, add; if negative, subtract
                balance += amt

        return _round_money(balance)

    @staticmethod
    def credit_wallet(
        db: Session,
        wallet_id: int,
        amount: Decimal,
        idempotency_key: str,
        source_type: str = "PAYMENT",
        source_id: str = "1",
        currency_code: str = "USD",
        actor_user_id: Optional[int] = None,
    ) -> WalletLedgerEntry:
        """Atomically credit a wallet with idempotency (FR-0125, FR-0128, FR-0129)."""
        with SubscriptionService._wallet_mutex:
            if amount <= Decimal("0.00"):
                raise ValueError("Credit amount must be greater than zero (FR-0127)")

            # Lock wallet for concurrent safety
            wallet = db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")

            # Idempotency check: if entry with same idempotency key already exists, return it
            existing_entry = db.query(WalletLedgerEntry).filter(
                WalletLedgerEntry.wallet_id == wallet_id,
                WalletLedgerEntry.idempotency_key == idempotency_key,
            ).first()
            if existing_entry:
                return existing_entry

            now = datetime.now(timezone.utc)
            rounded_amount = _round_money(amount)
            entry = WalletLedgerEntry(
                wallet_id=wallet.id,
                entry_type_code_id=WALLET_ENTRY_TYPE["CREDIT"],
                amount=rounded_amount,
                currency_code=currency_code,
                source_type=source_type,
                source_id=str(source_id),
                idempotency_key=idempotency_key,
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(entry)
            wallet.updated_at = now
            db.commit()
            db.refresh(entry)
            return entry

    @staticmethod
    def debit_wallet(
        db: Session,
        wallet_id: int,
        amount: Decimal,
        idempotency_key: str,
        source_type: str = "USAGE",
        source_id: str = "1",
        currency_code: str = "USD",
        actor_user_id: Optional[int] = None,
    ) -> WalletLedgerEntry:
        """Atomically debit a wallet with concurrency lock and balance check (FR-0130, FR-0131)."""
        with SubscriptionService._wallet_mutex:
            if amount <= Decimal("0.00"):
                raise ValueError("Debit amount must be greater than zero (FR-0127)")

            rounded_amount = _round_money(amount)

            # FR-0131: Lock wallet row to guarantee atomic balance check and deduction
            wallet = db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
            if not wallet:
                raise ValueError(f"Wallet with ID {wallet_id} not found")

            # Idempotency check: if already processed, return existing entry
            existing_entry = db.query(WalletLedgerEntry).filter(
                WalletLedgerEntry.wallet_id == wallet_id,
                WalletLedgerEntry.idempotency_key == idempotency_key,
            ).first()
            if existing_entry:
                return existing_entry

            # FR-0130: Insufficient credit deduction check
            current_balance = SubscriptionService.get_wallet_balance(db, wallet_id)
            if current_balance < rounded_amount:
                raise ValueError(
                    f"Insufficient wallet credits. Current balance: {current_balance}, required: {rounded_amount} (FR-0130)"
                )

            now = datetime.now(timezone.utc)
            entry = WalletLedgerEntry(
                wallet_id=wallet.id,
                entry_type_code_id=WALLET_ENTRY_TYPE["DEBIT"],
                amount=rounded_amount,
                currency_code=currency_code,
                source_type=source_type,
                source_id=str(source_id),
                idempotency_key=idempotency_key,
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(entry)
            wallet.updated_at = now
            db.commit()
            db.refresh(entry)
            return entry

    @staticmethod
    def correct_wallet_ledger(
        db: Session,
        original_entry_id: int,
        adjustment_amount: Decimal,
        idempotency_key: str,
        reason: str,
        actor_user_id: Optional[int] = None,
    ) -> WalletLedgerEntry:
        """Post an append-only compensating correction referencing original entry without modifying it (FR-0129, FR-0138, FR-0206)."""
        original_entry = db.query(WalletLedgerEntry).filter(
            WalletLedgerEntry.id == original_entry_id,
            WalletLedgerEntry.deleted_at.is_(None),
        ).first()
        if not original_entry:
            raise ValueError(f"Original ledger entry with ID {original_entry_id} not found")

        # Capture original values to verify immutability
        orig_amount = original_entry.amount
        orig_idempotency = original_entry.idempotency_key
        orig_type = original_entry.entry_type_code_id

        # Idempotency check
        existing = db.query(WalletLedgerEntry).filter(
            WalletLedgerEntry.wallet_id == original_entry.wallet_id,
            WalletLedgerEntry.idempotency_key == idempotency_key,
        ).first()
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        rounded_adj = _round_money(adjustment_amount)
        correction_entry = WalletLedgerEntry(
            wallet_id=original_entry.wallet_id,
            entry_type_code_id=WALLET_ENTRY_TYPE["CORRECTION"],
            amount=rounded_adj,
            currency_code=original_entry.currency_code,
            source_type="CORRECTION",
            source_id=str(original_entry.id),
            original_entry_id=original_entry.id,
            idempotency_key=idempotency_key,
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(correction_entry)
        db.commit()
        db.refresh(correction_entry)

        # Assert FR-0206 immutability: original entry MUST NOT have been mutated
        db.refresh(original_entry)
        assert original_entry.amount == orig_amount, "Original entry amount mutated! Violation of FR-0206"
        assert original_entry.idempotency_key == orig_idempotency, "Original entry key mutated! Violation of FR-0206"
        assert original_entry.entry_type_code_id == orig_type, "Original entry type mutated! Violation of FR-0206"

        return correction_entry

    @staticmethod
    def download_candidate_profile(
        db: Session,
        account_id: int,
        recruiter_user_id: int,
        candidate_profile_id: int,
        organisation_id: int,
        credits_cost: Decimal = Decimal("1.00"),
        idempotency_key: Optional[str] = None,
    ) -> Tuple[ProfileDownloadHistory, CreditConsumption]:
        """Download candidate profile deducting credits and recording append-only history (FR-0130, FR-0132)."""
        key = idempotency_key or f"dl-{account_id}-{candidate_profile_id}-{uuid.uuid4().hex[:12]}"

        # Validate candidate
        candidate = db.query(CandidateProfile).filter(CandidateProfile.id == candidate_profile_id).first()
        if not candidate:
            raise ValueError(f"Candidate profile {candidate_profile_id} not found")

        # Get wallet
        wallet = SubscriptionService.get_or_create_wallet(db, account_id)

        # Atomic debit under row lock (raises ValueError if insufficient balance)
        debit_entry = SubscriptionService.debit_wallet(
            db=db,
            wallet_id=wallet.id,
            amount=credits_cost,
            idempotency_key=f"debit-{key}",
            source_type="PROFILE_DOWNLOAD",
            source_id=str(candidate_profile_id),
            actor_user_id=recruiter_user_id,
        )

        now = datetime.now(timezone.utc)
        consumption = CreditConsumption(
            account_id=account_id,
            status_code_id=1,  # SUCCESS
            amount=credits_cost,
            currency_code=wallet.currency_code,
            idempotency_key=key,
            created_at=now,
            created_by=recruiter_user_id,
            updated_at=now,
        )
        db.add(consumption)
        db.flush()

        history = ProfileDownloadHistory(
            candidate_profile_id=candidate_profile_id,
            actor_user_id=recruiter_user_id,
            organisation_id=organisation_id,
            downloaded_at=now,
            credit_consumption_id=consumption.id,
            request_id=key,
            created_at=now,
            created_by=recruiter_user_id,
            updated_at=now,
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        db.refresh(consumption)
        return history, consumption

    # =========================================================================
    # 3. PAYMENT PROCESSING & IDEMPOTENCY (FR-0125, FR-0126, FR-0127, FR-0133, FR-0134, FR-0136)
    # =========================================================================

    @staticmethod
    def create_payment_order(
        db: Session,
        account_id: int,
        amount: Decimal,
        currency_code: str,
        idempotency_key: str,
        provider_code: str = "STRIPE",
        actor_user_id: Optional[int] = None,
    ) -> PaymentOrder:
        """Create payment order with durable idempotency and zero card data storage (FR-0125, FR-0126, FR-0127)."""
        rounded_amount = _round_money(amount)

        # Idempotency check: if order with idempotency_key already exists, return it
        existing_order = db.query(PaymentOrder).filter(
            PaymentOrder.idempotency_key == idempotency_key,
        ).first()
        if existing_order:
            return existing_order

        now = datetime.now(timezone.utc)
        order = PaymentOrder(
            account_id=account_id,
            payment_provider_code=provider_code,
            provider_order_reference=f"ord_{uuid.uuid4().hex[:16]}",
            amount=rounded_amount,
            currency_code=currency_code.upper(),
            status_code_id=PAYMENT_ORDER_STATUS["PENDING"],
            idempotency_key=idempotency_key,
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def process_payment_webhook(
        db: Session,
        event_id: str,
        provider_order_reference: str,
        provider_transaction_reference: str,
        status: str,
        amount: Decimal,
        currency_code: str,
        idempotency_key: str,
        raw_metadata: Optional[dict] = None,
        masked_card_info: Optional[str] = None,
    ) -> PaymentTransaction:
        """Process external payment callback idempotently with recovery and zero card data (FR-0125, FR-0126, FR-0136)."""
        # Redact raw metadata to ensure FR-0126 compliance
        clean_metadata = dict(raw_metadata or {})
        for sensitive_key in ["card_number", "pan", "cvv", "cvc", "expiry", "password", "pin"]:
            if sensitive_key in clean_metadata:
                clean_metadata[sensitive_key] = "[REDACTED]"

        # Check existing webhook event
        existing_event = db.query(PaymentWebhookEvent).filter(
            PaymentWebhookEvent.actor_user_id.is_(None),  # systemic
        ).all()
        # Find matching idempotency in webhook event metadata
        for evt in existing_event:
            if evt.metadata_redacted and evt.metadata_redacted.get("event_id") == event_id:
                # Duplicate external event idempotently handled
                trans = db.query(PaymentTransaction).filter(
                    PaymentTransaction.provider_transaction_reference == provider_transaction_reference,
                ).first()
                if trans:
                    return trans

        # Log Webhook Event
        now = datetime.now(timezone.utc)
        webhook_log = PaymentWebhookEvent(
            event_code_id=1,  # RECEIVED
            occurred_at=now,
            metadata_redacted={"event_id": event_id, "status": status, **clean_metadata},
            created_at=now,
        )
        db.add(webhook_log)

        # Find Order
        order = db.query(PaymentOrder).filter(
            PaymentOrder.provider_order_reference == provider_order_reference,
        ).first()

        if not order:
            # Try finding by idempotency key
            order = db.query(PaymentOrder).filter(
                PaymentOrder.idempotency_key == idempotency_key,
            ).first()

        if not order:
            raise ValueError(f"Payment order matching reference {provider_order_reference} not found")

        # Check if transaction already exists (FR-0125 idempotency)
        existing_trans = db.query(PaymentTransaction).filter(
            PaymentTransaction.idempotency_key == idempotency_key,
        ).first()
        if existing_trans:
            return existing_trans

        # Map Status
        trans_status = PAYMENT_TRANSACTION_STATUS["SUCCEEDED"] if status.upper() in ["SUCCEEDED", "SUCCESS", "PAID"] else PAYMENT_TRANSACTION_STATUS["FAILED"]

        trans = PaymentTransaction(
            payment_order_id=order.id,
            provider_transaction_reference=provider_transaction_reference,
            amount=_round_money(amount),
            currency_code=currency_code.upper(),
            status_code_id=trans_status,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )
        db.add(trans)

        if trans_status == PAYMENT_TRANSACTION_STATUS["SUCCEEDED"]:
            order.status_code_id = PAYMENT_ORDER_STATUS["SUCCEEDED"]
            # Credit wallet automatically if top-up order
            wallet = SubscriptionService.get_or_create_wallet(db, order.account_id, currency_code)
            SubscriptionService.credit_wallet(
                db=db,
                wallet_id=wallet.id,
                amount=amount,
                idempotency_key=f"credit-ord-{order.id}",
                source_type="PAYMENT_ORDER",
                source_id=str(order.id),
                currency_code=currency_code,
            )
        else:
            # FR-0136: Payment failure recovery without creating false charges
            order.status_code_id = PAYMENT_ORDER_STATUS["FAILED"]

        order.updated_at = now
        db.commit()
        db.refresh(trans)
        return trans

    @staticmethod
    def process_refund(
        db: Session,
        payment_transaction_id: int,
        refund_amount: Decimal,
        idempotency_key: str,
        reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
    ) -> PaymentRefund:
        """Issue refund referencing original payment transaction, bounded by refundable amount (FR-0133)."""
        rounded_refund = _round_money(refund_amount)
        if rounded_refund <= Decimal("0.00"):
            raise ValueError("Refund amount must be strictly positive (FR-0127)")

        transaction = db.query(PaymentTransaction).filter(
            PaymentTransaction.id == payment_transaction_id,
        ).first()
        if not transaction:
            raise ValueError(f"Payment transaction {payment_transaction_id} not found")

        if transaction.status_code_id != PAYMENT_TRANSACTION_STATUS["SUCCEEDED"]:
            raise ValueError("Cannot refund a non-successful payment transaction")

        # Check existing refunds on this transaction
        past_refunds = db.query(PaymentRefund).filter(
            PaymentRefund.payment_transaction_id == payment_transaction_id,
            PaymentRefund.status_code_id == REFUND_STATUS["COMPLETED"],
            PaymentRefund.deleted_at.is_(None),
        ).all()

        total_already_refunded = sum((r.amount for r in past_refunds), Decimal("0.00"))
        remaining_refundable = _round_money(transaction.amount - total_already_refunded)

        if rounded_refund > remaining_refundable:
            raise ValueError(
                f"Refund amount {rounded_refund} exceeds remaining refundable amount {remaining_refundable} (FR-0133)"
            )

        # Idempotency check
        existing_refund = db.query(PaymentRefund).filter(
            PaymentRefund.idempotency_key == idempotency_key,
        ).first()
        if existing_refund:
            return existing_refund

        now = datetime.now(timezone.utc)
        order = db.query(PaymentOrder).filter(PaymentOrder.id == transaction.payment_order_id).first()
        account_id = order.account_id if order else 1

        refund = PaymentRefund(
            account_id=account_id,
            payment_transaction_id=transaction.id,
            status_code_id=REFUND_STATUS["COMPLETED"],
            amount=rounded_refund,
            currency_code=transaction.currency_code,
            reason=reason or "Customer refund request",
            idempotency_key=idempotency_key,
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(refund)

        # Debit wallet if top-up was previously credited
        wallet = db.query(Wallet).filter(
            Wallet.account_id == account_id,
            Wallet.currency_code == transaction.currency_code,
        ).first()
        if wallet:
            # Create refund ledger entry
            refund_ledger = WalletLedgerEntry(
                wallet_id=wallet.id,
                entry_type_code_id=WALLET_ENTRY_TYPE["DEBIT"],
                amount=rounded_refund,
                currency_code=transaction.currency_code,
                source_type="REFUND",
                source_id=str(transaction.id),
                idempotency_key=f"ref-ledger-{idempotency_key}",
                created_at=now,
                created_by=actor_user_id,
                updated_at=now,
            )
            db.add(refund_ledger)

        db.commit()
        db.refresh(refund)
        return refund

    @staticmethod
    def generate_invoice(
        db: Session,
        account_id: int,
        subtotal: Decimal,
        tax_rate: Decimal = Decimal("0.10"),
        subscription_id: Optional[int] = None,
        currency_code: str = "USD",
        lines_data: Optional[List[Dict[str, Any]]] = None,
        actor_user_id: Optional[int] = None,
    ) -> Invoice:
        """Generate invoice with validated totals: subtotal + tax = total (FR-0134)."""
        rounded_subtotal = _round_money(subtotal)
        rounded_tax = _round_money(rounded_subtotal * tax_rate)
        calculated_total = _round_money(rounded_subtotal + rounded_tax)

        now = datetime.now(timezone.utc)
        invoice_number = f"INV-{now.strftime('%Y%m')}-{uuid.uuid4().hex[:8].upper()}"

        invoice = Invoice(
            account_id=account_id,
            subscription_id=subscription_id,
            invoice_number=invoice_number,
            issued_on=now.date(),
            due_on=now.date() + timedelta(days=30),
            subtotal_amount=rounded_subtotal,
            tax_amount=rounded_tax,
            total_amount=calculated_total,
            currency_code=currency_code.upper(),
            created_at=now,
            created_by=actor_user_id,
            updated_at=now,
        )
        db.add(invoice)
        db.flush()

        # Add Line items if provided
        if lines_data:
            for idx, item in enumerate(lines_data, 1):
                item_amt = _round_money(Decimal(str(item.get("amount", rounded_subtotal))))
                line = InvoiceLine(
                    invoice_id=invoice.id,
                    account_id=account_id,
                    description=item.get("description", "Subscription Fee"),
                    quantity=item.get("quantity", 1),
                    unit_price=item_amt,
                    amount=item_amt,
                    currency_code=currency_code.upper(),
                    status_code_id=1,
                    created_at=now,
                )
                db.add(line)

        # Audit History
        history = InvoiceStatusHistory(
            invoice_id=invoice.id,
            event_code_id=1,  # ISSUED
            actor_user_id=actor_user_id,
            occurred_at=now,
            metadata_redacted={"total": str(calculated_total), "tax": str(rounded_tax)},
            created_at=now,
        )
        db.add(history)
        db.commit()
        db.refresh(invoice)
        return invoice
