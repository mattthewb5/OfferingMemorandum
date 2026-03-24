"""
Zoning Context Module — dual-county (Fairfax + Loudoun).

Provides build_zoning_context(lat, lon, county) → dict with zoning intelligence
keys consumed by the development_intelligence.html template and the planning_pts
component of _compute_sub_scores() in development_context.py.

Contributes up to 15 points to the development score via planning_pts.

Scoring uses the same 3-factor framework as loudoun_zoning_analysis.py:
  mismatch (40 pts) + restrictiveness (30 pts) + pressure (30 pts) = 0-100
  Scaled to 0-15 via round(score / 100 * 15).
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# ── Path anchors ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_RESEARCH = _ROOT / "multi-county-real-estate-research"

_FAIRFAX_CONFIG = _RESEARCH / "data" / "fairfax" / "config"
_FAIRFAX_COMP_PLAN = _RESEARCH / "data" / "fairfax" / "Comprehensive_Plan" / "processed"
_FAIRFAX_ZONING_ZIP = _RESEARCH / "data" / "fairfax" / "gis" / "zoning" / "raw" / "Zoning.zip"

_LOUDOUN_CONFIG = _RESEARCH / "data" / "loudoun" / "config"

# ── Fairfax REST endpoint ────────────────────────────────────────────────────
FAIRFAX_ZONING_ENDPOINT = (
    "https://services1.arcgis.com/ioennV6PpG5Xodq0"
    "/arcgis/rest/services/Zoning/FeatureServer/0/query"
)

# plan_area names that are actual growth centers (CBCs, TSAs, Suburban Centers)
_GROWTH_CENTER_PLAN_AREAS = {
    # CBCs
    "Annandale CBC", "Baileys Crossroads CBC", "Beacon/Groveton CBC",
    "Hybla Valley/Gum Springs CBC", "Kingstowne CBC", "Lincolnia CBC",
    "McLean CBC", "North Gateway CBC", "Penn Daw CBC", "Seven Corners CBC",
    "South County Center CBC", "Springfield CBC", "Woodlawn CBC",
    # TSAs
    "Franconia-Springfield TSA", "Herndon TSA", "Huntington TSA",
    "Reston Town Center TSA", "Van Dorn TSA", "Vienna TSA",
    "West Falls Church TSA", "Wiehle-Reston East TSA",
    # Suburban Centers & Named Areas
    "Dulles (Route 28 Corridor) Suburban Center", "Fairfax Center Area",
    "Flint Hill Suburban Center", "Merrifield Suburban Center",
    "Lorton-South Route 1 Suburban Center", "Centreville Area",
    # Industrial Areas
    "Beltway South Industrial Area", "I-95 Corridor Industrial Area",
    "Ravensworth Industrial Area",
    # Other named plan areas
    "Lake Anne Village Center", "Laurel Hill CPS LP1",
}


# ═════════════════════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def build_zoning_context(lat: float, lon: float, county: str) -> dict:
    """Build zoning intelligence context for the OM template.

    Args:
        lat: Property latitude
        lon: Property longitude
        county: 'fairfax' or 'loudoun'

    Returns:
        Dict with zoning_code_slash, comp_plan_designation, growth_center_distance,
        upzoning_risk, zoning_narrative, planning_pts (0-15), and related keys.
    """
    county_lower = county.strip().lower()
    try:
        if county_lower == "loudoun":
            return _build_zoning_context_loudoun(lat, lon)
        elif county_lower == "fairfax":
            return _build_zoning_context_fairfax(lat, lon)
        else:
            return _zoning_safe_defaults(county)
    except Exception as e:
        print(f"WARNING in build_zoning_context: {e}", file=sys.stderr)
        return _zoning_safe_defaults(county)


# ═════════════════════════════════════════════════════════════════════════════
#  FAIRFAX IMPLEMENTATION
# ═════════════════════════════════════════════════════════════════════════════

def _build_zoning_context_fairfax(lat: float, lon: float) -> dict:
    """Build Fairfax County zoning context."""
    # Load translation files
    zoning_trans = _load_json(_FAIRFAX_CONFIG / "fairfax_zoning_translations.json")
    comp_plan_trans = _load_json(_FAIRFAX_CONFIG / "fairfax_comp_plan_translations.json")

    static_trans = zoning_trans.get("static_translations", {}) if zoning_trans else {}
    cp_trans = comp_plan_trans.get("translations", {}) if comp_plan_trans else {}

    # 1. Zoning lookup — REST API primary, file fallback
    zoning_result = _fairfax_zoning_rest(lat, lon)
    if not zoning_result:
        zoning_result = _fairfax_zoning_file_fallback(lat, lon)

    zoning_code = zoning_result.get("zonecode", "N/A") if zoning_result else "N/A"
    zonetype = zoning_result.get("zonetype", "") if zoning_result else ""
    jurisdiction = zoning_result.get("jurisdiction", "FAIRFAX COUNTY") if zoning_result else "FAIRFAX COUNTY"

    # Translate zoning code
    zt = static_trans.get(zoning_code, {})
    zoning_name = zt.get("official_name", f"Zoning District {zoning_code}")
    zoning_character = zt.get("character", zonetype.title() if zonetype else "")
    zoning_intensity = zt.get("intensity", 3)

    # 2. Comp plan designation
    comp_plan_result = _fairfax_comp_plan_lookup(lat, lon)
    land_use_key = comp_plan_result.get("land_use_key", "N/A") if comp_plan_result else "N/A"

    cpt = cp_trans.get(land_use_key, {})
    comp_plan_designation = cpt.get("official_name", land_use_key)
    comp_plan_intensity = cpt.get("intensity", 3)

    # 3. Growth center distance
    gc_name, gc_distance_raw = _fairfax_growth_center_distance(lat, lon)

    # 4. Scoring — 3-factor framework (mismatch + restrictiveness + pressure)
    score_100 = _compute_fairfax_score(zoning_intensity, comp_plan_intensity)
    planning_pts = min(15, round(score_100 / 100 * 15))

    # Upzoning risk label using classify_development_risk thresholds
    upzoning_risk = _classify_upzoning_risk(score_100)

    # 5. Narrative
    juris_label = _format_jurisdiction(jurisdiction)
    zoning_narrative = _generate_fairfax_narrative(
        zoning_code, zoning_name, comp_plan_designation,
        gc_name, gc_distance_raw, upzoning_risk, juris_label
    )

    # Format keys to match existing template variables in _assemble_result()
    if gc_distance_raw is not None:
        growth_center_distance = f"{gc_distance_raw:.1f} mi — {gc_name}"
    else:
        growth_center_distance = "N/A"

    if zoning_code != "N/A":
        zoning_code_slash = f"{zoning_code} / {zoning_name}"
    else:
        zoning_code_slash = "N/A"

    return {
        # Keys matching existing template variables (development_context.py:446-450)
        "zoning_code_slash": zoning_code_slash,
        "comp_plan_designation": comp_plan_designation,
        "growth_center_distance": growth_center_distance,
        "upzoning_risk": upzoning_risk,
        "zoning_narrative": zoning_narrative,
        # Additional keys
        "zoning_code": zoning_code,
        "zoning_name": zoning_name,
        "zoning_character": zoning_character,
        "growth_center_name": gc_name,
        "growth_center_distance_raw": gc_distance_raw,
        "planning_pts": planning_pts,
        "zoning_county": "Fairfax",
        "zoning_jurisdiction": juris_label,
    }


def _fairfax_zoning_rest(lat: float, lon: float) -> Optional[dict]:
    """Query Fairfax zoning via ArcGIS REST endpoint."""
    try:
        x, y = _wgs84_to_web_mercator(lon, lat)
        params = {
            "geometry": f"{x},{y}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "ZONECODE,ZONETYPE,JURISDICTION",
            "returnGeometry": "false",
            "f": "json",
            "inSR": "3857",
        }
        resp = requests.get(FAIRFAX_ZONING_ENDPOINT, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        features = data.get("features", [])
        if not features:
            return None

        attrs = features[0].get("attributes", {})
        return {
            "zonecode": attrs.get("ZONECODE", ""),
            "zonetype": attrs.get("ZONETYPE", ""),
            "jurisdiction": attrs.get("JURISDICTION", "FAIRFAX COUNTY"),
        }
    except Exception as e:
        print(f"  Fairfax zoning REST failed: {e}", file=sys.stderr)
        return None


def _fairfax_zoning_file_fallback(lat: float, lon: float) -> Optional[dict]:
    """Fallback: load zoning from local shapefile."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        if not _FAIRFAX_ZONING_ZIP.exists():
            return None

        gdf = gpd.read_file(f"zip://{_FAIRFAX_ZONING_ZIP}")
        gdf = gdf.to_crs(epsg=4326)

        point = Point(lon, lat)
        mask = gdf.geometry.contains(point)
        matches = gdf[mask]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "zonecode": row.get("ZONECODE", ""),
            "zonetype": row.get("ZONETYPE", ""),
            "jurisdiction": row.get("JURISDICTI", "FAIRFAX COUNTY"),
        }
    except Exception as e:
        print(f"  Fairfax zoning file fallback failed: {e}", file=sys.stderr)
        return None


