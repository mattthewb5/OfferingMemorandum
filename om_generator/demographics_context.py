"""
Demographics Context Builder for OM Generator

Wires Census ACS 5-Year demographics data into the template variable
structure expected by context_sample.py / market_overview.html.

Bypasses demographics_calculator.py (which depends on Streamlit's
@st.cache_data decorator) and calls CensusClient + TIGERweb directly.

Supports Fairfax County and Loudoun County.

Usage:
    from demographics_context import build_demographics_context
    demo = build_demographics_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.census_api import CensusClient, CensusAPIError, ACS_YEAR

# County FIPS mapping
COUNTY_FIPS = {
    "fairfax": "059",
    "loudoun": "107",
}
STATE_FIPS = "51"  # Virginia

# Earth radius in miles
EARTH_RADIUS_MILES = 3958.8

# TIGERweb API for block group centroids
TIGERWEB_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/Tracts_Blocks/MapServer/8/query"
)

# National median household income (2023 ACS 5-Year)
# Used as fallback if live API call fails
_NATIONAL_MEDIAN_INCOME_FALLBACK = 75149


# ---------------------------------------------------------------------------
# Shared helpers (replicated from demographics_calculator.py, no Streamlit)
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    return EARTH_RADIUS_MILES * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _fetch_centroids(state: str, county: str) -> List[Dict[str, Any]]:
    """Fetch block group centroids from TIGERweb API."""
    params = {
        "where": f"STATE='{state}' AND COUNTY='{county}'",
        "outFields": "GEOID,CENTLAT,CENTLON,AREALAND",
        "returnGeometry": "false",
        "f": "json",
    }
    resp = requests.get(TIGERWEB_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    centroids = []
    for feat in data.get("features", []):
        attrs = feat.get("attributes", {})
        if attrs.get("CENTLAT") and attrs.get("CENTLON"):
            centroids.append({
                "geoid": attrs["GEOID"],
                "lat": float(attrs["CENTLAT"]),
                "lon": float(attrs["CENTLON"]),
            })
    return centroids


def _geoid_from_bg(bg: dict) -> str:
    """Extract GEOID from a Census block group record."""
    s = bg.get("state", "")
    c = bg.get("county", "")
    t = bg.get("tract", "")
    b = bg.get("block group", "")
    if s and c and t and b:
        return f"{s}{c}{t}{b}"
    geo = bg.get("GEO_ID", "")
    if "US" in geo:
        return geo.split("US")[-1]
    return ""


def _filter_by_radius(
    lat: float, lon: float, radius_miles: float,
    centroids: List[dict], block_groups: List[dict],
) -> List[dict]:
    """Return block groups whose centroids fall within radius."""
    in_radius = set()
    for c in centroids:
        if _haversine(lat, lon, c["lat"], c["lon"]) <= radius_miles:
            in_radius.add(c["geoid"])
    return [bg for bg in block_groups if _geoid_from_bg(bg) in in_radius]


# ---------------------------------------------------------------------------
# Aggregation (mirrors demographics_calculator.aggregate_block_group_data)
# ---------------------------------------------------------------------------

def _aggregate(selected: List[dict]) -> dict:
    """Aggregate Census block group records into summary metrics."""
    if not selected:
        return {}

    total_pop = sum(bg.get("total_population") or 0 for bg in selected)
    total_hh = sum(bg.get("total_households") or 0 for bg in selected)

    if total_pop == 0:
        return {}

    # Population-weighted median age
    w_age = sum((bg.get("median_age") or 0) * (bg.get("total_population") or 0) for bg in selected)
    median_age = w_age / total_pop

    # Household-weighted median income
    w_inc = sum((bg.get("median_household_income") or 0) * (bg.get("total_households") or 0) for bg in selected)
    median_income = w_inc / total_hh if total_hh > 0 else 0

    # Education — bachelor's+
    edu_total = sum(bg.get("edu_total_25_plus") or 0 for bg in selected)
    edu_ba = sum(
        (bg.get("edu_bachelors") or 0) + (bg.get("edu_masters") or 0)
        + (bg.get("edu_professional") or 0) + (bg.get("edu_doctorate") or 0)
        for bg in selected
    )
    bachelors_pct = (edu_ba / edu_total * 100) if edu_total > 0 else None

    # Income distribution — collapse 17 Census brackets to 5 template brackets
    income_200k = sum(bg.get("income_200k_plus") or 0 for bg in selected)
    income_150_200 = sum(bg.get("income_150k_200k") or 0 for bg in selected)
    income_100_150 = sum(
        (bg.get("income_100k_125k") or 0) + (bg.get("income_125k_150k") or 0)
        for bg in selected
    )
    income_75_100 = sum(bg.get("income_75k_100k") or 0 for bg in selected)
    income_under_75 = sum(
        (bg.get("income_under_10k") or 0) + (bg.get("income_10k_15k") or 0)
        + (bg.get("income_15k_20k") or 0) + (bg.get("income_20k_25k") or 0)
        + (bg.get("income_25k_30k") or 0) + (bg.get("income_30k_35k") or 0)
        + (bg.get("income_35k_40k") or 0) + (bg.get("income_40k_45k") or 0)
        + (bg.get("income_45k_50k") or 0) + (bg.get("income_50k_60k") or 0)
        + (bg.get("income_60k_75k") or 0)
        for bg in selected
    )

    bracket_counts = [income_200k, income_150_200, income_100_150, income_75_100, income_under_75]
    bracket_total = sum(bracket_counts)

    return {
        "total_population": total_pop,
        "total_households": total_hh,
        "median_age": median_age,
        "median_income": median_income,
        "bachelors_pct": bachelors_pct,
        "bracket_counts": bracket_counts,
        "bracket_total": bracket_total,
    }


# ---------------------------------------------------------------------------
# Supplementary data fetches
# ---------------------------------------------------------------------------

def _fetch_national_median_income(client: CensusClient) -> float:
    """Fetch national median household income from Census API."""
    try:
        url = f"{client.base_url}?get=B19013_001E&for=us:1&key={client.api_key}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if len(data) >= 2:
            return float(data[1][0])
    except Exception:
        pass
    return float(_NATIONAL_MEDIAN_INCOME_FALLBACK)


def _fetch_state_bachelors_pct(client: CensusClient) -> Optional[float]:
    """Fetch Virginia statewide bachelor's+ percentage from Census API."""
    try:
        vars_needed = "B15003_001E,B15003_022E,B15003_023E,B15003_024E,B15003_025E"
        url = (
            f"{client.base_url}?get={vars_needed}"
            f"&for=state:{STATE_FIPS}&key={client.api_key}"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if len(data) >= 2:
            row = data[1]
            total = float(row[0])
            ba_plus = sum(float(row[i]) for i in range(1, 5))
            if total > 0:
                return round(ba_plus / total * 100)
    except Exception:
        pass
    return None


def _compute_population_growth(county: str, county_fips: str) -> Optional[str]:
    """Compute 5-year county-level population growth (2018 vs 2023 ACS).

    Uses county-level totals instead of radius-based block group comparison
    to avoid GEOID mismatches between pre- and post-2020 redistricting vintages.
    """
    try:
        client_2023 = CensusClient(acs_year="2023")
        county_2023 = client_2023.get_county_data(state=STATE_FIPS, county=county_fips)
        pop_2023 = county_2023.get("total_population") or 0

        client_2018 = CensusClient(acs_year="2018")
        county_2018 = client_2018.get_county_data(state=STATE_FIPS, county=county_fips)
        pop_2018 = county_2018.get("total_population") or 0

        if pop_2018 > 0 and pop_2023 > 0:
            growth = (pop_2023 - pop_2018) / pop_2018 * 100
            sign = "+" if growth >= 0 else ""
            label = "growth" if growth >= 0 else "decline"
            print(f"  Population growth: {county.title()} County "
                  f"{pop_2018:,} (2018) → {pop_2023:,} (2023) = {sign}{growth:.1f}%")
            return f"{sign}{growth:.1f}% county 5-yr {label}"
    except Exception as e:
        print(f"  Population growth calc failed: {e}", file=sys.stderr)
    return "growth data unavailable"


# ---------------------------------------------------------------------------
# Income distribution formatting
# ---------------------------------------------------------------------------

_BRACKET_LABELS = [
    "$200,000+",
    "$150,000\u2013$200,000",
    "$100,000\u2013$150,000",
    "$75,000\u2013$100,000",
    "&lt;$75,000",
]

_BRACKET_FILL = [
    "bar-primary",   # $200K+
    "bar-primary",   # $150-200K
    "bar-primary",   # $100-150K
    "bar-light",     # $75-100K
    "bar-light",     # <$75K
]


def _format_brackets(counts: List[int], total: int) -> List[dict]:
    """Convert 5 bracket counts to template-ready dicts with normalized percentages."""
    if total <= 0:
        return []

    raw_pcts = [round(c / total * 100) for c in counts]

    # Normalize to 100%
    diff = 100 - sum(raw_pcts)
    if diff != 0:
        # Adjust the largest bracket
        max_idx = raw_pcts.index(max(raw_pcts))
        raw_pcts[max_idx] += diff

    result = []
    for i, (label, fill) in enumerate(zip(_BRACKET_LABELS, _BRACKET_FILL)):
        result.append({
            "label": label,
            "pct": f"{raw_pcts[i]}%",
            "fill_class": fill,
        })
    return result


# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

def _graceful_degradation() -> dict:
    return {
        "demo": {
            "median_income": "Data pending",
            "income_multiplier": "\u2014",
            "population": "\u2014",
            "population_growth": "\u2014",
            "bachelors_pct": "\u2014",
            "state_bachelors_pct": "\u2014",
            "median_age": "\u2014",
            "income_distribution": [],
            "income_source_footnote": "Demographics data unavailable for this location.",
        }
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_demographics_context(lat: float, lon: float, county: str) -> dict:
    """
    Build the demographics context dict matching the structure in context_sample.py.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name ('fairfax', 'loudoun', or 'unknown')

    Returns:
        Dict with key 'demo' containing all template variables.
    """
    try:
        county_fips = COUNTY_FIPS.get(county)
        if not county_fips:
            return _graceful_degradation()

        # 1. Fetch TIGERweb centroids for the county
        centroids = _fetch_centroids(STATE_FIPS, county_fips)
        if not centroids:
            print("WARNING: Could not fetch block group centroids", file=sys.stderr)
            return _graceful_degradation()

        # 2. Fetch 2023 ACS block group data
        client = CensusClient()
        block_groups = client.get_block_group_data(state=STATE_FIPS, county=county_fips)

        # 3. Filter to 3-mile radius and aggregate
        selected = _filter_by_radius(lat, lon, 3.0, centroids, block_groups)
        agg = _aggregate(selected)
        if not agg:
            return _graceful_degradation()

        total_pop = agg["total_population"]
        median_income = agg["median_income"]
        median_age = agg["median_age"]
        bachelors_pct = agg["bachelors_pct"]

        # 4. National median income for multiplier
        national_median = _fetch_national_median_income(client)
        if median_income and national_median > 0:
            multiplier = round(median_income / national_median, 1)
        else:
            multiplier = "\u2014"

        # 5. Virginia statewide bachelor's pct
        state_ba = _fetch_state_bachelors_pct(client)
        state_ba_str = f"{state_ba}%" if state_ba is not None else "41%"

        # 6. Population growth (county-level, 2018 vs 2023)
        pop_growth = _compute_population_growth(county, county_fips)

        # 7. Income distribution brackets
        brackets = _format_brackets(agg["bracket_counts"], agg["bracket_total"])

        return {
            "demo": {
                "median_income": f"${median_income:,.0f}" if median_income else "N/A",
                "income_multiplier": f"{multiplier}" if isinstance(multiplier, (int, float)) else multiplier,
                "population": f"{total_pop:,}",
                "population_growth": pop_growth or "growth data unavailable",
                "bachelors_pct": f"{bachelors_pct:.0f}%" if bachelors_pct is not None else "N/A",
                "state_bachelors_pct": state_ba_str,
                "median_age": f"{median_age:.0f} yrs" if median_age else "N/A",
                "income_distribution": brackets,
                "income_source_footnote": (
                    f"Source: U.S. Census Bureau ACS 5-Year Estimates (2019\u20132023), "
                    f"3-mile radius. Population growth: {county.title()} County "
                    f"2018 vs. 2023 ACS 5-Year Estimates."
                ),
            }
        }

    except Exception as e:
        print(f"ERROR in build_demographics_context: {e}", file=sys.stderr)
        return _graceful_degradation()
