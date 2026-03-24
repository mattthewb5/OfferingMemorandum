"""
Development Context Builder for OM Generator

Wires building permit and development pressure data into the template variable
structure expected by context_sample.py / development_intelligence.html.

Supports Fairfax County (parquet-backed FairfaxPermitsAnalysis)
and Loudoun County (CSV-backed DevelopmentPressureAnalyzer).

Usage:
    from development_context import build_development_context
    dev = build_development_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import sys
from pathlib import Path

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# Loudoun permits CSV path
_LOUDOUN_PERMITS = (
    _REPO_ROOT / "multi-county-real-estate-research" / "data" / "loudoun"
    / "building_permits" / "loudoun_permits_with_infrastructure.csv"
)


def _score_label_color(score: int) -> tuple:
    """Map a development pressure score to a display label and color."""
    if score <= 25:
        return "Low \u00b7 Supply Constrained", "green"
    if score <= 60:
        return "Moderate", "yellow"
    return "High \u00b7 Active Pipeline", "red"


def _bar_color_for_pts(pts: float, max_pts: int) -> str:
    """Choose a CSS color variable based on how high the sub-score is."""
    ratio = pts / max(max_pts, 1)
    if ratio <= 0.35:
        return "var(--green)"
    if ratio <= 0.65:
        return "var(--amber)"
    return "var(--red)"


def _graceful_default(county: str) -> dict:
    """Return all required keys with safe fallback values."""
    return {
        "dev_pressure_score": "0",
        "dev_pressure_label": "Data Unavailable",
        "dev_pressure_cover_tag": "Low Dev. Pressure",
        "dev_pressure_badge_class": "badge-green",
        "dev_pressure_narrative": "Development pressure data temporarily unavailable.",
        "dev_formula_components": [
            {"name": "Permit Volume", "weight": "30%", "bar_width": "0%",
             "bar_color": "var(--green)", "score_label": "N/A"},
            {"name": "Permit Recency", "weight": "20%", "bar_width": "0%",
             "bar_color": "var(--green)", "score_label": "N/A"},
            {"name": "Permit Type", "weight": "20%", "bar_width": "0%",
             "bar_color": "var(--green)", "score_label": "N/A"},
            {"name": "Proximity", "weight": "15%", "bar_width": "0%",
             "bar_color": "var(--green)", "score_label": "N/A"},
            {"name": "Planning Zone", "weight": "15%", "bar_width": "0%",
             "bar_color": "#cccccc", "score_label": "Pending"},
        ],
        "total_county_permits": "N/A",
        "permits_2mi_count": "0",
        "new_mf_permits_count": "0",
        "commercial_permits_count": "0",
        "nearest_permit_distance": "N/A",
        "permits_context_footnote": "Permit data temporarily unavailable.",
        "permit_activity_bars": [
            {"label": "New Construction", "width": "0%", "count": "0", "fill_class": "bar-high"},
            {"label": "Commercial Alteration", "width": "0%", "count": "0", "fill_class": "bar-medium"},
            {"label": "Residential Renovation", "width": "0%", "count": "0", "fill_class": "bar-low"},
        ],
        "permit_chart_footnote": "Permit data temporarily unavailable.",
        "comp_plan_designation": "See zoning report",
        "growth_center_distance": "N/A",
        "upzoning_risk": "Not assessed",
        "zoning_narrative": "Zoning intelligence module pending.",
        "zoning_code_slash": "N/A",
    }


def _build_fairfax(lat: float, lon: float, radius_miles: float) -> dict:
    """Build development context from Fairfax permits data."""
    import pandas as pd
    from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

    analyzer = FairfaxPermitsAnalysis()
    nearby_df = analyzer.get_permits_near_point(
        lat, lon, radius_miles=radius_miles, months_back=24
    )

    total_county_permits = len(analyzer.permits)
    permits_2mi_count = len(nearby_df)

    # Categorize permits using permit_category column
    new_mf_count = 0
    commercial_new_count = 0
    commercial_alt_count = 0
    residential_reno_count = 0

    if not nearby_df.empty and 'permit_category' in nearby_df.columns:
        cat = nearby_df['permit_category']
        new_mf_count = int(cat.str.contains('residential_new', na=False).sum())
        commercial_new_count = int(cat.str.contains('commercial_new', na=False).sum())
        commercial_alt_count = int(cat.str.contains('commercial_renovation', na=False).sum())
        residential_reno_count = int(cat.str.contains('residential_renovation', na=False).sum())

    new_construction_count = new_mf_count + commercial_new_count

    # Nearest permit distance
    if not nearby_df.empty and 'distance_miles' in nearby_df.columns:
        nearest_dist = nearby_df['distance_miles'].min()
        nearest_permit_distance = f"{nearest_dist:.1f} miles"
    else:
        nearest_dist = radius_miles + 1
        nearest_permit_distance = f"> {radius_miles} miles"

    # Recency: fraction of permits from last 6 months
    recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=180)
    if not nearby_df.empty:
        recent = nearby_df[
            (nearby_df['issued_date'] >= recent_cutoff) |
            ((nearby_df['issued_date'].isna()) & (nearby_df['submitted_date'] >= recent_cutoff))
        ]
        recent_count = len(recent)
    else:
        recent_count = 0

    # Type-weighted score (same weights as FairfaxPermitsAnalysis)
    weighted_score = (
        new_mf_count * 8
        + commercial_new_count * 3
        + residential_reno_count * 0.3
        + commercial_alt_count * 0.5
    )

    # Compute sub-scores first — these ARE the headline
    sub = _compute_sub_scores(
        weighted_score=weighted_score,
        new_mf_count=new_mf_count,
        new_construction_count=new_construction_count,
        permits_2mi_count=permits_2mi_count,
        recent_count=recent_count,
        nearest_dist=nearest_dist,
    )
    score = sub["volume_pts"] + sub["recency_pts"] + sub["type_pts"] + sub["proximity_pts"] + sub["planning_pts"]

    # Trend from analyzer
    pressure = analyzer.calculate_development_pressure(
        lat, lon, radius_miles=radius_miles, months_back=24
    )
    trend = pressure["trend"]

    # Rating from score thresholds
    if score <= 25:
        rating = "Low"
    elif score <= 60:
        rating = "Moderate"
    else:
        rating = "High"

    return _assemble_result(
        score=score,
        rating=rating,
        trend=trend,
        total_county_permits=total_county_permits,
        permits_2mi_count=permits_2mi_count,
        new_mf_count=new_mf_count,
        new_construction_count=new_construction_count,
        commercial_alt_count=commercial_alt_count,
        residential_reno_count=residential_reno_count,
        nearest_permit_distance=nearest_permit_distance,
        radius_miles=radius_miles,
        county="fairfax",
        nearby_df=nearby_df,
        sub_scores=sub,
    )


def _build_loudoun(lat: float, lon: float, radius_miles: float) -> dict:
    """Build development context from Loudoun permits data."""
    from core.development_pressure_analyzer import DevelopmentPressureAnalyzer

    analyzer = DevelopmentPressureAnalyzer(permits_csv_path=str(_LOUDOUN_PERMITS))
    pressure = analyzer.analyze_development_pressure(
        lat, lon, radius_miles=radius_miles
    )
    nearby_permits = analyzer.find_nearby_permits(
        lat, lon, radius_miles=radius_miles
    )

    trend = pressure.trend
    total_county_permits = pressure.total_permits
    permits_2mi_count = pressure.permits_within_radius

    # Categorize Loudoun permits using work_class and permit_type fields
    new_mf_count = 0
    commercial_new_count = 0
    commercial_alt_count = 0
    residential_reno_count = 0

    for p in nearby_permits:
        combined = f"{p.permit_type} {p.work_class} {p.description}".lower()
        if any(kw in combined for kw in ('multi-family', 'apartment', 'townhouse')):
            if 'new' in combined:
                new_mf_count += 1
        if 'commercial' in combined and 'new' in combined:
            commercial_new_count += 1
        elif 'commercial' in combined and any(kw in combined for kw in ('alteration', 'renovation', 'remodel')):
            commercial_alt_count += 1
        elif any(kw in combined for kw in ('residential',)) and any(kw in combined for kw in ('alteration', 'renovation', 'remodel')):
            residential_reno_count += 1

    new_construction_count = new_mf_count + commercial_new_count

    # Nearest permit distance
    if nearby_permits:
        nearest_dist = min(p.distance_miles for p in nearby_permits)
        nearest_permit_distance = f"{nearest_dist:.1f} miles"
    else:
        nearest_dist = radius_miles + 1
        nearest_permit_distance = f"> {radius_miles} miles"

    # Recency: fraction of permits from last 6 months
    from datetime import datetime as dt, timedelta
    recent_cutoff = dt.now() - timedelta(days=180)
    recent_count = sum(
        1 for p in nearby_permits
        if p.issue_date and p.issue_date >= recent_cutoff
    )

    # Type-weighted score (same weights as Fairfax)
    weighted_score = (
        new_mf_count * 8
        + commercial_new_count * 3
        + residential_reno_count * 0.3
        + commercial_alt_count * 0.5
    )

    # Compute sub-scores first — these ARE the headline
    sub = _compute_sub_scores(
        weighted_score=weighted_score,
        new_mf_count=new_mf_count,
        new_construction_count=new_construction_count,
        permits_2mi_count=permits_2mi_count,
        recent_count=recent_count,
        nearest_dist=nearest_dist,
    )
    score = sub["volume_pts"] + sub["recency_pts"] + sub["type_pts"] + sub["proximity_pts"] + sub["planning_pts"]

    # Rating from score thresholds
    if score <= 25:
        rating = "Low"
    elif score <= 60:
        rating = "Moderate"
    else:
        rating = "High"

    return _assemble_result(
        score=score,
        rating=rating,
        trend=trend,
        total_county_permits=total_county_permits,
        permits_2mi_count=permits_2mi_count,
        new_mf_count=new_mf_count,
        new_construction_count=new_construction_count,
        commercial_alt_count=commercial_alt_count,
        residential_reno_count=residential_reno_count,
        nearest_permit_distance=nearest_permit_distance,
        radius_miles=radius_miles,
        county="loudoun",
        nearby_df=None,
        sub_scores=sub,
    )


def _compute_sub_scores(
    weighted_score: float,
    new_mf_count: int,
    new_construction_count: int,
    permits_2mi_count: int,
    recent_count: int,
    nearest_dist: float,
) -> dict:
    """Compute the 5 formula sub-scores that compose the headline score.

    The headline IS the sum of these components — no independent calculation.
    """

    # Volume component (30 pts max) — based on type-weighted permit score
    # Calibration: 10 new MF (~ws 220) → ~11 pts, 50+ new MF (~ws 550) → ~28 pts
    volume_pts = min(30, round(weighted_score * 0.05))

    # Recency component (20 pts max) — fraction of permits from last 6 months
    recent_ratio = recent_count / max(1, permits_2mi_count)
    recency_pts = min(20, round(recent_ratio * 25))

    # Type component (20 pts max) — new multifamily share of weighted score
    if weighted_score > 0:
        type_pts = min(20, round((new_mf_count * 8) / weighted_score * 20))
    else:
        type_pts = 0

    # Proximity component (15 pts max) — distance tiers
    if nearest_dist <= 0.25:
        proximity_pts = 15
    elif nearest_dist <= 0.5:
        proximity_pts = 12
    elif nearest_dist <= 1.0:
        proximity_pts = 8
    elif nearest_dist <= 1.5:
        proximity_pts = 4
    else:
        proximity_pts = 0

    # Planning Zone (15 pts max) — stubbed until zoning module ready
    planning_pts = 0

    return {
        "volume_pts": volume_pts,
        "recency_pts": recency_pts,
        "type_pts": type_pts,
        "proximity_pts": proximity_pts,
        "planning_pts": planning_pts,
    }


def _assemble_result(
    score: int,
    rating: str,
    trend: str,
    total_county_permits: int,
    permits_2mi_count: int,
    new_mf_count: int,
    new_construction_count: int,
    commercial_alt_count: int,
    residential_reno_count: int,
    nearest_permit_distance: str,
    radius_miles: float,
    county: str,
    nearby_df=None,
    sub_scores: dict = None,
) -> dict:
    """Assemble the full development context dict."""

    label, color = _score_label_color(score)

    sub = sub_scores or {
        "volume_pts": 0, "recency_pts": 0, "type_pts": 0,
        "proximity_pts": 0, "planning_pts": 0,
    }

    dev_formula_components = [
        {"name": "Permit Volume", "weight": "30%",
         "bar_width": f"{round(sub['volume_pts'] / 30 * 100)}%",
         "bar_color": _bar_color_for_pts(sub['volume_pts'], 30),
         "score_label": f"{sub['volume_pts']}/30"},
        {"name": "Permit Recency", "weight": "20%",
         "bar_width": f"{round(sub['recency_pts'] / 20 * 100)}%",
         "bar_color": _bar_color_for_pts(sub['recency_pts'], 20),
         "score_label": f"{sub['recency_pts']}/20"},
        {"name": "Permit Type", "weight": "20%",
         "bar_width": f"{round(sub['type_pts'] / 20 * 100)}%",
         "bar_color": _bar_color_for_pts(sub['type_pts'], 20),
         "score_label": f"{sub['type_pts']}/20"},
        {"name": "Proximity", "weight": "15%",
         "bar_width": f"{round(sub['proximity_pts'] / 15 * 100)}%",
         "bar_color": _bar_color_for_pts(sub['proximity_pts'], 15),
         "score_label": f"{sub['proximity_pts']}/15"},
        {"name": "Planning Zone", "weight": "15%",
         "bar_width": f"{round(sub['planning_pts'] / 15 * 100)}%",
         "bar_color": _bar_color_for_pts(sub['planning_pts'], 15) if sub['planning_pts'] > 0 else "#cccccc",
         "score_label": f"{sub['planning_pts']}/15" if sub['planning_pts'] > 0 else "Pending"},
    ]

    # Permit activity bars
    total = max(1, permits_2mi_count)
    permit_activity_bars = [
        {"label": "New Construction",
         "count": str(new_construction_count),
         "width": f"{round((new_construction_count / total) * 100)}%",
         "fill_class": "bar-primary"},
        {"label": "Commercial Alteration",
         "count": str(commercial_alt_count),
         "width": f"{round((commercial_alt_count / total) * 100)}%",
         "fill_class": "bar-primary"},
        {"label": "Residential Renovation",
         "count": str(residential_reno_count),
         "width": f"{round((residential_reno_count / total) * 100)}%",
         "fill_class": "bar-light"},
    ]

    # Narrative
    if new_mf_count == 0:
        narrative = (
            f"Zero new multifamily permits have been filed within "
            f"{radius_miles} miles in the trailing 24 months. "
            f"{county.title()} County\u2019s development review process creates "
            f"a substantial barrier to competitive supply additions \u2014 "
            f"protecting in-place NOI and supporting rent growth."
        )
    else:
        narrative = (
            f"{permits_2mi_count} permits recorded within {radius_miles} "
            f"miles over the trailing 24 months, including {new_mf_count} "
            f"new multifamily permit{'s' if new_mf_count != 1 else ''}."
        )

    # Footnote
    permits_context_footnote = (
        f"{permits_2mi_count} permits within {radius_miles}-mile radius vs. "
        f"{county.title()} County permit database of {total_county_permits:,} "
        f"total permits. "
        f"{'Zero new' if new_mf_count == 0 else str(new_mf_count)} multifamily "
        f"permit{'s' if new_mf_count != 1 else ''} filed within "
        f"{radius_miles} miles in the trailing 24 months."
    )

    chart_footnote = (
        f"Commercial alteration permits indicate area economic activity without "
        f"introducing residential competition. Total: {permits_2mi_count} permits "
        f"within {radius_miles}-mi radius, 24-month period."
    )

    return {
        "dev_pressure_score": str(score),
        "dev_pressure_label": f"{rating} Development Pressure",
        "dev_pressure_cover_tag": f"{rating[:3]}. Dev. Pressure" if rating == "Moderate" else f"{rating} Dev. Pressure",
        "dev_pressure_badge_class": "badge-green" if rating == "Low" else "badge-amber" if rating == "Moderate" else "badge-red",
        "dev_pressure_narrative": narrative,
        "dev_formula_components": dev_formula_components,
        "total_county_permits": f"{total_county_permits:,}",
        "permits_2mi_count": str(permits_2mi_count),
        "new_mf_permits_count": str(new_mf_count),
        "commercial_permits_count": str(commercial_alt_count),
        "nearest_permit_distance": nearest_permit_distance,
        "permits_context_footnote": permits_context_footnote,
        "permit_activity_bars": permit_activity_bars,
        "permit_chart_footnote": chart_footnote,
        "comp_plan_designation": "See zoning report",
        "growth_center_distance": "N/A",
        "upzoning_risk": "Not assessed",
        "zoning_narrative": "Zoning intelligence module pending.",
        "zoning_code_slash": "N/A",
    }


def build_development_context(
    lat: float, lon: float, county: str, radius_miles: float = 2.0
) -> dict:
    """
    Build the development intelligence context dict for the OM template.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name ('fairfax' or 'loudoun')
        radius_miles: Search radius in miles (default: 2.0)

    Returns:
        Dict with all keys matching context_sample.py lines 274-320.
    """
    try:
        if county == 'fairfax':
            return _build_fairfax(lat, lon, radius_miles)
        elif county == 'loudoun':
            return _build_loudoun(lat, lon, radius_miles)
        else:
            print(f"WARNING: Unknown county '{county}' for development context",
                  file=sys.stderr)
            return _graceful_default(county)
    except Exception as e:
        print(f"WARNING in build_development_context: {e}", file=sys.stderr)
        return _graceful_default(county)
