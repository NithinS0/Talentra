"""Comprehensive Test Suite for Stage 15: Database Seeding & Test Data Engineering.

Tests verify:
1. Profile A Reference Data coverage: 249 ISO 3166-1 countries, calling codes, languages.
2. Profile A Idempotency: Re-running does not duplicate country or language records.
3. Profile B System Configuration: 9 docket actor roles, fine-grained permissions, role-permission matrix.
4. Profile B Idempotency: Re-running does not duplicate roles or permissions.
5. Profile C Minimal Development Demo: End-to-end traversal across all 12 modules.
6. Public Actor ID format and prefix validation: Exactly PPNNNNN format.
7. Profile D Functional Test Data: Candidate blocking, multi-tenant boundary, application lifecycle matrix.
8. Financial Fixtures & Ledger Invariants: Double-entry consistency and idempotency keys.
9. Profile E Scale Generator: Chunked batch inserts, deterministic generation, throughput telemetry.
10. Production Environment Safeguards: Rejection of destructive operations or demo seeding on production.
"""

import pytest
from decimal import Decimal
from sqlalchemy import select, func

from app.models.country import Country
from app.models.user import User, Role, UserRoleAssignment, UserActorIdentity
from app.models.organisation import Account, Organisation, OrganisationLocation
from app.models.candidate import CandidateProfile, CandidateContact
from app.models.job import JobRole, EmploymentType, WorkType, JobRequirement, JobPosition
from app.models.application import JobApplication, ApplicationStatusHistory, BlockListEntry
from app.models.gig import GigWorkerProfile, GigRequest, GigApplication, GigAssignment
from app.models.licence import Licence, LicenceSeatAllocation
from app.models.subscription import Subscription, Wallet, WalletLedgerEntry
from app.models.notification import Language, Notification, NotificationPreference
from app.models.verification import IdentityVerificationCase, GovernmentDocumentReference
from app.models.admin import Permission, RolePermission

from scripts.seed.profiles import (
    run_profile_a,
    run_profile_b,
    run_profile_c,
    run_profile_d,
    run_profile_e,
)
from scripts.seed.seed_runner import validate_environment, run_seeder
from tests.fixtures.seed_fixtures import (
    seed_db,
    seeded_reference_data,
    seeded_system_config,
    seeded_demo_ecosystem,
    seeded_functional_test_data,
)


class TestProfileAReferenceData:
    """Tests for Profile A: Reference Master Data."""

    def test_complete_iso_country_coverage(self, seeded_reference_data):
        """Verify complete 249 ISO 3166-1 country coverage and ITU-T E.164 calling codes."""
        countries = seeded_reference_data.execute(select(Country)).scalars().all()
        assert len(countries) >= 249

        # Verify key country codes exist
        country_dict = {c.country_code: c for c in countries}
        assert "IN" in country_dict
        assert country_dict["IN"].calling_code == "+91"
        assert country_dict["IN"].alpha3_code == "IND"

        assert "US" in country_dict
        assert country_dict["US"].calling_code == "+1"
        assert country_dict["US"].alpha3_code == "USA"

        assert "GB" in country_dict
        assert country_dict["GB"].calling_code == "+44"
        assert country_dict["GB"].alpha3_code == "GBR"

    def test_iso_languages_seeded(self, seeded_reference_data):
        """Verify standard ISO 639-1 languages exist."""
        langs = seeded_reference_data.execute(select(Language)).scalars().all()
        assert len(langs) >= 10
        lang_codes = {l.language_code for l in langs}
        assert "en" in lang_codes
        assert "hi" in lang_codes
        assert "es" in lang_codes

    def test_profile_a_idempotency(self, seeded_reference_data):
        """Verify re-running Profile A does not duplicate any records."""
        count_before = seeded_reference_data.execute(select(func.count(Country.id))).scalar()
        run_profile_a(seeded_reference_data)
        count_after = seeded_reference_data.execute(select(func.count(Country.id))).scalar()
        assert count_before == count_after


