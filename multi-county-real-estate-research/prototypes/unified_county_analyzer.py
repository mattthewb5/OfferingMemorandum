"""
Prototype: Unified County Analyzer
Demonstrates how to route to Loudoun vs Fairfax modules based on address.

This prototype shows:
1. County detection from address
2. Module routing
3. Unified method calls
4. Error handling

Run with:
    cd multi-county-real-estate-research
    python prototypes/unified_county_analyzer.py
"""

import sys
import os
import re
from typing import Dict, Tuple, Optional, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# =============================================================================
# COUNTY DETECTION
# =============================================================================

# Geographic bounds for rough detection
COUNTY_BOUNDS = {
    'loudoun': {
        'min_lat': 38.8, 'max_lat': 39.3,
        'min_lon': -78.0, 'max_lon': -77.3
    },
    'fairfax': {
        'min_lat': 38.6, 'max_lat': 39.0,
        'min_lon': -77.6, 'max_lon': -77.1
    }
}

# City/town indicators for string parsing
LOUDOUN_CITIES = [
    'LEESBURG', 'ASHBURN', 'STERLING', 'PURCELLVILLE', 'MIDDLEBURG',
    'HAMILTON', 'LOVETTSVILLE', 'ROUND HILL', 'HILLSBORO', 'ALDIE',
    'BRAMBLETON', 'SOUTH RIDING', 'LANSDOWNE', 'BROADLANDS'
]

FAIRFAX_CITIES = [
    'FAIRFAX', 'VIENNA', 'MCLEAN', 'FALLS CHURCH', 'ANNANDALE',
    'SPRINGFIELD', 'RESTON', 'HERNDON', 'BURKE', 'OAKTON',
    'TYSONS', 'GREAT FALLS', 'LORTON', 'FRANCONIA'
]

# Shared cities that cross county boundaries
SHARED_CITIES = ['CHANTILLY', 'CENTREVILLE', 'DULLES']

# ZIP code prefixes
LOUDOUN_ZIP_PREFIXES = ['201', '2014', '2015', '2016', '2017', '2018']
FAIRFAX_ZIP_PREFIXES = ['220', '221', '222']


def detect_county_from_string(address: str) -> Optional[str]:
    """
    Quick county detection from address string parsing.

    Returns 'loudoun', 'fairfax', or None if unable to determine.
    """
    if not address:
        return None

    address_upper = address.upper()

    # Check explicit county names first
    if 'LOUDOUN' in address_upper:
        return 'loudoun'
    if 'FAIRFAX' in address_upper:
        return 'fairfax'

    # Check for exclusive cities
    for city in LOUDOUN_CITIES:
        if city in address_upper and city not in SHARED_CITIES:
            return 'loudoun'

    for city in FAIRFAX_CITIES:
        if city in address_upper and city not in SHARED_CITIES:
            return 'fairfax'

    # Check ZIP codes
    zip_match = re.search(r'\b(\d{5})\b', address)
    if zip_match:
        zip_code = zip_match.group(1)
        for prefix in LOUDOUN_ZIP_PREFIXES:
            if zip_code.startswith(prefix):
                return 'loudoun'
        for prefix in FAIRFAX_ZIP_PREFIXES:
            if zip_code.startswith(prefix):
                return 'fairfax'

    return None


def detect_county_from_bounds(lat: float, lon: float) -> Optional[str]:
    """
    Detect county from coordinates using bounding boxes.

    Note: This is a rough detection - overlap zone exists.
    """
    for county, bounds in COUNTY_BOUNDS.items():
        if (bounds['min_lat'] <= lat <= bounds['max_lat'] and
            bounds['min_lon'] <= lon <= bounds['max_lon']):
            # Check if also in other county (overlap zone)
            other_county = 'fairfax' if county == 'loudoun' else 'loudoun'
            other_bounds = COUNTY_BOUNDS[other_county]

            if (other_bounds['min_lat'] <= lat <= other_bounds['max_lat'] and
                other_bounds['min_lon'] <= lon <= other_bounds['max_lon']):
                return None  # In overlap zone, need more precise detection

            return county

    return None


