CREATE TABLE IF NOT EXISTS "organisation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_type_code_id" bigint NOT NULL,
  "legal_name" varchar(200) NOT NULL,
  "display_name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "parent_organisation_id" bigint,
  "primary_country_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_parent_organisation_id" FOREIGN KEY ("parent_organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_identifier" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint NOT NULL,
  "country_id" bigint NOT NULL,
  "identifier_type_code_id" bigint NOT NULL,
  "identifier_ciphertext" bytea NOT NULL,
  "identifier_fingerprint" char(64) NOT NULL,
  "masked_identifier" varchar(80) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_identifier_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_identifier_country_id" FOREIGN KEY ("country_id") REFERENCES "country"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_recruiter_mapping" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint NOT NULL,
  "recruiter_user_id" bigint NOT NULL,
  "valid_from" timestamptz NOT NULL,
  "valid_until" timestamptz,
  "assigned_by_user_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_recruiter_mapping_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "account" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_code" varchar(80) NOT NULL,
  "account_name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "root_organisation_id" bigint NOT NULL,
  "billing_currency_code" char(3) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_account_account_code" UNIQUE ("account_code")
);

CREATE TABLE IF NOT EXISTS "account_organisation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_account_organisation_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_account_organisation_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "account_admin_assignment" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_account_admin_assignment_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_account_admin_assignment_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_contact" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_contact_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_contact_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_review" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_review_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_review_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_status_history_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_domain" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_domain_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_domain_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_document_reference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_document_reference_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_document_reference_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "account_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_account_status_history_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_hierarchy_closure" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_hierarchy_closure_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_hierarchy_closure_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_profile" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_profile_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_profile_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_location" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_location_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_location_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_verification" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint,
  "account_id" bigint,
  "name" varchar(200) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "valid_from" timestamptz,
  "valid_until" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_verification_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_organisation_verification_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "organisation_verification_event" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_verification_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_organisation_verification_event_organisation_verification_id" FOREIGN KEY ("organisation_verification_id") REFERENCES "organisation_verification"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);