"""
Comprehensive test script for Fairfax County analysis modules.

Tests crime, permits, and healthcare analysis with multiple locations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis


def test_crime_analysis():
    """Test crime analysis module."""
    print("=" * 70)
    print("TESTING: Crime Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxCrimeAnalysis()
        print(f"  Loaded {len(analyzer.incidents):,} geocoded crime incidents")

        # Test locations
        test_locations = [
            (38.8462, -77.3064, "Fairfax County (general)"),
            (38.9458, -77.3375, "Herndon area"),
            (38.7700, -77.1800, "Alexandria area")
        ]

        for lat, lon, name in test_locations:
            print(f"\n--- Testing: {name} ({lat}, {lon}) ---")

            # Safety score
            safety = analyzer.calculate_safety_score(lat, lon, radius_miles=0.5, months_back=6)
            print(f"  Safety Score: {safety['score']}/100 ({safety['rating']})")
            print(f"  Total crimes: {safety['total_crimes']}")
            print(f"  Breakdown: V={safety['breakdown']['violent']}, "
                  f"P={safety['breakdown']['property']}, "
                  f"O={safety['breakdown']['other']}")

            # Validate score range
            assert 0 <= safety['score'] <= 100, "Score out of range!"

            # Trends
            trends = analyzer.get_crime_trends(lat, lon, radius_miles=0.5, months_back=12)
            print(f"  Trend: {trends['trend']} ({trends['change_pct']:+.1f}%)")

            # Breakdown
            breakdown = analyzer.get_crime_breakdown(lat, lon, radius_miles=0.5, months_back=6)
            if breakdown['total'] > 0:
                total_pct = (
                    breakdown['violent']['percentage'] +
                    breakdown['property']['percentage'] +
                    breakdown['other']['percentage']
                )
                assert abs(total_pct - 100.0) < 0.5, f"Percentages don't sum to 100! Got {total_pct}"
            print(f"  Breakdown totals {breakdown['total']} crimes")

        print("\n  Crime Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Crime Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_permits_analysis():
    """Test permits analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Building Permits Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxPermitsAnalysis()
        print(f"  Loaded {len(analyzer.permits):,} geocoded building permits")

        # Test locations
        test_locations = [
            (38.8462, -77.3064, "Fairfax County (general)"),
            (38.9458, -77.3375, "Herndon area"),
            (38.7700, -77.1800, "Alexandria area")
        ]

        for lat, lon, name in test_locations:
            print(f"\n--- Testing: {name} ({lat}, {lon}) ---")

            # Development pressure
            pressure = analyzer.calculate_development_pressure(lat, lon, radius_miles=1.0, months_back=24)
            print(f"  Development Pressure: {pressure['score']}/100")
            print(f"  Trend: {pressure['trend']}")
            print(f"  Total permits: {pressure['total_permits']}")

            # Validate score range
            assert 0 <= pressure['score'] <= 100, "Score out of range!"

            # Trends
            trends = analyzer.get_permit_trends(lat, lon, radius_miles=1.0, months_back=24)
            print(f"  Yearly trends: {len(trends['yearly'])} years")
            if trends['yearly']:
                latest_year = max(trends['yearly'].keys())
                print(f"  Latest year ({latest_year}): {trends['yearly'][latest_year]} permits")

            # Breakdown
            breakdown = analyzer.get_permit_breakdown(lat, lon, radius_miles=1.0, months_back=24)
            if breakdown['total'] > 0 and breakdown['by_major_category']:
                total_pct = sum(cat['percentage'] for cat in breakdown['by_major_category'].values())
                assert abs(total_pct - 100.0) < 0.5, f"Percentages don't sum to 100! Got {total_pct}"
            print(f"  Breakdown totals {breakdown['total']} permits")

        print("\n  Building Permits Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Building Permits Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_healthcare_analysis():
    """Test healthcare analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Healthcare Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxHealthcareAnalysis()
        print(f"  Loaded {len(analyzer.facilities)} healthcare facilities")
        hospitals = len(analyzer.facilities[analyzer.facilities['facility_type'] == 'hospital'])
        urgent_care = len(analyzer.facilities[analyzer.facilities['facility_type'] == 'urgent_care'])
        print(f"    Hospitals: {hospitals}")
        print(f"    Urgent Care: {urgent_care}")

        # Test locations
        test_locations = [
            (38.8462, -77.3064, "Fairfax County (general)"),
            (38.9458, -77.3375, "Herndon area"),
            (38.7700, -77.1800, "Alexandria area")
        ]

        for lat, lon, name in test_locations:
            print(f"\n--- Testing: {name} ({lat}, {lon}) ---")

            # Healthcare access
            access = analyzer.calculate_healthcare_access_score(lat, lon)
            print(f"  Access Score: {access['score']}/100 ({access['rating']})")
            print(f"  Hospitals within 10mi: {access['hospitals_within_10mi']}")
            print(f"  Urgent care within 3mi: {access['urgent_care_within_3mi']}")

            # Validate score range
            assert 0 <= access['score'] <= 100, "Score out of range!"

            # Test facility search
            facilities = analyzer.get_facilities_near_point(lat, lon, radius_miles=10)
            print(f"  Total facilities within 10mi: {len(facilities)}")

            # Test facility comparison
            comparison = analyzer.compare_facilities(lat, lon, radius_miles=15, top_n=3)
            print(f"  Top hospitals compared: {len(comparison)}")

        # Test quality metrics
        print("\n--- Testing Quality Metrics ---")
        metrics = analyzer.get_quality_metrics("INOVA FAIRFAX")
        if metrics:
            print(f"  Found: {metrics['name']}")
            cms = metrics.get('cms_rating')
            cms_str = f"{int(cms)} stars" if cms else "N/A"
            print(f"  CMS Rating: {cms_str}")
            print(f"  Leapfrog Grade: {metrics.get('leapfrog_grade') or 'N/A'}")
            assert metrics['cms_rating'] == 5, "Inova Fairfax should be 5-star!"
            assert metrics['leapfrog_grade'] == 'A', "Inova Fairfax should be A grade!"

        print("\n  Healthcare Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Healthcare Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 68 + "=")
    print("       FAIRFAX COUNTY ANALYSIS MODULES - TEST SUITE")
    print("=" * 68 + "=\n")

    crime_passed = test_crime_analysis()
    permits_passed = test_permits_analysis()
    healthcare_passed = test_healthcare_analysis()

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Crime Analysis Module:      {'PASS' if crime_passed else 'FAIL'}")
    print(f"Permits Analysis Module:    {'PASS' if permits_passed else 'FAIL'}")
    print(f"Healthcare Analysis Module: {'PASS' if healthcare_passed else 'FAIL'}")
    print("=" * 70)

    if crime_passed and permits_passed and healthcare_passed:
        print("\n  ALL MODULES PASSED - Ready for integration!")
        return 0
    else:
        print("\n  Some tests failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
