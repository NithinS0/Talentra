"""014_actor_ids_and_country_master

Revision ID: 014_actor_ids_and_country_master
Revises: 013_business_constraints_and_indexes
Create Date: 2026-10-20 12:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '014_actor_ids_and_country_master'
down_revision: Union[str, None] = '013_business_constraints_and_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sequences for all 9 actor prefixes
    op.execute("""
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_sa START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_ad START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_aa START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_gu START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_ca START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_em START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_re START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_co START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    CREATE SEQUENCE IF NOT EXISTS seq_actor_id_po START WITH 1 INCREMENT BY 1 MINVALUE 1 MAXVALUE 99999 NO CYCLE;
    """)

    # 2. Create allocate_actor_id function
    op.execute("""
    CREATE OR REPLACE FUNCTION allocate_actor_id(p_prefix text)
    RETURNS text AS $$
    DECLARE
        v_seq_name text;
        v_val bigint;
    BEGIN
        CASE p_prefix
            WHEN 'SA' THEN v_seq_name := 'seq_actor_id_sa';
            WHEN 'AD' THEN v_seq_name := 'seq_actor_id_ad';
            WHEN 'AA' THEN v_seq_name := 'seq_actor_id_aa';
            WHEN 'GU' THEN v_seq_name := 'seq_actor_id_gu';
            WHEN 'CA' THEN v_seq_name := 'seq_actor_id_ca';
            WHEN 'EM' THEN v_seq_name := 'seq_actor_id_em';
            WHEN 'RE' THEN v_seq_name := 'seq_actor_id_re';
            WHEN 'CO' THEN v_seq_name := 'seq_actor_id_co';
            WHEN 'PO' THEN v_seq_name := 'seq_actor_id_po';
            ELSE
                RAISE EXCEPTION 'Invalid actor prefix: %. Must be one of SA, AD, AA, GU, CA, EM, RE, CO, PO', p_prefix;
        END CASE;

        v_val := nextval(v_seq_name);
        IF v_val > 99999 THEN
            RAISE EXCEPTION 'Actor ID capacity exhausted for prefix % (limit 99999 reached)', p_prefix;
        END IF;

        RETURN p_prefix || lpad(v_val::text, 5, '0');
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 3. Create central user_actor_identity table
    op.execute("""
    CREATE TABLE IF NOT EXISTS "user_actor_identity" (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        "user_id" bigint NOT NULL,
        "role_id" bigint NOT NULL,
        "role_code" varchar(50) NOT NULL,
        "actor_prefix" char(2) NOT NULL,
        "actor_id" varchar(7) NOT NULL,
        "organisation_id" bigint,
        "is_active" boolean NOT NULL DEFAULT true,
        "created_at" timestamptz NOT NULL DEFAULT now(),
        "created_by" bigint,
        "updated_at" timestamptz NOT NULL DEFAULT now(),
        "updated_by" bigint,
        "deleted_at" timestamptz,
        CONSTRAINT "uq_user_actor_identity_actor_id" UNIQUE ("actor_id"),
        CONSTRAINT "uq_user_actor_identity_user_role_org" UNIQUE ("user_id", "role_id", "organisation_id"),
        CONSTRAINT "ck_user_actor_identity_format" CHECK ("actor_id" ~ '^[A-Z]{2}[0-9]{5}$'),
        CONSTRAINT "fk_user_actor_identity_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
        CONSTRAINT "fk_user_actor_identity_role_id" FOREIGN KEY ("role_id") REFERENCES "role"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
        CONSTRAINT "fk_user_actor_identity_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
    );
    CREATE INDEX IF NOT EXISTS "idx_user_actor_identity_user_id" ON "user_actor_identity" ("user_id");
    CREATE INDEX IF NOT EXISTS "idx_user_actor_identity_role_id" ON "user_actor_identity" ("role_id");
    CREATE INDEX IF NOT EXISTS "idx_user_actor_identity_organisation_id" ON "user_actor_identity" ("organisation_id");
    """)

    # 4. Alter user_role_assignment to include actor_id
    op.execute("""
    ALTER TABLE "user_role_assignment"
        ADD COLUMN IF NOT EXISTS "actor_id" varchar(7),
        ADD CONSTRAINT "uq_user_role_assignment_actor_id" UNIQUE ("actor_id"),
        ADD CONSTRAINT "ck_user_role_assignment_actor_id_format" CHECK ("actor_id" IS NULL OR "actor_id" ~ '^[A-Z]{2}[0-9]{5}$');
    """)

    # 5. Alter candidate_profile to include actor_id
    op.execute("""
    ALTER TABLE "candidate_profile"
        ADD COLUMN IF NOT EXISTS "actor_id" varchar(7),
        ADD CONSTRAINT "uq_candidate_profile_actor_id" UNIQUE ("actor_id"),
        ADD CONSTRAINT "ck_candidate_profile_actor_id_format" CHECK ("actor_id" IS NULL OR "actor_id" ~ '^CA[0-9]{5}$');
    """)

    # 6. Alter consultant_profile to include actor_id
    op.execute("""
    ALTER TABLE "consultant_profile"
        ADD COLUMN IF NOT EXISTS "actor_id" varchar(7),
        ADD CONSTRAINT "uq_consultant_profile_actor_id" UNIQUE ("actor_id"),
        ADD CONSTRAINT "ck_consultant_profile_actor_id_format" CHECK ("actor_id" IS NULL OR "actor_id" ~ '^CO[0-9]{5}$');
    """)

    # 7. Immutability trigger function and triggers
    op.execute("""
    CREATE OR REPLACE FUNCTION prevent_actor_id_modification()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.actor_id IS NOT NULL AND NEW.actor_id != OLD.actor_id THEN
            RAISE EXCEPTION 'Actor ID is immutable once assigned. Cannot change % to % on table %', 
                OLD.actor_id, NEW.actor_id, TG_TABLE_NAME;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_immutable_actor_id_user_actor
    BEFORE UPDATE OF actor_id ON "user_actor_identity"
    FOR EACH ROW EXECUTE FUNCTION prevent_actor_id_modification();

    CREATE TRIGGER trg_immutable_actor_id_role_assign
    BEFORE UPDATE OF actor_id ON "user_role_assignment"
    FOR EACH ROW EXECUTE FUNCTION prevent_actor_id_modification();

    CREATE TRIGGER trg_immutable_actor_id_candidate
    BEFORE UPDATE OF actor_id ON "candidate_profile"
    FOR EACH ROW EXECUTE FUNCTION prevent_actor_id_modification();

    CREATE TRIGGER trg_immutable_actor_id_consultant
    BEFORE UPDATE OF actor_id ON "consultant_profile"
    FOR EACH ROW EXECUTE FUNCTION prevent_actor_id_modification();
    """)

    # 8. Alter country table
    op.execute("""
    ALTER TABLE "country"
        ADD COLUMN IF NOT EXISTS "alpha3_code" char(3),
        ADD COLUMN IF NOT EXISTS "numeric_code" char(3),
        ADD COLUMN IF NOT EXISTS "calling_code" varchar(20),
        ADD COLUMN IF NOT EXISTS "is_active" boolean NOT NULL DEFAULT true,
        ADD CONSTRAINT "uq_country_alpha3_code" UNIQUE ("alpha3_code"),
        ADD CONSTRAINT "uq_country_numeric_code" UNIQUE ("numeric_code");
    """)


