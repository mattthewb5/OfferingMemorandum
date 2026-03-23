"""
Employers Context Builder for OM Generator

Wires major employer data from ACFR JSON files into the template variable
structure expected by context_sample.py / market_overview.html.

Supports Fairfax County and Loudoun County.

Usage:
    from employers_context import build_employers_context
    emp = build_employers_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import json
import os
import sys
import types
from pathlib import Path

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# Data paths
_DATA_ROOT = _REPO_ROOT / "multi-county-real-estate-research" / "data"
_FAIRFAX_EMPLOYERS = _DATA_ROOT / "fairfax" / "major_employers.json"
_LOUDOUN_EMPLOYERS = _DATA_ROOT / "loudoun" / "major_employers.json"

FAIRFAX_EMPLOYER_DOMAINS = {
    "federal government": "usa.gov",
    "fairfax county public schools": "fcps.edu",
    "inova health system": "inova.org",
    "fairfax county government": "fairfaxcounty.gov",
    "george mason university": "gmu.edu",
    "booz allen hamilton": "boozallen.com",
    "amazon": "amazon.com",
    "capital one": "capitalone.com",
    "science applications international corporation": "saic.com",
    "federal home loan mortgage": "freddiemac.com",
}

LOUDOUN_EMPLOYER_DOMAINS = {
    "loudoun county public schools": "lcps.org",
    "county of loudoun": "loudoun.gov",
    "amazon": "amazon.com",
    "amazon web services": "aws.amazon.com",
    "microsoft": "microsoft.com",
    "google": "google.com",
    "meta": "meta.com",
    "equinix": "equinix.com",
    "digital realty": "digitalrealty.com",
    "leidos": "leidos.com",
}


def _get_sort_key(emp: dict) -> int:
    """Extract a numeric employee count for sorting, handling mixed formats."""
    if 'employees' in emp and isinstance(emp['employees'], int):
        return emp['employees']
    if 'employees_range' in emp:
        parts = emp['employees_range'].replace(',', '').split('-')
        try:
            return int(parts[-1].strip())
        except (ValueError, IndexError):
            return 0
    return 0


def _format_employees(emp: dict) -> str:
    """Format employee count for display, handling int and range formats."""
    if 'employees' in emp and isinstance(emp['employees'], int):
        return f"{emp['employees']:,}"
    return emp.get('employees_range', 'N/A')


def _load_infer_industry(county: str):
    """Import the sector inference function for the given county."""
    # Mock streamlit to avoid the dependency (module-level import in source)
    # st.cache_data is used both as @st.cache_data and @st.cache_data(ttl=...)
    def _cache_data_mock(func=None, **kwargs):
        if func is not None:
            return func
        return lambda f: f

    st_mock = types.ModuleType('streamlit')
    st_mock.cache_data = _cache_data_mock
    if 'streamlit' not in sys.modules or not hasattr(sys.modules['streamlit'], '__file__'):
        sys.modules['streamlit'] = st_mock

    if county == 'fairfax':
        from core.fairfax_economic_indicators import _infer_industry
    else:
        from core.economic_indicators import _infer_industry
    return _infer_industry


def _graceful_default(county: str) -> dict:
    return {
        "employers": [],
        "employer_footnote": "Employer data temporarily unavailable.",
        "employers_data_year": None,
        "employers_county": county,
    }


def build_employers_context(lat: float, lon: float, county: str) -> dict:
    """
    Build the employers context dict for the OM template.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name ('fairfax' or 'loudoun')

    Returns:
        Dict with keys: employers (list), employer_footnote, employers_data_year,
        employers_county.
    """
    try:
        # Select data file
        path = _FAIRFAX_EMPLOYERS if county == 'fairfax' else _LOUDOUN_EMPLOYERS
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        employers_by_year = data.get('employers_by_year', {})
        if not employers_by_year:
            print("WARNING: No employers_by_year data found", file=sys.stderr)
            return _graceful_default(county)

        # Most recent year
        data_year = max(employers_by_year.keys())
        employers = employers_by_year[data_year].get('employers', [])

        if not employers:
            print(f"WARNING: No employers for year {data_year}", file=sys.stderr)
            return _graceful_default(county)

        # Load sector inference
        _infer_industry = _load_infer_industry(county)

        # Logo domain lookup
        domain_map = FAIRFAX_EMPLOYER_DOMAINS if county == 'fairfax' else LOUDOUN_EMPLOYER_DOMAINS
        logo_dev_token = os.environ.get("LOGO_DEV_TOKEN", "")

        # Sort by employee count descending, take top 10
        sorted_emps = sorted(employers, key=_get_sort_key, reverse=True)[:10]

        employer_list = []
        for i, emp in enumerate(sorted_emps):
            domain = domain_map.get(emp["name"].lower())
            logo_url = (
                f"https://img.logo.dev/{domain}?token={logo_dev_token}&size=20&format=png"
                if domain and logo_dev_token else None
            )
            employer_list.append({
                "rank": str(i + 1),
                "name": emp["name"],
                "sector": _infer_industry(emp["name"]),
                "employees": _format_employees(emp),
                "logo_url": logo_url,
            })

        return {
            "employers": employer_list,
            "employer_footnote": (
                f"Source: {county.title()} County Annual Comprehensive Financial "
                f"Report (ACFR), {data_year}. Employee counts represent full-time "
                f"equivalents where reported; ranges indicate privately held employers."
            ),
            "employers_data_year": data_year,
            "employers_county": county,
        }

    except Exception as e:
        print(f"WARNING in build_employers_context: {e}", file=sys.stderr)
        return _graceful_default(county)
