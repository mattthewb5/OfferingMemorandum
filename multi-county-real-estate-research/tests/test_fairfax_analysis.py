"""
Comprehensive test script for Fairfax County analysis modules.

Tests crime, permits, healthcare, subdivisions, schools, zoning, and flood analysis.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
from core.fairfax_subdivisions_analysis import FairfaxSubdivisionsAnalysis
from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
from core.fairfax_flood_analysis import FairfaxFloodAnalysis


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


def test_subdivisions_analysis():
    """Test subdivisions analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Subdivisions Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxSubdivisionsAnalysis()
        stats = analyzer.get_subdivision_stats()
        print(f"  Loaded {stats['total_features']:,} subdivision features")
        print(f"  Unique subdivision names: {stats['unique_subdivision_names']:,}")

        # Validate dataset size
        assert stats['total_features'] > 10000, "Expected 10,000+ subdivision features"
        assert stats['unique_subdivision_names'] >= 4927, "Expected 4,927+ unique subdivisions"

        # Test point-in-polygon lookup with known subdivision (Dulles Business Park area)
        print("\n--- Testing: Point-in-Polygon Lookup ---")
        test_lat = 38.8969
        test_lon = -77.4327

        result = analyzer.get_subdivision(test_lat, test_lon)
        print(f"  Location: ({test_lat}, {test_lon})")
        print(f"  Found: {result['found']}")
        print(f"  Subdivision: {result['subdivision_name']}")

        assert result['found'] is True, "Expected to find subdivision for test point"
        assert result['subdivision_name'] == "DULLES BUSINESS PARK", \
            f"Expected 'DULLES BUSINESS PARK', got '{result['subdivision_name']}'"

        # Test handling of point outside subdivision boundaries
        print("\n--- Testing: Point Outside Subdivisions ---")
        outside_lat = 38.5  # South of Fairfax County
        outside_lon = -77.3

        result_outside = analyzer.get_subdivision(outside_lat, outside_lon)
        print(f"  Location: ({outside_lat}, {outside_lon})")
        print(f"  Found: {result_outside['found']}")
        print(f"  Message: {result_outside['message']}")

        assert result_outside['found'] is False, "Expected not to find subdivision outside bounds"
        assert result_outside['subdivision_name'] is None, "Subdivision name should be None"
        assert result_outside['message'] is not None, "Should have message for not found"

        # Test None/invalid coordinates
        print("\n--- Testing: Invalid Coordinates ---")
        result_invalid = analyzer.get_subdivision(None, None)
        print(f"  Found: {result_invalid['found']}")
        assert result_invalid['found'] is False, "Should handle None gracefully"

        # Test nearby subdivisions
        print("\n--- Testing: Nearby Subdivisions ---")
        nearby = analyzer.get_nearby_subdivisions(test_lat, test_lon, radius_miles=1.0, limit=5)
        print(f"  Found {len(nearby)} nearby subdivisions")
        for sub in nearby[:3]:
            print(f"    {sub['subdivision_name']}: {sub['distance_miles']} mi")

        assert len(nearby) > 0, "Expected to find nearby subdivisions"
        assert all('subdivision_name' in s for s in nearby), "Missing subdivision_name in results"
        assert all('distance_miles' in s for s in nearby), "Missing distance_miles in results"

        # Test data structure completeness
        print("\n--- Testing: Return Data Structure ---")
        expected_keys = ['found', 'subdivision_name', 'section', 'phase', 'block',
                        'record_date', 'deed_book', 'deed_page', 'message']
        missing_keys = [k for k in expected_keys if k not in result]
        assert len(missing_keys) == 0, f"Missing keys in result: {missing_keys}"
        print(f"  All {len(expected_keys)} expected keys present: ✓")

        # Test search functionality
        print("\n--- Testing: Subdivision Search ---")
        search_results = analyzer.search_subdivisions("RESTON", limit=5)
        print(f"  Search 'RESTON': {len(search_results)} results")
        assert len(search_results) > 0, "Expected to find RESTON subdivisions"
        assert search_results[0]['subdivision_name'] == 'RESTON', "RESTON should be first result"

        # Test stats structure
        print("\n--- Testing: Statistics ---")
        assert 'top_subdivisions_by_sections' in stats, "Missing top_subdivisions_by_sections"
        assert 'geographic_bounds' in stats, "Missing geographic_bounds"
        assert 'RESTON' in stats['top_subdivisions_by_sections'], "RESTON should be in top subdivisions"
        print(f"  Top subdivision: RESTON with {stats['top_subdivisions_by_sections']['RESTON']} sections")

        print("\n  Subdivisions Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Subdivisions Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schools_analysis():
    """Test schools analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Schools Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxSchoolsAnalysis()
        stats = analyzer.get_statistics()
        print(f"  Loaded {stats['attendance_zones']['total']} attendance zones")
        print(f"    Elementary: {stats['attendance_zones']['elementary']}")
        print(f"    Middle: {stats['attendance_zones']['middle']}")
        print(f"    High: {stats['attendance_zones']['high']}")
        print(f"  Loaded {stats['facilities']['total']} school facilities")

        # Validate dataset
        assert stats['attendance_zones']['elementary'] == 142, "Expected 142 elementary zones"
        assert stats['attendance_zones']['middle'] == 26, "Expected 26 middle zones"
        assert stats['attendance_zones']['high'] == 24, "Expected 24 high zones"
        assert stats['facilities']['total'] == 269, "Expected 269 facilities"

        # Test school assignment lookup
        print("\n--- Testing: School Assignment Lookup ---")
        test_lat = 38.8969
        test_lon = -77.4327

        assigned = analyzer.get_assigned_schools(test_lat, test_lon)
        print(f"  Location: ({test_lat}, {test_lon})")
        print(f"  All assigned: {assigned['all_assigned']}")

        for level in ['elementary', 'middle', 'high']:
            school = assigned.get(level)
            if school:
                print(f"  {level.title()}: {school['school_name']} ({school['distance_miles']} mi)")
            else:
                print(f"  {level.title()}: Not assigned")

        assert assigned['all_assigned'] is True, "Expected all schools to be assigned"
        assert assigned['elementary'] is not None, "Expected elementary assignment"
        assert assigned['middle'] is not None, "Expected middle assignment"
        assert assigned['high'] is not None, "Expected high assignment"

        # Test None coordinates
        print("\n--- Testing: Invalid Coordinates ---")
        result_invalid = analyzer.get_assigned_schools(None, None)
        assert result_invalid['all_assigned'] is False, "Should handle None gracefully"
        assert result_invalid['message'] is not None, "Should have error message"
        print(f"  Handled None coordinates: ✓")

        # Test facility search
        print("\n--- Testing: Nearby Facilities ---")
        nearby = analyzer.get_school_facilities(
            test_lat, test_lon, radius_miles=3.0, school_types=['ES'], limit=5
        )
        print(f"  Elementary schools within 3 mi: {len(nearby)}")
        for school in nearby[:3]:
            print(f"    {school['school_name']}: {school['distance_miles']} mi")

        assert len(nearby) > 0, "Expected to find nearby elementary schools"
        assert all('distance_miles' in s for s in nearby), "Missing distance_miles"
        assert nearby == sorted(nearby, key=lambda x: x['distance_miles']), "Not sorted by distance"

        # Test school search
        print("\n--- Testing: School Search ---")
        results = analyzer.search_schools("Fairfax", limit=5)
        print(f"  Search 'Fairfax': {len(results)} results")
        assert len(results) > 0, "Expected to find schools with 'Fairfax'"

        print("\n  Schools Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Schools Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_zoning_analysis():
    """Test zoning analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Zoning Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxZoningAnalysis()
        stats = analyzer.get_statistics()
        print(f"  Loaded {stats['districts']['total']} zoning districts")
        print(f"    Unique zone codes: {stats['districts']['unique_zone_codes']}")
        print(f"  Loaded {stats['overlays']['total']} overlay districts")

        # Validate dataset
        assert stats['districts']['total'] == 6431, "Expected 6431 districts"
        assert stats['districts']['unique_zone_codes'] == 74, "Expected 74 unique codes"
        assert stats['overlays']['total'] == 73, "Expected 73 overlays"

        # Test zoning lookup
        print("\n--- Testing: Zoning Lookup ---")
        test_lat = 38.8969
        test_lon = -77.4327

        zoning = analyzer.get_zoning(test_lat, test_lon)
        print(f"  Location: ({test_lat}, {test_lon})")
        print(f"  Zone Code: {zoning['zone_code']}")
        print(f"  Zone Type: {zoning['zone_type']}")
        print(f"  Overlays: {len(zoning['overlays'])}")

        assert zoning['zone_code'] is not None, "Expected zone code"
        assert zoning['zone_type'] is not None, "Expected zone type"
        assert zoning['message'] is None, "Should not have error message"

        # Test overlay detection
        print("\n--- Testing: Overlay Detection ---")
        overlays = analyzer.get_overlays(test_lat, test_lon)
        print(f"  Found {len(overlays)} overlays")
        for overlay in overlays:
            print(f"    {overlay['overlay_type']}")
            if 'decibel_level' in overlay:
                print(f"      Noise: {overlay['decibel_level']} dB")

        # Test airport noise check
        print("\n--- Testing: Airport Noise Check ---")
        noise = analyzer.check_airport_noise(test_lat, test_lon)
        if noise:
            print(f"  In noise zone: Yes ({noise['decibel_level']} dB)")
        else:
            print("  In noise zone: No")

        # Test None coordinates
        print("\n--- Testing: Invalid Coordinates ---")
        result_invalid = analyzer.get_zoning(None, None)
        assert result_invalid['zone_code'] is None, "Should handle None gracefully"
        assert result_invalid['message'] is not None, "Should have error message"
        print(f"  Handled None coordinates: ✓")

        # Test zone search
        print("\n--- Testing: Zone Search ---")
        results = analyzer.search_zones("R-1", limit=5)
        print(f"  Search 'R-1': {len(results)} zone codes")
        for zone in results[:3]:
            print(f"    {zone['zone_code']}: {zone['district_count']} districts")

        assert len(results) > 0, "Expected to find R-1 zones"

        # Test zone type counts
        print("\n--- Testing: Zone Type Counts ---")
        type_counts = analyzer.get_zone_types()
        assert 'residential' in type_counts, "Missing residential in type counts"
        assert type_counts['residential'] > 0, "Expected residential zones"
        print(f"  Residential: {type_counts.get('residential', 0)}")
        print(f"  Commercial: {type_counts.get('commercial', 0)}")

        print("\n  Zoning Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Zoning Analysis Module: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flood_analysis():
    """Test flood analysis module."""
    print("\n" + "=" * 70)
    print("TESTING: Flood Analysis Module")
    print("=" * 70)

    try:
        analyzer = FairfaxFloodAnalysis()
        stats = analyzer.get_statistics()
        print(f"  Loaded {stats['fema_zones']['total']} FEMA flood zones")
        print(f"    High risk: {stats['fema_zones']['by_risk_level'].get('high', 0)}")
        print(f"    Moderate: {stats['fema_zones']['by_risk_level'].get('moderate', 0)}")
        print(f"    Minimal: {stats['fema_zones']['by_risk_level'].get('minimal', 0)}")
        print(f"  Loaded {stats['dam_inundation']['total_zones']} dam inundation zones")
        print(f"  Loaded {stats['easements']['total']} floodplain easements")

        # Validate dataset
        assert stats['fema_zones']['total'] == 3313, "Expected 3313 FEMA zones"
        assert stats['dam_inundation']['unique_dams'] == 16, "Expected 16 unique dams"
        assert stats['easements']['total'] == 897, "Expected 897 easements"

        # Test flood risk lookup (minimal risk area)
        print("\n--- Testing: Flood Risk Lookup (Minimal Risk) ---")
        test_lat = 38.8969
        test_lon = -77.4327

        flood = analyzer.get_flood_risk(test_lat, test_lon)
        print(f"  Location: ({test_lat}, {test_lon})")
        print(f"  Overall Risk: {flood['overall_risk']}")
        print(f"  Insurance Required: {flood['insurance_required']}")

        if flood['fema_zone']:
            print(f"  FEMA Zone: {flood['fema_zone']['zone_code']}")
        else:
            print(f"  FEMA Zone: None (not in mapped zone)")

        print(f"  Dam Risks: {len(flood['dam_inundation_risks'])}")
        print(f"  In Easement: {flood['floodplain_easement']['in_easement']}")

        assert flood['message'] is None, "Should not have error message"

        # Test high-risk zone lookup
        print("\n--- Testing: High Risk Zone Lookup ---")
        # Get a point from a high-risk zone
        high_risk_zones = analyzer.fema_zones[analyzer.fema_zones['risk_level'] == 'high']
        high_risk_zone = high_risk_zones.iloc[0]
        rep_point = high_risk_zone.geometry.representative_point()
        hr_lat, hr_lon = rep_point.y, rep_point.x

        high_risk_flood = analyzer.get_flood_risk(hr_lat, hr_lon)
        print(f"  Location: ({hr_lat:.4f}, {hr_lon:.4f})")
        if high_risk_flood['fema_zone']:
            print(f"  FEMA Zone: {high_risk_flood['fema_zone']['zone_code']}")
            print(f"  Risk Level: {high_risk_flood['fema_zone']['risk_level']}")
            print(f"  Insurance Required: {high_risk_flood['insurance_required']}")
            assert high_risk_flood['fema_zone']['risk_level'] == 'high', "Expected high risk"
            assert high_risk_flood['insurance_required'] is True, "High risk should require insurance"

        # Test dam list
        print("\n--- Testing: Dam List ---")
        dams = analyzer.get_dams()
        print(f"  Total dams: {len(dams)}")
        for dam in dams[:3]:
            print(f"    {dam}")

        assert len(dams) == 16, "Expected 16 dams"
        assert "Burke Lake Dam" in dams, "Expected Burke Lake Dam"

        # Test None coordinates
        print("\n--- Testing: Invalid Coordinates ---")
        result_invalid = analyzer.get_flood_risk(None, None)
        assert result_invalid['overall_risk'] == 'unknown', "Should handle None gracefully"
        assert result_invalid['message'] is not None, "Should have error message"
        print(f"  Handled None coordinates: ✓")

        # Test zones by risk
        print("\n--- Testing: Get Zones by Risk ---")
        high_zones = analyzer.get_zones_by_risk('high')
        print(f"  High risk zones: {len(high_zones)}")
        assert len(high_zones) > 0, "Expected high risk zones"

        print("\n  Flood Analysis Module: ALL TESTS PASSED")
        return True

    except Exception as e:
        print(f"\n  Flood Analysis Module: FAILED - {e}")
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
    subdivisions_passed = test_subdivisions_analysis()
    schools_passed = test_schools_analysis()
    zoning_passed = test_zoning_analysis()
    flood_passed = test_flood_analysis()

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Crime Analysis Module:        {'PASS' if crime_passed else 'FAIL'}")
    print(f"Permits Analysis Module:      {'PASS' if permits_passed else 'FAIL'}")
    print(f"Healthcare Analysis Module:   {'PASS' if healthcare_passed else 'FAIL'}")
    print(f"Subdivisions Analysis Module: {'PASS' if subdivisions_passed else 'FAIL'}")
    print(f"Schools Analysis Module:      {'PASS' if schools_passed else 'FAIL'}")
    print(f"Zoning Analysis Module:       {'PASS' if zoning_passed else 'FAIL'}")
    print(f"Flood Analysis Module:        {'PASS' if flood_passed else 'FAIL'}")
    print("=" * 70)

    all_passed = all([
        crime_passed, permits_passed, healthcare_passed,
        subdivisions_passed, schools_passed, zoning_passed, flood_passed
    ])

    if all_passed:
        print("\n  ALL 7 MODULES PASSED - Ready for integration!")
        return 0
    else:
        print("\n  Some tests failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