def _fairfax_comp_plan_lookup(lat: float, lon: float) -> Optional[dict]:
    """Spatial join point against comp_plan_base_recommendation.geoparquet."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        parquet_path = _FAIRFAX_COMP_PLAN / "comp_plan_base_recommendation.geoparquet"
        if not parquet_path.exists():
            return None

        gdf = gpd.read_parquet(parquet_path)
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        point = Point(lon, lat)
        mask = gdf.geometry.contains(point)
        matches = gdf[mask]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "land_use_key": row.get("land_use_key", ""),
            "land_use_type": row.get("land_use_type", ""),
        }
    except Exception as e:
        print(f"  Fairfax comp plan lookup failed: {e}", file=sys.stderr)
        return None


def _fairfax_growth_center_distance(lat: float, lon: float) -> tuple:
    """Calculate distance to nearest CBC/TSA/Suburban Center.

    Returns:
        (name: str, distance_miles: float|None)
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point

        parquet_path = _FAIRFAX_COMP_PLAN / "comp_plan_land_units.geoparquet"
        if not parquet_path.exists():
            return ("N/A", None)

        gdf = gpd.read_parquet(parquet_path)
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Filter to growth center plan areas only
        gc_gdf = gdf[gdf["plan_area"].isin(_GROWTH_CENTER_PLAN_AREAS)].copy()
        if gc_gdf.empty:
            return ("N/A", None)

        # Fix invalid geometries before dissolve
        from shapely.validation import make_valid
        gc_gdf["geometry"] = gc_gdf.geometry.apply(
            lambda g: make_valid(g) if g is not None and not g.is_valid else g
        )

        # Dissolve by plan_area to get one polygon per center
        gc_dissolved = gc_gdf.dissolve(by="plan_area").reset_index()
        gc_dissolved["geometry"] = gc_dissolved.geometry.apply(
            lambda g: make_valid(g) if g is not None and not g.is_valid else g
        )

        point = Point(lon, lat)

        # Check if point is inside any growth center
        inside = gc_dissolved[gc_dissolved.geometry.contains(point)]
        if not inside.empty:
            return (inside.iloc[0]["plan_area"], 0.0)

        # Find nearest boundary
        min_dist = float("inf")
        nearest_name = "N/A"

        for _, row in gc_dissolved.iterrows():
            try:
                dist_deg = point.distance(row.geometry)
                # Approximate degrees to miles at this latitude (~38.8°N)
                dist_miles = dist_deg * 69.0
                if dist_miles < min_dist:
                    min_dist = dist_miles
                    nearest_name = row["plan_area"]
            except Exception:
                continue

        return (nearest_name, round(min_dist, 1))

    except Exception as e:
        print(f"  Fairfax growth center distance failed: {e}", file=sys.stderr)
        return ("N/A", None)


