"""Talentra Master and Reference Data Seed Script.

Populates initial reference domains, reference codes, countries, languages, currencies,
and standard system roles.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import text
from app.core.database import SessionLocal


def seed_master_data():
    """Seed foundational master data."""
    db = SessionLocal()
    print("Starting master data seeding...")
    try:
        # 0. Reference Domain & Reference Code
        db.execute(text("""
        INSERT INTO "reference_domain" ("domain_code", "description") 
        VALUES ('GENERAL_STATUS', 'General system status domain')
        ON CONFLICT ("domain_code") DO NOTHING;
        """))
        db.execute(text("""
        INSERT INTO "reference_code" ("reference_domain_id", "code", "active", "sort_order")
        SELECT rd.id, 'ACTIVE', true, 1
        FROM "reference_domain" rd
        WHERE rd.domain_code = 'GENERAL_STATUS'
          AND NOT EXISTS (
            SELECT 1 FROM "reference_code" rc 
            WHERE rc.reference_domain_id = rd.id AND rc.code = 'ACTIVE'
          );
        """))
        print("  [OK] Seeded GENERAL_STATUS reference domain and ACTIVE code.")

        # 1. Countries
        countries = [
            ("IN", "India"),
            ("US", "United States"),
            ("GB", "United Kingdom"),
            ("SG", "Singapore"),
            ("AE", "United Arab Emirates"),
            ("CA", "Canada"),
            ("AU", "Australia"),
            ("DE", "Germany"),
        ]
        for code, name in countries:
            db.execute(
                text("""
                INSERT INTO "country" ("country_code", "name")
                VALUES (:code, :name)
                ON CONFLICT ("country_code") DO NOTHING;
                """),
                {"code": code, "name": name}
            )
        print(f"  [OK] Seeded {len(countries)} countries.")

        # 2. Languages
        languages = [
            ("en", "English", True),
            ("hi", "Hindi", False),
            ("es", "Spanish", False),
            ("fr", "French", False),
            ("de", "German", False),
        ]
        for code, name, is_def in languages:
            db.execute(
                text("""
                INSERT INTO "language" ("language_code", "display_name", "is_default")
                VALUES (:code, :name, :is_def)
                ON CONFLICT ("language_code") DO NOTHING;
                """),
                {"code": code, "name": name, "is_def": is_def}
            )
        print(f"  [OK] Seeded {len(languages)} languages.")

        # 3. Currencies
        currencies = [
            ("INR", "Indian Rupee", "Indian Rupee (₹)"),
            ("USD", "US Dollar", "United States Dollar ($)"),
            ("EUR", "Euro", "European Euro (€)"),
            ("GBP", "British Pound", "British Pound Sterling (£)"),
            ("SGD", "Singapore Dollar", "Singapore Dollar (S$)"),
            ("AED", "UAE Dirham", "United Arab Emirates Dirham (AED)"),
        ]
        for code, name, desc in currencies:
            db.execute(
                text("""
                INSERT INTO "currency" ("code", "name", "status_code_id", "description")
                SELECT :code, :name, rc.id, :desc
                FROM "reference_code" rc
                WHERE rc.code = 'ACTIVE'
                  AND NOT EXISTS (
                    SELECT 1 FROM "currency" c WHERE c.code = :code
                  );
                """),
                {"code": code, "name": name, "desc": desc}
            )
        print(f"  [OK] Seeded {len(currencies)} currencies.")

        # 4. Standard Roles (9 Docket Actor Classes)
        roles = [
            ("SUPER_ADMIN", "Super Administrator", "Super Administrator with platform-wide privileges"),
            ("ADMIN", "Platform Administrator", "Platform Administrator for operations and governance"),
            ("ACCOUNT_ADMIN", "Account Administrator", "Organisation / Employer Account Administrator"),
            ("GUEST", "Guest User", "Public / Unauthenticated Guest Visitor"),
            ("CANDIDATE", "Candidate", "Job seeker and profile owner"),
            ("EMPLOYER", "Employer", "Hiring enterprise organisation user"),
            ("RECRUITER", "Recruiter", "Mapped recruiter acting on company requirements"),
            ("CONSULTANT", "Sourcing Consultant", "External sourcing consultant"),
            ("PLACEMENT_OFFICER", "Placement Officer", "Training and Placement Officer (TPO) for academic institutions"),
        ]
        for code, disp, desc in roles:
            db.execute(
                text("""
                INSERT INTO "role" ("role_code", "display_name", "description", "is_system_role")
                VALUES (:code, :disp, :desc, true)
                ON CONFLICT ("role_code") DO NOTHING;
                """),
                {"code": code, "disp": disp, "desc": desc}
            )
        print(f"  [OK] Seeded {len(roles)} core roles.")

        # Commit all master data
        db.commit()
        print("Master data seeding completed successfully.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error seeding master data: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    seed_master_data()
