# Talentra — Authoritative Product Requirements

## 1. Executive Summary

Talentra is a next-generation enterprise campus placement, recruitment, and talent operating platform. It unifies candidate lifecycle management, employer campus hiring, external recruitment consulting, gig work marketplace, and university placement cell operations into a single multi-tenant system with strict role-based access control, immutable financial and audit ledgers, and automated compliance verification.

The platform is designed to replace fragmented hiring processes with an integrated, high-velocity workflow inspired by industry benchmarks (such as Superset) while providing enterprise-grade multi-tenancy, data sovereignty, and dual-control compliance.

---

## 2. Core Functional Modules (M01 – M13)

### M01: Core Reference & Master Data
- **Taxonomies & Domains**: Standardized lookups for countries (ISO 3166-1 alpha-2/alpha-3), currencies (ISO 4217), languages (ISO 639-1), industry sectors, skill taxonomies, academic degrees, and institutions.
- **Data Integrity**: Reference tables are centrally managed and enforce referential integrity across all downstream profile and job matching operations.

### M02: Candidate Profiles, Academic Records & Cryptographic Document Vault
- **Actor Prefix**: `CA`
- **Complete Profile Management**: Multi-section candidate profile covering personal details, headline, bio summary, avatar photo upload/removal, contact and location information, placement preferences, visibility controls, and dynamic completeness calculator with missing items checklist.
- **Comprehensive Academic Pathways**: Multi-pathway qualifications supporting Class 10 (Secondary), Class 12 (Higher Secondary), Diploma (Polytechnic), Undergraduate, and Postgraduate degrees. System strictly prevents duplicate Class 10 entries and tracks percentage, CGPA, passing year, and marksheet uploads.
- **Semester Performance & Grade Sheets**: For tertiary education, tracks semester-wise progression (Semesters 1 through 10) with SGPA, cumulative CGPA, credits registered/earned, backlog subject details, and PDF grade sheet attachments.
- **Multi-Version Resume Management**: Candidates can upload and maintain multiple tailored resumes (`resume_version`), designate a primary default resume, and download versions.
- **Application Resume Immutability**: When submitting an application for a job, an immutable snapshot (`resume_snapshot_title`, `resume_snapshot_file_name`) is locked to the application record. Subsequent updates to candidate resumes never alter previously submitted applications.
- **Cryptographic Document Vault**: Multi-category storage (transcripts, degree certificates, category certificates, ID proofs) verified with magic-byte file signature validation (blocking spoofed executables) and SHA-256 integrity hashing.
- **Candidate Privacy & Blocking**: Candidates can define employer blocking lists, preventing selected organisations from viewing their profiles or search listings.

### M03: Structured Job Requirements & Automated Eligibility Engine
- **Structured Requisition Management**: Roles specify job overview, key responsibilities, required qualifications, accepted branches, minimum CGPA/percentage cutoffs, backlog allowance policies (`allow_backlogs`, `max_active_backlogs`), experience ranges, required technical and soft skills, and mandatory verification documents.
- **Candidate Eligibility Engine**: Live rule evaluation returns `ELIGIBLE`, `NOT_ELIGIBLE`, or `UNABLE_TO_DETERMINE`. Candidates receive a granular breakdown of each criterion (required value vs. candidate value, pass/fail status, and explanation) and actionable warnings for missing profile information.
- **Recruiter Pipeline Review**: Employer and Recruiter review tables display evaluated candidate eligibility status badges alongside submitted immutable resume snapshots.

### M04: Administration & Identity Governance
- **Actor Prefixes**: `SA` (Super Admin), `AD` (Platform Admin), `AA` (Account Admin).
- **Identity & Authentication**: Session-based and JWT authentication, multi-factor authentication (MFA), password policies, and security questions.
- **Role Governance**: Granular permissions assigned to nine system personas. Separation of duties ensuring platform administrators cannot modify client financial records without dual-control authorization.

### M05: Organisations & Account Management
- **Actor Prefix**: `EM` (Employer Admin/Recruiter).
- **Multi-Tenancy**: Strict multi-tenant isolation where each organisation (enterprise employer, consulting agency, university) owns its isolated workspace, team members, billing accounts, and job postings.
- **Sub-accounts & Departments**: Hierarchical accounts supporting parent enterprises, subsidiary entities, and business units with allocated recruitment seats.

### M06: Gig Marketplace & On-Demand Work
- **Actor Prefix**: `GU` (Gig Worker / Guest User) / `CA`.
- **Milestone-Based Engagements**: Short-term contracting, project-based gig assignments, milestone tracking, deliverable approvals, and escrow-based disbursements.
- **Time Tracking & Availability**: Weekly availability slots enforced by GiST exclusion constraints (`excl_gig_worker_availability_window`) to prevent overlapping commitments.

### M07: Licences, Seats & Device Sessions
- **Licence Allocation**: Tiered subscription models enforcing maximum concurrent active seats per organisation.
- **Device & Session Management**: Tracking of active logins by IP address, user-agent, device fingerprint, and session expiry. Admin forced termination capability for compromised sessions.
- **Licence Exclusivity**: Temporal licence period enforcement via GiST exclusion constraints (`excl_subscription_licence_period`).