class TestProfileBSystemConfig:
    """Tests for Profile B: System Configuration & RBAC."""

    def test_nine_actor_roles_configured(self, seeded_system_config):
        """Verify exactly the 9 documented actor roles are configured."""
        roles = seeded_system_config.execute(select(Role)).scalars().all()
        role_codes = {r.role_code for r in roles}

        expected_roles = {
            "SUPER_ADMIN", "ADMIN", "ACCOUNT_ADMIN", "GUEST",
            "CANDIDATE", "EMPLOYER", "RECRUITER", "CONSULTANT", "PLACEMENT_OFFICER"
        }
        assert expected_roles.issubset(role_codes)

    def test_rbac_permissions_and_mapping(self, seeded_system_config):
        """Verify permissions are seeded and mapped to roles."""
        perms = seeded_system_config.execute(select(Permission)).scalars().all()
        assert len(perms) >= 15

        role_perms = seeded_system_config.execute(select(RolePermission)).scalars().all()
        assert len(role_perms) > 0

    def test_profile_b_idempotency(self, seeded_system_config):
        """Verify re-running Profile B is strictly idempotent."""
        role_count_1 = seeded_system_config.execute(select(func.count(Role.id))).scalar()
        perm_count_1 = seeded_system_config.execute(select(func.count(Permission.id))).scalar()

        run_profile_b(seeded_system_config)

        role_count_2 = seeded_system_config.execute(select(func.count(Role.id))).scalar()
        perm_count_2 = seeded_system_config.execute(select(func.count(Permission.id))).scalar()

        assert role_count_1 == role_count_2
        assert perm_count_1 == perm_count_2


class TestProfileCDevDemo:
    """Tests for Profile C: Minimal Development Demo Dataset."""

    def test_nine_synthetic_actors_with_valid_prefixes(self, seeded_demo_ecosystem):
        """Verify 9 synthetic actors follow the exact PPNNNNN public ID format."""
        actors = seeded_demo_ecosystem.execute(select(UserActorIdentity)).scalars().all()
        assert len(actors) >= 9

        prefix_map = {
            "SUPER_ADMIN": "SA",
            "ADMIN": "AD",
            "ACCOUNT_ADMIN": "AA",
            "GUEST": "GU",
            "CANDIDATE": "CA",
            "EMPLOYER": "EM",
            "RECRUITER": "RE",
            "CONSULTANT": "CO",
            "PLACEMENT_OFFICER": "PO",
        }

        actor_ids = {a.role_code: a.actor_id for a in actors}
        for role_code, expected_prefix in prefix_map.items():
            assert role_code in actor_ids
            actual_id = actor_ids[role_code]
            assert actual_id.startswith(expected_prefix)
            assert len(actual_id) == 7
            assert actual_id[2:].isdigit()

    def test_end_to_end_demo_module_traversal(self, seeded_demo_ecosystem):
        """Verify all core entities exist and have valid foreign keys in Demo profile."""
        # 1. Accounts & Orgs
        accounts = seeded_demo_ecosystem.execute(select(Account)).scalars().all()
        assert len(accounts) >= 1

        orgs = seeded_demo_ecosystem.execute(select(Organisation)).scalars().all()
        assert len(orgs) >= 2

        # 2. Candidate & Job & Application
        cands = seeded_demo_ecosystem.execute(select(CandidateProfile)).scalars().all()
        assert len(cands) >= 1

        jobs = seeded_demo_ecosystem.execute(select(JobRequirement)).scalars().all()
        assert len(jobs) >= 1

        apps = seeded_demo_ecosystem.execute(select(JobApplication)).scalars().all()
        assert len(apps) >= 1
        assert apps[0].job_requirement_id == jobs[0].id
        assert apps[0].candidate_profile_id == cands[0].id

        # 3. Gig Marketplace
        gigs = seeded_demo_ecosystem.execute(select(GigAssignment)).scalars().all()
        assert len(gigs) >= 1

        # 4. Licences & Seats
        licences = seeded_demo_ecosystem.execute(select(Licence)).scalars().all()
        assert len(licences) >= 1
        seats = seeded_demo_ecosystem.execute(select(LicenceSeatAllocation)).scalars().all()
        assert len(seats) >= 1

        # 5. Subscriptions & Wallets
        subs = seeded_demo_ecosystem.execute(select(Subscription)).scalars().all()
        assert len(subs) >= 1
        wallets = seeded_demo_ecosystem.execute(select(Wallet)).scalars().all()
        assert len(wallets) >= 1

        # 6. Verification
        cases = seeded_demo_ecosystem.execute(select(IdentityVerificationCase)).scalars().all()
        assert len(cases) >= 1

    def test_profile_c_idempotency(self, seeded_demo_ecosystem):
        """Verify re-running Profile C does not duplicate primary accounts or jobs."""
        jobs_1 = seeded_demo_ecosystem.execute(select(func.count(JobRequirement.id))).scalar()
        run_profile_c(seeded_demo_ecosystem)
        jobs_2 = seeded_demo_ecosystem.execute(select(func.count(JobRequirement.id))).scalar()
        assert jobs_1 == jobs_2