# ═════════════════════════════════════════════════════════════════════════════
#  LOUDOUN IMPLEMENTATION
# ═════════════════════════════════════════════════════════════════════════════

def _build_zoning_context_loudoun(lat: float, lon: float) -> dict:
    """Build Loudoun County zoning context by reusing loudoun_zoning_analysis.py."""
    from core.loudoun_zoning_analysis import (
        get_zoning_data_loudoun,
        get_place_type_loudoun,
        detect_jurisdiction,
        calculate_development_probability_loudoun,
        classify_development_risk,
        get_plain_english_zoning,
    )

    print("  [Loudoun] Calling loudoun_zoning_analysis.py functions...")

    # Get zoning data
    jurisdiction_info = detect_jurisdiction(lat, lon)
    jurisdiction = jurisdiction_info.get("jurisdiction", "LOUDOUN")
    town_name = jurisdiction_info.get("town_name", "")

    zoning_data = get_zoning_data_loudoun(lat, lon)
    zoning_code = zoning_data.get("zoning", "N/A")
    zoning_desc = zoning_data.get("zoning_description", "")

    # Get place type (comp plan equivalent)
    place_type_data = get_place_type_loudoun(lat, lon)
    place_type = place_type_data.get("place_type", "")
    place_type_code = place_type_data.get("place_type_code", "")
    policy_area = place_type_data.get("policy_area", "")

    # Get plain English translation
    zoning_translation = get_plain_english_zoning(zoning_code)
    if zoning_translation.get("success"):
        zoning_name = zoning_translation.get("official_name", zoning_desc)
        zoning_character = zoning_translation.get("character", "")
    else:
        zoning_name = zoning_desc
        zoning_character = ""

    # Score: Loudoun's 0-100 scale → 0-15 planning_pts
    loudoun_score = calculate_development_probability_loudoun(
        zoning_code, place_type, jurisdiction
    )
    planning_pts = min(15, round(loudoun_score / 100 * 15))

    risk_level = classify_development_risk(loudoun_score)

    # Map risk level to upzoning_risk label
    upzoning_risk = _risk_level_to_upzoning_label(risk_level)

    # Growth center: infer from place type
    gc_name, gc_distance_raw = _loudoun_growth_center_from_place_type(
        place_type, place_type_code, policy_area
    )

    # Comp plan designation = place type name
    comp_plan_designation = place_type if place_type else "N/A"

    # Narrative
    jurisdiction_label = town_name if town_name else "Loudoun County"
    zoning_narrative = _generate_loudoun_narrative(
        zoning_code, zoning_name, comp_plan_designation,
        gc_name, gc_distance_raw, upzoning_risk, jurisdiction_label
    )

    # Format template keys
    if gc_distance_raw is not None:
        growth_center_distance = f"{gc_distance_raw:.1f} mi — {gc_name}"
    else:
        growth_center_distance = "N/A"

    if zoning_code != "N/A" and zoning_name:
        zoning_code_slash = f"{zoning_code} / {zoning_name}"
    else:
        zoning_code_slash = zoning_code

    return {
        "zoning_code_slash": zoning_code_slash,
        "comp_plan_designation": comp_plan_designation,
        "growth_center_distance": growth_center_distance,
        "upzoning_risk": upzoning_risk,
        "zoning_narrative": zoning_narrative,
        "zoning_code": zoning_code,
        "zoning_name": zoning_name,
        "zoning_character": zoning_character,
        "growth_center_name": gc_name,
        "growth_center_distance_raw": gc_distance_raw,
        "planning_pts": planning_pts,
        "zoning_county": "Loudoun",
        "zoning_jurisdiction": jurisdiction_label,
    }


