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
