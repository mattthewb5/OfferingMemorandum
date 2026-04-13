"""
Financial defaults — county-keyed Tier 2 assumptions for the financial engine.

All default assumptions live here. When a county-specific key is missing,
fall back to "default". Broker inputs from the sidecar JSON always override
these values.
"""

import json
import os
import re
from pathlib import Path


# ============================================================================
# DEFAULTS — keyed by county (lowercase)
# ============================================================================

_FAIRFAX_DEFAULTS = {
    "vacancy_pct": 0.045,
    "credit_loss_pct": 0.005,
    "mgmt_pct": 0.05,
    "real_estate_tax_rate": 0.01040,        # per $1 of assessed value
    "insurance_per_unit": 625,
    "repairs_per_unit": 1050,
    "utility_per_unit": 879,
    "utility_benchmark_low": 820,
    "utility_benchmark_high": 960,
    "admin_pct_of_egi": 0.016,
    "reserves_per_unit": 250,
    "rent_growth_assumption": 0.035,
    "financing_ltv": 0.65,
    "financing_interest_rate": 0.0625,
    "financing_amortization": 30,
    "exit_cap_spread": 0.0025,              # exit cap = going-in cap + this spread
    "hold_period": 5,
    "below_market_threshold_pct": 0.97,     # unit is "below market" if in_place < market × this
}

DEFAULTS = {
    "fairfax": dict(_FAIRFAX_DEFAULTS),
    "loudoun": {
        **_FAIRFAX_DEFAULTS,
        "real_estate_tax_rate": 0.00875,    # Loudoun County rate
    },
    "default": dict(_FAIRFAX_DEFAULTS),
}


def get_defaults(county: str) -> dict:
    """Return merged defaults: county-specific over default."""
    base = DEFAULTS.get("default", {}).copy()
    base.update(DEFAULTS.get(county.lower(), {}))
    return base


# ============================================================================
# SIDECAR LOADER
# ============================================================================

_SCRIPT_DIR = Path(__file__).resolve().parent
_TEST_INPUTS_DIR = _SCRIPT_DIR / "test_inputs"


def _slugify(address: str) -> str:
    """Convert address to filename slug.

    e.g. "9333 Clocktower Place, Fairfax VA 22031"
         → "9333_clocktower_place_fairfax_va_22031"
    """
    slug = address.lower().strip()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    slug = re.sub(r'\s+', '_', slug)
    return slug


def load_financial_inputs(address: str, county: str) -> dict:
    """
    Load broker financial inputs for this property.

    Search order:
    1. test_inputs/financial_inputs_{slug}.json (address-level match)
    2. test_inputs/financial_inputs_{county}.json (county-level fallback)
    3. Return empty dict (engine runs on defaults + RentCast only)

    The returned dict is merged over defaults:
      defaults ← loaded_json (broker values win over defaults)
    """
    inputs = get_defaults(county)

    # Search order 1: address-specific file
    slug = _slugify(address)
    address_file = _TEST_INPUTS_DIR / f"financial_inputs_{slug}.json"
    if address_file.exists():
        try:
            with open(address_file, 'r', encoding='utf-8') as f:
                broker = json.load(f)
            inputs.update(broker)
            print(f"  Financial inputs loaded: {address_file.name}")
            return inputs
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {address_file.name}: {e}")

    # Search order 2: county-level fallback
    county_file = _TEST_INPUTS_DIR / f"financial_inputs_{county.lower()}.json"
    if county_file.exists():
        try:
            with open(county_file, 'r', encoding='utf-8') as f:
                broker = json.load(f)
            inputs.update(broker)
            print(f"  Financial inputs loaded (county fallback): {county_file.name}")
            return inputs
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {county_file.name}: {e}")

    # Search order 3: defaults only
    print(f"  No financial inputs file found for '{address}' — using defaults only")
    return inputs
