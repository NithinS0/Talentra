# Talentra Documentation Index

Welcome to the authoritative documentation for **Talentra** — an enterprise campus placement, recruitment, and talent operating platform.

This directory contains the canonical documentation for all aspects of the platform. All historical stage reports and superseded audits have been organized and archived in [`docs/archive/`](archive/README.md).

---

## 1. Documentation Structure & Map

```text
docs/
├── README.md                                  # You are here (Documentation Hub)
├── requirements/
│   └── TALENTRA_REQUIREMENTS.md               # Authoritative PRD, 13 modules, business rules
├── architecture/
│   ├── SYSTEM_ARCHITECTURE.md                 # System boundaries, multi-tenancy, service map
│   ├── DATABASE_SCHEMA.md                     # 216 tables, 233 FKs, 489 indexes, triggers
│   └── API_AND_INTEGRATION.md                 # FastAPI catalog, webhooks, third-party integrations
├── product/
│   ├── PERSONAS_AND_PERMISSIONS.md            # The 9 Personas, RBAC, route permissions
│   └── UI_AND_DESIGN_SYSTEM.md                # Superset-inspired design, theme tokens, carets
├── development/
│   ├── LOCAL_SETUP.md                         # Local environment runbook (FE & BE)
│   ├── TESTING.md                             # Vitest (154 tests), Pytest, 218 acceptance cases
│   └── SEEDING_AND_TEST_DATA.md               # Master reference data & test profile generators
├── operations/
│   ├── DEPLOYMENT.md                          # Production release runbook, Docker, CI/CD
│   ├── SECURITY_AND_PRIVACY.md                # Dual-control KYC, candidate blocking, retention
│   └── BACKUP_AND_RECOVERY.md                 # PITR recovery, Alembic migration rollbacks
├── archive/
│   └── README.md                              # Historical stage reports index (92 reports)
└── REPOSITORY_CLEANUP_REPORT.md               # Audit log of repository cleanup and verification
```

---

## 2. Quick Navigation by Topic

### 📋 Requirements & Governance
- [**Talentra Requirements & Business Rules**](requirements/TALENTRA_REQUIREMENTS.md): Core functional requirements across all 13 modules (M01 to M13), actor prefixes, and compliance constraints.

### 🏛️ System & Database Architecture
- [**System Architecture**](architecture/SYSTEM_ARCHITECTURE.md): Multi-tier layout (Next.js, FastAPI, PostgreSQL), multi-tenant isolation, and background services.
- [**Database Schema & Dictionary**](architecture/DATABASE_SCHEMA.md): Complete blueprint of the 216 tables, 233 foreign keys, 489 indexes, `btree_gist` exclusion constraints, and 4 append-only triggers.
- [**API Catalog & Integrations**](architecture/API_AND_INTEGRATION.md): RESTful `/api/v1` endpoints, payment webhooks (Stripe/Razorpay), KYC gateways (SurePass/DigiLocker), and antivirus scanning (ClamAV).

### 👥 Product & User Experience
- [**The Nine Personas & Permissions**](product/PERSONAS_AND_PERMISSIONS.md): Responsibilities, actor prefixes (`SA-`, `AD-`, `AA-`, `GU-`, `CA-`, `EM-`, `RE-`, `CO-`, `PO-`), and role-route permission matrix.
- [**UI & Design System**](product/UI_AND_DESIGN_SYSTEM.md): Superset-inspired UI principles, light mode default with dark mode support, HSL tokens, and caret fidelity rules.

### 💻 Development, Testing & Data
- [**Local Setup Runbook**](development/LOCAL_SETUP.md): Step-by-step developer guide for running frontend (Port 3000), backend (Port 8000), and Supabase connection.
- [**Testing Strategy & Verification**](development/TESTING.md): Vitest suite (15 suites, 154 passing tests), Pytest suite, and 218 end-to-end acceptance test cases.
- [**Seeding & Test Data Guide**](development/SEEDING_AND_TEST_DATA.md): Master reference data seeding (countries, currencies, languages, roles) and synthetic test profiles.

### 🚀 Operations, Security & Resilience
- [**Production Deployment**](operations/DEPLOYMENT.md): Containerization, environment variables matrix, and production release checklist.
- [**Security, Privacy & Retention**](operations/SECURITY_AND_PRIVACY.md): Immutable audit logs, candidate anti-surveillance blocking, and statutory data retention schedules.
- [**Production Readiness & Repository Audit Report**](PRODUCTION_READINESS_REPORT.md): Stage 19 production readiness verification, audit scope, test evidence, and fixes.
- [**Candidate Profile & Academic Records Feature Specification**](TALENTRA_CANDIDATE_PROFILE_ACADEMIC_DOCUMENTS.md): Complete specification of candidate demographics, education pathways, semester grade cards, resume versions, and structured eligibility engine.
- [**Synthetic Data Seeding Strategy & Coverage Matrix**](TALENTRA_SEEDING_STRATEGY.md): Hackathon docket data generation framework, profiles A–E, and benchmark extrapolation.

### 🗄️ Historical Archive
- [**Documentation Archive**](archive/README.md): Index of 92 historical stage reports, audit logs, and milestone deliverables preserved for historical traceability.

---

## 3. Documentation Maintenance Rule

**Rule of Single Source of Truth**:
- Do not create a new audit or stage document for future modifications.
- Update the relevant canonical document above when a feature, route, schema, or test changes.
- Ensure all relative links remain valid after document updates.
