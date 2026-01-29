"""
Fairfax County Test Fixtures

Provides Fairfax-specific fixtures for isolated testing.
These tests should be runnable without Loudoun data.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module")
def fairfax_report_module():
    """Load Fairfax report module."""
    from reports import fairfax_report
    return fairfax_report


@pytest.fixture(scope="module")
def fairfax_schools_class():
    """Load Fairfax schools analysis class."""
    try:
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        return FairfaxSchoolsAnalysis
    except ImportError:
        pytest.skip("FairfaxSchoolsAnalysis not available")
    except FileNotFoundError:
        pytest.skip("Fairfax school data files not found")


@pytest.fixture(scope="module")
def fairfax_crime_class():
    """Load Fairfax crime analysis class."""
    try:
        from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
        return FairfaxCrimeAnalysis
    except ImportError:
        pytest.skip("FairfaxCrimeAnalysis not available")
    except FileNotFoundError:
        pytest.skip("Fairfax crime data files not found")


@pytest.fixture(scope="module")
def fairfax_zoning_class():
    """Load Fairfax zoning analysis class."""
    try:
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
        return FairfaxZoningAnalysis
    except ImportError:
        pytest.skip("FairfaxZoningAnalysis not available")
    except FileNotFoundError:
        pytest.skip("Fairfax zoning data files not found")


@pytest.fixture
def fairfax_coords():
    """Standard Fairfax test coordinates (Vienna)."""
    return (38.9012, -77.2653)


@pytest.fixture
def fairfax_reston_coords():
    """Reston test coordinates."""
    return (38.9586, -77.3570)
