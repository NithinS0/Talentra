# Talentra — Testing Strategy & Verification Guide

## 1. Testing Architecture Overview

Talentra maintains a multi-layered verification strategy spanning unit tests, integration tests, static typing, database schema verification, and end-to-end acceptance criteria.

```text
┌────────────────────────────────────────────────────────┐
│           End-to-End Acceptance (218 Cases)           │
├────────────────────────────────────────────────────────┤
│   Frontend Tests (Vitest)  │   Backend Tests (Pytest)  │
│      15 Suites, 154 Tests  │   Health & Schema Tests   │
├────────────────────────────┴───────────────────────────┤
│    Database Catalog Verification (verify_schema.py)   │
│     216 Tables, 233 FKs, 489 Indexes, 4 Triggers       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Test Suite (Vitest)

The frontend test suite is powered by **Vitest** with `@testing-library/react` and `jsdom`. It validates component rendering, theme switching, persona portal navigation, accessibility, and caret preservation.

### 2.1. Executing Frontend Tests
From the `frontend/` directory:

```bash
# Run all tests once
npm run test

# Run tests in interactive watch mode
npm run test:watch

# Run tests with test coverage reporting
npm run test:coverage
```

### 2.2. Verified Frontend Test Coverage Matrix
All 15 test suites and 154 tests currently pass with 0 failures:

| Test Suite File | Tested Functional Area | Test Count | Status |
|:---|:---|:---:|:---:|
| `superset-design-polish.test.tsx` | Superset design polish, typography, density | 12 tests | **PASS** |
| `portal-dashboards.test.tsx` | Dashboards for all 9 personas | 18 tests | **PASS** |
| `theme-system.test.tsx` | Light mode default & dark mode toggle | 14 tests | **PASS** |
| `caret-fidelity.test.tsx` | Preservation of blinking text carets in inputs | 10 tests | **PASS** |
| `landing-page.test.tsx` | Public landing page hero, features, and CTAs | 12 tests | **PASS** |
| `solutions-pages.test.tsx` | University, Employer, and Candidate solution pages | 15 tests | **PASS** |
| `candidate-portal.test.tsx` | Candidate profile, applications, and resumes | 12 tests | **PASS** |
| `employer-portal.test.tsx` | Employer requisitions, pipeline, team seats | 11 tests | **PASS** |
| `recruiter-portal.test.tsx` | Sourcing, applicant screening, interview scheduler | 10 tests | **PASS** |
| `consultant-portal.test.tsx` | Consultant mandates, representation lock | 8 tests | **PASS** |
| `placement-officer.test.tsx` | Campus placement drives, slot allocation, batch stats | 9 tests | **PASS** |
| `admin-portal.test.tsx` | Admin user moderation, KYC queues, dispute desk | 8 tests | **PASS** |
| `account-admin.test.tsx` | Organisation seat billing, licences, audit trail | 7 tests | **PASS** |
| `super-admin.test.tsx` | Global system health, tenant registry, kill-switch | 4 tests | **PASS** |
| `accessibility.test.tsx` | WCAG contrast, ARIA landmarks, focus rings | 4 tests | **PASS** |
| **Total Verified** | **Entire Frontend Surface** | **154 tests** | **100% PASS** |

### 2.3. Frontend TypeScript Validation
```bash
npm run typecheck
```
Exits with code 0 (0 errors).

---

## 3. Backend Test Suite (Pytest)

Backend tests validate API routing, authentication dependencies, database health probes, and business constraints.

### 3.1. Executing Backend Tests
From the repository root with the virtual environment activated:

```powershell
# Run backend pytest suite
.\.venv\Scripts\pytest -v tests/test_health.py
```

### 3.2. Database Schema Automated Verification
The repository provides automated catalog verification scripts in `backend/app/`:

```powershell
# Verify Supabase PostgreSQL connectivity
.\.venv\Scripts\python.exe backend/app/verify_db.py

# Verify schema against 216-table blueprint
.\.venv\Scripts\python.exe backend/app/verify_schema.py
```

---

## 4. Acceptance Test Plan & Baseline

The platform's acceptance baseline is governed by `Talentra_Final_Test_Cases_All_Modules.xlsx` containing **218 test cases** across all 13 modules.

### Verification Rule of Evidence:
- No test case is marked as "Passed" without executed proof (terminal stdout or test runner logs).
- In automated test runs, test outputs must be preserved in corresponding test logs.
- Unresolved defects or flaky tests must be recorded in the issue tracker, never silently bypassed.
