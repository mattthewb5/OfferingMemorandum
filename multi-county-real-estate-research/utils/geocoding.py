"""
Geocoding Module (POC Implementation)

Converts addresses to latitude/longitude coordinates.

POC LIMITATION: Uses hardcoded test addresses only.
Production would integrate with Google Maps Geocoding API, Nominatim, or similar.
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


# Hardcoded test addresses for POC
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

    POC LIMITATION: Only works with predefined test addresses.
    Production implementation would use a real geocoding API.

    Args:
        address: Address string to geocode

    Returns:
        Tuple of (latitude, longitude)

    Raises:
        GeocodingError: If address cannot be geocoded

    Example:
        >>> lat, lon = geocode_address("Leesburg")
        >>> print(f"{lat}, {lon}")
        39.1157, -77.5636
    """
    if not address or not isinstance(address, str):
        raise GeocodingError("Invalid address: must be a non-empty string")

    # Normalize address for lookup
    normalized = address.lower().strip()

    # Direct match
    if normalized in TEST_ADDRESSES:
        coords = TEST_ADDRESSES[normalized]
        logger.info(f"Geocoded '{address}' -> {coords}")
        return coords

    # Partial match - check if any key is contained in the address
    for key, coords in TEST_ADDRESSES.items():
        if key in normalized:
            logger.info(f"Geocoded '{address}' (partial match: '{key}') -> {coords}")
            return coords

    # Check if address contains any key
    for key, coords in TEST_ADDRESSES.items():
        if normalized in key:
            logger.info(f"Geocoded '{address}' (reverse partial match: '{key}') -> {coords}")
            return coords

    # No match found
    logger.warning(f"POC geocoding: Address '{address}' not in test database")
    raise GeocodingError(
        f"Address '{address}' not found in POC test database. "
        "Try: Leesburg, Vienna, Ashburn, Fairfax, Reston, etc."
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
    # Virginia approximate bounds
    return (
        36.5 <= lat <= 39.5 and
        -83.7 <= lon <= -75.2
    )
