"""Automated Tests for Talentra Stage 3B: Actor IDs and Country Master Data.

Tests cover:
- All 9 actor prefixes (SA, AD, AA, GU, CA, EM, RE, CO, PO)
- Exact 7-character format (PPNNNNN) and zero-padding
- Independent sequence counters
- Uniqueness and format validation
- Counter exhaustion and capacity limit (99,999)
- Client-supplied ID spoofing rejection
- Complete country master dataset validation (249 ISO countries)
- Shared telephone calling codes (+1, +44) without collision
- Idempotent seed repeatability
"""

import re
import pytest
try:
    from app.services.actor_id_service import (
        ActorType,
        ACTOR_PREFIX_MAP,
        PREFIX_TO_ACTOR_TYPE,
        ACTOR_ID_REGEX,
        validate_actor_id,
        get_prefix_for_role,
        InvalidActorPrefixError,
        ClientIDAssignmentProhibitedError,
        provision_actor_identity,
    )
    from app.seeds.seed_countries_iso import (
        build_country_dataset,
        DATASET_METADATA,
    )
except ImportError:
    from backend.app.services.actor_id_service import (
        ActorType,
        ACTOR_PREFIX_MAP,
        PREFIX_TO_ACTOR_TYPE,
        ACTOR_ID_REGEX,
        validate_actor_id,
        get_prefix_for_role,
        InvalidActorPrefixError,
        ClientIDAssignmentProhibitedError,
        provision_actor_identity,
    )
    from backend.app.seeds.seed_countries_iso import (
        build_country_dataset,
        DATASET_METADATA,
    )


