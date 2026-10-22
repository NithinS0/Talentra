"""Migration 011_analytics_reporting_marts: Analytics Reporting Marts & Star Schema (M11: 16 tables)

Revision ID: 011_analytics_reporting_marts
Revises: 010_notifications_and_community
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '011_analytics_reporting_marts'
down_revision: Union[str, None] = '010_notifications_and_community'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation for Analytics Reporting Marts & Star Schema (M11: 16 tables) (16 tables)
    op.execute("""
CREATE TABLE IF NOT EXISTS "dim_date" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "date_key" integer NOT NULL,
  "calendar_date" date NOT NULL,
  "year_number" smallint NOT NULL,
  "quarter_number" smallint NOT NULL,
  "month_number" smallint NOT NULL,
  "day_number" smallint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "dim_organisation" (
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

CREATE TABLE IF NOT EXISTS "dim_candidate" (
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

CREATE TABLE IF NOT EXISTS "dim_job" (
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

CREATE TABLE IF NOT EXISTS "dim_status" (
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

CREATE TABLE IF NOT EXISTS "fact_application" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "date_key" integer NOT NULL,
  "candidate_dimension_id" bigint NOT NULL,
  "job_dimension_id" bigint NOT NULL,
  "status_dimension_id" bigint NOT NULL,
  "application_count" integer NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "fact_job_requirement" (
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

CREATE TABLE IF NOT EXISTS "fact_gig_assignment" (
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

CREATE TABLE IF NOT EXISTS "fact_wallet_transaction" (
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

CREATE TABLE IF NOT EXISTS "fact_notification_delivery" (
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

CREATE TABLE IF NOT EXISTS "aggregate_dashboard_daily" (
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

CREATE TABLE IF NOT EXISTS "analytics_refresh_run" (
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

CREATE TABLE IF NOT EXISTS "analytics_kpi_definition" (
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

CREATE TABLE IF NOT EXISTS "fact_profile_activity" (
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

CREATE TABLE IF NOT EXISTS "fact_profile_download" (
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

CREATE TABLE IF NOT EXISTS "analytics_data_quality_issue" (
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
    """)


def downgrade() -> None:
    # Warning: Destructive rollback. All data in these tables will be removed.
    op.execute('DROP TABLE IF EXISTS "analytics_data_quality_issue" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_profile_download" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_profile_activity" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "analytics_kpi_definition" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "analytics_refresh_run" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "aggregate_dashboard_daily" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_notification_delivery" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_wallet_transaction" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_gig_assignment" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_job_requirement" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "fact_application" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dim_status" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dim_job" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dim_candidate" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dim_organisation" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "dim_date" CASCADE;')
