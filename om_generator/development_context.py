"""
Development Intelligence Context Builder for OM Generator

Computes development pressure score, permit categorization, formula
components, and narrative from Fairfax or Loudoun building-permit data.

Fairfax path: FairfaxPermitsAnalysis (parquet-backed)
Loudoun path: DevelopmentPressureAnalyzer (CSV-backed)

Usage:
    from development_context import build_development_context
    ctx = build_development_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# Loudoun permits path (infrastructure-enriched, 99.6 % geocoded)
_LOUDOUN_PERMITS = (
    _REPO_ROOT
    / "multi-county-real-estate-research"
    / "data"
    / "loudoun"
    / "building_permits"
    / "loudoun_permits_with_infrastructure.csv"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_label_color(score: int) -> tuple:
    """Map a 0-100 pressure score to a human label and CSS color variable."""
    if score <= 25:
        return "Low \u00b7 Supply Constrained", "var(--green)"
    if score <= 60:
        return "Moderate", "var(--amber)"
    return "High \u00b7 Active Pipeline", "var(--red)"


def _component_color(ratio: float) -> str:
    """Pick a bar color for a formula-component fill ratio (0-1)."""
    if ratio <= 0.35:
        return "var(--green)"
    if ratio <= 0.65:
        return "var(--amber)"
    return "var(--red)"


def _component_label(ratio: float) -> str:
    """Pick a qualitative score label for a formula-component ratio."""
    if ratio <= 0.20:
        return "Low"
    if ratio <= 0.40:
        return "Low-Med"
    if ratio <= 0.65:
        return "Moderate"
    return "High"


# ---------------------------------------------------------------------------
# Fairfax path
# ---------------------------------------------------------------------------

def _build_fairfax(lat: float, lon: float, radius_miles: float) -> dict:
    import pandas as pd
    from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

    analyzer = FairfaxPermitsAnalysis()

    # Total county permits (all time, all locations)
    total_county_permits = len(analyzer.permits)

    # Nearby permits — 24-month window
    nearby_df = analyzer.get_permits_near_point(
        lat, lon, radius_miles=radius_miles, months_back=24,
    )
    permits_2mi = len(nearby_df)

    # Also get 12-month subset for recency component
    nearby_12mo = analyzer.get_permits_near_point(
        lat, lon, radius_miles=radius_miles, months_back=12,
    )
    permits_12mo = len(nearby_12mo)

    # Categorize permits using permit_category column
    if permits_2mi > 0:
        cats = nearby_df["permit_category"].value_counts()
        new_res_count = int(cats.get("residential_new", 0))
        new_com_count = int(cats.get("commercial_new", 0))
        com_alt_count = int(cats.get("commercial_renovation", 0))
        res_reno_count = int(cats.get("residential_renovation", 0))
        nearest_dist = float(nearby_df["distance_miles"].min())
    else:
        new_res_count = new_com_count = com_alt_count = res_reno_count = 0
        nearest_dist = None

    new_construction_count = new_res_count + new_com_count

    # Pressure score — delegate to analyzer
    pressure = analyzer.calculate_development_pressure(
        lat, lon, radius_miles=radius_miles, months_back=24,
    )
    score = int(pressure["score"])
    trend = pressure["trend"]

    return _assemble(
        score=score,
        trend=trend,
        total_county_permits=total_county_permits,
        permits_2mi=permits_2mi,
        permits_12mo=permits_12mo,
        new_mf_count=new_res_count,  # residential_new as multifamily proxy
        commercial_alt_count=com_alt_count,
        residential_reno_count=res_reno_count,
        new_construction_count=new_construction_count,
        nearest_dist=nearest_dist,
        county="fairfax",
        radius_miles=radius_miles,
    )


# ---------------------------------------------------------------------------
# Loudoun path
# ---------------------------------------------------------------------------

def _build_loudoun(lat: float, lon: float, radius_miles: float) -> dict:
    from core.development_pressure_analyzer import DevelopmentPressureAnalyzer

    analyzer = DevelopmentPressureAnalyzer(permits_csv_path=str(_LOUDOUN_PERMITS))
    total_county_permits = len(analyzer.permits_df)

    pressure = analyzer.analyze_development_pressure(
        lat, lon, radius_miles=radius_miles,
    )
    nearby = analyzer.find_nearby_permits(lat, lon, radius_miles=radius_miles)

    score = int(pressure.score)
    trend = pressure.trend
    permits_2mi = pressure.permits_within_radius

    # Categorize using permit fields on the Permit dataclass
    new_mf_count = 0
    commercial_alt_count = 0
    residential_reno_count = 0
    new_construction_count = 0
    permits_12mo = 0
    twelve_months_ago = datetime.now() - timedelta(days=365)

    for p in nearby:
        combined = f"{p.permit_type} {p.work_class} {p.description}".lower()
        if p.issue_date and p.issue_date >= twelve_months_ago:
            permits_12mo += 1

        is_new = "new" in combined or "new construction" in combined or "new building" in combined
        is_commercial = "commercial" in combined
        is_residential = "residential" in combined or "single family" in combined or "townhouse" in combined
        is_multifamily = "multi" in combined or "apartment" in combined
        is_alteration = "alteration" in combined or "renovation" in combined or "remodel" in combined

        if is_multifamily and is_new:
            new_mf_count += 1
            new_construction_count += 1
        elif is_new and (is_commercial or is_residential):
            new_construction_count += 1
        elif is_commercial and is_alteration:
            commercial_alt_count += 1
        elif is_residential and is_alteration:
            residential_reno_count += 1

    nearest_dist = nearby[0].distance_miles if nearby else None

    return _assemble(
        score=score,
        trend=trend,
        total_county_permits=total_county_permits,
        permits_2mi=permits_2mi,
        permits_12mo=permits_12mo,
        new_mf_count=new_mf_count,
        commercial_alt_count=commercial_alt_count,
        residential_reno_count=residential_reno_count,
        new_construction_count=new_construction_count,
        nearest_dist=nearest_dist,
        county="loudoun",
        radius_miles=radius_miles,
    )


# ---------------------------------------------------------------------------
# Shared assembly
# ---------------------------------------------------------------------------

def _assemble(
    *,
    score: int,
    trend: str,
    total_county_permits: int,
    permits_2mi: int,
    permits_12mo: int,
    new_mf_count: int,
    commercial_alt_count: int,
    residential_reno_count: int,
    new_construction_count: int,
    nearest_dist: float | None,
    county: str,
    radius_miles: float,
) -> dict:
    label, _color = _score_to_label_color(score)

    # --- Narrative -----------------------------------------------------------
    if new_mf_count == 0:
        narrative = (
            f"Zero new multifamily permits have been filed within "
            f"{radius_miles} miles in the trailing 24 months. The subject "
            f"property faces no near-term competitive multifamily supply "
            f"pipeline per {county.title()} County permit records "
            f"({total_county_permits:,} total permits on file)."
        )
    else:
        narrative = (
            f"{permits_2mi} permits recorded within {radius_miles} "
            f"miles over the trailing 24 months, including {new_mf_count} "
            f"new multifamily permit{'s' if new_mf_count != 1 else ''}."
        )

    # --- Formula components (5 items) ----------------------------------------
    # 1. Permit Volume (30 pts)
    #    Baseline: median county density ~ 50 permits per 2-mi radius per 24mo
    baseline = max(total_county_permits / 800, 1)  # rough per-radius baseline
    volume_ratio = min(permits_2mi / baseline, 1.0) if baseline else 0
    volume_pts = round(volume_ratio * 30)

    # 2. Permit Recency (20 pts)
    recency_ratio = (permits_12mo / max(permits_2mi, 1))
    recency_pts = round(recency_ratio * 20)

    # 3. Permit Type (20 pts) — new construction vs alteration
    type_ratio = (new_construction_count / max(permits_2mi, 1))
    type_pts = round(type_ratio * 20)

    # 4. Proximity (15 pts) — inverse of nearest distance
    if nearest_dist is not None and nearest_dist < radius_miles:
        proximity_ratio = max(0, 1.0 - (nearest_dist / radius_miles))
    else:
        proximity_ratio = 0
    proximity_pts = round(proximity_ratio * 15)

    # 5. Planning Zone (15 pts) — stub
    zone_pts = 0

    dev_formula_components = [
        {
            "name": "Permit Volume (# near property vs. county baseline)",
            "weight": "30%",
            "bar_width": f"{round(volume_ratio * 100)}%",
            "bar_color": _component_color(volume_ratio),
            "score_label": _component_label(volume_ratio),
        },
        {
            "name": "Permit Recency (last 12 mo. vs. 24 mo. total)",
            "weight": "20%",
            "bar_width": f"{round(recency_ratio * 100)}%",
            "bar_color": _component_color(recency_ratio),
            "score_label": _component_label(recency_ratio),
        },
        {
            "name": "Permit Type (residential/new vs. commercial alt.)",
            "weight": "20%",
            "bar_width": f"{round(type_ratio * 100)}%",
            "bar_color": _component_color(type_ratio),
            "score_label": _component_label(type_ratio),
        },
        {
            "name": "Proximity (distance from nearest permit activity)",
            "weight": "15%",
            "bar_width": f"{round(proximity_ratio * 100)}%",
            "bar_color": _component_color(proximity_ratio),
            "score_label": _component_label(proximity_ratio),
        },
        {
            "name": "Planning Zone (Comp Plan growth center distance)",
            "weight": "15%",
            "bar_width": "0%",
            "bar_color": "#cccccc",
            "score_label": "Pending",
        },
    ]

    # --- Permit activity bars (3 items) --------------------------------------
    total = max(1, permits_2mi)
    new_construction_width = round((new_construction_count / total) * 100)
    com_alt_width = round((commercial_alt_count / total) * 100)
    res_reno_width = round((residential_reno_count / total) * 100)

    permit_activity_bars = [
        {
            "label": "New Residential",
            "count": str(new_construction_count),
            "width": f"{new_construction_width}%",
            "fill_class": "bar-primary",
        },
        {
            "label": "Commercial Alteration",
            "count": str(commercial_alt_count),
            "width": f"{com_alt_width}%",
            "fill_class": "bar-primary",
        },
        {
            "label": "Residential Renovation",
            "count": str(residential_reno_count),
            "width": f"{res_reno_width}%",
            "fill_class": "bar-light",
        },
    ]

    # --- Nearest permit display ----------------------------------------------
    if nearest_dist is not None:
        nearest_display = f"{nearest_dist:.1f} mi"
    else:
        nearest_display = f"> {radius_miles} miles"

    # --- Footnotes -----------------------------------------------------------
    permits_context_footnote = (
        f"{permits_2mi} permits within {radius_miles}-mile radius vs. "
        f"{county.title()} County permit database of {total_county_permits:,} "
        f"total permits. "
        + (
            f"Zero new multifamily permits filed within {radius_miles} miles "
            f"in the trailing 24 months."
            if new_mf_count == 0
            else f"{new_mf_count} new multifamily permit{'s' if new_mf_count != 1 else ''} "
            f"within {radius_miles} miles in the trailing 24 months."
        )
    )

    permit_chart_footnote = (
        f"Commercial alteration permits indicate area economic activity without "
        f"introducing residential competition. Total: {permits_2mi} permits "
        f"within {radius_miles}-mi radius, 24-month period."
    )

    # --- Zoning stubs --------------------------------------------------------
    return {
        "dev_pressure_score": str(score),
        "dev_pressure_label": f"{label}",
        "dev_pressure_narrative": narrative,
        "dev_formula_components": dev_formula_components,
        "total_county_permits": f"{total_county_permits:,}",
        "permits_2mi_count": str(permits_2mi),
        "new_mf_permits_count": str(new_mf_count),
        "commercial_permits_count": str(commercial_alt_count),
        "nearest_permit_distance": nearest_display,
        "permits_context_footnote": permits_context_footnote,
        "permit_activity_bars": permit_activity_bars,
        "permit_chart_footnote": permit_chart_footnote,
        # Zoning stubs — future sprint
        "comp_plan_designation": "See zoning report",
        "growth_center_distance": "N/A",
        "upzoning_risk": "Not assessed",
        "zoning_narrative": "Zoning intelligence module pending.",
        "zoning_code_slash": "N/A",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_SAFE_DEFAULTS = {
    "dev_pressure_score": "0",
    "dev_pressure_label": "Data Unavailable",
    "dev_pressure_narrative": "Development pressure data temporarily unavailable.",
    "dev_formula_components": [],
    "total_county_permits": "0",
    "permits_2mi_count": "0",
    "new_mf_permits_count": "0",
    "commercial_permits_count": "0",
    "nearest_permit_distance": "N/A",
    "permits_context_footnote": "",
    "permit_activity_bars": [],
    "permit_chart_footnote": "",
    "comp_plan_designation": "N/A",
    "growth_center_distance": "N/A",
    "upzoning_risk": "N/A",
    "zoning_narrative": "",
    "zoning_code_slash": "N/A",
}


def build_development_context(
    lat: float,
    lon: float,
    county: str,
    radius_miles: float = 2.0,
) -> dict:
    """Build development-intelligence context for the OM template.

    Args:
        lat: Property latitude.
        lon: Property longitude.
        county: 'fairfax' or 'loudoun'.
        radius_miles: Analysis radius (default 2.0 miles per template spec).

    Returns:
        Dict with all keys expected by development_intelligence.html.
    """
    try:
        if county == "fairfax":
            return _build_fairfax(lat, lon, radius_miles)
        else:
            return _build_loudoun(lat, lon, radius_miles)
    except Exception as exc:
        logger.warning(
            "Failed to build development context: %s", exc, exc_info=True,
        )
        return dict(_SAFE_DEFAULTS)