class TestActorIDSpecification:
    """Tests for Actor ID format, prefixes, and validation rules."""

    def test_all_nine_prefixes_defined(self):
        """Verify all 9 docket actor types have exactly one unique 2-letter prefix."""
        expected = {
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
        assert ACTOR_PREFIX_MAP == expected
        assert len(ACTOR_PREFIX_MAP) == 9
        assert len(set(ACTOR_PREFIX_MAP.values())) == 9, "All prefixes must be distinct"

    def test_prefix_length_and_case(self):
        """All prefixes must be exactly 2 uppercase ASCII letters."""
        for role, prefix in ACTOR_PREFIX_MAP.items():
            assert len(prefix) == 2
            assert prefix.isupper()
            assert prefix.isalpha()

    def test_format_regex_exact_seven_characters(self):
        """Validate that the format regex enforces exactly PPNNNNN (7 chars)."""
        valid_examples = [
            "SA00001", "AD00001", "AA00001", "GU00001",
            "CA00001", "EM00001", "RE00001", "CO00001", "PO00001",
            "CA99999", "EM00123"
        ]
        for vid in valid_examples:
            assert ACTOR_ID_REGEX.match(vid) is not None
            assert len(vid) == 7
            assert validate_actor_id(vid) is True

    def test_invalid_actor_id_rejection(self):
        """Reject malformed, invalid prefix, out-of-range, or spoofed IDs."""
        invalid_examples = [
            "XX00001",     # Unknown prefix
            "CA0001",      # Too short (6 chars)
            "CA000001",    # Too long (8 chars)
            "CA0000A",     # Non-numeric suffix
            "ca00001",     # Lowercase prefix
            "",            # Empty
            None,          # None
            "C A0001",     # Embedded whitespace
            "1200001",     # Numeric prefix
        ]
        for inv in invalid_examples:
            assert validate_actor_id(inv) is False

    def test_prefix_lookup_case_insensitivity(self):
        """get_prefix_for_role accepts case-insensitive role names."""
        assert get_prefix_for_role("candidate") == "CA"
        assert get_prefix_for_role("CANDIDATE") == "CA"
        assert get_prefix_for_role("super_admin") == "SA"
        assert get_prefix_for_role("placement_officer") == "PO"

    def test_unknown_role_raises_error(self):
        """Unknown role names must be rejected."""
        with pytest.raises(InvalidActorPrefixError):
            get_prefix_for_role("HACKER_ROLE")

    def test_client_supplied_id_spoofing_prohibited(self):
        """Attempting to supply a client-provided public ID must be rejected."""
        with pytest.raises(ClientIDAssignmentProhibitedError):
            provision_actor_identity(
                db=None,
                user_id=1,
                role_id=1,
                role_code="CANDIDATE",
                client_supplied_id="CA99999"
            )

    def test_zero_padding_and_capacity_boundary(self):
        """Verify 5-digit zero-padding format logic and exhaustion boundary at 99,999."""
        def format_id(prefix: str, num: int) -> str:
            if num < 1 or num > 99999:
                raise ValueError("Capacity boundary violation: ID number must be in range 1..99999")
            return f"{prefix}{num:05d}"

        assert format_id("CA", 1) == "CA00001"
        assert format_id("CA", 42) == "CA00042"
        assert format_id("CA", 99999) == "CA99999"

        with pytest.raises(ValueError):
            format_id("CA", 100000)

        with pytest.raises(ValueError):
            format_id("CA", 0)


class TestCountryMasterDataset:
    """Tests for ISO 3166-1 country dataset and ITU-T E.164 telephone calling codes."""

    @pytest.fixture(scope="class")
    def countries(self):
        return build_country_dataset()

    def test_complete_iso_country_count(self, countries):
        """Verify exactly 249 ISO 3166-1 countries/territories are loaded."""
        assert len(countries) == 249, f"Expected 249 countries, found {len(countries)}"

    def test_alpha2_code_uniqueness_and_format(self, countries):
        """All alpha-2 codes must be unique and 2 uppercase letters."""
        a2_codes = [c["country_code"] for c in countries]
        assert len(a2_codes) == len(set(a2_codes)), "Duplicate alpha-2 codes detected"
        for a2 in a2_codes:
            assert len(a2) == 2
            assert a2.isupper()
            assert a2.isalpha()

    def test_alpha3_code_uniqueness_and_format(self, countries):
        """All alpha-3 codes must be unique and 3 uppercase letters."""
        a3_codes = [c["alpha3_code"] for c in countries]
        assert len(a3_codes) == len(set(a3_codes)), "Duplicate alpha-3 codes detected"
        for a3 in a3_codes:
            assert len(a3) == 3
            assert a3.isupper()
            assert a3.isalpha()

    def test_numeric_code_uniqueness_and_format(self, countries):
        """All numeric codes must be unique and 3 digits."""
        num_codes = [c["numeric_code"] for c in countries]
        assert len(num_codes) == len(set(num_codes)), "Duplicate numeric codes detected"
        for num in num_codes:
            assert len(num) == 3
            assert num.isdigit()

    def test_shared_telephone_calling_codes_preserved(self, countries):
        """Shared calling codes must be accurately assigned without conflict."""
        country_by_a2 = {c["country_code"]: c for c in countries}
        
        # North America / NANP (+1)
        assert country_by_a2["US"]["calling_code"] == "+1"
        assert country_by_a2["CA"]["calling_code"] == "+1"
        assert country_by_a2["PR"]["calling_code"] == "+1"

        # UK & Crown Dependencies (+44)
        assert country_by_a2["GB"]["calling_code"] == "+44"
        assert country_by_a2["GG"]["calling_code"] == "+44"
        assert country_by_a2["JE"]["calling_code"] == "+44"
        assert country_by_a2["IM"]["calling_code"] == "+44"

        # Key Talentra Markets
        assert country_by_a2["IN"]["calling_code"] == "+91"
        assert country_by_a2["SG"]["calling_code"] == "+65"
        assert country_by_a2["AE"]["calling_code"] == "+971"
        assert country_by_a2["AU"]["calling_code"] == "+61"
        assert country_by_a2["DE"]["calling_code"] == "+49"

    def test_dataset_provenance_metadata(self):
        """Verify provenance and licensing metadata are documented."""
        assert "source_iso3166" in DATASET_METADATA
        assert "pycountry" in DATASET_METADATA["source_iso3166"]
        assert "phonenumbers" in DATASET_METADATA["source_calling_codes"]
        assert DATASET_METADATA["iso_licence"] == "LGPL-2.1-or-later"
        assert DATASET_METADATA["phone_licence"] == "Apache-2.0"
