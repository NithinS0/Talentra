# TALENTRA — Candidate Profile, Academic Records, Document Management & Company Job Descriptions

## 1. Executive Summary & Objective

This document provides the complete end-to-end engineering specification and verification evidence for the **Candidate Profile, Academic Records, Document Management, and Company Job Descriptions & Eligibility Engine** module in Talentra.

The module integrates seamlessly with the existing Supabase PostgreSQL database, private Supabase Storage vault, FastAPI backend, role-based authentication and authorization system, and Next.js frontend.

---

## 2. Architecture & Identity Design

### 2.1 Canonical Actor Identity
- Every candidate maintains an immutable canonical identity allocated by the database trigger/function `allocate_actor_id('CANDIDATE')`.
- Format: `CA00001` through `CA99999`.
- Candidate profile records are strictly anchored to the primary user record via `user_id` and `actor_id`.
- Actor IDs are immutable: users cannot edit, spoof, or overwrite their system-allocated identity.

### 2.2 Education Pathways
Talentra supports diverse, flexible education pathways without forcing irrelevant prerequisites:
1. **Secondary Education (Class 10)**: Board, institution, completion year, percentage / CGPA, marksheet document.
2. **Higher Secondary Education (Class 12)**: Board, institution, stream (Science, Commerce, Arts), marksheet.
3. **Diploma Education (Polytechnic)**: Technical board, institution, specialization, semester marksheets, diploma certificate. *Does not require Class 12.*
4. **Undergraduate Education (College / University)**: Degree (B.Tech, B.E., B.Sc, BCA, etc.), university, branch, CGPA / percentage, active and historical backlog tracking, semester-by-semester grade sheets.
5. **Postgraduate Education**: Degree (M.Tech, MCA, MBA, M.Sc, etc.), specialization, university, CGPA.

### 2.3 Resumes and Application Snapshots
- Multi-version resume management: Candidates can maintain multiple resumes (e.g., "Full-Stack Engineer Resume", "Cloud Systems Resume") with discrete version numbers.
- Default resume tagging: One resume can be set as the default for quick applications.
- **Application Snapshot Binding**: When a candidate applies to a job, the exact resume version (`resume_version_id`, filename, title) is frozen and stored on the `job_application` record. Subsequent resume updates or replacements by the candidate do not alter historical application records.

### 2.4 Document Vault & Security Isolation
- Private Storage Vault: All resumes, marksheets, transcripts, and supporting documents are stored in private storage buckets.
- File Signature Validation: Backend checks magic bytes (`%PDF-`, `\xff\xd8\xff`, `\x89PNG`, `PK\x03\x04`, `\xd0\xcf\x11\xe0`) to prevent file extension spoofing and reject malicious binaries.
- Object-Level Authorization: Document retrieval (`/candidates/me/documents/{id}/download`, `/candidates/me/resumes/{id}/download`, `/candidates/me/education/{id}/document`) enforces strict ownership. Candidates cannot access other candidates' private documents, and employers can only view documents belonging to candidates who have submitted active applications to their organisation's jobs.

---

## 3. Database Schema & Models

### 3.1 Candidate Models (`backend/app/models/candidate.py`)

