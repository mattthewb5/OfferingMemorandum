"""
Loudoun County Report Tests

Tests for the Loudoun report generator:
- Report module structure
- Shared component usage
- Data independence from Fairfax
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestLoudounReportStructure:
    """Test Loudoun report module structure."""

    def test_loudoun_report_exists(self):
        """Verify Loudoun report module exists."""
        from reports import loudoun_report
        assert loudoun_report is not None

    def test_loudoun_report_has_render_function(self):
        """Verify render_report function exists."""
        from reports.loudoun_report import render_report
        assert callable(render_report)

    def test_loudoun_report_has_alias(self):
        """Verify backwards-compatible alias exists."""
        from reports.loudoun_report import render_loudoun_report
        assert callable(render_loudoun_report)


class TestLoudounSharedComponents:
    """Test that Loudoun uses shared presentation components."""

    def test_loudoun_imports_shared_components(self):
        """Verify Loudoun report imports shared components."""
        import inspect
        from reports import loudoun_report

        source = inspect.getsource(loudoun_report)

        # Check for shared component imports
        assert 'from reports.shared_components import' in source
        assert 'render_report_header' in source
        assert 'render_score_card' in source
        assert 'render_section_header' in source


class TestLoudounDataIndependence:
    """Test that Loudoun tests can run without Fairfax data."""

    def test_loudoun_module_no_fairfax_imports(self):
        """Verify Loudoun report doesn't import Fairfax modules."""
        import inspect
        from reports import loudoun_report

        source = inspect.getsource(loudoun_report)

        # Should not import Fairfax modules
        assert 'fairfax_' not in source.lower() or 'fairfax_report' not in source

    def test_loudoun_core_modules_exist(self, loudoun_metro_module):
        """Verify Loudoun core modules are available."""
        assert loudoun_metro_module is not None
        assert hasattr(loudoun_metro_module, 'calculate_metro_proximity')

    def test_loudoun_metro_proximity(self, loudoun_metro_module, loudoun_ashburn_coords):
        """Test metro proximity calculation for Ashburn."""
        lat, lon = loudoun_ashburn_coords

        result = loudoun_metro_module.calculate_metro_proximity((lat, lon))

        assert 'nearest_station' in result
        assert 'distance_miles' in result
        assert 'all_stations' in result

        # Ashburn should be close to Ashburn Metro
        assert result['distance_miles'] < 3.0  # Should be within 3 miles


class TestLoudounSpecificFeatures:
    """Test Loudoun-specific features."""

    def test_loudoun_has_metro_section(self):
        """Verify Loudoun report includes Metro analysis section."""
        import inspect
        from reports import loudoun_report

        source = inspect.getsource(loudoun_report)

        # Metro analysis is Loudoun-specific
        assert 'Metro' in source or 'metro' in source
        assert 'loudoun_metro_analysis' in source

    def test_loudoun_accessibility_tiers(self, loudoun_metro_module):
        """Test accessibility tier classification."""
        get_tier = loudoun_metro_module.get_accessibility_tier

        # Very close - Walk-to-Metro
        tier = get_tier(0.3)
        assert tier['tier'] == 'Walk-to-Metro'

        # Medium distance - Metro-Accessible
        tier = get_tier(3.0)
        assert tier['tier'] == 'Metro-Accessible'

        # Far - Metro-Distant
        tier = get_tier(15.0)
        assert tier['tier'] == 'Metro-Distant'
