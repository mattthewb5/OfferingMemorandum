"""
Property-identity context builder for the OM Jinja2 template.

Populates ~15 property-level keys (address, city, county, metro, university, etc.)
that context_sample.py hardcodes for Regent's Park / Fairfax.  Called first in
generate_om.py so every downstream builder inherits correct property identity.
"""

import logging
import math
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# Add multi-county research package to path (for api_config)
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

logger = logging.getLogger(__name__)

# ── Street‐type abbreviations ──────────────────────────────────────────────
_STREET_ABBREV = {
    "Place": "Pl.",
    "Road": "Rd.",
    "Street": "St.",
    "Drive": "Dr.",
    "Avenue": "Ave.",
    "Boulevard": "Blvd.",
    "Lane": "Ln.",
    "Court": "Ct.",
    "Circle": "Cir.",
    "Terrace": "Ter.",
    "Trail": "Trl.",
    "Way": "Way",
    "Parkway": "Pkwy.",
    "Pike": "Pike",
    "Highway": "Hwy.",
    "Turnpike": "Tpke.",
}


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in miles between two points."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _abbreviate_street(address: str) -> str:
    """Abbreviate the trailing street type in *address*."""
    for full, abbr in _STREET_ABBREV.items():
        if address.endswith(full):
            return address[: -len(full)] + abbr
    return address


def _parse_street_address(address: str) -> str:
    """Extract the street-number + street-name portion from a full address.

    Strips city, state, and ZIP by splitting on the first comma.
    """
    street = address.split(",")[0].strip()
    return street


def _reverse_geocode(lat: float, lon: float, api_key: str) -> dict:
    """Reverse-geocode *lat*/*lon* via Google Maps and return city, ZIP, state.

    Returns a dict with keys ``city``, ``zip``, ``state``, and ``state_abbr``,
    all strings.  Falls back to empty strings on any error.
    """
    result = {"city": "", "zip": "", "state": "", "state_abbr": ""}
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        resp = requests.get(
            url,
            params={"latlng": f"{lat},{lon}", "key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("results"):
            return result

        components = data["results"][0].get("address_components", [])
        for comp in components:
            types = comp.get("types", [])
            if "locality" in types:
                result["city"] = comp["long_name"]
            elif "postal_code" in types:
                result["zip"] = comp["short_name"]
            elif "administrative_area_level_1" in types:
                result["state"] = comp["long_name"]
                result["state_abbr"] = comp["short_name"]
    except Exception as exc:
        logger.warning("Reverse geocode failed: %s", exc)
    return result


def _nearest_place(
    lat: float,
    lon: float,
    place_type: str,
    api_key: str,
    radius_m: int = 8047,
    rank_preference: str = "POPULARITY",
) -> dict | None:
    """Find the nearest *place_type* via Google Places Nearby Search.

    *radius_m* defaults to ~5 miles (8047 m).  *rank_preference* is
    ``"POPULARITY"`` (default) or ``"DISTANCE"``.  Returns the first result
    dict or ``None`` on failure / no results.
    """
    try:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.location",
        }
        body = {
            "includedTypes": [place_type],
            "maxResultCount": 1,
            "rankPreference": rank_preference,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": radius_m,
                }
            },
        }
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
        places = resp.json().get("places", [])
        if places:
            return places[0]
    except Exception as exc:
        logger.warning("Places lookup (%s) failed: %s", place_type, exc)
    return None


def _metro_badge(station_name: str) -> str:
    """Derive a short badge label from the full metro station name.

    Takes the first meaningful word(s): e.g.
      "Vienna/Fairfax-GMU" → "Vienna Metro"
      "Ashburn Station"    → "Ashburn Metro"
    """
    # Strip common suffixes
    clean = re.split(r"[/\-–—]", station_name)[0].strip()
    clean = re.sub(r"\s+(Metro|Station|Transit)\b.*", "", clean, flags=re.IGNORECASE)
    return f"{clean} Metro" if clean else "Transit"


