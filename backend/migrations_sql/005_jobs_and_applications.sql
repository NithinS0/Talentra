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