"""
Healthcare Context Builder for OM Generator

Wires healthcare facility data into the template variable structure
expected by context_sample.py / location_analysis.html.

Supports Fairfax County (parquet-backed FairfaxHealthcareAnalysis)
and Loudoun County (GeoJSON + CMS CSV inline parsing).

Usage:
    from healthcare_context import build_healthcare_context
    hc = build_healthcare_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import csv
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

# Data paths
_DATA_ROOT = _REPO_ROOT / "multi-county-real-estate-research" / "data"
_FAIRFAX_MATERNITY = _DATA_ROOT / "fairfax" / "healthcare" / "maternity_hospitals.json"
_LOUDOUN_MATERNITY = _DATA_ROOT / "loudoun" / "healthcare" / "maternity_hospitals.json"
_LOUDOUN_GEOJSON = _DATA_ROOT / "loudoun" / "healthcare" / "Loudoun_Hospitals_and_Urgent_Care (1).geojson"
_CMS_CSV = _DATA_ROOT / "loudoun" / "healthcare" / "CMS_Hospital_28dec25.csv"
_FAIRFAX_EMPLOYERS = _DATA_ROOT / "fairfax" / "major_employers.json"
_LOUDOUN_EMPLOYERS = _DATA_ROOT / "loudoun" / "major_employers.json"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two lat/lon points."""
    R = 3959  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _get_drive_time(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
    distance_miles: float,
) -> str:
    """Get drive time via Google Distance Matrix API, with estimation fallback."""
    try:
        import googlemaps
        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if api_key:
            gmaps = googlemaps.Client(key=api_key)
            result = gmaps.distance_matrix(
                origins=[f"{origin_lat},{origin_lon}"],
                destinations=[f"{dest_lat},{dest_lon}"],
                mode="driving",
            )
            element = result['rows'][0]['elements'][0]
            if element['status'] == 'OK':
                minutes = round(element['duration']['value'] / 60)
                return f"{minutes} min"
    except Exception:
        pass

    # Fallback: estimate from straight-line distance
    est_minutes = round((distance_miles * 2.0) + 3)
    return f"~{est_minutes} min (est.)"


def _get_pharmacy_count(lat: float, lon: float, radius_miles: float = 1.0) -> Optional[int]:
    """Count nearby pharmacies via Google Places API (New)."""
    try:
        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if not api_key:
            return None

        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName",
            "Content-Type": "application/json",
        }
        body = {
            "includedTypes": ["pharmacy"],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_miles * 1609.34,
                }
            },
        }
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        return len(resp.json().get("places", []))
    except Exception:
        return None


def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _match_maternity(hospitals: list, primary_name: str) -> Optional[dict]:
    """Find a maternity hospital entry by fuzzy name match."""
    primary_lower = primary_name.lower()
    for h in hospitals:
        if h["name"].lower() in primary_lower or primary_lower in h["name"].lower():
            return h
    # Fallback: partial word overlap
    primary_words = set(primary_lower.split())
    for h in hospitals:
        h_words = set(h["name"].lower().split())
        if len(primary_words & h_words) >= 2:
            return h
    return None


def _get_employee_count(county: str) -> str:
    """Get Inova employee count from major employers JSON."""
    try:
        path = _FAIRFAX_EMPLOYERS if county == 'fairfax' else _LOUDOUN_EMPLOYERS
        data = _load_json(path)
        years = sorted(data.get("employers_by_year", {}).keys(), reverse=True)
        if not years:
            return "N/A"
        employers = data["employers_by_year"][years[0]].get("employers", [])
        for emp in employers:
            if "inova" in emp.get("name", "").lower():
                # Fairfax uses integer "employees", Loudoun uses string "employees_range"
                count = emp.get("employees")
                if count and isinstance(count, (int, float)) and count >= 1000:
                    return f"{int(count):,}+"
                emp_range = emp.get("employees_range", "")
                if emp_range:
                    return emp_range
                if count:
                    return str(count)
    except Exception:
        pass
    return "N/A"


def _format_certifications(cms_rating, leapfrog_grade: Optional[str] = None) -> str:
    """Build certification string for template."""
    parts = []
    if cms_rating is not None:
        try:
            rating = int(float(cms_rating))
            parts.append(f"CMS {rating}-Star Rating")
        except (ValueError, TypeError):
            pass
    if leapfrog_grade:
        parts.append(f"Leapfrog Safety Grade {leapfrog_grade}")
    if not parts:
        parts.append("CMS Rated Facility")
    return " \u00b7 ".join(parts)


def _score_label(score: int) -> str:
    if score >= 85:
        return "Top Tier"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Moderate"
    elif score >= 40:
        return "Limited"
    return "Below Average"


