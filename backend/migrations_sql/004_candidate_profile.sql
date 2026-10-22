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
  "completion_score" numeric(5,2) NOT NULL DEFAULT 0.00,
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