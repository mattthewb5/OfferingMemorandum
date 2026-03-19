#!/usr/bin/env python3
"""
Employer Map Context — builds geocoded marker list and Google Static Maps URL
for embedding a print-safe map image in the OM.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add multi-county research package to path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

logger = logging.getLogger(__name__)

# Geocache file stores lat/lon for employer HQs to avoid repeated API calls
_CACHE_PATH = os.path.join(os.path.dirname(__file__), "employer_geocache.json")

# Sector mapping — mirrors fairfax_economic_indicators._infer_industry
_SECTOR_MAP = {
    "federal government": "Public Administration",
    "fairfax county government": "Public Administration",
    "fairfax county public schools": "Education",
    "george mason university": "Higher Education",
    "inova health system": "Healthcare",
    "booz allen hamilton": "Defense / Consulting",
    "leidos": "Defense Technology",
    "science applications": "Defense Technology",
    "dxc technology": "IT Services",
    "capital one": "Financial Services",
    "navy federal": "Financial Services",
    "general dynamics": "Defense",
    "northrop grumman": "Defense",
    "amazon": "Technology",
    "mitre": "Technology",
    "freddie mac": "Financial Services",
}


def _infer_sector(name: str) -> str:
    """Map employer name to a display sector label."""
    name_lower = name.lower()
    for key, sector in _SECTOR_MAP.items():
        if key in name_lower:
            return sector
    return "Other"


def _load_geocache() -> Dict[str, Any]:
    """Load the employer geocache from disk."""
    if os.path.exists(_CACHE_PATH):
        try:
            with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_geocache(cache: Dict[str, Any]) -> None:
    """Persist the employer geocache to disk."""
    try:
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logger.warning("Could not save employer geocache: %s", e)


def _geocode_employer(name: str, county: str, api_key: str,
                      cache: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    Geocode an employer name to lat/lon.  Uses cache first, then Google
    Geocoding API.  Returns {"lat": ..., "lon": ...} or None.
    """
    cache_key = f"{name}|{county}"
    if cache_key in cache:
        return cache[cache_key]

    try:
        query = f"{name}, {county} County, Virginia"
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        resp = requests.get(url, params={"address": query, "key": api_key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            result = {"lat": loc["lat"], "lon": loc["lng"]}
            cache[cache_key] = result
            return result
    except Exception as e:
        logger.warning("Geocode failed for %s: %s", name, e)

    return None


def _load_employers(county: str) -> List[Dict[str, Any]]:
    """Load the most recent year's employers from major_employers.json."""
    json_path = (
        _REPO_ROOT
        / "multi-county-real-estate-research"
        / "data"
        / county
        / "major_employers.json"
    )
    if not json_path.exists():
        logger.warning("No employer data at %s", json_path)
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    years = sorted(data.get("employers_by_year", {}).keys())
    if not years:
        return []

    latest = data["employers_by_year"][years[-1]]
    return latest.get("employers", [])


def _build_static_map_url(
    subject_lat: float,
    subject_lon: float,
    markers: list,
    api_key: str,
    width: int = 800,
    height: int = 420,
) -> str:
    base = "https://maps.googleapis.com/maps/api/staticmap"
    params = [
        f"size={width}x{height}",
        "scale=2",
        f"zoom=11",
        f"center={subject_lat},{subject_lon}",
        # Subject property — gold star equivalent (red, large, label P)
        f"markers=color:0xb8966a|size:mid|label:P"
        f"|{subject_lat},{subject_lon}",
    ]
    # Employer markers — numbered 1–9, then use A for 10
    labels = "123456789A"
    for i, m in enumerate(markers[:10]):
        if m.get("lat") and m.get("lon"):
            label = labels[i]
            params.append(
                f"markers=color:0x2a52a0|size:mid|label:{label}"
                f"|{m['lat']},{m['lon']}"
            )
    params.append(f"key={api_key}")
    return base + "?" + "&".join(params)


def build_employer_map_context(
    lat: float, lon: float, county: str
) -> Dict[str, Any]:
    """
    Build the employer map context dict for the OM template.

    Returns dict with keys:
        employer_map_markers      — list of marker dicts
        employer_map_markers_json — JSON string of markers
        employer_map_center_lat   — subject property latitude
        employer_map_center_lon   — subject property longitude
        employer_map_zoom         — default zoom level
        employer_map_static_url   — Google Static Maps URL (or None)
    """
    _safe = {
        "employer_map_markers": [],
        "employer_map_markers_json": "[]",
        "employer_map_center_lat": lat,
        "employer_map_center_lon": lon,
        "employer_map_zoom": 11,
        "employer_map_static_url": None,
    }

    try:
        from core.api_config import get_api_key

        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
        employers = _load_employers(county)
        if not employers:
            logger.info("No employer data for county=%s", county)
            return _safe

        cache = _load_geocache()
        markers = []

        for emp in employers[:10]:
            name = emp.get("name", "")
            employees = emp.get("employees", 0)
            sector = _infer_sector(name)

            coords = None
            if api_key:
                coords = _geocode_employer(name, county, api_key, cache)

            markers.append({
                "name": name,
                "sector": sector,
                "employees": f"{employees:,}" if isinstance(employees, int) else str(employees),
                "lat": coords["lat"] if coords else None,
                "lon": coords["lon"] if coords else None,
            })

        _save_geocache(cache)

        static_map_url = (
            _build_static_map_url(lat, lon, markers, api_key)
            if api_key and markers
            else None
        )

        return {
            "employer_map_markers": markers,
            "employer_map_markers_json": json.dumps(markers),
            "employer_map_center_lat": lat,
            "employer_map_center_lon": lon,
            "employer_map_zoom": 11,
            "employer_map_static_url": static_map_url,
        }

    except Exception as e:
        logger.warning("employer_map_context failed: %s", e, exc_info=True)
        return _safe
