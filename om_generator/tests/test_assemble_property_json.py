"""Tests for the pure sidecar builder in provenance_app.

Exercises ``_build_property_sidecar_dict`` (no Streamlit, no I/O). Streamlit
and a few heavy deps are stubbed so importing ``provenance_app`` doesn't
require the full UI runtime.
"""

import sys
import types
from pathlib import Path

import pytest


def _install_stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


def _ensure_provenance_app_importable():
    """Stub heavy deps so we can import provenance_app for the pure helper."""

    if "provenance_app" in sys.modules:
        return sys.modules["provenance_app"]

    # ── streamlit stub ───────────────────────────────────────────────
    if "streamlit" not in sys.modules:
        st_mod = _install_stub("streamlit")

        def _passthrough(*_a, **_kw):
            return None

        # Streamlit decorators / helpers used at provenance_app import time
        def _cache_data(*args, **kwargs):
            if args and callable(args[0]):
                return args[0]
            return lambda fn: fn

        st_mod.cache_data = _cache_data
        st_mod.cache_resource = _cache_data
        st_mod.session_state = {}

        # The functions provenance_app calls at import time must exist but
        # never fire during import; module-level code in provenance_app is
        # mostly defs + constants.
        for fn_name in (
            "set_page_config", "markdown", "info", "warning", "error",
            "success", "header", "subheader", "title", "caption",
            "write", "divider", "text_input", "number_input", "radio",
            "checkbox", "selectbox", "button", "rerun", "columns",
            "container", "expander", "data_editor", "file_uploader",
            "tabs", "metric", "table", "dataframe", "image", "code",
            "exception", "spinner", "status", "sidebar", "form",
        ):
            setattr(st_mod, fn_name, _passthrough)

        class _ColCfgStub:
            TextColumn = staticmethod(_passthrough)
            NumberColumn = staticmethod(_passthrough)
            DateColumn = staticmethod(_passthrough)

        st_mod.column_config = _ColCfgStub

    # ── pandas stub for module import (provenance_app imports pandas) ─
    if "pandas" not in sys.modules:
        try:
            import pandas  # noqa: F401
        except ImportError:
            pd_mod = _install_stub("pandas")
            pd_mod.DataFrame = type("DataFrame", (), {})
            pd_mod.read_csv = lambda *a, **kw: None
            pd_mod.read_excel = lambda *a, **kw: None

    # ── om_generator package + om_generator.storage stub ─────────────
    repo_root = Path(__file__).resolve().parents[2]
    om_path = str(repo_root / "om_generator")
    if om_path not in sys.path:
        sys.path.insert(0, om_path)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if "om_generator" not in sys.modules:
        og_pkg = _install_stub("om_generator")
        og_pkg.__path__ = [om_path]
    if "om_generator.storage" not in sys.modules:
        storage = _install_stub("om_generator.storage")
        storage.write_json = lambda *_a, **_kw: None
        storage.read_json = lambda *_a, **_kw: {}
        storage.file_exists = lambda *_a, **_kw: False
        storage.ensure_dir = lambda *_a, **_kw: None
        storage.write_file = lambda *_a, **_kw: None
        storage.read_file = lambda *_a, **_kw: b""
        storage.read_text = lambda *_a, **_kw: ""

    # ── multi-county package path (county_detector lives here) ───────
    mc_root = repo_root / "multi-county-real-estate-research"
    if mc_root.exists() and str(mc_root) not in sys.path:
        sys.path.insert(0, str(mc_root))

    # ── generate_om stub: real module imports requests etc. ──────────
    if "generate_om" not in sys.modules:
        gom = _install_stub("generate_om")
        gom.geocode_address = lambda *_a, **_kw: None
        gom.run_om_generation = lambda *_a, **_kw: {}

    # ── utils.county_detector stub ──────────────────────────────────
    if "utils" not in sys.modules:
        _install_stub("utils").__path__ = []
    if "utils.county_detector" not in sys.modules:
        cd = _install_stub("utils.county_detector")
        cd.detect_county = lambda *_a, **_kw: "fairfax"

    sys.path.insert(0, str(repo_root))
    import importlib
    return importlib.import_module("provenance_app")


