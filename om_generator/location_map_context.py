"""
Location Map Context Builder for OM Generator

Builds a Google Static Maps URL showing schools, hospital, metro station,
fire stations, police stations, and 1mi/2mi radius rings around the
subject property.

Usage:
    from location_map_context import build_location_map_context
    ctx = build_location_map_context(lat, lon, county, schools_ctx, healthcare_ctx, prop_ctx)
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

# Fairfax emergency services data
_FAIRFAX_FIRE = (
    _REPO_ROOT / "multi-county-real-estate-research" / "data" / "fairfax"
    / "emergency_services" / "processed" / "fire_stations.parquet"
)
_FAIRFAX_POLICE = (
    _REPO_ROOT / "multi-county-real-estate-research" / "data" / "fairfax"
    / "emergency_services" / "processed" / "police_stations.parquet"
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


def _circle_path(lat: float, lon: float, radius_miles: float,
                 color: str, n_points: int = 32) -> str:
    """Build an encoded circle path parameter for Static Maps.

    Returns a path=... string with color, weight, and polyline points.
    """
    R_earth = 3958.8
    points = []
    for i in range(n_points + 1):
        angle = 2 * math.pi * i / n_points
        dlat = math.degrees(radius_miles / R_earth) * math.cos(angle)
        dlon = math.degrees(
            radius_miles / (R_earth * math.cos(math.radians(lat)))
        ) * math.sin(angle)
        points.append(f"{lat + dlat:.6f},{lon + dlon:.6f}")

    path_points = "|".join(points)
    return f"path=color:{color}|weight:1|fillcolor:0x00000000|{path_points}"


def _load_fairfax_stations(lat: float, lon: float, station_type: str,
                           max_count: int = 2, max_miles: float = 3.0):
    """Load nearest fire/police stations from Fairfax parquet data."""
    import pandas as pd

    path = _FAIRFAX_FIRE if station_type == "fire" else _FAIRFAX_POLICE
    if not path.exists():
        return []

    df = pd.read_parquet(path)
    results = []
    for _, row in df.iterrows():
        slat = row.get("latitude")
        slon = row.get("longitude")
        if slat is None or slon is None:
            continue
        try:
            slat, slon = float(slat), float(slon)
        except (ValueError, TypeError):
            continue
        dist = _haversine_miles(lat, lon, slat, slon)
        if dist <= max_miles:
            results.append((slat, slon, dist))

    results.sort(key=lambda x: x[2])
    return results[:max_count]


def _places_nearest(lat: float, lon: float, place_type: str,
                    api_key: str) -> tuple | None:
    """Find nearest place via Google Places Nearby Search. Returns (lat, lon) or None."""
    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.location",
        }
        body = {
            "includedTypes": [place_type],
            "maxResultCount": 1,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": 4828,  # ~3 miles
                }
            },
        }
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        places = resp.json().get("places", [])
        if places:
            loc = places[0].get("location", {})
            plat = loc.get("latitude")
            plon = loc.get("longitude")
            if plat is not None and plon is not None:
                return (plat, plon)
    except Exception:
        pass
    return None


def build_location_map_context(lat: float, lon: float, county: str,
                               schools_ctx: dict, healthcare_ctx: dict,
                               prop_ctx: dict) -> dict:
    """Build the location context map Static Maps URL.

    Returns dict with:
        location_map_static_url: URL string or None
    """
    try:
        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("  WARNING: GOOGLE_MAPS_API_KEY not available for location map",
                  file=sys.stderr)
            return {"location_map_static_url": None}

        parts = [
            f"{_STATIC_MAP_BASE}?size=800x390&scale=2&zoom=13",
            f"center={lat},{lon}",
        ]

        # Subject property marker
        parts.append(f"markers=color:0xb8966a|size:mid|label:P|{lat},{lon}")

        # School markers (up to 3)
        placed = []
        schools = schools_ctx.get("schools", [])
        school_locs = []
        for s in schools[:3]:
            slat = s.get("lat")
            slon = s.get("lon")
            if slat is not None and slon is not None:
                school_locs.append(f"{slat},{slon}")
                placed.append("schools")
        if school_locs:
            locs = "|".join(school_locs)
            parts.append(f"markers=color:green|size:small|label:S|{locs}")

        # Hospital marker
        hlat = healthcare_ctx.get("hospital_lat")
        hlon = healthcare_ctx.get("hospital_lon")
        if hlat is not None and hlon is not None:
            parts.append(
                f"markers=color:red|size:small|label:H|{hlat},{hlon}"
            )
            placed.append("hospital")

        # Metro station marker
        mlat = prop_ctx.get("metro_lat")
        mlon = prop_ctx.get("metro_lon")
        if mlat is not None and mlon is not None:
            parts.append(
                f"markers=color:0x2a52a0|size:small|label:M|{mlat},{mlon}"
            )
            placed.append("metro")

        # Fire stations
        county_lower = county.lower().strip()
        fire_stations = []
        if county_lower == "fairfax":
            fire_stations = _load_fairfax_stations(lat, lon, "fire")
        else:
            # Loudoun or other — use Google Places
            result = _places_nearest(lat, lon, "fire_station", api_key)
            if result:
                fire_stations = [(*result, 0)]

        if fire_stations:
            locs = "|".join(f"{f[0]},{f[1]}" for f in fire_stations)
            parts.append(f"markers=color:0xFF4400|size:tiny|label:F|{locs}")
            placed.append("fire")

        # Police stations
        police_stations = []
        if county_lower == "fairfax":
            police_stations = _load_fairfax_stations(lat, lon, "police")
        else:
            result = _places_nearest(lat, lon, "police", api_key)
            if result:
                police_stations = [(*result, 0)]

        if police_stations:
            locs = "|".join(f"{p[0]},{p[1]}" for p in police_stations)
            parts.append(f"markers=color:0x333333|size:tiny|label:L|{locs}")
            placed.append("police")

        # Radius rings (1mi and 2mi)
        ring_1mi = _circle_path(lat, lon, 1.0, "0x2a52a080")
        ring_2mi = _circle_path(lat, lon, 2.0, "0x2a52a040")
        parts.append(ring_1mi)
        parts.append(ring_2mi)

        parts.append(f"key={api_key}")
        url = "&".join(parts)

        # Check URL length
        if len(url) > 16000:
            # Drop radius rings if URL is too long
            parts_trimmed = [p for p in parts
                             if not p.startswith("path=")]
            parts_trimmed.append(f"key={api_key}")
            url = "&".join(parts_trimmed)

        unique_placed = list(dict.fromkeys(placed))
        print(f"  Location map wired: markers placed for {', '.join(unique_placed) if unique_placed else 'none'}")

        return {"location_map_static_url": url}

    except Exception as exc:
        print(f"  WARNING: Location map context failed: {exc}", file=sys.stderr)
        return {"location_map_static_url": None}