def _graceful_degradation() -> dict:
    return {
        "healthcare": {
            "primary_label": "HEALTHCARE DATA UNAVAILABLE",
            "name": "Data pending for this county",
            "distance": "\u2014",
            "drive_time": "\u2014",
            "certifications": "\u2014",
            "births_per_year": "\u2014",
            "csection_rate": "\u2014",
            "employee_count": "\u2014",
            "urgent_care_count": "\u2014",
            "pharmacy_count": "\u2014",
            "total_facilities": "\u2014",
            "score": "\u2014",
        },
        "hospital_lat": None,
        "hospital_lon": None,
    }


# ---------------------------------------------------------------------------
# Fairfax path
# ---------------------------------------------------------------------------

def _build_fairfax(lat: float, lon: float) -> dict:
    from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
    import pandas as pd

    analyzer = FairfaxHealthcareAnalysis()

    # Access score
    # TODO: calibrate score thresholds against county-wide averages — same issue as crime score (23)
    access = analyzer.calculate_healthcare_access_score(lat, lon)
    score = access["score"]

    # All facilities near point
    nearby = analyzer.get_facilities_near_point(lat, lon, radius_miles=10)

    # Primary hospital: closest hospital with highest CMS rating
    hospitals = nearby[nearby["facility_type"] == "hospital"].copy()
    if hospitals.empty:
        return _graceful_degradation()

    # Prefer 5-star within 10 mi, else closest
    five_star = hospitals[hospitals["cms_rating"] == 5]
    if not five_star.empty:
        primary = five_star.iloc[0]
    else:
        primary = hospitals.iloc[0]

    primary_name = primary["name"]
    # Parquet stores names in ALL CAPS; title-case for display
    if primary_name == primary_name.upper():
        primary_name = primary_name.title()
    dist_miles = round(primary["distance_miles"], 1)
    primary_lat = primary["latitude"]
    primary_lon = primary["longitude"]

    # Certifications
    certifications = _format_certifications(
        primary.get("cms_rating"),
        primary.get("leapfrog_grade"),
    )

    # Drive time
    drive_time = _get_drive_time(lat, lon, primary_lat, primary_lon, dist_miles)

    # Maternity data
    births_str = "\u2014"
    csection_str = "\u2014"
    try:
        maternity_data = _load_json(_FAIRFAX_MATERNITY)
        match = _match_maternity(maternity_data.get("hospitals", []), primary_name)
        if match:
            m = match.get("maternity", {})
            births = m.get("live_births_annual")
            if births:
                births_str = f"{births:,}"
            csection = m.get("c_section_rate")
            if csection is not None:
                csection_str = f"{round(csection * 100)}%"
    except Exception:
        pass

    # Urgent care count within 3 miles
    uc_nearby = nearby[
        (nearby["facility_type"] == "urgent_care") & (nearby["distance_miles"] <= 3)
    ]
    uc_count = len(uc_nearby)

    # Pharmacy count
    pharm = _get_pharmacy_count(lat, lon, radius_miles=1.0)
    pharm_str = f"{pharm} within 1 mile" if pharm is not None else "N/A"

    # Employee count
    emp_count = _get_employee_count("fairfax")

    # Total facilities
    total = len(analyzer.facilities)

    return {
        "healthcare": {
            "primary_label": f"PRIMARY HOSPITAL \u2014 {primary_name.upper()}",
            "name": primary_name,
            "distance": f"{dist_miles} mi",
            "drive_time": drive_time,
            "certifications": certifications,
            "births_per_year": births_str,
            "csection_rate": csection_str,
            "employee_count": emp_count,
            "urgent_care_count": f"{uc_count} within 3 miles",
            "pharmacy_count": pharm_str,
            "total_facilities": f"{total} Fairfax County",
            "score": f"{score}/100 {_score_label(score)}",
        },
        "hospital_lat": primary_lat,
        "hospital_lon": primary_lon,
    }


# ---------------------------------------------------------------------------
# Loudoun path
# ---------------------------------------------------------------------------

def _load_loudoun_facilities() -> List[dict]:
    """Parse Loudoun GeoJSON into a flat list of facility dicts."""
    data = _load_json(_LOUDOUN_GEOJSON)
    facilities = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [None, None])
        # GeoJSON is [lon, lat]
        lon, lat_val = coords[0], coords[1]
        facilities.append({
            "name": props.get("FACILITY_NAME", "Unknown"),
            "facility_type": "hospital" if props.get("FACILITY") == "H" else "urgent_care",
            "cms_rating": props.get("CMS_Rating"),
            "beds": props.get("Beds"),
            "health_system": props.get("Health_System"),
            "emergency_services": props.get("Emergency_Services"),
            "address": props.get("Address", ""),
            "latitude": lat_val,
            "longitude": lon,
        })
    return facilities