# ── Virginia WMATA station → line corridor mapping ─────────────────────────
# Key is a lowercase substring that should match the resolved Google Places
# transit_station displayName. Value is the corridor label used on the cover.
_VA_METRO_CORRIDORS = {
    # Silver Line (VA segment)
    "ashburn": "Silver Line Corridor",
    "loudoun gateway": "Silver Line Corridor",
    "dulles": "Silver Line Corridor",
    "innovation center": "Silver Line Corridor",
    "herndon": "Silver Line Corridor",
    "reston town center": "Silver Line Corridor",
    "wiehle": "Silver Line Corridor",
    "spring hill": "Silver Line Corridor",
    "greensboro": "Silver Line Corridor",
    "tysons": "Silver Line Corridor",
    "mclean": "Silver Line Corridor",
    # Orange Line (VA segment)
    "vienna": "Orange Line Corridor",
    "fairfax-gmu": "Orange Line Corridor",
    "dunn loring": "Orange Line Corridor",
    "west falls church": "Orange Line Corridor",
    "east falls church": "Orange Line Corridor",
    "ballston": "Orange / Silver Line Corridor",
    "virginia square": "Orange / Silver Line Corridor",
    "clarendon": "Orange / Silver Line Corridor",
    "court house": "Orange / Silver Line Corridor",
    # Blue Line (VA segment)
    "franconia": "Blue Line Corridor",
    "springfield": "Blue Line Corridor",
    "van dorn": "Blue Line Corridor",
    "king st": "Blue / Yellow Line Corridor",
    "king street": "Blue / Yellow Line Corridor",
    "braddock": "Blue / Yellow Line Corridor",
    "eisenhower": "Yellow Line Corridor",
    "huntington": "Yellow Line Corridor",
    # Rosslyn–Pentagon stretch (Blue/Orange/Silver overlap on VA side)
    "rosslyn": "Blue / Orange / Silver Line Corridor",
    "arlington cemetery": "Blue Line Corridor",
    "pentagon city": "Blue / Yellow Line Corridor",
    "pentagon": "Blue / Yellow Line Corridor",
    "crystal city": "Blue / Yellow Line Corridor",
    "ronald reagan": "Blue / Yellow Line Corridor",
    "potomac yard": "Blue / Yellow Line Corridor",
}


def _transit_corridor(station_name: str) -> str:
    """Return the WMATA line corridor label for a resolved station name.

    Empty string when the station is not in the VA WMATA dict (e.g. out-of-region
    properties or non-rail transit stations returned by Google Places).
    """
    if not station_name:
        return ""
    normalized = station_name.lower()
    normalized = normalized.replace("\u2019", "").replace("'", "").replace(".", "")
    normalized = " ".join(normalized.split())
    for key, corridor in _VA_METRO_CORRIDORS.items():
        if key in normalized:
            return corridor
    return ""


# ── Public API ──────────────────────────────────────────────────────────────

