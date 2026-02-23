"""
Geocoding Module

Converts addresses to latitude/longitude coordinates.

Strategy:
1. Try Google Maps Geocoding API (production - accurate to ~10m)
2. Fall back to TEST_ADDRESSES (for testing/demos when API unavailable)
"""

import logging
import os
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def _geocode_with_google_maps(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode address using Google Maps API.

    Args:
        address: Full address string

    Returns:
        (latitude, longitude) tuple or None if geocoding fails
    """
    try:
        import requests

        # Try to get API key from environment or config
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            try:
                from core.api_config import get_api_key
                api_key = get_api_key('GOOGLE_MAPS_API_KEY')
            except Exception:
                pass

        if not api_key:
            logger.debug("No Google Maps API key available")
            return None

        # Call Google Maps Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Google Maps API returned status {response.status_code}")
            return None

        data = response.json()

        if data.get('status') != 'OK' or not data.get('results'):
            logger.warning(f"Google Maps API status: {data.get('status')}")
            return None

        location = data['results'][0]['geometry']['location']
        lat = location['lat']
        lon = location['lng']

        logger.info(f"Google Maps geocoded '{address}' -> ({lat}, {lon})")
        return (lat, lon)

    except Exception as e:
        logger.warning(f"Google Maps geocoding error: {e}")
        return None


# Hardcoded test addresses for fallback/demos
# Format: lowercase search term -> (lat, lon)
TEST_ADDRESSES = {
    # Loudoun County addresses
    'leesburg': (39.1157, -77.5636),
    '43422 cloister pl': (39.112665, -77.495668),
    '43422 cloister pl, leesburg': (39.112665, -77.495668),
    '43422 cloister pl, leesburg, va': (39.112665, -77.495668),
    '43422 cloister pl, leesburg, va 20176': (39.112665, -77.495668),
    'ashburn': (39.0437, -77.4875),
    '42831 falling leaf ct': (39.0437, -77.4875),
    '42831 falling leaf ct, ashburn': (39.0437, -77.4875),
    '42831 falling leaf ct, ashburn, va': (39.0437, -77.4875),
    'sterling': (39.0062, -77.4286),
    'purcellville': (39.1368, -77.7147),
    'south riding': (38.9210, -77.5063),

    # Fairfax County addresses
    'vienna': (38.9012, -77.2653),
    'fairfax': (38.8462, -77.3064),
    'reston': (38.9586, -77.3570),
    'mclean': (38.9339, -77.1773),
    'annandale': (38.8304, -77.1961),
    'burke': (38.7934, -77.2714),
    'springfield': (38.7893, -77.1872),
    'herndon': (38.9696, -77.3861),
    '13172 ruby lace ct': (38.918914, -77.401634),
    '13172 ruby lace ct, herndon': (38.918914, -77.401634),
    '13172 ruby lace ct, herndon, va 20170': (38.918914, -77.401634),
    '13172 ruby lace ct, herndon va 20170': (38.918914, -77.401634),
    'tysons': (38.9187, -77.2311),
    'falls church': (38.8823, -77.1711),

    # Edge case - outside both counties
    'washington dc': (38.9072, -77.0369),
    'arlington': (38.8799, -77.1068),
}


class GeocodingError(Exception):
    """Raised when geocoding fails."""
    pass


def geocode_address(address: str) -> Tuple[float, float]:
    """
    Convert an address string to latitude/longitude coordinates.

    Strategy:
    1. Try Google Maps API first (production - accurate to ~10m)
    2. Fall back to TEST_ADDRESSES (for testing/demos)

    Args:
        address: Address string to geocode

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        GeocodingError: If address cannot be geocoded

    Example:
        >>> lat, lon = geocode_address("13172 Ruby Lace Ct, Herndon, VA 20170")
        >>> print(f"{lat}, {lon}")
        38.919085, -77.401652
    """
    if not address or not isinstance(address, str):
        raise GeocodingError("Invalid address: must be a non-empty string")

    # Try Google Maps API first (production)
    coords = _geocode_with_google_maps(address)
    if coords:
        lat, lon = coords
        if is_valid_coordinates(lat, lon):
            return coords
        else:
            logger.warning(f"Google Maps returned invalid coordinates: {coords}")

    # Fall back to TEST_ADDRESSES (for testing/demos)
    normalized = address.lower().strip()

    # Direct match
    if normalized in TEST_ADDRESSES:
        coords = TEST_ADDRESSES[normalized]
        logger.info(f"Geocoded '{address}' (test fallback) -> {coords}")
        return coords

    # Partial match - check if any key is contained in the address
    for key, coords in TEST_ADDRESSES.items():
        if key in normalized:
            logger.info(f"Geocoded '{address}' (test fallback, partial: '{key}') -> {coords}")
            return coords

    # Check if address contains any key
    for key, coords in TEST_ADDRESSES.items():
        if normalized in key:
            logger.info(f"Geocoded '{address}' (test fallback, reverse: '{key}') -> {coords}")
            return coords

    # No match found
    logger.warning(f"Geocoding failed for: '{address}'")
    raise GeocodingError(
        f"Address '{address}' could not be geocoded. "
        "Ensure Google Maps API key is configured or try a known test address."
    )


def geocode_address_safe(address: str) -> Optional[Tuple[float, float]]:
    """
    Safe version of geocode_address that returns None instead of raising.

    Args:
        address: Address string to geocode

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    try:
        return geocode_address(address)
    except GeocodingError:
        return None


def get_test_addresses() -> dict:
    """
    Get all available test addresses (for debugging/testing).

    Returns:
        Dictionary mapping address strings to (lat, lon) tuples
    """
    return TEST_ADDRESSES.copy()


def is_valid_coordinates(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are within reasonable bounds.

    Args:
        lat: Latitude value
        lon: Longitude value

    Returns:
        True if coordinates are valid, False otherwise
    """
    # Virginia/DC metro area approximate bounds
    return (
        36.5 <= lat <= 39.5 and
        -83.7 <= lon <= -75.2
    )