| Table Name | Entity Class | Key Columns & Constraints | Purpose |
|------------|--------------|---------------------------|---------|
| `candidate_profile` | `CandidateProfile` | `id`, `user_id` (FK User, unique), `actor_id` (unique), `first_name`, `last_name`, `headline`, `summary`, `completion_score` (Numeric 5,2), `availability_status`, `profile_visibility_code_id` | Core candidate demographic & profile info |
| `candidate_contact` | `CandidateContact` | `id`, `candidate_profile_id` (FK, unique), `email_address`, `phone_e164`, `phone_country_id` (FK Country) | Verified contact details |
| `candidate_education` | `CandidateEducation` | `id`, `candidate_profile_id` (FK), `education_level` (Enum/String), `institution_name`, `board_or_university`, `field_of_study`, `stream_specialization`, `percentage`, `cgpa`, `has_backlogs`, `active_backlogs_count`, `document_storage_key` | Academic history records across secondary, diploma, UG, PG |
| `candidate_education_semester` | `CandidateEducationSemester` | `id`, `candidate_education_id` (FK), `semester_number` (1..12), `academic_term`, `result_status`, `sgpa`, `cgpa`, `credits_registered`, `credits_earned`, `has_backlog`, `grade_sheet_storage_key` | Semester-wise marksheets and grade cards |
| `candidate_resume` | `CandidateResume` | `id`, `candidate_profile_id` (FK), `resume_title`, `target_role`, `is_default`, `deleted_at` | Resume container entity |
| `resume_version` | `ResumeVersion` | `id`, `candidate_resume_id` (FK), `version_number`, `storage_object_key`, `file_name`, `file_size_bytes`, `mime_type`, `is_archived` | Immutable resume version binaries |
| `candidate_document` | `CandidateDocument` | `id`, `candidate_profile_id` (FK), `document_category`, `title`, `file_name`, `storage_path`, `content_sha256`, `is_verified`, `is_archived` | Private document vault metadata |
| `candidate_skill` | `CandidateSkill` | `id`, `candidate_profile_id` (FK), `skill_name`, `proficiency_level`, `years_experience`, `is_primary` | Candidate technical & core skills |
| `candidate_project` | `CandidateProject` | `id`, `candidate_profile_id` (FK), `project_name`, `role_description`, `technologies`, `project_url` | Candidate projects and portfolios |
| `candidate_certification` | `CandidateCertification` | `id`, `candidate_profile_id` (FK), `name`, `issuing_organisation`, `issue_date`, `credential_id`, `document_storage_key` | Professional certifications |
| `candidate_work_experience` | `CandidateWorkExperience` | `id`, `candidate_profile_id` (FK), `company_name`, `job_title`, `employment_type`, `start_date`, `end_date`, `is_current` | Internships and professional experience |

### 3.2 Job & Application Models (`backend/app/models/job.py`, `application.py`)

| Table Name | Entity Class | Structured Eligibility Fields | Purpose |
|------------|--------------|------------------------------|---------|
| `job_requirement` | `JobRequirement` | `required_qualifications`, `accepted_branches`, `min_percentage`, `min_cgpa`, `allow_backlogs`, `max_active_backlogs`, `min_experience_years`, `max_experience_years`, `required_skills`, `preferred_skills`, `required_documents` | Structured campus and corporate job requisitions |
| `job_application` | `JobApplication` | `job_requirement_id` (FK), `candidate_profile_id` (FK), `resume_version_id` (FK ResumeVersion), `resume_snapshot_title`, `resume_snapshot_file_name`, `status_code_id`, `eligibility_status`, `eligibility_notes` | Application pipeline entries preserving resume snapshots |

---

## 4. Supabase Storage Architecture & File Security

### 4.1 Storage Organisation
```
talentra-documents/ (Private Bucket)
└── candidates/
    └── {actor_id}/
        ├── photo/{unique_id}_{filename}
        ├── resumes/{unique_id}_{filename}
        ├── education/{unique_id}_{filename}
        ├── gradesheet/{unique_id}_{filename}
        └── vault/{unique_id}_{filename}
```

### 4.2 Security Controls
1. **Private Access**: Buckets are non-public. Direct unauthenticated HTTP requests receive `403 Forbidden`.
2. **Magic Byte Signature Inspection**: Every uploaded file is analyzed for binary signatures:
   - `PDF`: `%PDF-`
   - `JPEG`: `\xff\xd8\xff`
   - `PNG`: `\x89PNG\r\n\x1a\n`
   - `WebP`: `RIFF....WEBP`
   - `DOCX`: `PK\x03\x04`
   - `DOC`: `\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1`