def build_property_context(
    address: str, lat: float, lon: float, county: str
) -> dict:
    """Return a dict of ~15 property-identity keys for the OM template.

    Called first in generate_om.py so all downstream builders inherit
    correct property identity.

    Parameters
    ----------
    address : str
        Full address string as entered by the user (e.g. "21001 Sycolin Rd, Ashburn VA 20147").
    lat, lon : float
        Geocoded coordinates.
    county : str
        Lowercase county name from detect_county() (e.g. "loudoun").
    """
    street = _parse_street_address(address)
    street_short = _abbreviate_street(street)
    property_county = county.title() + " County"

    # ── Google API lookups ──────────────────────────────────────────────
    api_key = None
    try:
        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
    except Exception:
        pass

    # Reverse-geocode for city, ZIP, and state
    city = ""
    zip_code = ""
    state = ""
    state_abbr = ""
    if api_key:
        geo = _reverse_geocode(lat, lon, api_key)
        city = geo["city"]
        zip_code = geo["zip"]
        state = geo["state"]
        state_abbr = geo["state_abbr"]

    if not city:
        # Fallback: attempt to parse city from the address string
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 2:
            # Second segment often looks like "Ashburn VA 20147" or "Fairfax VA 22031"
            tokens = parts[1].split()
            if tokens:
                # Take all leading tokens that aren't a state abbr or ZIP
                city_tokens = []
                for t in tokens:
                    if re.match(r"^[A-Z]{2}$", t) or re.match(r"^\d{5}", t):
                        break
                    city_tokens.append(t)
                city = " ".join(city_tokens) if city_tokens else ""

    if not zip_code:
        # Fallback: parse ZIP from the portion after the street (city/state/ZIP)
        after_street = address.split(",", 1)[1] if "," in address else address
        m = re.search(r"\b(\d{5})(?:-\d{4})?\b", after_street)
        if m:
            zip_code = m.group(1)

    # Metro station lookup
    metro_station_name = "See broker for transit details"
    metro_badge_text = "Transit"
    metro_distance = "\u2014"
    mlat = None
    mlon = None

    if api_key:
        metro = _nearest_place(
            lat,
            lon,
            "subway_station",
            api_key,
            radius_m=16093,
            rank_preference="DISTANCE",
        )
        if metro:
            name = metro.get("displayName", {}).get("text", "")
            if name:
                metro_station_name = name
                metro_badge_text = _metro_badge(name)
                loc = metro.get("location", {})
                mlat = loc.get("latitude")
                mlon = loc.get("longitude")
                if mlat is not None and mlon is not None:
                    dist = _haversine_miles(lat, lon, mlat, mlon)
                    metro_distance = f"{dist:.1f} mi"
    else:
        logger.warning("GOOGLE_MAPS_API_KEY not available for property context lookups")

    # University lookup (10-mile radius = 16093 m)
    university_name_short = "See broker"
    university_distance = "\u2014"

    if api_key:
        uni = _nearest_place(lat, lon, "university", api_key, radius_m=16093)
        if uni:
            name = uni.get("displayName", {}).get("text", "")
            if name:
                # Shorten: first strip " - <suffix>" (e.g. "- Loudoun Campus"),
                # then drop a trailing "University" / "College" word.
                short = name
                if " - " in short:
                    short = short[:short.index(" - ")]
                short = re.sub(
                    r"\s*(University|College)\s*$", "", short, flags=re.IGNORECASE
                ).strip()
                university_name_short = short or name
                loc = uni.get("location", {})
                ulat = loc.get("latitude")
                ulon = loc.get("longitude")
                if ulat is not None and ulon is not None:
                    dist = _haversine_miles(lat, lon, ulat, ulon)
                    university_distance = f"{dist:.1f} mi"

    # Transit corridor derived from resolved metro station name
    transit_corridor = _transit_corridor(metro_station_name)

    # Report date
    report_date = datetime.now().strftime("%B %Y")

    # Submarket — default to city name; broker can override later
    submarket_name = city if city else "See broker"  # TODO: broker input

    return {
        "property_name": street,  # TODO: broker input — marketing name
        "property_address": street,
        "property_address_short": street_short,
        "property_city": city or "See broker",
        "property_state": state or "\u2014",
        "property_state_abbr": state_abbr or "\u2014",
        "property_zip": zip_code or "\u2014",
        "property_county": property_county,
        "submarket_name": submarket_name,  # TODO: broker input
        "transit_corridor": transit_corridor,
        "metro_station_name": metro_station_name,
        "metro_badge_text": metro_badge_text,
        "metro_distance": metro_distance,
        "metro_lat": mlat,
        "metro_lon": mlon,
        "university_name_short": university_name_short,
        "university_distance": university_distance,
        "report_date": report_date,
        # Owned by property_context.py — source of truth for downstream builders
        "employer_map_center_lat": lat,
        "employer_map_center_lon": lon,
        "employers_county": county,
    }
