"""
Loudoun County Report Generator - Production Version

Generates comprehensive property analysis reports for Loudoun County using
production-ready modules and shared presentation components.

Phase 1B: Critical Modules Integration
--------------------------------------
1. Metro Analysis - Silver Line proximity, tiers, drive times
2. Zoning Analysis - Place types, development probability, plain English
3. School Percentiles - County/state rankings, trajectory
4. Sales Data - Transaction history from Commissioner of Revenue
5. Valuation Context - Estimate formatting (when orchestrator data available)

Architecture:
- Data fetching: County-specific modules (core/loudoun_*.py)
- Presentation: Shared components (reports/shared_components.py)
- Error handling: Graceful degradation per section
- Caching: Module-level caching for performance

Future Phases:
- Phase 2: School charts, Community/HOA, Places/Amenities, AI Narrative
- Phase 3: Traffic volume, Power line analysis
"""

import streamlit as st
from typing import Dict, Any, Optional, Tuple
import os


# =============================================================================
# DATA CONVERSION HELPERS
# =============================================================================

def _convert_metro_to_score(metro_result: Dict) -> Dict[str, Any]:
    """
    Convert Metro analysis output to shared component score format.

    Args:
        metro_result: Output from analyze_metro_access()

    Returns:
        Dict in score_card format for render_score_card()
    """
    if not metro_result.get('available'):
        return {
            'score': 0,
            'rating': 'Unavailable',
            'details': {'Error': metro_result.get('error', 'Metro data unavailable')}
        }

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

    proximity = metro_result.get('proximity', {})
    tier_data = metro_result.get('tier', {})
    drive_time = metro_result.get('drive_time', {})

    tier = tier_data.get('tier', 'Metro-Distant')

    return {
        'score': tier_scores.get(tier, 25),
        'rating': tier_ratings.get(tier, 'Unknown'),
        'details': {
            'Nearest Station': proximity.get('nearest_station', 'N/A'),
            'Distance': f"{proximity.get('distance_miles', 0):.1f} miles",
            'Drive Time': drive_time.get('display', 'N/A'),
            'Rush Hour': drive_time.get('rush_hour_note', ''),
            'Tier': f"{tier_data.get('icon', '')} {tier}",
        }
    }


def _convert_school_to_score(school_context: Dict) -> Dict[str, Any]:
    """
    Convert school percentile context to shared component score format.

    Args:
        school_context: Output from get_school_context()

    Returns:
        Dict in score_card format
    """
    if not school_context:
        return {
            'score': 0,
            'rating': 'Unknown',
            'details': {'Note': 'School data not available'}
        }

    county = school_context.get('county', {})
    state = school_context.get('state', {})
    metrics = school_context.get('metrics', {})
    trajectory = school_context.get('trajectory', {})

    # Use county percentile as primary score
    county_percentile = county.get('percentile', 0)

    # Map percentile to rating
    if county_percentile >= 90:
        rating = 'Excellent'
    elif county_percentile >= 75:
        rating = 'Good'
    elif county_percentile >= 50:
        rating = 'Fair'
    else:
        rating = 'Below Average'

    # Build trajectory display
    direction = trajectory.get('direction', 'stable')
    delta = trajectory.get('delta', 0)
    if direction == 'improving':
        trajectory_display = f"Improving (+{delta:.1f} pts)"
    elif direction == 'declining':
        trajectory_display = f"Declining ({delta:.1f} pts)"
    else:
        trajectory_display = "Stable"

    return {
        'score': county_percentile,
        'rating': rating,
        'details': {
            'County Rank': f"{county.get('rank', 'N/A')} of {county.get('total', 'N/A')}",
            'County Percentile': f"{county_percentile}th",
            'State Percentile': f"{state.get('percentile', 'N/A')}th",
            'Overall Pass Rate': f"{metrics.get('overall_pass_rate', 'N/A')}%",
            'Math Pass Rate': f"{metrics.get('math_pass_rate', 'N/A')}%",
            'Reading Pass Rate': f"{metrics.get('reading_pass_rate', 'N/A')}%",
            'Trajectory': trajectory_display,
        }
    }


def _format_sale_price(price: Optional[int]) -> str:
    """Format sale price for display."""
    if price is None:
        return "N/A"
    return f"${price:,}"


def _format_sale_date(date_str: Optional[str]) -> str:
    """Format sale date for display."""
    if not date_str:
        return "N/A"
    # Already in YYYY-MM-DD format from module
    return date_str


# =============================================================================
# SECTION RENDERERS
# =============================================================================

