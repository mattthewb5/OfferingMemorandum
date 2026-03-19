"""
Employers Context Builder for OM Generator

Loads major employer data from county ACFR JSON files and applies
sector classification using existing _infer_industry() functions.

Supports Fairfax County and Loudoun County.

Usage:
    from employers_context import build_employers_context
    ctx = build_employers_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# The economic indicator modules import streamlit at module level for
# @st.cache_data.  Provide a lightweight shim so we can import
# _infer_industry without pulling in the full streamlit package.
if "streamlit" not in sys.modules:
    import types

    _st = types.ModuleType("streamlit")
    _st.cache_data = lambda f=None, **kw: f if f else (lambda fn: fn)
    sys.modules["streamlit"] = _st

# Data paths
_DATA_ROOT = _REPO_ROOT / "multi-county-real-estate-research" / "data"
_FAIRFAX_EMPLOYERS_JSON = _DATA_ROOT / "fairfax" / "major_employers.json"
_LOUDOUN_EMPLOYERS_JSON = _DATA_ROOT / "loudoun" / "major_employers.json"


def _get_sort_key(emp: dict) -> int:
    """Extract a numeric sort key from an employer record.

    Handles both integer employee counts and string ranges like '2,500-5,000'.
    """
    if "employees" in emp and isinstance(emp["employees"], (int, float)):
        return int(emp["employees"])
    if "employees_range" in emp:
        parts = emp["employees_range"].replace(",", "").split("-")
        try:
            return int(parts[-1].strip())
        except (ValueError, IndexError):
            return 0
    return 0


def _format_employees(emp: dict) -> str:
    """Format employee count for display, preserving ranges as-is."""
    if "employees" in emp and isinstance(emp["employees"], (int, float)):
        return f"{int(emp['employees']):,}"
    return emp.get("employees_range", "N/A")


def build_employers_context(lat: float, lon: float, county: str) -> dict:
    """Build employer context for the OM template.

    Args:
        lat: Property latitude (unused, kept for consistent interface).
        lon: Property longitude (unused, kept for consistent interface).
        county: 'fairfax' or 'loudoun'.

    Returns:
        Dict with keys: employers, employer_footnote, employers_data_year,
        employers_county.
    """
    _fail = {
        "employers": [],
        "employer_footnote": "Employer data temporarily unavailable.",
        "employers_data_year": None,
        "employers_county": county,
    }
    try:
        # Route to the correct _infer_industry implementation
        if county == "fairfax":
            from core.fairfax_economic_indicators import _infer_industry
            json_path = _FAIRFAX_EMPLOYERS_JSON
        else:
            from core.economic_indicators import _infer_industry
            json_path = _LOUDOUN_EMPLOYERS_JSON

        if not json_path.exists():
            logger.warning("Employers JSON not found: %s", json_path)
            return _fail

        with open(json_path, "r") as f:
            data = json.load(f)

        employers_by_year = data.get("employers_by_year", {})
        if not employers_by_year:
            logger.warning("No employer year data in %s", json_path)
            return _fail

        # Most recent year
        data_year = max(employers_by_year.keys())
        year_data = employers_by_year[data_year]
        employers = year_data.get("employers", [])

        # Sort by employee count (descending), take top 10
        sorted_emps = sorted(employers, key=_get_sort_key, reverse=True)[:10]

        result_employers = [
            {
                "rank": str(i + 1),
                "name": emp["name"],
                "sector": _infer_industry(emp["name"]),
                "employees": _format_employees(emp),
            }
            for i, emp in enumerate(sorted_emps)
        ]

        footnote = (
            f"Source: {county.title()} County Annual Comprehensive Financial "
            f"Report (ACFR), {data_year}. Employee counts represent full-time "
            f"equivalents where reported; ranges indicate privately held employers."
        )

        return {
            "employers": result_employers,
            "employer_footnote": footnote,
            "employers_data_year": data_year,
            "employers_county": county,
        }

    except Exception as exc:
        logger.warning("Failed to build employers context: %s", exc, exc_info=True)
        return _fail
