"""
Multi-County Property Intelligence Platform - Unified Router

Main entry point for the multi-county real estate analysis application.
Routes users to county-specific report generators based on property location.

Architecture:
- Dictionary dispatch pattern (not if/elif) for clean scaling
- Dynamic module loading for county-specific reports
- Shared presentation layer for consistent UX
- Session state for county persistence

Supported Counties:
- Loudoun County, VA
- Fairfax County, VA

Usage:
    streamlit run unified_app.py
"""

import streamlit as st
from importlib import import_module
import traceback

from utils.geocoding import geocode_address, GeocodingError
from utils.county_detector import detect_county, get_supported_counties


# ============================================================================
# DICTIONARY DISPATCH PATTERN
# ============================================================================
# Each county maps to its report module path.
# To add a new county:
# 1. Create reports/{county}_report.py with render_report(address, lat, lon)
# 2. Add entry here: '{county}': 'reports.{county}_report'
# 3. Add county bounds to utils/county_detector.py
# ============================================================================

COUNTY_RENDERERS = {
    'loudoun': 'reports.loudoun_report',
    'fairfax': 'reports.fairfax_report_new',  # TEMPORARY: Testing Phase 1 port
}

# Display names for UI
COUNTY_DISPLAY_NAMES = {
    'loudoun': 'Loudoun County, VA',
    'fairfax': 'Fairfax County, VA',
}


def _clear_report_state():
    """Clear session state related to report generation."""
    keys_to_clear = ['county', 'address', 'coords', 'report_generated']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def _render_county_report(county: str, address: str, lat: float, lon: float) -> bool:
    """
    Dynamically load and render a county-specific report.

    Args:
        county: County identifier (e.g., 'loudoun', 'fairfax')
        address: Property address
        lat: Property latitude
        lon: Property longitude

    Returns:
        True if report rendered successfully, False otherwise
    """
    if county not in COUNTY_RENDERERS:
        st.error(f"County '{county}' is not yet supported.")
        st.info(f"Supported counties: {', '.join(COUNTY_DISPLAY_NAMES.values())}")
        return False

    module_path = COUNTY_RENDERERS[county]

    try:
        # Dynamic import
        report_module = import_module(module_path)

        # Call the render function
        report_module.render_report(address, lat, lon)

        return True

    except ImportError as e:
        st.error(f"Failed to load report module for {county}")
        with st.expander("Error Details"):
            st.code(f"ImportError: {e}")
        return False

    except Exception as e:
        st.error(f"Error generating {county} report")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())
        return False


def main():
    """Main application entry point."""

    # ========== PAGE CONFIG ==========
    st.set_page_config(
        page_title="Multi-County Property Intelligence",
        page_icon="🏡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # ========== HEADER ==========
    st.title("🏘️ Multi-County Property Intelligence Platform")
    st.markdown("**Serving Loudoun and Fairfax Counties, Virginia**")
    st.markdown("---")

    # ========== SIDEBAR ==========
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This platform provides comprehensive property analysis for
        Northern Virginia counties.

        **Currently Supported:**
        """)
        for county_id, county_name in COUNTY_DISPLAY_NAMES.items():
            st.markdown(f"- {county_name}")

        st.markdown("---")

        st.header("How It Works")
        st.markdown("""
        1. Enter a property address
        2. System detects the county
        3. County-specific analysis runs
        4. Unified report is displayed
        """)

        st.markdown("---")

        # Debug info
        with st.expander("Session State (Debug)"):
            st.json({
                'county': st.session_state.get('county', 'None'),
                'address': st.session_state.get('address', 'None'),
                'coords': str(st.session_state.get('coords', 'None')),
            })

    # ========== MAIN INPUT SECTION ==========
    col1, col2 = st.columns([3, 1])

    with col1:
        address = st.text_input(
            "🏠 Enter property address:",
            placeholder="e.g., Leesburg, Vienna, Ashburn, Fairfax, or full address",
            help="Enter a city name or full street address"
        )

    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        analyze_button = st.button("🔍 Analyze Property", type="primary", width="stretch")

    # ========== ADVANCED OPTIONS ==========
    with st.expander("⚙️ Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            manual_county = st.selectbox(
                "Override county detection:",
                options=["Auto-detect"] + list(COUNTY_RENDERERS.keys()),
                help="Manually select a county instead of auto-detecting"
            )

        with col2:
            if st.button("🗑️ Clear Session", help="Reset all stored data"):
                _clear_report_state()
                st.success("Session cleared!")
                st.rerun()

    # ========== ANALYSIS FLOW ==========
    if analyze_button:
        if not address:
            st.warning("⚠️ Please enter an address to analyze")
        else:
            # Progress indicator
            with st.spinner("Analyzing property..."):

                # Step 1: Geocode address
                try:
                    lat, lon = geocode_address(address)
                    st.session_state['coords'] = (lat, lon)
                except GeocodingError as e:
                    st.error(f"📍 Geocoding failed: {e}")
                    st.info("Try entering a simpler address like 'Leesburg' or 'Vienna'")
                    st.session_state.pop('report_generated', None)
                    lat, lon = None, None

                # Step 2: Detect county (or use override)
                if lat is not None:
                    if manual_county != "Auto-detect":
                        county = manual_county
                    else:
                        county = detect_county(lat, lon)

                        if county == 'unknown':
                            st.error("📍 Unable to determine county for this location")
                            st.info(f"Coordinates: ({lat:.6f}, {lon:.6f})")
                            st.info("Try selecting a county manually in Advanced Options")
                            st.session_state.pop('report_generated', None)
                            county = None

                    # Store in session state for persistent rendering
                    if county:
                        st.session_state['county'] = county
                        st.session_state['address'] = address
                        st.session_state['report_generated'] = True

    # ========== REPORT RENDERING (persists across reruns) ==========
    # Render the report whenever session state has valid data.
    # This ensures widgets inside the report (e.g., selectboxes in tabs)
    # remain in the widget tree across Streamlit reruns triggered by
    # widget interactions, preventing orphaned-key session resets.
    if st.session_state.get('report_generated'):
        county = st.session_state.get('county')
        stored_address = st.session_state.get('address')
        coords = st.session_state.get('coords')

        if county and stored_address and coords:
            st.success(f"🎯 Detected county: **{COUNTY_DISPLAY_NAMES.get(county, county)}**")
            st.markdown("---")
            _render_county_report(county, stored_address, coords[0], coords[1])

    # ========== FOOTER ==========
    st.markdown("---")
    st.caption("🏡 Multi-County Property Intelligence Platform | POC v0.1")
    st.caption("Architecture: Router pattern with dictionary dispatch")


if __name__ == "__main__":
    main()
