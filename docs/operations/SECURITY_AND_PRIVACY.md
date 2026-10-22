# Talentra — Security, Privacy & Compliance Architecture

## 1. Security Architecture & Threat Model

Talentra operates in high-trust enterprise and higher-education environments handling sensitive candidate PII, academic transcripts, corporate hiring plans, and financial transactions.

```text
┌────────────────────────────────────────────────────────┐
│               Security & Privacy Controls              │
├────────────────────────────────────────────────────────┤
│  1. Immutable Financial & Audit Engine (Triggers)      │
│  2. Dual-Control Government KYC Attestation            │
│  3. Candidate Anti-Surveillance & Employer Blocking    │
│  4. Antivirus Quarantine Pipeline (ClamAV)             │
│  5. Automated Data Retention & Redaction Engine        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Immutable Append-Only Ledgers

To satisfy SOC 2, ISO 27001, and financial regulatory audits, four database triggers prevent modifying or deleting historical evidence:

### 2.1. Audit Events (`audit_events`)
- **Trigger**: `trg_immutable_audit_event`
- **Rule**: Rejects all `UPDATE` and `DELETE` operations at the PostgreSQL engine level.
- **Payload**: Records Actor ID (`SA-`, `AD-`, `CA-`, etc.), IP address, user agent, target entity, action, and JSON diffs of state changes.

### 2.2. Financial Ledgers (`wallet_ledgers` & `payment_transactions`)
- **Triggers**: `trg_immutable_wallet_ledger`, `trg_immutable_payment_transaction`
- **Rule**: Balances are calculated through ledger finality. Erroneous credits or refunds cannot overwrite existing rows; they require a corresponding debit or offset transaction row.

### 2.3. Profile Download History (`profile_download_history`)
- **Trigger**: `trg_immutable_profile_download_history`
- **Rule**: Whenever an employer, recruiter, or placement officer exports or downloads a candidate's resume or full profile, an indelible record is created.

---

## 3. Candidate Privacy & Anti-Surveillance

Talentra enforces candidate-first privacy safeguards:

### 3.1. Employer Blocking Lists
- Candidates can add specific enterprise organisations to their private blocking list.
- When an organisation is on a candidate’s blocking list:
  1. The candidate is completely filtered out of all candidate search results (`/api/v1/candidates/search`).
  2. The employer cannot view the candidate’s profile, active applications, or interview availability.
  3. The employer is never notified that they have been blocked.

### 3.2. PII Redaction & Minimization
- Government ID numbers (Aadhaar, SSN, PAN) are never stored in plain text. Only masked tokens (e.g., `XXXX-XXXX-1234`) and cryptographic verification hashes are retained.
- Uploaded identity documents are stored in private Supabase Storage buckets accessible exclusively via time-limited, signed URLs generated using a cryptographically secure pepper (`STORAGE_SIGNING_PEPPER`).

---

## 4. Government Verification & Ingestion Quarantine

1. **Malware Scanning (ClamAV)**:
   - Every file uploaded to the platform (resumes, government IDs, accreditation certificates) is streamed to ClamAV on port 3310 before persistence.
   - Files with detected malicious signatures are quarantined immediately and trigger a security incident event.
2. **Dual-Control Attestation**:
   - Automated KYC responses from SurePass or DigiLocker must be validated against the user's registered name and date of birth.
   - In case of OCR discrepancy, approval requires manual review by a Platform Admin (`AD`) with explicit review notes.

---

## 5. Automated Data Retention Schedules

To comply with global data protection laws (GDPR, DPDP Act 2023):

| Category | Retention Duration | Disposition Action |
|:---|:---:|:---|
| **KYC Verification Documents** | 7 Years (2,555 Days) | Automated hard delete of binary files after statutory compliance period |
| **Inactive Session Tokens** | 30 Days | Automated pruning of expired sessions and JWT refresh tokens |
| **Processed Webhook Records** | 90 Days | Pruned after reconciliation confirmation |
| **Rejected Job Applications** | 365 Days | Anonymized into aggregate data mart; candidate identity detached |
| **Immutable Audit Logs** | Indefinite / 7 Years | Archived to cold encrypted storage |
