"""
Loudoun County Test Fixtures

Provides Loudoun-specific fixtures for isolated testing.
These tests should be runnable without Fairfax data.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module")
def loudoun_report_module():
    """Load Loudoun report module."""
    from reports import loudoun_report
    return loudoun_report


@pytest.fixture(scope="module")
def loudoun_metro_module():
    """Load Loudoun metro analysis module."""
    try:
        from core import loudoun_metro_analysis
        return loudoun_metro_analysis
    except ImportError:
        pytest.skip("loudoun_metro_analysis not available")


@pytest.fixture(scope="module")
def loudoun_zoning_module():
    """Load Loudoun zoning analysis module."""
    try:
        from core import loudoun_zoning_analysis
        return loudoun_zoning_analysis
    except ImportError:
        pytest.skip("loudoun_zoning_analysis not available")


@pytest.fixture
def loudoun_coords():
    """Standard Loudoun test coordinates (Leesburg)."""
    return (39.112665, -77.495668)


@pytest.fixture
def loudoun_ashburn_coords():
    """Ashburn test coordinates (near Metro)."""
    return (39.0437, -77.4875)
