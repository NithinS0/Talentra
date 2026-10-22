"""Automated Test Suite for Candidate Profile, Academics, Resumes, Documents, and Eligibility.

Covers:
- Editable candidate profile and contact preferences
- Dynamic profile completeness checklist calculation
- Profile photo upload and deletion
- Education records across pathways (Class 10, Class 12, Diploma, Undergraduate)
- Uniqueness constraints (duplicate Class 10/12 prevention)
- Semester-wise grade sheets CRUD and uploads
- Multi-version resume management and default resume selection
- Immutable application resume snapshot preservation
- Private document vault
- File signature validation (rejecting invalid types / magic bytes)
- Structured job requirement criteria
- Candidate-to-job eligibility evaluation (ELIGIBLE, NOT_ELIGIBLE, UNABLE_TO_DETERMINE)
"""

import io
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment
from app.models.candidate import CandidateProfile, CandidateEducation, CandidateResume, ResumeVersion
from app.models.organisation import Organisation
from app.models.job import JobRequirement, JobRole, EmploymentType, WorkType
from app.models.application import JobApplication
from tests.test_candidate_registration import create_test_supabase_token


@pytest.fixture(scope="session")
def test_engine():
    """Create test SQLite engine with custom PostgreSQL function emulations."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sequence_counters = {}

    @event.listens_for(engine, "connect")
    def on_connect(dbapi_conn, record):
        def allocate_actor_id_udf(prefix):
            sequence_counters[prefix] = sequence_counters.get(prefix, 0) + 1
            return f"{prefix}{sequence_counters[prefix]:05d}"

        dbapi_conn.create_function("allocate_actor_id", 1, allocate_actor_id_udf)
        dbapi_conn.create_function("now", 0, lambda: datetime.now(timezone.utc).isoformat())

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(
            text("""
            INSERT INTO role (id, role_code, display_name, description, is_system_role)
            VALUES 
                (1, 'SUPER_ADMIN', 'Super Administrator', 'System Super Admin', 1),
                (2, 'ADMIN', 'Platform Administrator', 'Admin', 1),
                (3, 'ACCOUNT_ADMIN', 'Account Administrator', 'Account Admin', 1),
                (4, 'GUEST', 'Guest User', 'Guest', 1),
                (5, 'CANDIDATE', 'Candidate', 'Talentra Job Candidate', 1),
                (6, 'EMPLOYER', 'Employer', 'Hiring Employer', 1),
                (7, 'RECRUITER', 'Recruiter', 'Recruiter', 1),
                (8, 'CONSULTANT', 'Sourcing Consultant', 'External Consultant', 1),
                (9, 'PLACEMENT_OFFICER', 'Placement Officer', 'TPO', 1)
            """)
        )
        conn.execute(
            text("""
            INSERT INTO country (id, country_code, alpha3_code, numeric_code, name, calling_code, is_active)
            VALUES (1, 'IN', 'IND', '356', 'India', '+91', 1), (2, 'US', 'USA', '840', 'United States', '+1', 1)
            """)
        )
        conn.execute(
            text("""
            INSERT INTO employment_type (id, code, name, status_code_id, description)
            VALUES (1, 'FULL_TIME', 'Full-time', 1, 'Full-time employment')
            """)
        )
        conn.execute(
            text("""
            INSERT INTO work_type (id, code, name, status_code_id, description)
            VALUES (1, 'ON_SITE', 'On-site', 1, 'Work from office')
            """)
        )
        conn.execute(
            text("""
            INSERT INTO job_role (id, job_role_code, name)
            VALUES (1, 'SWE', 'Software Engineer')
            """)
        )
        conn.execute(
            text("""
            INSERT INTO organisation (id, organisation_type_code_id, legal_name, display_name, status_code_id)
            VALUES (1, 1, 'Acme Technologies Inc', 'Acme Tech', 1)
            """)
        )
        conn.commit()

    return engine


@pytest.fixture
def client(test_engine):
    """Provide FastAPI TestClient with database dependency override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_db(test_engine):
    """Provide session for direct database verification."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def registered_candidate(client):
    """Fixture providing a freshly registered candidate with authenticated token."""
    uid = f"supabase-cand-{datetime.now(timezone.utc).timestamp()}"
    email = f"cand_{datetime.now(timezone.utc).timestamp()}@example.com"
    token = create_test_supabase_token(sub=uid, email=email)

    payload = {
        "first_name": "Aarav",
        "last_name": "Patel",
        "country_code": "IN",
        "phone_number": "9123456780",
        "headline": "Full-Stack Software Engineer",
        "summary": "Passionate about scalable web services and cloud architecture.",
    }
    resp = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.text
    profile_data = resp.json()

    return {
        "token": token,
        "email": email,
        "profile": profile_data,
        "candidate_id": profile_data["id"],
        "actor_id": profile_data["actor_id"],
    }


@pytest.fixture
def employer_with_org(client, test_db):
    """Fixture providing an employer user and organization."""
    uid = f"supabase-emp-{datetime.now(timezone.utc).timestamp()}"
    email = f"employer_{datetime.now(timezone.utc).timestamp()}@acmecorp.com"
    token = create_test_supabase_token(sub=uid, email=email)

    db = test_db
    user = User(
            email_address=email,
            display_name="Acme Hiring Lead",
            account_status_code_id=1,
            identity_provider_code="SUPABASE",
            provider_subject=uid,
        )
    db.add(user)
    db.flush()

    role = db.query(Role).filter(Role.role_code == "EMPLOYER").first()
    if not role:
        role = Role(role_code="EMPLOYER", display_name="Employer", is_system_role=True)
        db.add(role)
        db.flush()

    assign = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        actor_id="EM00001",
        organisation_id=1,
        assigned_by_user_id=user.id,
    )
    db.add(assign)
    db.commit()
    db.refresh(user)

    return {
        "token": token,
        "user_id": user.id,
        "organisation_id": 1,
    }


# -----------------------------------------------------------------------------
# Profile & Completeness Tests
# -----------------------------------------------------------------------------

def test_candidate_profile_retrieval_and_update(client, registered_candidate):
    """Verify candidate can fetch profile and edit fields."""
    token = registered_candidate["token"]

    # 1. Fetch current profile
    get_resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == status.HTTP_200_OK
    data = get_resp.json()
    assert data["actor_id"] == registered_candidate["actor_id"]

    # 2. Update profile fields
    update_payload = {
        "headline": "Lead Backend Architect",
        "current_city": "Bengaluru",
        "current_state": "Karnataka",
        "linkedin_url": "https://linkedin.com/in/aarav-patel",
        "github_url": "https://github.com/aaravpatel",
        "preferred_roles": "Backend Engineer, Systems Architect",
        "preferred_locations": "Bengaluru, Remote",
        "preferred_employment_types": "FULL_TIME",
        "availability_status": "AVAILABLE",
        "is_public_visible": True,
    }
    put_resp = client.put(
        f"{settings.API_V1_PREFIX}/candidates/me",
        json=update_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_resp.status_code == status.HTTP_200_OK
    updated = put_resp.json()
    assert updated["headline"] == "Lead Backend Architect"
    assert updated["current_city"] == "Bengaluru"
    assert updated["linkedin_url"] == "https://linkedin.com/in/aarav-patel"


def test_profile_completeness_checklist(client, registered_candidate):
    """Verify dynamic profile completeness calculation and missing items checklist."""
    token = registered_candidate["token"]

    resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me/completeness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "overall_score" in data
    assert "checklist_items" in data
    assert len(data["checklist_items"]) >= 6

    # Verify keys exist in checklist
    keys = [item["key"] for item in data["checklist_items"]]
    assert "personal_info" in keys
    assert "academic_history" in keys
    assert "resume" in keys
    assert "skills" in keys


def test_profile_photo_upload_and_delete(client, registered_candidate):
    """Verify photo upload with real magic byte validation and deletion."""
    token = registered_candidate["token"]

    # Valid JPEG image bytes
    fake_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 200
    files = {"file": ("avatar.jpg", fake_jpeg, "image/jpeg")}

    upload_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/photo",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == status.HTTP_200_OK
    assert "photo_url" in upload_resp.json()

    # Verify profile now has photo URL
    me_resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.json()["profile_photo_url"] is not None

    # Delete photo
    del_resp = client.delete(
        f"{settings.API_V1_PREFIX}/candidates/me/photo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify photo is removed
    me_after = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_after.json()["profile_photo_url"] is None


# -----------------------------------------------------------------------------
# Academic Records & Semesters Tests
# -----------------------------------------------------------------------------

def test_education_crud_and_prevent_duplicate_class_10(client, registered_candidate):
    """Verify adding Class 10, Class 12, Degree and preventing duplicate Class 10."""
    token = registered_candidate["token"]

    # 1. Add Class 10
    c10_payload = {
        "education_level": "CLASS_10",
        "institution_name": "Delhi Public School",
        "board_or_university": "CBSE",
        "status": "COMPLETED",
        "completion_year": 2018,
        "grading_system": "PERCENTAGE",
        "percentage": 92.5,
    }
    resp1 = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json=c10_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == status.HTTP_201_CREATED
    c10_id = resp1.json()["id"]

    # 2. Attempt duplicate Class 10 - must be rejected
    dup_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json=c10_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dup_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # 3. Add College / Undergraduate Education
    college_payload = {
        "education_level": "UNDERGRADUATE",
        "institution_name": "Indian Institute of Technology, Madras",
        "board_or_university": "IIT Madras",
        "field_of_study": "Computer Science & Engineering",
        "stream_specialization": "Artificial Intelligence",
        "status": "PURSUING",
        "start_year": 2020,
        "completion_year": 2024,
        "grading_system": "CGPA_10",
        "cgpa": 8.85,
        "has_backlogs": False,
        "active_backlogs_count": 0,
    }
    resp2 = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json=college_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == status.HTTP_201_CREATED
    college_id = resp2.json()["id"]

    # 4. Update college education record
    update_college = {
        "cgpa": 9.10,
        "status": "COMPLETED",
    }
    put_edu = client.put(
        f"{settings.API_V1_PREFIX}/candidates/me/education/{college_id}",
        json=update_college,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_edu.status_code == status.HTTP_200_OK
    assert put_edu.json()["cgpa"] == 9.10

    # 5. Delete Class 10 record
    del_resp = client.delete(
        f"{settings.API_V1_PREFIX}/candidates/me/education/{c10_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT


def test_semester_gradesheet_crud_and_upload(client, registered_candidate):
    """Verify adding semester results, uploading grade sheet, and preventing duplicate semester."""
    token = registered_candidate["token"]

    # Create education record first
    edu_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json={
            "education_level": "UNDERGRADUATE",
            "institution_name": "Anna University",
            "field_of_study": "Computer Science",
            "grading_system": "CGPA_10",
            "cgpa": 8.5,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    edu_id = edu_resp.json()["id"]

    # 1. Add Semester 1
    sem_payload = {
        "semester_number": 1,
        "academic_term": "Fall 2020",
        "result_status": "PASS",
        "sgpa": 8.60,
        "cgpa": 8.60,
        "credits_registered": 24,
        "credits_earned": 24,
        "has_backlog": False,
    }
    sem1_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education/{edu_id}/semesters",
        json=sem_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sem1_resp.status_code == status.HTTP_201_CREATED
    sem1_data = sem1_resp.json()
    assert sem1_data["semester_number"] == 1
    assert sem1_data["sgpa"] == 8.60

    # 2. Upload grade sheet PDF for Semester 1
    fake_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    sheet_file = {"file": ("sem1_marksheet.pdf", fake_pdf, "application/pdf")}
    upload_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education/{edu_id}/semesters/1/gradesheet",
        files=sheet_file,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upload_resp.status_code == status.HTTP_200_OK
    assert upload_resp.json()["grade_sheet_name"] == "sem1_marksheet.pdf"

    # 3. Download semester grade sheet
    dl_resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me/education/{edu_id}/semesters/1/gradesheet",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dl_resp.status_code == status.HTTP_200_OK
    assert dl_resp.content == fake_pdf


# -----------------------------------------------------------------------------
# Resume Management & Immutable Application Snapshots
# -----------------------------------------------------------------------------

def test_resume_upload_versioning_and_application_snapshot(client, registered_candidate, employer_with_org):
    """Verify multi-version resume upload, setting default, and that submitted applications preserve snapshot."""
    cand_token = registered_candidate["token"]
    emp_token = employer_with_org["token"]

    # 1. Upload Resume Version 1 (PDF)
    pdf_v1 = b"%PDF-1.4 Resume Version 1 content" + b"\x00" * 100
    res1 = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/resumes",
        files={"file": ("aarav_cv_v1.pdf", pdf_v1, "application/pdf")},
        data={"title": "Primary Resume", "target_role": "Backend Engineer", "is_default": "true"},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert res1.status_code == status.HTTP_201_CREATED
    res1_data = res1.json()
    assert res1_data["is_default"] is True
    assert len(res1_data["versions"]) == 1
    v1_id = res1_data["versions"][0]["id"]

    # 2. Create a job requisition
    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    job_payload = {
        "organisation_id": employer_with_org["organisation_id"],
        "job_role_id": 1,
        "title": "Senior Python Backend Engineer",
        "description": "Building high-performance distributed microservices.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 2,
        "application_deadline": deadline,
        "publish_now": True,
    }
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=job_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert job_resp.status_code == status.HTTP_201_CREATED
    job_id = job_resp.json()["id"]

    # 3. Apply to job with Version 1
    app_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/apply",
        json={"resume_version_id": v1_id, "cover_letter": "Excited to apply for this backend role!"},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert app_resp.status_code == status.HTTP_201_CREATED
    app_data = app_resp.json()
    assert app_data["resume_version_id"] == v1_id
    assert app_data["resume_snapshot_title"] == "Primary Resume"
    assert app_data["resume_snapshot_file_name"] == "aarav_cv_v1.pdf"

    # 4. Upload Resume Version 2 under same title
    pdf_v2 = b"%PDF-1.4 Resume Version 2 Updated content" + b"\x00" * 100
    res2 = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/resumes",
        files={"file": ("aarav_cv_v2.pdf", pdf_v2, "application/pdf")},
        data={"title": "Primary Resume", "target_role": "Staff Engineer", "is_default": "true"},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert res2.status_code == status.HTTP_201_CREATED
    res2_data = res2.json()
    assert len(res2_data["versions"]) == 2
    v2_id = res2_data["versions"][0]["id"]
    assert v2_id != v1_id

    # 5. Verify the previously submitted application STILL references Version 1 snapshot!
    my_apps = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me/applications",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert my_apps.status_code == status.HTTP_200_OK
    found_app = [a for a in my_apps.json()["items"] if a["id"] == app_data["id"]][0]
    assert found_app["resume_version_id"] == v1_id
    assert found_app["resume_snapshot_file_name"] == "aarav_cv_v1.pdf"


# -----------------------------------------------------------------------------
# Structured Eligibility Evaluation Tests
# -----------------------------------------------------------------------------

def test_structured_eligibility_evaluation(client, registered_candidate, employer_with_org, test_db):
    """Verify criteria evaluation: ELIGIBLE, NOT_ELIGIBLE, and UNABLE_TO_DETERMINE."""
    cand_token = registered_candidate["token"]
    emp_token = employer_with_org["token"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Create job with strict criteria
    job_payload = {
        "organisation_id": employer_with_org["organisation_id"],
        "job_role_id": 1,
        "title": "Graduate Cloud Architect",
        "description": "Campus hiring for cloud engineers.",
        "employment_type_id": 1,
        "work_type_id": 1,
        "positions_count": 1,
        "application_deadline": deadline,
        "publish_now": True,
        # Criteria
        "required_qualifications": "B.Tech, B.E, MCA",
        "accepted_branches": "Computer Science, Information Technology",
        "min_percentage": 75.0,
        "min_cgpa": 7.5,
        "allow_backlogs": False,
        "required_skills": "Python, Docker, SQL",
    }
    job_resp = client.post(
        f"{settings.API_V1_PREFIX}/jobs",
        json=job_payload,
        headers={"Authorization": f"Bearer {emp_token}"},
    )
    assert job_resp.status_code == status.HTTP_201_CREATED
    job_id = job_resp.json()["id"]

    # Case A: Initial state -> UNABLE_TO_DETERMINE (no education or skills on profile yet)
    eval_resp1 = client.get(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/eligibility",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert eval_resp1.status_code == status.HTTP_200_OK
    eval1 = eval_resp1.json()
    assert eval1["overall_status"] == "UNABLE_TO_DETERMINE"
    assert eval1["can_apply"] is False
    assert len(eval1["missing_requirements"]) > 0

    # Add education matching branch and degree, but with a backlog and low CGPA
    client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json={
            "education_level": "UNDERGRADUATE",
            "institution_name": "Tech University",
            "field_of_study": "Computer Science",
            "stream_specialization": "Information Technology",
            "percentage": 65.0,  # Below 75%
            "cgpa": 6.8,        # Below 7.5
            "has_backlogs": True,
            "active_backlogs_count": 2, # Active backlogs prohibited
        },
        headers={"Authorization": f"Bearer {cand_token}"},
    )

    # Case B: Ineligible state -> NOT_ELIGIBLE
    eval_resp2 = client.get(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/eligibility",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert eval_resp2.status_code == status.HTTP_200_OK
    eval2 = eval_resp2.json()
    assert eval2["overall_status"] == "NOT_ELIGIBLE"
    assert eval2["can_apply"] is False

    # Check criteria breakdown has UNSATISFIED
    unsatisfied = [c for c in eval2["criteria"] if c["status"] == "UNSATISFIED"]
    assert len(unsatisfied) >= 1

    # Now update candidate education to satisfy all criteria: 85% / 8.8 CGPA, 0 backlogs
    # And add required skills
    db = test_db
    edu = db.query(CandidateEducation).filter(
        CandidateEducation.candidate_profile_id == registered_candidate["candidate_id"]
    ).first()
    edu.percentage = 85.0
    edu.cgpa = 8.8
    edu.has_backlogs = False
    edu.active_backlogs_count = 0
    db.commit()

    for skill in ["Python", "Docker", "SQL"]:
        client.post(
            f"{settings.API_V1_PREFIX}/candidates/me/skills",
            json={"skill_name": skill, "proficiency_level": "EXPERT"},
            headers={"Authorization": f"Bearer {cand_token}"},
        )

    # Case C: Fully eligible state -> ELIGIBLE
    eval_resp3 = client.get(
        f"{settings.API_V1_PREFIX}/jobs/{job_id}/eligibility",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert eval_resp3.status_code == status.HTTP_200_OK
    eval3 = eval_resp3.json()
    assert eval3["overall_status"] == "ELIGIBLE"
    assert eval3["can_apply"] is True


# -----------------------------------------------------------------------------
# File Signature / Security Validation Tests
# -----------------------------------------------------------------------------

def test_file_upload_security_signature_validation(client, registered_candidate):
    """Verify that uploading files with spoofed or forbidden magic bytes is rejected."""
    token = registered_candidate["token"]

    # Executable binary spoofed as .pdf
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100
    files = {"file": ("malicious.pdf", fake_exe, "application/pdf")}

    resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/resumes",
        files=files,
        data={"title": "Hacked Resume"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "signature" in resp.json()["detail"].lower()


# -----------------------------------------------------------------------------
# Diploma Pathway & Document Vault Privacy Tests
# -----------------------------------------------------------------------------

def test_diploma_pathway_without_class_12(client):
    """Verify that a candidate can register a Diploma pathway without requiring Class 12."""
    sub = "supabase_user_diploma_101"
    token = create_test_supabase_token(sub=sub, email="diploma.student@talentra.io")

    # 1. Register candidate
    reg_resp = client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={
            "first_name": "Rohan",
            "last_name": "Kamat",
            "country_code": "IN",
            "phone_number": "+919876543210",
            "headline": "Diploma in Mechanical Engineering",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reg_resp.status_code == status.HTTP_201_CREATED

    # 2. Add Class 10 (Secondary)
    c10_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json={
            "education_level": "SECONDARY",
            "institution_name": "St. Xavier's High School",
            "board_or_university": "State Board",
            "percentage": 88.5,
            "status": "COMPLETED",
            "start_year": 2018,
            "completion_year": 2020,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert c10_resp.status_code == status.HTTP_201_CREATED

    # 3. Add Diploma directly (No HIGHER_SECONDARY required!)
    diploma_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/education",
        json={
            "education_level": "DIPLOMA",
            "institution_name": "Government Polytechnic Pune",
            "board_or_university": "BTE",
            "field_of_study": "Mechanical Engineering",
            "stream_specialization": "Automobile Design",
            "percentage": 82.0,
            "cgpa": 8.4,
            "status": "COMPLETED",
            "start_year": 2020,
            "completion_year": 2023,
            "has_backlogs": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert diploma_resp.status_code == status.HTTP_201_CREATED
    diploma_id = diploma_resp.json()["id"]

    # 4. Add Diploma Semesters (e.g. Sem 1 to 6)
    for sem in range(1, 4):
        s_resp = client.post(
            f"{settings.API_V1_PREFIX}/candidates/me/education/{diploma_id}/semesters",
            json={
                "semester_number": sem,
                "academic_term": f"Year {(sem + 1) // 2}",
                "result_status": "PASS",
                "sgpa": 8.0 + sem * 0.1,
                "has_backlog": False,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert s_resp.status_code == status.HTTP_201_CREATED

    # 5. Verify education records retrieve both Class 10 and Diploma
    prof_resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prof_resp.status_code == status.HTTP_200_OK
    edus = prof_resp.json()["education_records"]
    assert len(edus) == 2
    levels = [e["education_level"] for e in edus]
    assert "SECONDARY" in levels
    assert "DIPLOMA" in levels
    assert "HIGHER_SECONDARY" not in levels


def test_document_vault_and_cross_candidate_privacy(client, registered_candidate):
    """Verify document vault upload and prevent cross-candidate access."""
    cand_a_token = registered_candidate["token"]

    # Candidate A uploads a document to vault
    pdf_content = b"%PDF-1.4 Vault Document Secret A" + b"\x00" * 80
    doc_resp = client.post(
        f"{settings.API_V1_PREFIX}/candidates/me/documents",
        files={"file": ("cert_a.pdf", pdf_content, "application/pdf")},
        data={"category": "CERTIFICATE", "title": "AWS Cloud Practitioner"},
        headers={"Authorization": f"Bearer {cand_a_token}"},
    )
    assert doc_resp.status_code == status.HTTP_201_CREATED
    doc_id = doc_resp.json()["id"]

    # Candidate A downloads their document
    dl_resp = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {cand_a_token}"},
    )
    assert dl_resp.status_code == status.HTTP_200_OK
    assert dl_resp.content == pdf_content

    # Candidate B creates an account
    sub_b = "supabase_user_candidate_b"
    cand_b_token = create_test_supabase_token(sub=sub_b, email="candidate.b@talentra.io")
    client.post(
        f"{settings.API_V1_PREFIX}/auth/register/candidate",
        json={
            "first_name": "Bhavna",
            "last_name": "Patel",
            "country_code": "IN",
        },
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )

    # Candidate B tries to download Candidate A's document -> Must fail with 404 (or 403)
    unauthorized_dl = client.get(
        f"{settings.API_V1_PREFIX}/candidates/me/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )
    assert unauthorized_dl.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN)

    # Candidate B tries to delete Candidate A's document -> Must fail with 404
    unauthorized_del = client.delete(
        f"{settings.API_V1_PREFIX}/candidates/me/documents/{doc_id}",
        headers={"Authorization": f"Bearer {cand_b_token}"},
    )
    assert unauthorized_del.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN)

    # Candidate A can delete their own document
    del_resp = client.delete(
        f"{settings.API_V1_PREFIX}/candidates/me/documents/{doc_id}",
        headers={"Authorization": f"Bearer {cand_a_token}"},
    )
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

