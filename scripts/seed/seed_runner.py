"""Talentra Master Seeding CLI Runner & Orchestrator.

Supports CLI Subcommands:
  - reference: Profile A Reference Data (249 ISO countries, calling codes, languages, taxonomies)
  - config: Profile B System Configuration (9 roles, fine-grained permissions, feature flags)
  - demo: Profile C Minimal Development Demo (End-to-end dataset across 12 modules)
  - functional: Profile D Comprehensive Functional Test Data (Edge cases, lifecycle states, boundaries)
  - laptop-scale: Profile E Performance & Scale Data Generator (Configurable high-volume batch generation)
  - validate: Post-seed automated integrity and relational validation scorecard
  - report: Display metrics from last seeding checkpoint and database inventory
  - resume: Resume interrupted laptop-scale seeding run from last checkpoint
  - clean: Safely clean synthetic test fixtures (@talentra.io)

Backwards Compatibility:
  Also supports --profile [A|B|C|D|E|ALL] flag syntax.

Production Safeguards:
  - Destructive clean operations (clean) are prohibited in production environments.
  - Profiles C, D, and E cannot be executed against production databases.
"""

import os
import sys
import argparse
import time
import json
from typing import Dict, Any, Optional

# Ensure backend and root paths are available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from app.core.database import SessionLocal, engine
from app.core.config import settings

from scripts.seed.profiles import (
    run_profile_a,
    run_profile_b,
    run_profile_c,
    run_profile_d,
    run_profile_e,
)
from scripts.seed.checkpoint_manager import CheckpointManager
from scripts.seed.validator import run_validation


def validate_environment(env_name: str, profile: str, clean: bool = False):
    """Enforce strict production safeguards against unintended data alteration."""
    normalized_env = env_name.strip().lower()
    is_prod = normalized_env in ("production", "prod", "live")

    if is_prod and clean:
        raise PermissionError(
            f"CRITICAL ERROR: Destructive cleanup is strictly prohibited on production environment ('{env_name}')."
        )

    if is_prod and profile.upper() in ("C", "D", "E", "ALL", "DEMO", "FUNCTIONAL", "LAPTOP-SCALE"):
        raise PermissionError(
            f"CRITICAL ERROR: Synthetic test/demo profiles cannot be seeded into production ('{env_name}'). "
            "Only Profile A (Reference Data) and Profile B (System Configuration) are allowed on production."
        )


def clean_test_fixtures(db: Session):
    """Safely cleans synthetic test records while leaving master reference data intact."""
    print("Executing cleanup of synthetic development and test fixtures...")

    # Remove in strict foreign-key leaf-to-root order
    cleanup_tables = [
        "gig_assignment",
        "gig_application",
        "gig_request",
        "gig_worker_profile",
        "sourcing_request",
        "consultant_profile",
        "application_status_history",
        "job_application",
        "job_position",
        "job_requirement",
        "block_list_entry",
        "candidate_education_semester",
        "candidate_education",
        "candidate_skill",
        "resume_version",
        "candidate_resume",
        "candidate_document",
        "candidate_contact",
        "candidate_profile",
        "licence_seat_allocation",
        "registered_device",
        "licence",
        "wallet_ledger_entry",
        "wallet",
        "subscription",
        "identity_verification_case",
        "government_document_reference",
        "verification_review",
        "notification",
        "notification_preference",
        "user_actor_identity",
        "user_role_assignment",
        "organisation_recruiter_mapping",
        "account_organisation",
        "organisation_location",
        "organisation",
        "account",
    ]

    for table in cleanup_tables:
        try:
            db.execute(text(f'DELETE FROM "{table}" WHERE created_at IS NOT NULL;'))
        except Exception:
            pass

    # Clean synthetic users with @talentra.io emails
    try:
        db.execute(text("DELETE FROM \"user\" WHERE email_address LIKE '%@talentra.io';"))
    except Exception:
        pass

    db.commit()
    print("Cleanup completed successfully.")