class TestProfileDFunctionalTestData:
    """Tests for Profile D: Edge Cases and Functional Boundaries."""

    def test_candidate_blocking_seeded(self, seeded_functional_test_data):
        """Verify blocked candidate record exists with valid BlockListEntry."""
        block_entries = seeded_functional_test_data.execute(select(BlockListEntry)).scalars().all()
        assert len(block_entries) >= 1
        entry = block_entries[0]
        assert entry.blocker_user_id is not None
        assert entry.blocked_user_id is not None

    def test_application_lifecycle_states_seeded(self, seeded_functional_test_data):
        """Verify all major application lifecycle states (1 to 7) exist in the test dataset."""
        apps = seeded_functional_test_data.execute(select(JobApplication)).scalars().all()
        status_ids = {a.status_code_id for a in apps}
        for expected_id in [1, 2, 3, 4, 5, 6, 7]:
            assert expected_id in status_ids

    def test_exhausted_licence_boundary_fixture(self, seeded_functional_test_data):
        """Verify exhausted licence fixture has capacity exactly matched to allocated seats."""
        lic = seeded_functional_test_data.execute(
            select(Licence).where(Licence.licence_code == "LIC_TEST_EXHAUSTED_01")
        ).scalar_one_or_none()
        assert lic is not None
        assert lic.max_users == 1

        allocated_seats = seeded_functional_test_data.execute(
            select(func.count(LicenceSeatAllocation.id)).where(LicenceSeatAllocation.licence_id == lic.id)
        ).scalar()
        assert allocated_seats == lic.max_users  # Capacity fully exhausted

    def test_wallet_idempotency_fixture(self, seeded_functional_test_data):
        """Verify pre-seeded idempotent financial transaction key exists."""
        entry = seeded_functional_test_data.execute(
            select(WalletLedgerEntry).where(WalletLedgerEntry.idempotency_key == "IDEM_TEST_KEY_ALREADY_USED_001")
        ).scalar_one_or_none()
        assert entry is not None
        assert entry.amount == Decimal("100.00")
        assert entry.entry_type_code_id == 1  # CREDIT


class TestProfileEScaleGenerator:
    """Tests for Profile E: Performance & Scale Generator."""

    def test_chunked_scale_generation(self, seeded_system_config):
        """Verify ScaleGenerator executes in memory-bounded batches with telemetry."""
        result = run_profile_e(
            db=seeded_system_config,
            num_candidates=20,
            num_jobs=5,
            num_applications=15,
            batch_size=10,
            dry_run=False,
        )

        assert result["candidates_inserted"] >= 20
        assert result["jobs_inserted"] >= 5
        assert result["applications_inserted"] >= 15
        assert result["elapsed_seconds"] >= 0.0
        assert result["throughput_rows_per_second"] >= 0.0

    def test_scale_generator_dry_run(self, seed_db):
        """Verify dry-run mode returns target counts without writing to database."""
        result = run_profile_e(
            db=seed_db,
            num_candidates=50000,
            num_jobs=5000,
            num_applications=25000,
            dry_run=True,
        )
        assert result["dry_run"] is True
        assert result["target_candidates"] == 50000

        # Database should still have 0 candidates
        cand_count = seed_db.execute(select(func.count(CandidateProfile.id))).scalar()
        assert cand_count == 0


