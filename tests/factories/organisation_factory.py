"""Organisation and Account Model Factories."""

import itertools
from typing import Optional
from sqlalchemy.orm import Session
from app.models.organisation import Account, Organisation, AccountOrganisation, OrganisationLocation

_org_counter = itertools.count(1)


def create_factory_organisation(
    db: Session,
    display_name: str = "Factory Organisation",
    legal_name: Optional[str] = None,
    country_id: int = 1,
) -> Organisation:
    """Create a synthetic enterprise organisation."""
    idx = next(_org_counter)
    d_name = f"{display_name} #{idx}"
    l_name = legal_name or f"{d_name} Private Limited"

    org = Organisation(
        legal_name=l_name,
        display_name=d_name,
        organisation_type_code_id=1,
        status_code_id=1,
        primary_country_id=country_id,
    )
    db.add(org)
    db.flush()
    return org


def create_factory_account(
    db: Session,
    organisation: Optional[Organisation] = None,
    account_code: Optional[str] = None,
    name: str = "Factory Enterprise Account",
) -> Account:
    """Create a synthetic account container."""
    idx = next(_org_counter)
    code = account_code or f"ACC_FAC_{idx:04d}"

    if not organisation:
        organisation = create_factory_organisation(db)

    account = Account(
        account_code=code,
        account_name=f"{name} #{idx}",
        status_code_id=1,
        root_organisation_id=organisation.id,
        billing_currency_code="USD",
    )
    db.add(account)
    db.flush()

    db.add(AccountOrganisation(
        account_id=account.id,
        organisation_id=organisation.id,
        name="Primary Organisation",
        status_code_id=1,
    ))

    db.add(OrganisationLocation(
        organisation_id=organisation.id,
        account_id=account.id,
        name="Headquarters Location",
        status_code_id=1,
    ))
    db.flush()
    return account
