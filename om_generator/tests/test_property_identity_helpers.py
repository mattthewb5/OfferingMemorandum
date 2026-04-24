"""Tests for the auto-derivation helpers in ``property_identity_helpers``."""

import sys
from pathlib import Path

import pytest  # noqa: F401  (used by pytest fixture machinery)

_OM_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OM_DIR))

from property_identity import IdentityValue  # noqa: E402
from property_identity_helpers import (  # noqa: E402
    derive_management_company,
    derive_submarket_name,
)


# ---------------------------------------------------------------------------
# derive_management_company — Loudoun community lookup reuse
# ---------------------------------------------------------------------------


def test_management_company_returns_none_for_fairfax():
    assert derive_management_company("fairfax", "Regent's Park") is None


def test_management_company_returns_none_for_empty_subdivision():
    assert derive_management_company("loudoun", "") is None
    assert derive_management_company("loudoun", None) is None


def test_management_company_loudoun_known_subdivision():
    """Brambleton has a non-null management_company in the curated JSON."""
    result = derive_management_company("loudoun", "BRAMBLETON SECTION 42")
    assert isinstance(result, IdentityValue)
    assert result.source == "auto:loudoun_community_lookup"
    assert result.confirmed_by_broker is False
    # Value must come from the curated JSON, not be hardcoded in the test
    import json
    cfg = (
        Path(__file__).resolve().parents[2]
        / "multi-county-real-estate-research"
        / "data" / "loudoun" / "config" / "communities.json"
    )
    with open(cfg) as f:
        communities = json.load(f).get("communities", {})
    expected = communities["brambleton"]["management_company"]
    assert result.value == expected
    assert expected is not None and expected != ""


def test_management_company_loudoun_unknown_subdivision():
    assert derive_management_company("loudoun", "NotARealSubdivision") is None


def test_management_company_loudoun_match_with_null_management():
    """A community matched but with management_company=null returns None."""
    # ASHBURN VILLAGE has a non-null patterns entry but management_company=null
    # in the curated JSON. Confirm graceful None.
    result = derive_management_company("loudoun", "ASHBURN VILLAGE")
    assert result is None


# ---------------------------------------------------------------------------
# derive_submarket_name — zoning growth-center reuse
# ---------------------------------------------------------------------------


def test_submarket_returns_none_for_unsupported_county():
    assert derive_submarket_name("athens", "addr", 38.87, -77.27) is None


def test_submarket_returns_none_for_missing_coords():
    assert derive_submarket_name("fairfax", "addr", None, None) is None
    assert derive_submarket_name("fairfax", "addr", None, -77.27) is None
    assert derive_submarket_name("fairfax", "addr", 38.87, None) is None


def test_submarket_inside_growth_center_returns_value(monkeypatch):
    """When zoning_context returns an in-growth-center hit, helper wraps it."""
    import property_identity_helpers as h
    monkeypatch.setattr(
        h, "_build_zoning_context_or_none",
        lambda *_a, **_k: {
            "growth_center_name": "Tysons Corner Special District",
            "growth_center_distance_raw": 0.0,
        },
    )
    result = derive_submarket_name("fairfax", "addr", 38.92, -77.22)
    assert isinstance(result, IdentityValue)
    assert result.value == "Tysons Corner Special District"
    assert result.source == "auto:fairfax_zoning_growth_center"
    assert result.confirmed_by_broker is False


def test_submarket_outside_growth_center_returns_none(monkeypatch):
    import property_identity_helpers as h
    monkeypatch.setattr(
        h, "_build_zoning_context_or_none",
        lambda *_a, **_k: {
            "growth_center_name": "Tysons Corner Special District",
            "growth_center_distance_raw": 3.4,
        },
    )
    assert derive_submarket_name("fairfax", "addr", 38.0, -77.5) is None


def test_submarket_no_growth_center_returns_none(monkeypatch):
    import property_identity_helpers as h
    monkeypatch.setattr(
        h, "_build_zoning_context_or_none",
        lambda *_a, **_k: {"growth_center_name": "N/A",
                           "growth_center_distance_raw": None},
    )
    assert derive_submarket_name("fairfax", "addr", 38.0, -77.5) is None


def test_submarket_pipeline_exception_returns_none(monkeypatch):
    """If the underlying pipeline returns None (e.g. import error or raise),
    helper degrades gracefully."""
    import property_identity_helpers as h
    monkeypatch.setattr(
        h, "_build_zoning_context_or_none", lambda *_a, **_k: None,
    )
    assert derive_submarket_name("fairfax", "addr", 38.0, -77.5) is None
