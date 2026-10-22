"""Profile A: Master & Reference Data Seeder.

Authoritative reference datasets:
- 249 ISO 3166-1 Countries with ITU-T E.164 Calling Codes via pycountry & phonenumbers
- ISO 639-1 Standard Languages
- ISO 4217 Currencies (INR, USD, EUR, GBP, AED, SGD, CAD, AUD, JPY, CHF)
- Standard Employment Types, Work Types, and Core Job Roles
- Academic Qualifications & Qualification Levels
- Skills Taxonomy & Categories
- Geographical States & Major Cities
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from scripts.seed.reference_data.reference_importer import (
    seed_countries,
    seed_languages,
    seed_currencies,
    seed_taxonomies,
    seed_qualifications,
    seed_skills,
    seed_states_and_cities,
)


def run_profile_a(db: Session, dry_run: bool = False) -> Dict[str, Any]:
    """Execute Profile A (Reference Data) seeding idempotently."""
    results = {
        "profile": "A_REFERENCE_DATA",
        "dry_run": dry_run,
        "countries_processed": 0,
        "languages_processed": 0,
        "currencies_processed": 0,
        "taxonomies_processed": {},
        "qualifications_processed": 0,
        "skills_processed": 0,
        "cities_processed": 0,
    }

    if dry_run:
        from scripts.seed.reference_data.reference_importer import (
            get_country_dataset,
            LANGUAGES_DATASET,
            CURRENCIES_DATASET,
            EMPLOYMENT_TYPES,
            WORK_TYPES,
            JOB_ROLES,
            QUALIFICATIONS_DATASET,
            SKILLS_DATASET,
        )
        results["countries_processed"] = len(get_country_dataset())
        results["languages_processed"] = len(LANGUAGES_DATASET)
        results["currencies_processed"] = len(CURRENCIES_DATASET)
        results["taxonomies_processed"] = {
            "employment_types": len(EMPLOYMENT_TYPES),
            "work_types": len(WORK_TYPES),
            "job_roles": len(JOB_ROLES),
        }
        results["qualifications_processed"] = len(QUALIFICATIONS_DATASET)
        results["skills_processed"] = len(SKILLS_DATASET)
        results["cities_processed"] = 20
        return results

    # Live idempotent seeding
    inserted_countries, total_countries = seed_countries(db)
    inserted_langs, total_langs = seed_languages(db)
    inserted_curr, total_curr = seed_currencies(db)
    taxonomy_counts = seed_taxonomies(db)
    inserted_quals, total_quals = seed_qualifications(db)
    inserted_skills, total_skills = seed_skills(db)
    inserted_cities, total_cities = seed_states_and_cities(db)

    results["countries_processed"] = total_countries
    results["countries_inserted"] = inserted_countries
    results["languages_processed"] = total_langs
    results["languages_inserted"] = inserted_langs
    results["currencies_processed"] = total_curr
    results["currencies_inserted"] = inserted_curr
    results["taxonomies_processed"] = taxonomy_counts
    results["qualifications_processed"] = total_quals
    results["qualifications_inserted"] = inserted_quals
    results["skills_processed"] = total_skills
    results["skills_inserted"] = inserted_skills
    results["cities_processed"] = total_cities
    results["cities_inserted"] = inserted_cities

    return results
