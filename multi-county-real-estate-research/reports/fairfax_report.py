"""
Fairfax County Report Generator

Generates property analysis reports for Fairfax County using standardized
class-based modules and shared presentation components.

Features (7 Sections):
1. School Performance - Assigned schools and nearby facilities
2. Crime & Safety - 6-month incident analysis with safety score
3. Zoning & Development - Land use and overlay districts
4. Parks & Recreation - Park access score and nearby parks
5. Healthcare Access - Hospitals and urgent care proximity
6. Flood Risk Analysis - FEMA flood zone assessment
7. Transit & Metro Access - 32 WMATA stations, bus service (NEW)

This module demonstrates the router architecture where:
- Data fetching uses county-specific modules (Fairfax classes)
- Presentation uses shared components (consistent UX)
- Error handling provides graceful degradation
"""

import streamlit as st
from typing import Dict, Any


def _convert_to_score_format(data: Dict[str, Any], title: str) -> Dict[str, Any]:
    """
    Convert Fairfax module output to shared component score format.

    Args:
        data: Raw data from Fairfax module
        title: Section title for error messages

    Returns:
        Dict in score_card format: {'score': int, 'rating': str, 'details': dict}
    """
    if not data or not isinstance(data, dict):
        return {'score': 0, 'rating': 'Unknown', 'details': {'Error': 'No data available'}}

    return {
        'score': data.get('score', 0),
        'rating': data.get('rating', 'Unknown'),
        'details': {
            k: v for k, v in data.items()
            if k not in ('score', 'rating', 'message') and v is not None
        }
    }


def _df_to_items_list(df, name_col: str = 'name') -> list:
    """
    Convert a DataFrame to list of item dicts for render_nearby_items.

    Args:
        df: DataFrame with nearby items
        name_col: Column to use for item name

    Returns:
        List of dicts with 'name', 'distance_miles', etc.
    """
    if df is None or df.empty:
        return []

    items = []
    for _, row in df.iterrows():
        item = {
            'name': row.get(name_col, row.get('school_name', row.get('facility_name', 'Unknown'))),
            'distance_miles': row.get('distance_miles', None),
        }
        # Add latitude/longitude if available
        if 'latitude' in row:
            item['latitude'] = row['latitude']
        if 'longitude' in row:
            item['longitude'] = row['longitude']
        items.append(item)

    return items


