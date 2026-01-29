"""
Shared Test Fixtures for Multi-County POC

Provides common fixtures used across all test modules.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# COORDINATE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def loudoun_test_address():
    """Loudoun County test address with known coordinates."""
    return {
        'address': '43422 Cloister Pl, Leesburg, VA 20176',
        'lat': 39.112665,
        'lon': -77.495668,
        'expected_county': 'loudoun',
        'city': 'Leesburg'
    }


@pytest.fixture(scope="session")
def fairfax_test_address():
    """Fairfax County test address with known coordinates."""
    return {
        'address': 'Vienna, VA',
        'lat': 38.9012,
        'lon': -77.2653,
        'expected_county': 'fairfax',
        'city': 'Vienna'
    }


@pytest.fixture(scope="session")
def unknown_location():
    """Location outside supported counties."""
    return {
        'address': 'New York City',
        'lat': 40.7128,
        'lon': -74.0060,
        'expected_county': 'unknown'
    }


# ============================================================================
# MODULE IMPORT FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def county_detector():
    """Import county detector module."""
    from utils.county_detector import detect_county, get_supported_counties
    return {
        'detect_county': detect_county,
        'get_supported_counties': get_supported_counties
    }


@pytest.fixture(scope="session")
def geocoding():
    """Import geocoding module."""
    from utils.geocoding import geocode_address, GeocodingError
    return {
        'geocode_address': geocode_address,
        'GeocodingError': GeocodingError
    }


@pytest.fixture(scope="session")
def shared_components():
    """Import shared presentation components."""
    from reports.shared_components import (
        render_report_header,
        render_score_card,
        render_nearby_items,
        render_section_header,
        render_statistics_summary,
    )
    return {
        'render_report_header': render_report_header,
        'render_score_card': render_score_card,
        'render_nearby_items': render_nearby_items,
        'render_section_header': render_section_header,
        'render_statistics_summary': render_statistics_summary,
    }


# ============================================================================
# ROUTER FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def router_config():
    """Get router configuration."""
    from unified_app import COUNTY_RENDERERS, COUNTY_DISPLAY_NAMES
    return {
        'renderers': COUNTY_RENDERERS,
        'display_names': COUNTY_DISPLAY_NAMES
    }


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_score_data():
    """Sample score data for testing render_score_card."""
    return {
        'score': 85,
        'rating': 'Good',
        'details': {
            'Category A': 'Value 1',
            'Category B': 'Value 2',
        }
    }


@pytest.fixture
def sample_nearby_items():
    """Sample nearby items for testing render_nearby_items."""
    return [
        {'name': 'Place A', 'distance_miles': 0.5, 'latitude': 39.0, 'longitude': -77.0},
        {'name': 'Place B', 'distance_miles': 1.2, 'latitude': 39.1, 'longitude': -77.1},
        {'name': 'Place C', 'distance_miles': 2.0, 'latitude': 39.2, 'longitude': -77.2},
    ]
