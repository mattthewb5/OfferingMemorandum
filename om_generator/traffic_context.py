"""
Traffic Context Builder for OM Generator

Wires VDOT Average Daily Traffic (ADT) data into the template variable
structure expected by context_sample.py / location_analysis.html.

Supports Fairfax County (CSV-backed) and Loudoun County (GeoJSON-backed).

Usage:
    from traffic_context import build_traffic_context
    ctx = build_traffic_context(lat=38.8731, lon=-77.2689, county='fairfax')
"""

import logging
import math
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

# Data paths
_FAIRFAX_CSV = (
    _REPO_ROOT / "multi-county-real-estate-research" / "data" / "fairfax"
    / "traffic" / "raw" / "fairfax_vdot_traffic.csv"
)

_SAFE_DEFAULTS = {
    "traffic": {
        "primary_road_name": "",
        "primary_road_count": "",
        "secondary_road_name": "",
        "secondary_road_count": "",
    }
}

# Common display names for Virginia routes (used when road_name is a cross-street)
_ROUTE_DISPLAY = {
    "I-66": "I-66",
    "I-95": "I-95",
    "I-495": "I-495 / Capital Beltway",
    "I-395": "I-395",
    "US-29": "Lee Hwy (Rt. 29)",
    "US-50": "Arlington Blvd (Rt. 50)",
    "US-1": "Richmond Hwy (US-1)",
    "VA-7": "Leesburg Pike (Rt. 7)",
    "VA-28": "Sully Rd (Rt. 28)",
    "VA-123": "Chain Bridge Rd (Rt. 123)",
    "VA-236": "Little River Tpke (Rt. 236)",
    "VA-267": "Dulles Toll Rd (Rt. 267)",
    "VA-286": "Fairfax County Pkwy (Rt. 286)",
}


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles."""
    R = 3959
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _format_adt(adt_value):
    """Format ADT as comma-separated string (e.g. '42,000')."""
    rounded = round(adt_value / 1000) * 1000
    return f"{rounded:,}"


def _route_prefix(route_name):
    """Extract route prefix like 'I-66', 'US-29', 'VA-236' from route_name."""
    m = re.match(r"((?:I|US|VA)-\d+)", str(route_name))
    return m.group(1) if m else None


def _build_fairfax(lat, lon):
    """Build traffic context from Fairfax VDOT CSV data."""
    import pandas as pd

    if not _FAIRFAX_CSV.exists():
        logger.warning("Fairfax VDOT traffic CSV not found: %s", _FAIRFAX_CSV)
        return _SAFE_DEFAULTS

    df = pd.read_csv(_FAIRFAX_CSV)

    # Calculate distance from subject property
    df["_dist"] = df.apply(
        lambda r: _haversine(lat, lon, r["latitude"], r["longitude"]), axis=1
    )

    # Filter: ADT > 10,000, within 3 miles, exclude ramp segments
    major = df[
        (df["adt"] > 10000)
        & (df["_dist"] <= 3.0)
        & (~df["road_name"].str.contains("RAMP", case=False, na=False))
    ].copy()

    if major.empty:
        logger.warning("No major roads (ADT > 10,000) found within 3 mi of (%.4f, %.4f)", lat, lon)
        return _SAFE_DEFAULTS

    # Extract route prefix and group by it
    major["_route"] = major["route_name"].apply(_route_prefix)
    major = major.dropna(subset=["_route"])

    if major.empty:
        logger.warning("No classifiable routes found near (%.4f, %.4f)", lat, lon)
        return _SAFE_DEFAULTS

    # Group by route prefix: median ADT, closest distance
    routes = []
    for route, grp in major.groupby("_route"):
        med_adt = int(grp["adt"].median())
        min_dist = grp["_dist"].min()
        is_interstate = route.startswith("I-")
        routes.append({
            "route": route,
            "adt": med_adt,
            "dist": min_dist,
            "is_interstate": is_interstate,
        })

    # Classify: best interstate vs best non-interstate
    interstates = sorted(
        [r for r in routes if r["is_interstate"]], key=lambda r: r["adt"], reverse=True
    )
    local_roads = sorted(
        [r for r in routes if not r["is_interstate"]], key=lambda r: r["adt"], reverse=True
    )

    if interstates and local_roads:
        primary = local_roads[0]
        secondary = interstates[0]
    elif len(routes) >= 2:
        by_adt = sorted(routes, key=lambda r: r["adt"], reverse=True)
        primary = by_adt[0]
        secondary = by_adt[1]
    else:
        primary = routes[0]
        secondary = None

    def display_name(rec):
        route = rec["route"]
        return _ROUTE_DISPLAY.get(route, route)

    result = {
        "traffic": {
            "primary_road_name": display_name(primary),
            "primary_road_count": _format_adt(primary["adt"]),
            "secondary_road_name": display_name(secondary) if secondary else "",
            "secondary_road_count": _format_adt(secondary["adt"]) if secondary else "",
        }
    }

    logger.info(
        "Traffic context: primary=%s (%s ADT), secondary=%s (%s ADT)",
        result["traffic"]["primary_road_name"],
        result["traffic"]["primary_road_count"],
        result["traffic"]["secondary_road_name"],
        result["traffic"]["secondary_road_count"],
    )

    return result


def _build_loudoun(lat, lon):
    """Build traffic context from Loudoun VDOT GeoJSON data."""
    try:
        from core.loudoun_traffic_volume import LoudounTrafficVolumeAnalyzer
    except ImportError:
        logger.warning("Could not import LoudounTrafficVolumeAnalyzer")
        return _SAFE_DEFAULTS

    analyzer = LoudounTrafficVolumeAnalyzer()
    if not analyzer.data_loaded:
        logger.warning("Loudoun traffic data not loaded")
        return _SAFE_DEFAULTS

    # Find the two nearest high-ADT road segments
    # Use coordinate-based lookup with increasing radius
    import json

    traffic_file = (
        _REPO_ROOT / "multi-county-real-estate-research" / "data" / "loudoun"
        / "gis" / "traffic" / "vdot_traffic_volume.geojson"
    )

    if not traffic_file.exists():
        logger.warning("Loudoun traffic GeoJSON not found")
        return _SAFE_DEFAULTS

    with open(traffic_file, "r") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        logger.warning("No features in Loudoun traffic GeoJSON")
        return _SAFE_DEFAULTS

    # Calculate distance and ADT for each feature
    candidates = []
    for feat in features:
        props = feat.get("properties", {})
        adt = props.get("ADT", 0)
        if not adt or adt < 10000:
            continue

        geometry = feat.get("geometry", {})
        coords = geometry.get("coordinates", [])
        if not coords:
            continue

        # Handle MultiLineString
        if geometry.get("type") == "MultiLineString":
            all_coords = [c for line in coords for c in line]
        else:
            all_coords = coords

        # Find minimum distance to this road segment
        min_dist = float("inf")
        for coord in all_coords:
            lon2, lat2 = coord[0], coord[1]
            d = _haversine(lat, lon, lat2, lon2)
            if d < min_dist:
                min_dist = d

        if min_dist <= 3.0:
            route_common = props.get("ROUTE_COMMON_NAME", "")
            route_name = props.get("ROUTE_NAME", "")
            route_alias = str(props.get("ROUTE_ALIAS", "")).strip()
            candidates.append({
                "route_common": route_common,
                "route_name": route_name,
                "route_alias": route_alias,
                "adt": adt,
                "dist": min_dist,
                "is_interstate": "I-" in route_common or "I-" in route_name,
            })

    if not candidates:
        logger.warning("No major roads (ADT > 10,000) found within 3 mi for Loudoun")
        return _SAFE_DEFAULTS

    # Deduplicate by route prefix (e.g., VA-7, I-66) — merge directions
    by_route = {}
    for c in candidates:
        prefix = _route_prefix(c["route_common"]) or c["route_common"]
        if prefix not in by_route or c["adt"] > by_route[prefix]["adt"]:
            by_route[prefix] = c
            by_route[prefix]["_prefix"] = prefix
    deduped = list(by_route.values())

    interstates = [r for r in deduped if r["is_interstate"]]
    local_roads = [r for r in deduped if not r["is_interstate"]]
    interstates.sort(key=lambda r: r["adt"], reverse=True)
    local_roads.sort(key=lambda r: r["adt"], reverse=True)

    if interstates and local_roads:
        primary = local_roads[0]
        secondary = interstates[0]
    elif len(deduped) >= 2:
        by_adt = sorted(deduped, key=lambda r: r["adt"], reverse=True)
        primary = by_adt[0]
        secondary = by_adt[1]
    else:
        primary = deduped[0]
        secondary = None

    def display_name(rec):
        alias = rec.get("route_alias", "").strip()
        route = rec.get("route_common", "")
        # Extract readable name from route_common like "VA-7E (Loudoun County)"
        m = re.search(r"((?:I|US|VA)-\d+)", route)
        route_key = m.group(1) if m else None
        # Use common display name if available
        if route_key and route_key in _ROUTE_DISPLAY:
            return _ROUTE_DISPLAY[route_key]
        if alias and m:
            return f"{alias} ({m.group(1)})"
        if m:
            return m.group(1)
        return route or "Unknown"

    result = {
        "traffic": {
            "primary_road_name": display_name(primary),
            "primary_road_count": _format_adt(primary["adt"]),
            "secondary_road_name": display_name(secondary) if secondary else "",
            "secondary_road_count": _format_adt(secondary["adt"]) if secondary else "",
        }
    }

    logger.info(
        "Traffic context (Loudoun): primary=%s (%s ADT), secondary=%s (%s ADT)",
        result["traffic"]["primary_road_name"],
        result["traffic"]["primary_road_count"],
        result["traffic"]["secondary_road_name"],
        result["traffic"]["secondary_road_count"],
    )

    return result


def build_traffic_context(lat: float, lon: float, county: str) -> dict:
    """
    Build traffic context dict for the OM template.

    Finds the nearest major road segments to (lat, lon) and returns their
    ADT counts from VDOT data.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: County name (e.g. 'fairfax', 'loudoun')

    Returns:
        Dict matching context_sample.py traffic keys with live data.
    """
    try:
        county_lower = county.lower().strip()
        if county_lower == "fairfax":
            return _build_fairfax(lat, lon)
        elif county_lower == "loudoun":
            return _build_loudoun(lat, lon)
        else:
            logger.warning(
                "Traffic data not available for county '%s'. Returning safe defaults.", county
            )
            return _SAFE_DEFAULTS
    except Exception:
        logger.warning("Traffic context builder failed", exc_info=True)
        return _SAFE_DEFAULTS