def _render_metro_section(lat: float, lon: float) -> None:
    """Render Metro Access Analysis section."""
    from reports.shared_components import (
        render_section_header,
        render_score_card,
        render_error_section,
    )

    render_section_header(
        "🚇",
        "Metro Access Analysis",
        "Silver Line proximity and commute options"
    )

    try:
        from core.loudoun_metro_analysis import analyze_metro_access

        metro_result = analyze_metro_access((lat, lon))

        if metro_result.get('available'):
            # Display score card
            metro_score = _convert_metro_to_score(metro_result)
            render_score_card("Metro Accessibility", metro_score)

            # Show all stations with distances
            proximity = metro_result.get('proximity', {})
            all_stations = proximity.get('all_stations', [])

            if all_stations:
                st.markdown("**All Silver Line Stations:**")
                for station in all_stations:
                    st.markdown(
                        f"- **{station['name']}** - {station['distance_miles']:.1f} miles "
                        f"({station.get('location', '')})"
                    )

            # Show narrative if available
            narrative = metro_result.get('narrative')
            if narrative:
                with st.expander("Detailed Analysis"):
                    st.markdown(narrative)
        else:
            st.warning(f"Metro analysis unavailable: {metro_result.get('error', 'Unknown error')}")

    except ImportError as e:
        render_error_section("Metro Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Metro Analysis", str(e))


def _render_zoning_section(lat: float, lon: float) -> None:
    """Render Zoning & Development Probability section."""
    from reports.shared_components import (
        render_section_header,
        render_statistics_summary,
        render_error_section,
    )

    render_section_header(
        "🏗️",
        "Zoning & Development Probability",
        "2019 Comprehensive Plan classification and change risk"
    )

    try:
        from core.loudoun_zoning_analysis import (
            analyze_property_zoning_loudoun,
            get_plain_english_placetype,
            get_plain_english_zoning,
            calculate_development_probability_detailed,
        )

        # Get complete zoning analysis
        zoning_result = analyze_property_zoning_loudoun(lat, lon)

        # Check if we got valid data (structure is nested)
        place_type_data = zoning_result.get('place_type', {})
        current_zoning_data = zoning_result.get('current_zoning', {})

        has_place_type = isinstance(place_type_data, dict) and place_type_data.get('success')
        has_zoning = isinstance(current_zoning_data, dict) and current_zoning_data.get('success')

        if has_place_type or has_zoning:
            # Display Place Type and Policy Area
            col1, col2 = st.columns(2)

            with col1:
                place_type = place_type_data.get('place_type', 'Unknown') if has_place_type else 'Unknown'
                place_type_code = place_type_data.get('place_type_code', 'N/A') if has_place_type else 'N/A'
                st.markdown(f"**Place Type:** {place_type}")
                st.markdown(f"**Code:** `{place_type_code}`")

                # Get plain English translation
                if place_type_code and place_type_code != 'N/A':
                    plain_english = get_plain_english_placetype(place_type_code)
                    if plain_english.get('found'):
                        with st.expander("What this means"):
                            st.markdown(f"**Character:** {plain_english.get('character', 'N/A')}")
                            st.markdown(f"**Allows:** {plain_english.get('allows', 'N/A')}")
                            st.markdown(f"**Intensity:** {plain_english.get('intensity', 'N/A')}")

            with col2:
                policy_area = place_type_data.get('policy_area', 'Unknown') if has_place_type else 'Unknown'
                policy_code = place_type_data.get('policy_area_code', 'N/A') if has_place_type else 'N/A'
                st.markdown(f"**Policy Area:** {policy_area}")
                st.markdown(f"**Code:** `{policy_code}`")

                jurisdiction = zoning_result.get('jurisdiction', 'LOUDOUN')
                if jurisdiction != 'LOUDOUN':
                    st.markdown(f"**Jurisdiction:** Town of {jurisdiction.title()}")

            st.divider()

            # Current Zoning
            if has_zoning:
                zone_code = current_zoning_data.get('zoning', 'Unknown')
                zone_name = current_zoning_data.get('zoning_description', 'Unknown')

                st.markdown(f"**Current Zoning:** {zone_name} (`{zone_code}`)")

                # Plain English zoning translation
                if zone_code and zone_code != 'Unknown':
                    zoning_plain = get_plain_english_zoning(zone_code)
                    if zoning_plain.get('found'):
                        with st.expander("Zoning Details"):
                            st.markdown(f"**Category:** {zoning_plain.get('category', 'N/A')}")
                            st.markdown(f"**Description:** {zoning_plain.get('description', 'N/A')}")
                            st.markdown(f"**Typical Uses:** {zoning_plain.get('typical_uses', 'N/A')}")

            st.divider()

            # Development Probability Score
            st.markdown("### Development Risk Assessment")

            dev_prob = zoning_result.get('development_probability', {})
            if dev_prob:
                score = dev_prob.get('score', 0)
                risk_level = dev_prob.get('risk_level', 'Unknown')

                # Color-coded risk display
                if risk_level == 'Low':
                    risk_color = 'green'
                    risk_icon = '🟢'
                elif risk_level == 'Medium':
                    risk_color = 'orange'
                    risk_icon = '🟡'
                elif risk_level == 'High':
                    risk_color = 'red'
                    risk_icon = '🔴'
                else:
                    risk_color = 'gray'
                    risk_icon = '⚪'

                col1, col2 = st.columns([1, 2])

                with col1:
                    st.metric("Development Probability", f"{score}/100", risk_level)

                with col2:
                    st.markdown(f"**Risk Level:** {risk_icon} {risk_level}")

                    # Show component breakdown if available
                    components = dev_prob.get('component_scores', {})
                    if components:
                        st.markdown("**Score Components:**")
                        st.markdown(f"- Mismatch: {components.get('mismatch', 0)} pts")
                        st.markdown(f"- Restrictiveness: {components.get('restrictiveness', 0)} pts")
                        st.markdown(f"- Pressure: {components.get('pressure', 0)} pts")

                # Show component reasons if available
                component_reasons = dev_prob.get('component_reasons', {})
                if component_reasons:
                    with st.expander("Analysis Details"):
                        for component, reason in component_reasons.items():
                            st.markdown(f"- **{component.title()}:** {reason}")
            else:
                st.info("Development probability data not available")

        else:
            error_msg = zoning_result.get('error', 'Unable to retrieve zoning data')
            st.warning(f"Zoning analysis unavailable: {error_msg}")

    except ImportError as e:
        render_error_section("Zoning Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Zoning Analysis", str(e))


