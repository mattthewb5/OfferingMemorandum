"""
Schools Context Builder for OM Generator

Wires fairfax_schools_analysis.py and fairfax_school_performance_analysis.py
output into the template variable structure expected by context_sample.py /
location_analysis.html.

Usage:
    from schools_context import build_schools_context
    schools_dict = build_schools_context(lat=38.8462, lon=-77.3064)
"""

import sys
import pandas as pd
from pathlib import Path

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
from core.fairfax_school_performance_analysis import FairfaxSchoolPerformanceAnalysis

# Virginia statewide SOL averages (VDOE data, used for both Loudoun & Fairfax)
_STATE_AVG_CSV = (
    _REPO_ROOT
    / "multi-county-real-estate-research"
    / "data"
    / "loudoun"
    / "school_performance_trends_with_state_avg.csv"
)

# Maps get_assigned_schools() keys to display labels and School_Type codes
_LEVEL_MAP = {
    "elementary": {"label": "Elementary", "school_type": "Elem"},
    "middle": {"label": "Middle School", "school_type": "Middle"},
    "high": {"label": "High School", "school_type": "High"},
}


def _load_state_averages() -> pd.DataFrame:
    """Load Virginia statewide SOL averages (School_ID == 999999)."""
    df = pd.read_csv(_STATE_AVG_CSV)
    return df[df["School_ID"] == 999999][
        ["School_Type", "Year", "Overall_Pass_Rate"]
    ].copy()


def _get_state_avg(
    state_df: pd.DataFrame, school_type: str, year: str
) -> float | None:
    """Look up the state average for a given school type and year.

    Falls back to the most recent available year if no exact match.
    """
    match = state_df[
        (state_df["School_Type"] == school_type) & (state_df["Year"] == year)
    ]
    if len(match) > 0:
        return float(match.iloc[0]["Overall_Pass_Rate"])

    # Fallback: most recent year for this school type
    fallback = (
        state_df[state_df["School_Type"] == school_type]
        .sort_values("Year", ascending=False)
    )
    if len(fallback) > 0:
        return float(fallback.iloc[0]["Overall_Pass_Rate"])

    return None


def build_schools_context(lat: float, lon: float) -> dict:
    """
    Build the schools context dict matching the structure in context_sample.py.

    Args:
        lat: Property latitude
        lon: Property longitude

    Returns:
        Dict with keys: schools (list of dicts), school_footnote (str)
    """
    schools_analyzer = FairfaxSchoolsAnalysis()
    perf_analyzer = FairfaxSchoolPerformanceAnalysis()
    state_df = _load_state_averages()

    assigned = schools_analyzer.get_assigned_schools(lat, lon)

    schools = []
    years_used = set()

    for level_key, meta in _LEVEL_MAP.items():
        assignment = assigned.get(level_key)
        if assignment is None:
            continue

        school_name = assignment["school_name"]
        perf = perf_analyzer.get_school_performance(school_name)

        # Zone data may return short names (e.g. "Daniels Run") while
        # performance data uses full names ("Daniels Run Elementary").
        # Retry with the fuzzy suggestion if initial lookup fails.
        if not perf.get("found") and perf.get("suggestion"):
            perf = perf_analyzer.get_school_performance(perf["suggestion"])

        if not perf.get("found"):
            continue

        # Use the canonical name from the performance database
        school_name = perf["school_name"]

        sol_pass = perf["recent_overall_pass_rate"]
        year = perf["most_recent_year"]
        years_used.add(year)

        state_avg = _get_state_avg(state_df, meta["school_type"], year)

        # Format values
        sol_pass_rounded = round(sol_pass)
        sol_pass_str = f"{sol_pass_rounded}%"

        if state_avg is not None:
            state_avg_rounded = round(state_avg)
            state_avg_str = f"{state_avg_rounded}%"
            delta = sol_pass_rounded - state_avg_rounded
            delta_str = f"+{delta}%" if delta >= 0 else f"{delta}%"
        else:
            state_avg_str = "N/A"
            delta_str = "N/A"

        schools.append(
            {
                "level": meta["label"],
                "name": school_name,
                "sol_pass": sol_pass_str,
                "state_avg": state_avg_str,
                "delta": delta_str,
            }
        )

    # Build footnote
    year_display = ", ".join(sorted(years_used)) if years_used else "N/A"
    school_footnote = (
        f"Multi-year SOL pass rate trends available in Data Appendix. "
        f"School quality is the #1 stated retention driver for family renters "
        f"in Fairfax County. Source: Virginia DOE ({year_display})."
    )

    return {
        "schools": schools,
        "school_footnote": school_footnote,
    }