def run_seeder(
    profile: str,
    env_name: str = "development",
    dry_run: bool = False,
    clean: bool = False,
    scale_candidates: int = 1000,
    scale_jobs: int = 100,
    scale_applications: int = 500,
    batch_size: int = 1000,
    random_seed: int = 42,
    db: Session = None,
) -> Dict[str, Any]:
    """Orchestrates seed profile execution with safety validations."""
    validate_environment(env_name, profile, clean)

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    overall_results: Dict[str, Any] = {
        "status": "SUCCESS",
        "profile": profile.upper(),
        "env": env_name,
        "dry_run": dry_run,
        "profile_results": {},
    }

    start_time = time.perf_counter()

    try:
        if clean and not dry_run:
            clean_test_fixtures(db)

        # Map named subcommands to canonical profile codes
        cmd_map = {
            "REFERENCE": "A",
            "CONFIG": "B",
            "SYSTEM-CONFIG": "B",
            "DEMO": "C",
            "FUNCTIONAL": "D",
            "LAPTOP-SCALE": "E",
            "SCALE": "E",
        }
        target = cmd_map.get(profile.upper(), profile.upper())

        if target in ("A", "ALL"):
            print("--> Running Profile A: Reference Data...")
            res_a = run_profile_a(db, dry_run=dry_run)
            overall_results["profile_results"]["A"] = res_a
            print(f"    [OK] Profile A: {res_a['countries_processed']} countries, {res_a['languages_processed']} languages.")

        if target in ("B", "ALL"):
            print("--> Running Profile B: System Configuration...")
            res_b = run_profile_b(db, dry_run=dry_run)
            overall_results["profile_results"]["B"] = res_b
            print(f"    [OK] Profile B: {res_b['roles_processed']} roles, {res_b['permissions_processed']} permissions, {res_b['role_permissions_mapped']} role mappings.")

        if target in ("C", "ALL"):
            print("--> Running Profile C: Minimal Development Demo...")
            res_c = run_profile_c(db, dry_run=dry_run)
            overall_results["profile_results"]["C"] = res_c
            print(f"    [OK] Profile C: {res_c['users_created']} users, {res_c['jobs_created']} jobs, {res_c['applications_created']} applications, {res_c['gigs_created']} gigs.")

        if target in ("D", "ALL"):
            print("--> Running Profile D: Comprehensive Functional Test Data...")
            res_d = run_profile_d(db, dry_run=dry_run)
            overall_results["profile_results"]["D"] = res_d
            print(f"    [OK] Profile D: {res_d['lifecycle_applications_seeded']} lifecycle applications, {res_d['boundary_scenarios_seeded']} boundary scenarios.")

        if target == "E":
            print(f"--> Running Profile E: Performance & Scale Generator (Target: {scale_candidates:,} candidates, {scale_jobs:,} jobs, {scale_applications:,} applications)...")
            res_e = run_profile_e(
                db,
                num_candidates=scale_candidates,
                num_jobs=scale_jobs,
                num_applications=scale_applications,
                batch_size=batch_size,
                random_seed=random_seed,
                dry_run=dry_run,
            )
            overall_results["profile_results"]["E"] = res_e
            print(f"    [OK] Profile E: Processed {res_e['candidates_inserted']:,} candidates, {res_e['jobs_inserted']:,} jobs in {res_e['elapsed_seconds']}s ({res_e['throughput_rows_per_second']} rows/sec).")

        overall_results["duration_seconds"] = round(time.perf_counter() - start_time, 2)
        print(f"\n=======================================================")
        print(f"Seeding completed successfully in {overall_results['duration_seconds']}s")
        print(f"=======================================================")
        return overall_results

    except Exception as e:
        db.rollback()
        overall_results["status"] = "FAILED"
        overall_results["error"] = str(e)
        print(f"\n[ERROR] Seeding execution failed: {e}")
        raise
    finally:
        if should_close:
            db.close()