### M08: Sourcing & External Consultants
- **Actor Prefix**: `CO` (External Consultant / Agency Recruiter).
- **Consultant Sourcing Mandates**: Employers can issue external candidate search mandates to verified third-party recruitment consultants with designated commission structures.
- **Duplicate Prevention**: Automated candidate ownership windows (e.g., 90-day candidate representation lock) preventing commission disputes between competing recruiters.

### M09: Subscriptions, Wallet & Payments
- **Financial Architecture**: Double-entry ledger principles for wallet credits, prepaid hiring packages, gig escrow accounts, and candidate assessment fees.
- **Immutability Requirement**: All records in `wallet_ledgers` and `payment_transactions` are enforced as append-only via database-level triggers (`trg_immutable_wallet_ledger`, `trg_immutable_payment_transaction`). `UPDATE` and `DELETE` operations are strictly rejected at the database engine level.
- **Multi-Currency Support**: Payments processed via Stripe, Razorpay, or bank wire with currency conversion tracking.

### M10: Notifications & Community Forums
- **Multi-Channel Delivery**: In-app notifications, transactional email (SendGrid/SMTP), SMS (Twilio), and push notifications (FCM/WebPush).
- **User Preference Matrix**: Granular delivery preferences per notification category (interview invites, application status changes, marketing, billing alerts).
- **Campus & Topic Forums**: Moderated community discussion boards, peer-to-peer Q&A for drive preparations, and placement announcements.

### M11: Analytics, Reporting & Data Marts
- **Aggregates & Metrics**: Near-real-time recruitment funnel analytics (time-to-hire, drop-off rates, drive conversion efficiency, diversity ratios).
- **University Placement Marts**: Batch placement statistics, median CTC packages, top recruiting sectors, and unplaced student tracking.
- **Export Formats**: Standard CSV, Excel, and automated scheduled PDF summaries.

### M12: Government ID Verification & Compliance
- **Dual-Control KYC**: Integration with SurePass, DigiLocker, and Aadhaar/PAN/Passport verification gateways for identity attestation.
- **Document Quarantine & Scanning**: ClamAV integration for malware scanning prior to document ingestion.
- **Data Minimization & Redaction**: Strict storage of masked document numbers and signed storage hashes; raw biometric data is never stored.

### M13: Audit, Compliance & Extensions
- **Immutable Audit Trail**: Append-only audit events table (`trg_immutable_audit_event`) capturing actor ID, client IP, action name, resource target, and before/after JSON state diffs.
- **Data Retention Policies**: Automated purging schedules (e.g., KYC documents retained 7 years / 2555 days, inactive session tokens purged after 30 days).

---

## 3. The Nine System Personas

| # | Persona | Code | Actor ID Prefix | Scope & Responsibility |
|---|---|---|---|---|
| 1 | **Super Admin** | `SA` | `SA-` | Global system control, infrastructure management, tenant provisioning, system kill-switch. |
| 2 | **Platform Admin** | `AD` | `AD-` | Cross-tenant compliance, platform-wide user management, master data governance, dispute mediation. |
| 3 | **Account Admin** | `AA` | `AA-` | Organisation-level workspace control, team seat management, company billing, licence administration. |
| 4 | **Guest User** | `GU` | `GU-` | Unverified prospective users, public landing page exploration, job preview, self-registration onboarding. |
| 5 | **Candidate** | `CA` | `CA-` | Student/job seeker, profile and resume management, job applications, interview scheduling, offer acceptance. |
| 6 | **Employer** | `EM` | `EM-` | Hiring manager/business unit lead, headcount approval, job requirement definition, final interviews. |
| 7 | **Recruiter** | `RE` | `RE-` | In-house corporate recruiter, candidate sourcing, application pipeline screening, interview scheduling. |
| 8 | **Consultant** | `CO` | `CO-` | Third-party agency recruiter, external sourcing mandates, candidate profile submission, placement fee tracking. |
| 9 | **Placement Officer**| `PO` | `PO-` | University placement coordinator, drive scheduling, student eligibility verification, institutional reporting. |

---

## 4. Non-Functional & Regulatory Constraints

1. **Strict Immutability**: Financial transactions, wallet balance adjustments, candidate profile download histories, submitted application resume snapshots, and security audit logs cannot be updated or deleted by any user or administrator.
2. **Actor Prefix Isolation**: All generated actor identifiers must strictly follow their assigned 2-letter prefix (`SA-`, `AD-`, `AA-`, `GU-`, `CA-`, `EM-`, `RE-`, `CO-`, `PO-`).
3. **Multi-Tenant Data Sovereignty**: All organisation-scoped queries must filter by `organisation_id` to prevent cross-tenant data leaks.
4. **Zero Dark Patterns in UI**: UI must provide clear dismissals, explicit confirmation on destructive actions, standard keyboard navigation, and normal blinking text carets exclusively in text inputs.
