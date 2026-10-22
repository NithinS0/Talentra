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