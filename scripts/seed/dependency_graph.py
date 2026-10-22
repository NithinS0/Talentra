"""Topological Dependency Graph and Execution Planner for Talentra Seeding."""

from typing import List, Dict, Set


# Standard dependency DAG across Talentra's 12 Modules
SEED_DEPENDENCY_ORDER = [
    # 1. Master Reference Data (No dependencies)
    "reference_domain",
    "reference_code",
    "country",
    "language",
    "currency",
    "employment_type",
    "work_type",
    "job_role",
    "skill",

    # 2. System Administration & RBAC
    "role",
    "permission",
    "role_permission",

    # 3. Organisations & Accounts
    "account",
    "organisation",
    "account_organisation",
    "organisation_location",
    "organisation_identifier",

    # 4. Identity & Users (Depends on Role, Organisation)
    "user",
    "user_role_assignment",
    "user_actor_identity",
    "consent_record",
    "identity_session",

    # 5. Candidate Profiles
    "candidate_profile",
    "candidate_contact",

    # 6. Jobs & Requisitions (Depends on Organisation, JobRole, User)
    "job_requirement",
    "job_position",

    # 7. Applications & Status (Depends on JobRequirement, CandidateProfile)
    "job_application",
    "application_status_history",

    # 8. Sourcing & Consultant Requests
    "sourcing_request",
    "consultant_profile",
    "consultant_rate_card",
    "consultant_skill",
    "consultant_request_decision",
    "candidate_sourcing_shortlist",
    "outreach_batch",
    "outreach_recipient",

    # 9. Gig Marketplace
    "gig_worker_profile",
    "gig_service_offering",
    "gig_worker_skill",
    "gig_request",
    "gig_application",
    "gig_assignment",
    "gig_earnings_reconciliation",

    # 10. Licences, Seats & Devices
    "licence",
    "licence_entitlement",
    "licence_seat_allocation",
    "registered_device",
    "device_login_counter",

    # 11. Subscriptions, Wallet & Payments
    "subscription_plan",
    "plan_entitlement",
    "subscription",
    "wallet",
    "payment_order",
    "payment_transaction",
    "invoice",
    "invoice_line",
    "wallet_ledger_entry",
    "credit_consumption",

    # 12. Notifications & Community
    "notification_template",
    "notification_preference",
    "notification",
    "notification_delivery",
    "community_post",
    "community_comment",
    "community_reaction",

    # 13. Government Document Verification
    "identity_verification_provider",
    "identity_verification_case",
    "government_document_reference",
    "verification_review",
    "verification_access_log",
    "verification_consent_purpose",
    "verification_retention_job",

    # 14. Dimensional Analytics Marts
    "dim_date",
    "dim_organisation",
    "dim_candidate",
    "dim_job",
    "dim_status",
    "fact_application",
    "fact_job_requirement",
    "fact_gig_assignment",
    "fact_wallet_transaction",
    "fact_notification_delivery",
    "aggregate_dashboard_daily",
    "analytics_refresh_run",
    "analytics_kpi_definition",

    # 15. Optional Reference Extensions
    "salary_benchmark",
    "trending_job_snapshot",
    "feature_flag",
    "dashboard_aggregate_config",
    "organisation_rating_aggregate",
]


class DependencyGraph:
    """Manages seeding dependencies and validates insertion sequences."""

    @staticmethod
    def get_execution_order() -> List[str]:
        """Return the pre-calculated topological order of tables."""
        return list(SEED_DEPENDENCY_ORDER)

    @staticmethod
    def validate_dependencies_met(seeded_tables: Set[str], target_table: str) -> bool:
        """Verify that all prerequisite tables for a target table have already been seeded."""
        if target_table not in SEED_DEPENDENCY_ORDER:
            return True  # Unknown/optional table

        target_idx = SEED_DEPENDENCY_ORDER.index(target_table)
        for i in range(target_idx):
            prereq = SEED_DEPENDENCY_ORDER[i]
            # Core prerequisites must be satisfied
            if prereq in ["role", "user", "organisation", "job_requirement", "candidate_profile"]:
                if prereq not in seeded_tables:
                    return False
        return True
