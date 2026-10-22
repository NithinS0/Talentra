-- Talentra PostgreSQL schema starter
-- Source: Talentra Database Design Hackathon Docket, uploaded PDF (12 pages).
-- IMPORTANT: Review generated DDL and all open decisions before applying to any database.
-- Recommended target: PostgreSQL (Supabase is managed PostgreSQL). The docket permits PostgreSQL or MySQL.
-- Docket requires relational FK/check constraints, append-only audit/payment/wallet histories, licence/device concurrency controls,
-- and analytics marts. MongoDB is not the target engine for this docket.
-- Naming: snake_case; singular table names; id BIGINT identity PK; UTC timestamptz; money NUMERIC + currency code.
-- Security: do not store raw Aadhaar/PAN or card/bank data in clear text; never store passwords in plaintext.
BEGIN;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE IF NOT EXISTS "country" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "country_code" char(2) NOT NULL,
  "name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_country_country_code" UNIQUE ("country_code")
);

CREATE TABLE IF NOT EXISTS "state" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "country_id" bigint NOT NULL,
  "state_code" varchar(20) NOT NULL,
  "name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_state_country_id" FOREIGN KEY ("country_id") REFERENCES "country"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "city" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "state_id" bigint NOT NULL,
  "name" varchar(150) NOT NULL,
  "latitude" numeric(9,6),
  "longitude" numeric(9,6),
  "coordinate_source" varchar(100),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_city_latitude_range" CHECK (latitude BETWEEN -90 AND 90),
  CONSTRAINT "ck_city_longitude_range" CHECK (longitude BETWEEN -180 AND 180),
  CONSTRAINT "fk_city_state_id" FOREIGN KEY ("state_id") REFERENCES "state"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "language" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "language_code" varchar(10) NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "is_default" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_language_language_code" UNIQUE ("language_code")
);

CREATE TABLE IF NOT EXISTS "skill" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "skill_code" varchar(60) NOT NULL,
  "name" varchar(150) NOT NULL,
  "parent_skill_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_skill_parent_skill_id" FOREIGN KEY ("parent_skill_id") REFERENCES "skill"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "qualification" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "qualification_code" varchar(60) NOT NULL,
  "name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "industry" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "industry_code" varchar(60) NOT NULL,
  "name" varchar(150) NOT NULL,
  "parent_industry_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_industry_parent_industry_id" FOREIGN KEY ("parent_industry_id") REFERENCES "industry"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_role" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_role_code" varchar(60) NOT NULL,
  "name" varchar(150) NOT NULL,
  "industry_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_job_role_industry_id" FOREIGN KEY ("industry_id") REFERENCES "industry"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "employment_type" (
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

CREATE TABLE IF NOT EXISTS "work_type" (
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

CREATE TABLE IF NOT EXISTS "reference_domain" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "domain_code" varchar(80) NOT NULL,
  "description" varchar(500) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_reference_domain_domain_code" UNIQUE ("domain_code")
);

CREATE TABLE IF NOT EXISTS "reference_code" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "reference_domain_id" bigint NOT NULL,
  "code" varchar(80) NOT NULL,
  "active" boolean NOT NULL DEFAULT false,
  "sort_order" integer NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_reference_code_reference_domain_id" FOREIGN KEY ("reference_domain_id") REFERENCES "reference_domain"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "reference_code_translation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "reference_code_id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_reference_code_translation_reference_code_id" FOREIGN KEY ("reference_code_id") REFERENCES "reference_code"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_reference_code_translation_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "ui_translation_key" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "translation_key" varchar(180) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_ui_translation_key_translation_key" UNIQUE ("translation_key")
);

CREATE TABLE IF NOT EXISTS "ui_translation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "ui_translation_key_id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "translated_text" varchar(2000) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_ui_translation_ui_translation_key_id" FOREIGN KEY ("ui_translation_key_id") REFERENCES "ui_translation_key"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_ui_translation_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "currency" (
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

