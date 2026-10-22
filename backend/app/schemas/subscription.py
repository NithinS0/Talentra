"""Pydantic Schemas for Module M09: Subscriptions, Wallet & Payments.

Compliant with:
- FR-0124: Subscription period validity (ends_at >= starts_at, non-overlapping active periods per licence)
- FR-0125: Payment idempotency (duplicate orders/callbacks handled idempotently)
- FR-0126: No card/bank data storage (zero PAN/CVV, only masked metadata and provider references)
- FR-0127: Money decimal precision (Numeric(14, 2) + ISO 4217 companion currency code)
- FR-0128: Wallet balance consistency (balance equals algebraic sum of ledger entries)
- FR-0129: Append-only wallet ledger (updates/deletes prohibited; corrections reference original_entry_id)
- FR-0130: Insufficient credit deduction (atomic rejection without partial/negative balance)
- FR-0131: Concurrent wallet deductions (atomic balance check and deduction under row lock)
- FR-0132: Profile download history (append-only history linked to credit consumption)
- FR-0133: Refund references original payment (cannot exceed refundable amount)
- FR-0134: Invoice totals (subtotal + tax = total, decimal rounded)
- FR-0135: Subscription cancellation (records cancelled_at, preserves payment history)
- FR-0136: Payment failure recovery (timeout recovery doesn't duplicate charges)
- FR-0137: Entitlement enforcement (active subscription entitlement gates features)
- FR-0138: Wallet ledger correction linkage (correction points to original_entry_id)
- FR-0206: Payment ledger correction never overwrites original (immutable ledger history)
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. Plan & Entitlement Schemas
# ==========================================

class PlanEntitlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    feature_key: str
    entitlement_type: str
    limit_value: Optional[int] = None
    is_unlimited: bool = False
    created_at: datetime


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_code: str
    plan_name: str
    description: Optional[str] = None
    billing_cycle_code_id: int
    price_amount: Decimal
    currency_code: str
    max_seats: int
    max_candidates_search: Optional[int] = None
    profile_download_quota: Optional[int] = None
    is_active: bool
    is_public: bool
    display_order: int
    created_at: datetime
    updated_at: datetime
    entitlements: List[PlanEntitlementResponse] = []


# ==========================================
# 2. Subscription Schemas
# ==========================================

class SubscriptionCreate(BaseModel):
    account_id: int
    plan_id: int
    licence_id: int
    starts_at: datetime
    ends_at: datetime
    auto_renew: bool = False
    seats_allocated: int = Field(default=1, ge=1)

    @field_validator("ends_at")
    @classmethod
    def validate_dates(cls, v: datetime, info) -> datetime:
        starts_at = info.data.get("starts_at")
        if starts_at and v <= starts_at:
            raise ValueError("ends_at must be strictly greater than starts_at (FR-0124)")
        return v


class SubscriptionCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
    cancellation_effective_date: Optional[datetime] = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    plan_id: int
    licence_id: int
    subscription_status_code_id: int
    starts_at: datetime
    ends_at: datetime
    auto_renew: bool
    renewal_count: int
    seats_allocated: int
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ==========================================
# 3. Wallet & Ledger Schemas
# ==========================================

class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    balance_amount: Decimal
    currency_code: str
    wallet_status_code_id: int
    is_locked: bool
    overdraft_limit: Decimal
    created_at: datetime
    updated_at: datetime


class WalletCreditRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Positive decimal credit amount (FR-0127)")
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    source_reference: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=120)


class WalletDebitRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Positive decimal debit amount (FR-0127)")
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    purpose: Optional[str] = Field(None, max_length=80)
    source_reference: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=120)


class WalletCorrectionRequest(BaseModel):
    original_entry_id: int = Field(..., description="ID of entry being corrected (FR-0138, FR-0206)")
    amount: Decimal = Field(..., decimal_places=2, description="Signed adjustment amount")
    reason: str = Field(..., min_length=5, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=120)


class WalletLedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wallet_id: int
    entry_type_code_id: int
    direction_code_id: int
    amount: Decimal
    balance_after: Decimal
    currency_code: str
    idempotency_key: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    original_entry_id: Optional[int] = None
    created_at: datetime


# ==========================================
# 4. Payment Order & Transaction Schemas
# ==========================================

class PaymentOrderCreate(BaseModel):
    account_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    provider_code: str = Field(default="STRIPE", max_length=50)
    idempotency_key: str = Field(..., min_length=8, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    subscription_id: Optional[int] = None


class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_reference: str
    account_id: int
    subscription_id: Optional[int] = None
    provider_order_id: Optional[str] = None
    amount: Decimal
    currency_code: str
    order_status_code_id: int
    idempotency_key: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PaymentTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    gateway_transaction_id: str
    provider_code: str
    amount: Decimal
    currency_code: str
    transaction_type_code_id: int
    status_code_id: int
    masked_card_number: Optional[str] = None
    card_brand: Optional[str] = None
    idempotency_key: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: datetime


class PaymentWebhookPayload(BaseModel):
    event_id: str = Field(..., min_length=3, max_length=120)
    event_type: str = Field(..., min_length=3, max_length=80)
    provider_code: str = Field(default="STRIPE", max_length=50)
    order_reference: str = Field(..., min_length=3, max_length=80)
    gateway_transaction_id: str = Field(..., min_length=3, max_length=120)
    status: str = Field(..., description="SUCCEEDED, FAILED, PENDING")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency_code: str = Field(default="USD", min_length=3, max_length=3)
    signature: Optional[str] = None
    error_message: Optional[str] = None


class RefundCreate(BaseModel):
    payment_transaction_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reason: str = Field(..., min_length=3, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=120)


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_transaction_id: int
    refund_reference: str
    amount: Decimal
    currency_code: str
    status_code_id: int
    reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    created_at: datetime


# ==========================================
# 5. Invoice Schemas
# ==========================================

class InvoiceLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    line_number: int
    description: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal
    tax_amount: Decimal


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    account_id: int
    subscription_id: Optional[int] = None
    order_id: Optional[int] = None
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency_code: str
    invoice_status_code_id: int
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_pdf_url: Optional[str] = None
    created_at: datetime
    lines: List[InvoiceLineResponse] = []


# ==========================================
# 6. Profile Download & Credit Schemas
# ==========================================

class ProfileDownloadRequest(BaseModel):
    candidate_id: int
    download_format: str = Field(default="PDF", max_length=20)
    purpose: Optional[str] = Field(None, max_length=120)


class ProfileDownloadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    user_id: int
    candidate_id: int
    credits_consumed: int
    download_format: str
    purpose: Optional[str] = None
    downloaded_at: datetime
