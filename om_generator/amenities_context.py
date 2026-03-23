"""
Amenities Context Builder for OM Generator

Queries Google Places Nearby Search (New) API for six amenity categories
within a 1-mile radius, then uses Distance Matrix (walking) to get
walk time and distance to the nearest place in each category.

Usage:
    from amenities_context import build_amenities_context
    ctx = build_amenities_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import math
import sys
from pathlib import Path

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

# Category definitions: (label, includedTypes)
_CATEGORIES = [
    ("Restaurants", ["restaurant"]),
    ("Grocery / Market", ["grocery_store", "supermarket"]),
    ("Fitness / Gym", ["gym", "fitness_center"]),
    ("Parks / Trails", ["park"]),
    ("Coffee Shops", ["coffee_shop", "cafe"]),
    ("Retail Shops", ["store", "clothing_store", "home_goods_store"]),
]

_DEGRADED_ITEM = {
    "count": "\u2014",
    "label": "",
    "nearest_name": "\u2014",
    "nearest_dist": "\u2014",
    "nearest_walk": "\u2014",
}


def _graceful_degradation() -> dict:
    """Return all six amenity items with dash placeholders."""
    return {
        "amenities": [
            {**_DEGRADED_ITEM, "label": label}
            for label, _ in _CATEGORIES
        ]
    }


def _places_nearby(lat: float, lon: float, included_types: list, api_key: str) -> list:
    """Run a Places Nearby Search (New) and return list of place dicts."""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location",
        "Content-Type": "application/json",
    }
    body = {
        "includedTypes": included_types,
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": 1609.34,  # 1 mile in meters
            }
        },
    }
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    resp.raise_for_status()
    return resp.json().get("places", [])


def _batch_walking_distances(
    lat: float, lon: float,
    destinations: list,
    api_key: str,
) -> list:
    """
    Get walking distance and duration for multiple destinations in one call.

    Args:
        destinations: list of (dest_lat, dest_lon) tuples

    Returns:
        list of (distance_text, duration_text) tuples, or ("—", "—") per failed element.
    """
    if not destinations:
        return []

    dest_str = "|".join(f"{d[0]},{d[1]}" for d in destinations)
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{lat},{lon}",
        "destinations": dest_str,
        "mode": "walking",
        "key": api_key,
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = []
    elements = data.get("rows", [{}])[0].get("elements", [])
    for elem in elements:
        if elem.get("status") == "OK":
            dist_m = elem["distance"]["value"]
            dur_s = elem["duration"]["value"]
            dist_mi = dist_m / 1609.34
            dur_min = max(1, round(dur_s / 60))
            results.append((f"{dist_mi:.1f} mi", f"{dur_min} min"))
        else:
            results.append(("\u2014", "\u2014"))

    # Pad if response was shorter than expected
    while len(results) < len(destinations):
        results.append(("\u2014", "\u2014"))

    return results


def _get_amenity_data(lat: float, lon: float, api_key: str) -> list:
    """
    Query all six amenity categories and return list of dicts.
    Each dict: {count, label, nearest_name, nearest_dist, nearest_walk}
    """
    items = []
    nearest_coords = []  # (lat, lon) for each category's nearest place

    for label, types in _CATEGORIES:
        try:
            places = _places_nearby(lat, lon, types, api_key)
            count = min(len(places), 99)

            if places:
                nearest = places[0]
                nearest_name = nearest.get("displayName", {}).get("text", "\u2014")
                loc = nearest.get("location", {})
                nearest_lat = loc.get("latitude")
                nearest_lon = loc.get("longitude")
            else:
                nearest_name = "\u2014"
                nearest_lat = None
                nearest_lon = None

            items.append({
                "count": str(count) if count > 0 else "\u2014",
                "label": label,
                "nearest_name": nearest_name,
                "nearest_dist": "\u2014",
                "nearest_walk": "\u2014",
            })
            nearest_coords.append((nearest_lat, nearest_lon) if nearest_lat else None)

        except Exception:
            items.append({**_DEGRADED_ITEM, "label": label})
            nearest_coords.append(None)

    # Batch walking distance for all categories with a nearest place
    valid_indices = [i for i, c in enumerate(nearest_coords) if c is not None]
    valid_dests = [nearest_coords[i] for i in valid_indices]

    if valid_dests:
        try:
            walk_results = _batch_walking_distances(lat, lon, valid_dests, api_key)
            for idx, (dist_text, dur_text) in zip(valid_indices, walk_results):
                items[idx]["nearest_dist"] = dist_text
                items[idx]["nearest_walk"] = dur_text
        except Exception:
            pass  # items already have "—" defaults

    return items


def build_amenities_context(lat: float, lon: float, county: str) -> dict:
    """
    Build the amenities context dict for the OM template.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name ('fairfax', 'loudoun', or 'unknown')

    Returns:
        Dict with key 'amenities' containing list of 6 category dicts.
    """
    try:
        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if not api_key:
            print("WARNING: GOOGLE_MAPS_API_KEY not available for amenities",
                  file=sys.stderr)
            return _graceful_degradation()

        amenity_list = _get_amenity_data(lat, lon, api_key)
        return {"amenities": amenity_list}

    except Exception as e:
        print(f"ERROR in build_amenities_context: {e}", file=sys.stderr)
        return _graceful_degradation()
