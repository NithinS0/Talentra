# Talentra Documentation Archive

This directory contains historical stage reports, audit logs, milestone specifications, and development scratch records created during earlier phases of the Talentra platform lifecycle.

All useful requirements, architecture specifications, role matrices, setup commands, test suites, and operational runbooks from these historical files have been consolidated into the authoritative canonical documentation structure located in `docs/`.

---

## 1. Canonical Mapping Guide

If you are looking for specific information previously found in a historical stage report, refer to the consolidated canonical document below:

| Historical Report Series / Topic | Consolidated Authoritative Document |
|:---|:---|
| Functional requirements, rules, PRD (`STAGE_8` to `STAGE_14` specs) | [`docs/requirements/TALENTRA_REQUIREMENTS.md`](../requirements/TALENTRA_REQUIREMENTS.md) |
| System architecture, boundaries, multi-tenancy, service layout | [`docs/architecture/SYSTEM_ARCHITECTURE.md`](../architecture/SYSTEM_ARCHITECTURE.md) |
| 216 tables, 233 FKs, 489 indexes, 4 triggers, schema reconciliations | [`docs/architecture/DATABASE_SCHEMA.md`](../architecture/DATABASE_SCHEMA.md) |
| FastAPI `/api/v1` catalog, webhooks, third-party integrations | [`docs/architecture/API_AND_INTEGRATION.md`](../architecture/API_AND_INTEGRATION.md) |
| Nine personas, responsibilities, dashboard matrices, RBAC routes | [`docs/product/PERSONAS_AND_PERMISSIONS.md`](../product/PERSONAS_AND_PERMISSIONS.md) |
| Superset UI design principles, tokens, light/dark themes, caret rules | [`docs/product/UI_AND_DESIGN_SYSTEM.md`](../product/UI_AND_DESIGN_SYSTEM.md) |
| Local setup, virtualenv, FastAPI start, Next.js dev server, env vars | [`docs/development/LOCAL_SETUP.md`](../development/LOCAL_SETUP.md) |
| Vitest test suites (154 tests), Pytest suites, 218 acceptance cases | [`docs/development/TESTING.md`](../development/TESTING.md) |
| Master reference data (countries, currencies, roles), seed scripts | [`docs/development/SEEDING_AND_TEST_DATA.md`](../development/SEEDING_AND_TEST_DATA.md) |
| Production deployment, containerization, CI/CD, readiness checklists | [`docs/operations/DEPLOYMENT.md`](../operations/DEPLOYMENT.md) |
| Immutable triggers, candidate privacy & blocking, KYC, data retention | [`docs/operations/SECURITY_AND_PRIVACY.md`](../operations/SECURITY_AND_PRIVACY.md) |
| Point-In-Time Recovery (PITR), Alembic rollbacks, disaster drills | [`docs/operations/BACKUP_AND_RECOVERY.md`](../operations/BACKUP_AND_RECOVERY.md) |

---

## 2. Inventory of Historical Files (Merged & Pruned)