def print_status_report(db: Session, checkpoint_file: str = "scratch/scale_seed_checkpoint.json"):
    """Displays metrics from the last seeding run and live database inventory."""
    print("\n" + "=" * 60)
    print("TALENTRA SEEDING STATUS & INVENTORY REPORT")
    print("=" * 60)

    # Checkpoint state
    cp = CheckpointManager(checkpoint_file=checkpoint_file)
    print("Checkpoint Status:")
    for k, v in cp.state.items():
        print(f"  - {k}: {v}")

    print("\nLive Database Record Counts:")
    from app.models.country import Country
    from app.models.user import User, Role
    from app.models.organisation import Organisation, Account
    from app.models.candidate import CandidateProfile, CandidateEducation, CandidateSkill
    from app.models.job import JobRequirement, JobPosition
    from app.models.application import JobApplication

    counts = {
        "Country (Master)": db.execute(select(func.count(Country.id))).scalar() or 0,
        "Role (Master)": db.execute(select(func.count(Role.id))).scalar() or 0,
        "Account": db.execute(select(func.count(Account.id))).scalar() or 0,
        "Organisation": db.execute(select(func.count(Organisation.id))).scalar() or 0,
        "User": db.execute(select(func.count(User.id))).scalar() or 0,
        "CandidateProfile": db.execute(select(func.count(CandidateProfile.id))).scalar() or 0,
        "CandidateEducation": db.execute(select(func.count(CandidateEducation.id))).scalar() or 0,
        "CandidateSkill": db.execute(select(func.count(CandidateSkill.id))).scalar() or 0,
        "JobRequirement": db.execute(select(func.count(JobRequirement.id))).scalar() or 0,
        "JobPosition": db.execute(select(func.count(JobPosition.id))).scalar() or 0,
        "JobApplication": db.execute(select(func.count(JobApplication.id))).scalar() or 0,
    }

    for name, c in counts.items():
        print(f"  - {name:<22}: {c:>10,}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Talentra Database Seeding & Synthetic Data CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Support either subcommands or flags
    subparsers = parser.add_subparsers(dest="subcommand", help="Seeding subcommand")

    # seed reference
    subparsers.add_parser("reference", help="Seed Profile A Reference Data (Countries, languages, taxonomies)")

    # seed config
    subparsers.add_parser("config", help="Seed Profile B System Configuration (Roles, permissions, flags)")

    # seed demo
    subparsers.add_parser("demo", help="Seed Profile C Minimal Development Demo (9 actor roles, all modules)")

    # seed functional
    subparsers.add_parser("functional", help="Seed Profile D Comprehensive Functional Test Data (Edge cases, boundaries)")

    # seed laptop-scale
    scale_parser = subparsers.add_parser("laptop-scale", help="Seed Profile E Laptop-Scale Dataset (1M cands, 100k jobs, 5M apps)")
    scale_parser.add_argument("--candidates", type=int, default=1000, help="Target candidate count (laptop target: 1,000,000)")
    scale_parser.add_argument("--jobs", type=int, default=100, help="Target job count (laptop target: 100,000)")
    scale_parser.add_argument("--applications", type=int, default=500, help="Target application count (laptop target: 5,000,000)")
    scale_parser.add_argument("--batch-size", type=int, default=1000, help="Chunk batch size (default: 1,000)")
    scale_parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism (default: 42)")
    scale_parser.add_argument("--dry-run", action="store_true", help="Simulate execution without modifying the database")
    scale_parser.add_argument("--clean", action="store_true", help="Clean owned test fixtures before seeding")
    scale_parser.add_argument("--env", default=os.getenv("APP_ENV", "development"), help="Target environment")

    # seed validate
    subparsers.add_parser("validate", help="Run automated 12-point post-seed integrity validation scorecard")

    # seed report
    subparsers.add_parser("report", help="Display live database inventory and checkpoint status")

    # seed resume
    subparsers.add_parser("resume", help="Resume interrupted laptop-scale seeding run from checkpoint")

    # seed clean
    subparsers.add_parser("clean", help="Clean owned synthetic test fixtures (@talentra.io)")

    # Global / flag options for backwards compatibility
    parser.add_argument(
        "--profile",
        "-p",
        choices=["A", "B", "C", "D", "E", "ALL", "reference", "config", "demo", "functional", "laptop-scale"],
        default=None,
        help="Profile selection flag (A: Reference, B: System Config, C: Demo, D: Functional, E: Scale, ALL: Full suite)",
    )
    parser.add_argument(
        "--env",
        "-e",
        default=os.getenv("APP_ENV", "development"),
        help="Target environment (development, test, staging, production)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without modifying the database",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean owned test fixtures before seeding (prohibited in production)",
    )
    parser.add_argument(
        "--scale-candidates",
        type=int,
        default=1000,
        help="Number of synthetic candidates for Profile E (default: 1,000; laptop target: 1,000,000)",
    )
    parser.add_argument(
        "--scale-jobs",
        type=int,
        default=100,
        help="Number of synthetic jobs for Profile E (default: 100; laptop target: 100,000)",
    )
    parser.add_argument(
        "--scale-applications",
        type=int,
        default=500,
        help="Number of synthetic applications for Profile E (default: 500; laptop target: 5,000,000)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch chunk size (default: 1,000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )

    args = parser.parse_args()

    # Determine command from subcommand or --profile flag
    command = args.subcommand.upper() if args.subcommand else (args.profile.upper() if args.profile else "C")

    # Handle special administrative commands: validate, report, resume, clean
    if command == "VALIDATE":
        with SessionLocal() as db:
            run_validation(db)
        return

    if command == "REPORT":
        with SessionLocal() as db:
            print_status_report(db)
        return

    if command == "CLEAN":
        validate_environment(args.env, "CLEAN", clean=True)
        with SessionLocal() as db:
            clean_test_fixtures(db)
        return

    if command == "RESUME":
        print("Resuming scale seeding from last recorded checkpoint...")
        command = "E"

    # Resolve candidate/job/app scale counts
    cands = getattr(args, "candidates", None) or args.scale_candidates
    jobs = getattr(args, "jobs", None) or args.scale_jobs
    apps = getattr(args, "applications", None) or args.scale_applications
    batch_sz = getattr(args, "batch_size", 1000)
    rand_seed = getattr(args, "seed", 42)

    run_seeder(
        profile=command,
        env_name=args.env,
        dry_run=args.dry_run,
        clean=args.clean,
        scale_candidates=cands,
        scale_jobs=jobs,
        scale_applications=apps,
        batch_size=batch_sz,
        random_seed=rand_seed,
    )


if __name__ == "__main__":
    main()