def detect_county(address: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """
    Comprehensive county detection using multiple methods.

    Returns:
        {
            'county': 'loudoun' | 'fairfax' | None,
            'confidence': 'high' | 'medium' | 'low',
            'method': str,
            'error': str | None
        }
    """
    result = {
        'county': None,
        'confidence': 'low',
        'method': None,
        'error': None
    }

    # Method 1: String parsing (quick, free)
    county = detect_county_from_string(address)
    if county:
        result['county'] = county
        result['confidence'] = 'medium'
        result['method'] = 'string_parsing'
        return result

    # Method 2: Coordinate bounds (if coordinates provided)
    if lat is not None and lon is not None:
        county = detect_county_from_bounds(lat, lon)
        if county:
            result['county'] = county
            result['confidence'] = 'medium'
            result['method'] = 'bounding_box'
            return result

        # In overlap zone
        result['error'] = 'Address is in overlap zone between counties'
    else:
        result['error'] = 'Unable to determine county from address'

    return result


# =============================================================================
# UNIFIED ADAPTERS
# =============================================================================

class UnifiedSchoolsAdapter:
    """Unified interface for school analysis across counties."""

    def __init__(self, county: str):
        self.county = county.lower()
        self._backend = None
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize the county-specific backend."""
        if self.county == 'loudoun':
            # For prototype, we'll mock the Loudoun backend
            self._backend = None  # Would be: SchoolLookup(LOUDOUN_CONFIG)
            self._backend_type = 'loudoun'
        elif self.county == 'fairfax':
            try:
                from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
                self._backend = FairfaxSchoolsAnalysis()
                self._backend_type = 'fairfax'
            except ImportError as e:
                print(f"Warning: Could not import Fairfax schools module: {e}")
                self._backend = None
                self._backend_type = 'mock'
        else:
            raise ValueError(f"Unsupported county: {self.county}")

    def get_assigned_schools(self, lat: float, lon: float, address: str = None) -> Dict:
        """Get school assignments for a location."""
        if self._backend is None:
            # Return mock data for testing
            return {
                'county': self.county,
                'elementary': {'school_name': f'Mock Elementary ({self.county})', 'distance_miles': 0.5},
                'middle': {'school_name': f'Mock Middle ({self.county})', 'distance_miles': 1.0},
                'high': {'school_name': f'Mock High ({self.county})', 'distance_miles': 1.5},
                'all_assigned': True,
                'message': 'Mock data - backend not initialized'
            }

        if self.county == 'fairfax':
            return self._backend.get_assigned_schools(lat, lon)
        else:
            # Loudoun transformation would go here
            # result = self._backend.get_schools(address, lat, lon)
            # return transform_loudoun_to_common(result)
            pass


class UnifiedZoningAdapter:
    """Unified interface for zoning analysis across counties."""

    def __init__(self, county: str):
        self.county = county.lower()
        self._backend = None
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize the county-specific backend."""
        if self.county == 'loudoun':
            self._backend = None  # Would be function-based
            self._backend_type = 'loudoun'
        elif self.county == 'fairfax':
            try:
                from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
                self._backend = FairfaxZoningAnalysis()
                self._backend_type = 'fairfax'
            except ImportError as e:
                print(f"Warning: Could not import Fairfax zoning module: {e}")
                self._backend = None
                self._backend_type = 'mock'
        else:
            raise ValueError(f"Unsupported county: {self.county}")

    def get_zoning(self, lat: float, lon: float) -> Dict:
        """Get zoning information for a location."""
        if self._backend is None:
            return {
                'county': self.county,
                'zone_code': 'R-1',
                'zone_type': 'residential',
                'zone_description': f'Mock zoning data ({self.county})',
                'message': 'Mock data - backend not initialized'
            }

        if self.county == 'fairfax':
            return self._backend.get_zoning(lat, lon)
        else:
            # Loudoun transformation:
            # from core.loudoun_zoning_analysis import analyze_property_zoning_loudoun
            # result = analyze_property_zoning_loudoun(lat, lon)
            # return transform_loudoun_zoning_to_common(result)
            pass


class UnifiedTransitAdapter:
    """Unified interface for transit analysis across counties."""

    def __init__(self, county: str):
        self.county = county.lower()
        self._backend = None
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize the county-specific backend."""
        if self.county == 'loudoun':
            self._backend = None
            self._backend_type = 'loudoun'
        elif self.county == 'fairfax':
            try:
                from core.fairfax_transit_analysis import FairfaxTransitAnalysis
                self._backend = FairfaxTransitAnalysis()
                self._backend_type = 'fairfax'
            except ImportError as e:
                print(f"Warning: Could not import Fairfax transit module: {e}")
                self._backend = None
                self._backend_type = 'mock'
        else:
            raise ValueError(f"Unsupported county: {self.county}")

    def get_transit_score(self, lat: float, lon: float) -> Dict:
        """Get transit accessibility score for a location."""
        if self._backend is None:
            return {
                'county': self.county,
                'score': 50,
                'rating': 'Moderate',
                'nearest_metro_distance': 2.5,
                'message': 'Mock data - backend not initialized'
            }

        if self.county == 'fairfax':
            return self._backend.calculate_transit_score(lat, lon)
        else:
            # Loudoun transformation:
            # from core.loudoun_metro_analysis import analyze_metro_access
            # result = analyze_metro_access((lat, lon))
            # return transform_loudoun_transit_to_common(result)
            pass


# =============================================================================
# UNIFIED ANALYSIS ORCHESTRATOR
# =============================================================================

class UnifiedPropertyAnalyzer:
    """
    Main orchestrator for property analysis across counties.

    Usage:
        analyzer = UnifiedPropertyAnalyzer()
        results = analyzer.analyze("123 Main St, Vienna, VA 22180")
    """

    def __init__(self):
        self.county = None
        self.lat = None
        self.lon = None
        self._adapters = {}

    def analyze(self, address: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """
        Analyze a property address.

        Args:
            address: Full address string
            lat: Optional latitude (if already geocoded)
            lon: Optional longitude (if already geocoded)

        Returns:
            Complete analysis results dictionary
        """
        results = {
            'address': address,
            'county': None,
            'detection': None,
            'coordinates': None,
            'schools': None,
            'zoning': None,
            'transit': None,
            'error': None
        }

        # Step 1: Detect county
        detection = detect_county(address, lat, lon)
        results['detection'] = detection

        if detection['county'] is None:
            results['error'] = detection.get('error', 'Unable to determine county')
            return results

        self.county = detection['county']
        results['county'] = self.county

        # For prototype, use hardcoded coordinates if not provided
        if lat is None or lon is None:
            # Would use geocoding in real implementation
            if self.county == 'loudoun':
                lat, lon = 39.112665, -77.495668  # Default Loudoun
            else:
                lat, lon = 38.8462, -77.3064  # Default Fairfax

        self.lat = lat
        self.lon = lon
        results['coordinates'] = {'lat': lat, 'lon': lon}

        # Step 2: Initialize adapters for detected county
        self._initialize_adapters()

        # Step 3: Run analysis
        try:
            results['schools'] = self._adapters['schools'].get_assigned_schools(lat, lon, address)
            results['zoning'] = self._adapters['zoning'].get_zoning(lat, lon)
            results['transit'] = self._adapters['transit'].get_transit_score(lat, lon)
        except Exception as e:
            results['error'] = f"Analysis error: {str(e)}"

        return results

    def _initialize_adapters(self) -> None:
        """Initialize adapters for the detected county."""
        self._adapters = {
            'schools': UnifiedSchoolsAdapter(self.county),
            'zoning': UnifiedZoningAdapter(self.county),
            'transit': UnifiedTransitAdapter(self.county),
        }


# =============================================================================
# TEST / DEMO
# =============================================================================

def test_county_detection():
    """Test county detection with sample addresses."""
    print("\n" + "=" * 60)
    print("TESTING: County Detection")
    print("=" * 60)

    test_addresses = [
        # Loudoun addresses
        ("43422 Cloister Pl, Leesburg, VA 20176", "loudoun"),
        ("22395 Powers Court, Ashburn, VA 20148", "loudoun"),
        ("1234 Main St, Purcellville, VA 20132", "loudoun"),

        # Fairfax addresses
        ("6560 Braddock Rd, Alexandria, VA 22312", "fairfax"),
        ("123 Maple Ave, Vienna, VA 22180", "fairfax"),
        ("456 Chain Bridge Rd, McLean, VA 22101", "fairfax"),

        # Ambiguous addresses
        ("100 Main St, Centreville, VA 20121", None),  # Shared city
        ("500 Dulles Airport Access Rd", None),  # Airport area
    ]

    for address, expected in test_addresses:
        result = detect_county(address)
        detected = result['county']
        status = "✓" if detected == expected else "✗"
        print(f"\n{status} Address: {address}")
        print(f"  Expected: {expected}, Got: {detected}")
        print(f"  Method: {result['method']}, Confidence: {result['confidence']}")


def test_unified_analysis():
    """Test unified property analysis."""
    print("\n" + "=" * 60)
    print("TESTING: Unified Property Analysis")
    print("=" * 60)

    analyzer = UnifiedPropertyAnalyzer()

    # Test Loudoun address
    print("\n--- Loudoun County Test ---")
    result = analyzer.analyze("43422 Cloister Pl, Leesburg, VA 20176")
    print(f"County: {result['county']}")
    print(f"Schools: {result['schools']}")
    print(f"Zoning: {result['zoning']}")
    print(f"Transit: {result['transit']}")

    # Test Fairfax address with coordinates
    print("\n--- Fairfax County Test (with coordinates) ---")
    result = analyzer.analyze(
        "6560 Braddock Rd, Alexandria, VA 22312",
        lat=38.8114,
        lon=-77.1964
    )
    print(f"County: {result['county']}")
    print(f"Coordinates: {result['coordinates']}")
    print(f"Schools: {result['schools']}")
    print(f"Zoning: {result['zoning']}")
    print(f"Transit: {result['transit']}")


def test_real_fairfax_modules():
    """Test with real Fairfax modules if available."""
    print("\n" + "=" * 60)
    print("TESTING: Real Fairfax Modules")
    print("=" * 60)

    # Test location near Thomas Jefferson HS
    test_lat = 38.8114
    test_lon = -77.1964

    try:
        # Schools
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        schools = FairfaxSchoolsAnalysis()
        result = schools.get_assigned_schools(test_lat, test_lon)
        print(f"\n✓ Schools Analysis:")
        print(f"  Elementary: {result.get('elementary', {}).get('school_name', 'N/A')}")
        print(f"  Middle: {result.get('middle', {}).get('school_name', 'N/A')}")
        print(f"  High: {result.get('high', {}).get('school_name', 'N/A')}")
    except Exception as e:
        print(f"\n✗ Schools Analysis failed: {e}")

    try:
        # Zoning
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
        zoning = FairfaxZoningAnalysis()
        result = zoning.get_zoning(test_lat, test_lon)
        print(f"\n✓ Zoning Analysis:")
        print(f"  Zone: {result.get('zone_code', 'N/A')}")
        print(f"  Type: {result.get('zone_type', 'N/A')}")
    except Exception as e:
        print(f"\n✗ Zoning Analysis failed: {e}")

    try:
        # Cell Towers (Fairfax-only)
        from core.fairfax_cell_towers_analysis import FairfaxCellTowersAnalysis
        towers = FairfaxCellTowersAnalysis()
        result = towers.calculate_coverage_score(test_lat, test_lon)
        print(f"\n✓ Cell Towers Analysis (Fairfax-only):")
        print(f"  Score: {result.get('score', 'N/A')}/100")
        print(f"  Nearest: {result.get('nearest_tower_miles', 'N/A')} mi")
    except Exception as e:
        print(f"\n✗ Cell Towers Analysis failed: {e}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("UNIFIED COUNTY ANALYZER - PROTOTYPE")
    print("=" * 60)

    test_county_detection()
    test_unified_analysis()
    test_real_fairfax_modules()

    print("\n" + "=" * 60)
    print("PROTOTYPE TESTS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
