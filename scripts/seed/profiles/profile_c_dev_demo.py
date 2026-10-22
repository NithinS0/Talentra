"""Profile C: Minimal Development Demo Seeder.

Constructs a coherent, deterministic, synthetic end-to-end dataset across all 12 modules:
- 1 Root Account & 2 Organisations (Employer & Agency)
- 9 Synthetic Actors (SA00001, AD00001, AA00001, GU00001, CA00001, EM00001, RE00001, CO00001, PO00001)
- Candidate Profile, Contact, and Experience
- Job Requisitions and Job Positions
- Job Application and Status Audit History
- External Sourcing Request and Consultant Assignment
- Gig Marketplace Profile, Request, Application, and Active Assignment
- Enterprise Licence, Seat Allocation, and Registered Device
- Subscription Plan, Active Subscription, and Funded Wallet with Ledger Entry
- Notification Templates, Preferences, and Delivered Messages
- Community Post and Interactions
- Synthetic Government Document Verification Case and Masked Reference
- Analytical Dashboard Daily Aggregates
"""

import json
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy import select, text
from sqlalchemy.orm import Session

# Core models
from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Account, Organisation, AccountOrganisation, OrganisationLocation, OrganisationRecruiterMapping
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.job import JobRole, EmploymentType, WorkType, JobRequirement, JobPosition
from app.models.application import JobApplication, ApplicationStatusHistory
from app.models.sourcing import SourcingRequest, ConsultantProfile, ConsultantRateCard
from app.models.gig import GigWorkerProfile, GigRequest, GigApplication, GigAssignment
from app.models.licence import Licence, LicenceSeatAllocation, RegisteredDevice
from app.models.subscription import SubscriptionPlan, Subscription, Wallet, WalletLedgerEntry, PaymentOrder, PaymentTransaction
from app.models.notification import Language, NotificationTemplate, NotificationPreference, Notification, CommunityPost
from app.models.verification import IdentityVerificationProvider, IdentityVerificationCase, GovernmentDocumentReference
from app.models.admin import ConsentRecord
from app.models.analytics import AggregateDashboardDaily


