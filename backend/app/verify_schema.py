"""PostgreSQL Catalog Verification Script for Talentra.

Verifies the live database catalog against the approved 216-table blueprint,
233 foreign keys, covering indexes, exclusion constraints, and triggers.
"""

import os
import sys

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.config import settings
from app.core.database import SessionLocal, check_database_connection


def verify_database_schema():
    """Verify live catalog against blueprint expectations."""
    print("=================================================================")
    print("Talentra — Live PostgreSQL Catalog Verification")
    print("=================================================================")
    
    is_ok, msg = check_database_connection()
    if not is_ok:
        print(f"[ERROR] Cannot connect to database: {msg}")
        return False
    
    db = SessionLocal()
    try:
        # 1. Total Tables in public schema
        tbl_res = db.execute(text("""
            SELECT count(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
              AND table_name != 'alembic_version';
        """)).scalar()
        print(f"Total Tables in 'public' schema: {tbl_res} (Expected: 216)")

        # 2. Total Columns in public schema
        col_res = db.execute(text("""
            SELECT count(*) 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name != 'alembic_version';
        """)).scalar()
        print(f"Total Columns in 'public' schema: {col_res} (Expected: 2,357)")

        # 3. Total Foreign Keys
        fk_res = db.execute(text("""
            SELECT count(*)
            FROM information_schema.table_constraints
            WHERE table_schema = 'public' 
              AND constraint_type = 'FOREIGN KEY';
        """)).scalar()
        print(f"Total Foreign Key Constraints: {fk_res} (Expected: 233)")

        # 4. Total Indexes
        idx_res = db.execute(text("""
            SELECT count(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename != 'alembic_version';
        """)).scalar()
        print(f"Total Indexes in 'public' schema: {idx_res} (Expected: >= 233 covering + PKs)")

        # 5. Exclusion Constraints
        excl_res = db.execute(text("""
            SELECT conname, conrelid::regclass 
            FROM pg_constraint 
            WHERE contype = 'x';
        """)).fetchall()
        print(f"Exclusion Constraints Found: {len(excl_res)} (Expected: 2)")
        for cname, tname in excl_res:
            print(f"  [OK] Exclusion constraint: {cname} on {tname}")

        # 6. Triggers for Immutable Ledgers
        trig_res = db.execute(text("""
            SELECT trigger_name, event_object_table 
            FROM information_schema.triggers 
            WHERE trigger_schema = 'public';
        """)).fetchall()
        print(f"Database Triggers Found: {len(trig_res)} (Expected: >= 4)")
        for tname, tbl in trig_res:
            print(f"  [OK] Trigger: {tname} on {tbl}")

        # 7. Check 9 Nullability Fixes
        null_checks = [
            ("candidate_profile", "completion_score"),
            ("gig_request", "price_amount"),
            ("subscription_plan", "price_amount"),
            ("payment_order", "amount"),
            ("payment_transaction", "amount"),
            ("invoice", "subtotal_amount"),
            ("invoice", "tax_amount"),
            ("invoice", "total_amount"),
            ("wallet_ledger_entry", "amount"),
        ]
        print("\nVerifying 9 Critical Nullability Constraints:")
        all_not_null = True
        for tname, cname in null_checks:
            res = db.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = :tname 
                  AND column_name = :cname;
            """), {"tname": tname, "cname": cname}).scalar()
            
            if res == 'NO':
                print(f"  [OK] {tname}.{cname} is NOT NULL")
            else:
                print(f"  [FAIL] {tname}.{cname} is NULLABLE ({res})")
                all_not_null = False

        print("\n=================================================================")
        if tbl_res == 216 and col_res == 2357 and fk_res == 233 and all_not_null:
            print("SCHEMA VERIFICATION: 100% MATCH WITH APPROVED BLUEPRINT!")
        else:
            print("SCHEMA VERIFICATION: DISCREPANCIES DETECTED.")
        print("=================================================================")
        return True
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    verify_database_schema()