The following 92 historical reports, specifications, and audits have had their requirements, architectural decisions, and testing evidence fully merged into the canonical documents above, and have been pruned from active development to maintain a clean repository structure:
### 2.1. Backend Stages 8–15 (Core API & Modules)
- `STAGE_8_API_SPECIFICATION.md`: Sourcing & External Consultant API specifications.
- `STAGE_8_SOURCING_CONSULTANT_REQUESTS.md`: Consultant mandate workflow and representation locks.
- `STAGE_8_TEST_REPORT.md`: Stage 8 integration test evidence.
- `STAGE_9_API_SPECIFICATION.md`: Gig Marketplace API specifications.
- `STAGE_9_GIG_MARKETPLACE.md`: Freelance and milestone contract execution design.
- `STAGE_9_TEST_REPORT.md`: Stage 9 test execution evidence.
- `STAGE_10_API_SPECIFICATION.md`: Licences, seats, and session tokens API.
- `STAGE_10_LICENCES_SEATS_DEVICES_SESSIONS.md`: Concurrent seat allocation and GiST temporal exclusion.
- `STAGE_10_TEST_REPORT.md`: Stage 10 test execution evidence.
- `STAGE_11_API_SPECIFICATION.md`: Subscriptions, wallets, and payments API.
- `STAGE_11_FINANCIAL_INTEGRITY.md`: Double-entry ledger architecture and append-only trigger rules.
- `STAGE_11_SUBSCRIPTIONS_WALLET_PAYMENTS.md`: Payment intent lifecycle and gateway webhooks.
- `STAGE_11_TEST_REPORT.md`: Stage 11 financial test evidence.
- `STAGE_12_API_SPECIFICATION.md`: Notifications and community discussion forum API.
- `STAGE_12_NOTIFICATIONS_PREFERENCES_COMMUNITY.md`: Multi-channel notification delivery rules.
- `STAGE_12_TEST_REPORT.md`: Stage 12 notification test evidence.
- `STAGE_13_ANALYTICS_REPORTING.md`: Analytics data marts and reporting aggregation logic.
- `STAGE_13_API_SPECIFICATION.md`: Analytics reporting API contracts.
- `STAGE_13_METRIC_DEFINITIONS.md`: Recruitment funnel and campus placement metric formulas.
- `STAGE_13_TEST_REPORT.md`: Stage 13 analytics test evidence.
- `STAGE_14_API_SPECIFICATION.md`: Government ID, document quarantine, and retention API.
- `STAGE_14_AUDIT_AND_RETENTION.md`: Immutable audit events and statutory retention schedules.
- `STAGE_14_GOVERNMENT_VERIFICATION.md`: Dual-control KYC workflows (SurePass/DigiLocker).
- `STAGE_14_INTEGRATIONS_CATALOG.md`: External integration directory.
- `STAGE_14_TEST_REPORT.md`: Stage 14 verification and retention test evidence.
- `STAGE_15_SEEDING_TEST_REPORT.md`: Reference master data and scale seeding test execution.

### 2.2. Frontend Foundation & Stages 17A–17E
- `STAGE_17A_FRONTEND_FOUNDATION.md`: Initial Next.js project setup and routing foundation.
- `STAGE_17A_TEST_REPORT.md`: Frontend initialization test report.
- `STAGE_17B_AUTH_CONTRACT.md`: Authentication flow and token management.
- `STAGE_17B_ROUTE_ACCESS_MATRIX.md`: Initial route guard and access matrix.
- `STAGE_17B_TEST_REPORT.md`: Authentication and navigation test evidence.
- `STAGE_17C_API_MAPPING.md`: API client mapping for candidate and jobs portals.
- `STAGE_17C_IMPLEMENTATION_REPORT.md`: Implementation status for candidate workflows.
- `STAGE_17C_TEST_REPORT.md`: Candidate and job application test evidence.
- `STAGE_17D_API_MAPPING.md`: API client mapping for employer and recruiter portals.
- `STAGE_17D_IMPLEMENTATION_REPORT.md`: Implementation status for employer workflows.
- `STAGE_17D_ROUTE_ACCESS_MATRIX.md`: Employer and consultant route access matrix.
- `STAGE_17D_TEST_REPORT.md`: Verification and administrative portal test evidence.
- `STAGE_17E_DEFECT_BACKLOG.md`: Frontend defect backlog and bug resolution tracker.
- `STAGE_17E_FRONTEND_COVERAGE_AUDIT.md`: Frontend route and screen coverage audit.
- `STAGE_17E_SECURITY_CHECKLIST.md`: Frontend XSS, CSRF, and input hygiene checklist.
- `STAGE_17E_TEST_REPORT.md`: Stage 17E comprehensive frontend test report.

### 2.3. System Integration, Resilience & Deployment (Stages 18–20)
- `STAGE_18_DEFECT_BACKLOG.md`: End-to-end integration defect tracker.
- `STAGE_18_E2E_COVERAGE_MATRIX.md`: End-to-end integration coverage across all 13 modules.
- `STAGE_18_SECURITY_AND_DATA_INTEGRITY_RESULTS.md`: Security test findings and data integrity verification.
- `STAGE_18_SYSTEM_INTEGRATION_REPORT.md`: System integration milestone report.
- `STAGE_19_DATA_INTEGRITY_REPORT.md`: PostgreSQL constraint and trigger enforcement report.
- `STAGE_19_DEFECT_BACKLOG.md`: Pre-production defect remediation list.
- `STAGE_19_PERFORMANCE_BENCHMARK.md`: API latency and database query benchmarks.
- `STAGE_19_REMEDIATION_SUMMARY.md`: Summary of remediated issues.
- `STAGE_19_RESILIENCE_REPORT.md`: Fault tolerance, chaos, and failover test results.
- `STAGE_19_SECURITY_ASSESSMENT.md`: Penetration testing and OWASP Top 10 assessment.
- `STAGE_20_BLOCKERS_AND_REMEDIATION.md`: Release blockers and resolution paths.
- `STAGE_20_CICD_AND_RELEASE_PLAN.md`: Continuous integration and release pipeline.
- `STAGE_20_DATABASE_MIGRATION_AND_RECOVERY_PLAN.md`: Database rollback and disaster recovery plan.
- `STAGE_20_DEPLOYMENT_ARCHITECTURE.md`: Cloud deployment topology specification.
- `STAGE_20_DEPLOYMENT_CHECKLIST.md`: Pre-flight deployment checklist.
- `STAGE_20_ENVIRONMENT_AND_SECRETS_AUDIT.md`: Environment secrets audit.
- `STAGE_20_MONITORING_AND_INCIDENT_RUNBOOK.md`: Monitoring alarms and incident runbooks.
- `STAGE_20_PRODUCTION_READINESS_REPORT.md`: Production readiness certification.

