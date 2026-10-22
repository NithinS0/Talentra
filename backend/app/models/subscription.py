"""Subscriptions, Wallet, Payments, and Downloads Models.

Implements M09 Subscriptions, Wallet, Payments & Downloads tables aligned to PostgreSQL migration 009 and blueprint:
- subscription_plan
- plan_entitlement
- subscription
- subscription_renewal
- subscription_cancellation
- payment_order
- payment_transaction
- invoice
- invoice_line
- payment_refund
- wallet
- wallet_ledger_entry
- credit_consumption
- profile_download_history
- payment_webhook_event
- wallet_balance_snapshot
- invoice_status_history
- payment_reconciliation_run
"""

from typing import Optional, List
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import (
    BigInteger,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
    JSON,
    CheckConstraint,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SubscriptionPlan(Base):
    """Catalog of subscription tiers with pricing and billing intervals."""

    __tablename__ = "subscription_plan"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    plan_code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    billing_interval_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=MONTHLY, 2=ANNUAL
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
    entitlements = relationship("PlanEntitlement", back_populates="plan", cascade="all, delete-orphan")


class PlanEntitlement(Base):
    """Specific feature/entitlement permissions mapped to a subscription plan."""

    __tablename__ = "plan_entitlement"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_plan_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("subscription_plan.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=INACTIVE
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    plan = relationship("SubscriptionPlan", back_populates="entitlements")


class Subscription(Base):
    """Active customer account subscription linked to a plan and optional licence."""

    __tablename__ = "subscription"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    subscription_plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("subscription_plan.id"), nullable=False, index=True)
    licence_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("licence.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=CANCELLED, 3=EXPIRED, 4=SUSPENDED, 5=PENDING_PAYMENT
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("ends_at >= starts_at", name="ck_subscription_timestamp_range"),
    )

    # Relationships
    account = relationship("Account", backref="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    licence = relationship("Licence", backref="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")


class SubscriptionRenewal(Base):
    """Log of subscription renewal events and idempotency keys."""

    __tablename__ = "subscription_renewal"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("subscription.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SubscriptionCancellation(Base):
    """Audit log of subscription cancellations with effective timestamp and rationale."""

    __tablename__ = "subscription_cancellation"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("subscription.id"), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentOrder(Base):
    """Payment order initiated with gateway provider (Stripe, Razorpay, Mock)."""

    __tablename__ = "payment_order"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    payment_provider_code: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_order_reference: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=PENDING, 2=SUCCEEDED, 3=FAILED, 4=CANCELLED
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account")
    transactions = relationship("PaymentTransaction", back_populates="order", cascade="all, delete-orphan")


class PaymentTransaction(Base):
    """Immutable ledger of payment provider transactions (FR-0126, FR-0206)."""

    __tablename__ = "payment_transaction"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    payment_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("payment_order.id"), nullable=False, index=True)
    provider_transaction_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=SUCCEEDED, 2=FAILED, 3=PENDING, 4=REFUNDED
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("PaymentOrder", back_populates="transactions")


class Invoice(Base):
    """Tax invoice generated for subscriptions or credit purchases (FR-0134)."""

    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("subscription.id"), nullable=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    due_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account")
    subscription = relationship("Subscription", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    status_history = relationship("InvoiceStatusHistory", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    """Individual line item within an invoice."""

    __tablename__ = "invoice_line"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("invoice.id"), nullable=True, index=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="lines")


class InvoiceStatusHistory(Base):
    """Lifecycle history of invoice transitions."""

    __tablename__ = "invoice_status_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("invoice.id"), nullable=False, index=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="status_history")


class PaymentRefund(Base):
    """Refund transaction linked to a source payment (FR-0133)."""

    __tablename__ = "payment_refund"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    payment_transaction_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("payment_transaction.id"), nullable=True, index=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=COMPLETED, 2=PENDING, 3=FAILED
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    payment_transaction = relationship("PaymentTransaction")


class Wallet(Base):
    """Account credits and prepaid balance wallet container (FR-0128)."""

    __tablename__ = "wallet"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=False, index=True)
    currency_code: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=ACTIVE, 2=FROZEN, 3=CLOSED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account")
    ledger_entries = relationship("WalletLedgerEntry", back_populates="wallet", cascade="all, delete-orphan")


class WalletLedgerEntry(Base):
    """Append-only financial transaction ledger (FR-0128, FR-0129, FR-0138, FR-0206)."""

    __tablename__ = "wallet_ledger_entry"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    wallet_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wallet.id"), nullable=False, index=True)
    entry_type_code_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 1=CREDIT, 2=DEBIT, 3=REFUND, 4=CORRECTION
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    original_entry_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("wallet_ledger_entry.id"), nullable=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="ledger_entries")
    original_entry = relationship("WalletLedgerEntry", remote_side=[id])


class CreditConsumption(Base):
    """Usage log when deducting credits for actions like candidate profile downloads (FR-0130, FR-0132)."""

    __tablename__ = "credit_consumption"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=SUCCESS, 2=FAILED
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ProfileDownloadHistory(Base):
    """Append-only history of candidate profile downloads by recruiters/employers (FR-0132)."""

    __tablename__ = "profile_download_history"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    candidate_profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("candidate_profile.id"), nullable=False, index=True)
    actor_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id"), nullable=False, index=True)
    organisation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("organisation.id"), nullable=False, index=True)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    credit_consumption_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("credit_consumption.id"), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    candidate_profile = relationship("CandidateProfile")
    actor_user = relationship("User")
    organisation = relationship("Organisation")
    credit_consumption = relationship("CreditConsumption")


class PaymentWebhookEvent(Base):
    """Audit log of raw external payment webhooks received and processed (FR-0125, FR-0136)."""

    __tablename__ = "payment_webhook_event"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    event_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)  # 1=RECEIVED, 2=PROCESSED, 3=FAILED, 4=DUPLICATE_IGNORED
    actor_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_redacted: Mapped[Optional[dict]] = mapped_column(JSON().with_variant(JSON, "sqlite"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class WalletBalanceSnapshot(Base):
    """Materialized snapshot of wallet balance for reconciliation audits (FR-0128)."""

    __tablename__ = "wallet_balance_snapshot"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class PaymentReconciliationRun(Base):
    """Audit of scheduled or manual financial balance reconciliation jobs."""

    __tablename__ = "payment_reconciliation_run"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("account.id"), nullable=True)
    status_code_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
