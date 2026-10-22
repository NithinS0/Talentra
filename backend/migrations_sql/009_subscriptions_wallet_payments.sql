CREATE TABLE IF NOT EXISTS "subscription_plan" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "plan_code" varchar(80) NOT NULL,
  "name" varchar(150) NOT NULL,
  "price_amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "billing_interval_code_id" bigint NOT NULL,
  "active" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_plan_plan_code" UNIQUE ("plan_code"),
  CONSTRAINT "uq_subscription_plan_currency_code" UNIQUE ("currency_code")
);

CREATE TABLE IF NOT EXISTS "plan_entitlement" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "code" varchar(80),
  "name" varchar(180),
  "status_code_id" bigint NOT NULL,
  "description" varchar(2000),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "subscription" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "subscription_plan_id" bigint NOT NULL,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz NOT NULL,
  "ends_at" timestamptz NOT NULL,
  "auto_renew" boolean NOT NULL DEFAULT false,
  "cancelled_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_subscription_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "ck_subscription_period_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_subscription_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_subscription_subscription_plan_id" FOREIGN KEY ("subscription_plan_id") REFERENCES "subscription_plan"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_subscription_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "subscription_renewal" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_renewal_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_subscription_renewal_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "subscription_cancellation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_cancellation_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_subscription_cancellation_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_order" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "payment_provider_code" varchar(80) NOT NULL,
  "provider_order_reference" varchar(255),
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_order_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_order_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_transaction" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "payment_order_id" bigint NOT NULL,
  "provider_transaction_reference" varchar(255),
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_transaction_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_transaction_payment_order_id" FOREIGN KEY ("payment_order_id") REFERENCES "payment_order"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "subscription_id" bigint,
  "invoice_number" varchar(80) NOT NULL,
  "issued_on" date NOT NULL,
  "due_on" date,
  "subtotal_amount" numeric(14,2) NOT NULL,
  "tax_amount" numeric(14,2) NOT NULL,
  "total_amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_invoice_invoice_number" UNIQUE ("invoice_number"),
  CONSTRAINT "uq_invoice_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_invoice_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_invoice_subscription_id" FOREIGN KEY ("subscription_id") REFERENCES "subscription"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice_line" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_invoice_line_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_invoice_line_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_refund" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_refund_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_refund_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "wallet" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "wallet_ledger_entry" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "wallet_id" bigint NOT NULL,
  "entry_type_code_id" bigint NOT NULL,
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "source_type" varchar(80) NOT NULL,
  "source_id" varchar(100) NOT NULL,
  "original_entry_id" bigint,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_ledger_entry_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_ledger_entry_wallet_id" FOREIGN KEY ("wallet_id") REFERENCES "wallet"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "credit_consumption" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_credit_consumption_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_credit_consumption_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "profile_download_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "actor_user_id" bigint NOT NULL,
  "organisation_id" bigint NOT NULL,
  "downloaded_at" timestamptz NOT NULL,
  "credit_consumption_id" bigint,
  "request_id" uuid,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_profile_download_history_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_profile_download_history_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_profile_download_history_credit_consumption_id" FOREIGN KEY ("credit_consumption_id") REFERENCES "credit_consumption"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_webhook_event" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "wallet_balance_snapshot" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_balance_snapshot_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_balance_snapshot_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "invoice_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_invoice_status_history_invoice_id" FOREIGN KEY ("invoice_id") REFERENCES "invoice"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_reconciliation_run" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_reconciliation_run_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_reconciliation_run_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);