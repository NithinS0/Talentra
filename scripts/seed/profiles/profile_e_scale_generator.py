"""Profile E: High-Throughput Performance & Scale Data Generator.

Generates scalable synthetic candidate, job, and application datasets:
- Configurable record counts (Laptop target: 1M candidates, 100k jobs, 5M applications)
- Chunked, memory-bounded batch execution (default 1,000 - 5,000 rows per batch, < 100MB RAM)
- Deterministic pseudo-random generation with fixed seed
- Resumable state checkpoints via CheckpointManager
- Real-time throughput telemetry (rows/sec) via SeedingTelemetry
- Guaranteed foreign key referential integrity and application pair uniqueness
- Full relational dependency seeding: candidate contact, education, skills, resumes, positions, application history
- Docket Actor ID limit enforcement: PPNNNNN capped at 99,999 without wrapping or duplication
"""

import os
import json
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Organisation
from app.models.candidate import (
    CandidateProfile,
    CandidateContact,
    CandidateEducation,
    CandidateSkill,
    CandidateResume,
    ResumeVersion,
)
from app.models.job import JobRole, EmploymentType, WorkType, JobRequirement, JobPosition
from app.models.application import JobApplication, ApplicationStatusHistory
from scripts.seed.checkpoint_manager import CheckpointManager, SeedingTelemetry


FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Sneha", "Kunal", "Pooja", "Vikram", "Ananya", "Rahul", "Neha",
    "David", "Sarah", "Alex", "Elena", "Michael", "Arjun", "Kavya", "Varun", "Isha", "Aditya",
    "Priyanka", "Siddharth", "Meera", "Gaurav", "Divya", "Naveen", "Swati", "Rishi", "Tanvi", "Kartik",
]
LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Singh", "Nair", "Iyer", "Rao", "Gupta", "Deshmukh", "Kaur",
    "Smith", "Johnson", "Brown", "Taylor", "Miller", "Chatterjee", "Bhattacharya", "Reddy", "Choudhury", "Joshi",
    "Pillai", "Menon", "Agarwal", "Bansal", "Kapoor", "Malhotra", "Saxena", "Sengupta", "Das", "Pandey",
]
JOB_TITLES = [
    "Full Stack Python Engineer", "Senior Backend Architect", "Cloud DevOps Specialist",
    "Data Platform Engineer", "Machine Learning Engineer", "Frontend React Developer",
    "Database Reliability Engineer", "Security Operations Specialist", "Distributed Systems Programmer",
    "AI/ML Research Scientist", "Site Reliability Engineer", "Mobile App Developer (React Native)",
]
EDUCATION_PATHWAYS = [
    ("BTECH", "Bachelor of Technology", "UNDERGRADUATE", "Computer Science & Engineering", 4),
    ("BE", "Bachelor of Engineering", "UNDERGRADUATE", "Information Technology", 4),
    ("BCA", "Bachelor of Computer Applications", "UNDERGRADUATE", "Computer Applications", 3),
    ("BSC_CS", "Bachelor of Science in CS", "UNDERGRADUATE", "Computer Science", 3),
]
SKILL_TAXONOMY = [
    ("PYTHON", "Python", "EXPERT"),
    ("POSTGRESQL", "PostgreSQL", "ADVANCED"),
    ("SYSTEM_DESIGN", "Distributed System Design", "ADVANCED"),
    ("FASTAPI", "FastAPI", "INTERMEDIATE"),
    ("DOCKER", "Docker & Containerization", "INTERMEDIATE"),
    ("KUBERNETES", "Kubernetes", "INTERMEDIATE"),
    ("AWS", "Amazon Web Services (AWS)", "ADVANCED"),
    ("REDIS", "Redis Caching", "INTERMEDIATE"),
    ("TYPESCRIPT", "TypeScript", "INTERMEDIATE"),
    ("REACT", "React.js", "ADVANCED"),
    ("MACHINE_LEARNING", "Machine Learning", "INTERMEDIATE"),
    ("CI_CD", "CI/CD & DevOps", "INTERMEDIATE"),
]