def _render_schools_section(
    lat: float,
    lon: float,
    school_assignments: Optional[Dict[str, str]] = None
) -> None:
    """
    Render School Performance section.

    Args:
        lat: Property latitude
        lon: Property longitude
        school_assignments: Optional dict with school assignments like
            {"elementary": "School Name", "middle": "School Name", "high": "School Name"}
    """
    from reports.shared_components import (
        render_section_header,
        render_score_card,
        render_error_section,
    )

    render_section_header(
        "📚",
        "School Performance",
        "Assigned schools with county and state rankings"
    )

    try:
        from core.loudoun_school_percentiles import (
            get_school_context,
            get_school_comparison_narrative,
        )

        # If school assignments provided, use them
        # Otherwise, we'd need to look them up from school boundary data
        if school_assignments:
            schools_to_analyze = school_assignments
        else:
            # Placeholder - in production, would query school boundary GIS layers
            st.info(
                "School assignments not provided. "
                "Enter school names manually or integrate school boundary lookup."
            )

            # Allow manual input for testing
            with st.expander("Enter School Names (for testing)"):
                elem_school = st.text_input("Elementary School", "")
                middle_school = st.text_input("Middle School", "")
                high_school = st.text_input("High School", "")

                if elem_school or middle_school or high_school:
                    schools_to_analyze = {}
                    if elem_school:
                        schools_to_analyze['elementary'] = elem_school
                    if middle_school:
                        schools_to_analyze['middle'] = middle_school
                    if high_school:
                        schools_to_analyze['high'] = high_school
                else:
                    return

        # Analyze each school level
        for level, school_name in schools_to_analyze.items():
            if not school_name:
                continue

            st.markdown(f"#### {level.title()} School")

            # Get school context
            school_type_map = {
                'elementary': 'Elementary',
                'middle': 'Middle',
                'high': 'High'
            }
            school_type = school_type_map.get(level.lower())

            context = get_school_context(school_name, school_type)

            if context:
                # Display as score card
                school_score = _convert_school_to_score(context)
                render_score_card(context.get('school_name', school_name), school_score)

                # Show narrative summary
                narrative = get_school_comparison_narrative(school_name, school_type)
                if narrative:
                    st.markdown(f"*{narrative}*")

                # Loudoun context note
                if context.get('narrative', {}).get('loudoun_context'):
                    st.caption(
                        "Note: Loudoun County schools generally outperform state averages. "
                        "Mid-pack Loudoun often means top-tier statewide."
                    )
            else:
                st.warning(f"Performance data not found for: {school_name}")

            st.markdown("---")

    except ImportError as e:
        render_error_section("School Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("School Analysis", str(e))


def _render_sales_section(apn: Optional[str] = None) -> None:
    """
    Render Sales History section.

    Args:
        apn: Property APN/PARID (e.g., "110-39-4004-000" or "110394004000")
    """
    from reports.shared_components import (
        render_section_header,
        render_data_table,
        render_error_section,
    )

    render_section_header(
        "💰",
        "Sales History",
        "Arms-length transactions from Commissioner of Revenue (2020-2025)"
    )

    if not apn:
        st.info(
            "Property APN/PARID required for sales history lookup. "
            "This is typically obtained from the property assessment API."
        )

        # Allow manual input for testing
        with st.expander("Enter APN (for testing)"):
            manual_apn = st.text_input(
                "APN/PARID",
                placeholder="e.g., 110-39-4004-000",
                help="Enter the property's Assessor Parcel Number"
            )
            if manual_apn:
                apn = manual_apn
            else:
                return

    try:
        from core.loudoun_sales_data import get_cached_loudoun_sales_data

        # Get cached sales data
        sales_data = get_cached_loudoun_sales_data()

        # Check if data loaded
        stats = sales_data.get_stats()
        if not stats.get('loaded'):
            st.error(f"Sales data not available: {stats.get('error', 'Unknown error')}")
            return

        # Look up sales history
        result = sales_data.get_sales_history(apn, max_records=5)

        if result.get('found'):
            # Display metadata
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**PARID:** `{result.get('parid_lookup', 'N/A')}`")
            with col2:
                st.markdown(f"**Data Range:** {result.get('data_range', 'N/A')}")

            st.markdown(f"**Transactions Found:** {result.get('sale_count', 0)}")

            # Display sales table
            sales = result.get('sales', [])
            if sales:
                # Format for display
                display_data = []
                for i, sale in enumerate(sales, 1):
                    display_data.append({
                        '#': i,
                        'Date': _format_sale_date(sale.get('sale_date')),
                        'Price': _format_sale_price(sale.get('sale_price')),
                        'Type': sale.get('verification_code', 'N/A'),
                        'From': (sale.get('old_owner', '')[:30] + '...') if len(sale.get('old_owner', '')) > 30 else sale.get('old_owner', 'N/A'),
                        'To': (sale.get('new_owner', '')[:30] + '...') if len(sale.get('new_owner', '')) > 30 else sale.get('new_owner', 'N/A'),
                    })

                render_data_table(
                    "Transaction History (Newest First)",
                    display_data,
                    columns=['#', 'Date', 'Price', 'Type']
                )

                # Show full details in expander
                with st.expander("Full Transaction Details"):
                    for i, sale in enumerate(sales, 1):
                        st.markdown(f"**Sale #{i}**")
                        st.markdown(f"- Date: {_format_sale_date(sale.get('sale_date'))}")
                        st.markdown(f"- Price: {_format_sale_price(sale.get('sale_price'))}")
                        st.markdown(f"- Type: {sale.get('verification_code', 'N/A')}")
                        st.markdown(f"- From: {sale.get('old_owner', 'N/A')}")
                        st.markdown(f"- To: {sale.get('new_owner', 'N/A')}")
                        st.markdown(f"- Instrument: {sale.get('instrument_number', 'N/A')}")
                        st.markdown("---")
        else:
            st.info(
                f"No arms-length sales found for PARID `{result.get('parid_lookup', apn)}` "
                f"in the {result.get('data_range', '2020-2025')} range."
            )
            st.caption(
                "This property may not have sold during this period, "
                "or the sale was a non-arms-length transaction (family transfer, etc.)"
            )

    except ImportError as e:
        render_error_section("Sales History", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Sales History", str(e))


def _render_valuation_section(
    valuation_result: Optional[Dict[str, Any]] = None,
    sqft: Optional[int] = None
) -> None:
    """
    Render Property Valuation section.

    Args:
        valuation_result: Output from PropertyValuationOrchestrator (if available)
        sqft: Property square footage (for context)
    """
    from reports.shared_components import (
        render_section_header,
        render_statistics_summary,
        render_error_section,
    )

    render_section_header(
        "💵",
        "Property Valuation",
        "Estimated value and market position"
    )

    if not valuation_result:
        st.info(
            "Valuation data requires PropertyValuationOrchestrator integration. "
            "This section displays when orchestrator results are provided."
        )

        # Show placeholder for what would be displayed
        with st.expander("Valuation Data Format (for integration)"):
            st.code("""
# Expected input format from PropertyValuationOrchestrator:
valuation_result = {
    'current_value': {
        'triangulated_estimate': 895000,
        'confidence_score': 8.2
    },
    'price_per_sqft': {
        'property': 285.00,
        'neighborhood_avg': 273.08,
        'position': 'At market'
    },
    'comparable_sales': [...],
    'data_sources': ['ATTOM', 'RentCast', ...]
}
            """, language="python")
        return

    try:
        from core.loudoun_valuation_context import (
            get_valuation_narrative_context,
            format_valuation_narrative_sentence,
        )

        # Extract narrative-ready context
        context = get_valuation_narrative_context(valuation_result)

        # Display main estimate
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Estimated Value",
                context.get('estimate_formatted', 'N/A'),
                f"{context.get('confidence_level', 'N/A')} confidence"
            )

        with col2:
            psf = context.get('price_per_sqft', {})
            st.metric(
                "Price per Sqft",
                f"${psf.get('property', 0):.0f}",
                f"{psf.get('difference_pct', 0):+.1f}% vs area"
            )

        with col3:
            comps = context.get('comps_summary', {})
            st.metric(
                "Comparable Sales",
                comps.get('count', 0),
                f"Median: ${comps.get('median_price', 0):,}"
            )

        # Market position
        position = context.get('price_per_sqft', {}).get('position', 'Unknown')
        value_desc = context.get('narrative_helpers', {}).get('value_descriptor', '')

        st.markdown(f"**Market Position:** {position}")
        st.markdown(f"*{value_desc}*")

        # Narrative sentence
        narrative = format_valuation_narrative_sentence(context)
        st.info(narrative)

        # Sources
        sources = context.get('sources_used', [])
        if sources:
            st.caption(f"Data Sources: {', '.join(sources)}")

    except ImportError as e:
        render_error_section("Valuation Analysis", f"Module not available: {e}")
    except Exception as e:
        render_error_section("Valuation Analysis", str(e))


def _render_phase2_placeholder() -> None:
    """Render placeholder for Phase 2 features."""
    st.divider()
    st.markdown("### Coming in Phase 2")

    with st.expander("Planned Features", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Phase 2: Important**
            - 📊 School Performance Charts
            - 🏘️ Community & HOA Info
            - 🍽️ Neighborhood Amenities
            - 🤖 AI Narrative Generation
            """)

        with col2:
            st.markdown("""
            **Phase 3: Enhancement**
            - 🚗 VDOT Traffic Volume
            - ⚡ Power Line Proximity
            """)


# =============================================================================
# MAIN REPORT FUNCTION
# =============================================================================

def render_report(
    address: str,
    lat: float,
    lon: float,
    property_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Generate Loudoun County property analysis report.

    Integrates 5 Critical modules with shared presentation components.
    Handles missing data gracefully with section-level error isolation.

    Args:
        address: The property address being analyzed
        lat: Property latitude
        lon: Property longitude
        property_data: Optional dict with additional property context:
            {
                'apn': str,  # APN/PARID for sales lookup
                'sqft': int,  # Square footage
                'school_assignments': {'elementary': str, 'middle': str, 'high': str},
                'valuation_result': dict,  # From PropertyValuationOrchestrator
            }
    """
    from reports.shared_components import render_report_header

    # Extract property data if provided
    property_data = property_data or {}
    apn = property_data.get('apn')
    sqft = property_data.get('sqft')
    school_assignments = property_data.get('school_assignments')
    valuation_result = property_data.get('valuation_result')

    # ========== HEADER ==========
    render_report_header("Loudoun County", address, lat, lon)

    # ========== SECTION 1: METRO ACCESS ==========
    _render_metro_section(lat, lon)
    st.divider()

    # ========== SECTION 2: ZONING & DEVELOPMENT ==========
    _render_zoning_section(lat, lon)
    st.divider()

    # ========== SECTION 3: SCHOOLS ==========
    _render_schools_section(lat, lon, school_assignments)
    st.divider()

    # ========== SECTION 4: SALES HISTORY ==========
    _render_sales_section(apn)
    st.divider()

    # ========== SECTION 5: VALUATION ==========
    _render_valuation_section(valuation_result, sqft)

    # ========== PHASE 2 PLACEHOLDER ==========
    _render_phase2_placeholder()

    # ========== FOOTER ==========
    st.divider()
    st.caption("📍 Loudoun County Property Analysis Report - Phase 1B (Critical Modules)")
    st.caption(f"Location: ({lat:.6f}, {lon:.6f})")
    st.success("✅ Report generation complete")


# Alias for backwards compatibility
render_loudoun_report = render_report
