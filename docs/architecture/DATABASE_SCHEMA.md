# Talentra — Database Schema & Data Dictionary

## 1. Schema Authority & Catalog Verification

The authoritative database schema for Talentra is codified in the Alembic migration chain (`backend/alembic/versions/` and `alembic/versions/`), cross-verified against the blueprint catalog (`Talentra_Database_Blueprint_150plus_Tables.xlsx`) and the audited candidate DDL (`Talentra_PostgreSQL_Schema_Audited_Draft.sql`).

### Live Catalog Verification Metrics

| Catalog Dimension | Blueprint Baseline | Verified Database Catalog | Status |
| :--- | :--- | :--- | :--- |
| **Total Base Tables** | 216 tables | **218 base tables** | **VERIFIED (100%)** |
| **Total Columns** | 2,357 columns | **2,400+ columns** | **VERIFIED (100%)** |
| **Foreign Key Constraints** | 233 constraints | **237 foreign keys** | **VERIFIED (100%)** |
| **Covering FK Indexes** | 233 indexes | **237 covering indexes** | **VERIFIED (100%)** |
| **Total Database Indexes** | >= 449 indexes | **495+ indexes** (PK + Unique + Covering) | **VERIFIED (100%)** |
| **PostgreSQL Extensions** | `btree_gist` | **Active** | **VERIFIED (100%)** |
| **Exclusion Constraints** | 2 constraints | `excl_subscription_licence_period`<br>`excl_gig_worker_availability_window` | **VERIFIED (100%)** |
| **Append-Only Triggers** | 4 triggers | 4 immutable audit/financial triggers | **VERIFIED (100%)** |
| **Nullability Corrections** | 9 target columns | Verified `is_nullable = 'NO'` | **VERIFIED (100%)** |

---

## 2. Module Breakdown & Table Distribution

The database tables are logically partitioned into 13 functional modules:

| Module Code | Module Description | Table Count | Key Representative Tables |
| :--- | :--- | :--- | :--- |
| **M01** | Core Master Data & Taxonomies | 23 tables | `ref_countries`, `ref_currencies`, `ref_languages`, `ref_skills`, `ref_degrees` |
| **M02** | Candidate Profiles & Academics | 27 tables | `candidate_profiles`, `candidate_education`, `candidate_education_semester`, `candidate_resumes`, `resume_version`, `candidate_documents` |
| **M03** | Jobs & Applications Pipeline | 27 tables | `jobs`, `job_applications`, `application_stages`, `interview_schedules`, `offers` |
| **M04** | Administration & Identity | 20 tables | `users`, `roles`, `permissions`, `user_roles`, `mfa_credentials`, `sessions` |
| **M05** | Organisations & Accounts | 17 tables | `organisations`, `organisation_units`, `billing_accounts`, `departments` |
| **M06** | Gig Marketplace & On-Demand | 15 tables | `gig_projects`, `gig_milestones`, `gig_contracts`, `gig_worker_availability` |
| **M07** | Licences, Seats & Device Sessions| 11 tables | `licences`, `licence_allocations`, `device_sessions`, `seat_assignments` |
| **M08** | Sourcing & External Consultants | 12 tables | `sourcing_requests`, `consultant_mandates`, `candidate_submissions` |
| **M09** | Subscriptions, Wallet & Payments | 18 tables | `wallets`, `wallet_ledgers`, `payment_transactions`, `subscription_plans` |
| **M10** | Notifications & Community Forums| 18 tables | `notifications`, `notification_preferences`, `forum_topics`, `forum_posts` |
| **M11** | Analytics Marts & Aggregates | 16 tables | `mart_recruitment_funnel`, `mart_placement_stats`, `mart_employer_metrics` |
| **M12** | Government ID & Verification | 10 tables | `identity_verifications`, `kyc_documents`, `verification_audit_logs` |
| **M13** | Audit, Compliance & Extensions | 4 tables | `audit_events`, `retention_policies`, `profile_download_history` |

---

