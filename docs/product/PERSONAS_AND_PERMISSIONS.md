# Talentra — Personas, Portals & Permissions Matrix

## 1. The Nine Personas Overview

Talentra organizes platform functionality around nine distinct personas. Each persona has a dedicated actor ID prefix, a tailored portal experience, strictly defined business responsibilities, and immutable audit logging.

```text
SA (Super Admin)         ──> Global infrastructure, system settings, kill-switch
AD (Platform Admin)      ──> Cross-tenant compliance, user moderation, dispute resolution
AA (Account Admin)       ──> Organisation settings, seats, team billing, licences
GU (Guest User)          ──> Public exploration, self-registration, job browsing
CA (Candidate)           ──> Student/Job seeker, profile, jobs, applications, interviews
EM (Employer)            ──> Department head, job requisitions, final hiring decisions
RE (Recruiter)           ──> Talent sourcing, pipeline screening, interview scheduling
CO (Consultant)          ──> Third-party agency recruiter, mandate submissions
PO (Placement Officer)   ──> University coordinator, campus drives, batch tracking
```

---

## 2. Persona Specifications & Portal Routes

### 2.1. Super Admin (`SA`)
- **Actor Prefix**: `SA-`
- **Portal Base Route**: `/portal/super-admin`
- **Core Responsibilities**: Infrastructure health, database migrations, security secrets, system maintenance modes, and tenant creation.
- **Key Navigation Items**: System Health, Tenant Directory, Global Logs, Security Configuration, Kill-Switch.
- **Restrictions**: Cannot view candidate private personal notes or tamper with immutable financial ledgers.

### 2.2. Platform Admin (`AD`)
- **Actor Prefix**: `AD-`
- **Portal Base Route**: `/portal/admin`
- **Core Responsibilities**: Multi-tenant platform moderation, master data taxonomies, user status governance, verification audits, and dispute resolution.
- **Key Navigation Items**: Verification Queue, User Directory, Master Data Taxonomies, Dispute Resolution, Compliance Audit.
- **Restrictions**: Cannot impersonate enterprise users without explicit dual-control audit approval.

### 2.3. Account Admin (`AA`)
- **Actor Prefix**: `AA-`
- **Portal Base Route**: `/portal/account-admin`
- **Core Responsibilities**: Organisation profile, team seat allocations, billing methods, subscription tiers, and corporate security settings.
- **Key Navigation Items**: Organisation Profile, Team & Seats, Subscriptions & Invoices, Wallet Balance, Access Logs.
- **Restrictions**: Strictly scoped to their own organisation (`organisation_id`). Cannot access other tenants.

### 2.4. Guest User (`GU`)
- **Actor Prefix**: `GU-`
- **Portal Base Route**: Public routes (`/`, `/jobs`, `/solutions/*`, `/register`)
- **Core Responsibilities**: Unauthenticated visitors and prospective candidates exploring platform capabilities.
- **Restrictions**: Cannot apply for jobs or view full salary details without registering and completing basic profile verification.

### 2.5. Candidate (`CA`)
- **Actor Prefix**: `CA-`
- **Portal Base Route**: `/portal/candidate`
- **Core Responsibilities**: Profile management, academic credentials, resume versions, job discovery, application status tracking, interview schedules, and offer letters.
- **Key Navigation Items**: Overview, Profile & Resumes, Job Board, Applications Pipeline, Interviews, Offers, Employer Blocking.
- **Restrictions**: Can only access their own profile and applications. Cannot view other candidates' profiles or employer internal screening notes.

### 2.6. Employer (`EM`)
- **Actor Prefix**: `EM-`
- **Portal Base Route**: `/portal/employer`
- **Core Responsibilities**: Department hiring requisitions, team capacity management, budget approvals, final interview evaluations, and offer sign-offs.
- **Key Navigation Items**: Hiring Requisitions, Active Jobs, Pipeline Overview, Team Capacity, Offer Approvals, Sourcing Requests.
- **Restrictions**: Scoped to company departments. Cannot modify candidate verification status directly.

### 2.7. Recruiter (`RE`)
- **Actor Prefix**: `RE-`
- **Portal Base Route**: `/portal/recruiter`
- **Core Responsibilities**: Active talent sourcing, job posting creation, application screening, assessment evaluation, and interview scheduling.
- **Key Navigation Items**: Job Postings, Candidate Search, Application Pipelines, Assessment Scores, Interview Scheduler.
- **Restrictions**: Scoped to assigned job postings within their employer organisation.

### 2.8. Consultant (`CO`)
- **Actor Prefix**: `CO-`
- **Portal Base Route**: `/portal/consultant`
- **Core Responsibilities**: External recruitment agency sourcing, mandate acceptance, candidate profile submissions, candidate representation tracking, and commission invoices.
- **Key Navigation Items**: Sourcing Mandates, Candidate Submissions, Representation Lock Status, Commission Ledger.
- **Restrictions**: Can only submit candidates who have not been approached or submitted by competing agencies within the 90-day lock window.

### 2.9. Placement Officer (`PO`)
- **Actor Prefix**: `PO-`
- **Portal Base Route**: `/portal/placement-officer`
- **Core Responsibilities**: University campus placement drive management, batch student eligibility verification, company drive coordination, student offer tracking, and institutional reports.
- **Key Navigation Items**: Campus Drives, Student Directory, Drive Eligibility Verification, Slot Coordination, Placement Analytics.
- **Restrictions**: Scoped to students enrolled at their university or affiliated campus colleges.

---

## 3. Role-to-Route Permission Matrix

| Route Path | `SA` | `AD` | `AA` | `GU` | `CA` | `EM` | `RE` | `CO` | `PO` |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/portal/super-admin/*` | **Allow** | Deny | Deny | Deny | Deny | Deny | Deny | Deny | Deny |
| `/portal/admin/*` | **Allow** | **Allow** | Deny | Deny | Deny | Deny | Deny | Deny | Deny |
| `/portal/account-admin/*` | Deny | Deny | **Allow** | Deny | Deny | Deny | Deny | Deny | Deny |
| `/portal/candidate/*` | Deny | Deny | Deny | Deny | **Allow** | Deny | Deny | Deny | Deny |
| `/portal/employer/*` | Deny | Deny | Deny | Deny | Deny | **Allow** | Deny | Deny | Deny |
| `/portal/recruiter/*` | Deny | Deny | Deny | Deny | Deny | Deny | **Allow** | Deny | Deny |
| `/portal/consultant/*` | Deny | Deny | Deny | Deny | Deny | Deny | Deny | **Allow** | Deny |
| `/portal/placement-officer/*` | Deny | Deny | Deny | Deny | Deny | Deny | Deny | Deny | **Allow** |
| `/jobs` (Public Search) | Allow | Allow | Allow | **Allow** | Allow | Allow | Allow | Allow | Allow |
| `/login`, `/register` | Deny | Deny | Deny | **Allow** | Deny | Deny | Deny | Deny | Deny |

---

## 4. Cross-Persona Authorization Rules

1. **Explicit Route Guarding**: Attempting to navigate to an unauthorized portal triggers a clean `403 Forbidden` redirect to the user's authorized home portal.
2. **Multi-Role Accounts**: Users with multiple personas (e.g. Recruiter + Employer) are presented with a role switcher header component to switch contexts safely without mixing permissions.
3. **Audit Trail**: Every role switch, administrative override, and mandate submission writes an immutable record to the `audit_events` table.