def _loudoun_growth_center_from_place_type(
    place_type: str, place_type_code: str, policy_area: str
) -> tuple:
    """Infer growth center proximity from Loudoun place type.

    Returns:
        (name: str, distance_miles: float|None)
    """
    pt_upper = (place_type or "").upper()
    code_upper = (place_type_code or "").upper()

    # Highest-growth types → within growth area
    if any(kw in pt_upper for kw in ["URBAN TRANSIT", "TOWN CENTER", "METROPOLITAN"]):
        return (place_type, 0.0)
    if code_upper in ("URBTC", "URBMUS"):
        return (place_type, 0.0)

    # Suburban mixed use / compact → within growth corridor
    if any(kw in pt_upper for kw in ["SUBURBAN MIXED USE", "SUBURBAN COMPACT"]):
        return (place_type, 0.0)
    if code_upper in ("SUBMUS", "SUBCMP", "SUBEM", "SUBCOM", "SUBIM"):
        return (place_type, 0.0)

    # Suburban neighborhood → near growth area
    if "SUBURBAN NEIGHBORHOOD" in pt_upper or code_upper == "SUBNBR":
        return ("Suburban Neighborhood corridor", 0.5)

    # Transition → moderate distance
    if "TRANSITION" in pt_upper or code_upper.startswith("TRN"):
        return ("Transition area", 2.0)

    # Rural → outside growth area
    if any(kw in pt_upper for kw in ["RURAL", "AGRICULTURAL"]):
        return ("Outside designated growth area", 5.0)
    if code_upper.startswith("RUR"):
        return ("Outside designated growth area", 5.0)

    # JLMA → established area
    if "JLMA" in pt_upper:
        return ("JLMA administrative area", 1.0)

    # Default
    return (policy_area if policy_area else "N/A", 1.0)