def downgrade() -> None:
    # 8. Revert country alterations
    op.execute("""
    ALTER TABLE "country"
        DROP CONSTRAINT IF EXISTS "uq_country_numeric_code",
        DROP CONSTRAINT IF EXISTS "uq_country_alpha3_code",
        DROP COLUMN IF EXISTS "is_active",
        DROP COLUMN IF EXISTS "calling_code",
        DROP COLUMN IF EXISTS "numeric_code",
        DROP COLUMN IF EXISTS "alpha3_code";
    """)

    # 7. Drop immutability triggers
    op.execute("""
    DROP TRIGGER IF EXISTS trg_immutable_actor_id_consultant ON "consultant_profile";
    DROP TRIGGER IF EXISTS trg_immutable_actor_id_candidate ON "candidate_profile";
    DROP TRIGGER IF EXISTS trg_immutable_actor_id_role_assign ON "user_role_assignment";
    DROP TRIGGER IF EXISTS trg_immutable_actor_id_user_actor ON "user_actor_identity";
    DROP FUNCTION IF EXISTS prevent_actor_id_modification();
    """)

    # 6. Revert consultant_profile
    op.execute("""
    ALTER TABLE "consultant_profile"
        DROP CONSTRAINT IF EXISTS "ck_consultant_profile_actor_id_format",
        DROP CONSTRAINT IF EXISTS "uq_consultant_profile_actor_id",
        DROP COLUMN IF EXISTS "actor_id";
    """)

    # 5. Revert candidate_profile
    op.execute("""
    ALTER TABLE "candidate_profile"
        DROP CONSTRAINT IF EXISTS "ck_candidate_profile_actor_id_format",
        DROP CONSTRAINT IF EXISTS "uq_candidate_profile_actor_id",
        DROP COLUMN IF EXISTS "actor_id";
    """)

    # 4. Revert user_role_assignment
    op.execute("""
    ALTER TABLE "user_role_assignment"
        DROP CONSTRAINT IF EXISTS "ck_user_role_assignment_actor_id_format",
        DROP CONSTRAINT IF EXISTS "uq_user_role_assignment_actor_id",
        DROP COLUMN IF EXISTS "actor_id";
    """)

    # 3. Drop user_actor_identity
    op.execute("""
    DROP TABLE IF EXISTS "user_actor_identity";
    """)

    # 2. Drop allocate_actor_id function
    op.execute("""
    DROP FUNCTION IF EXISTS allocate_actor_id(text);
    """)

    # 1. Drop sequences
    op.execute("""
    DROP SEQUENCE IF EXISTS seq_actor_id_po;
    DROP SEQUENCE IF EXISTS seq_actor_id_co;
    DROP SEQUENCE IF EXISTS seq_actor_id_re;
    DROP SEQUENCE IF EXISTS seq_actor_id_em;
    DROP SEQUENCE IF EXISTS seq_actor_id_ca;
    DROP SEQUENCE IF EXISTS seq_actor_id_gu;
    DROP SEQUENCE IF EXISTS seq_actor_id_aa;
    DROP SEQUENCE IF EXISTS seq_actor_id_ad;
    DROP SEQUENCE IF EXISTS seq_actor_id_sa;
    """)
