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
from engine_dispatcher import route_financial_engine
from exceptions import OMFinancialEngineInputError
from financial_defaults import get_defaults, load_property_inputs


def build_financial_context(address: str, lat: float, lon: float,
                             county: str, ctx: dict,
                             financial_inputs_path: str = None) -> dict:
    """
    Load inputs, fetch market rents, route to correct engine.

    Args:
        financial_inputs_path: Optional explicit path to a financial sidecar
            JSON file. When provided, this file is loaded instead of the
            default test_inputs/ search.

    Returns ctx_update dict ready for ctx.update().

    Error handling: ``OMFinancialEngineInputError`` (raised by an engine
    when its sidecar inputs are missing or inconsistent) propagates
    unchanged so the wizard surfaces the engine's diagnostic to the
    broker. Unrelated errors — network failures fetching market rents,
    unexpected runtime errors — are still trapped and yield ``{}`` so
    the OM falls back to seed values rather than blocking generation.
    """
    # 1. Load inputs as the v1.0 PropertyInputs dataclass. Schema-format
    #    failures surface as SchemaVersionError; the dispatcher reads
    #    property_type off the dataclass attribute (not the .financial
    #    catch-all dict).
    defaults = get_defaults(county)
    inputs = load_property_inputs(address, county, path=financial_inputs_path)
    property_type = inputs.property_type

    # 2. Fetch market rents (MF only) — network failures swallowed
    market_rents = {}
    if property_type == "multifamily":
        zipcode = ctx.get("property_zip", "")
        if zipcode:
            try:
                api_key = get_api_key("RENTCAST_API_KEY")
                if api_key:
                    rentcast = RentCastClient(api_key=api_key)
                    market_rents = rentcast.get_market_rent_for_unit_mix(
                        zipcode, inputs.financial.get("unit_mix", []))
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

    # 3. Route to engine via the dispatcher. OMFinancialEngineInputError
    #    propagates so the wizard can surface the engine's diagnostic.
    #    Unrelated runtime errors are still trapped to keep seed-value
    #    fallback working.
    try:
        result = route_financial_engine(inputs, defaults, market_rents)
    except (OMFinancialEngineInputError, NotImplementedError):
        # Engine input failures and stubbed paths must reach the broker.
        raise
    except Exception as e:
        print(f"  ERROR in financial engine: {e}")
        import traceback
        traceback.print_exc()
        return {}

    print(f"  Financial engine ({property_type}): "
          f"cap={result.get('t12_cap_rate', 'N/A')}, "
          f"CoC={result.get('cash_on_cash', 'N/A')}, "
          f"IRR={result.get('irr', 'N/A')}")
    return result
