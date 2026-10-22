# Talentra — Enterprise Freelance & Escrow Marketplace (Frontend)

Next.js 16 (App Router) + TypeScript (Strict) + Tailwind CSS frontend application for the Talentra enterprise marketplace, integrated with the FastAPI backend and Supabase PostgreSQL database.

---

## 1. Quick Start

### Prerequisites
- Node.js v20+ LTS (Tested on v24.18.0)
- npm v10+ (Tested on v11.5.2)
- Talentra FastAPI backend running at `http://localhost:8000/api/v1`

### Installation
```bash
cd frontend
npm install --legacy-peer-deps
```

### Environment Configuration
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Configuration settings:
```env
NEXT_PUBLIC_API_BASE_URL="http://localhost:8000/api/v1"
NEXT_PUBLIC_APP_ENV="development"
NEXT_PUBLIC_APP_NAME="Talentra"
```

### Running Locally
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

---

## 2. Scripts & Verification

| Command | Purpose |
| :--- | :--- |
| `npm run dev` | Launch local development server on port 3000 |
| `npm run build` | Execute production Next.js build with Turbopack (39 routes compiled) |
| `npm run typecheck` | Run TypeScript compiler strict type checking (`tsc --noEmit` — 0 errors) |
| `npx eslint . --quiet` | Run ESLint checks against Next.js and React 19 rules (0 errors, 0 warnings) |
| `npm test` | Run Vitest unit & integration test suites (144/144 tests passing across 14 suites) |

---

## 3. Stage 17E: Frontend Acceptance Testing & Hardening Summary

During Stage 17E, the entire frontend was verified against the approved specification, the FastAPI `/api/v1` backend, and the database design docket:
- **Requirements Coverage:** 100% of documented pages (36 feature pages, 8 role portals, and system routes) verified and mapped.
- **Automated Test Suite:** 14 test suites comprising 144 tests covering authentication, route guards, core workflows, financial ledgers, government verification, and security invariants.
- **Zero Leaked Secrets:** Verified that no Supabase service keys, database passwords, or private tokens exist in client bundles or public environment variables.
- **Data Integrity & Immutability:** Append-only financial ledgers (FR-0138, FR-0206) and audit logs (FR-0059) are strictly protected against modification or deletion in the UI.
- **Dual-Control Governance:** High-risk identity verification overrides require mandatory second approver verification (FR-0176, FR-0178).

---

## 3. Application Routes & Modules

### Core Business Workflows (Stage 17C)
- `/candidates` & `/candidates/me`: Candidate profile viewing and editing.
- `/jobs`, `/jobs/[jobId]`, `/jobs/new`: Job discovery, search, and requirement publishing.
- `/applications`, `/applications/[applicationId]`: Application tracking and status progression.
- `/organisations`, `/organisations/[organisationId]`: Employer organisation registry and recruiter mapping.
- `/sourcing`: Talent search, candidate bookmarking, and consultant sourcing requests.
- `/gigs`, `/gigs/[gigId]`: Milestone-based gig assignments and deliverables.

### Remaining Modules & Administrative Interfaces (Stage 17D)
- `/licences`, `/licences/[licenceId]`: Licence capacity overview, seat allocations, SHA-256 device registration, and session cleanup.
- `/billing`: Authoritative wallet balance, append-only credit/debit forms, compensating ledger corrections, subscription plans, and payment orders.
- `/notifications`: In-app alert centre, bulk mark as read, expired body purge, and channel preferences.
- `/community`: Community discussion feed, UTF-8 post publishing (<=10,000 chars), and reaction toggling.
- `/support`: Customer support tickets, requester ownership checks (FR-0146), published FAQs, and referral attribution.
- `/analytics`: Platform metrics, recruitment funnel stage progression (FR-0151), watermark & lag monitoring, PII-minimized candidate table, and CSV export.
- `/verification`: Verification consent (FR-0163), zero raw PII initiation (FR-0164, FR-0209), short-lived presigned URLs, dual control reviews (FR-0178), and integration boundary registers.
- `/administration`: User governance, role granting preventing privilege escalation (FR-0068), account suspension, soft-deletion (`deleted_at`), append-only audit trail (FR-0059), and data classification catalog.
- `/master-data`: Live service liveness and database readiness probes, and standard reference domain lookup dictionary.

### Authenticated Role Portals (`/portal/*`)
The application features 8 dedicated role portal shells enforcing strict role authorization:

| Role Code | Public Prefix | Actor ID | Portal Route | Primary Workflows |
| :--- | :---: | :---: | :--- | :--- |
| `SUPER_ADMIN` | `SA` | `SA00001` | `/portal/super-admin` | Global governance, feature flags, audit logs |
| `ADMIN` | `AD` | `AD00001` | `/portal/admin` | Platform operations, KYC queue, dispute appeals |
| `ACCOUNT_ADMIN` | `AA` | `AA00001` | `/portal/account-admin` | Employer tenant management, seats, billing |
| `EMPLOYER` | `EM` | `EM00001` | `/portal/employer` | Job posting, recruiter management, invoices |
| `RECRUITER` | `RC` | `RC00001` | `/portal/recruiter` | Candidate sourcing, pipeline progression, interviews |
| `CONSULTANT` | `CO` | `CO00001` | `/portal/consultant` | Assigned requirements, candidate submissions |
| `PLACEMENT_OFFICER` | `PO` | `PO00001` | `/portal/placement-officer` | Campus cohort management, institutional drives |
| `CANDIDATE` | `CA` | `CA00001` | `/portal/candidate` | Profile completion, job discovery, gigs |

---

## 4. API Client Modules (`src/lib/api/`)

- `client.ts`: Base typed HTTP client handling base URLs, Bearer token injection, and structured error responses.
- `auth.ts`: Authentication, sign-in, token refresh, and registration.
- `candidates.ts`: Candidate profile operations.
- `jobs.ts`: Job requirement discovery and creation.
- `applications.ts`: Job applications and status transitions.
- `organisations.ts`: Organisation registry and recruiter assignments.
- `sourcing.ts`: Candidate search, bookmarking, and consultant requests.
- `gig.ts`: Gig projects, milestones, deliverables, and submissions.
- `licences.ts`: Licence lifecycle, seats, registered devices, and sessions.
- `subscriptions.ts`: Subscription plans, wallet balance, credits/debits, corrections, and orders.
- `notifications.ts`: In-app alerts, channel preferences, community posts, reactions, support tickets, and FAQs.
- `analytics.ts`: Reporting marts, recruitment funnel, watermark lags, and KPI catalogues.
- `verification.ts`: Consent capture, identity verification, presigned URLs, reviews, and integration registers.
- `admin.ts`: User governance, role granting/revoking, status updates, soft deletion, audit logs, and access reviews.
