export interface PlanEntitlementResponse {
  id: number;
  plan_id: number;
  feature_key: string;
  entitlement_type: string;
  limit_value?: number | null;
  is_unlimited: boolean;
  created_at: string;
}

export interface SubscriptionPlanResponse {
  id: number;
  plan_code: string;
  plan_name: string;
  description?: string | null;
  billing_cycle_code_id: number;
  price_amount: number | string;
  currency_code: string;
  max_seats: number;
  max_candidates_search?: number | null;
  profile_download_quota?: number | null;
  is_active: boolean;
  is_public: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
  entitlements: PlanEntitlementResponse[];
}

export interface SubscriptionCreatePayload {
  account_id: number;
  plan_id: number;
  licence_id: number;
  starts_at: string;
  ends_at: string;
  auto_renew?: boolean;
  seats_allocated?: number;
}

export interface SubscriptionCancelPayload {
  reason: string;
  cancellation_effective_date?: string | null;
}

export interface SubscriptionResponse {
  id: number;
  account_id: number;
  plan_id: number;
  licence_id: number;
  subscription_status_code_id: number;
  starts_at: string;
  ends_at: string;
  auto_renew: boolean;
  renewal_count: number;
  seats_allocated: number;
  cancelled_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WalletResponse {
  id: number;
  account_id: number;
  balance_amount: number | string;
  currency_code: string;
  wallet_status_code_id: number;
  is_locked: boolean;
  overdraft_limit: number | string;
  created_at: string;
  updated_at: string;
}

export interface WalletCreditPayload {
  amount: number | string;
  currency_code?: string;
  source_reference?: string;
  description?: string;
  idempotency_key: string;
}

export interface WalletDebitPayload {
  amount: number | string;
  currency_code?: string;
  purpose?: string;
  source_reference?: string;
  description?: string;
  idempotency_key: string;
}

export interface WalletCorrectionPayload {
  original_entry_id: number;
  amount: number | string;
  reason: string;
  idempotency_key: string;
}

export interface WalletLedgerEntryResponse {
  id: number;
  wallet_id: number;
  entry_type_code_id: number;
  direction_code_id: number;
  amount: number | string;
  balance_after: number | string;
  currency_code: string;
  idempotency_key?: string | null;
  reference_type?: string | null;
  reference_id?: string | null;
  description?: string | null;
  original_entry_id?: number | null;
  created_at: string;
}

export interface PaymentOrderCreatePayload {
  account_id: number;
  amount: number | string;
  currency_code?: string;
  provider_code?: string;
  idempotency_key: string;
  description?: string;
  subscription_id?: number;
}

export interface PaymentOrderResponse {
  id: number;
  order_reference: string;
  account_id: number;
  subscription_id?: number | null;
  provider_order_id?: string | null;
  amount: number | string;
  currency_code: string;
  order_status_code_id: number;
  idempotency_key?: string | null;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RefundCreatePayload {
  payment_transaction_id: number;
  amount: number | string;
  reason: string;
  idempotency_key: string;
}

export interface RefundResponse {
  id: number;
  payment_transaction_id: number;
  refund_reference: string;
  amount: number | string;
  currency_code: string;
  status_code_id: number;
  reason?: string | null;
  idempotency_key?: string | null;
  created_at: string;
}

export interface InvoiceLineResponse {
  id: number;
  invoice_id: number;
  line_number: number;
  description: string;
  quantity: number;
  unit_price: number | string;
  line_total: number | string;
  tax_rate: number | string;
  tax_amount: number | string;
}

export interface InvoiceResponse {
  id: number;
  invoice_number: string;
  account_id: number;
  subscription_id?: number | null;
  order_id?: number | null;
  subtotal_amount: number | string;
  tax_amount: number | string;
  total_amount: number | string;
  currency_code: string;
  invoice_status_code_id: number;
  due_date?: string | null;
  paid_at?: string | null;
  invoice_pdf_url?: string | null;
  created_at: string;
  lines: InvoiceLineResponse[];
}

export interface ProfileDownloadPayload {
  candidate_id: number;
  download_format?: string;
  purpose?: string;
}

export interface ProfileDownloadResponse {
  id: number;
  account_id: number;
  user_id: number;
  candidate_id: number;
  credits_consumed: number;
  download_format: string;
  purpose?: string | null;
  downloaded_at: string;
}
