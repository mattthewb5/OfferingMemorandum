"""
Fairfax County Report Generator

Generates property analysis reports for Fairfax County using standardized
class-based modules and shared presentation components.

Features (11 Sections):
1. School Performance - Assigned schools and nearby facilities
2. Crime & Safety - 6-month incident analysis with safety score
3. Zoning & Development - Land use and overlay districts
4. Parks & Recreation - Park access score and nearby parks
5. Healthcare Access - Hospitals and urgent care proximity
6. Flood Risk Analysis - FEMA flood zone assessment
7. Transit & Metro Access - 32 WMATA stations, bus service
8. Traffic & Road Network - VDOT traffic data, 148K road segments
9. Cell Tower Coverage - FCC tower data, RF coverage analysis (NEW)
10. Development Activity - Building permits and construction trends (NEW)
11. School Performance Trends - SOL test scores and academic analysis (NEW)

Data advantages vs Loudoun:
- 148,594 road segments (5x more than Loudoun's 29,217)
- 32 Metro stations (vs Loudoun's 4)
- Real VDOT ADT counts, not estimates
- Building permit history with development pressure scoring
- FCC cell tower coverage analysis

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

    st.divider()

    # ========== TRAFFIC & ROAD NETWORK ==========
    render_section_header("🚗", "Traffic & Road Network", "VDOT traffic volumes and highway access")

    try:
        from core.fairfax_traffic_analysis import FairfaxTrafficAnalysis
        traffic = FairfaxTrafficAnalysis()

        # Calculate traffic exposure score (inverted: lower traffic = higher score)
        exposure_score = traffic.calculate_traffic_exposure_score(lat, lon)

        # Convert to score format for display
        score_data = {
            'score': exposure_score.get('score', 0),
            'max_score': 100,
            'rating': exposure_score.get('rating', 'Unknown'),
            'description': 'Lower traffic exposure = higher score (better for residential)'
        }
        render_score_card("Traffic Exposure Score", score_data)

        # Get nearby roads with traffic data
        nearby_roads = traffic.get_nearby_traffic(lat, lon, radius_miles=0.5)

        if nearby_roads:
            st.markdown("### 🛣️ Nearest Roads")

            # Show nearest road metrics
            nearest = nearby_roads[0]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Nearest Road",
                    nearest.get('road_name', 'Unknown')[:20]  # Truncate long names
                )

            with col2:
                st.metric(
                    "Distance",
                    f"{nearest.get('distance_miles', 0):.2f} mi"
                )

            with col3:
                adt = nearest.get('adt', 0)
                st.metric(
                    "Daily Traffic",
                    f"{adt:,}" if adt else "N/A"
                )

            # Traffic level context
            traffic_level = nearest.get('traffic_level', 'Unknown')
            if traffic_level == 'Very High':
                st.warning(f"⚠️ **{traffic_level} Traffic** - Nearest road carries significant vehicle volume")
            elif traffic_level == 'High':
                st.info(f"🟡 **{traffic_level} Traffic** - Moderate to high vehicle volume nearby")
            elif traffic_level in ['Low', 'Very Low']:
                st.success(f"✅ **{traffic_level} Traffic** - Quiet residential area")
            else:
                st.info(f"🔹 **{traffic_level} Traffic**")

            # High-traffic roads count
            high_traffic_count = exposure_score.get('high_traffic_roads_nearby', 0)
            if high_traffic_count > 0:
                st.markdown(f"**High-traffic roads within 1 mile:** {high_traffic_count}")

        # Detailed road list in expander
        if nearby_roads and len(nearby_roads) > 1:
            with st.expander(f"📊 All Roads Within 0.5 Miles ({len(nearby_roads)} roads)"):
                # Format data for table
                table_data = []
                for road in nearby_roads[:15]:  # Limit to 15
                    table_data.append({
                        'Road': road.get('road_name', 'Unknown'),
                        'Route': road.get('route_name', '-'),
                        'Distance': f"{road.get('distance_miles', 0):.2f} mi",
                        'Daily Traffic': f"{road.get('adt', 0):,}",
                        'Level': road.get('traffic_level', 'N/A')
                    })

                render_data_table(table_data)

        # Analysis summary
        analysis = exposure_score.get('analysis', '')
        if analysis:
            st.markdown(f"**Analysis:** {analysis}")

        # Score interpretation
        score = exposure_score.get('score', 0)
        if score >= 70:
            st.success(
                "✅ **Low Traffic Exposure** - Property is well-insulated from heavy traffic. "
                "Ideal for families and those seeking quiet residential environment."
            )
        elif score >= 40:
            st.info(
                "🟡 **Moderate Traffic Exposure** - Some traffic nearby but manageable. "
                "Good balance of accessibility and residential character."
            )
        else:
            st.warning(
                "🟠 **High Traffic Exposure** - Property is near major roads with heavy traffic. "
                "May experience noise. Consider during commute hours before purchase."
            )

        # VDOT data attribution
        st.caption(
            "📌 Traffic data: Virginia DOT (VDOT) actual vehicle counts. "
            "ADT = Average Daily Traffic. Fairfax County: 148,594 road segments."
        )

    except FileNotFoundError as e:
        render_error_section("Traffic Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Traffic Analysis", str(e))

    st.divider()

    # ========== CELL TOWERS & RF COVERAGE ==========
    render_section_header("📡", "Cell Tower Coverage", "Cellular network infrastructure and signal strength")

    try:
        from core.fairfax_cell_towers_analysis import FairfaxCellTowersAnalysis
        cell_towers = FairfaxCellTowersAnalysis()

        # Calculate coverage score
        coverage_score = cell_towers.calculate_coverage_score(lat, lon)
        score_data = _convert_to_score_format(coverage_score, "Coverage")
        render_score_card("Cell Tower Coverage Score", score_data)

        # Get nearest towers
        nearest_towers = cell_towers.get_nearest_towers(lat, lon, n=5)

        if nearest_towers is not None and len(nearest_towers) > 0:
            st.markdown("### 📡 Nearest Cell Towers")

            # Show closest tower metrics
            nearest = nearest_towers.iloc[0]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Distance",
                    f"{nearest.get('distance_miles', 0):.2f} mi"
                )

            with col2:
                st.metric(
                    "Structure Type",
                    nearest.get('structure_type', 'Unknown')
                )

            with col3:
                height = nearest.get('height_ft', nearest.get('overall_height_ft'))
                st.metric(
                    "Height",
                    f"{height:.0f} ft" if height else "N/A"
                )

        # Get towers within 2 miles for detailed view
        nearby_towers = cell_towers.get_towers_near_point(lat, lon, radius_miles=2.0)

        if nearby_towers is not None and len(nearby_towers) > 0:
            towers_2mi = coverage_score.get('towers_within_2mi', len(nearby_towers))

            with st.expander(f"📡 {towers_2mi} towers within 2 miles"):
                tower_data = []
                for idx, tower in nearby_towers.head(10).iterrows():
                    tower_data.append({
                        'Structure': tower.get('structure_type', 'Unknown'),
                        'Distance': f"{tower.get('distance_miles', 0):.2f} mi",
                        'Height': f"{tower.get('height_ft', tower.get('overall_height_ft', 0)):.0f} ft",
                        'City': tower.get('city', 'N/A')
                    })
                render_data_table(tower_data)

        # Coverage assessment
        score = coverage_score.get('score', 0)
        if score >= 70:
            st.success("✅ **Excellent Coverage** - Multiple towers nearby provide redundant cellular coverage.")
        elif score >= 40:
            st.info("🟡 **Good Coverage** - Adequate cell tower infrastructure for reliable service.")
        else:
            st.warning("🟠 **Limited Coverage** - May experience weak cellular signal in some areas.")

        st.caption("📌 Cell tower data from FCC registration database.")

    except FileNotFoundError as e:
        render_error_section("Cell Tower Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Cell Tower Analysis", str(e))

    st.divider()

    # ========== BUILDING PERMITS & DEVELOPMENT ==========
    render_section_header("📋", "Development Activity", "Building permits and construction trends")

    try:
        from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
        permits = FairfaxPermitsAnalysis()

        # Calculate development pressure score
        dev_pressure = permits.calculate_development_pressure(lat, lon, radius_miles=0.5, months_back=24)
        score_data = _convert_to_score_format(dev_pressure, "Development")
        render_score_card("Development Pressure Score", score_data)

        # Get recent permits
        nearby_permits = permits.get_permits_near_point(lat, lon, radius_miles=0.5)

        if nearby_permits is not None and len(nearby_permits) > 0:
            st.markdown("### 🏗️ Recent Construction Activity")

            # Summary metrics
            total_permits = len(nearby_permits)

            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Permits (0.5 mi)",
                    f"{total_permits:,}"
                )
            with col2:
                trend = dev_pressure.get('trend', 'stable')
                trend_icon = "📈" if trend == "increasing" else "📉" if trend == "decreasing" else "➡️"
                st.metric(
                    "Trend",
                    f"{trend_icon} {trend.title()}"
                )

            # Permit breakdown by type
            breakdown = dev_pressure.get('breakdown', {})
            if breakdown:
                with st.expander("📊 Permit Type Breakdown"):
                    for ptype, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True):
                        if count > 0:
                            st.write(f"- **{ptype}:** {count} permits")

            # Detailed permit table
            with st.expander(f"📋 View recent permits ({min(total_permits, 15)} shown)"):
                permit_data = []
                for idx, permit in nearby_permits.head(15).iterrows():
                    permit_data.append({
                        'Type': permit.get('permit_type', 'Unknown'),
                        'Status': permit.get('status', 'N/A'),
                        'Distance': f"{permit.get('distance_miles', 0):.2f} mi",
                        'Year': str(permit.get('year', 'N/A'))
                    })
                render_data_table(permit_data)
        else:
            st.info("ℹ️ No building permits found within 0.5 miles.")

        # Development context (inverted: high development = warning)
        score = dev_pressure.get('score', 0)
        if score >= 70:
            st.warning(
                "⚠️ **High Development Activity** - Significant construction nearby. "
                "May experience temporary traffic and noise impacts."
            )
        elif score >= 40:
            st.info(
                "🟡 **Moderate Development** - Some construction activity in the area. "
                "Neighborhood is evolving."
            )
        else:
            st.success(
                "✅ **Stable Area** - Low development pressure. "
                "Established neighborhood with minimal construction disruption."
            )

        st.caption("📌 Building permit data from Fairfax County Department of Land Development Services.")

    except FileNotFoundError as e:
        render_error_section("Permits Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("Permits Analysis", str(e))

    st.divider()

    # ========== SCHOOL PERFORMANCE ANALYSIS ==========
    render_section_header("📊", "School Performance Trends", "SOL test scores and academic performance analysis")

    try:
        from core.fairfax_school_performance_analysis import FairfaxSchoolPerformanceAnalysis
        school_perf = FairfaxSchoolPerformanceAnalysis()

        # Get assigned schools from basic schools module
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        schools_basic = FairfaxSchoolsAnalysis()
        assigned = schools_basic.get_assigned_schools(lat, lon)

        has_performance_data = False

        if assigned:
            # Try elementary school first (most important for families)
            elementary = assigned.get('elementary')
            if elementary:
                school_name = elementary.get('school_name')
                if school_name:
                    # Get quality score
                    quality_score = school_perf.calculate_school_quality_score(school_name)

                    if quality_score.get('found', False):
                        has_performance_data = True
                        st.markdown(f"### 🏫 {school_name}")

                        # Display quality score
                        score_data = {
                            'score': quality_score.get('score', 0),
                            'max_score': 100,
                            'rating': quality_score.get('rating', 'Unknown'),
                            'details': 'Based on SOL test scores and performance trends'
                        }
                        render_score_card("School Quality Score", score_data)

                        # Get detailed performance
                        performance = school_perf.get_school_performance(school_name)

                        if performance.get('found', False):
                            # Pass rates
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                reading_rate = performance.get('recent_reading_pass_rate')
                                if reading_rate is not None:
                                    st.metric("Reading", f"{reading_rate:.1f}%")
                                else:
                                    st.metric("Reading", "N/A")

                            with col2:
                                math_rate = performance.get('recent_math_pass_rate')
                                if math_rate is not None:
                                    st.metric("Math", f"{math_rate:.1f}%")
                                else:
                                    st.metric("Math", "N/A")

                            with col3:
                                overall_rate = performance.get('recent_overall_pass_rate')
                                if overall_rate is not None:
                                    st.metric("Overall", f"{overall_rate:.1f}%")
                                else:
                                    st.metric("Overall", "N/A")

                            # Trend analysis
                            trend = quality_score.get('trend', 'stable')
                            trend_icon = "📈" if trend == "improving" else "📉" if trend == "declining" else "➡️"
                            st.info(f"{trend_icon} **5-Year Trend:** {trend.title()}")

                            # Score interpretation
                            score = quality_score.get('score', 0)
                            if score >= 70:
                                st.success(
                                    "✅ **High-Performing School** - Strong academic results "
                                    "and consistent performance."
                                )
                            elif score >= 50:
                                st.info(
                                    "🟡 **Average Performance** - Meeting standards with "
                                    "room for improvement."
                                )
                            else:
                                st.warning(
                                    "⚠️ **Below Average** - School may be facing academic challenges. "
                                    "Consider reviewing detailed performance data."
                                )

        if not has_performance_data:
            st.info("ℹ️ School performance data not available for assigned schools at this location.")

        st.caption("📌 School performance data from Virginia Department of Education (VDOE) SOL results.")

    except FileNotFoundError as e:
        render_error_section("School Performance Analysis", f"Data files not found: {e}")
    except Exception as e:
        render_error_section("School Performance Analysis", str(e))

    # ========== REPORT FOOTER ==========
    st.divider()
    st.caption("📍 Fairfax County Property Analysis Report")
    st.caption(f"Location: ({lat:.6f}, {lon:.6f})")
    st.success("✅ Report generation complete")


# Alias for backwards compatibility
render_fairfax_report = render_report
