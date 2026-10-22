# Talentra — API Specifications & Integration Contracts

## 1. API Architecture & Standards

Talentra exposes a comprehensive RESTful API built with FastAPI following OpenAPI 3.1 specifications.

- **Base URL Prefix**: `/api/v1`
- **Data Exchange**: JSON (`application/json`) with standard UTF-8 encoding and multipart/form-data for document streaming.
- **Authentication**: Bearer JWT tokens in the `Authorization` header (`Bearer <access_token>`) accompanied by optional secure, HTTP-only session cookies.
- **Error Standard**: RFC 7807 Problem Details for HTTP APIs:
  ```json
  {
    "type": "https://api.talentra.com/v1/errors/RESOURCE_NOT_FOUND",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "Candidate with ID 'CA-4109' does not exist or has been blocked.",
    "instance": "/api/v1/candidates/CA-4109",
    "code": "CANDIDATE_NOT_FOUND",
    "timestamp": "2026-10-21T10:00:00Z"
  }
  ```

---

## 2. Core Endpoint Directory

### 2.1. System Health & Probes
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/health` | Liveness probe returning service status and version | None |
| `GET` | `/api/v1/health/db` | Readiness probe validating live PostgreSQL connectivity | None |

### 2.2. Authentication & Session Management
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Self-service registration for candidates and guest users | None |
| `POST` | `/api/v1/auth/login` | Credential validation, MFA check, issue JWT & session | None |
| `POST` | `/api/v1/auth/refresh` | Refresh access token using valid refresh token | Refresh Token |
| `POST` | `/api/v1/auth/logout` | Invalidate current session and revoke tokens | Bearer Token |
| `GET` | `/api/v1/auth/me` | Fetch active user profile, roles, and accessible portals | Bearer Token |

### 2.3. Candidates & Profile Lifecycle (`/api/v1/candidates`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/candidates/me` | Retrieve authenticated candidate full profile with all relations | `CA` |
| `PUT` | `/api/v1/candidates/me` | Update candidate personal details, preferences, and visibility | `CA` |
| `GET` | `/api/v1/candidates/me/completeness` | Dynamic completeness score and missing requirements checklist | `CA` |
| `POST` | `/api/v1/candidates/me/photo` | Upload profile photo (JPEG, PNG, WebP) | `CA` |
| `DELETE` | `/api/v1/candidates/me/photo` | Delete profile photo | `CA` |
| `POST` | `/api/v1/candidates/me/education` | Add academic record (Class 10, 12, Diploma, UG, PG) | `CA` |
| `PUT` | `/api/v1/candidates/me/education/{id}` | Update academic record | `CA` |
| `DELETE` | `/api/v1/candidates/me/education/{id}` | Delete academic record | `CA` |
| `POST` | `/api/v1/candidates/me/education/{id}/document` | Upload qualification marksheet/certificate document | `CA` |
| `GET` | `/api/v1/candidates/me/education/{id}/document` | Securely download qualification marksheet | `CA`, `EM`, `PO` |
| `GET` | `/api/v1/candidates/me/education/{id}/semesters` | List semester-wise grade sheet performance records | `CA`, `EM`, `PO` |
| `POST` | `/api/v1/candidates/me/education/{id}/semesters` | Record semester SGPA, CGPA, credits, and backlog details | `CA` |
| `DELETE` | `/api/v1/candidates/me/education/{id}/semesters/{sem_id}` | Remove semester record | `CA` |
| `POST` | `/api/v1/candidates/me/education/{id}/semesters/{sem_num}/gradesheet` | Upload semester grade sheet PDF/document | `CA` |
| `GET` | `/api/v1/candidates/me/semesters/{sem_id}/document` | Download semester grade sheet file | `CA`, `EM`, `PO` |
| `GET` | `/api/v1/candidates/me/resumes` | List candidate resumes with version history | `CA` |
| `POST` | `/api/v1/candidates/me/resumes` | Upload resume version (PDF, DOCX) with magic byte check | `CA` |
| `PUT` | `/api/v1/candidates/me/resumes/{id}/default` | Set resume as primary default | `CA` |
| `DELETE` | `/api/v1/candidates/me/resumes/{id}` | Delete resume (retaining historical application snapshots) | `CA` |
| `GET` | `/api/v1/candidates/me/resumes/{id}/versions/{v_id}/download` | Download resume version file | `CA`, `EM`, `RE` |
| `GET` | `/api/v1/candidates/me/documents` | List documents stored in candidate cryptographic vault | `CA` |
| `POST` | `/api/v1/candidates/me/documents` | Upload document to vault with SHA-256 integrity verification | `CA` |
| `DELETE` | `/api/v1/candidates/me/documents/{id}` | Delete document from vault | `CA` |
| `GET` | `/api/v1/candidates/me/documents/{id}/download` | Securely download vault document | `CA`, `EM`, `PO` |
| `POST` | `/api/v1/candidates/me/skills` | Add technical/soft skill with proficiency rating | `CA` |
| `DELETE` | `/api/v1/candidates/me/skills/{id}` | Remove skill | `CA` |
| `POST` | `/api/v1/candidates/me/projects` | Add project with repository and demo URL | `CA` |
| `DELETE` | `/api/v1/candidates/me/projects/{id}` | Delete project | `CA` |
| `POST` | `/api/v1/candidates/me/certifications` | Add verified certification or credential | `CA` |
| `DELETE` | `/api/v1/candidates/me/certifications/{id}` | Delete certification | `CA` |
| `POST` | `/api/v1/candidates/me/work-experience` | Add industry internship or employment experience | `CA` |
| `DELETE` | `/api/v1/candidates/me/work-experience/{id}` | Delete work experience | `CA` |
| `GET` | `/api/v1/candidates/me/applications` | List job applications submitted by current candidate | `CA` |
| `POST` | `/api/v1/candidates/blocking` | Add employer organisation to candidate blocking list | `CA` |
| `GET` | `/api/v1/candidates/search` | Search verified candidates (filtered by blocking) | `EM`, `RE`, `CO`, `PO` |