# ═════════════════════════════════════════════════════════════════════════════
#  SCORING — 3-factor framework (mirrors loudoun_zoning_analysis.py)
# ═════════════════════════════════════════════════════════════════════════════

def _compute_fairfax_score(zoning_intensity: int, comp_plan_intensity: int) -> int:
    """Compute 0-100 development probability score for Fairfax.

    Uses the same 3-factor framework as calculate_development_probability_loudoun():
      Factor 1: Mismatch (0-40) — gap between current zoning and comp plan
      Factor 2: Restrictiveness (0-30) — how restrictive current zoning is, scaled
      Factor 3: Pressure (0-30) — comp plan development pressure, scaled

    Both restrictiveness and pressure are scaled by intensity_diff alignment.
    """
    intensity_diff = comp_plan_intensity - zoning_intensity

    # Factor 1: Mismatch (0-40 pts)
    if intensity_diff >= 2:
        mismatch = 40
    elif intensity_diff == 1:
        mismatch = 15
    elif intensity_diff == 0:
        mismatch = 5
    else:
        mismatch = 0

    # Factor 2: Restrictiveness (0-30 pts base, scaled by alignment)
    # More restrictive zoning = higher base score
    restrictiveness_map = {1: 30, 2: 20, 3: 15, 4: 10, 5: 5}
    raw_restrictiveness = restrictiveness_map.get(zoning_intensity, 15)
    if intensity_diff <= 0:
        restrictiveness = raw_restrictiveness // 6
    elif intensity_diff == 1:
        restrictiveness = raw_restrictiveness // 2
    else:
        restrictiveness = raw_restrictiveness

    # Factor 3: Pressure (0-30 pts base, scaled by alignment)
    # Higher comp plan intensity = higher base pressure
    pressure_map = {5: 30, 4: 20, 3: 10, 2: 5, 1: 5}
    raw_pressure = pressure_map.get(comp_plan_intensity, 10)
    if intensity_diff <= 0:
        pressure = raw_pressure // 6
    elif intensity_diff == 1:
        pressure = raw_pressure // 2
    else:
        pressure = raw_pressure

    return min(mismatch + restrictiveness + pressure, 100)


def _classify_upzoning_risk(score: int) -> str:
    """Classify upzoning risk using classify_development_risk thresholds."""
    risk_level = _score_to_risk_level(score)
    return _risk_level_to_upzoning_label(risk_level)


def _score_to_risk_level(score: int) -> str:
    """Same thresholds as classify_development_risk in loudoun_zoning_analysis.py."""
    if score >= 76:
        return "Very High"
    elif score >= 51:
        return "High"
    elif score >= 26:
        return "Moderate"
    else:
        return "Low"


def _risk_level_to_upzoning_label(risk_level: str) -> str:
    """Map risk level to investor-facing upzoning risk label."""
    labels = {
        "Low": "Low \u2014 Consistent with comp plan",
        "Moderate": "Moderate \u2014 Upzoning opportunity exists",
        "High": "High \u2014 Significant zoning/comp plan mismatch",
        "Very High": "Very High \u2014 Major redevelopment pressure",
    }
    return labels.get(risk_level, "N/A")


# ═════════════════════════════════════════════════════════════════════════════
#  NARRATIVE GENERATION
# ═════════════════════════════════════════════════════════════════════════════

