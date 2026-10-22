"""Migration 012_government_id_and_extensions: Government ID Verification & Optional Extensions (M12/M13: 14 tables)

Revision ID: 012_government_id_and_extensions
Revises: 011_analytics_reporting_marts
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '012_government_id_and_extensions'
down_revision: Union[str, None] = '011_analytics_reporting_marts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation for Government ID Verification & Optional Extensions (M12/M13: 14 tables) (14 tables)
    op.execute("""
CREATE TABLE IF NOT EXISTS "identity_verification_case" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "document_type_code_id" bigint NOT NULL,
  "provider_code" varchar(80) NOT NULL,
  "provider_case_reference" varchar(255),
  "status_code_id" bigint NOT NULL,
  "requested_at" timestamptz NOT NULL,
  "completed_at" timestamptz,
  "consent_record_id" bigint NOT NULL,
  "provider_token_ciphertext" bytea,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_identity_verification_case_provider_code" UNIQUE ("provider_code"),
  CONSTRAINT "fk_identity_verification_case_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_identity_verification_case_consent_record_id" FOREIGN KEY ("consent_record_id") REFERENCES "consent_record"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "government_document_reference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "verification_case_id" bigint NOT NULL,
  "document_type_code_id" bigint NOT NULL,
  "masked_identifier" varchar(80) NOT NULL,
  "identifier_fingerprint" char(64),
  "encrypted_identifier_reference" varchar(255),
  "issuing_country_id" bigint NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_government_document_reference_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "identity_verification_provider" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "provider_code" varchar(80) NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "enabled" boolean NOT NULL DEFAULT false,
  "configuration_reference" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_identity_verification_provider_provider_code" UNIQUE ("provider_code")
);

CREATE TABLE IF NOT EXISTS "identity_verification_event" (
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

CREATE TABLE IF NOT EXISTS "verification_review" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "provider_code" varchar(80),
  "provider_reference" varchar(255),
  "masked_identifier" varchar(80),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_verification_review_provider_code" UNIQUE ("provider_code"),
  CONSTRAINT "fk_verification_review_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "verification_access_log" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "verification_case_id" bigint NOT NULL,
  "actor_user_id" bigint NOT NULL,
  "action_code" varchar(100) NOT NULL,
  "occurred_at" timestamptz NOT NULL,
  "outcome_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "verification_consent_purpose" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "provider_code" varchar(80),
  "provider_reference" varchar(255),
  "masked_identifier" varchar(80),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_verification_consent_purpose_provider_code" UNIQUE ("provider_code"),
  CONSTRAINT "fk_verification_consent_purpose_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "verification_provider_event" (
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

CREATE TABLE IF NOT EXISTS "verification_retention_job" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "provider_code" varchar(80),
  "provider_reference" varchar(255),
  "masked_identifier" varchar(80),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_verification_retention_job_provider_code" UNIQUE ("provider_code"),
  CONSTRAINT "fk_verification_retention_job_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "salary_benchmark" (
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

CREATE TABLE IF NOT EXISTS "trending_job_snapshot" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_requirement_id" bigint,
  "job_application_id" bigint,
  "candidate_profile_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_trending_job_snapshot_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_trending_job_snapshot_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_trending_job_snapshot_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "feature_flag" (
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

CREATE TABLE IF NOT EXISTS "dashboard_aggregate_config" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "source_business_key" varchar(100) NOT NULL,
  "snapshot_at" timestamptz NOT NULL,
  "measure_value" numeric(20,4),
  "source_watermark" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "organisation_rating_aggregate" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "source_business_key" varchar(100) NOT NULL,
  "snapshot_at" timestamptz NOT NULL,
  "measure_value" numeric(20,4),
  "source_watermark" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);
    """)


def downgrade() -> None:
    # Warning: Destructive rollback. All data in these tables will be removed.
    op.execute('DROP TABLE IF EXISTS "organisation_rating_aggregate" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dashboard_aggregate_config" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "feature_flag" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "trending_job_snapshot" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "salary_benchmark" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "verification_retention_job" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "verification_provider_event" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "verification_consent_purpose" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "verification_access_log" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "verification_review" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "identity_verification_event" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "identity_verification_provider" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "government_document_reference" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "identity_verification_case" CASCADE;')