### 2.4. Jobs & Structured Eligibility Pipeline (`/api/v1/jobs`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/jobs` | Search and list active job postings | Any / Authenticated |
| `POST` | `/api/v1/jobs` | Create a job posting with structured criteria & cutoffs | `EM`, `RE` |
| `GET` | `/api/v1/jobs/{job_id}` | Retrieve job details, responsibilities & eligibility rules | Any / Authenticated |
| `PUT` | `/api/v1/jobs/{job_id}` | Update job criteria and attributes | `EM`, `RE` |
| `PATCH`| `/api/v1/jobs/{job_id}/status` | Update job lifecycle status (OPEN, CLOSED, DRAFT) | `EM`, `RE` |
| `GET` | `/api/v1/jobs/{job_id}/eligibility` | Evaluate candidate eligibility against job cutoffs | `CA`, `EM`, `RE` |
| `POST` | `/api/v1/jobs/{job_id}/apply` | Submit job application preserving frozen resume snapshot | `CA` |
| `GET` | `/api/v1/jobs/{job_id}/applications` | List candidate applications with eligibility status badges | `EM`, `RE`, `PO` |
| `PATCH`| `/api/v1/applications/{app_id}/status` | Advance application pipeline status | `EM`, `RE` |

### 2.5. Sourcing & External Consultants (`/api/v1/sourcing`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/sourcing/mandates` | Employer publishes search mandate to agencies | `EM`, `RE` |
| `GET` | `/api/v1/sourcing/mandates` | List mandates assigned to consultant agency | `CO` |
| `POST` | `/api/v1/sourcing/submissions` | Agency submits candidate with representation lock | `CO` |

### 2.6. Gig Marketplace (`/api/v1/gigs`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/gigs/projects` | Search freelance and short-term project listings | `CA`, `GU` |
| `POST` | `/api/v1/gigs/milestones/{id}/submit` | Gig worker submits milestone deliverable | `CA`, `GU` |
| `POST` | `/api/v1/gigs/milestones/{id}/approve` | Client approves milestone and releases escrow | `EM`, `AA` |

### 2.7. Wallet, Billing & Payments (`/api/v1/billing`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/billing/wallet` | View organisation or user wallet balance | `AA`, `EM`, `CO`, `CA` |
| `POST` | `/api/v1/billing/topup` | Initiate credit top-up via payment gateway | `AA`, `EM` |
| `POST` | `/api/v1/billing/webhook/stripe` | Ingest Stripe webhook events | Stripe Signature |
| `POST` | `/api/v1/billing/webhook/razorpay` | Ingest Razorpay payment callbacks | Razorpay Signature |

### 2.8. Government Identity & KYC (`/api/v1/verification`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/verification/initiate` | Initiate Aadhaar/PAN/Passport verification | `CA` |
| `POST` | `/api/v1/verification/webhook` | Webhook callback from SurePass / DigiLocker | Provider Signature |
| `GET` | `/api/v1/verification/status` | Check verification status and verified badges | `CA`, `EM`, `PO` |

---

## 3. External Integration Contracts

### 3.1. Supabase Storage & Local Vault Engine
- **MIME & Magic Bytes Enforcement**: File uploads are scanned using magic byte signatures (PDF: `%PDF-`, PNG: `\x89PNG\r\n\x1a\n`, JPEG: `\xff\xd8\xff`, WebP: `RIFF....WEBP`, ZIP/DOCX: `PK\x03\x04`). Executables, scripts, and spoofed files are rejected with `400 Bad Request`.
- **Integrity Validation**: All stored files are hashed using SHA-256 (`content_sha256`) to ensure tamper detection and audit trail reliability.
- **Dual-Mode Persistence**: The storage service seamlessly writes to Supabase Storage buckets (`candidate-documents`, `candidate-resumes`, `candidate-photos`) with automated zero-config fallback to the secure local vault (`storage_vault/`).
- **Path Sanitization**: Object storage keys are sanitized to strictly prevent path traversal vulnerabilities.

### 3.2. Payment Gateways (Stripe & Razorpay)
- **Idempotency**: All payment transactions include an `Idempotency-Key` header generated by the client to prevent double charging.
- **Webhook Security**: All webhook requests must pass signature validation (`STRIPE_WEBHOOK_SECRET` / Razorpay HMAC-SHA256). Non-matching signatures are rejected with `400 Bad Request`.
- **Immutability Enforcement**: Incoming payment success events write directly to `payment_transactions` and create corresponding credit entries in `wallet_ledgers`.

### 3.3. Multi-Channel Notifications (SendGrid, Twilio, FCM)
- **SendGrid / SMTP**: Transactional emails for account verification, password resets, and interview schedules.
- **Twilio**: SMS alerts for urgent placement drive updates and MFA OTPs.
- **Firebase Cloud Messaging (FCM)**: Mobile and web push notifications for real-time application updates.
- **Resilience**: Failed dispatches are retried up to 3 times with exponential backoff before logging an error event.
