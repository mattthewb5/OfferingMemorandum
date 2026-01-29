"""
Loudoun County Report Generator

Generates property analysis reports for Loudoun County using existing
function-based modules and shared presentation components.

This module demonstrates the router architecture where:
- Data fetching uses county-specific modules (Loudoun functions/classes)
- Presentation uses shared components (consistent UX)
- Data format translation happens in this layer
- Error handling provides graceful degradation

Key Insight: User should NOT be able to tell which county uses which
backend pattern just by looking at the report.
"""

import streamlit as st
from typing import Dict, Any, List


def _convert_metro_to_score(metro_data: Dict, tier_data: Dict) -> Dict[str, Any]:
    """
    Convert Loudoun metro analysis output to shared component score format.

    Args:
        metro_data: Output from calculate_metro_proximity()
        tier_data: Output from get_accessibility_tier()

    Returns:
        Dict in score_card format
    """
    # Map tier to numeric score
    tier_scores = {
        'Walk-to-Metro': 100,
        'Bike-to-Metro': 90,
        'Metro-Accessible': 75,
        'Metro-Available': 50,
        'Metro-Distant': 25,
    }

    # Map tier to rating
    tier_ratings = {
        'Walk-to-Metro': 'Excellent',
        'Bike-to-Metro': 'Excellent',
        'Metro-Accessible': 'Good',
        'Metro-Available': 'Fair',
        'Metro-Distant': 'Poor',
    }

    tier = tier_data.get('tier', 'Metro-Distant')

    return {
        'score': tier_scores.get(tier, 25),
        'rating': tier_ratings.get(tier, 'Unknown'),
        'details': {
            'Nearest Station': metro_data.get('nearest_station', 'N/A'),
            'Distance': f"{metro_data.get('distance_miles', 0):.1f} miles",
            'Tier': tier,
            'Description': tier_data.get('tier_description', ''),
        }
    }


def _convert_zoning_to_display(zoning_data: Dict) -> Dict[str, Any]:
    """
    Convert Loudoun zoning API output to display format.

    Args:
        zoning_data: Output from get_place_type_loudoun() or get_zoning_loudoun()

    Returns:
        Formatted zoning information
    """
    return {
        'place_type': zoning_data.get('place_type', 'Unknown'),
        'place_type_code': zoning_data.get('place_type_code', 'N/A'),
        'policy_area': zoning_data.get('policy_area', 'Unknown'),
        'policy_area_code': zoning_data.get('policy_area_code', 'N/A'),
        'success': zoning_data.get('success', False),
        'error': zoning_data.get('error'),
    }


def _convert_school_to_score(school_data: Dict) -> Dict[str, Any]:
    """
    Convert Loudoun school performance data to shared component score format.

    Args:
        school_data: School performance information

    Returns:
        Dict in score_card format
    """
    # Extract pass rate as score
    overall_rate = school_data.get('Overall_Pass_Rate', 0)

    # Map rate to rating
    if overall_rate >= 90:
        rating = 'Excellent'
    elif overall_rate >= 80:
        rating = 'Good'
    elif overall_rate >= 70:
        rating = 'Fair'
    else:
        rating = 'Needs Improvement'

    return {
        'score': int(overall_rate) if overall_rate else 0,
        'rating': rating,
        'details': {
            'Math Pass Rate': f"{school_data.get('Math_Pass_Rate', 0):.1f}%",
            'Reading Pass Rate': f"{school_data.get('Reading_Pass_Rate', 0):.1f}%",
            'Science Pass Rate': f"{school_data.get('Science_Pass_Rate', 0):.1f}%",
        }
    }


def _stations_to_items(stations: List[Dict]) -> List[Dict]:
    """Convert metro stations list to nearby items format."""
    items = []
    for station in stations:
        items.append({
            'name': f"{station.get('name', 'Unknown')} Metro",
            'distance_miles': station.get('distance_miles', 0),
            'latitude': station.get('lat'),
            'longitude': station.get('lon'),
        })
    return items