def _generate_fairfax_narrative(
    zoning_code: str, zoning_name: str, comp_plan_designation: str,
    gc_name: str, gc_distance: Optional[float], upzoning_risk: str,
    jurisdiction_label: str,
) -> str:
    """Generate 2-4 sentence zoning narrative for Fairfax."""
    if zoning_code == "N/A":
        return "Zoning analysis is not available for this property."

    parts = [
        f"The subject property is zoned {zoning_code} ({zoning_name}) "
        f"under {jurisdiction_label}\u2019s zoning ordinance"
    ]

    if comp_plan_designation and comp_plan_designation != "N/A":
        parts[0] += (
            f", consistent with the Comprehensive Plan\u2019s "
            f"{comp_plan_designation} designation for this corridor."
        )
    else:
        parts[0] += "."

    if gc_name and gc_name != "N/A" and gc_distance is not None:
        if gc_distance == 0.0:
            parts.append(
                f"The property is located within the {gc_name}, "
                f"one of Fairfax County\u2019s designated high-density activity centers."
            )
        else:
            parts.append(
                f"The property sits {gc_distance:.1f} miles from the {gc_name} boundary, "
                f"one of Fairfax County\u2019s designated activity centers."
            )

    if "Low" in upzoning_risk:
        parts.append(
            "The current zoning is well-aligned with the county\u2019s long-term vision "
            "for this area, suggesting limited entitlement risk and stable land use "
            "expectations for investors."
        )
    elif "Moderate" in upzoning_risk:
        parts.append(
            "A moderate gap between current zoning and the comp plan designation "
            "suggests potential upzoning opportunity, which could enhance long-term "
            "property value if entitlements are pursued."
        )
    else:
        parts.append(
            "A significant mismatch between current zoning and the comprehensive plan "
            "indicates meaningful redevelopment pressure in this corridor, presenting "
            "both opportunity and entitlement risk for investors."
        )

    return " ".join(parts)


def _generate_loudoun_narrative(
    zoning_code: str, zoning_name: str, comp_plan_designation: str,
    gc_name: str, gc_distance: Optional[float], upzoning_risk: str,
    jurisdiction_label: str,
) -> str:
    """Generate 2-4 sentence zoning narrative for Loudoun."""
    if zoning_code == "N/A":
        return "Zoning analysis is not available for this property."

    parts = [f"The subject property is zoned {zoning_code}"]
    if zoning_name:
        parts[0] += f" ({zoning_name})"
    parts[0] += f" under {jurisdiction_label}\u2019s zoning ordinance."

    if comp_plan_designation and comp_plan_designation != "N/A":
        parts.append(
            f"The 2019 Comprehensive Plan designates this area as "
            f"{comp_plan_designation}."
        )

    if gc_name and gc_name != "N/A" and gc_distance is not None:
        if gc_distance == 0.0:
            parts.append(
                f"The property is within the {gc_name} growth designation."
            )
        elif gc_distance <= 2.0:
            parts.append(
                f"The property is approximately {gc_distance:.1f} miles from "
                f"the nearest growth area ({gc_name})."
            )

    if "Low" in upzoning_risk:
        parts.append(
            "Current zoning aligns with the comprehensive plan, indicating "
            "stable land use expectations."
        )
    elif "Moderate" in upzoning_risk:
        parts.append(
            "The comp plan envisions moderately higher intensity for this area, "
            "suggesting potential upzoning opportunity."
        )
    else:
        parts.append(
            "Significant gap between current zoning and planned intensity "
            "indicates meaningful redevelopment pressure."
        )

    return " ".join(parts)


# ═════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═════════════════════════════════════════════════════════════════════════════

def _load_json(path: Path) -> Optional[dict]:
    """Load a JSON file, returning None on any error."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _wgs84_to_web_mercator(lon: float, lat: float) -> tuple:
    """Convert WGS84 lon/lat to Web Mercator (EPSG:3857) x/y."""
    x = lon * 20037508.34 / 180.0
    y_rad = math.log(math.tan((90.0 + lat) * math.pi / 360.0))
    y = y_rad * 20037508.34 / math.pi
    return (x, y)


def _format_jurisdiction(jurisdiction: str) -> str:
    """Normalize jurisdiction string for narrative use."""
    mapping = {
        "FAIRFAX COUNTY": "Fairfax County",
        "TOWN OF HERNDON": "Town of Herndon",
        "TOWN OF VIENNA": "Town of Vienna",
    }
    return mapping.get(jurisdiction, jurisdiction.title())


def _zoning_safe_defaults(county: str = "unknown") -> dict:
    """Return safe defaults on any unrecoverable error."""
    return {
        "zoning_code_slash": "N/A",
        "comp_plan_designation": "N/A",
        "growth_center_distance": "N/A",
        "upzoning_risk": "N/A",
        "zoning_narrative": "Zoning analysis is not available for this property.",
        "zoning_code": "N/A",
        "zoning_name": "Zoning data unavailable",
        "zoning_character": "",
        "growth_center_name": "N/A",
        "growth_center_distance_raw": None,
        "planning_pts": 0,
        "zoning_county": county.title(),
        "zoning_jurisdiction": "N/A",
    }
