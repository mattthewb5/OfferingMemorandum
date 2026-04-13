"""
Financial Context Router — entry point for the financial engine.

Loads inputs, fetches market rents, routes to the correct engine
(multifamily vs. commercial). Returns ctx_update dict ready for
ctx.update().
"""

import sys
from pathlib import Path

# Follow existing sys.path.insert pattern from generate_om.py
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key
from core.rentcast_client import RentCastClient
from financial_defaults import get_defaults, load_financial_inputs
from mf_financials import compute_mf_financials
from commercial_financials import compute_commercial_financials


def build_financial_context(address: str, lat: float, lon: float,
                             county: str, ctx: dict) -> dict:
    """
    Load inputs, fetch market rents, route to correct engine.

    Returns ctx_update dict ready for ctx.update().
    On any failure, returns {} so ctx.update({}) is a no-op and the
    hardcoded seed values remain in ctx.
    """
    try:
        # 1. Load inputs
        defaults = get_defaults(county)
        inputs = load_financial_inputs(address, county)
        property_type = inputs.get("property_type", "multifamily")

        # 2. Fetch market rents (MF only)
        market_rents = {}
        if property_type == "multifamily":
            zipcode = ctx.get("property_zip", "")
            if zipcode:
                try:
                    api_key = get_api_key("RENTCAST_API_KEY")
                    if api_key:
                        rentcast = RentCastClient(api_key=api_key)
                        market_rents = rentcast.get_market_rent_for_unit_mix(
                            zipcode, inputs.get("unit_mix", []))
                        if market_rents:
                            print(f"  Market rents fetched via RentCast: {market_rents}")
                        else:
                            print("  Warning: RentCast returned empty market rents — "
                                  "falling back to 10% premium")
                    else:
                        print("  Warning: RENTCAST_API_KEY not found — "
                              "falling back to 10% premium")
                except Exception as e:
                    print(f"  Warning: RentCast API error: {e} — "
                          "falling back to 10% premium")
                    market_rents = {}

        # 3. Route to engine
        if property_type == "multifamily":
            result = compute_mf_financials(inputs, defaults, market_rents)
        elif property_type in ("office", "retail", "industrial"):
            result = compute_commercial_financials(inputs, defaults, property_type)
        else:
            raise ValueError(f"Unknown property_type: {property_type}")

        print(f"  Financial engine ({property_type}): "
              f"cap={result.get('t12_cap_rate', 'N/A')}, "
              f"CoC={result.get('cash_on_cash', 'N/A')}, "
              f"IRR={result.get('irr', 'N/A')}")
        return result

    except Exception as e:
        print(f"  ERROR in financial engine: {e}")
        import traceback
        traceback.print_exc()
        return {}
