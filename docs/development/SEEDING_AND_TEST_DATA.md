# Talentra — Seeding & Test Data Guide

## 1. Reference Master Data Overview

Talentra requires baseline reference master data for core taxonomies before transactional workflows (candidate profile creation, job posting, and campus drive scheduling) can operate.

The canonical master data runner is located at `backend/app/seeds/seed_reference_data.py`.

---

## 2. Master Data Populations

### 2.1. Reference Countries (`ref_countries`)
The seed runner populates 8 primary operational countries with ISO-3166 codes and dial codes:
- India (`IN`, `IND`, `+91`, Currency: `INR`)
- United States (`US`, `USA`, `+1`, Currency: `USD`)
- United Kingdom (`GB`, `GBR`, `+44`, Currency: `GBP`)
- United Arab Emirates (`AE`, `ARE`, `+971`, Currency: `AED`)
- Singapore (`SG`, `SGP`, `+65`, Currency: `SGD`)
- Germany (`DE`, `DEU`, `+49`, Currency: `EUR`)
- Canada (`CA`, `CAN`, `+1`, Currency: `CAD`)
- Australia (`AU`, `AUS`, `+61`, Currency: `AUD`)

### 2.2. Reference Currencies (`ref_currencies`)
- `INR` — Indian Rupee (₹)
- `USD` — US Dollar ($)
- `EUR` — Euro (€)
- `GBP` — British Pound (£)
- `AED` — UAE Dirham (د.إ)
- `SGD` — Singapore Dollar (S$)

### 2.3. Reference Languages (`ref_languages`)
- `en` — English
- `hi` — Hindi
- `es` — Spanish
- `fr` — French
- `de` — German

### 2.4. Core Docket Roles (`roles`)
The platform initializes the 9 canonical personas with appropriate description and scope:
1. `SUPER_ADMIN` (Code: `SA`)
2. `PLATFORM_ADMIN` (Code: `AD`)
3. `ACCOUNT_ADMIN` (Code: `AA`)
4. `GUEST_USER` (Code: `GU`)
5. `CANDIDATE` (Code: `CA`)
6. `EMPLOYER` (Code: `EM`)
7. `RECRUITER` (Code: `RE`)
8. `CONSULTANT` (Code: `CO`)
9. `PLACEMENT_OFFICER` (Code: `PO`)

---

## 3. Executing Master Data Seeding

From the repository root with virtual environment activated:

```powershell
.\.venv\Scripts\python.exe backend/app/seeds/seed_reference_data.py
```

The script is **idempotent** — it uses `ON CONFLICT DO NOTHING` / upsert logic so executing it multiple times will not create duplicate records or violate unique constraints.

---

## 4. Synthetic Test Data & Scale Profiles

For development, testing, and staging environments, synthetic persona data can be generated using the scripts in `scripts/` and `backend/app/seeds/`:

### 4.1. Persona Test Profiles
- **Candidate Profiles**: Realistic student records with academic scores, 10th/12th/B.Tech CGPAs, uploaded sample resumes, and skill tags (React, Python, TypeScript, SQL).
- **Organisation Profiles**: Sample tech enterprises, placement partner universities, and boutique recruitment consultancies.
- **Jobs & Applications**: Open requisitions in active, screening, and closed states with populated applicant pipelines across all stages.
- **Campus Placement Drives**: University-specific drive events with eligible student cohorts and scheduled interview slots.

---

## 5. Safety & Environment Guardrails

- **Zero Destructive Operations**: Seed scripts must never issue `DROP TABLE`, `TRUNCATE CASCADE`, or delete production data.
- **Production Guard**: Seed scripts check `APP_ENV`. If `APP_ENV=production`, synthetic test profile generation is blocked automatically to prevent polluting production databases.
