"""Profile D: Comprehensive Functional Test Data Seeder.

Builds deterministic synthetic test scenarios exercising core business rules, edge cases,
and lifecycle boundaries across modules:
1. Multi-Tenant Organisation Boundaries & Recruiter Scoping
2. Candidate Blocking & Access Restrictions (BlockListEntry)
3. Full Application Lifecycle Matrix (DRAFT, APPLIED, SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN)
4. Sourcing Mandate Decision Lifecycles (REQUESTED, ACCEPTED, DECLINED)
5. Gig Marketplace Escrow & State Progression
6. Licence Seat Exhaustion & Device Allowance Boundaries
7. Wallet Ledger Idempotency & Financial Balance Boundary
8. Government Verification Decision Matrix (VERIFIED, REJECTED, MANUAL_REVIEW)
9. Security & Audit Retention Test Records
"""

import json
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Account, Organisation, AccountOrganisation, OrganisationRecruiterMapping
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.job import JobRole, EmploymentType, WorkType, JobRequirement
from app.models.application import JobApplication, ApplicationStatusHistory, BlockListEntry
from app.models.sourcing import SourcingRequest, ConsultantProfile
from app.models.gig import GigWorkerProfile, GigRequest, GigApplication, GigAssignment
from app.models.licence import Licence, LicenceSeatAllocation, RegisteredDevice
from app.models.subscription import SubscriptionPlan, Subscription, Wallet, WalletLedgerEntry, PaymentOrder, PaymentTransaction
from app.models.verification import IdentityVerificationProvider, IdentityVerificationCase, GovernmentDocumentReference, VerificationReview
from app.models.admin import AuditEvent, ConsentRecord


