"""015_candidate_academics_jobs

Revision ID: 015_candidate_academics_jobs
Revises: 014_actor_ids_and_country_master
Create Date: 2026-10-21 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic. Length MUST be <= 32 chars for alembic_version.version_num
revision: str = '015_candidate_academics_jobs'
down_revision: Union[str, None] = '014_actor_ids_and_country_master'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enhance candidate_profile
    op.execute("""
    ALTER TABLE "candidate_profile"
        ADD COLUMN IF NOT EXISTS "profile_photo_url" varchar(500),
        ADD COLUMN IF NOT EXISTS "profile_photo_storage_key" varchar(500),
        ADD COLUMN IF NOT EXISTS "linkedin_url" varchar(255),
        ADD COLUMN IF NOT EXISTS "github_url" varchar(255),
        ADD COLUMN IF NOT EXISTS "portfolio_url" varchar(255),
        ADD COLUMN IF NOT EXISTS "current_city" varchar(100),
        ADD COLUMN IF NOT EXISTS "current_state" varchar(100),
        ADD COLUMN IF NOT EXISTS "current_country_id" bigint REFERENCES "country"("id"),
        ADD COLUMN IF NOT EXISTS "preferred_roles" text,
        ADD COLUMN IF NOT EXISTS "preferred_locations" text,
        ADD COLUMN IF NOT EXISTS "preferred_employment_types" text,
        ADD COLUMN IF NOT EXISTS "expected_graduation_date" date,
        ADD COLUMN IF NOT EXISTS "availability_status" varchar(50) DEFAULT 'AVAILABLE',
        ADD COLUMN IF NOT EXISTS "is_public_visible" boolean NOT NULL DEFAULT true,
        ADD COLUMN IF NOT EXISTS "consent_placement_rules" boolean NOT NULL DEFAULT true,
        ADD COLUMN IF NOT EXISTS "consent_share_with_employers" boolean NOT NULL DEFAULT true;
    """)

    # 2. Enhance candidate_education
    op.execute("""
    ALTER TABLE "candidate_education"
        ADD COLUMN IF NOT EXISTS "education_level" varchar(50) NOT NULL DEFAULT 'UNDERGRADUATE',
        ADD COLUMN IF NOT EXISTS "board_or_university" varchar(200),
        ADD COLUMN IF NOT EXISTS "stream_specialization" varchar(150),
        ADD COLUMN IF NOT EXISTS "status" varchar(30) NOT NULL DEFAULT 'COMPLETED',
        ADD COLUMN IF NOT EXISTS "start_year" integer,
        ADD COLUMN IF NOT EXISTS "completion_year" integer,
        ADD COLUMN IF NOT EXISTS "grading_system" varchar(30) NOT NULL DEFAULT 'PERCENTAGE',
        ADD COLUMN IF NOT EXISTS "score_value" numeric(5,2),
        ADD COLUMN IF NOT EXISTS "max_score" numeric(6,2),
        ADD COLUMN IF NOT EXISTS "percentage" numeric(5,2),
        ADD COLUMN IF NOT EXISTS "cgpa" numeric(4,2),
        ADD COLUMN IF NOT EXISTS "has_backlogs" boolean NOT NULL DEFAULT false,
        ADD COLUMN IF NOT EXISTS "active_backlogs_count" integer NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS "historical_backlogs_count" integer NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS "document_storage_key" varchar(500),
        ADD COLUMN IF NOT EXISTS "document_name" varchar(255),
        ADD COLUMN IF NOT EXISTS "document_size_bytes" bigint,
        ADD COLUMN IF NOT EXISTS "document_mime_type" varchar(100);

    CREATE INDEX IF NOT EXISTS "idx_candidate_education_profile_level"
        ON "candidate_education" ("candidate_profile_id", "education_level");
    """)

    # 3. Create candidate_education_semester
    op.execute("""
    CREATE TABLE IF NOT EXISTS "candidate_education_semester" (
        "id" BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        "candidate_education_id" bigint NOT NULL REFERENCES "candidate_education"("id") ON DELETE CASCADE,
        "candidate_profile_id" bigint NOT NULL REFERENCES "candidate_profile"("id") ON DELETE CASCADE,
        "semester_number" integer NOT NULL,
        "academic_term" varchar(50),
        "result_status" varchar(30) NOT NULL DEFAULT 'PASS',
        "sgpa" numeric(4,2),
        "cgpa" numeric(4,2),
        "credits_registered" integer,
        "credits_earned" integer,
        "has_backlog" boolean NOT NULL DEFAULT false,
        "backlog_details" text,
        "grade_sheet_storage_key" varchar(500),
        "grade_sheet_name" varchar(255),
        "grade_sheet_size_bytes" bigint,
        "grade_sheet_mime_type" varchar(100),
        "uploaded_at" timestamptz DEFAULT now(),
        "created_at" timestamptz NOT NULL DEFAULT now(),
        "created_by" bigint,
        "updated_at" timestamptz NOT NULL DEFAULT now(),
        "updated_by" bigint,
        "deleted_at" timestamptz,
        CONSTRAINT "uq_candidate_education_semester_num" UNIQUE ("candidate_education_id", "semester_number")
    );

    CREATE INDEX IF NOT EXISTS "idx_cand_edu_sem_profile"
        ON "candidate_education_semester" ("candidate_profile_id");
    """)

    # 4. Create candidate_document
    op.execute("""
    CREATE TABLE IF NOT EXISTS "candidate_document" (
        "id" BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        "candidate_profile_id" bigint NOT NULL REFERENCES "candidate_profile"("id") ON DELETE CASCADE,
        "document_category" varchar(60) NOT NULL,
        "title" varchar(200) NOT NULL,
        "file_name" varchar(255) NOT NULL,
        "file_size_bytes" bigint NOT NULL,
        "mime_type" varchar(100) NOT NULL,
        "storage_path" varchar(500) NOT NULL,
        "content_sha256" char(64) NOT NULL,
        "is_verified" boolean NOT NULL DEFAULT false,
        "is_archived" boolean NOT NULL DEFAULT false,
        "linked_entity_type" varchar(50),
        "linked_entity_id" bigint,
        "created_at" timestamptz NOT NULL DEFAULT now(),
        "created_by" bigint,
        "updated_at" timestamptz NOT NULL DEFAULT now(),
        "updated_by" bigint,
        "deleted_at" timestamptz
    );

    CREATE INDEX IF NOT EXISTS "idx_candidate_document_profile_cat"
        ON "candidate_document" ("candidate_profile_id", "document_category");
    """)

    # 5. Enhance resume_version
    op.execute("""
    ALTER TABLE "resume_version"
        ADD COLUMN IF NOT EXISTS "file_name" varchar(255),
        ADD COLUMN IF NOT EXISTS "file_size_bytes" bigint,
        ADD COLUMN IF NOT EXISTS "mime_type" varchar(100) DEFAULT 'application/pdf',
        ADD COLUMN IF NOT EXISTS "target_role" varchar(100),
        ADD COLUMN IF NOT EXISTS "is_archived" boolean NOT NULL DEFAULT false;
    """)

    # 6. Create candidate_certification
    op.execute("""
    CREATE TABLE IF NOT EXISTS "candidate_certification" (
        "id" BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        "candidate_profile_id" bigint NOT NULL REFERENCES "candidate_profile"("id") ON DELETE CASCADE,
        "name" varchar(200) NOT NULL,
        "issuing_organisation" varchar(200) NOT NULL,
        "issue_date" date,
        "expiry_date" date,
        "credential_id" varchar(100),
        "credential_url" varchar(500),
        "document_storage_key" varchar(500),
        "document_name" varchar(255),
        "document_size_bytes" bigint,
        "created_at" timestamptz NOT NULL DEFAULT now(),
        "created_by" bigint,
        "updated_at" timestamptz NOT NULL DEFAULT now(),
        "updated_by" bigint,
        "deleted_at" timestamptz
    );

    CREATE INDEX IF NOT EXISTS "idx_candidate_cert_profile"
        ON "candidate_certification" ("candidate_profile_id");
    """)

    # 7. Enhance candidate_project
    op.execute("""
    ALTER TABLE "candidate_project"
        ADD COLUMN IF NOT EXISTS "technologies" varchar(255),
        ADD COLUMN IF NOT EXISTS "project_url" varchar(500),
        ADD COLUMN IF NOT EXISTS "description" text;
    """)

    # 8. Enhance candidate_skill
    op.execute("""
    ALTER TABLE "candidate_skill"
        ADD COLUMN IF NOT EXISTS "skill_name" varchar(100),
        ADD COLUMN IF NOT EXISTS "proficiency_level" varchar(50) DEFAULT 'INTERMEDIATE';
    """)

    # 9. Enhance job_requirement
    op.execute("""
    ALTER TABLE "job_requirement"
        ADD COLUMN IF NOT EXISTS "responsibilities" text,
        ADD COLUMN IF NOT EXISTS "required_skills" text,
        ADD COLUMN IF NOT EXISTS "preferred_skills" text,
        ADD COLUMN IF NOT EXISTS "required_qualifications" text,
        ADD COLUMN IF NOT EXISTS "accepted_branches" text,
        ADD COLUMN IF NOT EXISTS "min_percentage" numeric(5,2),
        ADD COLUMN IF NOT EXISTS "min_cgpa" numeric(4,2),
        ADD COLUMN IF NOT EXISTS "allow_backlogs" boolean NOT NULL DEFAULT false,
        ADD COLUMN IF NOT EXISTS "max_active_backlogs" integer NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS "min_experience_years" numeric(3,1),
        ADD COLUMN IF NOT EXISTS "max_experience_years" numeric(3,1),
        ADD COLUMN IF NOT EXISTS "location_city" varchar(100),
        ADD COLUMN IF NOT EXISTS "location_country" varchar(100),
        ADD COLUMN IF NOT EXISTS "required_documents" text;
    """)

    # 10. Enhance job_application
    op.execute("""
    ALTER TABLE "job_application"
        ADD COLUMN IF NOT EXISTS "resume_snapshot_title" varchar(200),
        ADD COLUMN IF NOT EXISTS "resume_snapshot_file_name" varchar(255),
        ADD COLUMN IF NOT EXISTS "eligibility_status" varchar(30) DEFAULT 'ELIGIBLE',
        ADD COLUMN IF NOT EXISTS "eligibility_notes" text;
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS "candidate_certification" CASCADE;
    DROP TABLE IF EXISTS "candidate_document" CASCADE;
    DROP TABLE IF EXISTS "candidate_education_semester" CASCADE;
    """)
