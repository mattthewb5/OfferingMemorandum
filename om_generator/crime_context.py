"""
Crime Context Builder for OM Generator

Wires fairfax_crime_analysis.py output into the template variable
structure expected by context_sample.py / location_analysis.html.

Usage:
    from crime_context import build_crime_context
    crime_dict = build_crime_context(lat=38.8462, lon=-77.3064)
"""

import sys
from pathlib import Path

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.fairfax_crime_analysis import FairfaxCrimeAnalysis

# Severity ordering: violent > property (used for incident sorting)
_SEVERITY_ORDER = {"violent": 0, "property": 1}


def _clean_crime_type(raw_description: str) -> str:
    """Extract a clean display name from NIBRS-style descriptions.

    E.g. 'ASSAULT - SIMPLE; NOT AGGRAVATED (13B)' -> 'Assault'
         'LARCENY - ALL OTHER LARCENY (23H)' -> 'Larceny'
         'ROBBERY - INDIVIDUAL (120)' -> 'Robbery'
    """
    # Take the first word before any dash/hyphen and title-case it
    text = raw_description.strip()
    for sep in (" - ", " -", "- "):
        if sep in text:
            text = text.split(sep, 1)[0]
            break
    return text.strip().title()

# Default analysis parameters
RADIUS_MILES = 1.0
MONTHS_BACK = 6


def build_crime_context(lat: float, lon: float) -> dict:
    """
    Build the crime context dict matching the structure in context_sample.py.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Dict with keys: safety_score, violent_count, property_count,
        total_incidents, incidents (list), footnote
    """
    analyzer = FairfaxCrimeAnalysis()

    # TODO: Calibrate safety score thresholds against county-wide averages
    # Run score across sample of Fairfax parcels to establish meaningful
    # Low / Moderate / High / Severe bands before client-facing use

    # Safety score (drives the summary boxes)
    safety = analyzer.calculate_safety_score(
        lat, lon, radius_miles=RADIUS_MILES, months_back=MONTHS_BACK
    )

    # All nearby incidents (same parameters for consistency)
    nearby = analyzer.get_crimes_near_point(
        lat, lon, radius_miles=RADIUS_MILES, months_back=MONTHS_BACK
    )

    # Filter to violent + property only, sort by severity then recency, top 5
    notable = nearby[nearby["category"].isin(["violent", "property"])].copy()
    notable["_severity"] = notable["category"].map(_SEVERITY_ORDER)
    notable = notable.sort_values(
        ["_severity", "date"], ascending=[True, False]
    ).head(5)

    # Format incident rows for the template
    incidents = []
    for _, row in notable.iterrows():
        date_str = row["date"].strftime("%b %Y") if hasattr(row["date"], "strftime") else str(row["date"])
        distance_str = f"{row['distance_miles']:.1f} mi"
        category = str(row["category"]).capitalize()

        incidents.append({
            "date": date_str,
            "type": _clean_crime_type(str(row["description"])),
            "type_class": str(row["category"]),
            "classification": category,
            "address": str(row["address"]).split(";")[0].strip(),
            "distance": distance_str,
        })

    # Build footnote from actual counts
    shown_count = len(incidents)
    total = safety["total_crimes"]
    footnote = (
        f"{shown_count} most notable incidents shown (violent + significant property crimes). "
        f"Full incident log ({total} events, {RADIUS_MILES:.0f}-mi radius, "
        f"trailing {MONTHS_BACK} months) available in Data Appendix. "
        f"Block-level addresses used per privacy standards."
    )

    return {
        "safety_score": str(safety["score"]),
        "violent_count": str(safety["breakdown"]["violent"]),
        "property_count": str(safety["breakdown"]["property"]),
        "total_incidents": str(total),
        "incidents": incidents,
        "footnote": footnote,
    }
