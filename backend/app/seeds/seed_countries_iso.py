"""Talentra Country Master Reference Data Seeder.

Populates the complete ISO 3166-1 country dataset (249 countries and territories)
with alpha-2, alpha-3, numeric codes, and ITU-T E.164 international calling codes.

Data Sources & Licences:
- ISO 3166-1 country dataset: pycountry package (Debian pkg-isocodes, LGPL 2.1)
- ITU-T E.164 calling codes: phonenumbers package (Google libphonenumber, Apache 2.0)
- Execution: Idempotent upsert preserving existing records, primary keys, and relations.
"""

import os
import sys
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pycountry
import phonenumbers
from sqlalchemy import text
from app.core.database import SessionLocal


DATASET_METADATA = {
    "source_iso3166": "pycountry 26.2.16 (ISO 3166-1 official assignations)",
    "source_calling_codes": "phonenumbers 9.0.41 (Google libphonenumber ITU-T E.164 mapping)",
    "iso_licence": "LGPL-2.1-or-later",
    "phone_licence": "Apache-2.0",
    "target_table": "public.country",
    "seeded_at_utc": datetime.now(timezone.utc).isoformat(),
}


def build_country_dataset() -> List[Dict[str, Any]]:
    """Build complete normalized country records from ISO 3166-1 and ITU-T E.164."""
    countries = []
    for c in pycountry.countries:
        a2 = c.alpha_2
        a3 = c.alpha_3
        num = getattr(c, "numeric", None)
        name = getattr(c, "common_name", None) or c.name
        
        # Resolve calling code from libphonenumber
        cc = phonenumbers.country_code_for_region(a2)
        calling_code = f"+{cc}" if cc else None

        countries.append({
            "country_code": a2,
            "alpha3_code": a3,
            "numeric_code": num,
            "name": name[:150],
            "calling_code": calling_code,
            "is_active": True,
        })
    # Sort deterministically by alpha-2
    countries.sort(key=lambda x: x["country_code"])
    return countries


def seed_country_master(db=None) -> Tuple[int, int]:
    """Execute idempotent seed of the complete country master dataset.
    
    Returns:
        Tuple of (records_processed, total_db_count).
    """
    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        dataset = build_country_dataset()
        print(f"Loaded {len(dataset)} country records from {DATASET_METADATA['source_iso3166']}.")
        
        upsert_stmt = text("""
        INSERT INTO "country" (
            "country_code", "alpha3_code", "numeric_code", "name", "calling_code", "is_active"
        ) VALUES (
            :country_code, :alpha3_code, :numeric_code, :name, :calling_code, :is_active
        )
        ON CONFLICT ("country_code") DO UPDATE SET
            "alpha3_code" = EXCLUDED."alpha3_code",
            "numeric_code" = EXCLUDED."numeric_code",
            "name" = EXCLUDED."name",
            "calling_code" = EXCLUDED."calling_code",
            "is_active" = EXCLUDED."is_active",
            "updated_at" = now();
        """)

        for record in dataset:
            db.execute(upsert_stmt, record)
        
        db.commit()

        total_count = db.execute(text("SELECT count(*) FROM \"country\";")).scalar()
        print(f"Country seeding complete. Total countries in database: {total_count}")
        return len(dataset), total_count
    except Exception as e:
        db.rollback()
        print(f"Error seeding country master data: {e}")
        raise
    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    seed_country_master()
