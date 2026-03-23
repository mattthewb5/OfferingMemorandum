"""
Employer Map Context Builder for OM Generator

Geocodes major employers and builds a Google Static Maps URL for the
employer location map section.

Usage:
    from employer_map_context import build_employer_map_context
    map_ctx = build_employer_map_context(lat, lon, employers_list, county)
"""

import json
import sys
from pathlib import Path

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

# Geocache path
_GEOCACHE_PATH = Path(__file__).resolve().parent / "data" / "employer_geocache.json"


def _load_geocache() -> dict:
    """Load the employer geocode cache from disk."""
    try:
        if _GEOCACHE_PATH.exists():
            with open(_GEOCACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_geocache(cache: dict) -> None:
    """Write the employer geocode cache to disk."""
    try:
        _GEOCACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_GEOCACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"WARNING: Could not save geocache: {e}", file=sys.stderr)


def _geocode_employer(name: str, county: str, api_key: str) -> dict:
    """Geocode an employer via Google Maps Geocoding API."""
    try:
        query = f"{name}, {county.title()} County, Virginia"
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        resp = requests.get(
            url,
            params={"address": query, "key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return {"lat": loc["lat"], "lon": loc["lng"], "source": "google"}
    except Exception as e:
        print(f"WARNING: Geocoding failed for '{name}': {e}", file=sys.stderr)
    return {"lat": None, "lon": None, "source": "failed"}


def _build_static_map_url(
    subject_lat: float,
    subject_lon: float,
    markers: list,
    api_key: str,
    width: int = 800,
    height: int = 420,
) -> str:
    """Build a Google Static Maps URL with subject property and employer markers."""
    base = "https://maps.googleapis.com/maps/api/staticmap"
    params = [
        f"size={width}x{height}",
        "scale=2",
        "zoom=11",
        f"center={subject_lat},{subject_lon}",
        (
            f"markers=color:0xb8966a|size:mid|label:P"
            f"|{subject_lat},{subject_lon}"
        ),
    ]
    labels = "123456789A"
    for i, m in enumerate(markers[:10]):
        if m.get("lat") and m.get("lon"):
            params.append(
                f"markers=color:0x2a52a0|size:mid|label:{labels[i]}"
                f"|{m['lat']},{m['lon']}"
            )
    params.append(f"key={api_key}")
    return base + "?" + "&".join(params)


def _graceful_default(lat: float, lon: float) -> dict:
    return {
        "employer_map_markers": [],
        "employer_map_markers_json": "[]",
        "employer_map_center_lat": lat,
        "employer_map_center_lon": lon,
        "employer_map_zoom": 11,
        "employer_map_static_url": None,
    }


def build_employer_map_context(
    lat: float, lon: float, employers: list, county: str
) -> dict:
    """
    Build employer map context with geocoded markers and static map URL.

    Args:
        lat: Subject property latitude
        lon: Subject property longitude
        employers: List of employer dicts from build_employers_context()
        county: County name ('fairfax' or 'loudoun')

    Returns:
        Dict with employer_map_markers, employer_map_markers_json,
        employer_map_center_lat/lon, employer_map_zoom, employer_map_static_url.
    """
    try:
        if not employers:
            return _graceful_default(lat, lon)

        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if not api_key:
            print("WARNING: GOOGLE_MAPS_API_KEY not available for employer map",
                  file=sys.stderr)
            return _graceful_default(lat, lon)

        # Load and update geocache
        cache = _load_geocache()
        cache_updated = False

        markers = []
        for emp in employers:
            name = emp.get("name", "")
            if not name:
                continue

            if name not in cache:
                cache[name] = _geocode_employer(name, county, api_key)
                cache_updated = True

            geo = cache[name]
            markers.append({
                "name": name,
                "lat": geo.get("lat"),
                "lon": geo.get("lon"),
                "rank": emp.get("rank", ""),
                "sector": emp.get("sector", ""),
            })

        if cache_updated:
            _save_geocache(cache)

        # Build static map URL
        valid_markers = [m for m in markers if m.get("lat") and m.get("lon")]
        static_map_url = (
            _build_static_map_url(lat, lon, valid_markers, api_key)
            if valid_markers else None
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
        print(f"WARNING in build_employer_map_context: {e}", file=sys.stderr)
        return _graceful_default(lat, lon)