def render_report(address: str, lat: float, lon: float) -> None:
    """
    Generate Fairfax County property analysis report.

    Uses standardized Fairfax modules (class-based pattern) and
    shared presentation components for consistent UX.

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
    render_report_header("Fairfax County", address, lat, lon)

    # ========== SCHOOLS ANALYSIS ==========
    render_section_header("📚", "Schools Analysis", "Assigned schools and nearby facilities")

    try:
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        schools = FairfaxSchoolsAnalysis()

        # Get assigned schools
        assigned = schools.get_assigned_schools(lat, lon)

        if assigned.get('all_assigned'):
            # Display assigned schools
            col1, col2, col3 = st.columns(3)

            with col1:
                elem = assigned.get('elementary', {})
                st.metric("Elementary", elem.get('school_name', 'N/A'))
                if elem.get('distance_miles'):
                    st.caption(f"{elem['distance_miles']:.1f} miles")

            with col2:
                middle = assigned.get('middle', {})
                st.metric("Middle School", middle.get('school_name', 'N/A'))
                if middle.get('distance_miles'):
                    st.caption(f"{middle['distance_miles']:.1f} miles")

            with col3:
                high = assigned.get('high', {})
                st.metric("High School", high.get('school_name', 'N/A'))
                if high.get('distance_miles'):
                    st.caption(f"{high['distance_miles']:.1f} miles")
        else:
            st.info(assigned.get('message', 'School assignment data unavailable'))

        # Get nearby school facilities
        try:
            nearby_df = schools.get_school_facilities(lat, lon, radius_miles=3.0, limit=10)
            nearby_items = _df_to_items_list(nearby_df, 'school_name')
            render_nearby_items("All Nearby Schools", nearby_items, "school")
        except Exception:
            st.info("Nearby school facilities data unavailable")

    except FileNotFoundError as e:
        render_error_section("Schools Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Schools Analysis", str(e))

    st.divider()

    # ========== CRIME & SAFETY ANALYSIS ==========
    render_section_header("🚨", "Crime & Safety Analysis", "6-month crime statistics")

    try:
        from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
        crime = FairfaxCrimeAnalysis()

        # Calculate safety score
        safety = crime.calculate_safety_score(lat, lon, radius_miles=0.5, months_back=6)
        score_data = _convert_to_score_format(safety, "Safety")
        render_score_card("Safety Score", score_data)

        # Show breakdown
        breakdown = safety.get('breakdown', {})
        if breakdown:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Violent Crimes", breakdown.get('violent', 0))
            with col2:
                st.metric("Property Crimes", breakdown.get('property', 0))
            with col3:
                st.metric("Other Incidents", breakdown.get('other', 0))

        # Crime trends
        try:
            trends = crime.get_crime_trends(lat, lon, radius_miles=0.5, months_back=12)
            trend_text = trends.get('trend', 'unknown')
            if trend_text == 'decreasing':
                st.success(f"📉 Crime trend: {trend_text.title()}")
            elif trend_text == 'increasing':
                st.warning(f"📈 Crime trend: {trend_text.title()}")
            else:
                st.info(f"➡️ Crime trend: {trend_text.title()}")
        except Exception:
            pass

    except FileNotFoundError as e:
        render_error_section("Crime Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Crime Analysis", str(e))

    st.divider()

    # ========== ZONING & DEVELOPMENT ==========
    render_section_header("🏗️", "Zoning & Development", "Land use and development potential")

    try:
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
        zoning = FairfaxZoningAnalysis()

        zoning_info = zoning.get_zoning(lat, lon)

        if zoning_info.get('zone_code'):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Zone Code:** `{zoning_info.get('zone_code')}`")
                st.markdown(f"**Zone Type:** {zoning_info.get('zone_type_description', zoning_info.get('zone_type', 'N/A'))}")

            with col2:
                st.markdown(f"**Has Proffer:** {'Yes' if zoning_info.get('has_proffer') else 'No'}")
                st.markdown(f"**Public Land:** {'Yes' if zoning_info.get('public_land') else 'No'}")

            # Overlays
            overlays = zoning_info.get('overlays', [])
            if overlays:
                st.markdown("**Overlay Districts:**")
                for overlay in overlays:
                    overlay_type = overlay.get('overlay_type', 'Unknown')
                    st.markdown(f"  - {overlay_type}")
        else:
            st.info(zoning_info.get('message', 'Zoning information unavailable'))

    except FileNotFoundError as e:
        render_error_section("Zoning Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Zoning Analysis", str(e))

    st.divider()

    # ========== PARKS & RECREATION ==========
    render_section_header("🌳", "Parks & Recreation", "Park access and recreational amenities")

    try:
        from core.fairfax_parks_analysis import FairfaxParksAnalysis
        parks = FairfaxParksAnalysis()

        # Park access score
        park_score = parks.calculate_park_access_score(lat, lon)
        score_data = _convert_to_score_format(park_score, "Parks")
        render_score_card("Park Access Score", score_data)

        # Nearby parks
        try:
            nearby_parks_df = parks.get_parks_near_point(lat, lon, radius_miles=2.0, limit=5)
            nearby_parks = _df_to_items_list(nearby_parks_df, 'park_name')
            render_nearby_items("Nearby Parks", nearby_parks, "park")
        except Exception:
            st.info("Nearby parks data unavailable")

    except FileNotFoundError as e:
        render_error_section("Parks Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Parks Analysis", str(e))

    st.divider()

    # ========== HEALTHCARE ACCESS ==========
    render_section_header("🏥", "Healthcare Access", "Hospitals and urgent care facilities")

    try:
        from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
        healthcare = FairfaxHealthcareAnalysis()

        # Healthcare access score
        health_score = healthcare.calculate_healthcare_access_score(lat, lon)
        score_data = _convert_to_score_format(health_score, "Healthcare")
        render_score_card("Healthcare Access Score", score_data)

        # Nearby hospitals
        try:
            hospitals_df = healthcare.get_facilities_near_point(
                lat, lon, radius_miles=10.0, facility_type='hospital'
            )
            hospitals = _df_to_items_list(hospitals_df, 'facility_name')
            render_nearby_items("Nearby Hospitals", hospitals, "hospital")
        except Exception:
            st.info("Hospital data unavailable")

    except FileNotFoundError as e:
        render_error_section("Healthcare Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Healthcare Analysis", str(e))

    st.divider()

    # ========== FLOOD ZONES ==========
    render_section_header("🌊", "Flood Risk Analysis", "FEMA flood zone assessment")

    try:
        from core.fairfax_flood_analysis import FairfaxFloodAnalysis
        flood = FairfaxFloodAnalysis()

        flood_info = flood.get_flood_zone(lat, lon)

        if flood_info:
            risk_level = flood_info.get('risk_level', 'Unknown')

            if risk_level == 'minimal':
                st.success(f"✅ **Flood Risk:** {risk_level.title()}")
            elif risk_level in ('low', 'moderate'):
                st.info(f"ℹ️ **Flood Risk:** {risk_level.title()}")
            else:
                st.warning(f"⚠️ **Flood Risk:** {risk_level.title()}")

            st.markdown(f"**FEMA Zone:** {flood_info.get('flood_zone', 'N/A')}")
            if flood_info.get('special_flood_hazard'):
                st.warning("⚠️ This property is in a Special Flood Hazard Area")
        else:
            st.info("Flood zone information unavailable")

    except FileNotFoundError as e:
        render_error_section("Flood Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Flood Analysis", str(e))

    st.divider()

    # ========== TRANSIT & METRO ACCESS ==========
    render_section_header("🚇", "Metro & Transit Access", "WMATA Metro stations and bus service")

    try:
        from core.fairfax_transit_analysis import FairfaxTransitAnalysis
        transit = FairfaxTransitAnalysis()

        # Calculate transit score
        transit_score = transit.calculate_transit_score(lat, lon)
        score_data = _convert_to_score_format(transit_score, "Transit")
        render_score_card("Transit Accessibility Score", score_data)

        # Get nearest Metro station
        nearest_metro = transit.get_nearest_metro_station(lat, lon)

        if nearest_metro and nearest_metro.get('station_name'):
            st.markdown("### 🚇 Nearest Metro Station")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Station",
                    nearest_metro.get('station_name', 'Unknown')
                )

            with col2:
                distance = nearest_metro.get('distance_miles', 0)
                st.metric(
                    "Distance",
                    f"{distance:.1f} mi" if distance else "N/A"
                )

            with col3:
                walk_time = nearest_metro.get('walk_time_minutes')
                if walk_time:
                    st.metric("Walk Time", f"{walk_time} min")
                else:
                    bike_time = nearest_metro.get('bike_time_minutes')
                    if bike_time:
                        st.metric("Bike Time", f"{bike_time} min")
                    else:
                        st.metric("Year Opened", nearest_metro.get('year_opened', 'N/A'))

            # Walk/bike time info
            if nearest_metro.get('walk_time_minutes'):
                if nearest_metro['walk_time_minutes'] <= 15:
                    st.success(f"🚶 **Walk to Metro:** {nearest_metro['walk_time_minutes']} minutes - Excellent walkability!")
                elif nearest_metro['walk_time_minutes'] <= 30:
                    st.info(f"🚶 **Walk to Metro:** {nearest_metro['walk_time_minutes']} minutes")
                else:
                    st.info(f"🚴 **Bike to Metro:** {nearest_metro.get('bike_time_minutes', 'N/A')} minutes")

        # Get commute options summary
        commute = transit.get_commute_options(lat, lon)

        if commute:
            accessibility = commute.get('overall_accessibility', 'unknown')

            # Display bus routes info
            bus_info = commute.get('bus', {})
            if bus_info and bus_info.get('routes_within_quarter_mi', 0) > 0:
                with st.expander(f"🚌 Bus Service ({bus_info.get('routes_within_quarter_mi', 0)} routes nearby)"):
                    st.markdown(f"**Routes within 0.25 mi:** {bus_info.get('routes_within_quarter_mi', 0)}")
                    route_names = bus_info.get('route_names', [])
                    if route_names:
                        st.markdown(f"**Routes:** {', '.join(route_names[:10])}")

            # Transit-Oriented Development context
            score = transit_score.get('score', 0)
            if score >= 70:
                st.success(
                    "✅ **Excellent Transit Access** - Properties near Metro stations "
                    "typically command 10-20% premium and experience stronger appreciation. "
                    "Fairfax County has 32 Metro stations across Orange, Blue, and Silver lines."
                )
            elif score >= 40:
                st.info(
                    "🟡 **Moderate Transit Access** - Within reasonable distance to Metro. "
                    "Consider parking availability at stations for park-and-ride commutes."
                )
            else:
                st.warning(
                    "🟠 **Limited Transit Access** - Metro is not a primary transportation option. "
                    "Property relies on road network. Check traffic patterns on major corridors."
                )

    except FileNotFoundError as e:
        render_error_section("Transit Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Transit Analysis", str(e))

    # ========== REPORT FOOTER ==========
    st.divider()
    st.caption("📍 Fairfax County Property Analysis Report")
    st.caption(f"Location: ({lat:.6f}, {lon:.6f})")
    st.success("✅ Report generation complete")


# Alias for backwards compatibility
render_fairfax_report = render_report
