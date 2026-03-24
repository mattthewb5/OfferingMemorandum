"""
Development Map Context Builder for OM Generator

Builds a Google Static Maps URL showing new-construction permit markers,
subject property, and metro station within a 2-mile radius.

Usage:
    from dev_map_context import build_dev_map_context
    ctx = build_dev_map_context(lat, lon, county, dev_ctx)
"""

import math
import sys
from pathlib import Path

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

_STATIC_MAP_BASE = "https://maps.googleapis.com/maps/api/staticmap"
_RADIUS_MILES = 2.0
_MAX_RESIDENTIAL_MARKERS = 40

# Loudoun permits CSV path (same as development_context.py)
_LOUDOUN_PERMITS = (
    _REPO_ROOT / "multi-county-real-estate-research" / "data" / "loudoun"
    / "building_permits" / "loudoun_permits_with_infrastructure.csv"
)


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in miles."""
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _load_fairfax_permits(lat: float, lon: float):
    """Load Fairfax new-construction permits within 2 miles."""
    from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

    analyzer = FairfaxPermitsAnalysis()
    nearby_df = analyzer.get_permits_near_point(
        lat, lon, radius_miles=_RADIUS_MILES, months_back=24
    )

    residential = []
    commercial = []

    if not nearby_df.empty and 'permit_category' in nearby_df.columns:
        for _, row in nearby_df.iterrows():
            cat = row.get('permit_category', '')
            rlat = row.get('centroid_lat')
            rlon = row.get('centroid_lon')
            if rlat is None or rlon is None:
                continue
            try:
                rlat, rlon = float(rlat), float(rlon)
            except (ValueError, TypeError):
                continue

            if 'residential_new' in str(cat):
                dist = _haversine_miles(lat, lon, rlat, rlon)
                residential.append((rlat, rlon, dist))
            elif 'commercial_new' in str(cat):
                commercial.append((rlat, rlon))

    return residential, commercial


def _load_loudoun_permits(lat: float, lon: float):
    """Load Loudoun new-construction permits within 2 miles."""
    from core.development_pressure_analyzer import DevelopmentPressureAnalyzer

    analyzer = DevelopmentPressureAnalyzer(permits_csv_path=str(_LOUDOUN_PERMITS))
    nearby = analyzer.find_nearby_permits(lat, lon, radius_miles=_RADIUS_MILES)

    residential = []
    commercial = []

    for p in nearby:
        combined = f"{p.permit_type} {p.work_class} {p.description}".lower()
        plat, plon = p.latitude, p.longitude
        if plat is None or plon is None:
            continue

        is_new = 'new' in combined
        if not is_new:
            continue

        is_residential = any(kw in combined for kw in
                             ('multi-family', 'apartment', 'townhouse',
                              'building (residential)'))
        is_commercial = 'commercial' in combined

        if is_residential:
            dist = _haversine_miles(lat, lon, plat, plon)
            residential.append((plat, plon, dist))
        elif is_commercial:
            commercial.append((plat, plon))

    return residential, commercial


def _build_static_map_url(lat, lon, residential, commercial,
                          metro_lat, metro_lon, api_key):
    """Assemble the Static Maps URL with all markers."""
    parts = [
        f"{_STATIC_MAP_BASE}?size=800x400&scale=2&zoom=13",
        f"center={lat},{lon}",
    ]

    # Subject property marker
    parts.append(f"markers=color:0xb8966a|size:mid|label:P|{lat},{lon}")

    # Residential new-construction markers (capped)
    residential.sort(key=lambda x: x[2])  # sort by distance
    capped = residential[:_MAX_RESIDENTIAL_MARKERS]
    if capped:
        locs = "|".join(f"{r[0]},{r[1]}" for r in capped)
        parts.append(f"markers=color:red|size:tiny|{locs}")

    # Commercial new-construction markers (all)
    if commercial:
        locs = "|".join(f"{c[0]},{c[1]}" for c in commercial)
        parts.append(f"markers=color:0xFFAA00|size:tiny|{locs}")

    # Metro station marker
    if metro_lat is not None and metro_lon is not None:
        parts.append(
            f"markers=color:0x2a52a0|size:small|label:M|{metro_lat},{metro_lon}"
        )

    parts.append(f"key={api_key}")
    return "&".join(parts)


def build_dev_map_context(lat: float, lon: float, county: str,
                          dev_ctx: dict) -> dict:
    """Build the development activity map Static Maps URL.

    Returns dict with:
        dev_map_static_url: URL string or None
    """
    try:
        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("  WARNING: GOOGLE_MAPS_API_KEY not available for dev map",
                  file=sys.stderr)
            return {"dev_map_static_url": None}

        county_lower = county.lower().strip()
        if county_lower == "fairfax":
            residential, commercial = _load_fairfax_permits(lat, lon)
        elif county_lower == "loudoun":
            residential, commercial = _load_loudoun_permits(lat, lon)
        else:
            print(f"  WARNING: Dev map not supported for county: {county}",
                  file=sys.stderr)
            return {"dev_map_static_url": None}

        # Get metro coords from the context (set by property_context.py)
        metro_lat = dev_ctx.get("metro_lat")
        metro_lon = dev_ctx.get("metro_lon")

        total = len(residential) + len(commercial)
        if total == 0:
            print("  Dev map: no new-construction permits found, skipping map",
                  file=sys.stderr)
            return {"dev_map_static_url": None}

        url = _build_static_map_url(
            lat, lon, residential, commercial, metro_lat, metro_lon, api_key
        )

        # Check URL length — Static Maps max is ~16384 chars
        if len(url) > 16000:
            # Reduce residential markers
            residential = residential[:20]
            url = _build_static_map_url(
                lat, lon, residential, commercial, metro_lat, metro_lon, api_key
            )

        res_count = min(len(residential), _MAX_RESIDENTIAL_MARKERS)
        com_count = len(commercial)
        print(f"  Dev map wired: {res_count} residential + {com_count} commercial "
              f"new-construction markers")

        return {"dev_map_static_url": url}

    except Exception as exc:
        print(f"  WARNING: Dev map context failed: {exc}", file=sys.stderr)
        return {"dev_map_static_url": None}
