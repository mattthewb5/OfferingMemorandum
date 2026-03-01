"""
Fairfax County Comprehensive Plan Analysis

Provides future land use designation lookups via spatial point-in-polygon
queries against Fairfax County GIS Comprehensive Plan data.

Data:
- Comprehensive Plan Base Recommendation (2,958 polygons)
  Future land use designations covering all county land
- Comprehensive Plan Land Units (512 polygons)
  Planning area units (CBCs, TSAs, Suburban Centers)

GeoParquet files: data/fairfax/Comprehensive_Plan/processed/

Usage:
    from core.fairfax_comprehensive_plan_analysis import get_comp_plan_designation

    result = get_comp_plan_designation(38.918914, -77.401634)
    print(result['land_use_category'])  # "Residential — 2-3 DU/AC"
    print(result['narrative'])
"""

import logging
import math
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "Comprehensive_Plan" / "processed"

BASE_REC_PATH = DATA_DIR / "comp_plan_base_recommendation.geoparquet"
LAND_UNITS_PATH = DATA_DIR / "comp_plan_land_units.geoparquet"

LAND_USE_TYPE_MAP = {
    "01": "Residential",
    "02": "Commercial/Employment",
    "03": "Parks & Open Space",
    "04": "Public Facilities",
    "05": "Mixed Use",
}

EARTH_RADIUS_MI = 3959.0

# Module-level cache
_base_rec_gdf = None
_land_units_gdf = None
_base_rec_sindex = None
_land_units_sindex = None


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_MI * 2 * math.asin(math.sqrt(a))


def _load_data():
    """Load GeoParquet files into module-level cache."""
    global _base_rec_gdf, _land_units_gdf, _base_rec_sindex, _land_units_sindex

    if _base_rec_gdf is not None:
        return

    import geopandas as gpd

    if BASE_REC_PATH.exists():
        _base_rec_gdf = gpd.read_parquet(BASE_REC_PATH)
        _base_rec_sindex = _base_rec_gdf.sindex
        logger.info(f"Loaded comp plan base recommendation: {len(_base_rec_gdf)} polygons")
    else:
        logger.warning(f"Comp plan base recommendation not found: {BASE_REC_PATH}")

    if LAND_UNITS_PATH.exists():
        _land_units_gdf = gpd.read_parquet(LAND_UNITS_PATH)
        _land_units_sindex = _land_units_gdf.sindex
        logger.info(f"Loaded comp plan land units: {len(_land_units_gdf)} polygons")
    else:
        logger.warning(f"Comp plan land units not found: {LAND_UNITS_PATH}")


def _find_nearest_planning_area(lat: float, lon: float, max_miles: float = 3.0) -> Optional[Dict]:
    """Find nearest planning area within max_miles using centroid distance."""
    if _land_units_gdf is None or _land_units_gdf.empty:
        return None

    best_dist = float('inf')
    best_row = None

    for _, row in _land_units_gdf.iterrows():
        centroid = row.geometry.centroid
        dist = _haversine(lat, lon, centroid.y, centroid.x)
        if dist < best_dist:
            best_dist = dist
            best_row = row

    if best_dist <= max_miles and best_row is not None:
        return {
            'name': best_row['plan_area'],
            'geo_unit': best_row['geo_unit'],
            'geo_unit_type': best_row['geo_unit_type'],
            'distance_miles': round(best_dist, 1),
            'plan_url': best_row.get('plan_url', ''),
        }

    return None


