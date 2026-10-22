CREATE TABLE IF NOT EXISTS "licence" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "licence_code" varchar(80) NOT NULL,
  "account_id" bigint NOT NULL,
  "max_users" integer NOT NULL,
  "max_devices_per_user" integer NOT NULL,
  "valid_from" timestamptz NOT NULL,
  "valid_until" timestamptz NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_licence_licence_code" UNIQUE ("licence_code"),
  CONSTRAINT "ck_licence_max_users_positive" CHECK (max_users > 0),
  CONSTRAINT "ck_licence_max_devices_per_user_positive" CHECK (max_devices_per_user > 0),
  CONSTRAINT "fk_licence_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "licence_seat_allocation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "expires_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_licence_seat_allocation_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_licence_seat_allocation_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "registered_device" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "device_fingerprint_hash" char(64) NOT NULL,
  "device_label" varchar(150),
  "first_seen_at" timestamptz NOT NULL,
  "last_seen_at" timestamptz NOT NULL,
  "revoked_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_registered_device_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "device_revocation_event" (
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

CREATE TABLE IF NOT EXISTS "session_revocation_event" (
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

CREATE TABLE IF NOT EXISTS "licence_usage_snapshot" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "expires_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_licence_usage_snapshot_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_licence_usage_snapshot_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "login_device_decision" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "expires_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_login_device_decision_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_login_device_decision_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "session_activity_event" (
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

CREATE TABLE IF NOT EXISTS "licence_entitlement" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "expires_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_licence_entitlement_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_licence_entitlement_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "licence_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "licence_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_licence_status_history_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "device_login_counter" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "occurred_at" timestamptz,
  "expires_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_device_login_counter_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_device_login_counter_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);