"""Authoritative Reference Data Importers for Talentra Stage 15."""

import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
import pycountry
import phonenumbers
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.country import Country
from app.models.notification import Language
from app.models.job import EmploymentType, WorkType, JobRole, Industry


# --- 1. Countries (ISO 3166-1 & ITU-T E.164) ---

def get_country_dataset() -> List[Dict[str, Any]]:
    """Build complete normalized country records from ISO 3166-1 and ITU-T E.164."""
    dataset = []
    for c in pycountry.countries:
        a2 = c.alpha_2
        a3 = c.alpha_3
        num = getattr(c, "numeric", None)
        name = getattr(c, "common_name", None) or c.name

        # Resolve calling code from libphonenumber
        cc = phonenumbers.country_code_for_region(a2)
        calling_code = f"+{cc}" if cc else None

        dataset.append({
            "country_code": a2,
            "alpha3_code": a3,
            "numeric_code": num,
            "name": name[:150],
            "calling_code": calling_code,
            "is_active": True,
        })
    dataset.sort(key=lambda x: x["country_code"])
    return dataset


def seed_countries(db: Session) -> Tuple[int, int]:
    """Idempotently seed the complete ISO 3166-1 country master dataset."""
    countries = get_country_dataset()
    existing_codes = set(db.execute(select(Country.country_code)).scalars().all())
    inserted = 0

    for item in countries:
        if item["country_code"] not in existing_codes:
            new_country = Country(
                country_code=item["country_code"],
                alpha3_code=item["alpha3_code"],
                numeric_code=item["numeric_code"],
                name=item["name"],
                calling_code=item["calling_code"],
                is_active=item["is_active"],
            )
            db.add(new_country)
            inserted += 1

    if inserted > 0:
        db.commit()
    total_count = len(existing_codes) + inserted
    return inserted, total_count


# --- 2. Languages (ISO 639-1) ---

LANGUAGES_DATASET = [
    {"code": "en", "name": "English", "is_default": True},
    {"code": "hi", "name": "Hindi", "is_default": False},
    {"code": "es", "name": "Spanish", "is_default": False},
    {"code": "fr", "name": "French", "is_default": False},
    {"code": "de", "name": "German", "is_default": False},
    {"code": "zh", "name": "Chinese", "is_default": False},
    {"code": "ja", "name": "Japanese", "is_default": False},
    {"code": "ar", "name": "Arabic", "is_default": False},
    {"code": "pt", "name": "Portuguese", "is_default": False},
    {"code": "bn", "name": "Bengali", "is_default": False},
    {"code": "ta", "name": "Tamil", "is_default": False},
    {"code": "te", "name": "Telugu", "is_default": False},
    {"code": "mr", "name": "Marathi", "is_default": False},
]


def seed_languages(db: Session) -> Tuple[int, int]:
    """Idempotently seed ISO 639-1 languages."""
    inserted = 0
    for lang in LANGUAGES_DATASET:
        existing = db.execute(select(Language).where(Language.language_code == lang["code"])).scalar_one_or_none()
        if not existing:
            new_lang = Language(
                language_code=lang["code"],
                display_name=lang["name"],
                is_default=lang["is_default"],
            )
            db.add(new_lang)
            inserted += 1
    db.commit()
    total = db.execute(select(Language)).scalars().all()
    return inserted, len(total)


# --- 3. Currencies (ISO 4217) ---

CURRENCIES_DATASET = [
    {"code": "INR", "name": "Indian Rupee", "description": "National currency of India (₹)"},
    {"code": "USD", "name": "United States Dollar", "description": "Global reserve currency ($)"},
    {"code": "EUR", "name": "Euro", "description": "European Union currency (€)"},
    {"code": "GBP", "name": "British Pound Sterling", "description": "United Kingdom currency (£)"},
    {"code": "AED", "name": "United Arab Emirates Dirham", "description": "UAE national currency (د.إ)"},
    {"code": "SGD", "name": "Singapore Dollar", "description": "Singapore currency (S$)"},
    {"code": "CAD", "name": "Canadian Dollar", "description": "Canada currency (C$)"},
    {"code": "AUD", "name": "Australian Dollar", "description": "Australia currency (A$)"},
    {"code": "JPY", "name": "Japanese Yen", "description": "Japan national currency (¥)"},
    {"code": "CHF", "name": "Swiss Franc", "description": "Switzerland currency (CHF)"},
]


