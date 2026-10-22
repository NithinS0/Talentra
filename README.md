# TALENTRA — Production-Grade Campus Placement, Recruitment & Talent Operating System

[![CI/CD Production Pipeline](https://github.com/talentra/talentra/actions/workflows/production-release.yml/badge.svg)](.github/workflows/production-release.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4.2-black.svg?logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1.svg?logo=postgresql)](https://www.postgresql.org)
[![Alembic](https://img.shields.io/badge/Alembic-15_Migrations-orange.svg)](alembic/)
[![Pytest](https://img.shields.io/badge/Pytest-266_Passing-brightgreen.svg)](tests/)
[![Vitest](https://img.shields.io/badge/Vitest-166_Passing-brightgreen.svg)](frontend/)
[![ESLint](https://img.shields.io/badge/ESLint-0_Errors-green.svg)](frontend/)

---

## 1. Project Title & Overview

**Talentra** is an enterprise-grade, multi-tenant talent acquisition, campus placement, and freelance workforce operating platform. Built to support university placement cells, corporate campus recruitment drives, staffing agencies, and freelance contracting, Talentra bridges candidate career records, employer hiring pipelines, and university training and placement offices (TPOs).

### Core Problem Solved
Traditional campus placement and recruitment systems suffer from fragmented academic records, unverifiable semester grade cards, resume-application desynchronization, candidate privacy leaks, and opaque shortlisting criteria. Talentra solves this through:
- **Canonical Actor Identities**: Immutable server-allocated IDs (`CA00001`–`CA99999`, `EM00001`–`EM99999`, etc.) that guarantee zero identity collisions or spoofing.
- **Auditable Academic & Document Vaults**: Flexible education pathways (Secondary, Higher Secondary, Polytechnic Diploma, Undergraduate, Postgraduate) paired with semester-by-semester grade cards and private object storage with magic byte validation.
- **Application Resume Version Snapshots**: Applications permanently freeze the exact resume version submitted, ensuring candidate profile updates never alter historical hiring records.
- **Automated Eligibility Engine**: Multi-criterion rule evaluation (`ELIGIBLE`, `NOT_ELIGIBLE`, `UNABLE_TO_DETERMINE`) based on structured degree, branch, percentage, CGPA, and backlog rules.
- **Append-Only Financial & Audit Ledgers**: Double-entry wallet transactions, payment webhooks, and audit logs protected by PostgreSQL triggers.

---

## 2. Key Capabilities by Architecture Module (M01–M13)

Talentra encompasses **13 fully realized backend modules** mapped to the 221-table database blueprint:

| Module Code | Module Name | Key Capabilities |
| :--- | :--- | :--- |
| **M01** | **Core Master Data** | ISO 3166-1 countries (249 records), ISO 639-1 languages (13 records), ISO 4217 currencies (10 records), system roles, permissions, document categories, job roles, and employment types. |
| **M02** | **Candidate Profile & Academics** | Demographic details, contact verification, profile photo vault, multi-pathway education records, semester grade cards (1..12), multi-version resume manager, skills, projects, certifications, work experience, and dynamic profile completeness engine. |
| **M03** | **Jobs & Applications Pipeline** | Structured job requisition creation, salary bands, position quotas, multi-stage application pipeline (`APPLIED`, `SCREENING`, `INTERVIEW`, `OFFERED`, `HIRED`, `REJECTED`, `WITHDRAWN`), candidate blocking, and application resume snapshots. |
| **M04** | **Administration & RBAC Identity** | User provisioning, multi-role assignments, actor identity resolution, tenant administration, API credentials with SHA-256 hashing, and system audit event logging. |
| **M05** | **Organisation & Account** | Multi-tenant company workspaces, employer account hierarchies, recruiter organisation mapping, billing profiles, and office locations. |
| **M06** | **Gig Marketplace** | Milestone-based contract management, escrow-backed deliverables, review workflows, dispute resolution, and payment disbursements. |
| **M07** | **Licences, Seats, Devices & Sessions** | Enterprise subscription seats, hardware device fingerprinting, session concurrency caps, and remote device revocation. |
| **M08** | **Sourcing & Consultant Requests** | Agency requisition assignments, candidate submission limits, consultant commissions, and vendor performance metrics. |
| **M09** | **Subscriptions, Wallets & Payments** | Multi-currency digital wallets, immutable append-only ledger entries, Stripe/Razorpay webhook processing, and credit purchases. |
| **M10** | **Notifications & Community** | Multi-channel delivery (Email, SMS, Push, In-App), delivery attempt tracking, candidate discussion boards, and campus announcement feeds. |
| **M11** | **Analytics & Reporting** | Star-schema OLAP marts, placement conversion funnels, salary distribution aggregations, and recruitment velocity reporting. |
| **M12** | **Government ID Verification** | KYC identity pipelines (SurePass, DigiLocker), document hash verification, and ClamAV quarantine integration. |
| **M13** | **Audit & Data Retention** | Statutory retention policies (7-year KYC archive, 30-day session purge), tamper-evident audit history, and compliance exports. |

---

## 3. The Nine Talentra Actor Roles & Permissions

Talentra enforces strict Role-Based Access Control (RBAC) across nine dedicated personas. UI navigation and server-side endpoints enforce tenant boundaries:

```
+---------------------------------------------------------------------------------------+
|                                TALENTRA ROLE MATRIX                                   |
+-------------------+---------------+---------------------------------------------------+
| Role Name         | Actor Prefix  | Responsibilities & Permissions                    |
+-------------------+---------------+---------------------------------------------------+
| SUPER_ADMIN       | SA            | System-wide master administration, global metrics |
| ADMIN             | AD            | Platform operations, tenant oversight, governance|
| ACCOUNT_ADMIN     | AA            | Organisation billing, seats, licences & users    |
| GUEST             | GU            | Anonymous discovery, public job directory browsing|
| CANDIDATE         | CA            | Profile, academics, resumes, jobs, applications   |
| EMPLOYER          | EM            | Requisition authoring, hiring pipeline review     |
| RECRUITER         | RC            | Candidate shortlisting, interview pipeline actions|
| CONSULTANT        | CO            | External talent sourcing & candidate submissions  |
| PLACEMENT_OFFICER | PO            | College TPO, student batches, campus placement drives|
+-------------------+---------------+---------------------------------------------------+
```

---

## 4. System Architecture

Talentra pairs a modern Next.js App Router frontend with a high-throughput FastAPI service backed by Supabase PostgreSQL and secure storage vaults:

```mermaid
graph TD
    Client[Browser Client / Next.js 16 App] -->|HTTPS / REST API| APIGateway[FastAPI Backend / Uvicorn]
    Client -->|Next.js Server Actions| NextServer[Next.js SSR / SSG Runtime]

    subgraph Backend Core
        APIGateway --> Security[Security & RBAC Middleware]
        Security --> Router[FastAPI APIRouter Modules]
        Router --> Services[Business Services Layer]
        Services --> StorageService[Storage Service & Magic Byte Validator]
        Services --> EligibilityEngine[Structured Eligibility Engine]
        Services --> AuditLogger[Immutable Audit Logger]
    end

    subgraph Data & Storage
        Services -->|SQLAlchemy 2.0 / Psycopg 3| SupabaseDB[(Supabase PostgreSQL 15+)]
        StorageService -->|Short-lived Signed URLs / Streaming| SupabaseStorage[(Supabase Private Storage)]
        StorageService -->|Resilient Fallback| LocalVault[(Storage Vault Fallback)]
    end

    subgraph External Services
        Services --> Stripe[Stripe / Razorpay Payments]
        Services --> SurePass[SurePass / DigiLocker KYC]
        Services --> SendGrid[SendGrid / Twilio Notifications]
        Services --> ClamAV[ClamAV Threat Scanning]
    end
```

---

## 5. Technology Stack

### Frontend
- **Framework**: [Next.js 16.4.2](https://nextjs.org/) (App Router, Turbopack, Partial Prerendering)
- **UI Engine**: [React 19](https://react.dev/), [Tailwind CSS 3.4](https://tailwindcss.com/)
- **Icons & Visuals**: [Lucide React](https://lucide.dev/)
- **State & Theme**: Theme Provider (Light mode default with dark mode support)
- **Testing**: [Vitest 3.0](https://vitest.dev/), [@testing-library/react](https://testing-library.com/)

### Backend
- **Framework**: [FastAPI 0.115+](https://fastapi.tiangolo.com/) (ASGI, Python 3.11+)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/latest/) & Pydantic Settings
- **ORM & Database Driver**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [Psycopg 3](https://www.psycopg.org/psycopg3/)
- **Migrations**: [Alembic 1.13+](https://alembic.sqlalchemy.org/)
- **Security & Cryptography**: Python-JOSE (JWT), Passlib / Bcrypt, Cryptography, Magic Byte Inspection
- **Testing**: [Pytest 8.4+](https://docs.pytest.org/)

### Database & Cloud
- **Database**: [Supabase PostgreSQL 15+](https://supabase.com/) with native extensions (`btree_gist`, GiST constraints)
- **Object Storage**: Supabase Private Buckets (`talentra-documents`)
- **CI/CD**: GitHub Actions (`production-release.yml`)

---

## 6. Repository Directory Structure

```text
Talentra/
├── .github/
│   └── workflows/
│       └── production-release.yml     # Complete CI/CD release pipeline
├── alembic/                           # Database migration scripts & environment
│   ├── versions/                      # 15 Linear Alembic migration revisions
│   └── env.py                         # Migration runtime configuration
├── backend/                           # FastAPI backend service
│   └── app/
│       ├── api/v1/                    # API route definitions
│       │   ├── endpoints/             # candidates, jobs, applications, admin, etc.
│       │   └── router.py              # Central APIRouter aggregator
│       ├── core/                      # Config, security, database session setup
│       ├── models/                    # SQLAlchemy ORM models (221 tables)
│       ├── schemas/                   # Pydantic v2 validation schemas
│       ├── services/                  # Business logic & storage vault handling
│       └── main.py                    # FastAPI application entrypoint
├── docs/                              # Comprehensive documentation suite
│   ├── architecture/                  # System, Database & API specifications
│   ├── development/                   # Local setup, testing & seeding runbooks
│   ├── operations/                    # Deployment, security & disaster recovery
│   ├── product/                       # Personas matrix & design system
│   ├── requirements/                  # Product specifications & business rules
│   └── TALENTRA_CANDIDATE_PROFILE_ACADEMIC_DOCUMENTS.md # Module specification
├── frontend/                          # Next.js 16 Web Application
│   ├── public/                        # Static assets & illustrations
│   └── src/
│       ├── app/                       # 39 Next.js App Router routes & 9 portals
│       ├── components/                # UI design system & layout shells
│       ├── lib/                       # API clients, auth context, utilities
│       └── types/                     # TypeScript strict interfaces
├── scratch/                           # Runtime scratch directory (checkpoints & reports)
│   └── .gitkeep                       # Preserved directory marker
├── scripts/                           # Seeding & automation tools
│   └── seed/                          # Scalable synthetic data generator (Profiles A–E)
├── tests/                             # Pytest test suite (266 unit & integration tests)
├── .env.example                       # Root environment configuration template
├── alembic.ini                        # Alembic CLI configuration
├── pyproject.toml                     # Pytest & tool configuration
├── requirements.txt                   # Backend Python dependencies
├── README.md                          # Root system overview & comprehensive data dictionary
├── Talentra_Database_Blueprint_150plus_Tables.xlsx # Authoritative 150+ tables schema blueprint
├── Talentra_Final_Test_Cases_All_Modules.xlsx      # Master test cases across all modules
├── Talentra_PostgreSQL_Schema_Audited_Draft.sql    # Audited PostgreSQL draft DDL
└── Talentra-Database-Design-Hackathon-Docket(3).pdf # Original hackathon requirements docket
```

---

## 7. Prerequisites

Before setting up Talentra, ensure the following tools are installed:

- **Python**: `3.11` or higher (`python --version`)
- **Node.js**: `20.x` or higher (`node --version`)
- **npm**: `10.x` or higher (`npm --version`)
- **PostgreSQL**: `15+` (or an active Supabase project)
- **Git**: `2.40+`

---

## 8. Environment Configuration

Copy `.env.example` to `.env` in the repository root:
```bash
cp .env.example .env
```

### Key Environment Variables

| Variable Name | Required | Service | Purpose & Example Placeholder |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Yes | Backend | `development`, `testing`, or `production` |
| `APP_DEBUG` | Yes | Backend | `true` for development, `false` for production |
| `DATABASE_URL` | Yes | Backend | `postgresql+psycopg://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres` |
| `MIGRATION_DATABASE_URL` | No | Alembic | Optional direct port 5432 connection for DDL migrations |
| `DB_POOL_SIZE` | No | Backend | Maximum connection pool size (default: `10`) |
| `SUPABASE_URL` | Yes | Backend | `https://[PROJECT-REF].supabase.co` |
| `SUPABASE_ANON_KEY` | Yes | Backend | Browser-safe Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY`| Yes | Backend | **Server-only** administrative key for private Storage vault |
| `SUPABASE_JWT_SECRET` | Yes | Backend | JWT secret matching Supabase Auth |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | Frontend | `http://localhost:8000/api/v1` (client API gateway) |
| `NEXT_PUBLIC_APP_NAME` | Yes | Frontend | `Talentra` |
| `NEXT_PUBLIC_APP_ENV` | Yes | Frontend | `development` or `production` |

> [!WARNING]
> Never commit `.env` or expose `SUPABASE_SERVICE_ROLE_KEY` to frontend client bundles.

---

## 9. Installation & Local Development

### 9.1. Backend Service
```powershell
# 1. Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
Copy-Item .env.example .env   # On Windows (cp on Linux)
# Edit .env with your database connection details

# 4. Verify database connectivity & migrations
python -m alembic current
python -m alembic upgrade head

# 5. Launch FastAPI development server (Port 8000)
$env:PYTHONPATH="backend"
uvicorn app.main:app --reload --port 8000
```
- API Base URL: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 9.2. Frontend Web Application
```bash
# 1. Navigate to frontend workspace
cd frontend

# 2. Install dependencies
npm install

# 3. Launch Next.js development server (Port 3000)
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

---

---

## 10. Comprehensive Database Architecture, Modules & Entity Encyclopedia
Talentra is powered by a high-performance **PostgreSQL 15+** database provisioned on **Supabase**, featuring **221 relational tables** partitioned into **13 business architecture modules** plus Alembic version control.
### 10.1 Database Infrastructure & Advanced Features
- **PostgreSQL Extensions**: `btree_gist` enabled to support high-performance GiST multidimensional exclusion constraints.
- **GiST Temporal Exclusion Constraints**:
  1. `excl_subscription_licence_period`: Prevents overlapping active enterprise subscription seat and licence validities.
  2. `excl_gig_worker_availability_window`: Prevents overlapping gig worker execution time commitments across concurrent contracts.
- **Immutable Append-Only Triggers**:
  1. `trg_immutable_audit_event` on `audit_events`: Aborts any `UPDATE` or `DELETE` to safeguard regulatory compliance.
  2. `trg_immutable_wallet_ledger` on `wallet_ledgers`: Enforces double-entry ledger finality; adjustments require counterbalancing entries.
  3. `trg_immutable_payment_transaction` on `payment_transactions`: Guarantees financial payment records cannot be altered or removed.
  4. `trg_immutable_profile_download_history` on `profile_download_history`: Ensures candidate resume download non-repudiation.
- **Deterministic Canonical Actor Identifiers**:
  - Generated via stored PostgreSQL function `allocate_actor_id(p_role_code, p_user_id, p_org_id)`.
  - Format: `CA00001` (Candidate), `EM00001` (Employer), `RE00001` (Recruiter), `CO00001` (Consultant), `PO00001` (Placement Officer), `SA00001` (Super Admin), `AD00001` (Admin), `AC00001` (Account Admin), `GU00001` (Guest).
- **Connection Topologies**:
  - **Direct Port 5432**: Required for Alembic schema migrations, prepared statements, and transactional DDL.
  - **Session Pooler Port 6543**: Optimized for high-concurrency runtime application queries.

### 10.2 Alembic Migration Linear Chain
All schema modifications strictly follow a linear version history without branching:
```text
000_enable_btree_gist
  └── 001_core_master_data (24 tables)
        └── 002_organisation_and_account (19 tables)
              └── 003_administration_and_identity (14 tables)
                    └── 004_candidate_profile (28 tables)
                          └── 005_jobs_and_applications (29 tables)
                                └── 006_gig_marketplace (15 tables)
                                      └── 007_licences_seats_devices (8 tables)
                                            └── 008_sourcing_and_consultants (10 tables)
                                                  └── 009_subscriptions_wallet_payments (17 tables)
                                                        └── 010_notifications_and_community (10 tables)
                                                              └── 011_analytics_reporting_marts (17 tables)
                                                                    └── 012_government_id_and_extensions (9 tables)
                                                                          └── 013_business_constraints_and_indexes
                                                                                └── 014_actor_ids_and_country_master
                                                                                      └── 015_candidate_academics_jobs (HEAD)
```

### 10.3 Module M01: Core Master Data, Geographies & Taxonomies
**Primary Domain**: Platform Reference Taxonomies | **Total Entities**: 24

Global ISO master reference taxonomies including ISO 3166-1 alpha-2/3 countries, ISO 4217 currencies, ISO 639-1 languages, states, cities, qualification hierarchies, skills taxonomy, job roles, industries, and localized UI translation strings.

**Key Architectural Invariants**:
- All ISO master data tables are immutable during standard operations and seeded via idempotent migration fixtures.
- Hierarchical taxonomies (industry, skill, qualification) support self-referential parent-child DAG relations.
- Localized translation keys map 1:N with supported platform languages.

#### Complete Entity Data Dictionary (24 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `city` | 11 | `id` | `state_id` &rarr; `state` | Stores City records including tenant mappings, metadata, and operational status. |
| `city_alias` | 10 | `id` | *None (Root)* | Stores City alias records including tenant mappings, metadata, and operational status. |
| `country` | 12 | `id` | *None (Root)* | Stores Country records including tenant mappings, metadata, and operational status. |
| `country_phone_rule` | 10 | `id` | *None (Root)* | Stores Country phone rule records including tenant mappings, metadata, and operational status. |
| `currency` | 10 | `id` | *None (Root)* | Stores Currency records including tenant mappings, metadata, and operational status. |
| `employment_type` | 10 | `id` | *None (Root)* | Stores Employment type records including tenant mappings, metadata, and operational status. |
| `employment_type_translation` | 9 | `id` | `language_id` &rarr; `language` | Localized language translation catalog for employment type. |
| `faq` | 10 | `id` | *None (Root)* | Stores Faq records including tenant mappings, metadata, and operational status. |
| `industry` | 9 | `id` | `parent_industry_id` &rarr; `industry` | Stores Industry records including tenant mappings, metadata, and operational status. |
| `industry_translation` | 9 | `id` | `language_id` &rarr; `language` | Localized language translation catalog for industry. |
| `job_role` | 9 | `id` | `industry_id` &rarr; `industry` | Stores Job role records including tenant mappings, metadata, and operational status. |
| `language` | 9 | `id` | *None (Root)* | Stores Language records including tenant mappings, metadata, and operational status. |
| `qualification` | 8 | `id` | *None (Root)* | Stores Qualification records including tenant mappings, metadata, and operational status. |
| `qualification_level` | 10 | `id` | *None (Root)* | Stores Qualification level records including tenant mappings, metadata, and operational status. |
| `reference_code` | 10 | `id` | `reference_domain_id` &rarr; `reference_domain` | Stores Reference code records including tenant mappings, metadata, and operational status. |
| `reference_code_translation` | 9 | `id` | `reference_code_id` &rarr; `reference_code`, `language_id` &rarr; `language` | Localized language translation catalog for reference code. |
| `reference_domain` | 8 | `id` | *None (Root)* | Stores Reference domain records including tenant mappings, metadata, and operational status. |
| `skill` | 9 | `id` | `parent_skill_id` &rarr; `skill` | Stores Skill records including tenant mappings, metadata, and operational status. |
| `skill_alias` | 10 | `id` | *None (Root)* | Stores Skill alias records including tenant mappings, metadata, and operational status. |
| `state` | 9 | `id` | `country_id` &rarr; `country` | Stores State records including tenant mappings, metadata, and operational status. |
| `ui_translation` | 9 | `id` | `ui_translation_key_id` &rarr; `ui_translation_key`, `language_id` &rarr; `language` | Localized language translation catalog for ui. |
| `ui_translation_key` | 7 | `id` | *None (Root)* | Localized language translation catalog for ui key. |
| `work_type` | 10 | `id` | *None (Root)* | Stores Work type records including tenant mappings, metadata, and operational status. |
| `work_type_translation` | 9 | `id` | `language_id` &rarr; `language` | Localized language translation catalog for work type. |

---

### 10.4 Module M02: Candidate Profiles, Academics, Resumes & Documents
**Primary Domain**: Candidate Profile & Academic Vault | **Total Entities**: 28

Comprehensive candidate master entities tracking identity, demographic data, multi-pathway education history, semester-by-semester grade sheets, multi-version resumes, skills, work experience, certifications, portfolio projects, and secure document vaults.

**Key Architectural Invariants**:
- Every candidate is assigned an immutable canonical Actor ID (e.g. CA00001) generated by PostgreSQL sequence allocation.
- Semester records track SGPA, CGPA, credits registered/earned, and backlog status with unique constraint per education level.
- Resumes support multi-version uploads; applications snapshot the active resume version at time of submission.
- Candidate documents and grade sheets are stored in private Supabase vaults with SHA-256 integrity validation.

#### Complete Entity Data Dictionary (28 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `candidate_activity_log` | 10 | `id` | *None (Root)* | Stores Candidate activity log records including tenant mappings, metadata, and operational status. |
| `candidate_application_history` | 10 | `id` | *None (Root)* | Stores Candidate application history records including tenant mappings, metadata, and operational status. |
| `candidate_assessment` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate assessment records including tenant mappings, metadata, and operational status. |
| `candidate_assessment_answer` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate assessment answer records including tenant mappings, metadata, and operational status. |
| `candidate_bookmark` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate bookmark records including tenant mappings, metadata, and operational status. |
| `candidate_certification` | 16 | `id` | `candidate_profile_id` &rarr; `candidate_profile` | Stores Candidate certification records including tenant mappings, metadata, and operational status. |
| `candidate_contact` | 12 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `city_id` &rarr; `city` | Stores Candidate contact records including tenant mappings, metadata, and operational status. |
| `candidate_contact_attempt` | 11 | `id` | `candidate_contact_id` &rarr; `candidate_contact` | Stores Candidate contact attempt records including tenant mappings, metadata, and operational status. |
| `candidate_contact_consent` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate contact consent records including tenant mappings, metadata, and operational status. |
| `candidate_course_enrolment` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate course enrolment records including tenant mappings, metadata, and operational status. |
| `candidate_document` | 18 | `id` | `candidate_profile_id` &rarr; `candidate_profile` | Private candidate document vault storing academic certificates, government IDs, and transcripts with magic-byte validation. |
| `candidate_education` | 31 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `qualification_id` &rarr; `qualification` | Multi-pathway academic history (10th, 12th, Diploma, UG, PG) with school/university, degree, branch, grading system, and score. |
| `candidate_education_semester` | 22 | `id` | `candidate_education_id` &rarr; `candidate_education`, `candidate_profile_id` &rarr; `candidate_profile` | Term-by-term academic performance tracking SGPA, CGPA, credits registered/earned, backlogs, and semester grade sheet object keys. |
| `candidate_job_search_history` | 10 | `id` | *None (Root)* | Stores Candidate job search history records including tenant mappings, metadata, and operational status. |
| `candidate_language` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `language_id` &rarr; `language` | Stores Candidate language records including tenant mappings, metadata, and operational status. |
| `candidate_profile` | 32 | `id` | `user_id` &rarr; `user`, `current_country_id` &rarr; `country` | Candidate master profile storing demographic info, contact details, profile completion score, and unique actor ID. |
| `candidate_profile_language` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate profile language records including tenant mappings, metadata, and operational status. |
| `candidate_profile_visibility_history` | 10 | `id` | *None (Root)* | Stores Candidate profile visibility history records including tenant mappings, metadata, and operational status. |
| `candidate_project` | 15 | `id` | `candidate_profile_id` &rarr; `candidate_profile` | Stores Candidate project records including tenant mappings, metadata, and operational status. |
| `candidate_project_skill` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate project skill records including tenant mappings, metadata, and operational status. |
| `candidate_referral` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate referral records including tenant mappings, metadata, and operational status. |
| `candidate_referral_attribution` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate referral attribution records including tenant mappings, metadata, and operational status. |
| `candidate_resume` | 9 | `id` | `candidate_profile_id` &rarr; `candidate_profile` | Stores Candidate resume records including tenant mappings, metadata, and operational status. |
| `candidate_skill` | 12 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `skill_id` &rarr; `skill` | Stores Candidate skill records including tenant mappings, metadata, and operational status. |
| `candidate_sourcing_shortlist` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Candidate sourcing shortlist records including tenant mappings, metadata, and operational status. |
| `candidate_work_experience` | 14 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `job_role_id` &rarr; `job_role` | Stores Candidate work experience records including tenant mappings, metadata, and operational status. |
| `resume_template` | 10 | `id` | *None (Root)* | Stores Resume template records including tenant mappings, metadata, and operational status. |
| `resume_version` | 16 | `id` | `candidate_resume_id` &rarr; `candidate_resume`, `language_id` &rarr; `language` | Multi-version resume asset registry tracking storage keys, file metadata, SHA-256 hashes, target roles, and archive flags. |

---

### 10.5 Module M03: Jobs, Requirements, Applications & Hiring Pipeline
**Primary Domain**: Requisition Management & Applicant Tracking | **Total Entities**: 29

Job opening requisitions, structured eligibility criteria (qualifications, skills, GPA cutoffs, active backlogs), multi-stage applicant tracking pipeline, custom screening questionnaires, interview rounds, offers, and hiring records.

**Key Architectural Invariants**:
- Job requirements define machine-readable eligibility criteria for real-time automated candidate evaluation.
- Job application status progresses through an auditable state machine with status transition history tracking.
- Applications permanently freeze candidate resume version ID and metadata to prevent historical record alteration.
- Candidate blocking rules prevent restricted candidates from discovering or applying to designated enterprise jobs.

#### Complete Entity Data Dictionary (29 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `application_answer` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application answer records including tenant mappings, metadata, and operational status. |
| `application_feedback` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Structured qualitative and quantitative feedback records for application. |
| `application_interview` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application interview records including tenant mappings, metadata, and operational status. |
| `application_interview_feedback` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Structured qualitative and quantitative feedback records for application interview. |
| `application_join_record` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application join record records including tenant mappings, metadata, and operational status. |
| `application_offer` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application offer records including tenant mappings, metadata, and operational status. |
| `application_rejection` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application rejection records including tenant mappings, metadata, and operational status. |
| `application_shortlist` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Application shortlist records including tenant mappings, metadata, and operational status. |
| `application_status_history` | 11 | `id` | `job_application_id` &rarr; `job_application` | Auditable lifecycle status change log for application. |
| `assessment_question` | 11 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Assessment question records including tenant mappings, metadata, and operational status. |
| `job_alert_preference` | 10 | `id` | `user_id` &rarr; `user` | Stores Job alert preference records including tenant mappings, metadata, and operational status. |
| `job_application` | 17 | `id` | `job_requirement_id` &rarr; `job_requirement`, `candidate_profile_id` &rarr; `candidate_profile`, `resume_version_id` &rarr; `resume_version` | Job application record linking candidate to job requisition, freezing submitted resume version ID, and recording eligibility evaluation. |
| `job_bookmark` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job bookmark records including tenant mappings, metadata, and operational status. |
| `job_position` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement` | Stores Job position records including tenant mappings, metadata, and operational status. |
| `job_publish_history` | 10 | `id` | *None (Root)* | Stores Job publish history records including tenant mappings, metadata, and operational status. |
| `job_questionnaire` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job questionnaire records including tenant mappings, metadata, and operational status. |
| `job_questionnaire_option` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job questionnaire option records including tenant mappings, metadata, and operational status. |
| `job_questionnaire_question` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job questionnaire question records including tenant mappings, metadata, and operational status. |
| `job_requirement` | 35 | `id` | `organisation_id` &rarr; `organisation`, `job_role_id` &rarr; `job_role`, `employment_type_id` &rarr; `employment_type`, +1 more | Enterprise job requisition defining structured role criteria, experience spans, salary ranges, and machine-readable eligibility cutoffs. |
| `job_requirement_employment_type` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job requirement employment type records including tenant mappings, metadata, and operational status. |
| `job_requirement_location` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job requirement location records including tenant mappings, metadata, and operational status. |
| `job_requirement_qualification` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job requirement qualification records including tenant mappings, metadata, and operational status. |
| `job_requirement_skill` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job requirement skill records including tenant mappings, metadata, and operational status. |
| `job_requirement_status_history` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement` | Auditable lifecycle status change log for job requirement. |
| `job_requirement_work_type` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job requirement work type records including tenant mappings, metadata, and operational status. |
| `job_search_saved_filter` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Job search saved filter records including tenant mappings, metadata, and operational status. |
| `job_view_history` | 10 | `id` | *None (Root)* | Stores Job view history records including tenant mappings, metadata, and operational status. |
| `salary_benchmark` | 10 | `id` | *None (Root)* | Stores Salary benchmark records including tenant mappings, metadata, and operational status. |
| `trending_job_snapshot` | 11 | `id` | `job_requirement_id` &rarr; `job_requirement`, `job_application_id` &rarr; `job_application`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Trending job snapshot records including tenant mappings, metadata, and operational status. |

---

### 10.6 Module M04: Administration, Identity, RBAC & Privacy
**Primary Domain**: Identity & Access Management | **Total Entities**: 14

Core user authentication records, identity sessions, multi-factor credentials, role-permission matrices, actor identity allocations, consent audit records, and user privacy preferences.

**Key Architectural Invariants**:
- Supports 9 distinct actor roles (Super Admin, Admin, Account Admin, Guest, Candidate, Employer, Recruiter, Consultant, Placement Officer).
- Actor identities are strictly partitioned via user_actor_identity linking users, roles, and tenant organisations.
- API credentials store salted SHA-256 hashes with automated revocation and expiration enforcement.

#### Complete Entity Data Dictionary (14 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `access_policy` | 10 | `id` | *None (Root)* | Stores Access policy records including tenant mappings, metadata, and operational status. |
| `consent_record` | 12 | `id` | `user_id` &rarr; `user` | Stores Consent record records including tenant mappings, metadata, and operational status. |
| `credential` | 10 | `id` | `user_id` &rarr; `user` | Stores Credential records including tenant mappings, metadata, and operational status. |
| `identity_session` | 14 | `id` | `user_id` &rarr; `user` | Stores Identity session records including tenant mappings, metadata, and operational status. |
| `permission` | 10 | `id` | *None (Root)* | Stores Permission records including tenant mappings, metadata, and operational status. |
| `permission_change_request` | 10 | `id` | *None (Root)* | Stores Permission change request records including tenant mappings, metadata, and operational status. |
| `privacy_preference` | 10 | `id` | `user_id` &rarr; `user` | Stores Privacy preference records including tenant mappings, metadata, and operational status. |
| `role` | 10 | `id` | *None (Root)* | Stores Role records including tenant mappings, metadata, and operational status. |
| `role_assignment_history` | 10 | `id` | *None (Root)* | Stores Role assignment history records including tenant mappings, metadata, and operational status. |
| `role_dashboard_config` | 10 | `id` | *None (Root)* | Stores Role dashboard config records including tenant mappings, metadata, and operational status. |
| `role_permission` | 9 | `id` | `role_id` &rarr; `role`, `permission_id` &rarr; `permission` | Stores Role permission records including tenant mappings, metadata, and operational status. |
| `user` | 12 | `id` | *None (Root)* | Core platform user authentication account with hashed credentials, email status, and MFA verification state. |
| `user_actor_identity` | 13 | `id` | `user_id` &rarr; `user`, `role_id` &rarr; `role`, `organisation_id` &rarr; `organisation` | Canonical actor identity mapping assigning deterministic actor IDs (CA, EM, RE, CO, PO, SA, AD, AC, GU) to users. |
| `user_role_assignment` | 14 | `id` | `user_id` &rarr; `user`, `role_id` &rarr; `role`, `organisation_id` &rarr; `organisation` | Stores User role assignment records including tenant mappings, metadata, and operational status. |

---

### 10.7 Module M05: Organisations, Accounts & Enterprise Workspaces
**Primary Domain**: Multi-Tenant Enterprise Workspaces | **Total Entities**: 19

Enterprise tenant workspaces, corporate account hierarchies (parent-child organisations), business units, recruiter mappings, office locations, billing accounts, and verified enterprise domains.

**Key Architectural Invariants**:
- Organisation hierarchy closure table enables fast recursive querying of enterprise corporate structures.
- Recruiters are mapped to specific organisations with distinct permission boundaries and hiring requisition quotas.
- Corporate domains require cryptographic DNS verification before granting automatic corporate email onboarding.

#### Complete Entity Data Dictionary (19 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `account` | 11 | `id` | *None (Root)* | Stores Account records including tenant mappings, metadata, and operational status. |
| `account_admin_assignment` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Account admin assignment records including tenant mappings, metadata, and operational status. |
| `account_organisation` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Account organisation records including tenant mappings, metadata, and operational status. |
| `account_recovery_request` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Account recovery request records including tenant mappings, metadata, and operational status. |
| `account_status_history` | 11 | `id` | `account_id` &rarr; `account` | Auditable lifecycle status change log for account. |
| `organisation` | 12 | `id` | `parent_organisation_id` &rarr; `organisation` | Enterprise company profile with industry classification, corporate hierarchy linkage, and verification badge status. |
| `organisation_contact` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation contact records including tenant mappings, metadata, and operational status. |
| `organisation_document_reference` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation document reference records including tenant mappings, metadata, and operational status. |
| `organisation_domain` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation domain records including tenant mappings, metadata, and operational status. |
| `organisation_hierarchy_closure` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation hierarchy closure records including tenant mappings, metadata, and operational status. |
| `organisation_identifier` | 12 | `id` | `organisation_id` &rarr; `organisation`, `country_id` &rarr; `country` | Stores Organisation identifier records including tenant mappings, metadata, and operational status. |
| `organisation_location` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation location records including tenant mappings, metadata, and operational status. |
| `organisation_profile` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation profile records including tenant mappings, metadata, and operational status. |
| `organisation_rating_aggregate` | 10 | `id` | *None (Root)* | Pre-computed aggregate rollups for high-throughput dashboard analytics. |
| `organisation_recruiter_mapping` | 11 | `id` | `organisation_id` &rarr; `organisation` | Stores Organisation recruiter mapping records including tenant mappings, metadata, and operational status. |
| `organisation_review` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation review records including tenant mappings, metadata, and operational status. |
| `organisation_status_history` | 11 | `id` | `organisation_id` &rarr; `organisation` | Auditable lifecycle status change log for organisation. |
| `organisation_verification` | 12 | `id` | `organisation_id` &rarr; `organisation`, `account_id` &rarr; `account` | Stores Organisation verification records including tenant mappings, metadata, and operational status. |
| `organisation_verification_event` | 11 | `id` | `organisation_verification_id` &rarr; `organisation_verification` | High-resolution security and telemetry event records for organisation verification. |

---

### 10.8 Module M06: Gig Marketplace & On-Demand Contracts
**Primary Domain**: Freelance Work & Milestone Contracting | **Total Entities**: 15

On-demand freelance gig requests, worker profiles, skill catalogues, project bids, milestone-based execution contracts, availability windows, deliverables handoff, and escrow reconciliation.

**Key Architectural Invariants**:
- Worker availability windows enforce PostgreSQL GiST temporal exclusion constraints (excl_gig_worker_availability_window) preventing overlapping gig bookings.
- Milestone disbursements require mutual cryptographic sign-off between contractor and hiring employer.
- Contract ratings and reviews feed directly into public worker trust scores.

#### Complete Entity Data Dictionary (15 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `gig_application` | 12 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig application records including tenant mappings, metadata, and operational status. |
| `gig_application_status_history` | 11 | `id` | `gig_application_id` &rarr; `gig_application` | Auditable lifecycle status change log for gig application. |
| `gig_assignment` | 12 | `id` | `gig_application_id` &rarr; `gig_application`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig assignment records including tenant mappings, metadata, and operational status. |
| `gig_assignment_status_history` | 11 | `id` | `gig_assignment_id` &rarr; `gig_assignment` | Auditable lifecycle status change log for gig assignment. |
| `gig_earnings_reconciliation` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig earnings reconciliation records including tenant mappings, metadata, and operational status. |
| `gig_handoff_reference` | 11 | `id` | `gig_assignment_id` &rarr; `gig_assignment` | Stores Gig handoff reference records including tenant mappings, metadata, and operational status. |
| `gig_rating` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig rating records including tenant mappings, metadata, and operational status. |
| `gig_request` | 16 | `id` | *None (Root)* | Stores Gig request records including tenant mappings, metadata, and operational status. |
| `gig_request_status_history` | 11 | `id` | `gig_request_id` &rarr; `gig_request` | Auditable lifecycle status change log for gig request. |
| `gig_service_offering` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig service offering records including tenant mappings, metadata, and operational status. |
| `gig_worker_availability` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Freelance contractor availability schedule governed by GiST temporal exclusion constraint preventing duplicate project bookings. |
| `gig_worker_favourite_history` | 10 | `id` | *None (Root)* | Stores Gig worker favourite history records including tenant mappings, metadata, and operational status. |
| `gig_worker_list_entry` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig worker list entry records including tenant mappings, metadata, and operational status. |
| `gig_worker_profile` | 10 | `id` | `user_id` &rarr; `user` | Stores Gig worker profile records including tenant mappings, metadata, and operational status. |
| `gig_worker_skill` | 13 | `id` | `gig_request_id` &rarr; `gig_request`, `gig_worker_profile_id` &rarr; `gig_worker_profile` | Stores Gig worker skill records including tenant mappings, metadata, and operational status. |

---

### 10.9 Module M07: Licences, Seats, Devices & Session Tokens
**Primary Domain**: Licensing & Hardware Device Concurrency | **Total Entities**: 8

Enterprise subscription licences, seat allocations, hardware device fingerprinting, concurrent login counters, session token verification, and remote device revocation events.

**Key Architectural Invariants**:
- Licence seat allocations enforce GiST exclusion constraints (excl_subscription_licence_period) preventing overlapping active seat assignments.
- Device logins track hardware hashes; suspicious or excess concurrent sessions trigger automatic device revocation events.
- Licence status history captures comprehensive lifecycle transitions from trial to active, suspended, and expired.

#### Complete Entity Data Dictionary (8 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `device_login_counter` | 11 | `id` | `user_id` &rarr; `user`, `licence_id` &rarr; `licence` | Stores Device login counter records including tenant mappings, metadata, and operational status. |
| `device_revocation_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for device revocation. |
| `licence` | 13 | `id` | `account_id` &rarr; `account` | Stores Licence records including tenant mappings, metadata, and operational status. |
| `licence_entitlement` | 11 | `id` | `user_id` &rarr; `user`, `licence_id` &rarr; `licence` | Stores Licence entitlement records including tenant mappings, metadata, and operational status. |
| `licence_seat_allocation` | 11 | `id` | `user_id` &rarr; `user`, `licence_id` &rarr; `licence` | Enterprise subscription seat reservation protected by GiST temporal exclusion constraint preventing overlapping allocations. |
| `licence_status_history` | 11 | `id` | `licence_id` &rarr; `licence` | Auditable lifecycle status change log for licence. |
| `licence_usage_snapshot` | 11 | `id` | `user_id` &rarr; `user`, `licence_id` &rarr; `licence` | Stores Licence usage snapshot records including tenant mappings, metadata, and operational status. |
| `registered_device` | 12 | `id` | `user_id` &rarr; `user` | Stores Registered device records including tenant mappings, metadata, and operational status. |

---

### 10.10 Module M08: Sourcing & External Consultants
**Primary Domain**: Agency Sourcing & Representation Locks | **Total Entities**: 10

External recruitment consultant profiles, agency rate cards, talent sourcing requests, consultant candidate submissions, outreach campaigns, and candidate representation locking.

**Key Architectural Invariants**:
- Consultant candidate submissions enforce representation locking windows preventing multi-agency duplicate submission disputes.
- Sourcing requests support targeted candidate quotas and commission rate schedules.
- Outreach campaigns enforce candidate consent checks prior to automated messaging.

#### Complete Entity Data Dictionary (10 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `consultant_profile` | 12 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `user_id` &rarr; `user` | Stores Consultant profile records including tenant mappings, metadata, and operational status. |
| `consultant_rate_card` | 10 | `id` | *None (Root)* | Stores Consultant rate card records including tenant mappings, metadata, and operational status. |
| `consultant_request_assignment_history` | 10 | `id` | *None (Root)* | Stores Consultant request assignment history records including tenant mappings, metadata, and operational status. |
| `consultant_request_decision` | 10 | `id` | *None (Root)* | Stores Consultant request decision records including tenant mappings, metadata, and operational status. |
| `consultant_skill` | 10 | `id` | *None (Root)* | Stores Consultant skill records including tenant mappings, metadata, and operational status. |
| `outreach_batch` | 11 | `id` | `organisation_id` &rarr; `organisation`, `job_requirement_id` &rarr; `job_requirement` | Stores Outreach batch records including tenant mappings, metadata, and operational status. |
| `outreach_consent_check` | 10 | `id` | *None (Root)* | Stores Outreach consent check records including tenant mappings, metadata, and operational status. |
| `outreach_recipient` | 11 | `id` | `outreach_batch_id` &rarr; `outreach_batch`, `candidate_profile_id` &rarr; `candidate_profile` | Stores Outreach recipient records including tenant mappings, metadata, and operational status. |
| `sourcing_request` | 13 | `id` | `job_requirement_id` &rarr; `job_requirement` | Stores Sourcing request records including tenant mappings, metadata, and operational status. |
| `sourcing_request_status_history` | 11 | `id` | `sourcing_request_id` &rarr; `sourcing_request` | Auditable lifecycle status change log for sourcing request. |

---

### 10.11 Module M09: Subscriptions, Wallets & Financial Ledgers
**Primary Domain**: Billing, Digital Wallets & Append-Only Ledgers | **Total Entities**: 17

Multi-currency digital wallets, double-entry wallet ledgers, subscription tiers, recurring billing invoices, payment orders, payment transaction logs, and gateway webhook events.

**Key Architectural Invariants**:
- Wallet ledger entries are protected by PostgreSQL append-only triggers (trg_immutable_wallet_ledger); modifications or deletions are rejected at database level.
- Payment transactions are immutable (trg_immutable_payment_transaction) for financial auditability and statutory compliance.
- Credit consumption records track real-time talent search and candidate profile download deductions.

#### Complete Entity Data Dictionary (17 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `credit_consumption` | 11 | `id` | `account_id` &rarr; `account` | Stores Credit consumption records including tenant mappings, metadata, and operational status. |
| `invoice` | 15 | `id` | `account_id` &rarr; `account`, `subscription_id` &rarr; `subscription` | Stores Invoice records including tenant mappings, metadata, and operational status. |
| `invoice_line` | 11 | `id` | `account_id` &rarr; `account` | Stores Invoice line records including tenant mappings, metadata, and operational status. |
| `invoice_status_history` | 11 | `id` | `invoice_id` &rarr; `invoice` | Auditable lifecycle status change log for invoice. |
| `payment_order` | 13 | `id` | `account_id` &rarr; `account` | Stores Payment order records including tenant mappings, metadata, and operational status. |
| `payment_reconciliation_run` | 11 | `id` | `account_id` &rarr; `account` | Stores Payment reconciliation run records including tenant mappings, metadata, and operational status. |
| `payment_refund` | 11 | `id` | `account_id` &rarr; `account` | Stores Payment refund records including tenant mappings, metadata, and operational status. |
| `payment_transaction` | 12 | `id` | `payment_order_id` &rarr; `payment_order` | Stores Payment transaction records including tenant mappings, metadata, and operational status. |
| `payment_webhook_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for payment webhook. |
| `plan_entitlement` | 10 | `id` | *None (Root)* | Stores Plan entitlement records including tenant mappings, metadata, and operational status. |
| `subscription` | 14 | `id` | `account_id` &rarr; `account`, `subscription_plan_id` &rarr; `subscription_plan`, `licence_id` &rarr; `licence` | Stores Subscription records including tenant mappings, metadata, and operational status. |
| `subscription_cancellation` | 11 | `id` | `account_id` &rarr; `account` | Stores Subscription cancellation records including tenant mappings, metadata, and operational status. |
| `subscription_plan` | 12 | `id` | *None (Root)* | Stores Subscription plan records including tenant mappings, metadata, and operational status. |
| `subscription_renewal` | 11 | `id` | `account_id` &rarr; `account` | Stores Subscription renewal records including tenant mappings, metadata, and operational status. |
| `wallet` | 9 | `id` | `account_id` &rarr; `account` | Stores Wallet records including tenant mappings, metadata, and operational status. |
| `wallet_balance_snapshot` | 11 | `id` | `account_id` &rarr; `account` | Stores Wallet balance snapshot records including tenant mappings, metadata, and operational status. |
| `wallet_ledger_entry` | 14 | `id` | `wallet_id` &rarr; `wallet` | Double-entry wallet ledger entry protected by PostgreSQL append-only trigger for tamper-evident financial accounting. |

---

### 10.12 Module M10: Notifications & Community Discussion Forums
**Primary Domain**: Multi-Channel Communications & Campus Community | **Total Entities**: 10

Omnichannel notification dispatch (in-app, email, push, SMS), delivery attempt logs, user communication preferences, campus community discussion posts, comments, reactions, and moderation logs.

**Key Architectural Invariants**:
- Notification deliveries track real-time delivery attempts, bouncebacks, and provider response payloads.
- User notification preferences support granular channel-level opt-ins and quiet hours enforcement.
- Community forums provide automated content moderation events and multi-language post support.

#### Complete Entity Data Dictionary (10 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `community_comment` | 10 | `id` | *None (Root)* | Stores Community comment records including tenant mappings, metadata, and operational status. |
| `community_moderation_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for community moderation. |
| `community_post` | 11 | `id` | `language_id` &rarr; `language` | Stores Community post records including tenant mappings, metadata, and operational status. |
| `community_reaction` | 10 | `id` | *None (Root)* | Stores Community reaction records including tenant mappings, metadata, and operational status. |
| `notification` | 10 | `id` | `user_id` &rarr; `user` | Stores Notification records including tenant mappings, metadata, and operational status. |
| `notification_delivery` | 13 | `id` | `notification_id` &rarr; `notification` | Stores Notification delivery records including tenant mappings, metadata, and operational status. |
| `notification_delivery_attempt` | 11 | `id` | `notification_delivery_id` &rarr; `notification_delivery` | Stores Notification delivery attempt records including tenant mappings, metadata, and operational status. |
| `notification_preference` | 10 | `id` | `user_id` &rarr; `user` | Stores Notification preference records including tenant mappings, metadata, and operational status. |
| `notification_preference_history` | 11 | `id` | `notification_preference_id` &rarr; `notification_preference` | Stores Notification preference history records including tenant mappings, metadata, and operational status. |
| `notification_template` | 10 | `id` | `user_id` &rarr; `user` | Stores Notification template records including tenant mappings, metadata, and operational status. |

---

### 10.13 Module M11: Analytics Data Marts & Aggregates
**Primary Domain**: Star-Schema OLAP Marts & Placement KPIs | **Total Entities**: 17

Dimensional data warehouse star schema including dimensions (dim_candidate, dim_job, dim_organisation, dim_date, dim_status) and fact marts tracking recruitment funnels, wallet velocities, placement ratios, and daily dashboard snapshots.

**Key Architectural Invariants**:
- Fact marts provide pre-aggregated rollups for sub-second dashboard rendering across institutional and employer portals.
- Analytics refresh runs track batch ETL pipeline execution durations and data quality validations.
- Aggregates support historical cohort retention and salary trend comparisons.

#### Complete Entity Data Dictionary (17 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `aggregate_dashboard_daily` | 10 | `id` | *None (Root)* | Pre-computed aggregate rollups for high-throughput dashboard analytics. |
| `analytics_data_quality_issue` | 10 | `id` | *None (Root)* | Stores Analytics data quality issue records including tenant mappings, metadata, and operational status. |
| `analytics_kpi_definition` | 10 | `id` | *None (Root)* | Stores Analytics kpi definition records including tenant mappings, metadata, and operational status. |
| `analytics_refresh_run` | 10 | `id` | *None (Root)* | Stores Analytics refresh run records including tenant mappings, metadata, and operational status. |
| `dashboard_aggregate_config` | 10 | `id` | *None (Root)* | Pre-computed aggregate rollups for high-throughput dashboard analytics. |
| `dim_candidate` | 10 | `id` | *None (Root)* | Star-schema dimensional lookup table for candidate analytics. |
| `dim_date` | 12 | `id` | *None (Root)* | Star-schema dimensional lookup table for date analytics. |
| `dim_job` | 10 | `id` | *None (Root)* | Star-schema dimensional lookup table for job analytics. |
| `dim_organisation` | 10 | `id` | *None (Root)* | Star-schema dimensional lookup table for organisation analytics. |
| `dim_status` | 10 | `id` | *None (Root)* | Star-schema dimensional lookup table for status analytics. |
| `fact_application` | 11 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical application metrics. |
| `fact_gig_assignment` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical gig assignment metrics. |
| `fact_job_requirement` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical job requirement metrics. |
| `fact_notification_delivery` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical notification delivery metrics. |
| `fact_profile_activity` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical profile activity metrics. |
| `fact_profile_download` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical profile download metrics. |
| `fact_wallet_transaction` | 10 | `id` | *None (Root)* | Star-schema transactional fact mart tracking historical wallet transaction metrics. |

---

### 10.14 Module M12: Government ID & Verification (KYC)
**Primary Domain**: Identity Verification & Statutory KYC Compliance | **Total Entities**: 9

Government identity verification cases (Aadhaar, PAN, Passport, Voter ID), provider integrations (SurePass, DigiLocker), user consent audit trails, and statutory data retention compliance jobs.

**Key Architectural Invariants**:
- Identity verification cases store cryptographic document hashes rather than raw biometric payloads.
- User consent records mandate explicit timestamped acceptance before accessing government verification APIs.
- Verification retention jobs enforce statutory data purge policies (e.g. 7-year regulatory retention lifecycle).

#### Complete Entity Data Dictionary (9 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `government_document_reference` | 14 | `id` | `user_id` &rarr; `user` | Stores Government document reference records including tenant mappings, metadata, and operational status. |
| `identity_verification_case` | 15 | `id` | `user_id` &rarr; `user`, `consent_record_id` &rarr; `consent_record` | Government KYC verification workflow case linking candidate, verification provider, verification status, and consent token. |
| `identity_verification_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for identity verification. |
| `identity_verification_provider` | 10 | `id` | *None (Root)* | Stores Identity verification provider records including tenant mappings, metadata, and operational status. |
| `verification_access_log` | 11 | `id` | *None (Root)* | Stores Verification access log records including tenant mappings, metadata, and operational status. |
| `verification_consent_purpose` | 11 | `id` | `user_id` &rarr; `user` | Stores Verification consent purpose records including tenant mappings, metadata, and operational status. |
| `verification_provider_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for verification provider. |
| `verification_retention_job` | 11 | `id` | `user_id` &rarr; `user` | Stores Verification retention job records including tenant mappings, metadata, and operational status. |
| `verification_review` | 11 | `id` | `user_id` &rarr; `user` | Stores Verification review records including tenant mappings, metadata, and operational status. |

---

### 10.15 Module M13: Audit, Compliance & Event Logging
**Primary Domain**: Security Telemetry, Tamper-Evident Auditing & Support | **Total Entities**: 20

Platform-wide security telemetry, tamper-evident audit event logs, candidate profile download histories, login attempt telemetry, session anomaly alerts, support ticketing, and system error logs.

**Key Architectural Invariants**:
- Audit events are append-only and enforced by PostgreSQL trigger (trg_immutable_audit_event); updates and deletions are aborted.
- Profile download history enforces append-only rules (trg_immutable_profile_download_history) to ensure non-repudiation during resume exports.
- Login attempts track IP geolocation, device signatures, and failed credential anomalies.

#### Complete Entity Data Dictionary (20 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `api_client_registration` | 10 | `id` | *None (Root)* | Stores Api client registration records including tenant mappings, metadata, and operational status. |
| `audit_event` | 13 | `id` | *None (Root)* | System-wide compliance audit log entry protected by PostgreSQL immutable trigger recording actor, action, and target entity. |
| `block_list_entry` | 11 | `id` | *None (Root)* | Stores Block list entry records including tenant mappings, metadata, and operational status. |
| `feature_flag` | 10 | `id` | *None (Root)* | Stores Feature flag records including tenant mappings, metadata, and operational status. |
| `login_attempt` | 10 | `id` | *None (Root)* | Stores Login attempt records including tenant mappings, metadata, and operational status. |
| `login_device_decision` | 11 | `id` | `user_id` &rarr; `user`, `licence_id` &rarr; `licence` | Stores Login device decision records including tenant mappings, metadata, and operational status. |
| `profile_completion_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for profile completion. |
| `profile_download_history` | 12 | `id` | `candidate_profile_id` &rarr; `candidate_profile`, `organisation_id` &rarr; `organisation`, `credit_consumption_id` &rarr; `credit_consumption` | Immutable candidate profile export log tracking recruiter access, organisation tenant, and deducted wallet credit balance. |
| `profile_view_history` | 10 | `id` | *None (Root)* | Stores Profile view history records including tenant mappings, metadata, and operational status. |
| `referral_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for referral. |
| `resume_download_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for resume download. |
| `security_alert_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for security alert. |
| `security_policy_version` | 10 | `id` | *None (Root)* | Stores Security policy version records including tenant mappings, metadata, and operational status. |
| `session_activity_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for session activity. |
| `session_revocation_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for session revocation. |
| `social_share_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for social share. |
| `support_ticket` | 13 | `id` | *None (Root)* | Stores Support ticket records including tenant mappings, metadata, and operational status. |
| `support_ticket_message` | 10 | `id` | *None (Root)* | Stores Support ticket message records including tenant mappings, metadata, and operational status. |
| `support_ticket_status_history` | 11 | `id` | `support_ticket_id` &rarr; `support_ticket` | Auditable lifecycle status change log for support ticket. |
| `system_error_event` | 10 | `id` | *None (Root)* | High-resolution security and telemetry event records for system error. |

---

### 10.16 System Internal: Migration Revision Tracking
**Primary Domain**: Schema Migration State | **Total Entities**: 1

Alembic version tracking table that maintains the current linear migration state of the database.

**Key Architectural Invariants**:
- Maintains the linear revision history from 000_enable_btree_gist to 015_candidate_academics_jobs.

#### Complete Entity Data Dictionary (1 Tables)

| Entity / Table | Cols | Primary Key | Key Foreign Keys | Purpose & Business Rules |
| :--- | :---: | :--- | :--- | :--- |
| `alembic_version` | 1 | `id` | *None (Root)* | Internal Alembic migration state table tracking the current linear schema revision hash. |

---

---

## 11. Synthetic Data Seeding & Scaling

Talentra includes a high-throughput, configurable synthetic data generation framework supporting the hackathon docket's target volumes:

### Supported Profiles (`scripts/seed/seed_runner.py`)
- **Profile A (`reference`)**: Canonical reference data (249 countries, 13 languages, 10 currencies, roles, permissions).
- **Profile B (`system_config`)**: System admin accounts, baseline organizations, subscription and licence tiers.
- **Profile C (`dev_demo`)**: Development dataset with 500 candidates, 50 job requisitions, applications, and gigs.
- **Profile D (`functional_test`)**: Edge-case fixtures (arrears, cutoffs, blocking, concurrent applications).
- **Profile E (`scale_generator`)**: High-volume generator with checkpointing and batch insertion.

### Seeding Commands
```powershell
$env:PYTHONPATH="backend"

# Seed baseline reference master data (idempotent)
python scripts/seed/seed_runner.py --profile reference

# Seed development demo dataset
python scripts/seed/seed_runner.py --profile dev_demo

# Run the 12-point post-seed relational integrity validation suite
python scripts/seed/validator.py
```

### Docket Scale Targets
- **Laptop Target**: 1,000,000 candidate profiles, 100,000 jobs, 5,000,000 applications.
- **Full-Scale Target**: 10,000,000 candidate profiles, 1,000,000 jobs, 100,000,000 applications.

---

## 12. API Documentation Summary

Base URL: `/api/v1`

| Method | Endpoint | Allowed Roles | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | All | Liveness probe returning service status |
| `GET` | `/health/db` | All | Readiness probe verifying PostgreSQL connection |
| `POST` | `/auth/register/candidate` | Guest | Self-registration and actor ID allocation |
| `GET` | `/candidates/me` | Candidate | Retrieve authenticated candidate profile |
| `PUT` | `/candidates/me` | Candidate | Update candidate profile & preferences |
| `GET` | `/candidates/me/completeness` | Candidate | Compute profile completeness checklist |
| `POST` | `/candidates/me/photo` | Candidate | Upload candidate profile photo |
| `POST` | `/candidates/me/education` | Candidate | Add education record (Class 10, 12, Diploma, UG, PG) |
| `POST` | `/candidates/me/education/{id}/semesters`| Candidate | Add/update semester grade card |
| `POST` | `/candidates/me/resumes` | Candidate | Upload new resume version |
| `PUT` | `/candidates/me/resumes/{id}/default` | Candidate | Set resume as default |
| `GET` | `/candidates/me/documents` | Candidate | List private documents |
| `POST` | `/candidates/me/documents` | Candidate | Upload document to private vault |
| `GET` | `/jobs` | All | Search and filter published job requisitions |
| `POST` | `/jobs` | Employer, Recruiter | Create structured job requisition |
| `GET` | `/jobs/{id}` | All | View job details and cutoffs |
| `GET` | `/jobs/{id}/eligibility` | Candidate, Employer| Evaluate candidate eligibility against job rules |
| `POST` | `/jobs/{id}/apply` | Candidate | Apply to job with specific resume version |
| `GET` | `/applications/me` | Candidate | List current candidate's applications |
| `GET` | `/jobs/{id}/applications` | Employer, Recruiter| View applicants for specific job |
| `PATCH`| `/applications/{id}/status` | Employer, Recruiter| Transition application pipeline stage |

---

## 13. Frontend Route Map

The Next.js App Router exposes **39 routes** covering public and authenticated flows:

- **Public & Discovery**: `/`, `/jobs`, `/jobs/[jobId]`, `/sign-in`, `/register`, `/support`
- **Candidate Workspace**: `/candidates/me` (Profile, Academics, Semesters, Resumes, Documents), `/portal/candidate`
- **Employer Workspace**: `/jobs/new`, `/portal/employer`, `/organisations`
- **Recruiter Workspace**: `/portal/recruiter`, `/sourcing`, `/applications`
- **Academic Administration**: `/portal/placement-officer`, `/master-data`
- **Enterprise & Billing**: `/licences`, `/billing`, `/portal/account-admin`
- **Platform Governance**: `/portal/admin`, `/portal/super-admin`, `/administration`, `/analytics`, `/verification`

---

## 14. Testing & Quality Verification

Talentra enforces comprehensive testing on every change:

### Run Backend Tests (266 Tests)
```powershell
python -m pytest tests/ -q
# Output: 266 passed in 16.55s
```

### Run Frontend Tests (166 Tests)
```bash
cd frontend
npm test
# Output: 16 test files passed, 166 passed in 3.44s
```

### Run Static Analysis & Type Checking
```bash
cd frontend
npm run typecheck    # TypeScript strict check (0 errors)
npx eslint . --quiet # ESLint analysis (0 errors)
npm run build        # Production Next.js Turbopack build (All 39 routes compiled)
```

---

## 15. Security & Privacy Controls

1. **Object-Level Tenant Isolation**: All candidate documents and private resume versions are validated by `_authorize_candidate_document_access`.
2. **Candidate Blocking**: Candidates can block employer organizations from finding their profiles or seeing their applications.
3. **Magic Byte Signature Inspection**: Uploaded files must match magic byte signatures (`%PDF-`, `\xff\xd8\xff`, `\x89PNG`, `PK\x03\x04`). Executables spoofed as `.pdf` are rejected.
4. **Append-Only Immutability**: Native database triggers protect wallet ledger transactions and audit logs from modification or deletion.
5. **No Secret Leaks**: Client bundles never receive service-role keys or database credentials.

---

## 16. Production Deployment Guide

Talentra is ready for deployment to containerized environments (Kubernetes, AWS ECS, Google Cloud Run) or managed platforms (Vercel, Render):

### Deployment Checklist
1. **Database**: Run `python -m alembic upgrade head` on the target database before directing traffic.
2. **Storage**: Configure a private Supabase bucket named `talentra-documents`.
3. **Backend**: Run `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`.
4. **Frontend**: Build with `npm run build` and run with `npm start` (or deploy directly to Vercel).
5. **CORS**: Set `CORS_ORIGINS` in backend environment to match production frontend domains.
6. **Health Monitoring**: Bind load balancer health probes to `/health` (Liveness) and `/api/v1/health/db` (Readiness).

---

## 17. Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `ModuleNotFoundError: No module named 'app'` | Running python from root without path set | Set `$env:PYTHONPATH="backend"` before executing python commands. |
| `Database disconnected (placeholder detected)` | `.env` has placeholder credentials | Update `DATABASE_URL` in root `.env` with actual Supabase connection string. |
| Next.js Typecheck / Build failure | Stale caches or type mismatch | Run `npm run typecheck` to locate exact line, delete `.next/` if cache is corrupt. |
| `File content does not match signature` | Uploaded file has fake extension | Ensure uploaded file is a genuine PDF/PNG/JPEG and not an executable or text file renamed to `.pdf`. |
| `409 Conflict: Duplicate application` | Applying multiple times to same job | Talentra prevents duplicate applications; verify status under `/candidates/me/applications`. |

---

## 18. Contributing & Conventions

- **Code Formatting**: PEP 8 for Python (Black / Flake8), Prettier for TypeScript.
- **Git Hygiene**: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`).
- **Invariants**: Never drop tables or rewrite existing Alembic migrations. Always add forward migration revisions.

---

## 19. License & Project Status

- **Project Status**: Production-Ready (Stage 19 completed).
- **License**: Proprietary / Talentra Platform License. All rights reserved.

---

## 20. Authoritative Documentation Index

Detailed specifications and architectural guides are available in [`docs/`](docs/README.md):

- 📋 [**Product Requirements**](docs/requirements/TALENTRA_REQUIREMENTS.md)
- 🏛️ [**System Architecture**](docs/architecture/SYSTEM_ARCHITECTURE.md)
- 🗄️ [**Database Schema Specification**](docs/architecture/DATABASE_SCHEMA.md)
- 🔌 [**API Catalog & Integration Runbook**](docs/architecture/API_AND_INTEGRATION.md)
- 👥 [**The Nine Personas & Permissions**](docs/product/PERSONAS_AND_PERMISSIONS.md)
- 🎨 [**UI & Design System**](docs/product/UI_AND_DESIGN_SYSTEM.md)
- 🛠️ [**Local Setup Runbook**](docs/development/LOCAL_SETUP.md)
- 🧪 [**Testing Strategy & Acceptance Baseline**](docs/development/TESTING.md)
- 🌱 [**Seeding & Synthetic Data Strategy**](docs/TALENTRA_SEEDING_STRATEGY.md)
- 📊 [**Seeding Coverage Matrix**](docs/TALENTRA_SEED_COVERAGE_MATRIX.md)
- 🎓 [**Candidate Profile & Academic Records Feature Specification**](docs/TALENTRA_CANDIDATE_PROFILE_ACADEMIC_DOCUMENTS.md)
- 🚀 [**Production Deployment Checklist**](docs/operations/DEPLOYMENT.md)
- 🔒 [**Security, Privacy & Retention**](docs/operations/SECURITY_AND_PRIVACY.md)
- 🔄 [**Backup, Recovery & Rollbacks**](docs/operations/BACKUP_AND_RECOVERY.md)