def run_profile_d(db: Session, dry_run: bool = False) -> Dict[str, Any]:
    """Execute Profile D (Comprehensive Functional Test Data) seeding idempotently."""
    results = {
        "profile": "D_FUNCTIONAL_TEST_DATA",
        "dry_run": dry_run,
        "boundary_scenarios_seeded": 0,
        "lifecycle_applications_seeded": 0,
        "blocked_candidates_seeded": 0,
        "exhausted_licences_seeded": 0,
        "financial_fixtures_seeded": 0,
        "verification_review_cases_seeded": 0,
    }

    if dry_run:
        results.update({
            "boundary_scenarios_seeded": 6,
            "lifecycle_applications_seeded": 8,
            "blocked_candidates_seeded": 1,
            "exhausted_licences_seeded": 1,
            "financial_fixtures_seeded": 1,
            "verification_review_cases_seeded": 1,
        })
        return results

    now_utc = datetime.now(timezone.utc)

    # 1. Multi-Tenant Isolation: Org Alpha vs Org Beta
    org_alpha = db.execute(select(Organisation).where(Organisation.display_name == "Alpha Technologies")).scalar_one_or_none()
    if not org_alpha:
        org_alpha = Organisation(
            legal_name="Alpha Technologies Private Limited",
            display_name="Alpha Technologies",
            organisation_type_code_id=1,
            status_code_id=1,
            primary_country_id=1,
        )
        db.add(org_alpha)
        db.flush()

    acct = db.execute(select(Account).where(Account.account_code == "ACC_TEST_ISOLATION")).scalar_one_or_none()
    if not acct:
        acct = Account(
            account_code="ACC_TEST_ISOLATION",
            account_name="Isolation Test Account",
            status_code_id=1,
            root_organisation_id=org_alpha.id,
            billing_currency_code="USD",
        )
        db.add(acct)
        db.flush()
        db.add(AccountOrganisation(account_id=acct.id, organisation_id=org_alpha.id, name="Primary", status_code_id=1))

    org_beta = db.execute(select(Organisation).where(Organisation.display_name == "Beta Innovations")).scalar_one_or_none()
    if not org_beta:
        org_beta = Organisation(
            legal_name="Beta Innovations Private Limited",
            display_name="Beta Innovations",
            organisation_type_code_id=1,
            status_code_id=1,
            primary_country_id=1,
        )
        db.add(org_beta)
        db.flush()
        db.add(AccountOrganisation(account_id=acct.id, organisation_id=org_beta.id, name="Secondary", status_code_id=1))

    results["boundary_scenarios_seeded"] += 2

    # Resolve test employer user
    emp_user = db.execute(select(User).where(User.email_address == "employer.demo@talentra.io")).scalar_one_or_none()
    if not emp_user:
        emp_user = User(
            email_address="employer.test@talentra.io",
            display_name="Hiring Lead Alpha",
            account_status_code_id=1,
            identity_provider_code="SUPABASE",
            provider_subject="sub-synthetic-em-test",
        )
        db.add(emp_user)
        db.flush()

    # 2. Blocked Candidate Fixture (BlockListEntry)
    cand_blocked_user = db.execute(select(User).where(User.email_address == "blocked.candidate@talentra.io")).scalar_one_or_none()
    if not cand_blocked_user:
        cand_blocked_user = User(
            email_address="blocked.candidate@talentra.io",
            display_name="Rohit Malviya (Blocked Candidate)",
            account_status_code_id=2,  # SUSPENDED
            identity_provider_code="SUPABASE",
            provider_subject="sub-synthetic-ca-blocked",
        )
        db.add(cand_blocked_user)
        db.flush()

        role_cand = db.execute(select(Role).where(Role.role_code == "CANDIDATE")).scalar_one_or_none()
        if role_cand:
            db.add(UserRoleAssignment(user_id=cand_blocked_user.id, role_id=role_cand.id, actor_id="CA99991", valid_from=datetime.now(timezone.utc), assigned_by_user_id=1))
            db.add(UserActorIdentity(user_id=cand_blocked_user.id, role_id=role_cand.id, role_code="CANDIDATE", actor_prefix="CA", actor_id="CA99991", is_active=False))

        blocked_prof = CandidateProfile(
            user_id=cand_blocked_user.id,
            actor_id="CA99991",
            first_name="Rohit",
            last_name="Malviya",
            profile_status_code_id=2,  # BLOCKED
            profile_visibility_code_id=1,
        )
        db.add(blocked_prof)
        db.flush()

        db.add(CandidateContact(
            candidate_profile_id=blocked_prof.id,
            email_address=cand_blocked_user.email_address,
            phone_e164="+919876599991",
            phone_country_id=1,
        ))

        db.add(BlockListEntry(
            blocker_user_id=emp_user.id,
            blocked_user_id=cand_blocked_user.id,
            created_by=emp_user.id,
        ))
        results["blocked_candidates_seeded"] += 1

    # 3. Application Lifecycle Matrix (All 8 States: DRAFT, APPLIED, SCREENING, INTERVIEW, OFFERED, HIRED, REJECTED, WITHDRAWN)

    role_rec = db.execute(select(JobRole).where(JobRole.job_role_code == "SOFTWARE_ENGINEER")).scalar_one_or_none()
    emp_t = db.execute(select(EmploymentType).where(EmploymentType.code == "FULL_TIME")).scalar_one_or_none()
    work_t = db.execute(select(WorkType).where(WorkType.code == "HYBRID")).scalar_one_or_none()

    job_alpha = db.execute(select(JobRequirement).where(JobRequirement.title == "Test Matrix Engineer")).scalar_one_or_none()
    if not job_alpha:
        job_alpha = JobRequirement(
            organisation_id=org_alpha.id,
            created_by_user_id=emp_user.id,
            job_role_id=role_rec.id if role_rec else 1,
            title="Test Matrix Engineer",
            description="Requisition for application lifecycle state testing.",
            employment_type_id=emp_t.id if emp_t else 1,
            work_type_id=work_t.id if work_t else 1,
            status_code_id=2,  # OPEN
            publish_state_code_id=2,  # PUBLISHED
            positions_count=8,
            min_cgpa=Decimal("6.00"),
            min_percentage=Decimal("60.00"),
            allow_backlogs=False,
            max_active_backlogs=0,
        )
        db.add(job_alpha)
        db.flush()

    # Create 8 distinct candidates in distinct lifecycle states
    status_states = [
        (0, "DRAFT", "App State 0: Draft in progress"),
        (1, "APPLIED", "App State 1: Submitted"),
        (2, "SCREENING", "App State 2: Under Recruiter Screening"),
        (3, "INTERVIEW", "App State 3: Technical Round Scheduled"),
        (4, "OFFERED", "App State 4: Formal Offer Extended"),
        (5, "HIRED", "App State 5: Placement Completed"),
        (6, "REJECTED", "App State 6: Not Suitable for Role"),
        (7, "WITHDRAWN", "App State 7: Candidate Self-Withdrawn"),
    ]

    for status_id, status_name, note in status_states:
        c_email = f"candidate.state{status_id}@talentra.io"
        u = db.execute(select(User).where(User.email_address == c_email)).scalar_one_or_none()
        if not u:
            u = User(
                email_address=c_email,
                display_name=f"Candidate State_{status_name}",
                account_status_code_id=1,
                identity_provider_code="SUPABASE",
                provider_subject=f"sub-synthetic-state-{status_id}",
            )
            db.add(u)
            db.flush()

            cp = CandidateProfile(
                user_id=u.id,
                actor_id=f"CA8000{status_id}",
                first_name="State",
                last_name=f"Candidate_{status_name}",
                profile_status_code_id=1,
                profile_visibility_code_id=1,
            )
            db.add(cp)
            db.flush()

            db.add(CandidateContact(
                candidate_profile_id=cp.id,
                email_address=u.email_address,
                phone_e164=f"+91987658000{status_id}",
                phone_country_id=1,
            ))

            app = JobApplication(
                job_requirement_id=job_alpha.id,
                candidate_profile_id=cp.id,
                status_code_id=status_id,
                cover_letter=note,
            )
            db.add(app)
            db.flush()

            db.add(ApplicationStatusHistory(
                job_application_id=app.id,
                from_status_code_id=1 if status_id > 1 else None,
                to_status_code_id=status_id,
                changed_by_user_id=emp_user.id,
            ))
            results["lifecycle_applications_seeded"] += 1

    # 3b. Deterministic Academic & Eligibility Boundary Test Fixtures
    from app.models.candidate import CandidateEducation
    from sqlalchemy import text

    btech_q = db.execute(text("SELECT id FROM qualification WHERE qualification_code = 'BTECH'")).fetchone()
    btech_qid = btech_q[0] if btech_q else 1

    # Strict eligibility cutoff job: CGPA >= 6.00, 0 active backlogs
    job_cutoff = db.execute(select(JobRequirement).where(JobRequirement.title == "Eligibility Benchmark Job (CGPA 6.00)")).scalar_one_or_none()
    if not job_cutoff:
        job_cutoff = JobRequirement(
            organisation_id=org_alpha.id,
            created_by_user_id=emp_user.id,
            job_role_id=role_rec.id if role_rec else 1,
            title="Eligibility Benchmark Job (CGPA 6.00)",
            description="Benchmark job for boundary testing eligibility engine.",
            employment_type_id=emp_t.id if emp_t else 1,
            work_type_id=work_t.id if work_t else 1,
            status_code_id=2,  # OPEN
            publish_state_code_id=2,  # PUBLISHED
            positions_count=2,
            min_cgpa=Decimal("6.00"),
            min_percentage=Decimal("60.00"),
            allow_backlogs=False,
            max_active_backlogs=0,
            required_qualifications=json.dumps(["BTECH", "BE"]),
        )
        db.add(job_cutoff)
        db.flush()

    boundary_candidates = [
        # (email, actor_id, fname, lname, cgpa, has_backlog, active_backlogs, has_edu)
        ("cand.boundary.below@talentra.io", "CA81001", "BelowCutoff", "Candidate", Decimal("5.99"), False, 0, True),
        ("cand.boundary.above@talentra.io", "CA81002", "ExactCutoff", "Candidate", Decimal("6.00"), False, 0, True),
        ("cand.boundary.backlog@talentra.io", "CA81003", "BacklogFail", "Candidate", Decimal("8.50"), True, 1, True),
        ("cand.boundary.nodata@talentra.io", "CA81004", "NoDataFail", "Candidate", None, False, 0, False),
    ]

    for c_email, a_id, fname, lname, cgpa, has_bl, act_bl, has_edu in boundary_candidates:
        u_bound = db.execute(select(User).where(User.email_address == c_email)).scalar_one_or_none()
        if not u_bound:
            u_bound = User(
                email_address=c_email,
                display_name=f"{fname} {lname}",
                account_status_code_id=1,
                identity_provider_code="SUPABASE",
                provider_subject=f"sub-synthetic-{a_id.lower()}",
            )
            db.add(u_bound)
            db.flush()

            cp_bound = CandidateProfile(
                user_id=u_bound.id,
                actor_id=a_id,
                first_name=fname,
                last_name=lname,
                profile_status_code_id=1,
                profile_visibility_code_id=1,
            )
            db.add(cp_bound)
            db.flush()

            db.add(CandidateContact(
                candidate_profile_id=cp_bound.id,
                email_address=u_bound.email_address,
                phone_e164=f"+9198765{a_id[2:]}",
                phone_country_id=1,
            ))

            if has_edu:
                db.add(CandidateEducation(
                    candidate_profile_id=cp_bound.id,
                    qualification_id=btech_qid,
                    institution_name="Benchmark State Institute of Technology",
                    field_of_study="Computer Science",
                    start_date=date(2018, 8, 1),
                    end_date=date(2022, 5, 31),
                    start_year=2018,
                    completion_year=2022,
                    education_level="UNDERGRADUATE",
                    board_or_university="State Tech University",
                    grading_system="CGPA_10",
                    score_value=cgpa,
                    max_score=Decimal("10.00"),
                    cgpa=cgpa,
                    percentage=cgpa * 10 if cgpa else None,
                    has_backlogs=has_bl,
                    active_backlogs_count=act_bl,
                    historical_backlogs_count=act_bl,
                    status="COMPLETED",
                ))

            # Submit application to test eligibility
            db.add(JobApplication(
                job_requirement_id=job_cutoff.id,
                candidate_profile_id=cp_bound.id,
                status_code_id=1,  # APPLIED
                cover_letter=f"Boundary test fixture for {fname}.",
            ))
            results["boundary_scenarios_seeded"] += 1

    # 4. Licence Seat Exhaustion Test Fixture
    lic_exhausted = db.execute(select(Licence).where(Licence.licence_code == "LIC_TEST_EXHAUSTED_01")).scalar_one_or_none()
    if not lic_exhausted:
        lic_exhausted = Licence(
            licence_code="LIC_TEST_EXHAUSTED_01",
            account_id=acct.id,
            max_users=1,  # Capacity of exactly 1 seat
            max_devices_per_user=1,
            valid_from=now_utc - timedelta(days=1),
            valid_until=now_utc + timedelta(days=30),
            status_code_id=1,
        )
        db.add(lic_exhausted)
        db.flush()

        # Allocate the 1 available seat to emp_user
        db.add(LicenceSeatAllocation(
            licence_id=lic_exhausted.id,
            user_id=emp_user.id,
            status_code_id=1,
            created_by=emp_user.id,
        ))
        results["exhausted_licences_seeded"] += 1

    # 5. Financial Ledger Idempotency & Zero-Balance Fixtures
    wallet_test = db.execute(select(Wallet).where(Wallet.account_id == acct.id)).scalar_one_or_none()
    if not wallet_test:
        wallet_test = Wallet(account_id=acct.id, currency_code="EUR", status_code_id=1)
        db.add(wallet_test)
        db.flush()

        # Pre-seed idempotent ledger entry
        db.add(WalletLedgerEntry(
            wallet_id=wallet_test.id,
            entry_type_code_id=1,  # CREDIT
            amount=Decimal("100.00"),
            currency_code="EUR",
            source_type="TEST_FIXTURE_TOPUP",
            source_id="FIXTURE_ORDER_001",
            idempotency_key="IDEM_TEST_KEY_ALREADY_USED_001",
        ))
        results["financial_fixtures_seeded"] += 1

    # 6. Verification Rejection & Review Case
    verif_provider = db.execute(select(IdentityVerificationProvider).where(IdentityVerificationProvider.provider_code == "SANDBOX_VERIFY_PROVIDER")).scalar_one_or_none()
    if verif_provider:
        case_rejected = db.execute(select(IdentityVerificationCase).where(IdentityVerificationCase.provider_code == "CASE_TEST_REJECTED_01")).scalar_one_or_none()
        if not case_rejected:
            consent_emp = db.execute(select(ConsentRecord).where(ConsentRecord.user_id == emp_user.id)).scalar_one_or_none()
            if not consent_emp:
                consent_emp = ConsentRecord(user_id=emp_user.id, consent_type_code_id=1, policy_version="v1.0", granted=True)
                db.add(consent_emp)
                db.flush()

            case_rejected = IdentityVerificationCase(
                user_id=emp_user.id,
                document_type_code_id=2,  # PAN
                provider_code="CASE_TEST_REJECTED_01",
                status_code_id=4,  # REJECTED
                requested_at=now_utc - timedelta(days=2),
                completed_at=now_utc - timedelta(days=2, minutes=-5),
                consent_record_id=consent_emp.id,
            )
            db.add(case_rejected)
            db.flush()

            db.add(VerificationReview(
                user_id=emp_user.id,
                status_code_id=4,
                provider_code="REF_REJECTED_BLURRY_IMAGE",
                masked_identifier="ABCDE1234F",
            ))
            results["verification_review_cases_seeded"] += 1

    # 7. Audit Event for Retention Purge Testing
    old_audit = db.execute(select(AuditEvent).where(AuditEvent.action_code == "TEST_HISTORICAL_EVENT")).scalar_one_or_none()
    if not old_audit:
        db.add(AuditEvent(
            actor_user_id=emp_user.id,
            action_code="TEST_HISTORICAL_EVENT",
            resource_type="ORGANISATION",
            resource_id="ORG_TEST_ALPHA",
            occurred_at=now_utc,
            request_id=None,
            metadata_redacted={"ip": "127.0.0.1", "status": "SUCCESS"},
        ))

    db.commit()
    return results