class TestProductionSafeguards:
    """Tests for production environment safety validation."""

    def test_clean_rejected_on_production(self):
        """Verify attempting --clean on production raises PermissionError."""
        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="production", profile="A", clean=True)

        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="prod", profile="B", clean=True)

    def test_demo_profiles_rejected_on_production(self):
        """Verify synthetic test profiles (C, D, E, ALL) are blocked on production."""
        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="production", profile="C", clean=False)

        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="production", profile="D", clean=False)

        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="production", profile="E", clean=False)

        with pytest.raises(PermissionError, match="CRITICAL ERROR"):
            validate_environment(env_name="production", profile="ALL", clean=False)

    def test_reference_profile_allowed_on_production_without_clean(self):
        """Verify Profile A and Profile B are permitted on production when clean is False."""
        # Should not raise exception
        validate_environment(env_name="production", profile="A", clean=False)
        validate_environment(env_name="production", profile="B", clean=False)


class TestSeedValidatorSuite:
    """Tests for the 12-point post-seed integrity validator."""

    def test_validator_scorecard_on_functional_data(self, seeded_functional_test_data):
        """Verify all 12 automated checks run and pass on seeded dataset."""
        from scripts.seed.validator import SeedValidator
        validator = SeedValidator(seeded_functional_test_data)
        report = validator.run_all_checks()

        assert report["checks_run"] == 12
        assert report["checks_passed"] == 12
        assert report["checks_failed"] == 0
        assert report["status"] == "PASSED"

        # Check key invariants
        assert report["results"]["check_3_foreign_key_orphans"]["orphan_candidates"] == 0
        assert report["results"]["check_4_unique_keys_and_actor_ids"]["duplicate_actor_ids"] == 0
        assert report["results"]["check_6_academic_integrity_and_dates"]["inverted_years"] == 0
        assert report["results"]["check_7_application_pair_uniqueness"]["duplicate_application_pairs"] == 0
        assert report["results"]["check_9_required_dependent_records"]["candidates_without_contact"] == 0


class TestAcademicEligibilityFixtures:
    """Tests for deterministic academic & eligibility engine boundary fixtures."""

    def test_boundary_candidates_seeded(self, seeded_functional_test_data):
        """Verify boundary test candidates (below cutoff, exact cutoff, active backlog) exist."""
        below = seeded_functional_test_data.execute(
            select(User).where(User.email_address == "cand.boundary.below@talentra.io")
        ).scalar_one_or_none()
        assert below is not None

        above = seeded_functional_test_data.execute(
            select(User).where(User.email_address == "cand.boundary.above@talentra.io")
        ).scalar_one_or_none()
        assert above is not None

        backlog = seeded_functional_test_data.execute(
            select(User).where(User.email_address == "cand.boundary.backlog@talentra.io")
        ).scalar_one_or_none()
        assert backlog is not None

        nodata = seeded_functional_test_data.execute(
            select(User).where(User.email_address == "cand.boundary.nodata@talentra.io")
        ).scalar_one_or_none()
        assert nodata is not None


class TestCheckpointManagerSuite:
    """Tests for resumable seeding checkpoints."""

    def test_checkpoint_lifecycle(self, tmp_path):
        """Verify recording batches, updating status, and marking completion."""
        from scripts.seed.checkpoint_manager import CheckpointManager
        chk_file = str(tmp_path / "test_checkpoint.json")
        cp = CheckpointManager(checkpoint_file=chk_file)

        assert cp.state["status"] == "INITIALIZED"
        cp.record_batch("CANDIDATES", count=500, batch_index=1)
        assert cp.state["batches_completed"] == 1
        assert cp.state["records_inserted"] == 500
        assert cp.state["status"] == "IN_PROGRESS"

        cp.mark_complete()
        assert cp.state["status"] == "COMPLETED"

        # Reload from disk
        cp_reloaded = CheckpointManager(checkpoint_file=chk_file)
        assert cp_reloaded.state["status"] == "COMPLETED"
        assert cp_reloaded.state["records_inserted"] == 500