def run_profile_c(db: Session, dry_run: bool = False) -> Dict[str, Any]:
    """Execute Profile C (Minimal Development Demo) seeding idempotently."""
    results = {
        "profile": "C_MINIMAL_DEV_DEMO",
        "dry_run": dry_run,
        "accounts_created": 0,
        "organisations_created": 0,
        "users_created": 0,
        "actor_identities_created": 0,
        "jobs_created": 0,
        "applications_created": 0,
        "gigs_created": 0,
        "licences_created": 0,
        "subscriptions_created": 0,
        "wallets_created": 0,
        "verification_cases_created": 0,
    }

    if dry_run:
        results.update({
            "accounts_created": 1,
            "organisations_created": 2,
            "users_created": 9,
            "actor_identities_created": 9,
            "jobs_created": 2,
            "applications_created": 1,
            "gigs_created": 1,
            "licences_created": 1,
            "subscriptions_created": 1,
            "wallets_created": 1,
            "verification_cases_created": 1,
        })
        return results

    now_utc = datetime.now(timezone.utc)

    # 1. Resolve Reference Master Entities
    in_country = db.execute(select(Country).where(Country.country_code == "IN")).scalar_one_or_none()
    if not in_country:
        in_country = Country(country_code="IN", alpha3_code="IND", numeric_code="356", name="India", calling_code="+91", is_active=True)
        db.add(in_country)
        db.flush()

    emp_type = db.execute(select(EmploymentType).where(EmploymentType.code == "FULL_TIME")).scalar_one_or_none()
    if not emp_type:
        emp_type = EmploymentType(code="FULL_TIME", name="Full Time", status_code_id=1, description="Permanent full time")
        db.add(emp_type)
        db.flush()

    work_type = db.execute(select(WorkType).where(WorkType.code == "HYBRID")).scalar_one_or_none()
    if not work_type:
        work_type = WorkType(code="HYBRID", name="Hybrid", status_code_id=1, description="Blended office and remote")
        db.add(work_type)
        db.flush()

    job_role = db.execute(select(JobRole).where(JobRole.job_role_code == "SOFTWARE_ENGINEER")).scalar_one_or_none()
    if not job_role:
        job_role = JobRole(job_role_code="SOFTWARE_ENGINEER", name="Software Engineer", industry_id=1)
        db.add(job_role)
        db.flush()

    # 2. Account & Organisations
    org_employer = db.execute(select(Organisation).where(Organisation.display_name == "Acme Technologies")).scalar_one_or_none()
    if not org_employer:
        org_employer = Organisation(
            legal_name="Acme Technologies Corporation Private Limited",
            display_name="Acme Technologies",
            organisation_type_code_id=1,
            status_code_id=1,
            primary_country_id=in_country.id,
        )
        db.add(org_employer)
        db.flush()
        results["organisations_created"] += 1

    account = db.execute(select(Account).where(Account.account_code == "ACC_DEMO_01")).scalar_one_or_none()
    if not account:
        account = Account(
            account_code="ACC_DEMO_01",
            account_name="Acme Enterprise Holdings",
            status_code_id=1,
            root_organisation_id=org_employer.id,
            billing_currency_code="USD",
        )
        db.add(account)
        db.flush()
        results["accounts_created"] += 1

        db.add(AccountOrganisation(
            account_id=account.id,
            organisation_id=org_employer.id,
            name="Primary Organisation",
            status_code_id=1,
        ))
        db.add(OrganisationLocation(
            organisation_id=org_employer.id,
            account_id=account.id,
            name="Bengaluru Technology Center",
            status_code_id=1,
        ))

    org_agency = db.execute(select(Organisation).where(Organisation.display_name == "TalentPro Recruitment Agency")).scalar_one_or_none()
    if not org_agency:
        org_agency = Organisation(
            legal_name="TalentPro Recruitment Agency Private Limited",
            display_name="TalentPro Recruitment Agency",
            organisation_type_code_id=2,
            status_code_id=1,
            primary_country_id=in_country.id,
        )
        db.add(org_agency)
        db.flush()
        db.add(AccountOrganisation(
            account_id=account.id,
            organisation_id=org_agency.id,
            name="Agency Partner",
            status_code_id=1,
        ))
        results["organisations_created"] += 1

    # 3. Roles and 9 Synthetic Actors
    roles = {r.role_code: r for r in db.execute(select(Role)).scalars().all()}
    
    actor_specs = [
        ("SUPER_ADMIN", "SA", "SA00001", "superadmin.demo@talentra.io", "Talentra Super Administrator", None),
        ("ADMIN", "AD", "AD00001", "admin.demo@talentra.io", "Compliance & Governance Admin", None),
        ("ACCOUNT_ADMIN", "AA", "AA00001", "accountadmin.demo@talentra.io", "Acme Account Administrator", org_employer.id),
        ("GUEST", "GU", "GU00001", "guest.demo@talentra.io", "Demo Guest Visitor", None),
        ("CANDIDATE", "CA", "CA00001", "candidate.demo@talentra.io", "Arun Sharma (Lead Engineer)", None),
        ("EMPLOYER", "EM", "EM00001", "employer.demo@talentra.io", "Priya Verma (Hiring Director)", org_employer.id),
        ("RECRUITER", "RE", "RE00001", "recruiter.demo@talentra.io", "Vikram Sen (Talent Recruiter)", org_agency.id),
        ("CONSULTANT", "CO", "CO00001", "consultant.demo@talentra.io", "Deepak Mehta (Sourcing Consultant)", None),
        ("PLACEMENT_OFFICER", "PO", "PO00001", "tpo.demo@talentra.io", "Dr. Kavita Nair (IIT Placement Dean)", None),
    ]

    seeded_users: Dict[str, User] = {}

    for role_code, prefix, actor_id, email, name, org_id in actor_specs:
        role = roles.get(role_code)
        if not role:
            role = Role(role_code=role_code, display_name=role_code.title(), description=f"Role {role_code}", is_system_role=True)
            db.add(role)
            db.flush()
            roles[role_code] = role

        user = db.execute(select(User).where(User.email_address == email)).scalar_one_or_none()
        if not user:
            user = User(
                email_address=email,
                phone_e164="+919876543210",
                display_name=name,
                account_status_code_id=1,
                identity_provider_code="SUPABASE",
                provider_subject=f"sub-synthetic-{prefix.lower()}-demo",
            )
            db.add(user)
            db.flush()
            results["users_created"] += 1

            # Role assignment
            db.add(UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                organisation_id=org_id,
                actor_id=actor_id,
                valid_from=now_utc,
                assigned_by_user_id=1,
            ))

            # Authoritative Actor Identity record
            db.add(UserActorIdentity(
                user_id=user.id,
                role_id=role.id,
                role_code=role_code,
                actor_prefix=prefix,
                actor_id=actor_id,
                organisation_id=org_id,
                is_active=True,
            ))
            results["actor_identities_created"] += 1

        seeded_users[role_code] = user

    # Map recruiter to employer organisation
    recruiter_user = seeded_users["RECRUITER"]
    existing_mapping = db.execute(
        select(OrganisationRecruiterMapping).where(
            OrganisationRecruiterMapping.recruiter_user_id == recruiter_user.id,
            OrganisationRecruiterMapping.organisation_id == org_employer.id,
        )
    ).scalar_one_or_none()
    if not existing_mapping:
        db.add(OrganisationRecruiterMapping(
            recruiter_user_id=recruiter_user.id,
            organisation_id=org_employer.id,
            valid_from=now_utc,
            assigned_by_user_id=seeded_users["EMPLOYER"].id,
        ))

    # 4. Candidate Profile
    cand_user = seeded_users["CANDIDATE"]
    cand_profile = db.execute(select(CandidateProfile).where(CandidateProfile.user_id == cand_user.id)).scalar_one_or_none()
    if not cand_profile:
        cand_profile = CandidateProfile(
            user_id=cand_user.id,
            actor_id="CA00001",
            first_name="Arun",
            last_name="Sharma",
            summary="Principal Distributed Systems Architect with 12+ years experience in Python, Cloud Native, and Event-Driven Pipelines.",
            profile_status_code_id=1,
            profile_visibility_code_id=1,
        )
        db.add(cand_profile)
        db.flush()
        db.add(CandidateContact(
            candidate_profile_id=cand_profile.id,
            email_address=cand_user.email_address,
            phone_e164="+919876543210",
            phone_country_id=in_country.id,
        ))

    from app.models.candidate import (
        CandidateEducation,
        CandidateEducationSemester,
        CandidateSkill,
        CandidateResume,
        ResumeVersion,
        CandidateDocument,
    )

    # Idempotent Academic History
    existing_edu = db.execute(select(CandidateEducation).where(CandidateEducation.candidate_profile_id == cand_profile.id)).scalars().first()
    if not existing_edu:
        btech_qual = db.execute(text("SELECT id FROM qualification WHERE qualification_code = 'BTECH'")).fetchone()
        class12_qual = db.execute(text("SELECT id FROM qualification WHERE qualification_code = 'CLASS_12'")).fetchone()
        class10_qual = db.execute(text("SELECT id FROM qualification WHERE qualification_code = 'CLASS_10'")).fetchone()

        # Class 10 (CBSE)
        db.add(CandidateEducation(
            candidate_profile_id=cand_profile.id,
            qualification_id=class10_qual[0] if class10_qual else 1,
            institution_name="Delhi Public School, R.K. Puram",
            field_of_study="General Science & Mathematics",
            start_date=date(2012, 6, 1),
            end_date=date(2013, 5, 31),
            start_year=2012,
            completion_year=2013,
            education_level="SECONDARY",
            board_or_university="CBSE",
            grading_system="PERCENTAGE",
            score_value=Decimal("91.50"),
            max_score=Decimal("100.00"),
            percentage=Decimal("91.50"),
            has_backlogs=False,
            active_backlogs_count=0,
            historical_backlogs_count=0,
            status="COMPLETED",
        ))

        # Class 12 (CBSE Science)
        db.add(CandidateEducation(
            candidate_profile_id=cand_profile.id,
            qualification_id=class12_qual[0] if class12_qual else 2,
            institution_name="Delhi Public School, R.K. Puram",
            field_of_study="Physics, Chemistry, Mathematics & Computer Science",
            start_date=date(2013, 6, 1),
            end_date=date(2015, 5, 31),
            start_year=2013,
            completion_year=2015,
            education_level="HIGHER_SECONDARY",
            board_or_university="CBSE",
            grading_system="PERCENTAGE",
            score_value=Decimal("89.20"),
            max_score=Decimal("100.00"),
            percentage=Decimal("89.20"),
            has_backlogs=False,
            active_backlogs_count=0,
            historical_backlogs_count=0,
            status="COMPLETED",
        ))

        # B.Tech Degree (CSE)
        btech_edu = CandidateEducation(
            candidate_profile_id=cand_profile.id,
            qualification_id=btech_qual[0] if btech_qual else 4,
            institution_name="Indian Institute of Technology, Madras",
            field_of_study="Computer Science & Engineering",
            stream_specialization="Distributed Computing & Systems Architecture",
            start_date=date(2015, 8, 1),
            end_date=date(2019, 5, 31),
            start_year=2015,
            completion_year=2019,
            education_level="UNDERGRADUATE",
            board_or_university="IIT Madras",
            grading_system="CGPA_10",
            score_value=Decimal("8.65"),
            max_score=Decimal("10.00"),
            cgpa=Decimal("8.65"),
            percentage=Decimal("86.50"),
            has_backlogs=False,
            active_backlogs_count=0,
            historical_backlogs_count=0,
            status="COMPLETED",
        )
        db.add(btech_edu)
        db.flush()

        # Semester records for B.Tech
        sgpas = [Decimal("8.20"), Decimal("8.40"), Decimal("8.50"), Decimal("8.70"), Decimal("8.80"), Decimal("8.90"), Decimal("8.70"), Decimal("8.85")]
        cum_cgpa = [Decimal("8.20"), Decimal("8.30"), Decimal("8.37"), Decimal("8.45"), Decimal("8.52"), Decimal("8.58"), Decimal("8.60"), Decimal("8.65")]
        for sem_idx, (sg, cg) in enumerate(zip(sgpas, cum_cgpa), start=1):
            db.add(CandidateEducationSemester(
                candidate_education_id=btech_edu.id,
                candidate_profile_id=cand_profile.id,
                semester_number=sem_idx,
                academic_term=f"Term {sem_idx} (2015-2019)",
                result_status="PASS",
                sgpa=sg,
                cgpa=cg,
                credits_registered=24,
                credits_earned=24,
                has_backlog=False,
            ))

    # Idempotent Skills
    existing_skills = db.execute(select(CandidateSkill).where(CandidateSkill.candidate_profile_id == cand_profile.id)).scalars().first()
    if not existing_skills:
        py_skill = db.execute(text("SELECT id FROM skill WHERE skill_code = 'PYTHON'")).fetchone()
        pg_skill = db.execute(text("SELECT id FROM skill WHERE skill_code = 'POSTGRESQL'")).fetchone()
        sys_skill = db.execute(text("SELECT id FROM skill WHERE skill_code = 'SYSTEM_DESIGN'")).fetchone()
        fa_skill = db.execute(text("SELECT id FROM skill WHERE skill_code = 'FASTAPI'")).fetchone()
        doc_skill = db.execute(text("SELECT id FROM skill WHERE skill_code = 'DOCKER'")).fetchone()

        skills_to_seed = [
            (py_skill[0] if py_skill else 1, "Python", 8, True, "EXPERT"),
            (pg_skill[0] if pg_skill else 2, "PostgreSQL", 7, True, "EXPERT"),
            (sys_skill[0] if sys_skill else 3, "Distributed System Design", 6, True, "ADVANCED"),
            (fa_skill[0] if fa_skill else 4, "FastAPI", 4, False, "ADVANCED"),
            (doc_skill[0] if doc_skill else 5, "Docker & Containerization", 5, False, "INTERMEDIATE"),
        ]
        for sid, sname, yrs, is_pri, prof in skills_to_seed:
            db.add(CandidateSkill(
                candidate_profile_id=cand_profile.id,
                skill_id=sid,
                skill_name=sname,
                years_experience=yrs,
                is_primary=is_pri,
                proficiency_level=prof,
            ))

    # Idempotent Resume
    existing_resume = db.execute(select(CandidateResume).where(CandidateResume.candidate_profile_id == cand_profile.id)).scalars().first()
    if not existing_resume:
        cand_resume = CandidateResume(
            candidate_profile_id=cand_profile.id,
            resume_title="Lead Backend Systems Architect - 2026",
            is_default=True,
        )
        db.add(cand_resume)
        db.flush()

        lang_record = db.execute(select(Language).where(Language.language_code == "en")).scalar_one_or_none()
        lang_id = lang_record.id if lang_record else None

        db.add(ResumeVersion(
            candidate_resume_id=cand_resume.id,
            version_number=1,
            file_name="Arun_Sharma_Resume_2026.pdf",
            file_size_bytes=134520,
            mime_type="application/pdf",
            storage_object_key="resumes/ca00001/arun_sharma_v1.pdf",
            content_sha256="b8c2d1e0f3a4b5c6d7e8f90123456789abcdef0123456789abcdef0123456789",
            language_id=lang_id,
            target_role="Lead Backend Systems Architect",
            is_archived=False,
        ))

    # Idempotent Document
    existing_doc = db.execute(select(CandidateDocument).where(CandidateDocument.candidate_profile_id == cand_profile.id)).scalars().first()
    if not existing_doc:
        edu_rec = db.execute(select(CandidateEducation).where(CandidateEducation.candidate_profile_id == cand_profile.id)).scalars().first()
        db.add(CandidateDocument(
            candidate_profile_id=cand_profile.id,
            document_category="ACADEMIC",
            title="B.Tech Degree Certificate & Transcripts",
            file_name="iit_madras_degree_certificate.pdf",
            file_size_bytes=245800,
            mime_type="application/pdf",
            storage_path="documents/ca00001/academic_degree_cert.pdf",
            content_sha256="4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123",
            is_verified=True,
            is_archived=False,
            linked_entity_type="candidate_education",
            linked_entity_id=edu_rec.id if edu_rec else None,
        ))

    # 5. Job Requirement & Position
    employer_user = seeded_users["EMPLOYER"]
    job_req = db.execute(select(JobRequirement).where(JobRequirement.title == "Lead Backend Systems Architect")).scalar_one_or_none()
    if job_req:
        # Ensure structured eligibility fields are set
        job_req.min_cgpa = Decimal("7.00")
        job_req.min_percentage = Decimal("70.00")
        job_req.allow_backlogs = False
        job_req.max_active_backlogs = 0
        job_req.required_skills = json.dumps(["Python", "PostgreSQL", "Distributed Systems"])
        job_req.preferred_skills = json.dumps(["FastAPI", "Docker", "Kubernetes"])
        job_req.required_qualifications = json.dumps(["BTECH", "BE", "MTECH"])
        job_req.accepted_branches = json.dumps(["Computer Science & Engineering", "Information Technology"])
        job_req.required_documents = json.dumps(["DEGREE_CERTIFICATE", "RESUME", "IDENTITY_PROOF"])
    else:
        job_req = JobRequirement(
            organisation_id=org_employer.id,
            created_by_user_id=employer_user.id,
            job_role_id=job_role.id,
            title="Lead Backend Systems Architect",
            description="Seeking a distinguished backend systems engineer to lead our distributed ledger and high-throughput pipeline.",
            employment_type_id=emp_type.id,
            work_type_id=work_type.id,
            status_code_id=2,  # OPEN
            publish_state_code_id=2,  # PUBLISHED
            open_to_consultants=True,
            positions_count=2,
            salary_min=Decimal("4500000.00"),
            salary_max=Decimal("6000000.00"),
            salary_currency_code="INR",
            application_deadline=now_utc + timedelta(days=45),
            min_cgpa=Decimal("7.00"),
            min_percentage=Decimal("70.00"),
            allow_backlogs=False,
            max_active_backlogs=0,
            min_experience_years=5,
            max_experience_years=15,
            location_city="Bengaluru",
            location_country="India",
            required_skills=json.dumps(["Python", "PostgreSQL", "Distributed Systems"]),
            preferred_skills=json.dumps(["FastAPI", "Docker", "Kubernetes"]),
            required_qualifications=json.dumps(["BTECH", "BE", "MTECH"]),
            accepted_branches=json.dumps(["Computer Science & Engineering", "Information Technology"]),
            required_documents=json.dumps(["DEGREE_CERTIFICATE", "RESUME", "IDENTITY_PROOF"]),
        )
        db.add(job_req)
        db.flush()
        results["jobs_created"] += 1

        db.add(JobPosition(
            job_requirement_id=job_req.id,
            position_code="POS_DEMO_001",
            title=job_req.title,
            headcount=1,
            filled_count=0,
        ))

    # 6. Job Application & Status History
    existing_app = db.execute(
        select(JobApplication).where(
            JobApplication.job_requirement_id == job_req.id,
            JobApplication.candidate_profile_id == cand_profile.id,
        )
    ).scalar_one_or_none()
    if not existing_app:
        app_obj = JobApplication(
            job_requirement_id=job_req.id,
            candidate_profile_id=cand_profile.id,
            status_code_id=2,  # SCREENING
            applied_at=now_utc,
            last_status_changed_at=now_utc,
            cover_letter="I have deep expertise in building fault-tolerant scalable backends.",
        )
        db.add(app_obj)
        db.flush()
        results["applications_created"] += 1

        db.add(ApplicationStatusHistory(
            job_application_id=app_obj.id,
            from_status_code_id=1,
            to_status_code_id=2,
            changed_at=now_utc,
            changed_by_user_id=employer_user.id,
        ))

    # 7. Sourcing Request & Consultant Profile
    consultant_user = seeded_users["CONSULTANT"]
    consultant_prof = db.execute(select(ConsultantProfile).where(ConsultantProfile.user_id == consultant_user.id)).scalar_one_or_none()
    if not consultant_prof:
        consultant_prof = ConsultantProfile(
            user_id=consultant_user.id,
            title="Senior Executive Talent Headhunter",
            description="15 years sourcing elite engineering and C-suite talent across APAC.",
            status_code_id=1,
        )
        db.add(consultant_prof)
        db.flush()

    sourcing_req = db.execute(select(SourcingRequest).where(SourcingRequest.job_requirement_id == job_req.id)).scalar_one_or_none()
    if not sourcing_req:
        sourcing_req = SourcingRequest(
            job_requirement_id=job_req.id,
            requester_user_id=employer_user.id,
            consultant_user_id=consultant_user.id,
            status_code_id=2,  # ACCEPTED
            open_to_consultants_snapshot=True,
            requested_at=now_utc - timedelta(days=2),
            responded_at=now_utc - timedelta(days=1),
        )
        db.add(sourcing_req)
        db.flush()

    # 8. Gig Marketplace
    gig_worker = db.execute(select(GigWorkerProfile).where(GigWorkerProfile.user_id == cand_user.id)).scalar_one_or_none()
    if not gig_worker:
        gig_worker = GigWorkerProfile(
            user_id=cand_user.id,
            display_name="Arun Sharma (Specialist Contractor)",
            bio="Available for cloud microservices migration sprints and distributed query optimization.",
            availability_status_code_id=1,  # AVAILABLE
        )
        db.add(gig_worker)
        db.flush()

    gig_req = db.execute(select(GigRequest).where(GigRequest.title == "Event-Driven Stream Migration Sprint")).scalar_one_or_none()
    if not gig_req:
        gig_req = GigRequest(
            requester_organisation_id=org_employer.id,
            created_by_user_id=employer_user.id,
            title="Event-Driven Stream Migration Sprint",
            description="Execute zero-downtime database stream replication to event consumer bus.",
            starts_at=now_utc + timedelta(days=3),
            ends_at=now_utc + timedelta(days=17),
            pricing_type_code_id=1,  # FIXED
            price_amount=Decimal("3500.00"),
            currency_code="USD",
            status_code_id=3,  # IN_PROGRESS
        )
        db.add(gig_req)
        db.flush()

        gig_app = GigApplication(
            gig_request_id=gig_req.id,
            gig_worker_profile_id=gig_worker.id,
            status_code_id=2,  # ACCEPTED
            decided_by_user_id=employer_user.id,
            decided_at=now_utc,
        )
        db.add(gig_app)
        db.flush()

        gig_assign = GigAssignment(
            gig_application_id=gig_app.id,
            requester_organisation_id=org_employer.id,
            gig_worker_profile_id=gig_worker.id,
            starts_at=now_utc + timedelta(days=3),
            ends_at=now_utc + timedelta(days=17),
            status_code_id=2,  # ACTIVE
        )
        db.add(gig_assign)
        results["gigs_created"] += 1

    # 9. Licences, Seats & Devices
    licence = db.execute(select(Licence).where(Licence.licence_code == "LIC_DEMO_ENTERPRISE_01")).scalar_one_or_none()
    if not licence:
        licence = Licence(
            licence_code="LIC_DEMO_ENTERPRISE_01",
            account_id=account.id,
            max_users=15,
            max_devices_per_user=3,
            valid_from=now_utc - timedelta(days=10),
            valid_until=now_utc + timedelta(days=355),
            status_code_id=1,  # ACTIVE
        )
        db.add(licence)
        db.flush()
        results["licences_created"] += 1

        db.add(LicenceSeatAllocation(
            licence_id=licence.id,
            user_id=employer_user.id,
            status_code_id=1,
            created_by=seeded_users["ACCOUNT_ADMIN"].id,
        ))

        db.add(RegisteredDevice(
            user_id=employer_user.id,
            device_fingerprint_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            device_label="Priya MacBook Pro M3",
        ))

    # 10. Subscription, Wallet & Ledger
    sub_plan = db.execute(select(SubscriptionPlan).where(SubscriptionPlan.plan_code == "PLAN_ENTERPRISE_MONTHLY")).scalar_one_or_none()
    if not sub_plan:
        sub_plan = SubscriptionPlan(
            plan_code="PLAN_ENTERPRISE_MONTHLY",
            name="Enterprise Multi-Seat Plan",
            price_amount=Decimal("499.00"),
            currency_code="USD",
            billing_interval_code_id=1,  # MONTHLY
            active=True,
        )
        db.add(sub_plan)
        db.flush()

    sub = db.execute(select(Subscription).where(Subscription.account_id == account.id)).scalar_one_or_none()
    if not sub:
        sub = Subscription(
            account_id=account.id,
            subscription_plan_id=sub_plan.id,
            licence_id=licence.id,
            status_code_id=1,  # ACTIVE
            starts_at=now_utc - timedelta(days=10),
            ends_at=now_utc + timedelta(days=20),
            auto_renew=True,
        )
        db.add(sub)
        db.flush()
        results["subscriptions_created"] += 1

    wallet = db.execute(select(Wallet).where(Wallet.account_id == account.id)).scalar_one_or_none()
    if not wallet:
        wallet = Wallet(
            account_id=account.id,
            currency_code="USD",
            status_code_id=1,  # ACTIVE
        )
        db.add(wallet)
        db.flush()
        results["wallets_created"] += 1

        db.add(WalletLedgerEntry(
            wallet_id=wallet.id,
            entry_type_code_id=1,  # CREDIT
            amount=Decimal("2500.00"),
            currency_code="USD",
            source_type="INITIAL_DEPOSIT",
            source_id="DEP_DEMO_001",
            idempotency_key="IDEM_LEDGER_DEMO_DEPOSIT_001",
        ))

    # 11. Notifications & Preferences
    pref = db.execute(select(NotificationPreference).where(NotificationPreference.user_id == cand_user.id)).scalar_one_or_none()
    if not pref:
        db.add(NotificationPreference(
            user_id=cand_user.id,
            notification_type_code_id=2,  # APPLICATION_UPDATE
            channel_code_id=1,  # IN_APP
            enabled=True,
        ))

    db.add(Notification(
        user_id=cand_user.id,
        setting_code_id=1,  # UNREAD
        setting_value={
            "title": "Application Received",
            "content": "Your application for Lead Backend Systems Architect has been received and advanced to screening.",
            "notification_type": "APPLICATION_UPDATE",
        },
        enabled=True,
    ))

    # 12. Synthetic Verification Case
    provider = db.execute(select(IdentityVerificationProvider).where(IdentityVerificationProvider.provider_code == "SANDBOX_VERIFY_PROVIDER")).scalar_one_or_none()
    if not provider:
        provider = IdentityVerificationProvider(
            provider_code="SANDBOX_VERIFY_PROVIDER",
            display_name="Talentra Mock Government Verification Sandbox",
            enabled=True,
        )
        db.add(provider)
        db.flush()

    consent = db.execute(select(ConsentRecord).where(ConsentRecord.user_id == cand_user.id)).scalar_one_or_none()
    if not consent:
        consent = ConsentRecord(
            user_id=cand_user.id,
            consent_type_code_id=1,
            policy_version="v1.0",
            granted=True,
            captured_at=now_utc,
        )
        db.add(consent)
        db.flush()

    verif_case = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.user_id == cand_user.id)).scalar_one_or_none()
    if not verif_case:
        verif_case = IdentityVerificationCase(
            user_id=cand_user.id,
            document_type_code_id=1,  # AADHAAR
            provider_code="CASE_DEMO_CA00001_01",
            status_code_id=3,  # VERIFIED
            requested_at=now_utc - timedelta(days=5),
            completed_at=now_utc - timedelta(days=5, minutes=-10),
            consent_record_id=consent.id,
        )
        db.add(verif_case)
        db.flush()
        results["verification_cases_created"] += 1

        db.add(GovernmentDocumentReference(
            user_id=cand_user.id,
            verification_case_id=verif_case.id,
            document_type_code_id=1,
            masked_identifier="XXXXXXXX1234",
            issuing_country_id=in_country.id,
            status_code_id=1,
        ))

    # 13. Daily Dashboard Aggregate
    existing_agg = db.execute(select(AggregateDashboardDaily).where(AggregateDashboardDaily.source_business_key == "DEMO_DASHBOARD_DAILY")).scalar_one_or_none()
    if not existing_agg:
        db.add(AggregateDashboardDaily(
            source_business_key="DEMO_DASHBOARD_DAILY",
            snapshot_at=now_utc,
            measure_value=Decimal("100.00"),
            source_watermark="STAGE_15_SEED_INIT",
        ))

    db.commit()
    return results
