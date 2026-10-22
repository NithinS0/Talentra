"""Profile B: System Configuration Seeder.

Seeds system configuration required by Talentra:
- 9 Authoritative Actor Roles (SUPER_ADMIN, ADMIN, ACCOUNT_ADMIN, GUEST, CANDIDATE, EMPLOYER, RECRUITER, CONSULTANT, PLACEMENT_OFFICER)
- Fine-grained RBAC Permissions
- Authoritative Role-Permission Matrix
- Core Platform Feature Flags
"""

from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Role
from app.models.admin import Permission, RolePermission
from app.models.verification import FeatureFlag


CORE_ROLES = [
    {
        "role_code": "SUPER_ADMIN",
        "display_name": "Super Administrator",
        "description": "Root platform administrator with unrestricted governance and audit privileges.",
        "is_system_role": True,
    },
    {
        "role_code": "ADMIN",
        "display_name": "Platform Administrator",
        "description": "Operations and compliance administrator for day-to-day platform oversight.",
        "is_system_role": True,
    },
    {
        "role_code": "ACCOUNT_ADMIN",
        "display_name": "Account Administrator",
        "description": "Organisation account administrator managing seats, licences, and billing.",
        "is_system_role": True,
    },
    {
        "role_code": "GUEST",
        "display_name": "Guest User",
        "description": "Unauthenticated or public visitor with read-only access to published jobs.",
        "is_system_role": True,
    },
    {
        "role_code": "CANDIDATE",
        "display_name": "Candidate",
        "description": "Job seeker maintaining candidate profile, documents, and applications.",
        "is_system_role": True,
    },
    {
        "role_code": "EMPLOYER",
        "display_name": "Employer",
        "description": "Enterprise hiring manager posting jobs, managing applicants, and sourcing.",
        "is_system_role": True,
    },
    {
        "role_code": "RECRUITER",
        "display_name": "Recruiter",
        "description": "Mapped agency recruiter sourcing, reviewing candidates, and managing pipelines.",
        "is_system_role": True,
    },
    {
        "role_code": "CONSULTANT",
        "display_name": "Sourcing Consultant",
        "description": "External recruitment specialist fulfilling sourcing mandates and rate cards.",
        "is_system_role": True,
    },
    {
        "role_code": "PLACEMENT_OFFICER",
        "display_name": "Placement Officer",
        "description": "Campus Training and Placement Officer coordinating cohort opportunities.",
        "is_system_role": True,
    },
]

SYSTEM_PERMISSIONS = [
    # Administration & Audit
    {"code": "admin:system_config", "resource": "admin", "action": "configure", "desc": "Modify system parameters and global flags"},
    {"code": "admin:audit_read", "resource": "audit", "action": "read", "desc": "View platform security and audit logs"},
    {"code": "admin:user_manage", "resource": "user", "action": "manage", "desc": "Manage user accounts and role assignments"},
    # Organisations & Licences
    {"code": "organisation:manage", "resource": "organisation", "action": "manage", "desc": "Manage enterprise organisation structure"},
    {"code": "licence:manage", "resource": "licence", "action": "manage", "desc": "Manage seat allocations and device registrations"},
    # Candidates
    {"code": "candidate:profile_manage", "resource": "candidate", "action": "manage", "desc": "Manage personal candidate profile"},
    {"code": "candidate:profile_view", "resource": "candidate", "action": "view", "desc": "View candidate profiles within search boundaries"},
    # Jobs & Applications
    {"code": "job:create", "resource": "job", "action": "create", "desc": "Create and publish job requirements"},
    {"code": "job:read", "resource": "job", "action": "read", "desc": "Search and view job listings"},
    {"code": "application:submit", "resource": "application", "action": "submit", "desc": "Apply to open job positions"},
    {"code": "application:review", "resource": "application", "action": "review", "desc": "Review and update applicant lifecycle stages"},
    # Sourcing & Consultants
    {"code": "sourcing:request_create", "resource": "sourcing", "action": "create", "desc": "Create external sourcing requests"},
    {"code": "sourcing:consultant_assign", "resource": "sourcing", "action": "assign", "desc": "Assign sourcing requests to vetted consultants"},
    # Gig Marketplace
    {"code": "gig:request_manage", "resource": "gig", "action": "manage", "desc": "Create and manage gig assignments"},
    {"code": "gig:worker_apply", "resource": "gig", "action": "apply", "desc": "Apply for gig projects as a verified worker"},
    # Payments & Wallet
    {"code": "payment:order_create", "resource": "payment", "action": "create", "desc": "Create payment orders and top up wallet"},
    {"code": "wallet:balance_view", "resource": "wallet", "action": "view", "desc": "View organisation credit and ledger history"},
    # Verification & Integrations
    {"code": "verification:submit", "resource": "verification", "action": "submit", "desc": "Submit government ID verification documents"},
    {"code": "verification:review", "resource": "verification", "action": "review", "desc": "Review verification cases and audit documents"},
    # Notifications & Community
    {"code": "notification:read", "resource": "notification", "action": "read", "desc": "Receive and manage user notification preferences"},
    {"code": "community:participate", "resource": "community", "action": "participate", "desc": "Post and comment in community discussions"},
]

