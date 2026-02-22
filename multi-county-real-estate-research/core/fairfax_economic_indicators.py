"""
Economic Indicators Module for Fairfax County App

Handles:
- Major employers data (static JSON)
- Labor force participation rate (Census ACS)
- Industry employment mix (Census ACS)
- BLS labor market data (unemployment, labor force trends)

Usage:
    from core.fairfax_economic_indicators import (
        get_lfpr_data,
        get_industry_mix_data,
        fetch_bls_data,
        load_major_employers,
        get_employers_by_year,
        get_employer_trends
    )
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st

from core.api_config import get_api_key


# =============================================================================
# CONFIGURATION
# =============================================================================

FAIRFAX_FIPS = {"state": "51", "county": "059"}

# Census ACS 5-Year Dataset
CENSUS_ACS_YEAR = "2023"
CENSUS_ACS_BASE = "https://api.census.gov/data/2023/acs/acs5/profile"

# BLS API Configuration
BLS_API_BASE = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# BLS LAUS Series IDs for Fairfax County (51059)
BLS_SERIES = {
    "labor_force": "LAUCN510590000000006",
    "employment": "LAUCN510590000000005",
    "unemployment_rate": "LAUCN510590000000003",
}

# Cache directory
CACHE_DIR = "cache/economic_indicators"

# Data file path
EMPLOYERS_JSON_PATH = "data/fairfax/major_employers.json"


# =============================================================================
# MAJOR EMPLOYERS (Static Data from CAFR)
# =============================================================================

@st.cache_data
def load_major_employers() -> Dict[str, Any]:
    """Load major employers data from JSON file."""
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), EMPLOYERS_JSON_PATH)

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)

    # Fallback: return empty structure
    return {"employers_by_year": {}, "trends": {}}


def get_employers_by_year(year: int) -> List[Dict[str, Any]]:
    """
    Get employer list for a specific year.

    Args:
        year: The fiscal year (e.g., 2025)

    Returns:
        List of employer dictionaries with rank, name, employees, etc.
    """
    data = load_major_employers()
    year_data = data.get("employers_by_year", {}).get(str(year), {})
    employers = year_data.get("employers", [])

    # Format for display
    formatted = []
    for emp in employers:
        employees = emp.get("employees")
        employees_range = emp.get("employees_range", "")

        formatted.append({
            "rank": emp.get("rank", 0),
            "name": emp.get("name", ""),
            "employees_display": f"{employees:,}" if employees else employees_range,
            "pct_of_total": emp.get("pct", 0),
            "industry": _infer_industry(emp.get("name", ""))
        })

    return formatted


def _infer_industry(employer_name: str) -> str:
    """Infer industry category from employer name."""
    name_lower = employer_name.lower()

    if "federal government" in name_lower:
        return "Federal Government"
    elif "school" in name_lower or "fcps" in name_lower:
        return "Education"
    elif "george mason" in name_lower or "university" in name_lower:
        return "Education"
    elif "fairfax county" in name_lower or "county of fairfax" in name_lower:
        return "Government"
    elif "inova" in name_lower or "health system" in name_lower or "hospital" in name_lower or "medical" in name_lower:
        return "Healthcare"
    elif "booz allen" in name_lower:
        return "Professional Services"
    elif "science applications" in name_lower or "saic" in name_lower or "leidos" in name_lower:
        return "Professional Services"
    elif "amazon" in name_lower:
        return "Technology"
    elif "computer science corporation" in name_lower or "mitre" in name_lower:
        return "Technology"
    elif "capital one" in name_lower or "navy federal" in name_lower:
        return "Financial Services"
    elif "federal home loan" in name_lower or "freddie mac" in name_lower:
        return "Financial Services"
    elif "general dynamics" in name_lower or "northrop" in name_lower or "lockheed" in name_lower:
        return "Defense"
    else:
        return "Other"


def get_employer_trends() -> Dict[str, Any]:
    """
    Calculate key employer trends for highlights box.

    Returns:
        Dictionary with FCPS growth, Inova growth, notable entries/exits.
    """
    data = load_major_employers()
    summary = data.get("summary", {})
    key_trends = summary.get("key_trends", {})
    fcps_employment = summary.get("fcps_employment", {})
    inova_employment = summary.get("inova_employment", {})

    # Calculate FCPS growth (data starts 2009)
    fcps_start = fcps_employment.get("2009", 0)
    fcps_end = fcps_employment.get("2025", 0)
    fcps_pct = ((fcps_end - fcps_start) / fcps_start) * 100 if fcps_start else 0

    # Calculate Inova growth (dramatic expansion)
    inova_start = inova_employment.get("2009", 0)
    inova_end = inova_employment.get("2025", 0)
    inova_pct = ((inova_end - inova_start) / inova_start) * 100 if inova_start else 0

    return {
        "fcps_growth": {
            "start_year": 2009,
            "start_employees": fcps_start,
            "end_year": 2025,
            "end_employees": fcps_end,
            "pct_change": round(fcps_pct, 1)
        },
        "inova_growth": {
            "start_year": 2009,
            "start_employees": inova_start,
            "end_year": 2025,
            "end_employees": inova_end,
            "pct_change": round(inova_pct, 1)
        },
        "notable_entries": key_trends.get("notable_entries", []),
        "notable_exits": key_trends.get("notable_exits", []),
        "notable_declines": key_trends.get("notable_declines", [])
    }


# =============================================================================
# CENSUS DATA (LFPR & Industry Mix)
# =============================================================================

@st.cache_data(ttl=86400*7)  # 7-day cache
def fetch_census_economic_data() -> Dict[str, Dict[str, Any]]:
    """
    Fetch LFPR and industry mix from Census ACS 5-Year.

    Returns:
        Dictionary with data for fairfax, virginia, and usa.
    """
    api_key = get_api_key("CENSUS_API_KEY")
    if not api_key:
        return {}

    # Variables to fetch
    variables = [
        "NAME",
        "DP03_0002PE",  # LFPR (percent)
        "DP03_0002PM",  # LFPR MOE
        # Industry employment percentages
        "DP03_0033PE",  # Agriculture/Mining
        "DP03_0034PE",  # Construction
        "DP03_0035PE",  # Manufacturing
        "DP03_0036PE",  # Wholesale Trade
        "DP03_0037PE",  # Retail Trade
        "DP03_0038PE",  # Transportation/Utilities
        "DP03_0039PE",  # Information
        "DP03_0040PE",  # Finance/Insurance/Real Estate
        "DP03_0041PE",  # Professional/Scientific
        "DP03_0042PE",  # Education/Healthcare
        "DP03_0043PE",  # Arts/Entertainment/Food
        "DP03_0044PE",  # Other Services
        "DP03_0045PE",  # Public Administration
    ]

    results = {}

    # Fetch for Fairfax, Virginia, USA
    geographies = [
        ("fairfax", "county:059", "state:51"),
        ("virginia", "state:51", None),
        ("usa", "us:1", None),
    ]

    for geo_name, geo_for, geo_in in geographies:
        try:
            params = {
                "get": ",".join(variables),
                "for": geo_for,
                "key": api_key
            }
            if geo_in:
                params["in"] = geo_in

            response = requests.get(CENSUS_ACS_BASE, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                results[geo_name] = _parse_census_response(data)
        except Exception as e:
            # Silently continue - we'll show what data we have
            pass

    return results


def _parse_census_response(data: List) -> Dict[str, Any]:
    """Parse Census API response into structured dict."""
    if not data or len(data) < 2:
        return {}

    headers = data[0]
    values = data[1]

    result = {}
    for i, header in enumerate(headers):
        try:
            val = values[i]
            if val is None or val == "" or val == "-888888888" or val == "-666666666":
                result[header] = None
            else:
                result[header] = float(val)
        except (ValueError, TypeError):
            result[header] = values[i]

    return result


def get_lfpr_data() -> Dict[str, Any]:
    """
    Get Labor Force Participation Rate with comparisons.

    Returns:
        Dictionary with LFPR for Fairfax, Virginia, USA, and deltas.
    """
    census_data = fetch_census_economic_data()

    fairfax_lfpr = census_data.get("fairfax", {}).get("DP03_0002PE")
    va_lfpr = census_data.get("virginia", {}).get("DP03_0002PE")
    usa_lfpr = census_data.get("usa", {}).get("DP03_0002PE")

    return {
        "fairfax": fairfax_lfpr,
        "virginia": va_lfpr,
        "usa": usa_lfpr,
        "fairfax_vs_va": round(fairfax_lfpr - va_lfpr, 1) if fairfax_lfpr and va_lfpr else None,
        "fairfax_vs_usa": round(fairfax_lfpr - usa_lfpr, 1) if fairfax_lfpr and usa_lfpr else None,
        "source": "Census ACS 2019-2023 5-Year Estimates"
    }


def get_industry_mix_data() -> Dict[str, Any]:
    """
    Get industry employment percentages for chart.

    Returns:
        Dictionary with industries list and source.
    """
    census_data = fetch_census_economic_data()

    # Industry variable mapping (ordered by typical Fairfax percentages)
    industry_vars = {
        "DP03_0041PE": "Professional/Scientific",
        "DP03_0042PE": "Education/Healthcare",
        "DP03_0045PE": "Public Administration",
        "DP03_0040PE": "Finance/Insurance/RE",
        "DP03_0037PE": "Retail Trade",
        "DP03_0043PE": "Arts/Entertainment/Food",
        "DP03_0034PE": "Construction",
        "DP03_0044PE": "Other Services",
        "DP03_0035PE": "Manufacturing",
        "DP03_0038PE": "Transportation/Utilities",
        "DP03_0039PE": "Information (Tech)",
        "DP03_0036PE": "Wholesale Trade",
        "DP03_0033PE": "Agriculture/Mining"
    }

    industries = []
    for var, name in industry_vars.items():
        industries.append({
            "sector": name,
            "fairfax": census_data.get("fairfax", {}).get(var),
            "virginia": census_data.get("virginia", {}).get(var),
            "usa": census_data.get("usa", {}).get(var)
        })

    # Sort by Fairfax percentage (descending)
    industries.sort(key=lambda x: x["fairfax"] or 0, reverse=True)

    return {
        "industries": industries,
        "source": "Census ACS 2019-2023 5-Year Estimates"
    }


# =============================================================================
# BLS DATA (Labor Force & Unemployment)
# =============================================================================

@st.cache_data(ttl=86400*7)  # 7-day cache
def fetch_bls_data() -> Dict[str, Any]:
    """
    Fetch labor force and unemployment from BLS LAUS.

    Returns:
        Dictionary with labor_force and unemployment_rate data.
    """
    api_key = get_api_key("BLS_API_KEY")

    series_ids = [
        BLS_SERIES["labor_force"],
        BLS_SERIES["unemployment_rate"],
    ]

    headers = {'Content-type': 'application/json'}
    current_year = datetime.now().year

    payload = {
        "seriesid": series_ids,
        "startyear": str(current_year - 2),
        "endyear": str(current_year),
    }

    # Add registration key if available (increases rate limit)
    if api_key:
        payload["registrationkey"] = api_key

    try:
        response = requests.post(
            BLS_API_BASE,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            return _parse_bls_response(response.json())
    except Exception as e:
        pass

    return {}


def _parse_bls_response(data: Dict) -> Dict[str, Any]:
    """Parse BLS API response into structured format."""
    if data.get("status") != "REQUEST_SUCCEEDED":
        return {}

    results = {}

    for series in data.get("Results", {}).get("series", []):
        series_id = series.get("seriesID", "")
        data_points = series.get("data", [])

        if not data_points:
            continue

        # Get most recent value
        current = data_points[0]
        current_value = float(current.get("value", 0))
        current_date = f"{current.get('periodName', '')} {current.get('year', '')}"

        # Find same month last year for YoY comparison
        current_month = current.get("period", "")
        current_year = int(current.get("year", 0))
        prior_year_value = None

        for point in data_points:
            if point.get("period") == current_month and int(point.get("year", 0)) == current_year - 1:
                prior_year_value = float(point.get("value", 0))
                break

        # Calculate YoY change
        yoy_change = None
        if prior_year_value and prior_year_value > 0:
            if "000003" in series_id:  # Unemployment rate - use absolute difference
                yoy_change = current_value - prior_year_value
            else:  # Labor force - use percentage change
                yoy_change = ((current_value - prior_year_value) / prior_year_value) * 100

        # Identify series and store
        if "000006" in series_id:  # Labor force
            results["labor_force"] = {
                "value": current_value,
                "date": current_date,
                "yoy_change": round(yoy_change, 1) if yoy_change is not None else None
            }
        elif "000003" in series_id:  # Unemployment rate
            results["unemployment_rate"] = {
                "value": current_value,
                "date": current_date,
                "yoy_change": round(yoy_change, 2) if yoy_change is not None else None
            }

    results["source"] = "BLS Local Area Unemployment Statistics"
    results["note"] = "Not seasonally adjusted"

    return results