3. **Integrity Hashing**: SHA-256 digests are calculated and stored in `candidate_document.content_sha256` for audit and tamper detection.
4. **Sanitized File Paths**: Strips directory traversal sequences (`../`, `..\`) and replaces non-alphanumeric characters.
5. **Dual-Mode Persistence**: Uploads stream to Supabase Storage with local resilient fallback (`storage_vault/`) for offline environments.

---

## 5. Structured Eligibility Engine

The eligibility engine evaluates candidate profiles against job requirements in `backend/app/services/job_service.py:evaluate_candidate_eligibility`:

### Evaluation Rules:
1. **Required Qualifications**: Checks whether candidate possesses required qualifications (e.g., `B.Tech`, `B.E.`, `MCA`, `Diploma`). Distinguishes exact match, aliases, and degree levels.
2. **Accepted Branches**: Matches branch/stream (e.g., `Computer Science`, `Information Technology`, `Electronics`).
3. **Academic Cutoffs**:
   - Minimum Percentage: Evaluates highest percentage against `job.min_percentage`.
   - Minimum CGPA: Evaluates highest CGPA against `job.min_cgpa`.
4. **Backlog Policy**: If `allow_backlogs == False`, active backlogs must equal 0. If `allow_backlogs == True`, total active backlogs cannot exceed `max_active_backlogs`.
5. **Core Skills**: Evaluates whether candidate has recorded required skills in their profile.
6. **Required Documents**: Verifies presence of required document categories (e.g. `Resume`, `Class 10 Marksheet`, etc.).

### Decision States:
- `ELIGIBLE`: All mandatory criteria satisfied (`can_apply = True`).
- `NOT_ELIGIBLE`: One or more criteria unsatisfied (e.g. active backlogs exceeded, CGPA below cutoff, `can_apply = False`).
- `UNABLE_TO_DETERMINE`: Crucial information missing from candidate profile (e.g. no education records or marks added, `can_apply = False`).

---

## 6. Backend API Reference

| HTTP Method | Route | Authorization | Description |
|-------------|-------|---------------|-------------|
| `GET` | `/api/v1/candidates/me` | Candidate | Retrieve current candidate profile with education, resumes, skills |
| `PUT` | `/api/v1/candidates/me` | Candidate | Update personal details, headline, links, preferences |
| `GET` | `/api/v1/candidates/me/completeness` | Candidate | Compute profile completeness score and missing items checklist |
| `POST` | `/api/v1/candidates/me/photo` | Candidate | Upload candidate profile photo (JPEG/PNG/WebP) |
| `DELETE` | `/api/v1/candidates/me/photo` | Candidate | Delete candidate profile photo |
| `POST` | `/api/v1/candidates/me/education` | Candidate | Add education qualification (Class 10, Class 12, Diploma, UG, PG) |
| `PUT` | `/api/v1/candidates/me/education/{id}` | Candidate | Update education qualification |
| `DELETE` | `/api/v1/candidates/me/education/{id}` | Candidate | Delete education qualification |
| `POST` | `/api/v1/candidates/me/education/{id}/document` | Candidate | Upload marksheet / degree certificate |
| `GET` | `/api/v1/candidates/me/education/{id}/document` | Candidate / Employer | Authorized marksheet download stream |
| `POST` | `/api/v1/candidates/me/education/{id}/semesters` | Candidate | Add or update semester record (term, SGPA, CGPA, backlogs) |
| `DELETE` | `/api/v1/candidates/me/education/{id}/semesters/{sid}` | Candidate | Delete semester record |
| `POST` | `/api/v1/candidates/me/education/{id}/semesters/{snum}/gradesheet` | Candidate | Upload semester grade sheet file |
| `GET` | `/api/v1/candidates/me/education/{id}/semesters/{snum}/gradesheet` | Candidate / Employer | Authorized semester grade sheet download stream |
| `POST` | `/api/v1/candidates/me/resumes` | Candidate | Upload resume version (PDF, DOC, DOCX) |
| `PUT` | `/api/v1/candidates/me/resumes/{id}/default` | Candidate | Set resume as default |
| `DELETE` | `/api/v1/candidates/me/resumes/{id}` | Candidate | Delete resume |
| `GET` | `/api/v1/candidates/me/resumes/{version_id}/download` | Candidate / Employer | Authorized resume version download stream |
| `GET` | `/api/v1/candidates/me/documents` | Candidate | List private document vault items |
| `POST` | `/api/v1/candidates/me/documents` | Candidate | Upload document to vault with category |
| `DELETE` | `/api/v1/candidates/me/documents/{id}` | Candidate | Delete document from vault |
| `GET` | `/api/v1/candidates/me/documents/{id}/download` | Candidate / Employer | Authorized vault document download stream |
| `POST` | `/api/v1/candidates/me/skills` | Candidate | Add candidate skill |
| `DELETE` | `/api/v1/candidates/me/skills/{id}` | Candidate | Delete candidate skill |
| `GET` | `/api/v1/jobs/{id}/eligibility` | Candidate / Employer | Evaluate candidate eligibility against job cutoffs |
| `POST` | `/api/v1/jobs/{id}/apply` | Candidate | Apply to job with specific `resume_version_id` |

---

## 7. Frontend Route & Component Mapping

| Route | Primary Component | Key Capabilities |
|-------|-------------------|------------------|
| `/candidates/me` | `CandidateProfilePage` | Tabbed workspace: Personal info, Academic qualifications (Class 10, Class 12, Diploma, UG, PG), Semester-wise grade sheets, Multi-version resume manager, Document vault, Skills, and dynamic profile completeness meter with deep-linking |
| `/jobs/[jobId]` | `JobDetailPage` | Full job description, Structured Placement Criteria card, Real-time Candidate Eligibility Assessment card with status breakdown (`ELIGIBLE`, `NOT_ELIGIBLE`, `UNABLE_TO_DETERMINE`), Missing requirements guidance, Application modal with Authoritative Resume Version selector, and Employer review pipeline |
| `/jobs/new` | `NewJobPage` | Employer/Recruiter requisition posting form with structured criteria: qualifications, branches, cutoffs, backlogs, skills, documents |
| `/portal/candidate` | `CandidatePortalPage` | Candidate overview dashboard: completeness score, verification status, pending campus tasks, application trackers |

---

## 8. Role-Based Authorization & Privacy Matrix

| Resource | Candidate Owner | Other Candidate | Recruiter (Mapped Org) | Recruiter (Unmapped Org) | Super Admin |
|----------|-----------------|-----------------|------------------------|--------------------------|-------------|
| Candidate Profile View | Read / Write | Restricted / Denied | Read (with application) | Denied | Read |
| Academic Marksheets | Read / Write | **Denied (403/404)** | Read (with application) | **Denied (403/404)** | Read |
| Semester Grade Sheets | Read / Write | **Denied (403/404)** | Read (with application) | **Denied (403/404)** | Read |
| Resumes & Versions | Read / Write | **Denied (403/404)** | Read submitted snapshot | **Denied (403/404)** | Read |
| Document Vault Files | Read / Write | **Denied (403/404)** | Read (with application) | **Denied (403/404)** | Read |
| Create Job Requirement | Denied | Denied | Create for mapped org | Denied | Create |
| Evaluate Job Eligibility | Evaluate own profile | Denied | Evaluate candidate | Denied | Evaluate |
| Apply to Job | Apply with resume ver | Denied | Denied | Denied | Denied |

---

## 9. Comprehensive Feature-to-Component Mapping Table

| Feature | Database Model | Backend Endpoint | Frontend Route / Component | Authorization Rule | Automated Tests | Implementation Status |
|---------|----------------|------------------|----------------------------|--------------------|-----------------|-----------------------|
| Candidate Profile CRUD | `CandidateProfile`, `CandidateContact` | `GET/PUT /candidates/me` | `/candidates/me` | Self-owner only | `test_candidate_profile_retrieval_and_update` | **Implemented and Verified** |
| Profile Completeness Checklist | `CandidateProfile` | `GET /candidates/me/completeness` | `/candidates/me` | Self-owner only | `test_profile_completeness_checklist` | **Implemented and Verified** |
| Profile Photo Upload/Delete | `CandidateProfile` | `POST/DELETE /candidates/me/photo` | `/candidates/me` | Self-owner only | `test_profile_photo_upload_and_delete` | **Implemented and Verified** |
| Education Records (Class 10, 12, UG) | `CandidateEducation` | `POST/PUT/DELETE /candidates/me/education` | `/candidates/me` (Academics) | Self-owner only | `test_education_crud_and_prevent_duplicate_class_10` | **Implemented and Verified** |
| Diploma Pathway without Class 12 | `CandidateEducation` | `POST /candidates/me/education` | `/candidates/me` (Academics) | Self-owner only | `test_diploma_pathway_without_class_12` | **Implemented and Verified** |
| Semester-wise Grade Sheets | `CandidateEducationSemester` | `POST/DELETE /candidates/me/education/{id}/semesters` | `/candidates/me` (Semesters) | Self-owner only | `test_semester_gradesheet_crud_and_upload` | **Implemented and Verified** |
| Resume Upload & Versioning | `CandidateResume`, `ResumeVersion` | `POST/DELETE /candidates/me/resumes` | `/candidates/me` (Resumes) | Self-owner only | `test_resume_upload_versioning_and_application_snapshot` | **Implemented and Verified** |
| Application Resume Snapshot | `JobApplication` | `POST /jobs/{id}/apply` | `/jobs/[jobId]` (Apply Modal) | Preserves submitted version | `test_resume_upload_versioning_and_application_snapshot` | **Implemented and Verified** |
| Document Vault & Isolation | `CandidateDocument` | `GET/POST/DELETE /candidates/me/documents` | `/candidates/me` (Documents) | Cross-candidate isolation enforced | `test_document_vault_and_cross_candidate_privacy` | **Implemented and Verified** |
| Magic Byte Signature Validation | `StorageService` | File upload endpoints | Form upload handlers | Rejects spoofed binaries | `test_file_upload_security_signature_validation` | **Implemented and Verified** |
| Structured Job Creation | `JobRequirement` | `POST /jobs` | `/jobs/new` | Employer / Recruiter mapped | `test_fr0037_create_job_requirement_employer_success` | **Implemented and Verified** |
| Candidate Eligibility Engine | `JobRequirement` | `GET /jobs/{id}/eligibility` | `/jobs/[jobId]` (Eligibility Card) | Multi-tenant aware | `test_structured_eligibility_evaluation` | **Implemented and Verified** |
| Candidate Job Application | `JobApplication` | `POST /jobs/{id}/apply` | `/jobs/[jobId]` (Apply Modal) | Candidate only, duplicate checked | `test_candidate_apply_success_and_history` | **Implemented and Verified** |

---

## 10. Test Execution Report & Evidence

### 10.1 Backend Pytest Execution
- Command: `python -m pytest tests/test_candidate_academics_documents.py tests/test_jobs_and_applications.py tests/test_candidate_registration.py -v`
- Execution Result: **37 passed, 0 failed in 5.64s**
```
tests/test_candidate_academics_documents.py::test_candidate_profile_retrieval_and_update PASSED
tests/test_candidate_academics_documents.py::test_profile_completeness_checklist PASSED
tests/test_candidate_academics_documents.py::test_profile_photo_upload_and_delete PASSED
tests/test_candidate_academics_documents.py::test_education_crud_and_prevent_duplicate_class_10 PASSED
tests/test_candidate_academics_documents.py::test_semester_gradesheet_crud_and_upload PASSED
tests/test_candidate_academics_documents.py::test_resume_upload_versioning_and_application_snapshot PASSED
tests/test_candidate_academics_documents.py::test_structured_eligibility_evaluation PASSED
tests/test_candidate_academics_documents.py::test_file_upload_security_signature_validation PASSED
tests/test_candidate_academics_documents.py::test_diploma_pathway_without_class_12 PASSED
tests/test_candidate_academics_documents.py::test_document_vault_and_cross_candidate_privacy PASSED
tests/test_jobs_and_applications.py::test_fr0037_create_job_requirement_employer_success PASSED
tests/test_jobs_and_applications.py::test_fr0038_recruiter_company_boundary_enforced PASSED
tests/test_jobs_and_applications.py::test_fr0040_salary_range_validation PASSED
tests/test_jobs_and_applications.py::test_fr0041_job_closing_date_validation PASSED
tests/test_jobs_and_applications.py::test_fr0042_job_position_count_positive PASSED
tests/test_jobs_and_applications.py::test_fr0043_publish_state_transition PASSED
tests/test_jobs_and_applications.py::test_fr0051_job_search_and_filters PASSED
tests/test_jobs_and_applications.py::test_candidate_apply_success_and_history PASSED
tests/test_jobs_and_applications.py::test_fr0044_duplicate_application_prevention PASSED
tests/test_jobs_and_applications.py::test_apply_to_draft_or_closed_job_rejected PASSED
tests/test_jobs_and_applications.py::test_fr0052_candidate_blocking_enforced PASSED
tests/test_jobs_and_applications.py::test_fr0053_cross_candidate_application_privacy PASSED
tests/test_jobs_and_applications.py::test_fr0045_application_status_transition_by_recruiter PASSED
tests/test_candidate_registration.py (14 tests) ALL PASSED
======================= 37 passed in 5.64s =======================
```

### 10.2 Frontend Vitest Test Execution
- Command: `npm test` in `frontend`
- Execution Result: **16 passed test files, 166 passed tests in 3.11s**
```
Test Files  16 passed (16)
Tests       166 passed (166)
Duration    3.11s
```

### 10.3 Next.js Production Build Validation
- Command: `npm run build` in `frontend`
- Execution Result: **Code 0 — All 39 Next.js static and dynamic app routes successfully compiled and optimized without errors.**
