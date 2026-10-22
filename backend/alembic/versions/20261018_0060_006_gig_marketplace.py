"""Migration 006_gig_marketplace: Gig Marketplace (M06: 15 tables)

Revision ID: 006_gig_marketplace
Revises: 005_jobs_and_applications
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_gig_marketplace'
down_revision: Union[str, None] = '005_jobs_and_applications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation for Gig Marketplace (M06: 15 tables) (15 tables)
    op.execute("""
CREATE TABLE IF NOT EXISTS "gig_worker_profile" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "bio" varchar(3000),
  "availability_status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_worker_profile_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_request" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "requester_organisation_id" bigint NOT NULL,
  "created_by_user_id" bigint NOT NULL,
  "title" varchar(180) NOT NULL,
  "description" text NOT NULL,
  "starts_at" timestamptz NOT NULL,
  "ends_at" timestamptz NOT NULL,
  "pricing_type_code_id" bigint NOT NULL,
  "price_amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_request_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_request_timestamp_range" CHECK (ends_at >= starts_at)
);

CREATE TABLE IF NOT EXISTS "gig_application" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint NOT NULL,
  "gig_worker_profile_id" bigint NOT NULL,
  "applied_at" timestamptz NOT NULL,
  "status_code_id" bigint NOT NULL,
  "decided_by_user_id" bigint,
  "decided_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_application_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_application_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_assignment" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_application_id" bigint NOT NULL,
  "requester_organisation_id" bigint NOT NULL,
  "gig_worker_profile_id" bigint NOT NULL,
  "starts_at" timestamptz NOT NULL,
  "ends_at" timestamptz NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_gig_assignment_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_assignment_gig_application_id" FOREIGN KEY ("gig_application_id") REFERENCES "gig_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_assignment_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_handoff_reference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_assignment_id" bigint NOT NULL,
  "fulfilment_provider_code" varchar(80) NOT NULL,
  "external_handoff_reference" varchar(255) NOT NULL,
  "handoff_status_code_id" bigint NOT NULL,
  "last_reconciled_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_handoff_reference_gig_assignment_id" FOREIGN KEY ("gig_assignment_id") REFERENCES "gig_assignment"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_earnings_reconciliation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_earnings_reconciliation_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_earnings_reconciliation_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_earnings_reconciliation_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_earnings_reconciliation_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_worker_list_entry" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_worker_list_entry_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_worker_list_entry_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_worker_list_entry_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_worker_list_entry_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_rating" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_rating_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_rating_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_rating_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_rating_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_request_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_request_status_history_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_application_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_application_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_application_status_history_gig_application_id" FOREIGN KEY ("gig_application_id") REFERENCES "gig_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_assignment_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_assignment_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_gig_assignment_status_history_gig_assignment_id" FOREIGN KEY ("gig_assignment_id") REFERENCES "gig_assignment"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_worker_favourite_history" (
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

CREATE TABLE IF NOT EXISTS "gig_service_offering" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_service_offering_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_service_offering_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_service_offering_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_service_offering_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_worker_skill" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_worker_skill_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_worker_skill_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_worker_skill_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_worker_skill_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "gig_worker_availability" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "gig_request_id" bigint,
  "gig_worker_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz,
  "ends_at" timestamptz,
  "currency_code" char(3),
  "amount" numeric(14,2),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_gig_worker_availability_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "ck_gig_worker_availability_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_gig_worker_availability_gig_request_id" FOREIGN KEY ("gig_request_id") REFERENCES "gig_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_gig_worker_availability_gig_worker_profile_id" FOREIGN KEY ("gig_worker_profile_id") REFERENCES "gig_worker_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);
    """)


def downgrade() -> None:
    # Warning: Destructive rollback. All data in these tables will be removed.
    op.execute('DROP TABLE IF EXISTS "gig_worker_availability" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_worker_skill" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_service_offering" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_worker_favourite_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_assignment_status_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_application_status_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_request_status_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_rating" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_worker_list_entry" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_earnings_reconciliation" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_handoff_reference" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_assignment" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_application" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_request" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "gig_worker_profile" CASCADE;')
