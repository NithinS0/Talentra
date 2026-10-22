"""Migration 010_notifications_and_community: Notifications, Preferences & Community (M10: 18 tables)

Revision ID: 010_notifications_and_community
Revises: 009_subscriptions_wallet_payments
Create Date: 2026-10-18 14:00:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '010_notifications_and_community'
down_revision: Union[str, None] = '009_subscriptions_wallet_payments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema creation for Notifications, Preferences & Community (M10: 18 tables) (18 tables)
    op.execute("""
CREATE TABLE IF NOT EXISTS "notification_preference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "notification_type_code_id" bigint NOT NULL,
  "channel_code_id" bigint NOT NULL,
  "enabled" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_notification_preference_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_alert_preference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "setting_code_id" bigint NOT NULL,
  "setting_value" jsonb,
  "enabled" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_job_alert_preference_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "privacy_preference" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "setting_code_id" bigint NOT NULL,
  "setting_value" jsonb,
  "enabled" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_privacy_preference_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "notification" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "setting_code_id" bigint NOT NULL,
  "setting_value" jsonb,
  "enabled" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_notification_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "notification_delivery" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "notification_id" bigint NOT NULL,
  "channel_code_id" bigint NOT NULL,
  "provider_code" varchar(80) NOT NULL,
  "delivery_status_code_id" bigint NOT NULL,
  "attempt_count" integer NOT NULL,
  "provider_message_reference" varchar(255),
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_notification_delivery_provider_code" UNIQUE ("provider_code"),
  CONSTRAINT "ck_notification_delivery_attempt_count_positive" CHECK (attempt_count >= 0),
  CONSTRAINT "fk_notification_delivery_notification_id" FOREIGN KEY ("notification_id") REFERENCES "notification"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "notification_template" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "setting_code_id" bigint NOT NULL,
  "setting_value" jsonb,
  "enabled" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_notification_template_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "community_post" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "author_user_id" bigint NOT NULL,
  "title" varchar(200) NOT NULL,
  "body" varchar(10000) NOT NULL,
  "language_id" bigint,
  "moderation_status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_community_post_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "community_reaction" (
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

CREATE TABLE IF NOT EXISTS "community_comment" (
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

CREATE TABLE IF NOT EXISTS "support_ticket" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "requester_user_id" bigint NOT NULL,
  "ticket_number" varchar(80) NOT NULL,
  "subject" varchar(200) NOT NULL,
  "description" varchar(8000) NOT NULL,
  "priority_code_id" bigint NOT NULL,
  "status_code_id" bigint NOT NULL,
  "assigned_to_user_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_support_ticket_ticket_number" UNIQUE ("ticket_number")
);

CREATE TABLE IF NOT EXISTS "support_ticket_message" (
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

CREATE TABLE IF NOT EXISTS "faq" (
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

CREATE TABLE IF NOT EXISTS "referral_event" (
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

CREATE TABLE IF NOT EXISTS "social_share_event" (
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

CREATE TABLE IF NOT EXISTS "notification_delivery_attempt" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "notification_delivery_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_notification_delivery_attempt_notification_delivery_id" FOREIGN KEY ("notification_delivery_id") REFERENCES "notification_delivery"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "notification_preference_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "notification_preference_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_notification_preference_history_notification_preference_id" FOREIGN KEY ("notification_preference_id") REFERENCES "notification_preference"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "support_ticket_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "support_ticket_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_support_ticket_status_history_support_ticket_id" FOREIGN KEY ("support_ticket_id") REFERENCES "support_ticket"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "community_moderation_event" (
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
    """)


def downgrade() -> None:
    # Warning: Destructive rollback. All data in these tables will be removed.
    op.execute('DROP TABLE IF EXISTS "community_moderation_event" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "support_ticket_status_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification_preference_history" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification_delivery_attempt" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "social_share_event" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "referral_event" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "faq" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "support_ticket_message" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "support_ticket" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "community_comment" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "community_reaction" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "community_post" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification_template" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification_delivery" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "privacy_preference" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "job_alert_preference" CASCADE;')
    op.execute('DROP TABLE IF EXISTS "notification_preference" CASCADE;')