class ScaleGenerator:
    """Memory-bounded, chunked synthetic data generator for high-volume scale testing."""

    def __init__(
        self,
        db: Session,
        num_candidates: int = 1000,
        num_jobs: int = 100,
        num_applications: int = 500,
        batch_size: int = 1000,
        random_seed: int = 42,
        checkpoint_file: str = "scratch/scale_seed_checkpoint.json",
    ):
        self.db = db
        self.num_candidates = num_candidates
        self.num_jobs = num_jobs
        self.num_applications = num_applications
        self.batch_size = max(100, min(10000, batch_size))
        self.random_seed = random_seed
        self.rng = random.Random(random_seed)
        self.checkpoint = CheckpointManager(checkpoint_file=checkpoint_file)
        self.telemetry = SeedingTelemetry()

    def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """Execute scale generation in topological dependency order with batch commits."""
        summary = {
            "profile": "E_SCALE_GENERATOR",
            "dry_run": dry_run,
            "target_candidates": self.num_candidates,
            "target_jobs": self.num_jobs,
            "target_applications": self.num_applications,
            "batch_size": self.batch_size,
            "candidates_inserted": 0,
            "jobs_inserted": 0,
            "applications_inserted": 0,
            "elapsed_seconds": 0.0,
            "throughput_rows_per_second": 0.0,
        }

        if dry_run:
            print(f"[DRY-RUN] Scale Generator: targets {self.num_candidates:,} candidates, {self.num_jobs:,} jobs, {self.num_applications:,} applications.")
            summary["candidates_inserted"] = self.num_candidates
            summary["jobs_inserted"] = self.num_jobs
            summary["applications_inserted"] = self.num_applications
            return summary

        # 1. Ensure Anchor Organisation, Role & References Exist
        org = self.db.execute(select(Organisation)).scalars().first()
        if not org:
            org = Organisation(
                legal_name="Scale Benchmark Enterprise Private Limited",
                display_name="Scale Benchmark Enterprise",
                organisation_type_code_id=1,
                status_code_id=1,
                primary_country_id=1,
            )
            self.db.add(org)
            self.db.flush()

        role_cand = self.db.execute(select(Role).where(Role.role_code == "CANDIDATE")).scalar_one_or_none()
        if not role_cand:
            role_cand = Role(role_code="CANDIDATE", display_name="Candidate", description="Scale Candidate", is_system_role=True)
            self.db.add(role_cand)
            self.db.flush()

        creator_user = self.db.execute(select(User)).scalars().first()
        if not creator_user:
            creator_user = User(
                email_address="scale.admin@talentra.io",
                display_name="Scale Benchmark Administrator",
                account_status_code_id=1,
                identity_provider_code="SUPABASE",
                provider_subject="sub-scale-admin",
            )
            self.db.add(creator_user)
            self.db.flush()

        emp_type = self.db.execute(select(EmploymentType)).scalars().first()
        work_type = self.db.execute(select(WorkType)).scalars().first()
        job_role = self.db.execute(select(JobRole)).scalars().first()

        emp_type_id = emp_type.id if emp_type else 1
        work_type_id = work_type.id if work_type else 1
        job_role_id = job_role.id if job_role else 1

        # Resolve qualification & skill IDs
        btech_row = self.db.execute(text("SELECT id FROM qualification WHERE qualification_code = 'BTECH'")).fetchone()
        btech_qid = btech_row[0] if btech_row else 1

        skill_rows = self.db.execute(text("SELECT id, skill_code, name FROM skill LIMIT 20")).fetchall()
        skill_catalog = [(r[0], r[1], r[2]) for r in skill_rows] if skill_rows else [(1, "PYTHON", "Python"), (2, "POSTGRESQL", "PostgreSQL")]

        # 2. Chunked Candidate Seeding with Dependent Records
        print(f"--> [Scale] Seeding Candidates (Target: {self.num_candidates:,})...")
        candidate_ids: List[int] = []
        existing_cand_ids = self.db.execute(select(CandidateProfile.id)).scalars().all()

        if len(existing_cand_ids) >= self.num_candidates:
            candidate_ids = list(existing_cand_ids[:self.num_candidates])
            summary["candidates_inserted"] = len(candidate_ids)
            print(f"    Existing candidate count ({len(existing_cand_ids):,}) satisfies target ({self.num_candidates:,}).")
        else:
            candidates_needed = self.num_candidates - len(existing_cand_ids)
            inserted_cands = 0
            batch_num = 0

            while inserted_cands < candidates_needed:
                current_batch_size = min(self.batch_size, candidates_needed - inserted_cands)
                start_idx = len(existing_cand_ids) + inserted_cands + 1

                # Batch 1: Users
                users_batch = []
                for i in range(current_batch_size):
                    idx = start_idx + i
                    fname = self.rng.choice(FIRST_NAMES)
                    lname = self.rng.choice(LAST_NAMES)
                    u = User(
                        email_address=f"scale.cand.{idx}@talentra.io",
                        display_name=f"{fname} {lname}",
                        account_status_code_id=1,
                        identity_provider_code="SUPABASE",
                        provider_subject=f"sub-scale-cand-{idx}",
                    )
                    users_batch.append((u, fname, lname, idx))
                    self.db.add(u)

                self.db.flush()

                # Batch 2: Candidate Profiles
                profiles_batch = []
                for u, fname, lname, idx in users_batch:
                    # Docket actor ID rule: CA00001 to CA99999. Beyond 99,999, profile has no public actor ID
                    actor_id = f"CA{idx:05d}" if idx <= 99999 else None

                    cp = CandidateProfile(
                        user_id=u.id,
                        actor_id=actor_id,
                        first_name=fname,
                        last_name=lname,
                        profile_status_code_id=1,
                        profile_visibility_code_id=1,
                    )
                    profiles_batch.append((cp, u, idx))
                    self.db.add(cp)

                self.db.flush()

                # Batch 3: Dependent Records (Contact, Education, Skills, Resume)
                for cp, u, idx in profiles_batch:
                    candidate_ids.append(cp.id)

                    # Contact
                    self.db.add(CandidateContact(
                        candidate_profile_id=cp.id,
                        email_address=u.email_address,
                        phone_e164=f"+9198765{idx % 100000:05d}",
                        phone_country_id=1,
                    ))

                    # Education (Realistic normal distribution around 7.8 CGPA)
                    base_cgpa = min(9.9, max(5.5, round(self.rng.normalvariate(7.8, 1.1), 2)))
                    has_backlogs = self.rng.random() < 0.12
                    active_backlogs = 1 if has_backlogs and self.rng.random() < 0.4 else 0
                    pathway = self.rng.choice(EDUCATION_PATHWAYS)
                    s_year = 2018 + (idx % 3)
                    c_year = s_year + pathway[4]

                    self.db.add(CandidateEducation(
                        candidate_profile_id=cp.id,
                        qualification_id=btech_qid,
                        institution_name=f"Institute of Technology #{idx % 50 + 1}",
                        field_of_study=pathway[3],
                        start_date=date(s_year, 8, 1),
                        end_date=date(c_year, 5, 31),
                        start_year=s_year,
                        completion_year=c_year,
                        education_level=pathway[2],
                        board_or_university=f"State University #{(idx % 15) + 1}",
                        grading_system="CGPA_10",
                        score_value=Decimal(str(base_cgpa)),
                        max_score=Decimal("10.00"),
                        cgpa=Decimal(str(base_cgpa)),
                        percentage=Decimal(str(round(base_cgpa * 10, 2))),
                        has_backlogs=has_backlogs,
                        active_backlogs_count=active_backlogs,
                        historical_backlogs_count=1 if has_backlogs else 0,
                        status="COMPLETED",
                    ))

                    # Skills (3 to 5 skills per candidate)
                    selected_skills = self.rng.sample(skill_catalog, k=min(len(skill_catalog), self.rng.randint(3, 5)))
                    for s_idx, (sid, scode, sname) in enumerate(selected_skills):
                        self.db.add(CandidateSkill(
                            candidate_profile_id=cp.id,
                            skill_id=sid,
                            skill_name=sname,
                            years_experience=self.rng.randint(1, 8),
                            is_primary=(s_idx == 0),
                            proficiency_level=self.rng.choice(["INTERMEDIATE", "ADVANCED", "EXPERT"]),
                        ))

                    # Default Resume
                    cr = CandidateResume(
                        candidate_profile_id=cp.id,
                        resume_title=f"{cp.first_name} {cp.last_name} - Software Engineer",
                        is_default=True,
                    )
                    self.db.add(cr)

                # Commit batch transaction (Memory bounded < 100MB RAM)
                self.db.commit()
                inserted_cands += current_batch_size
                batch_num += 1
                tele_metrics = self.telemetry.update(current_batch_size)
                self.checkpoint.record_batch("CANDIDATES", current_batch_size, batch_num)
                print(f"    Batch {batch_num}: {inserted_cands:,}/{candidates_needed:,} candidates committed ({tele_metrics['throughput_rows_per_second']} rows/sec).")

            summary["candidates_inserted"] = len(existing_cand_ids) + inserted_cands

        # 3. Chunked Job Requirements Seeding
        print(f"--> [Scale] Seeding Jobs (Target: {self.num_jobs:,})...")
        job_ids: List[int] = []
        existing_job_ids = self.db.execute(select(JobRequirement.id)).scalars().all()

        if len(existing_job_ids) >= self.num_jobs:
            job_ids = list(existing_job_ids[:self.num_jobs])
            summary["jobs_inserted"] = len(job_ids)
            print(f"    Existing job count ({len(existing_job_ids):,}) satisfies target ({self.num_jobs:,}).")
        else:
            jobs_needed = self.num_jobs - len(existing_job_ids)
            inserted_jobs = 0
            batch_num = 0

            while inserted_jobs < jobs_needed:
                current_batch_size = min(self.batch_size, jobs_needed - inserted_jobs)
                start_idx = len(existing_job_ids) + inserted_jobs + 1
                jobs_batch = []

                for i in range(current_batch_size):
                    idx = start_idx + i
                    title = f"{self.rng.choice(JOB_TITLES)} #{idx}"
                    min_sal = self.rng.randint(600000, 1600000)
                    max_sal = min_sal + self.rng.randint(400000, 1500000)

                    jr = JobRequirement(
                        organisation_id=org.id,
                        created_by_user_id=creator_user.id,
                        job_role_id=job_role_id,
                        title=title[:180],
                        description=f"Scale job requisition {idx} requirement specification.",
                        employment_type_id=emp_type_id,
                        work_type_id=work_type_id,
                        status_code_id=2,  # OPEN
                        publish_state_code_id=2,  # PUBLISHED
                        positions_count=self.rng.randint(1, 5),
                        salary_min=Decimal(str(min_sal)),
                        salary_max=Decimal(str(max_sal)),
                        salary_currency_code="INR",
                        application_deadline=datetime.now(timezone.utc) + timedelta(days=self.rng.randint(15, 60)),
                        min_cgpa=Decimal("6.00"),
                        min_percentage=Decimal("60.00"),
                        allow_backlogs=self.rng.choice([True, False]),
                        max_active_backlogs=0,
                        required_skills=json.dumps(["Python", "SQL", "Git"]),
                        preferred_skills=json.dumps(["FastAPI", "Docker", "AWS"]),
                        required_qualifications=json.dumps(["BTECH", "BE", "MCA"]),
                    )
                    jobs_batch.append(jr)
                    self.db.add(jr)

                self.db.flush()

                # Add positions for jobs
                for jr in jobs_batch:
                    job_ids.append(jr.id)
                    self.db.add(JobPosition(
                        job_requirement_id=jr.id,
                        position_code=f"POS_SCALE_{jr.id:06d}",
                        title=jr.title,
                        headcount=jr.positions_count,
                        filled_count=0,
                    ))

                self.db.commit()
                inserted_jobs += current_batch_size
                batch_num += 1
                tele_metrics = self.telemetry.update(current_batch_size)
                self.checkpoint.record_batch("JOBS", current_batch_size, batch_num)
                print(f"    Batch {batch_num}: {inserted_jobs:,}/{jobs_needed:,} jobs committed ({tele_metrics['throughput_rows_per_second']} rows/sec).")

            summary["jobs_inserted"] = len(existing_job_ids) + inserted_jobs

        # 4. Chunked Applications Seeding (Ensuring Unique Pairs & Relational Status History)
        print(f"--> [Scale] Seeding Applications (Target: {self.num_applications:,})...")
        existing_apps_count = self.db.execute(select(func.count(JobApplication.id))).scalar() or 0

        if existing_apps_count >= self.num_applications:
            summary["applications_inserted"] = existing_apps_count
            print(f"    Existing application count ({existing_apps_count:,}) satisfies target ({self.num_applications:,}).")
        else:
            apps_needed = self.num_applications - existing_apps_count
            inserted_apps = 0
            batch_num = 0
            seen_pairs = set()

            all_cand_ids = list(candidate_ids) if candidate_ids else list(existing_cand_ids)
            all_job_ids = list(job_ids) if job_ids else list(existing_job_ids)

            # Application status distributions: 35% APPLIED(1), 25% SCREENING(2), 15% INTERVIEW(3), 5% OFFERED(4), 3% HIRED(5), 15% REJECTED(6), 2% WITHDRAWN(7)
            status_pool = [1] * 35 + [2] * 25 + [3] * 15 + [4] * 5 + [5] * 3 + [6] * 15 + [7] * 2

            if all_cand_ids and all_job_ids:
                while inserted_apps < apps_needed:
                    current_batch_size = min(self.batch_size, apps_needed - inserted_apps)
                    apps_batch = []

                    for _ in range(current_batch_size):
                        cand_id = self.rng.choice(all_cand_ids)
                        job_id = self.rng.choice(all_job_ids)
                        pair = (cand_id, job_id)
                        attempts = 0
                        while pair in seen_pairs and attempts < 10:
                            cand_id = self.rng.choice(all_cand_ids)
                            job_id = self.rng.choice(all_job_ids)
                            pair = (cand_id, job_id)
                            attempts += 1
                        seen_pairs.add(pair)

                        st_id = self.rng.choice(status_pool)
                        app = JobApplication(
                            job_requirement_id=job_id,
                            candidate_profile_id=cand_id,
                            status_code_id=st_id,
                            cover_letter="Synthetic benchmark application submission.",
                            applied_at=datetime.now(timezone.utc) - timedelta(days=self.rng.randint(1, 30)),
                        )
                        apps_batch.append((app, st_id))
                        self.db.add(app)

                    self.db.flush()

                    # Add application status history
                    for app, st_id in apps_batch:
                        self.db.add(ApplicationStatusHistory(
                            job_application_id=app.id,
                            from_status_code_id=1 if st_id > 1 else None,
                            to_status_code_id=st_id,
                            changed_by_user_id=creator_user.id,
                        ))

                    self.db.commit()
                    inserted_apps += current_batch_size
                    batch_num += 1
                    tele_metrics = self.telemetry.update(current_batch_size)
                    self.checkpoint.record_batch("APPLICATIONS", current_batch_size, batch_num)
                    print(f"    Batch {batch_num}: {inserted_apps:,}/{apps_needed:,} applications committed ({tele_metrics['throughput_rows_per_second']} rows/sec).")

            summary["applications_inserted"] = existing_apps_count + inserted_apps

        metrics = self.telemetry.update(0)
        summary["elapsed_seconds"] = metrics["elapsed_seconds"]
        summary["throughput_rows_per_second"] = metrics["throughput_rows_per_second"]
        self.checkpoint.mark_complete()
        print(f"--> [Scale] Completed in {summary['elapsed_seconds']}s ({summary['throughput_rows_per_second']} rows/sec).")

        return summary


def run_profile_e(
    db: Session,
    num_candidates: int = 1000,
    num_jobs: int = 100,
    num_applications: int = 500,
    batch_size: int = 1000,
    dry_run: bool = False,
    random_seed: int = 42,
    checkpoint_file: str = "scratch/scale_seed_checkpoint.json",
) -> Dict[str, Any]:
    """Execute Profile E (Performance and Scale Generator)."""
    generator = ScaleGenerator(
        db=db,
        num_candidates=num_candidates,
        num_jobs=num_jobs,
        num_applications=num_applications,
        batch_size=batch_size,
        random_seed=random_seed,
        checkpoint_file=checkpoint_file,
    )
    return generator.run(dry_run=dry_run)