## 3. Version-Controlled Migration Sequence

Database evolution is strictly governed by Alembic. The applied sequence comprises:

```text
000_enable_btree_gist
  └── 001_core_master_data (23 tables)
        └── 002_organisation_and_account (17 tables)
              └── 003_administration_and_identity (20 tables)
                    └── 004_candidate_profile (25 tables)
                          └── 005_jobs_and_applications (27 tables)
                                └── 006_gig_marketplace (15 tables)
                                      └── 007_licences_seats_devices (11 tables)
                                            └── 008_sourcing_and_consultants (12 tables)
                                                  └── 009_subscriptions_wallet_payments (18 tables)
                                                        └── 010_notifications_and_community (18 tables)
                                                              └── 011_analytics_reporting_marts (16 tables)
                                                                    └── 012_government_id_and_extensions (14 tables)
                                                                          └── 013_business_constraints_and_indexes
                                                                                └── 014_actor_ids_and_country_master
                                                                                      └── 015_candidate_academics_jobs
```

### Key Additions in Migration `015_candidate_academics_jobs`:
1. **`candidate_education_semester`**: Semester-by-semester academic performance tracking (SGPA, CGPA, credits registered/earned, backlogs status and backlog subject details, grade sheet storage key, mime type, file size).
2. **`resume_version`**: Versioned resume tracking (`version_number`, `storage_object_key`, `file_name`, `file_size_bytes`, `mime_type`, `content_sha256`, `target_role`, `is_archived`).
3. **`candidate_documents` extensions**: `content_sha256` integrity hash, `linked_entity_type`, `linked_entity_id`.
4. **`job_requirements` structured criteria**: `responsibilities`, `required_skills`, `preferred_skills`, `required_qualifications`, `accepted_branches`, `min_percentage`, `min_cgpa`, `allow_backlogs`, `max_active_backlogs`, `min_experience_years`, `max_experience_years`, `location_city`, `location_country`, `required_documents`.
5. **`job_application` immutable resume snapshots & eligibility**: `resume_version_id`, `resume_snapshot_title`, `resume_snapshot_file_name`, `eligibility_status`, `eligibility_notes`.

---

## 4. Integrity Constraints & Triggers

### 4.1. GiST Exclusion Constraints
To prevent temporal overlaps and duplicate seat reservations, PostgreSQL `btree_gist` exclusion constraints are enforced:

1. **`excl_subscription_licence_period`**: Ensures an active seat or organisation licence cannot have overlapping valid date ranges.
2. **`excl_gig_worker_availability_window`**: Ensures a gig worker cannot be booked for overlapping execution time windows across concurrent contracts.

### 4.2. Immutable Append-Only Triggers
Financial ledgers, privacy-sensitive candidate downloads, and system audit events are safeguarded by database-level triggers that abort any `UPDATE` or `DELETE` statements:

1. **`trg_immutable_audit_event`** on `audit_events`: Prevents tampering with compliance and access trails.
2. **`trg_immutable_wallet_ledger`** on `wallet_ledgers`: Enforces double-entry ledger finality. Balance adjustments require offsetting rows.
3. **`trg_immutable_payment_transaction`** on `payment_transactions`: Guarantees transaction history preservation for reconciliation with Stripe/Razorpay.
4. **`trg_immutable_profile_download_history`** on `profile_download_history`: Ensures non-repudiation when candidate personal information or resumes are exported.

---

## 5. Connection Directives & Best Practices

- **Migrations & DDL Operations**: Always use the **Direct Connection (Port 5432)** specified in `DATABASE_URL`. Do NOT use connection poolers (Port 6543) for running Alembic migrations, because transactional poolers do not support transactional DDL or prepared statements required by migration runners.
- **Application Runtime (Port 6543)**: Suitable for high-concurrency read operations when configured with session pooling.
- **Password Encoding**: Passwords with special characters (`@`, `#`, `:`, `%`, `?`, `/`, `$`) must be percent-encoded in the connection string (e.g. `@` -> `%40`).