def render_report(address: str, lat: float, lon: float) -> None:
    """
    Generate Loudoun County property analysis report.

    Uses existing Loudoun modules (function-based, older pattern) and
    shared presentation components. Translates Loudoun data formats
    to shared component expectations.

    Args:
        address: The property address being analyzed
        lat: Property latitude
        lon: Property longitude
    """
    from reports.shared_components import (
        render_report_header,
        render_score_card,
        render_nearby_items,
        render_section_header,
        render_statistics_summary,
        render_error_section,
    )

    # ========== HEADER ==========
    render_report_header("Loudoun County", address, lat, lon)

    # ========== METRO ACCESS ANALYSIS ==========
    # Loudoun-specific feature: Silver Line Metro proximity
    render_section_header("🚇", "Metro Access Analysis", "Silver Line proximity (Loudoun exclusive)")

    try:
        from core.loudoun_metro_analysis import (
            calculate_metro_proximity,
            get_accessibility_tier,
        )

        # Calculate metro proximity
        metro_data = calculate_metro_proximity((lat, lon))
        tier_data = get_accessibility_tier(metro_data.get('distance_miles', 999))

        # Convert to score format and display
        metro_score = _convert_metro_to_score(metro_data, tier_data)
        render_score_card("Metro Accessibility", metro_score)

        # Show nearby stations
        all_stations = metro_data.get('all_stations', [])
        station_items = _stations_to_items(all_stations)
        render_nearby_items("Metro Stations", station_items, "station")

        # Display tier badge
        tier_icon = tier_data.get('icon', '⚪')
        tier_name = tier_data.get('tier', 'Unknown')
        st.markdown(f"**Accessibility Tier:** {tier_icon} {tier_name}")

    except ImportError as e:
        render_error_section("Metro Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Metro Analysis", str(e))

    st.divider()

    # ========== ZONING & PLACE TYPES ==========
    render_section_header("🏗️", "Zoning & Place Types", "2019 Comprehensive Plan classification")

    try:
        from core.loudoun_zoning_analysis import get_place_type_loudoun

        # Get place type info
        zoning_data = get_place_type_loudoun(lat, lon)
        display_data = _convert_zoning_to_display(zoning_data)

        if display_data['success']:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Place Type:** {display_data['place_type']}")
                st.markdown(f"**Code:** `{display_data['place_type_code']}`")

            with col2:
                st.markdown(f"**Policy Area:** {display_data['policy_area']}")
                st.markdown(f"**Code:** `{display_data['policy_area_code']}`")
        else:
            st.info(display_data.get('error', 'Zoning information unavailable'))

    except ImportError as e:
        render_error_section("Zoning Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Zoning Analysis", str(e))

    st.divider()

    # ========== SCHOOLS ANALYSIS ==========
    render_section_header("📚", "Schools Analysis", "Performance data and nearby schools")

    try:
        from core.loudoun_school_performance import (
            load_performance_data,
            load_school_coordinates,
            haversine,
        )

        # Load school data
        performance_df = load_performance_data()
        coords_df = load_school_coordinates()

        # Find nearby schools (within 3 miles)
        nearby_schools = []
        for _, school in coords_df.iterrows():
            school_lat = school.get('Latitude')
            school_lon = school.get('Longitude')
            if school_lat and school_lon:
                distance = haversine(lat, lon, school_lat, school_lon)
                if distance <= 3.0:
                    nearby_schools.append({
                        'name': school.get('School_Name', 'Unknown'),
                        'type': school.get('School_Type', 'Unknown'),
                        'distance_miles': round(distance, 2),
                        'latitude': school_lat,
                        'longitude': school_lon,
                    })

        # Sort by distance
        nearby_schools.sort(key=lambda x: x['distance_miles'])

        if nearby_schools:
            # Show nearest school performance
            nearest = nearby_schools[0]
            school_name = nearest['name']

            # Try to find performance data for this school
            perf_match = performance_df[
                performance_df['School_Name'].str.contains(school_name.split()[0], case=False, na=False)
            ]

            if not perf_match.empty:
                # Get most recent year
                latest = perf_match.sort_values('Year', ascending=False).iloc[0]
                school_score = _convert_school_to_score(latest.to_dict())
                render_score_card(f"Nearest School ({school_name})", school_score)
            else:
                st.info(f"Performance data not available for {school_name}")

            # Show nearby schools list
            render_nearby_items("Nearby Schools", nearby_schools, "school")
        else:
            st.info("No schools found within 3 miles")

    except FileNotFoundError as e:
        render_error_section("Schools Analysis", f"Data files not found: {e}")
    except ImportError as e:
        render_error_section("Schools Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Schools Analysis", str(e))

    st.divider()

    # ========== UTILITIES ANALYSIS ==========
    render_section_header("⚡", "Utilities & Infrastructure", "Power line proximity analysis")

    try:
        from core.loudoun_utilities_analysis import PowerLineAnalyzer

        # Create analyzer and get proximity info
        analyzer = PowerLineAnalyzer()
        proximity = analyzer.analyze_proximity(lat, lon)

        if proximity:
            nearest_distance = proximity.get('nearest_distance_miles', float('inf'))

            # Visual impact assessment
            if nearest_distance <= 0.1:
                impact = "High - Directly adjacent"
                impact_color = "🔴"
            elif nearest_distance <= 0.25:
                impact = "Moderate - Visible"
                impact_color = "🟠"
            elif nearest_distance <= 0.5:
                impact = "Low - May be visible"
                impact_color = "🟡"
            else:
                impact = "Minimal - Not visible"
                impact_color = "🟢"

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Nearest Power Line", f"{nearest_distance:.2f} miles")

            with col2:
                st.markdown(f"**Visual Impact:** {impact_color} {impact}")

            # Voltage info if available
            nearest_line = proximity.get('nearest_line', {})
            if nearest_line:
                voltage = nearest_line.get('voltage', 'Unknown')
                status = nearest_line.get('status', 'Unknown')
                st.markdown(f"**Line Details:** {voltage} ({status})")
        else:
            st.success("✅ No major power lines detected nearby")

    except FileNotFoundError as e:
        render_error_section("Utilities Analysis", f"Data files not found: {e}")
    except ImportError as e:
        render_error_section("Utilities Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Utilities Analysis", str(e))

    st.divider()

    # ========== NEIGHBORHOOD AMENITIES ==========
    render_section_header("🏪", "Neighborhood Amenities", "Nearby dining, grocery, and shopping")

    try:
        # Note: This module requires API key, so we handle gracefully
        from core.loudoun_places_analysis import PLACE_CATEGORIES

        st.info(
            "Amenities analysis requires Google Places API key. "
            "Categories available: " + ", ".join(PLACE_CATEGORIES.keys())
        )

        # Show what would be analyzed
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Available Categories:**")
            for cat, config in PLACE_CATEGORIES.items():
                st.markdown(f"- {config['display_name']} ({config['radius_miles']} mi)")

        with col2:
            st.markdown("**Note:**")
            st.markdown("- Quality filtered (4.0+ rating)")
            st.markdown("- Results cached for 7 days")
            st.markdown("- Limited to top 10 per category")

    except ImportError:
        st.info("Amenities module not available for this analysis")
    except Exception as e:
        render_error_section("Amenities Analysis", str(e))

    # ========== REPORT FOOTER ==========
    st.divider()
    st.caption("📍 Loudoun County Property Analysis Report")
    st.caption(f"Location: ({lat:.6f}, {lon:.6f})")
    st.success("✅ Report generation complete")


# Alias for backwards compatibility
render_loudoun_report = render_report
