"""
County Detection Module

Detects which Virginia county a coordinate falls within based on bounding boxes.
Used by the multi-county router to dispatch to county-specific report generators.

POC Implementation: Uses simplified rectangular bounds. Production would use
actual county boundary polygons (GeoJSON).
"""

from typing import Optional


# County bounding boxes (simplified rectangular approximations)
# Production would use actual county boundary polygons
COUNTY_BOUNDS = {
    'loudoun': {
        'min_lat': 38.84,
        'max_lat': 39.32,
        'min_lon': -77.98,
        'max_lon': -77.32
    },
    'fairfax': {
        'min_lat': 38.58,
        'max_lat': 39.04,
        'min_lon': -77.54,
        'max_lon': -77.04
    }
}

# Supported counties list (for validation and display)
SUPPORTED_COUNTIES = list(COUNTY_BOUNDS.keys())


def _point_in_bounds(lat: float, lon: float, bounds: dict) -> bool:
    """
    Check if a point falls within rectangular bounds.

    Args:
        lat: Latitude of the point
        lon: Longitude of the point
        bounds: Dictionary with min_lat, max_lat, min_lon, max_lon

    Returns:
        True if point is within bounds, False otherwise
    """
    return (
        bounds['min_lat'] <= lat <= bounds['max_lat'] and
        bounds['min_lon'] <= lon <= bounds['max_lon']
    )


def detect_county(lat: float, lon: float) -> str:
    """
    Detect which county a coordinate falls within.

    Args:
        lat: Latitude of the location
        lon: Longitude of the location

    Returns:
        County name ('loudoun', 'fairfax') or 'unknown' if not in supported area

    Example:
        >>> detect_county(39.1157, -77.5636)  # Leesburg
        'loudoun'
        >>> detect_county(38.9012, -77.2653)  # Vienna
        'fairfax'
        >>> detect_county(40.0, -74.0)  # NYC area
        'unknown'
    """
    # Validate inputs
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return 'unknown'

    # Check each county's bounds
    # Note: Checking Loudoun first since it's further west and less likely to overlap
    for county_name, bounds in COUNTY_BOUNDS.items():
        if _point_in_bounds(lat, lon, bounds):
            return county_name

    return 'unknown'


def get_county_bounds(county: str) -> Optional[dict]:
    """
    Get the bounding box for a specific county.

    Args:
        county: County name (lowercase)

    Returns:
        Dictionary with bounds or None if county not found
    """
    return COUNTY_BOUNDS.get(county.lower())


def is_supported_county(county: str) -> bool:
    """
    Check if a county is supported by the platform.

    Args:
        county: County name to check

    Returns:
        True if county is supported, False otherwise
    """
    return county.lower() in SUPPORTED_COUNTIES


def get_supported_counties() -> list:
    """
    Get list of all supported counties.

    Returns:
        List of supported county names (lowercase)
    """
    return SUPPORTED_COUNTIES.copy()
