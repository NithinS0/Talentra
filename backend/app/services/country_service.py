"""Country Master Validation and Telephone Formatting Service.

Provides ISO 3166-1 country lookup and ITU-T E.164 phone number validation/formatting.
"""

from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from sqlalchemy.orm import Session

from app.models.country import Country


class InvalidCountryCodeError(ValueError):
    """Raised when a country code is not found in the verified ISO country table."""
    pass


class InvalidPhoneNumberError(ValueError):
    """Raised when a phone number is invalid for the specified country."""
    pass


def get_country_by_code(db: Session, country_code: str) -> Country:
    """Fetch and validate an active country by its 2-letter ISO alpha-2 code.
    
    Args:
        db: SQLAlchemy session.
        country_code: 2-character ISO code (e.g. 'IN', 'US', 'GB').
        
    Returns:
        Country database record.
        
    Raises:
        InvalidCountryCodeError: If country code is missing, invalid format, or not in DB.
    """
    if not country_code or not isinstance(country_code, str):
        raise InvalidCountryCodeError("Country code must be a non-empty string.")

    normalized = country_code.strip().upper()
    if len(normalized) != 2 or not normalized.isalpha():
        raise InvalidCountryCodeError(
            f"Country code '{country_code}' is invalid. Must be a 2-letter ISO 3166-1 alpha-2 code."
        )

    country = db.query(Country).filter(
        Country.country_code == normalized,
        Country.is_active.is_(True),
    ).first()

    if not country:
        raise InvalidCountryCodeError(
            f"Country code '{normalized}' is not recognized or not currently active."
        )

    return country


def validate_and_format_phone(phone_str: str, country_code: str) -> str:
    """Validate a telephone number against its country format and output E.164 format.
    
    Args:
        phone_str: Raw telephone string provided by user.
        country_code: 2-letter ISO country code for parsing context.
        
    Returns:
        E.164 formatted string (e.g. '+919876543210').
        
    Raises:
        InvalidPhoneNumberError: If phone number is malformed or invalid for country.
    """
    if not phone_str or not isinstance(phone_str, str):
        raise InvalidPhoneNumberError("Phone number must be a non-empty string.")

    cleaned_phone = phone_str.strip()
    normalized_country = country_code.strip().upper()

    try:
        parsed = phonenumbers.parse(cleaned_phone, normalized_country)
    except NumberParseException as e:
        raise InvalidPhoneNumberError(
            f"Could not parse phone number '{phone_str}' for country '{country_code}': {e}"
        ) from e

    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneNumberError(
            f"Phone number '{phone_str}' is not a valid telephone number in country '{country_code}'."
        )

    # Format to standard international E.164 string (e.g. '+14155552671')
    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
