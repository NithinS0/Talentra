CREATE TABLE IF NOT EXISTS "sourcing_request" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_requirement_id" bigint NOT NULL,
  "requester_user_id" bigint NOT NULL,
  "consultant_user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "open_to_consultants_snapshot" boolean NOT NULL,
  "requested_at" timestamptz NOT NULL,
  "responded_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_sourcing_request_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "consultant_request_decision" (
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

CREATE TABLE IF NOT EXISTS "outreach_batch" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint NOT NULL,
  "created_by_user_id" bigint NOT NULL,
  "job_requirement_id" bigint,
  "status_code_id" bigint NOT NULL,
  "recipient_count" integer NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_outreach_batch_recipient_count_positive" CHECK (recipient_count >= 0),
  CONSTRAINT "fk_outreach_batch_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_outreach_batch_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "outreach_recipient" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "outreach_batch_id" bigint NOT NULL,
  "candidate_profile_id" bigint NOT NULL,
  "delivery_status_code_id" bigint NOT NULL,
  "provider_message_reference" varchar(255),
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_outreach_recipient_outreach_batch_id" FOREIGN KEY ("outreach_batch_id") REFERENCES "outreach_batch"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_outreach_recipient_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_sourcing_shortlist" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint,
  "user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "title" varchar(180),
  "description" varchar(4000),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_sourcing_shortlist_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_sourcing_shortlist_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "sourcing_request_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "sourcing_request_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_sourcing_request_status_history_sourcing_request_id" FOREIGN KEY ("sourcing_request_id") REFERENCES "sourcing_request"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_contact_attempt" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_contact_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_contact_attempt_candidate_contact_id" FOREIGN KEY ("candidate_contact_id") REFERENCES "candidate_contact"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "consultant_profile" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint,
  "user_id" bigint,
  "status_code_id" bigint NOT NULL,
  "title" varchar(180),
  "description" varchar(4000),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_consultant_profile_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_consultant_profile_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "consultant_skill" (
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

CREATE TABLE IF NOT EXISTS "consultant_rate_card" (
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

CREATE TABLE IF NOT EXISTS "outreach_consent_check" (
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

CREATE TABLE IF NOT EXISTS "consultant_request_assignment_history" (
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