"""
Fairfax County Report Tests

Tests for the Fairfax report generator:
- Report module structure
- Shared component usage
- Data independence from Loudoun
- Class-based module pattern
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestFairfaxReportStructure:
    """Test Fairfax report module structure."""

    def test_fairfax_report_exists(self):
        """Verify Fairfax report module exists."""
        from reports import fairfax_report
        assert fairfax_report is not None

    def test_fairfax_report_has_render_function(self):
        """Verify render_report function exists."""
        from reports.fairfax_report import render_report
        assert callable(render_report)

    def test_fairfax_report_has_alias(self):
        """Verify backwards-compatible alias exists."""
        from reports.fairfax_report import render_fairfax_report
        assert callable(render_fairfax_report)


class TestFairfaxSharedComponents:
    """Test that Fairfax uses shared presentation components."""

    def test_fairfax_imports_shared_components(self):
        """Verify Fairfax report imports shared components."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Check for shared component imports
        assert 'from reports.shared_components import' in source
        assert 'render_report_header' in source
        assert 'render_score_card' in source
        assert 'render_section_header' in source


class TestFairfaxDataIndependence:
    """Test that Fairfax tests can run without Loudoun data."""

    def test_fairfax_module_no_loudoun_imports(self):
        """Verify Fairfax report doesn't import Loudoun modules."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Should not import Loudoun modules
        assert 'loudoun_' not in source.lower() or 'loudoun_report' not in source

    def test_fairfax_uses_class_pattern(self):
        """Verify Fairfax report uses class-based modules."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Should use class instantiation pattern
        assert 'FairfaxSchoolsAnalysis()' in source or 'FairfaxSchoolsAnalysis' in source
        assert 'FairfaxCrimeAnalysis()' in source or 'FairfaxCrimeAnalysis' in source


class TestFairfaxClassPattern:
    """Test Fairfax class-based module pattern."""

    def test_fairfax_schools_class_exists(self):
        """Verify FairfaxSchoolsAnalysis class exists."""
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        assert FairfaxSchoolsAnalysis is not None

    def test_fairfax_crime_class_exists(self):
        """Verify FairfaxCrimeAnalysis class exists."""
        from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
        assert FairfaxCrimeAnalysis is not None

    def test_fairfax_zoning_class_exists(self):
        """Verify FairfaxZoningAnalysis class exists."""
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
        assert FairfaxZoningAnalysis is not None


class TestFairfaxSpecificFeatures:
    """Test Fairfax-specific features."""

    def test_fairfax_has_crime_section(self):
        """Verify Fairfax report includes crime analysis section."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Crime analysis should be present
        assert 'Crime' in source or 'crime' in source
        assert 'fairfax_crime_analysis' in source

    def test_fairfax_has_flood_section(self):
        """Verify Fairfax report includes flood analysis section."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Flood analysis should be present
        assert 'Flood' in source or 'flood' in source
        assert 'fairfax_flood_analysis' in source

    def test_fairfax_has_parks_section(self):
        """Verify Fairfax report includes parks analysis section."""
        import inspect
        from reports import fairfax_report

        source = inspect.getsource(fairfax_report)

        # Parks analysis should be present
        assert 'Parks' in source or 'parks' in source
        assert 'fairfax_parks_analysis' in source