def _ensure_auxiliary_reference_tables(db: Session):
    """Ensures auxiliary reference tables exist in test/in-memory SQLite environments."""
    bind = db.get_bind()
    if bind.dialect.name == "sqlite":
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS currency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                status_code_id INTEGER DEFAULT 1,
                description TEXT,
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS qualification_level (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                status_code_id INTEGER DEFAULT 1,
                description TEXT,
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS qualification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qualification_code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS skill (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_code VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                parent_skill_id INTEGER,
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_id INTEGER,
                state_code VARCHAR(20) NOT NULL,
                name VARCHAR(150) NOT NULL,
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS city (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state_id INTEGER,
                name VARCHAR(150) NOT NULL,
                latitude NUMERIC,
                longitude NUMERIC,
                coordinate_source VARCHAR(50),
                created_at TIMESTAMP,
                created_by INTEGER,
                updated_at TIMESTAMP,
                updated_by INTEGER,
                deleted_at TIMESTAMP
            );
        """))
        db.commit()


def seed_currencies(db: Session) -> Tuple[int, int]:
    """Idempotently seed ISO 4217 currencies into currency table."""
    _ensure_auxiliary_reference_tables(db)
    inserted = 0
    now_utc = datetime.now(timezone.utc)
    for c in CURRENCIES_DATASET:
        row = db.execute(text("SELECT id FROM currency WHERE code = :code"), {"code": c["code"]}).fetchone()
        if not row:
            db.execute(
                text("""
                    INSERT INTO currency (code, name, status_code_id, description, created_at, updated_at)
                    VALUES (:code, :name, 1, :desc, :now, :now)
                """),
                {"code": c["code"], "name": c["name"], "desc": c["description"], "now": now_utc}
            )
            inserted += 1
    db.commit()
    total_count = db.execute(text("SELECT count(*) FROM currency")).scalar() or 0
    return inserted, total_count


# --- 4. Employment & Work Types & Taxonomies ---

EMPLOYMENT_TYPES = [
    {"code": "FULL_TIME", "name": "Full Time", "description": "Permanent standard full-time employment"},
    {"code": "PART_TIME", "name": "Part Time", "description": "Part-time employment"},
    {"code": "CONTRACT", "name": "Contract", "description": "Fixed-term contractor engagement"},
    {"code": "INTERNSHIP", "name": "Internship", "description": "Trainee or educational internship"},
    {"code": "FREELANCE", "name": "Freelance", "description": "Gig or project-based milestone engagement"},
]

WORK_TYPES = [
    {"code": "ONSITE", "name": "On-site", "description": "Full-time physical office presence"},
    {"code": "REMOTE", "name": "Remote", "description": "Fully remote work from anywhere"},
    {"code": "HYBRID", "name": "Hybrid", "description": "Blended on-site and remote schedule"},
]

INDUSTRIES = [
    {"code": "TECH", "name": "Technology, Software & Internet"},
    {"code": "HR_STAFFING", "name": "Human Resources & Talent Acquisition"},
    {"code": "FINANCE", "name": "Banking, Financial Services & Insurance"},
    {"code": "CONSULTING", "name": "Management & Technical Consulting"},
    {"code": "HEALTHCARE", "name": "Healthcare, Biotech & Pharmaceuticals"},
    {"code": "EDUCATION", "name": "Universities & Higher Education Institutions"},
]

JOB_ROLES = [
    {"code": "SOFTWARE_ENGINEER", "name": "Software Engineer", "industry_code": "TECH", "description": "Backend, frontend, or full-stack software development"},
    {"code": "DATA_SCIENTIST", "name": "Data Scientist", "industry_code": "TECH", "description": "Machine learning, AI, and statistical analytics"},
    {"code": "DEVOPS_ENGINEER", "name": "DevOps Engineer", "industry_code": "TECH", "description": "Infrastructure automation, CI/CD, and site reliability"},
    {"code": "PRODUCT_MANAGER", "name": "Product Manager", "industry_code": "TECH", "description": "Product strategy, roadmap, and stakeholder management"},
    {"code": "QA_ENGINEER", "name": "Quality Assurance & Test Automation Engineer", "industry_code": "TECH", "description": "Automated testing, test harnesses, and quality governance"},
    {"code": "SECURITY_ENGINEER", "name": "Cybersecurity & InfoSec Specialist", "industry_code": "TECH", "description": "Security auditing, vulnerability assessment, and threat modeling"},
    {"code": "RECRUITER", "name": "Talent Acquisition Specialist", "industry_code": "HR_STAFFING", "description": "Technical recruitment, sourcing, and candidate management"},
    {"code": "SOURCING_LEAD", "name": "Campus Sourcing & Relations Lead", "industry_code": "HR_STAFFING", "description": "University placement drive coordination and student talent pipelines"},
    {"code": "FINANCIAL_ANALYST", "name": "Financial Analyst", "industry_code": "FINANCE", "description": "Financial planning, accounting, and fiscal analysis"},
    {"code": "CONSULTANT_TECH", "name": "Technology Strategy Consultant", "industry_code": "CONSULTING", "description": "Architecture advising and enterprise systems modernization"},
]


def seed_taxonomies(db: Session) -> Dict[str, int]:
    """Seed foundational industries, employment types, work types, and job roles."""
    counts = {"industries": 0, "employment_types": 0, "work_types": 0, "job_roles": 0}

    for ind in INDUSTRIES:
        existing = db.execute(select(Industry).where(Industry.industry_code == ind["code"])).scalar_one_or_none()
        if not existing:
            db.add(Industry(industry_code=ind["code"], name=ind["name"]))
            counts["industries"] += 1
        else:
            existing.name = ind["name"]

    db.flush()

    for et in EMPLOYMENT_TYPES:
        existing = db.execute(select(EmploymentType).where(EmploymentType.code == et["code"])).scalar_one_or_none()
        if not existing:
            db.add(EmploymentType(code=et["code"], name=et["name"], status_code_id=1, description=et["description"]))
            counts["employment_types"] += 1

    for wt in WORK_TYPES:
        existing = db.execute(select(WorkType).where(WorkType.code == wt["code"])).scalar_one_or_none()
        if not existing:
            db.add(WorkType(code=wt["code"], name=wt["name"], status_code_id=1, description=wt["description"]))
            counts["work_types"] += 1

    for jr in JOB_ROLES:
        existing = db.execute(select(JobRole).where(JobRole.job_role_code == jr["code"])).scalar_one_or_none()
        if not existing:
            ind_record = db.execute(select(Industry).where(Industry.industry_code == jr.get("industry_code"))).scalar_one_or_none()
            ind_id = ind_record.id if ind_record else None
            db.add(JobRole(job_role_code=jr["code"], name=jr["name"], industry_id=ind_id))
            counts["job_roles"] += 1

    db.commit()
    return counts


# --- 5. Qualifications & Qualification Levels ---

QUALIFICATION_LEVELS_DATASET = [
    {"code": "SECONDARY", "name": "Class 10 / Secondary School", "description": "Matriculation or Secondary School Certificate"},
    {"code": "HIGHER_SECONDARY", "name": "Class 12 / Higher Secondary", "description": "Senior Secondary or Intermediate (+2)"},
    {"code": "DIPLOMA", "name": "Diploma / Polytechnic", "description": "Engineering or Vocational Diploma"},
    {"code": "UNDERGRADUATE", "name": "Undergraduate Degree", "description": "Bachelor's level degree program"},
    {"code": "POSTGRADUATE", "name": "Postgraduate Degree", "description": "Master's level degree program"},
    {"code": "DOCTORATE", "name": "Doctorate / Ph.D", "description": "Doctoral research degree program"},
]

QUALIFICATIONS_DATASET = [
    {"code": "CLASS_10", "name": "Class 10 / SSC / Matriculation"},
    {"code": "CLASS_12", "name": "Class 12 / HSC / Intermediate"},
    {"code": "DIPLOMA_ENGG", "name": "Diploma in Engineering & Technology"},
    {"code": "BTECH", "name": "Bachelor of Technology (B.Tech)"},
    {"code": "BE", "name": "Bachelor of Engineering (B.E.)"},
    {"code": "BSC_CS", "name": "Bachelor of Science in Computer Science (B.Sc CS)"},
    {"code": "BCA", "name": "Bachelor of Computer Applications (BCA)"},
    {"code": "MTECH", "name": "Master of Technology (M.Tech)"},
    {"code": "MCA", "name": "Master of Computer Applications (MCA)"},
    {"code": "MBA", "name": "Master of Business Administration (MBA)"},
    {"code": "MS_CS", "name": "Master of Science in Computing (M.S.)"},
    {"code": "PHD_ENGG", "name": "Doctor of Philosophy in Engineering (Ph.D)"},
]


def seed_qualifications(db: Session) -> Tuple[int, int]:
    """Idempotently seed qualification levels and qualifications."""
    inserted = 0
    now_utc = datetime.now(timezone.utc)

    # Qualification levels
    for ql in QUALIFICATION_LEVELS_DATASET:
        row = db.execute(text("SELECT id FROM qualification_level WHERE code = :code"), {"code": ql["code"]}).fetchone()
        if not row:
            db.execute(
                text("""
                    INSERT INTO qualification_level (code, name, status_code_id, description, created_at, updated_at)
                    VALUES (:code, :name, 1, :desc, :now, :now)
                """),
                {"code": ql["code"], "name": ql["name"], "desc": ql["description"], "now": now_utc}
            )
            inserted += 1

    # Qualifications
    for q in QUALIFICATIONS_DATASET:
        row = db.execute(text("SELECT id FROM qualification WHERE qualification_code = :code"), {"code": q["code"]}).fetchone()
        if not row:
            db.execute(
                text("""
                    INSERT INTO qualification (qualification_code, name, created_at, updated_at)
                    VALUES (:code, :name, :now, :now)
                """),
                {"code": q["code"], "name": q["name"], "now": now_utc}
            )
            inserted += 1

    db.commit()
    total_quals = db.execute(text("SELECT count(*) FROM qualification")).scalar() or 0
    return inserted, total_quals


# --- 6. Skills Taxonomy ---

SKILLS_DATASET = [
    # Programming Languages
    {"code": "PYTHON", "name": "Python"},
    {"code": "JAVASCRIPT", "name": "JavaScript"},
    {"code": "TYPESCRIPT", "name": "TypeScript"},
    {"code": "JAVA", "name": "Java"},
    {"code": "C_PLUS_PLUS", "name": "C++"},
    {"code": "GO", "name": "Go (Golang)"},
    {"code": "RUST", "name": "Rust"},
    {"code": "SQL", "name": "SQL & Relational Databases"},
    # Web & Frameworks
    {"code": "REACT", "name": "React.js"},
    {"code": "NEXTJS", "name": "Next.js"},
    {"code": "NODEJS", "name": "Node.js"},
    {"code": "FASTAPI", "name": "FastAPI"},
    {"code": "DJANGO", "name": "Django"},
    {"code": "SPRING_BOOT", "name": "Spring Boot"},
    # Cloud & DevOps
    {"code": "DOCKER", "name": "Docker & Containerization"},
    {"code": "KUBERNETES", "name": "Kubernetes"},
    {"code": "AWS", "name": "Amazon Web Services (AWS)"},
    {"code": "GCP", "name": "Google Cloud Platform (GCP)"},
    {"code": "AZURE", "name": "Microsoft Azure"},
    {"code": "TERRAFORM", "name": "Terraform & IaC"},
    {"code": "CI_CD", "name": "CI/CD & GitHub Actions"},
    {"code": "POSTGRESQL", "name": "PostgreSQL"},
    {"code": "REDIS", "name": "Redis In-Memory Caching"},
    # Data & Machine Learning
    {"code": "MACHINE_LEARNING", "name": "Machine Learning"},
    {"code": "PYTORCH", "name": "PyTorch"},
    {"code": "TENSORFLOW", "name": "TensorFlow"},
    {"code": "DATA_STRUCTURES", "name": "Data Structures & Algorithms"},
    {"code": "SYSTEM_DESIGN", "name": "Distributed System Design"},
]


def seed_skills(db: Session) -> Tuple[int, int]:
    """Idempotently seed standard skills taxonomy."""
    inserted = 0
    now_utc = datetime.now(timezone.utc)

    for s in SKILLS_DATASET:
        row = db.execute(text("SELECT id FROM skill WHERE skill_code = :code"), {"code": s["code"]}).fetchone()
        if not row:
            db.execute(
                text("""
                    INSERT INTO skill (skill_code, name, created_at, updated_at)
                    VALUES (:code, :name, :now, :now)
                """),
                {"code": s["code"], "name": s["name"], "now": now_utc}
            )
            inserted += 1

    db.commit()
    total_skills = db.execute(text("SELECT count(*) FROM skill")).scalar() or 0
    return inserted, total_skills


# --- 7. States & Major Cities ---

STATES_AND_CITIES = [
    {
        "country_code": "IN",
        "state_code": "KA",
        "state_name": "Karnataka",
        "cities": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru"],
    },
    {
        "country_code": "IN",
        "state_code": "MH",
        "state_name": "Maharashtra",
        "cities": ["Mumbai", "Pune", "Nagpur", "Nashik"],
    },
    {
        "country_code": "IN",
        "state_code": "TS",
        "state_name": "Telangana",
        "cities": ["Hyderabad", "Warangal"],
    },
    {
        "country_code": "IN",
        "state_code": "DL",
        "state_name": "Delhi",
        "cities": ["New Delhi", "Dwarka"],
    },
    {
        "country_code": "IN",
        "state_code": "TN",
        "state_name": "Tamil Nadu",
        "cities": ["Chennai", "Coimbatore", "Madurai"],
    },
    {
        "country_code": "US",
        "state_code": "CA",
        "state_name": "California",
        "cities": ["San Francisco", "San Jose", "Los Angeles"],
    },
    {
        "country_code": "US",
        "state_code": "NY",
        "state_name": "New York",
        "cities": ["New York City", "Buffalo"],
    },
    {
        "country_code": "GB",
        "state_code": "ENG",
        "state_name": "England",
        "cities": ["London", "Manchester", "Birmingham"],
    },
]


def seed_states_and_cities(db: Session) -> Tuple[int, int]:
    """Idempotently seed states and cities."""
    inserted_states = 0
    inserted_cities = 0
    now_utc = datetime.now(timezone.utc)

    for item in STATES_AND_CITIES:
        c_row = db.execute(text("SELECT id FROM country WHERE country_code = :cc"), {"cc": item["country_code"]}).fetchone()
        if not c_row:
            continue
        country_id = c_row[0]

        s_row = db.execute(
            text("SELECT id FROM state WHERE country_id = :cid AND state_code = :scode"),
            {"cid": country_id, "scode": item["state_code"]},
        ).fetchone()

        if not s_row:
            s_id = db.execute(
                text("""
                    INSERT INTO state (country_id, state_code, name, created_at, updated_at)
                    VALUES (:cid, :scode, :sname, :now, :now)
                    RETURNING id
                """),
                {"cid": country_id, "scode": item["state_code"], "sname": item["state_name"], "now": now_utc},
            ).scalar()
            inserted_states += 1
        else:
            s_id = s_row[0]

        for city_name in item["cities"]:
            city_row = db.execute(
                text("SELECT id FROM city WHERE state_id = :sid AND name = :name"),
                {"sid": s_id, "name": city_name},
            ).fetchone()
            if not city_row:
                db.execute(
                    text("""
                        INSERT INTO city (state_id, name, created_at, updated_at)
                        VALUES (:sid, :name, :now, :now)
                    """),
                    {"sid": s_id, "name": city_name, "now": now_utc},
                )
                inserted_cities += 1

    db.commit()
    total_cities = db.execute(text("SELECT count(*) FROM city")).scalar() or 0
    return inserted_cities, total_cities