def _enrich_with_cms(primary_name: str) -> dict:
    """Look up CMS quality fields for a Loudoun hospital by name match."""
    try:
        with open(_CMS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                county = (row.get("County/Parish") or "").upper()
                if county != "LOUDOUN":
                    continue
                cms_name = (row.get("Facility Name") or "").upper()
                if primary_name.upper() in cms_name or cms_name in primary_name.upper():
                    return {
                        "cms_rating": row.get("Hospital overall rating"),
                        "hospital_type": row.get("Hospital Type"),
                        "emergency_services": row.get("Emergency Services"),
                        "ownership": row.get("Hospital Ownership"),
                    }
    except Exception:
        pass
    return {}


def _build_loudoun(lat: float, lon: float) -> dict:
    facilities = _load_loudoun_facilities()

    # Add distances
    for f in facilities:
        f["distance_miles"] = _haversine_distance(lat, lon, f["latitude"], f["longitude"])

    # Filter to 10 miles
    nearby = [f for f in facilities if f["distance_miles"] <= 10]

    # Primary hospital: closest hospital with best CMS rating
    hospitals = sorted(
        [f for f in nearby if f["facility_type"] == "hospital"],
        key=lambda f: (-1 * (f.get("cms_rating") or 0), f["distance_miles"]),
    )
    if not hospitals:
        return _graceful_degradation()

    primary = hospitals[0]
    primary_name = primary["name"]
    dist_miles = round(primary["distance_miles"], 1)

    # Enrich from CMS CSV
    cms_extra = _enrich_with_cms(primary_name)
    cms_rating = primary.get("cms_rating") or cms_extra.get("cms_rating")

    # Certifications
    certifications = _format_certifications(cms_rating)

    # Drive time
    drive_time = _get_drive_time(lat, lon, primary["latitude"], primary["longitude"], dist_miles)

    # Maternity
    births_str = "\u2014"
    csection_str = "\u2014"
    try:
        maternity_data = _load_json(_LOUDOUN_MATERNITY)
        match = _match_maternity(maternity_data.get("hospitals", []), primary_name)
        if match:
            m = match.get("maternity", {})
            births = m.get("live_births_annual")
            if births:
                births_str = f"{births:,}"
            csection = m.get("c_section_rate")
            if csection is not None:
                csection_str = f"{round(csection * 100)}%"
    except Exception:
        pass

    # Urgent care within 3 miles
    uc_count = len([f for f in nearby if f["facility_type"] == "urgent_care" and f["distance_miles"] <= 3])

    # Pharmacy count
    pharm = _get_pharmacy_count(lat, lon, radius_miles=1.0)
    pharm_str = f"{pharm} within 1 mile" if pharm is not None else "N/A"

    # Employee count
    emp_count = _get_employee_count("loudoun")

    # Compute access score (simple proxy — no dedicated Loudoun class)
    score = 50
    if dist_miles <= 5:
        score += 10
    try:
        if int(float(cms_rating)) >= 4:
            score += 10
    except (TypeError, ValueError):
        pass
    if uc_count >= 2:
        score += 10
    if pharm is not None and pharm >= 2:
        score += 10
    # drive time check
    try:
        minutes = int("".join(c for c in drive_time if c.isdigit()))
        if minutes <= 15:
            score += 10
    except (ValueError, TypeError):
        pass
    score = min(score, 100)

    # Total facilities from GeoJSON
    total = len(facilities)

    return {
        "healthcare": {
            "primary_label": f"PRIMARY HOSPITAL \u2014 {primary_name.upper()}",
            "name": primary_name,
            "distance": f"{dist_miles} mi",
            "drive_time": drive_time,
            "certifications": certifications,
            "births_per_year": births_str,
            "csection_rate": csection_str,
            "employee_count": emp_count,
            "urgent_care_count": f"{uc_count} within 3 miles",
            "pharmacy_count": pharm_str,
            "total_facilities": f"{total} Loudoun County",
            "score": f"{score}/100 {_score_label(score)}",
        },
        "hospital_lat": primary["latitude"],
        "hospital_lon": primary["longitude"],
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_healthcare_context(lat: float, lon: float, county: str) -> dict:
    """
    Build the healthcare context dict matching the structure in context_sample.py.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name ('fairfax', 'loudoun', or 'unknown')

    Returns:
        Dict with key 'healthcare' containing all template variables.
    """
    try:
        if county == "fairfax":
            return _build_fairfax(lat, lon)
        elif county == "loudoun":
            return _build_loudoun(lat, lon)
        else:
            return _graceful_degradation()
    except Exception as e:
        print(f"ERROR in build_healthcare_context: {e}", file=sys.stderr)
        return _graceful_degradation()
