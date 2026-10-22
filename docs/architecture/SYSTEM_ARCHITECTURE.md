# Talentra — System Architecture Specification

## 1. Architectural Overview

Talentra is architected as a modern, decoupled enterprise platform composed of a high-performance Next.js frontend, a robust FastAPI backend service layer, and a hardened Supabase PostgreSQL database foundation.

```mermaid
graph TD
    subgraph Client Layer
        Web["Next.js 16 Web App<br/>(React 19, TypeScript, Tailwind CSS)"]
        Mobile["Responsive Mobile Browser View"]
    end

    subgraph Edge & API Gateway
        Nginx["Reverse Proxy / Edge Gateway (HTTPS / TLS 1.3)"]
        AuthMiddleware["JWT & Session Auth / RBAC Middleware"]
    end

    subgraph Service Layer - FastAPI (Python 3.11+)
        API["FastAPI REST Endpoints (/api/v1)"]
        HealthService["Health & Diagnostics Service"]
        TenantService["Multi-Tenant Isolation Scoper"]
        PaymentService["Payment & Wallet Engine"]
        NotifService["Notification & Delivery Dispatcher"]
        AuditService["Immutable Audit Service"]
    end

    subgraph Storage & Persistence - Supabase PostgreSQL
        DB[(PostgreSQL 15+<br/>216 Base Tables)]
        BtreeGist["btree_gist Extension"]
        Triggers["4 Immutability Triggers<br/>(Audit, Wallet, Payments, Downloads)"]
        Exclusions["GiST Exclusion Constraints"]
    end

    subgraph External Integrations
        Stripe["Stripe / Razorpay (Payments)"]
        SurePass["SurePass / DigiLocker (Government ID)"]
        SendGrid["SendGrid / Twilio / FCM (Alerts)"]
        ClamAV["ClamAV (Antivirus Ingestion Scan)"]
    end

    Web --> Nginx
    Mobile --> Nginx
    Nginx --> AuthMiddleware
    AuthMiddleware --> API
    API --> HealthService
    API --> TenantService
    API --> PaymentService
    API --> NotifService
    API --> AuditService

    TenantService --> DB
    PaymentService --> DB
    AuditService --> DB
    DB --- BtreeGist
    DB --- Triggers
    DB --- Exclusions

    PaymentService --> Stripe
    API --> SurePass
    NotifService --> SendGrid
    API --> ClamAV
```

---

## 2. Frontend Layer (Next.js App Router)

- **Framework**: Next.js 16 (App Router) with React 19 and TypeScript.
- **Styling & Design System**: Tailwind CSS v3 with CSS custom properties (`hsl(var(--...))`) enabling seamless light mode (default) and dark mode switching.
- **Visual Identity**: Inspired by modern campus and talent recruitment benchmarks (Superset) featuring clean typography (Inter / Geist), high-density data tables, accessible status badges, and contextual action menus.
- **Navigation & Routing**:
  - Public marketing routes: `/`, `/solutions/*`, `/pricing`, `/about`, `/careers`, `/contact`.
  - Authentication routes: `/login`, `/register`, `/auth/forgot-password`.
  - Authenticated portals: `/portal/[persona]/*` mapping directly to the nine system roles.
- **Form Controls & Input Standards**: Standard blinking text caret (`caret-primary`) is strictly preserved in editable input fields; decorative non-editable components never display pseudo-carets.

---

## 3. Backend Service Layer (FastAPI)

- **Framework**: FastAPI on Python 3.11+.
- **Database Connectivity**: Synchronous SQLAlchemy 2.x engine using the `psycopg` (Psycopg 3) binary driver.
- **Configuration Management**: Pydantic Settings v2 reading from local `.env` with safe credential masking in logs.
- **API Organization**:
  - Base prefix: `/api/v1`
  - Health probes: `/api/v1/health` (liveness), `/api/v1/health/db` (readiness).
  - Business modules: Modular API routers organized by domain (`auth`, `admin`, `organisations`, `candidates`, `jobs`, `sourcing`, `gig_marketplace`, `licenses`, `payments`, `notifications`, `analytics`, `verification`).
- **Error Handling**: Standardized RFC 7807 problem details error responses with machine-readable error codes and correlation IDs.

---

## 4. Database & Persistence Layer (PostgreSQL)

- **Hosting & Infrastructure**: Supabase PostgreSQL.
  - **Port 5432 (Direct Connection)**: Mandatory for Alembic migrations, DDL execution, and catalog management.
  - **Port 6543 (Session/Transaction Pooler)**: Optional for high-concurrency read replicas.
- **Schema Volume**: 216 base tables across 13 functional modules.
- **Advanced Constraints**:
  - PostgreSQL `btree_gist` extension enabled for temporal range checks.
  - GiST exclusion constraints (`excl_subscription_licence_period`, `excl_gig_worker_availability_window`) preventing double-booking and concurrent seat overlaps.
  - Native append-only triggers preventing updates or deletions on audit, payment, and wallet tables.

---

## 5. Multi-Tenancy & Data Isolation Model

Talentra employs a logical multi-tenancy model enforced at both the database schema level and the application service layer:

1. **Tenant Anchor**: Every organisation is assigned a unique `UUID` primary key in the `organisations` table.
2. **Tenant Scoping**: All tenant-owned tables (`jobs`, `applications`, `sourcing_requests`, `licence_allocations`, `interviews`) carry an `organisation_id` foreign key.
3. **Application Enforcement**: Repository queries automatically filter by the authenticated user's `organisation_id` extracted from their validated session/token.
4. **Cross-Tenant Prevention**: Platform administrators and consultants access tenant resources only through explicitly granted mandate scopes with full audit event logging.

---

## 6. Actor Identity & Prefix Conventions

Every actor created in Talentra receives a unique identifier formatted with a canonical 2-letter uppercase prefix followed by an alphanumeric identifier:

```text
Prefix Pattern:  <PREFIX>-<UNIQUE_ID>
Examples:
  - Super Admin:       SA-0001
  - Platform Admin:    AD-1042
  - Account Admin:     AA-2910
  - Guest User:        GU-9011
  - Candidate:         CA-4109
  - Employer:          EM-3001
  - Recruiter:         RE-5120
  - Consultant:        CO-6002
  - Placement Officer: PO-7001
```

This prefix is checked by authorization dependencies to validate route eligibility before query execution.
