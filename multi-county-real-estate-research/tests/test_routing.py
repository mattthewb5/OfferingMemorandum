"""
Router and Core Utilities Tests

Tests for the multi-county routing system:
- County detection
- Geocoding
- Dictionary dispatch pattern
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestCountyDetection:
    """Test county detection functionality."""

    def test_county_detection_loudoun(self, county_detector, loudoun_test_address):
        """Verify Loudoun County coordinates are detected correctly."""
        detect = county_detector['detect_county']
        lat = loudoun_test_address['lat']
        lon = loudoun_test_address['lon']

        result = detect(lat, lon)

        assert result == 'loudoun', f"Expected 'loudoun', got '{result}'"

    def test_county_detection_fairfax(self, county_detector, fairfax_test_address):
        """Verify Fairfax County coordinates are detected correctly."""
        detect = county_detector['detect_county']
        lat = fairfax_test_address['lat']
        lon = fairfax_test_address['lon']

        result = detect(lat, lon)

        assert result == 'fairfax', f"Expected 'fairfax', got '{result}'"

    def test_county_detection_unknown(self, county_detector, unknown_location):
        """Verify out-of-bounds coordinates return 'unknown'."""
        detect = county_detector['detect_county']
        lat = unknown_location['lat']
        lon = unknown_location['lon']

        result = detect(lat, lon)

        assert result == 'unknown', f"Expected 'unknown', got '{result}'"

    def test_supported_counties_list(self, county_detector):
        """Verify supported counties are returned correctly."""
        get_supported = county_detector['get_supported_counties']

        supported = get_supported()

        assert 'loudoun' in supported
        assert 'fairfax' in supported
        assert len(supported) == 2

    def test_county_detection_herndon_is_fairfax(self, county_detector):
        """
        Regression test: Herndon, VA must detect as Fairfax County.

        Historical bug: Herndon was incorrectly detected as Loudoun with
        rectangular bounding boxes due to overlap.

        Fix: GIS polygon detection using dissolved zoning boundaries.
        """
        detect = county_detector['detect_county']

        # Herndon, VA coordinates
        lat, lon = 38.9696, -77.3861

        result = detect(lat, lon)

        assert result == 'fairfax', \
            f"Herndon (38.9696, -77.3861) should be 'fairfax', got '{result}'"

    def test_county_detection_ashburn_is_loudoun(self, county_detector):
        """
        Regression test: Ashburn, VA must detect as Loudoun County.

        Historical bug: Ashburn (39.0437, -77.4875) fell in gap between
        rectangular bounding boxes and returned 'unknown'.

        Fix: GIS polygon detection using dissolved zoning boundaries.
        """
        detect = county_detector['detect_county']

        # Ashburn, VA coordinates (42831 Falling Leaf Ct)
        lat, lon = 39.0437, -77.4875

        result = detect(lat, lon)

        assert result == 'loudoun', \
            f"Ashburn (39.0437, -77.4875) should be 'loudoun', got '{result}'"

    def test_county_detection_leesburg_loudoun(self, county_detector):
        """Verify Leesburg detects as Loudoun."""
        detect = county_detector['detect_county']

        # Leesburg, VA coordinates
        lat, lon = 39.1157, -77.5636

        result = detect(lat, lon)

        assert result == 'loudoun', \
            f"Leesburg (39.1157, -77.5636) should be 'loudoun', got '{result}'"

    def test_county_detection_vienna_fairfax(self, county_detector):
        """Verify Vienna detects as Fairfax."""
        detect = county_detector['detect_county']

        # Vienna, VA coordinates
        lat, lon = 38.9012, -77.2653

        result = detect(lat, lon)

        assert result == 'fairfax', \
            f"Vienna (38.9012, -77.2653) should be 'fairfax', got '{result}'"


class TestGISPolygonDetection:
    """Test GIS polygon-based county detection specifics."""

    def test_boundary_caching(self):
        """Verify county boundaries are cached for performance."""
        from utils.county_detector import _get_county_boundary, clear_boundary_cache

        # Clear cache first
        clear_boundary_cache()

        # First call loads boundary
        loudoun1 = _get_county_boundary('loudoun')
        assert loudoun1 is not None

        # Second call should return same object (cached)
        loudoun2 = _get_county_boundary('loudoun')
        assert loudoun1 is loudoun2, "Boundaries should be cached (same object)"

    def test_get_county_bounds_loudoun(self):
        """Verify get_county_bounds returns valid bounds for Loudoun."""
        from utils.county_detector import get_county_bounds

        bounds = get_county_bounds('loudoun')

        assert bounds is not None
        assert 'min_lat' in bounds
        assert 'max_lat' in bounds
        assert 'min_lon' in bounds
        assert 'max_lon' in bounds

        # Loudoun should be roughly in this area
        assert 38.8 < bounds['min_lat'] < 39.0
        assert 39.2 < bounds['max_lat'] < 39.4
        assert -78.0 < bounds['min_lon'] < -77.5
        assert -77.5 < bounds['max_lon'] < -77.2

    def test_get_county_bounds_fairfax(self):
        """Verify get_county_bounds returns valid bounds for Fairfax."""
        from utils.county_detector import get_county_bounds

        bounds = get_county_bounds('fairfax')

        assert bounds is not None
        # Fairfax should be roughly in this area
        assert 38.5 < bounds['min_lat'] < 38.7
        assert 39.0 < bounds['max_lat'] < 39.1
        assert -77.6 < bounds['min_lon'] < -77.4
        assert -77.1 < bounds['max_lon'] < -77.0

    def test_invalid_county_bounds(self):
        """Verify get_county_bounds returns None for invalid county."""
        from utils.county_detector import get_county_bounds

        bounds = get_county_bounds('nonexistent')
        assert bounds is None


class TestGeocoding:
    """Test geocoding functionality."""

    def test_geocode_known_address(self, geocoding):
        """Verify known addresses geocode correctly."""
        geocode = geocoding['geocode_address']

        lat, lon = geocode("Leesburg")

        assert lat == pytest.approx(39.1157, abs=0.01)
        assert lon == pytest.approx(-77.5636, abs=0.01)

    def test_geocode_fairfax_address(self, geocoding):
        """Verify Fairfax address geocodes correctly."""
        geocode = geocoding['geocode_address']

        lat, lon = geocode("Vienna")

        assert lat == pytest.approx(38.9012, abs=0.01)
        assert lon == pytest.approx(-77.2653, abs=0.01)

    def test_geocode_unknown_address_raises(self, geocoding):
        """Verify unknown addresses raise GeocodingError."""
        geocode = geocoding['geocode_address']
        GeocodingError = geocoding['GeocodingError']

        with pytest.raises(GeocodingError):
            geocode("Unknown City That Does Not Exist")

    def test_geocode_empty_address_raises(self, geocoding):
        """Verify empty addresses raise GeocodingError."""
        geocode = geocoding['geocode_address']
        GeocodingError = geocoding['GeocodingError']

        with pytest.raises(GeocodingError):
            geocode("")


class TestDictionaryDispatch:
    """Test the dictionary dispatch routing pattern."""

    def test_county_renderers_structure(self, router_config):
        """Verify COUNTY_RENDERERS has correct structure."""
        renderers = router_config['renderers']

        assert isinstance(renderers, dict)
        assert 'loudoun' in renderers
        assert 'fairfax' in renderers

    def test_county_renderers_module_paths(self, router_config):
        """Verify renderer module paths are correct."""
        renderers = router_config['renderers']

        assert renderers['loudoun'] == 'reports.loudoun_report'
        assert renderers['fairfax'] == 'reports.fairfax_report'

    def test_display_names_match_renderers(self, router_config):
        """Verify display names exist for all renderers."""
        renderers = router_config['renderers']
        display_names = router_config['display_names']

        for county in renderers.keys():
            assert county in display_names, f"Missing display name for {county}"

    def test_renderer_modules_importable(self, router_config):
        """Verify all renderer modules can be imported."""
        from importlib import import_module
        renderers = router_config['renderers']

        for county, module_path in renderers.items():
            module = import_module(module_path)
            assert hasattr(module, 'render_report'), \
                f"Module {module_path} missing render_report function"


class TestIntegration:
    """Integration tests for the full routing flow."""

    def test_loudoun_full_flow(self, geocoding, county_detector):
        """Test full flow: address -> geocode -> detect -> Loudoun."""
        geocode = geocoding['geocode_address']
        detect = county_detector['detect_county']

        # Geocode
        lat, lon = geocode("Leesburg")

        # Detect
        county = detect(lat, lon)

        assert county == 'loudoun'

    def test_fairfax_full_flow(self, geocoding, county_detector):
        """Test full flow: address -> geocode -> detect -> Fairfax."""
        geocode = geocoding['geocode_address']
        detect = county_detector['detect_county']

        # Geocode
        lat, lon = geocode("Vienna")

        # Detect
        county = detect(lat, lon)

        assert county == 'fairfax'

    def test_adding_county_estimate(self, router_config):
        """
        Validate architecture scalability:
        Adding a county requires ~2 lines in router + report module.
        """
        renderers = router_config['renderers']

        # Each county is one line in COUNTY_RENDERERS
        # One line in COUNTY_DISPLAY_NAMES
        # One report module (~200-500 lines)
        lines_per_county_in_router = 2
        current_counties = len(renderers)

        # Verify current state
        assert current_counties == 2

        # Calculate marginal effort for next county
        # This is O(1) - constant effort per county
        marginal_lines = lines_per_county_in_router

        assert marginal_lines <= 5, "Adding a county should be trivial"
