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