# Role-permission mapping rules
ROLE_PERMISSION_RULES = {
    "SUPER_ADMIN": ["*"],  # All permissions
    "ADMIN": [
        "admin:system_config", "admin:audit_read", "admin:user_manage",
        "organisation:manage", "licence:manage", "candidate:profile_view",
        "job:read", "application:review", "verification:review",
        "wallet:balance_view", "notification:read", "community:participate",
    ],
    "ACCOUNT_ADMIN": [
        "organisation:manage", "licence:manage", "job:create", "job:read",
        "application:review", "sourcing:request_create", "gig:request_manage",
        "payment:order_create", "wallet:balance_view", "notification:read",
    ],
    "EMPLOYER": [
        "job:create", "job:read", "application:review", "candidate:profile_view",
        "sourcing:request_create", "gig:request_manage", "notification:read",
        "community:participate",
    ],
    "RECRUITER": [
        "job:read", "application:review", "candidate:profile_view",
        "sourcing:request_create", "notification:read", "community:participate",
    ],
    "CANDIDATE": [
        "candidate:profile_manage", "job:read", "application:submit",
        "gig:worker_apply", "verification:submit", "notification:read",
        "community:participate",
    ],
    "CONSULTANT": [
        "job:read", "candidate:profile_view", "sourcing:consultant_assign",
        "gig:worker_apply", "notification:read", "community:participate",
    ],
    "PLACEMENT_OFFICER": [
        "job:read", "candidate:profile_view", "notification:read",
        "community:participate",
    ],
    "GUEST": [
        "job:read",
    ],
}

FEATURE_FLAGS = [
    {"code": "FEATURE_AI_SOURCING", "name": "AI-Powered Sourcing Assistant", "status_code_id": 1, "description": "Enable vector and LLM candidate matching"},
    {"code": "FEATURE_AADHAAR_VERIFICATION", "name": "Aadhaar Identity Verification", "status_code_id": 1, "description": "Enable Aadhaar OTP and document verification"},
    {"code": "FEATURE_WALLET_AUTO_RECHARGE", "name": "Wallet Auto-Recharge", "status_code_id": 1, "description": "Automatic credit top-up when threshold breached"},
    {"code": "FEATURE_COMMUNITY_MODERATION", "name": "Community Auto-Moderation", "status_code_id": 1, "description": "Automated sentiment and spam filtering on posts"},
    {"code": "FEATURE_GIG_ESCROW", "name": "Gig Milestone Escrow", "status_code_id": 1, "description": "Escrow protection for gig project milestones"},
]


def run_profile_b(db: Session, dry_run: bool = False) -> Dict[str, Any]:
    """Execute Profile B (System Configuration) seeding idempotently."""
    results = {
        "profile": "B_SYSTEM_CONFIG",
        "dry_run": dry_run,
        "roles_processed": 0,
        "permissions_processed": 0,
        "role_permissions_mapped": 0,
        "feature_flags_processed": 0,
    }

    if dry_run:
        results["roles_processed"] = len(CORE_ROLES)
        results["permissions_processed"] = len(SYSTEM_PERMISSIONS)
        results["feature_flags_processed"] = len(FEATURE_FLAGS)
        return results

    # 1. Seed Roles
    role_map: Dict[str, Role] = {}
    for r in CORE_ROLES:
        existing = db.execute(select(Role).where(Role.role_code == r["role_code"])).scalar_one_or_none()
        if not existing:
            role_obj = Role(
                role_code=r["role_code"],
                display_name=r["display_name"],
                description=r["description"],
                is_system_role=r["is_system_role"],
            )
            db.add(role_obj)
            db.flush()
            role_map[r["role_code"]] = role_obj
        else:
            existing.display_name = r["display_name"]
            existing.description = r["description"]
            role_map[r["role_code"]] = existing
        results["roles_processed"] += 1

    # 2. Seed Permissions
    perm_map: Dict[str, Permission] = {}
    for p in SYSTEM_PERMISSIONS:
        existing = db.execute(select(Permission).where(Permission.permission_code == p["code"])).scalar_one_or_none()
        if not existing:
            perm_obj = Permission(
                permission_code=p["code"],
                resource_code=p["resource"],
                action_code=p["action"],
                description=p["desc"],
            )
            db.add(perm_obj)
            db.flush()
            perm_map[p["code"]] = perm_obj
        else:
            perm_map[p["code"]] = existing
        results["permissions_processed"] += 1

    # 3. Map Role Permissions
    for role_code, perm_codes in ROLE_PERMISSION_RULES.items():
        role = role_map.get(role_code)
        if not role:
            continue

        target_perms: List[Permission] = []
        if perm_codes == ["*"]:
            target_perms = list(perm_map.values())
        else:
            target_perms = [perm_map[c] for c in perm_codes if c in perm_map]

        for p in target_perms:
            existing_link = db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == p.id,
                )
            ).scalar_one_or_none()

            if not existing_link:
                db.add(RolePermission(
                    role_id=role.id,
                    permission_id=p.id,
                    effect_code="ALLOW",
                ))
                results["role_permissions_mapped"] += 1

    # 4. Feature Flags
    for f in FEATURE_FLAGS:
        existing = db.execute(select(FeatureFlag).where(FeatureFlag.code == f["code"])).scalar_one_or_none()
        if not existing:
            db.add(FeatureFlag(
                code=f["code"],
                name=f["name"],
                status_code_id=f["status_code_id"],
                description=f["description"],
            ))
            results["feature_flags_processed"] += 1

    db.commit()
    return results