@pytest.fixture(scope="module")
def pa():
    return _ensure_provenance_app_importable()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_identity_block_renames_and_wraps(pa):
    pd_details = {
        "property_name": "Regent's Park",
        "year_built": 1997,
        "stories": 4,
        "floor_plan_count": 22,
        "management_company": "Bozzuto Management Company",
        "submarket_label": "Merrifield-Vienna",     # wizard key
        "utility_structure": "Tenant: Elec+Gas | LL: Water",  # wizard key
        "asking_price": 232000000,
        "total_units": 552,
    }

    sidecar = pa._build_property_sidecar_dict(
        ptype="multifamily",
        pd_details=pd_details,
        fin={"pro_forma": {}, "financing": {}, "t12": {}, "unit_mix_rows": []},
        address="9333 Clocktower Place, Fairfax VA 22031",
        county="fairfax",
        geocode={"lat": 38.87, "lon": -77.27, "county": "fairfax"},
        slug="9333-clocktower-place-fairfax-va-22031",
    )

    assert sidecar["schema_version"] == "1.0"
    assert sidecar["county"] == "fairfax"
    assert sidecar["property_type"] == "multifamily"

    p = sidecar["property"]

    # Direct broker fields
    assert p["property_name"] == {
        "value": "Regent's Park", "source": "broker", "confirmed_by_broker": True,
    }
    assert p["year_built"]["value"] == 1997
    assert p["year_built"]["source"] == "broker"
    assert p["stories"]["value"] == 4
    assert p["floor_plan_count"]["value"] == 22

    # Wizard key renames
    assert "submarket_label" not in p
    assert p["submarket_name"]["value"] == "Merrifield-Vienna"
    assert "utility_structure" not in p
    assert p["utility_structure_short"]["value"] == "Tenant: Elec+Gas | LL: Water"


def test_management_company_short_is_derived(pa):
    sidecar = pa._build_property_sidecar_dict(
        ptype="multifamily",
        pd_details={"management_company": "FirstService Residential"},
        fin={"pro_forma": {}, "financing": {}, "t12": {}, "unit_mix_rows": []},
        address="addr",
        county="loudoun",
        geocode={},
        slug="x",
    )
    p = sidecar["property"]
    assert p["management_company"]["value"] == "FirstService Residential"
    assert p["management_company"]["source"] == "broker"

    assert p["management_company_short"]["value"] == "FirstService"
    assert p["management_company_short"]["source"] == "derived"
    assert p["management_company_short"]["confirmed_by_broker"] is False


def test_management_company_short_strips_known_suffixes(pa):
    cases = [
        ("Bozzuto Management Company", "Bozzuto"),
        ("Greystar Management", "Greystar"),
        ("FirstService Residential", "FirstService"),
        ("Bozzuto", "Bozzuto"),
    ]
    for full, expected in cases:
        sidecar = pa._build_property_sidecar_dict(
            ptype="multifamily",
            pd_details={"management_company": full},
            fin={"pro_forma": {}, "financing": {}, "t12": {}, "unit_mix_rows": []},
            address="addr", county="fairfax", geocode={}, slug="x",
        )
        assert sidecar["property"]["management_company_short"]["value"] == expected


def test_hero_image_label_default_always_present(pa):
    sidecar = pa._build_property_sidecar_dict(
        ptype="multifamily",
        pd_details={},
        fin={"pro_forma": {}, "financing": {}, "t12": {}, "unit_mix_rows": []},
        address="addr", county="fairfax", geocode={}, slug="x",
    )
    h = sidecar["property"]["hero_image_label"]
    assert h["value"] == "Property Exterior"
    assert h["source"] == "default"
    assert h["confirmed_by_broker"] is False


def test_empty_wizard_fields_are_omitted(pa):
    pd_details = {
        "property_name": "",            # blank
        "year_built": None,             # blank number_input
        "stories": "",
        "submarket_label": None,
    }
    sidecar = pa._build_property_sidecar_dict(
        ptype="multifamily",
        pd_details=pd_details,
        fin={"pro_forma": {}, "financing": {}, "t12": {}, "unit_mix_rows": []},
        address="addr", county="fairfax", geocode={}, slug="x",
    )
    p = sidecar["property"]
    assert "property_name" not in p
    assert "year_built" not in p
    assert "stories" not in p
    assert "submarket_name" not in p
    # default still fires
    assert "hero_image_label" in p


def test_financial_block_unchanged_shape(pa):
    fin = {
        "pro_forma": {"rent_growth": 3.5, "hold_period": 5, "exit_cap_spread_bps": 25},
        "financing": {"ltv": 65.0, "interest_rate": 6.25, "amortization": 30},
        "t12": {"gpr": 16428000, "vacancy_pct": 4.5, "real_estate_taxes": 1385000},
        "unit_mix_rows": [
            {"Unit Type": "1 BR / 1 BA", "Count": 184, "Avg SF": 728,
             "In-Place Rent ($/mo)": 2130},
        ],
    }
    pd_details = {"asking_price": 232000000, "total_units": 552}
    sidecar = pa._build_property_sidecar_dict(
        ptype="multifamily",
        pd_details=pd_details,
        fin=fin,
        address="addr", county="fairfax", geocode={}, slug="x",
    )
    assert sidecar["asking_price"] == 232000000
    assert sidecar["total_units"] == 552
    assert sidecar["rent_growth_assumption"] == pytest.approx(0.035)
    assert sidecar["exit_cap_spread"] == pytest.approx(0.0025)
    assert sidecar["hold_period"] == 5
    assert sidecar["financing"]["ltv"] == pytest.approx(0.65)
    assert sidecar["financing"]["interest_rate"] == pytest.approx(0.0625)
    assert sidecar["t12"]["gpr"] == 16428000
    assert sidecar["t12"]["vacancy_pct"] == pytest.approx(0.045)
    assert sidecar["unit_mix"][0]["count"] == 184