def _build_narrative(result: Dict, zoning_code: str = "") -> str:
    """Build a 2-3 sentence human-readable narrative."""
    lu_type = result.get('land_use_type', '')
    lu_key = result.get('land_use_key', '')
    in_area = result.get('in_planning_area', False)
    area_name = result.get('planning_area_name')
    area_dist = result.get('planning_area_distance_mi')

    zoning_note = ""
    if zoning_code:
        zoning_note = f", consistent with current {zoning_code} zoning"

    if lu_type == 'Residential':
        base = (
            f"The Fairfax County Comprehensive Plan designates this area as "
            f"{lu_key} Residential density{zoning_note}."
        )
        if in_area and area_name:
            return (
                f"{base} The property is within the {area_name} planning area, "
                f"where the county envisions targeted development and investment."
            )
        elif area_name and area_dist and area_dist <= 1.0:
            return (
                f"{base} The property is {area_dist} miles from the "
                f"{area_name} planning area, where higher-density mixed-use "
                f"development is planned. This proximity may influence long-term "
                f"area character."
            )
        else:
            return (
                f"{base} This indicates a stable neighborhood with no planned "
                f"density changes. The plan supports continued residential use "
                f"in this established community."
            )

    elif lu_type == 'Mixed Use':
        return (
            f"The Fairfax County Comprehensive Plan designates this area for "
            f"Mixed Use development, indicating planned transformation toward "
            f"higher-density, multi-use development. This designation often "
            f"signals future commercial and residential investment activity in "
            f"the corridor."
        )

    elif lu_type == 'Commercial/Employment':
        return (
            f"The Fairfax County Comprehensive Plan designates this area as "
            f"{lu_key}{zoning_note}. Properties in commercially-designated areas "
            f"may experience increased traffic and development activity over time."
        )

    elif lu_type == 'Parks & Open Space':
        return (
            f"The Fairfax County Comprehensive Plan designates this area as "
            f"{lu_key}. This designation preserves open space and limits "
            f"future development in the immediate vicinity."
        )

    elif lu_type == 'Public Facilities':
        return (
            f"The Fairfax County Comprehensive Plan designates this area for "
            f"Public Facilities. This typically indicates government or "
            f"institutional use in the county's long-range plan."
        )

    return (
        "Comprehensive Plan designation data is available from Fairfax County GIS. "
        "Contact the Department of Planning and Development for site-specific guidance."
    )


def get_comp_plan_designation(
    lat: float,
    lon: float,
    zoning_code: str = "",
) -> Dict:
    """
    Get Comprehensive Plan designation for a given lat/lon.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)
        zoning_code: Optional current zoning code for narrative context

    Returns:
        Dict with keys:
        - land_use_type: str (e.g., "Residential", "Mixed Use")
        - land_use_key: str (e.g., "2-3 DU/AC", "Mixed Uses")
        - land_use_category: str (e.g., "Residential — 2-3 DU/AC")
        - in_planning_area: bool
        - planning_area_name: str or None
        - planning_area_distance_mi: float or None
        - planning_area_url: str or None
        - narrative: str
        - source: str
    """
    default = {
        'land_use_type': None,
        'land_use_key': None,
        'land_use_category': None,
        'in_planning_area': False,
        'planning_area_name': None,
        'planning_area_distance_mi': None,
        'planning_area_url': None,
        'narrative': '',
        'source': 'Fairfax County 2030 Comprehensive Plan (GIS)',
    }

    try:
        from shapely.geometry import Point

        _load_data()

        if _base_rec_gdf is None:
            default['narrative'] = 'Comprehensive Plan data not available.'
            return default

        point = Point(lon, lat)

        # Base Recommendation lookup
        possible_idx = list(_base_rec_sindex.intersection(point.bounds))
        if possible_idx:
            candidates = _base_rec_gdf.iloc[possible_idx]
            match = candidates[candidates.geometry.contains(point)]
            if not match.empty:
                row = match.iloc[0]
                type_code = row['landuse_type_code']
                default['land_use_type'] = LAND_USE_TYPE_MAP.get(type_code, type_code)
                default['land_use_key'] = row['land_use_key']
                default['land_use_category'] = (
                    f"{default['land_use_type']} — {default['land_use_key']}"
                )

        # Land Unit lookup — check if inside a planning area
        if _land_units_gdf is not None and _land_units_sindex is not None:
            lu_idx = list(_land_units_sindex.intersection(point.bounds))
            if lu_idx:
                lu_candidates = _land_units_gdf.iloc[lu_idx]
                lu_match = lu_candidates[lu_candidates.geometry.contains(point)]
                if not lu_match.empty:
                    lu_row = lu_match.iloc[0]
                    default['in_planning_area'] = True
                    default['planning_area_name'] = lu_row['plan_area']
                    default['planning_area_distance_mi'] = 0.0
                    default['planning_area_url'] = lu_row.get('plan_url', '')

            # If not inside, find nearest within 3 miles
            if not default['in_planning_area']:
                nearest = _find_nearest_planning_area(lat, lon, max_miles=3.0)
                if nearest:
                    default['planning_area_name'] = nearest['name']
                    default['planning_area_distance_mi'] = nearest['distance_miles']
                    default['planning_area_url'] = nearest.get('plan_url', '')

        # Build narrative
        default['narrative'] = _build_narrative(default, zoning_code=zoning_code)

    except Exception as e:
        logger.warning(f"Comprehensive plan lookup failed: {e}")
        default['narrative'] = 'Comprehensive Plan data could not be loaded for this location.'

    return default
