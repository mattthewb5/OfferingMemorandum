"""Tests for ``load_property_inputs`` and the v1.0 sidecar loader."""

import json
import sys
import warnings
from pathlib import Path

import pytest

# Match the production sys.path pattern used by generate_om.py
_OM_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OM_DIR))

from financial_defaults import load_property_inputs, load_financial_inputs  # noqa: E402
from property_identity import (  # noqa: E402
    SCHEMA_VERSION,
    IdentityValue,
    PropertyInputs,
    SchemaVersionError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def canonical_payload():
    return {
        "schema_version": "1.0",
        "slug": "9333_clocktower_place_fairfax_va_22031",
        "address": "9333 Clocktower Place, Fairfax VA 22031",
        "county": "fairfax",
        "property_type": "multifamily",
        "property": {
            "property_name": {
                "value": "Regent's Park",
                "source": "broker",
                "confirmed_by_broker": True,
            },
            "year_built": {
                "value": 1997,
                "source": "auto:attom",
                "confirmed_by_broker": False,
            },
            "management_company_short": {
                "value": "Bozzuto",
                "source": "derived",
                "confirmed_by_broker": False,
            },
        },
        "asking_price": 232000000,
        "total_units": 552,
        "financing": {"ltv": 0.65, "interest_rate": 0.0625, "amortization": 30},
        "rent_growth_assumption": 0.035,
        "exit_cap_spread": 0.0025,
        "hold_period": 5,
    }


@pytest.fixture
def legacy_payload():
    return {
        "property_type": "multifamily",
        "asking_price": 85000000,
        "total_units": 220,
        "financing": {"ltv": 0.65, "interest_rate": 0.0625, "amortization": 30},
        "rent_growth_assumption": 0.035,
        "exit_cap_spread": 0.0025,
        "hold_period": 5,
    }


def _write(tmp_path, name, payload):
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tier 0 — explicit path
# ---------------------------------------------------------------------------


def test_explicit_canonical_path_returns_property_inputs(tmp_path, canonical_payload):
    path = _write(tmp_path, "property_test.json", canonical_payload)

    result = load_property_inputs(
        "9333 Clocktower Place, Fairfax VA 22031", "fairfax", path=str(path),
    )

    assert isinstance(result, PropertyInputs)
    assert result.schema_version == SCHEMA_VERSION
    assert result.county == "fairfax"
    assert "property_name" in result.identity
    pn = result.identity["property_name"]
    assert isinstance(pn, IdentityValue)
    assert pn.value == "Regent's Park"
    assert pn.source == "broker"
    assert pn.confirmed_by_broker is True
    # Auto-prefixed source must be accepted
    assert result.identity["year_built"].source == "auto:attom"
    # Financial fields are flat and merged with defaults
    assert result.financial["asking_price"] == 232000000
    assert result.financial["hold_period"] == 5
    # County default merged in
    assert "vacancy_pct" in result.financial


def test_explicit_legacy_path_emits_deprecation(tmp_path, legacy_payload):
    path = _write(tmp_path, "financial_inputs_old.json", legacy_payload)

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = load_property_inputs(
            "21001 Sycolin Rd, Ashburn VA", "loudoun", path=str(path),
        )

    assert any(issubclass(w.category, DeprecationWarning) for w in captured)
    assert result.identity == {}
    assert result.financial["asking_price"] == 85000000


# ---------------------------------------------------------------------------
# Tier 1 — canonical address-level lookup via the directory
# ---------------------------------------------------------------------------


def test_tier1_canonical_address_lookup(tmp_path, monkeypatch, canonical_payload):
    import financial_defaults as fd

    canonical_dir = tmp_path / "property_inputs"
    canonical_dir.mkdir()
    monkeypatch.setattr(fd, "_PROPERTY_INPUTS_DIR", canonical_dir)
    # Point legacy dir to an empty location so it doesn't shadow the canonical hit.
    monkeypatch.setattr(fd, "_TEST_INPUTS_DIR", tmp_path / "no_legacy_here")

    address = "9333 Clocktower Place, Fairfax VA 22031"
    slug = fd._slugify(address)
    (canonical_dir / f"property_{slug}.json").write_text(
        json.dumps(canonical_payload), encoding="utf-8"
    )

    result = fd.load_property_inputs(address, "fairfax")
    assert result.identity["property_name"].value == "Regent's Park"
    assert result.financial["asking_price"] == 232000000


# ---------------------------------------------------------------------------
# Tier 1b — legacy address-level lookup emits DeprecationWarning
# ---------------------------------------------------------------------------


def test_tier1b_legacy_address_lookup_warns(tmp_path, monkeypatch, legacy_payload):
    import financial_defaults as fd

    legacy_dir = tmp_path / "test_inputs"
    legacy_dir.mkdir()
    monkeypatch.setattr(fd, "_TEST_INPUTS_DIR", legacy_dir)
    monkeypatch.setattr(fd, "_PROPERTY_INPUTS_DIR", tmp_path / "no_canonical_here")

    address = "21001 Sycolin Rd, Ashburn VA"
    slug = fd._slugify(address)
    (legacy_dir / f"financial_inputs_{slug}.json").write_text(
        json.dumps(legacy_payload), encoding="utf-8"
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        result = fd.load_property_inputs(address, "loudoun")

    assert any(issubclass(w.category, DeprecationWarning) for w in captured)
    assert result.identity == {}
    assert result.financial["asking_price"] == 85000000


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------


def test_unknown_schema_version_raises(tmp_path, canonical_payload):
    canonical_payload["schema_version"] = "0.9"
    path = _write(tmp_path, "bad_version.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))


def test_missing_schema_version_raises(tmp_path, canonical_payload):
    canonical_payload["schema_version"] = None
    path = _write(tmp_path, "no_version.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))


def test_malformed_identity_entry_not_dict_raises(tmp_path, canonical_payload):
    canonical_payload["property"]["property_name"] = "Regent's Park"  # bare string
    path = _write(tmp_path, "bad_identity.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))


def test_identity_entry_missing_value_raises(tmp_path, canonical_payload):
    canonical_payload["property"]["property_name"] = {"source": "broker"}
    path = _write(tmp_path, "no_value.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))


def test_unknown_source_raises(tmp_path, canonical_payload):
    canonical_payload["property"]["property_name"] = {
        "value": "X",
        "source": "nonsense",
        "confirmed_by_broker": False,
    }
    path = _write(tmp_path, "bad_source.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))


def test_auto_prefixed_source_accepted(tmp_path, canonical_payload):
    canonical_payload["property"]["property_name"] = {
        "value": "X",
        "source": "auto:attom",
        "confirmed_by_broker": False,
    }
    path = _write(tmp_path, "auto_source.json", canonical_payload)
    result = load_property_inputs("addr", "fairfax", path=str(path))
    assert result.identity["property_name"].source == "auto:attom"


# ---------------------------------------------------------------------------
# Backward-compat alias
# ---------------------------------------------------------------------------


def test_load_financial_inputs_alias_emits_deprecation(tmp_path, canonical_payload):
    path = _write(tmp_path, "property_test.json", canonical_payload)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        flat = load_financial_inputs("addr", "fairfax", financial_inputs_path=str(path))

    assert any(issubclass(w.category, DeprecationWarning) for w in captured)
    # Returns the financial dict, not a PropertyInputs
    assert isinstance(flat, dict)
    assert flat["asking_price"] == 232000000


# ---------------------------------------------------------------------------
# Wave 2 — schema-level property_type enforcement + engine input validation
# ---------------------------------------------------------------------------


from exceptions import OMFinancialEngineInputError  # noqa: E402
from property_identity import PROPERTY_TYPE_MISSING_MSG  # noqa: E402


def test_missing_property_type_raises_documented_message(tmp_path, canonical_payload):
    """A v1.0 sidecar without property_type must fail at sidecar load with
    the wizard-facing documented error string — not at engine entry."""
    canonical_payload.pop("property_type")
    path = _write(tmp_path, "no_ptype.json", canonical_payload)
    with pytest.raises(SchemaVersionError) as excinfo:
        load_property_inputs("addr", "fairfax", path=str(path))
    assert str(excinfo.value) == PROPERTY_TYPE_MISSING_MSG


def test_por_mode_missing_cap_rate_override_raises(tmp_path, canonical_payload):
    """POR=true and no cap_rate_override → engine raises
    OMFinancialEngineInputError (not silent {} return)."""
    pytest.importorskip("requests")  # financial_context pulls in network deps
    from financial_context import build_financial_context

    canonical_payload["asking_price"] = None
    canonical_payload["price_upon_request"] = True
    canonical_payload["cap_rate_override"] = None
    path = _write(tmp_path, "por_no_override.json", canonical_payload)

    with pytest.raises(OMFinancialEngineInputError) as excinfo:
        build_financial_context(
            address="9333 Clocktower Place, Fairfax VA 22031",
            lat=38.87, lon=-77.27, county="fairfax",
            ctx={"property_zip": "22031"},
            financial_inputs_path=str(path),
        )
    assert "Price-on-request mode requires cap_rate_override" in str(excinfo.value)


def test_no_price_no_override_raises(tmp_path, canonical_payload):
    """asking_price=None, price_upon_request=False, cap_rate_override=None
    → engine raises OMFinancialEngineInputError."""
    pytest.importorskip("requests")  # financial_context pulls in network deps
    from financial_context import build_financial_context

    canonical_payload["asking_price"] = None
    canonical_payload["price_upon_request"] = False
    canonical_payload["cap_rate_override"] = None
    path = _write(tmp_path, "no_price_no_override.json", canonical_payload)

    with pytest.raises(OMFinancialEngineInputError) as excinfo:
        build_financial_context(
            address="9333 Clocktower Place, Fairfax VA 22031",
            lat=38.87, lon=-77.27, county="fairfax",
            ctx={"property_zip": "22031"},
            financial_inputs_path=str(path),
        )
    assert "either asking_price or cap_rate_override" in str(excinfo.value)


def test_cap_rate_override_out_of_range_raises(tmp_path, canonical_payload):
    """cap_rate_override outside [0.01, 0.20] is a schema-format error."""
    canonical_payload["cap_rate_override"] = 0.5  # 50% — clearly out of range
    path = _write(tmp_path, "bad_override.json", canonical_payload)
    with pytest.raises(SchemaVersionError):
        load_property_inputs("addr", "fairfax", path=str(path))