CREATE TABLE IF NOT EXISTS "country_phone_rule" (
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

CREATE TABLE IF NOT EXISTS "qualification_level" (
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

CREATE TABLE IF NOT EXISTS "industry_translation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "industry__id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_industry_translation_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "skill_alias" (
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

CREATE TABLE IF NOT EXISTS "work_type_translation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "work_type__id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_work_type_translation_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "employment_type_translation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "employment_type__id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_employment_type_translation_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "city_alias" (
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

CREATE TABLE IF NOT EXISTS "candidate_profile" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "first_name" varchar(150) NOT NULL,
  "middle_name" varchar(150),
  "last_name" varchar(150) NOT NULL,
  "headline" varchar(240),
  "summary" text,
  "profile_status_code_id" bigint NOT NULL,
  "profile_visibility_code_id" bigint NOT NULL,
  "completion_score" numeric(5,2) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_candidate_profile_completion_score_range" CHECK (completion_score BETWEEN 0 AND 100),
  CONSTRAINT "fk_candidate_profile_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_contact" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "email_address" varchar(254),
  "phone_e164" varchar(16),
  "phone_country_id" bigint,
  "city_id" bigint,
  "address_line_1" varchar(250),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_contact_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_contact_city_id" FOREIGN KEY ("city_id") REFERENCES "city"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_education" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "qualification_id" bigint NOT NULL,
  "institution_name" varchar(200) NOT NULL,
  "field_of_study" varchar(150),
  "start_date" date NOT NULL,
  "end_date" date,
  "grade_value" varchar(50),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_candidate_education_date_range" CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT "fk_candidate_education_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_education_qualification_id" FOREIGN KEY ("qualification_id") REFERENCES "qualification"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_work_experience" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "employer_name" varchar(200) NOT NULL,
  "job_title" varchar(150) NOT NULL,
  "job_role_id" bigint,
  "start_date" date NOT NULL,
  "end_date" date,
  "is_current" boolean NOT NULL DEFAULT false,
  "description" text,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_candidate_work_experience_date_range" CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT "fk_candidate_work_experience_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_work_experience_job_role_id" FOREIGN KEY ("job_role_id") REFERENCES "job_role"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_skill" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "skill_id" bigint NOT NULL,
  "years_experience" numeric(5,2),
  "is_primary" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_skill_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_skill_skill_id" FOREIGN KEY ("skill_id") REFERENCES "skill"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_language" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "language_id" bigint NOT NULL,
  "can_read" boolean NOT NULL,
  "can_write" boolean NOT NULL,
  "can_speak" boolean NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_language_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_language_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_project" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "project_name" varchar(180) NOT NULL,
  "role_description" varchar(500) NOT NULL,
  "start_date" date NOT NULL,
  "end_date" date,
  "outcome" varchar(1000),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_candidate_project_date_range" CHECK (end_date IS NULL OR end_date >= start_date),
  CONSTRAINT "fk_candidate_project_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_resume" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "resume_title" varchar(180) NOT NULL,
  "is_default" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_candidate_resume_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "resume_version" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_resume_id" bigint NOT NULL,
  "version_number" integer NOT NULL,
  "storage_object_key" varchar(500) NOT NULL,
  "content_sha256" char(64) NOT NULL,
  "language_id" bigint,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_resume_version_version_number_positive" CHECK (version_number > 0),
  CONSTRAINT "fk_resume_version_candidate_resume_id" FOREIGN KEY ("candidate_resume_id") REFERENCES "candidate_resume"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_resume_version_language_id" FOREIGN KEY ("language_id") REFERENCES "language"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "resume_template" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "template_code" varchar(60) NOT NULL,
  "name" varchar(150) NOT NULL,
  "layout_config" jsonb NOT NULL,
  "active" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_resume_template_template_code" UNIQUE ("template_code")
);

CREATE TABLE IF NOT EXISTS "candidate_assessment" (
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
  CONSTRAINT "fk_candidate_assessment_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_assessment_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_assessment_answer" (
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
  CONSTRAINT "fk_candidate_assessment_answer_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_assessment_answer_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "assessment_question" (
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
  CONSTRAINT "fk_assessment_question_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_assessment_question_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_course_enrolment" (
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
  CONSTRAINT "fk_candidate_course_enrolment_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_course_enrolment_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "profile_completion_event" (
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

CREATE TABLE IF NOT EXISTS "profile_view_history" (
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

CREATE TABLE IF NOT EXISTS "candidate_activity_log" (
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

CREATE TABLE IF NOT EXISTS "candidate_referral" (
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
  CONSTRAINT "fk_candidate_referral_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_referral_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_bookmark" (
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
  CONSTRAINT "fk_candidate_bookmark_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_bookmark_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_profile_language" (
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
  CONSTRAINT "fk_candidate_profile_language_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_profile_language_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_contact_consent" (
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
  CONSTRAINT "fk_candidate_contact_consent_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_contact_consent_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_profile_visibility_history" (
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

CREATE TABLE IF NOT EXISTS "resume_download_event" (
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

CREATE TABLE IF NOT EXISTS "candidate_project_skill" (
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
  CONSTRAINT "fk_candidate_project_skill_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_project_skill_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_referral_attribution" (
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
  CONSTRAINT "fk_candidate_referral_attribution_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_candidate_referral_attribution_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "organisation_id" bigint NOT NULL,
  "created_by_user_id" bigint NOT NULL,
  "job_role_id" bigint NOT NULL,
  "title" varchar(180) NOT NULL,
  "description" text NOT NULL,
  "employment_type_id" bigint NOT NULL,
  "work_type_id" bigint NOT NULL,
  "status_code_id" bigint NOT NULL,
  "publish_state_code_id" bigint NOT NULL,
  "open_to_consultants" boolean NOT NULL DEFAULT false,
  "positions_count" integer NOT NULL,
  "salary_min" numeric(14,2),
  "salary_max" numeric(14,2),
  "salary_currency_code" char(3),
  "application_deadline" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_job_requirement_positions_count_positive" CHECK (positions_count > 0),
  CONSTRAINT "ck_job_requirement_salary_range" CHECK (salary_max IS NULL OR salary_min IS NULL OR salary_max >= salary_min),
  CONSTRAINT "ck_job_requirement_positive_positions" CHECK (positions_count > 0),
  CONSTRAINT "fk_job_requirement_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_job_role_id" FOREIGN KEY ("job_role_id") REFERENCES "job_role"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_employment_type_id" FOREIGN KEY ("employment_type_id") REFERENCES "employment_type"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_work_type_id" FOREIGN KEY ("work_type_id") REFERENCES "work_type"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_position" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_requirement_id" bigint NOT NULL,
  "position_code" varchar(60) NOT NULL,
  "title" varchar(180) NOT NULL,
  "headcount" integer NOT NULL,
  "filled_count" integer NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_job_position_headcount_positive" CHECK (headcount > 0),
  CONSTRAINT "fk_job_position_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement_skill" (
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
  CONSTRAINT "fk_job_requirement_skill_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_skill_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_skill_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement_qualification" (
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
  CONSTRAINT "fk_job_requirement_qualification_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_qualification_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_qualification_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement_location" (
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
  CONSTRAINT "fk_job_requirement_location_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_location_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_location_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_publish_history" (
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

CREATE TABLE IF NOT EXISTS "job_questionnaire" (
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
  CONSTRAINT "fk_job_questionnaire_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_questionnaire_question" (
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
  CONSTRAINT "fk_job_questionnaire_question_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_question_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_question_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_questionnaire_option" (
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
  CONSTRAINT "fk_job_questionnaire_option_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_option_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_questionnaire_option_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_application" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_requirement_id" bigint NOT NULL,
  "candidate_profile_id" bigint NOT NULL,
  "applied_at" timestamptz NOT NULL,
  "status_code_id" bigint NOT NULL,
  "resume_version_id" bigint,
  "cover_letter" varchar(8000),
  "last_status_changed_at" timestamptz NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_job_application_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_application_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_application_resume_version_id" FOREIGN KEY ("resume_version_id") REFERENCES "resume_version"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_application_id" bigint NOT NULL,
  "from_status_code_id" bigint,
  "to_status_code_id" bigint NOT NULL,
  "changed_by_user_id" bigint NOT NULL,
  "changed_at" timestamptz NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_application_status_history_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_answer" (
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
  CONSTRAINT "fk_application_answer_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_answer_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_answer_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_shortlist" (
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
  CONSTRAINT "fk_application_shortlist_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_shortlist_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_shortlist_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_interview" (
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
  CONSTRAINT "fk_application_interview_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_interview_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_interview_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_interview_feedback" (
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
  CONSTRAINT "fk_application_interview_feedback_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_interview_feedback_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_interview_feedback_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_offer" (
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
  CONSTRAINT "fk_application_offer_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_offer_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_offer_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_join_record" (
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
  CONSTRAINT "fk_application_join_record_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_join_record_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_join_record_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_rejection" (
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
  CONSTRAINT "fk_application_rejection_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_rejection_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_rejection_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "candidate_job_search_history" (
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

CREATE TABLE IF NOT EXISTS "candidate_application_history" (
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

CREATE TABLE IF NOT EXISTS "job_bookmark" (
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
  CONSTRAINT "fk_job_bookmark_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_bookmark_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_bookmark_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_view_history" (
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

CREATE TABLE IF NOT EXISTS "job_requirement_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "job_requirement_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_job_requirement_status_history_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement_employment_type" (
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
  CONSTRAINT "fk_job_requirement_employment_type_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_employment_type_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_employment_type_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_requirement_work_type" (
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
  CONSTRAINT "fk_job_requirement_work_type_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_work_type_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_requirement_work_type_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "application_feedback" (
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
  CONSTRAINT "fk_application_feedback_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_feedback_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_application_feedback_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "job_search_saved_filter" (
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
  CONSTRAINT "fk_job_search_saved_filter_job_requirement_id" FOREIGN KEY ("job_requirement_id") REFERENCES "job_requirement"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_search_saved_filter_job_application_id" FOREIGN KEY ("job_application_id") REFERENCES "job_application"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_job_search_saved_filter_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "user" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "email_address" varchar(254),
  "phone_e164" varchar(16),
  "display_name" varchar(150) NOT NULL,
  "account_status_code_id" bigint NOT NULL,
  "identity_provider_code" varchar(60) NOT NULL,
  "provider_subject" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "credential" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "credential_type_code_id" bigint NOT NULL,
  "password_hash" varchar(255),
  "provider_credential_reference" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_credential_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "role" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "role_code" varchar(60) NOT NULL,
  "display_name" varchar(150) NOT NULL,
  "description" varchar(500) NOT NULL,
  "is_system_role" boolean NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_role_role_code" UNIQUE ("role_code")
);

CREATE TABLE IF NOT EXISTS "permission" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "permission_code" varchar(100) NOT NULL,
  "resource_code" varchar(80) NOT NULL,
  "action_code" varchar(60) NOT NULL,
  "description" varchar(500) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_permission_permission_code" UNIQUE ("permission_code")
);

CREATE TABLE IF NOT EXISTS "role_permission" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "role_id" bigint NOT NULL,
  "permission_id" bigint NOT NULL,
  "effect_code" varchar(10) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_role_permission_role_id" FOREIGN KEY ("role_id") REFERENCES "role"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_role_permission_permission_id" FOREIGN KEY ("permission_id") REFERENCES "permission"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "user_role_assignment" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "role_id" bigint NOT NULL,
  "organisation_id" bigint,
  "valid_from" timestamptz NOT NULL,
  "valid_until" timestamptz,
  "assigned_by_user_id" bigint NOT NULL,
  "revoked_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_user_role_assignment_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_user_role_assignment_role_id" FOREIGN KEY ("role_id") REFERENCES "role"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_user_role_assignment_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "access_policy" (
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

CREATE TABLE IF NOT EXISTS "role_dashboard_config" (
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

CREATE TABLE IF NOT EXISTS "identity_session" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "provider_session_reference" varchar(255),
  "device_id" bigint,
  "started_at" timestamptz NOT NULL,
  "last_activity_at" timestamptz NOT NULL,
  "expires_at" timestamptz NOT NULL,
  "ended_at" timestamptz,
  "revoked_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_identity_session_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "consent_record" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "user_id" bigint NOT NULL,
  "consent_type_code_id" bigint NOT NULL,
  "policy_version" varchar(80) NOT NULL,
  "granted" boolean NOT NULL,
  "captured_at" timestamptz NOT NULL,
  "withdrawn_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_consent_record_user_id" FOREIGN KEY ("user_id") REFERENCES "user"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "audit_event" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "actor_user_id" bigint,
  "action_code" varchar(100) NOT NULL,
  "resource_type" varchar(100) NOT NULL,
  "resource_id" varchar(100),
  "occurred_at" timestamptz NOT NULL,
  "request_id" uuid,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz
);

CREATE TABLE IF NOT EXISTS "system_error_event" (
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

CREATE TABLE IF NOT EXISTS "block_list_entry" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "blocker_user_id" bigint NOT NULL,
  "blocked_user_id" bigint,
  "blocked_organisation_id" bigint,
  "reason_code_id" bigint,
  "revoked_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_block_list_entry_block_target_exactly_one" CHECK ((blocked_user_id IS NOT NULL)::int + (blocked_organisation_id IS NOT NULL)::int = 1)
);

CREATE TABLE IF NOT EXISTS "login_attempt" (
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

CREATE TABLE IF NOT EXISTS "account_recovery_request" (
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
  CONSTRAINT "fk_account_recovery_request_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_account_recovery_request_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "api_client_registration" (
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

CREATE TABLE IF NOT EXISTS "security_policy_version" (
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

CREATE TABLE IF NOT EXISTS "role_assignment_history" (
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

CREATE TABLE IF NOT EXISTS "permission_change_request" (
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

CREATE TABLE IF NOT EXISTS "security_alert_event" (
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

CREATE TABLE IF NOT EXISTS "subscription_plan" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "plan_code" varchar(80) NOT NULL,
  "name" varchar(150) NOT NULL,
  "price_amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "billing_interval_code_id" bigint NOT NULL,
  "active" boolean NOT NULL DEFAULT false,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_plan_plan_code" UNIQUE ("plan_code"),
  CONSTRAINT "uq_subscription_plan_currency_code" UNIQUE ("currency_code")
);

CREATE TABLE IF NOT EXISTS "plan_entitlement" (
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

CREATE TABLE IF NOT EXISTS "subscription" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "subscription_plan_id" bigint NOT NULL,
  "licence_id" bigint,
  "status_code_id" bigint NOT NULL,
  "starts_at" timestamptz NOT NULL,
  "ends_at" timestamptz NOT NULL,
  "auto_renew" boolean NOT NULL DEFAULT false,
  "cancelled_at" timestamptz,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "ck_subscription_timestamp_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "ck_subscription_period_range" CHECK (ends_at >= starts_at),
  CONSTRAINT "fk_subscription_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_subscription_subscription_plan_id" FOREIGN KEY ("subscription_plan_id") REFERENCES "subscription_plan"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_subscription_licence_id" FOREIGN KEY ("licence_id") REFERENCES "licence"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "subscription_renewal" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_renewal_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_subscription_renewal_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "subscription_cancellation" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_subscription_cancellation_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_subscription_cancellation_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_order" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "payment_provider_code" varchar(80) NOT NULL,
  "provider_order_reference" varchar(255),
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_order_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_order_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_transaction" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "payment_order_id" bigint NOT NULL,
  "provider_transaction_reference" varchar(255),
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_transaction_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_transaction_payment_order_id" FOREIGN KEY ("payment_order_id") REFERENCES "payment_order"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "subscription_id" bigint,
  "invoice_number" varchar(80) NOT NULL,
  "issued_on" date NOT NULL,
  "due_on" date,
  "subtotal_amount" numeric(14,2) NOT NULL,
  "tax_amount" numeric(14,2) NOT NULL,
  "total_amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_invoice_invoice_number" UNIQUE ("invoice_number"),
  CONSTRAINT "uq_invoice_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_invoice_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_invoice_subscription_id" FOREIGN KEY ("subscription_id") REFERENCES "subscription"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice_line" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_invoice_line_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_invoice_line_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_refund" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_refund_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_refund_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "wallet" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint NOT NULL,
  "currency_code" char(3) NOT NULL,
  "status_code_id" bigint NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "wallet_ledger_entry" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "wallet_id" bigint NOT NULL,
  "entry_type_code_id" bigint NOT NULL,
  "amount" numeric(14,2) NOT NULL,
  "currency_code" char(3) NOT NULL,
  "source_type" varchar(80) NOT NULL,
  "source_id" varchar(100) NOT NULL,
  "original_entry_id" bigint,
  "idempotency_key" varchar(255) NOT NULL,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_ledger_entry_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_ledger_entry_wallet_id" FOREIGN KEY ("wallet_id") REFERENCES "wallet"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "credit_consumption" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_credit_consumption_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_credit_consumption_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "profile_download_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "candidate_profile_id" bigint NOT NULL,
  "actor_user_id" bigint NOT NULL,
  "organisation_id" bigint NOT NULL,
  "downloaded_at" timestamptz NOT NULL,
  "credit_consumption_id" bigint,
  "request_id" uuid,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_profile_download_history_candidate_profile_id" FOREIGN KEY ("candidate_profile_id") REFERENCES "candidate_profile"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_profile_download_history_organisation_id" FOREIGN KEY ("organisation_id") REFERENCES "organisation"(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT "fk_profile_download_history_credit_consumption_id" FOREIGN KEY ("credit_consumption_id") REFERENCES "credit_consumption"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_webhook_event" (
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

CREATE TABLE IF NOT EXISTS "wallet_balance_snapshot" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_wallet_balance_snapshot_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_wallet_balance_snapshot_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "invoice_status_history" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "invoice_id" bigint NOT NULL,
  "event_code_id" bigint NOT NULL,
  "actor_user_id" bigint,
  "occurred_at" timestamptz NOT NULL,
  "metadata_redacted" jsonb,
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "fk_invoice_status_history_invoice_id" FOREIGN KEY ("invoice_id") REFERENCES "invoice"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS "payment_reconciliation_run" (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  "account_id" bigint,
  "status_code_id" bigint NOT NULL,
  "amount" numeric(14,2),
  "currency_code" char(3),
  "idempotency_key" varchar(255),
  "created_at" timestamptz NOT NULL DEFAULT now(),
  "created_by" bigint,
  "updated_at" timestamptz NOT NULL DEFAULT now(),
  "updated_by" bigint,
  "deleted_at" timestamptz,
  CONSTRAINT "uq_payment_reconciliation_run_currency_code" UNIQUE ("currency_code"),
  CONSTRAINT "fk_payment_reconciliation_run_account_id" FOREIGN KEY ("account_id") REFERENCES "account"(id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

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

-- Seed the nine docket actor roles. Role permissions must be populated only after the reviewed permission matrix is approved.
INSERT INTO role (role_code, display_name, description, is_system_role)
VALUES
('SUPER_ADMIN','Super Admin','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('ADMIN','Admin','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('ACCOUNT_ADMIN','Account Admin','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('GUEST','Guest','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('CANDIDATE','Candidate','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('EMPLOYER','Employer','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('RECRUITER','Recruiter','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('CONSULTANT','Consultant','Docket actor class; permissions require approved RBAC matrix.',TRUE),
('PLACEMENT_OFFICER','Placement Officer (TPO)','Docket actor class; permissions require approved RBAC matrix.',TRUE)
ON CONFLICT (role_code) DO NOTHING;

-- Required implementation work before production:
-- 1) Add reviewed FK constraints for every relationship not fully inferred in this starter.
-- 2) Add immutable triggers/privileges for audit_event, wallet_ledger_entry, payment_transaction, history and download/view tables.
-- 3) Add exclusion constraints using tstzrange for subscription periods per licence and overlapping gig-worker windows.
-- 4) Enforce max_users/max_devices_per_user under transaction/row/advisory locks during seat allocation/login.
-- 5) Add row-level security/access-layer policies; UI route guards are not security.
-- 6) Create indexes based on EXPLAIN ANALYZE and measured workloads; use idx_table_column names.
-- 7) Partition high-volume application/notification/history tables only after workload measurement.
-- 8) Populate reference_domain/reference_code for all fixed enumerations; no free-text status enums.
COMMIT;
