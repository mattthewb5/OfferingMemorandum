"""
Employer Map Context Builder for OM Generator

Resolves employer domains (via Claude API), geocodes employer HQs
(via Google Maps / Census fallback), and builds a marker list for
the embedded Google Maps JavaScript API map.

Usage:
    from employer_map_context import build_employer_map_context
    ctx = build_employer_map_context(lat, lon, employers_list, 'fairfax')
"""

import json
import logging
import os
import sys
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Add multi-county research package to path for api_config
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# Cache paths — live inside om_generator/data/ so they are repo-tracked
_DATA_DIR = Path(__file__).resolve().parent / "data"
_DOMAIN_CACHE_PATH = _DATA_DIR / "employer_domain_cache.json"
_GEO_CACHE_PATH = _DATA_DIR / "employer_geocache.json"


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cache read failed (%s): %s", path.name, exc)
    return {}


def _save_cache(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except OSError as exc:
        logger.warning("Cache write failed (%s): %s", path.name, exc)


# ---------------------------------------------------------------------------
# Step 1 — Domain resolution via Claude API
# ---------------------------------------------------------------------------

def _resolve_domains(employers: list, cache: dict) -> dict:
    """Resolve employer names → web domains.  Uses cache, then one batch
    Claude API call for any uncached names."""
    uncached = [e for e in employers if e["name"] not in cache]
    if not uncached:
        return cache

    try:
        import anthropic

        client = anthropic.Anthropic()
        names = [e["name"] for e in uncached]

        prompt = (
            "Resolve employer names to their primary web domains for logo lookup.\n\n"
            "Return ONLY a valid JSON object. No preamble, no markdown, no explanation.\n"
            "Keys are employer names exactly as provided. "
            'Values are primary domains (e.g. "amazon.com", "loudoun.gov"). '
            "Use null for any you cannot determine with confidence.\n\n"
            f"Employers: {json.dumps(names)}"
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        domain_map = json.loads(response.content[0].text)
        cache.update(domain_map)
        _save_cache(_DOMAIN_CACHE_PATH, cache)
        logger.info("Resolved %d employer domains via Claude API", len(domain_map))
    except Exception as exc:
        logger.warning("Domain resolution failed: %s", exc)
        # Set uncached to None so we don't retry every run
        for e in uncached:
            cache.setdefault(e["name"], None)
        _save_cache(_DOMAIN_CACHE_PATH, cache)

    return cache


# ---------------------------------------------------------------------------
# Step 2 — Geocoding
# ---------------------------------------------------------------------------

def _geocode_employer(name: str, county: str) -> dict | None:
    """Geocode a single employer by name + county query string.

    Returns {"lat": float, "lon": float, "source": str} or None.
    """
    query = f"{name}, {county.title()} County, Virginia"

    # Try Google first
    try:
        from core.api_config import get_api_key

        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
        if api_key:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            resp = requests.get(
                url, params={"address": query, "key": api_key}, timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return {"lat": loc["lat"], "lon": loc["lng"], "source": "google"}
    except Exception as exc:
        logger.debug("Google geocode failed for %s: %s", name, exc)

    # Census fallback
    try:
        url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        resp = requests.get(
            url,
            params={
                "address": query,
                "benchmark": "Public_AR_Current",
                "format": "json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        matches = resp.json().get("result", {}).get("addressMatches", [])
        if matches:
            coords = matches[0]["coordinates"]
            return {"lat": coords["y"], "lon": coords["x"], "source": "census"}
    except Exception as exc:
        logger.debug("Census geocode failed for %s: %s", name, exc)

    return None


def _geocode_employers(employers: list, county: str, cache: dict) -> dict:
    """Geocode all employers, using cache where available."""
    updated = False
    for emp in employers:
        name = emp["name"]
        if name in cache and cache[name] is not None:
            continue
        result = _geocode_employer(name, county)
        if result:
            cache[name] = result
            updated = True
        else:
            # Mark as attempted so we don't retry every run
            cache[name] = None
            updated = True
            logger.warning("Could not geocode employer: %s", name)

    if updated:
        _save_cache(_GEO_CACHE_PATH, cache)
    return cache


# ---------------------------------------------------------------------------
# Step 3 + 4 — Build markers and return dict
# ---------------------------------------------------------------------------

def build_employer_map_context(
    lat: float,
    lon: float,
    employers: list,
    county: str,
) -> dict:
    """Build employer map context for the OM template.

    Args:
        lat: Subject property latitude.
        lon: Subject property longitude.
        employers: List of employer dicts from build_employers_context()
                   (keys: rank, name, sector, employees).
        county: 'fairfax' or 'loudoun'.

    Returns:
        Dict with employer_map_markers, employer_map_markers_json,
        employer_map_center_lat, employer_map_center_lon, employer_map_zoom.
    """
    _safe = {
        "employer_map_markers": [],
        "employer_map_markers_json": "[]",
        "employer_map_center_lat": lat,
        "employer_map_center_lon": lon,
        "employer_map_zoom": 11,
    }

    try:
        # Load caches
        domain_cache = _load_cache(_DOMAIN_CACHE_PATH)
        geo_cache = _load_cache(_GEO_CACHE_PATH)

        # Resolve domains
        domain_cache = _resolve_domains(employers, domain_cache)

        # Geocode
        geo_cache = _geocode_employers(employers, county, geo_cache)

        # Build markers
        token = os.environ.get("LOGO_DEV_TOKEN", "")
        markers = []
        for emp in employers:
            geo = geo_cache.get(emp["name"])
            if not geo or not geo.get("lat"):
                continue
            domain = domain_cache.get(emp["name"])
            logo_url = None
            if domain:
                if token:
                    logo_url = f"https://img.logo.dev/{domain}?token={token}&size=40"
                else:
                    logo_url = f"https://img.logo.dev/{domain}?size=40"
            markers.append({
                "name": emp["name"],
                "sector": emp["sector"],
                "employees": emp["employees"],
                "lat": geo["lat"],
                "lon": geo["lon"],
                "domain": domain,
                "logo_url": logo_url,
            })

        return {
            "employer_map_markers": markers,
            "employer_map_markers_json": json.dumps(markers),
            "employer_map_center_lat": lat,
            "employer_map_center_lon": lon,
            "employer_map_zoom": 11,
        }

    except Exception as exc:
        logger.warning("Failed to build employer map context: %s", exc, exc_info=True)
        return _safe