### 2.4. Module & Audit Reports
- `SUPABASE_SETUP_AND_SCHEMA_AUDIT.md`: Initial Supabase schema audit and migration analysis.
- `TALENTRA_ACCEPTANCE_TEST_PLAN.md`: Acceptance test matrix for 218 test cases.
- `TALENTRA_ACTOR_IDS_AND_COUNTRIES.md`: Actor ID prefix allocation and country master records.
- `TALENTRA_ADMINISTRATION_AND_ROLE_GOVERNANCE.md`: Role governance rules and permissions.
- `TALENTRA_API_FRONTEND_COVERAGE.md`: Early API vs frontend coverage gap audit.
- `TALENTRA_AUTH_AND_REGISTRATION.md`: Authentication and user registration flows.
- `TALENTRA_BLOCKERS_AND_PRIORITIES.md`: Historical blockers and sprint priorities.
- `TALENTRA_DATABASE_RECONCILIATION.md`: Database reconciliation report.
- `TALENTRA_DESIGN_SYSTEM.md`: Pre-redesign UI tokens and design system notes.
- `TALENTRA_FINAL_IMPLEMENTATION_STATUS.md`: Pre-cleanup implementation milestone status.
- `TALENTRA_IMPLEMENTATION_AUDIT.md`: Pre-redesign repository audit report.
- `TALENTRA_JOBS_AND_APPLICATIONS.md`: Jobs and applications module requirements.
- `TALENTRA_MIGRATION_PLAN.md`: Migration orchestration plan.
- `TALENTRA_ORGANISATION_AND_ACCOUNT_MANAGEMENT.md`: Multi-tenant organization specifications.
- `TALENTRA_PERSONA_DASHBOARD_MATRIX.md`: Early persona dashboard requirements.
- `TALENTRA_REFERENCE_DATA_SOURCES.md`: Master reference data source citations.
- `TALENTRA_ROLE_DASHBOARD_SPECIFICATION.md`: Role-specific dashboard specifications.
- `TALENTRA_ROLE_ROUTE_PERMISSION_MATRIX.md`: Role-to-route permission matrix.
- `TALENTRA_SCALE_DATA_GENERATOR.md`: Scale data generation scripts documentation.
- `TALENTRA_SCHEMA_RECONCILIATION.md`: Schema reconciliation logs.
- `TALENTRA_SEEDING_GUIDE.md`: Seeding execution runbook.
- `TALENTRA_SEEDING_READINESS.md`: Seeding readiness assessment.
- `TALENTRA_TEST_DATA_CATALOG.md`: Catalog of test fixtures and synthetic accounts.
- `TALENTRA_THEME_IMPLEMENTATION_REPORT.md`: Theme implementation report.
- `TALENTRA_UI_AUDIT.md`: UI audit identifying theme and caret issues.
- `TALENTRA_UI_REDESIGN_REPORT.md`: Superset-inspired UI redesign report.
- `TALENTRA_UI_REGRESSION_TEST_REPORT.md`: UI regression test run report.
- `TALENTRA_UI_TEST_REPORT.md`: UI test execution report.
- `ANTIGRAVITY_README.md`: Original Antigravity agent setup guide.
- `Talentra_PostgreSQL_Schema_Audit_Report.md`: Early static schema audit report.
- `Talentra_Frontend_Implementation_Specification.md`: Initial 36-page frontend draft.
- `Talentra_Database_Blueprint_Implementation_Guide.md`: Initial database blueprint implementation guide.
