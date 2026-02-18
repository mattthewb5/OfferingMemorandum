"""
Fairfax County Property Intelligence Report
============================================

Ported from Loudoun County report structure (4,970 lines) to ensure
consistent UX and professional quality across all counties.

Architecture:
- Uses Fairfax class-based analysis modules (core/fairfax_*.py)
- Maintains Loudoun's proven display patterns and formatting
- Comprehensive error handling and graceful degradation

Sections:
1. Schools Analysis - Assigned schools with performance trends
2. Location Quality - Roads, airports, flood zones, parks, Metro
3. Cell Tower Coverage - FCC tower data and RF analysis
4. Neighborhood Amenities - Convenience scoring
5. Community/HOA - Subdivision context
6. Demographics - Census Bureau data, charts
7. Economic Indicators - BLS unemployment, LFPR, industry mix
8. Medical Access - Hospitals, urgent care facilities
9. Development Infrastructure - Building permits, tech infrastructure
10. Zoning - Land use and overlay districts
11. Property Valuation - ATTOM/RentCast triangulation
12. AI Analysis - Claude API narrative generation
13. Data Sources Footer

Data Advantages vs Loudoun:
- 148,594 road segments (5x more than Loudoun)
- 32 Metro stations (8x more than Loudoun)
- Natural gas utility data (unique to Fairfax)
- Public crime data API with daily updates

Status: Phase 1 - Porting Schools, Crime, Zoning sections
Ported: 2026-02-03
Template: loudoun_report.py (4,970 lines)
"""

import streamlit as st
import sys
import os
import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import requests

# Add to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# NOTE: Page config is handled by unified_app.py router
# DO NOT add st.set_page_config() here - it will cause errors

# =============================================================================
# DARK MODE THEME SYSTEM
# =============================================================================

# Initialize theme state (default to light mode)
if 'dark_mode' not in st.session_state:
    st.session_state['dark_mode'] = False

# CSS for dark and light modes
DARK_MODE_CSS = """
<style>
    /* Dark mode - base colors */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    /* Section headers - ensure visibility */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #fafafa !important;
    }

    /* Body text and descriptions */
    p, span, label,
    .stMarkdown p, .stMarkdown span,
    .stMarkdown li, .stCaption, .stText {
        color: #e0e0e0 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1d24;
    }

    /* Text inputs and number inputs */
    .stTextInput input, .stNumberInput input {
        background-color: #262730;
        color: #fafafa;
        border: 2px solid #888 !important;
        border-radius: 4px !important;
    }

    /* Expanders - header visibility */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        background-color: #262730;
        color: #fafafa !important;
    }
    .streamlit-expanderContent {
        background-color: #1a1d24;
    }

    /* Tables */
    .stTable, .stDataFrame {
        background-color: #1a1d24;
    }
    table {
        color: #fafafa;
    }
    th {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    td {
        background-color: #1a1d24 !important;
        color: #fafafa !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #fafafa !important;
    }
    [data-testid="stMetricLabel"] {
        color: #b0b0b0 !important;
    }

    /* Markdown tables */
    .stMarkdown table {
        background-color: #1a1d24;
    }
    .stMarkdown th {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    .stMarkdown td {
        background-color: #1a1d24 !important;
        color: #e0e0e0 !important;
        border-color: #3a3a4a !important;
    }

    /* Cards and containers */
    .stAlert {
        background-color: #262730;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #6366f1;
    }

    /* Note: Plotly charts should use template="plotly_dark" in Python code
       CSS overrides can break chart rendering - removed */

    /* Folium maps - dark container */
    iframe {
        border: 1px solid #3a3a4a;
        border-radius: 4px;
    }

    /* Selectbox and multiselect - comprehensive targeting */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] [aria-selected="true"],
    .stMultiSelect > div > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #fafafa !important;
    }

    /* Selectbox selected value */
    [data-baseweb="select"] > div:first-child,
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        background-color: #262730 !important;
        color: #fafafa !important;
    }

    /* Selectbox dropdown menu */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div {
        background-color: #262730 !important;
    }
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {
        background-color: #262730 !important;
        color: #fafafa !important;
    }
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #3a3a4a !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: #ffffff;
    }
    .stButton > button:hover {
        background-color: #5558e3;
        color: #ffffff;
    }

    /* Toggle label */
    [data-testid="stToggle"] label span {
        color: #fafafa !important;
    }

    /* Captions and small text */
    .stCaption, small, .caption {
        color: #b0b0b0 !important;
    }
</style>
"""

LIGHT_MODE_CSS = """
<style>
    /* Light mode - base colors */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
    }

    /* Section headers */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
    .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #1a1a1a !important;
    }

    /* Body text and descriptions */
    p, span, label,
    .stMarkdown p, .stMarkdown span,
    .stMarkdown li, .stCaption, .stText {
        color: #1a1a1a !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Text inputs and number inputs */
    .stTextInput input, .stNumberInput input {
        background-color: #ffffff;
        color: #1a1a1a;
        border: 2px solid #666 !important;
        border-radius: 4px !important;
    }

    /* Expanders - header visibility */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader span,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        background-color: #f0f2f6;
        color: #1a1a1a !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff;
    }

    /* Tables */
    .stTable, .stDataFrame {
        background-color: #ffffff;
    }
    table {
        color: #1a1a1a;
    }
    th {
        background-color: #f0f2f6 !important;
        color: #1a1a1a !important;
    }
    td {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #1a1a1a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #5a5a5a !important;
    }

    /* Markdown tables */
    .stMarkdown table {
        background-color: #ffffff;
    }
    .stMarkdown th {
        background-color: #f0f2f6 !important;
        color: #1a1a1a !important;
    }
    .stMarkdown td {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border-color: #e0e0e0 !important;
    }

    /* Cards and containers */
    .stAlert {
        background-color: #f0f2f6;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #6366f1;
    }

    /* Note: Plotly charts use default light template - no CSS override needed */

    /* Folium maps - light container */
    iframe {
        border: 1px solid #d0d0d0;
        border-radius: 4px;
    }

    /* Selectbox and multiselect - comprehensive targeting */
    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] [aria-selected="true"],
    .stMultiSelect > div > div,
    .stMultiSelect [data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Selectbox selected value */
    [data-baseweb="select"] > div:first-child,
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }

    /* Selectbox dropdown menu */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div {
        background-color: #ffffff !important;
    }
    [data-baseweb="popover"] li,
    [data-baseweb="menu"] li,
    [role="listbox"] li,
    [role="option"] {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
    }
    [data-baseweb="popover"] li:hover,
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #f0f2f6 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: #ffffff;
    }
    .stButton > button:hover {
        background-color: #5558e3;
        color: #ffffff;
    }

    /* Toggle label */
    [data-testid="stToggle"] label span {
        color: #1a1a1a !important;
    }

    /* Captions and small text */
    .stCaption, small, .caption {
        color: #5a5a5a !important;
    }
</style>
"""

# Apply theme CSS
if st.session_state['dark_mode']:
    st.markdown(DARK_MODE_CSS, unsafe_allow_html=True)
else:
    st.markdown(LIGHT_MODE_CSS, unsafe_allow_html=True)

# Core imports
from core.location_quality_analyzer import LocationQualityAnalyzer, get_cached_location_analyzer
# Fairfax-specific modules (class-based)
from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
from core.fairfax_utilities_analysis import FairfaxUtilitiesAnalysis
from core.fairfax_transit_analysis import FairfaxTransitAnalysis
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
# from core.mls_sqft_lookup import get_mls_sqft  # DISABLED - not on this branch
from core.api_config import get_api_key
from core.loudoun_school_performance import (
    load_performance_data as load_performance_with_state_avg,
    load_school_coordinates as _load_loudoun_school_coordinates,
    find_peer_schools,
    create_performance_chart as _loudoun_create_performance_chart,
    normalize_school_name,
    match_school_in_performance_data as _loudoun_match_school_in_performance_data
)

# Fairfax wrappers: override county filter from 'Loudoun County' to 'Fairfax County'
def create_performance_chart(subject_school, peer_schools, metric_name, metric_col, school_type, perf_df):
    return _loudoun_create_performance_chart(
        subject_school, peer_schools, metric_name, metric_col, school_type, perf_df,
        division_name='Fairfax County'
    )

def _schools_have_data(subject_school, peer_schools, metric_col, perf_df):
    """Check if the subject school or any peer has data for a metric.

    Returns True only if at least one real school (not state average)
    has non-null data. This prevents showing charts with only a state
    average line when no actual schools have data for a subject.
    """
    import pandas as pd
    all_schools = [subject_school] + [name for name, _ in peer_schools]
    for school in all_schools:
        match = match_school_in_performance_data(school, perf_df)
        if match:
            rows = perf_df[
                (perf_df['School_Name'] == match) &
                (perf_df['Division_Name'] == 'Fairfax County')
            ]
            if rows[metric_col].notna().any():
                return True
    return False

def match_school_in_performance_data(school_name, perf_df):
    return _loudoun_match_school_in_performance_data(
        school_name, perf_df, division_name='Fairfax County'
    )


def load_school_coordinates() -> 'pd.DataFrame':
    """Load Fairfax school coordinates from the facilities parquet.

    Returns a DataFrame with columns matching the Loudoun format
    (School_Name, School_Type, Latitude, Longitude) so find_peer_schools()
    works unchanged.
    """
    import pandas as _pd
    facilities_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'fairfax', 'schools', 'processed', 'facilities.parquet'
    )
    try:
        df = _pd.read_parquet(facilities_path)
        # Map school_type to the format find_peer_schools() expects
        type_map = {'ES': 'Elem', 'MS': 'Middle', 'HS': 'High'}
        df = df[df['school_type'].isin(type_map.keys())].copy()
        df['School_Type'] = df['school_type'].map(type_map)
        # Build School_Name with suffix for VDOE matching
        suffix_map = {'ES': ' Elementary', 'MS': ' Middle', 'HS': ' High'}
        df['School_Name'] = df.apply(
            lambda r: r['school_name'] + suffix_map.get(r['school_type'], ''), axis=1
        )
        df = df.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'})
        return df[['School_Name', 'School_Type', 'Latitude', 'Longitude']].reset_index(drop=True)
    except Exception as e:
        print(f"Error loading Fairfax school coordinates: {e}")
        return _load_loudoun_school_coordinates()  # Fallback
from core.loudoun_places_analysis import analyze_neighborhood
from core.loudoun_traffic_volume import LoudounTrafficVolumeAnalyzer
from core.loudoun_narrative_generator import compile_narrative_data, generate_property_narrative

# Data handling
import pandas as pd

# Property valuation (with error handling for missing API keys)
VALUATION_AVAILABLE = False
ATTOM_CLIENT = None
try:
    from core.property_valuation_orchestrator import PropertyValuationOrchestrator
    from core.attom_client import ATTOMClient
    # Test if API keys are configured
    attom_key = get_api_key('ATTOM_API_KEY')
    if attom_key or get_api_key('RENTCAST_API_KEY'):
        VALUATION_AVAILABLE = True
    if attom_key:
        ATTOM_CLIENT = ATTOMClient(api_key=attom_key)
except Exception:
    pass

# Community lookup
try:
    from core.loudoun_community_lookup import create_property_community_context, CommunityLookup
    from core.community_spatial_lookup import lookup_community
    COMMUNITY_LOOKUP_AVAILABLE = True
    SPATIAL_LOOKUP_AVAILABLE = True
except Exception as e:
    COMMUNITY_LOOKUP_AVAILABLE = False
    SPATIAL_LOOKUP_AVAILABLE = False
    print(f"Community lookup import failed: {e}")

# Demographics (Census data)
DEMOGRAPHICS_AVAILABLE = False
try:
    from core.demographics_calculator import calculate_demographics
    from core.demographics_formatter import display_demographics_section
    DEMOGRAPHICS_AVAILABLE = True
except Exception as e:
    print(f"Demographics import failed: {e}")

# Economic Indicators
ECONOMIC_INDICATORS_AVAILABLE = False
try:
    from core.fairfax_economic_indicators import (
        get_lfpr_data,
        get_industry_mix_data,
        fetch_bls_data,
        load_major_employers,
        get_employers_by_year,
        get_employer_trends
    )
    ECONOMIC_INDICATORS_AVAILABLE = True
except Exception as e:
    print(f"Economic indicators import failed: {e}")

# Google Maps Geocoding
GOOGLE_MAPS_KEY = None
try:
    GOOGLE_MAPS_KEY = get_api_key('GOOGLE_MAPS_API_KEY')
except Exception:
    pass

# Mapping imports
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# Charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# GIS for school zone lookups
try:
    import geopandas as gpd
    from shapely.geometry import Point
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False

# Initialize community lookup for spatial integration
if COMMUNITY_LOOKUP_AVAILABLE:
    try:
        _COMMUNITY_LOOKUP_INSTANCE = CommunityLookup()
    except Exception as e:
        print(f"Failed to initialize CommunityLookup: {e}")
        _COMMUNITY_LOOKUP_INSTANCE = None
else:
    _COMMUNITY_LOOKUP_INSTANCE = None


# =============================================================================
# DATA PATHS
# =============================================================================
# Get repository root (one level up from reports/ directory)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, 'data', 'fairfax')
SCHOOLS_DIR = os.path.join(DATA_DIR, 'schools')
PERMITS_DIR = os.path.join(DATA_DIR, 'building_permits')
GIS_DIR = os.path.join(DATA_DIR, 'gis')
CELL_TOWERS_DIR = os.path.join(DATA_DIR, 'cell_towers')
HEALTHCARE_DIR = os.path.join(DATA_DIR, 'healthcare')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles."""
    import math
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def format_sale_date(date_str: str) -> str:
    """Convert '2020-04-28' → 'Apr 28, 2020'"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%b %d, %Y')
    except:
        return date_str or "—"


def format_sale_price(price) -> str:
    """Convert 1299000 → '$1,299,000'"""
    if price is None:
        return "N/A"
    try:
        return f"${int(price):,}"
    except:
        return "N/A"


def clean_verification_code(code: str) -> str:
    """Convert '1:MARKET SALE' → 'Market Sale'"""
    try:
        if not code:
            return "—"
        if ':' in code:
            code = code.split(':', 1)[1]
        return code.strip().title()
    except:
        return code or "—"


def format_time_since_sale(date_str: str) -> str:
    """Convert date to human-readable 'X years ago' format"""
    try:
        sale_date = datetime.strptime(date_str, '%Y-%m-%d')
        days = (datetime.now() - sale_date).days

        years = days / 365.25
        if years >= 1:
            return f"{years:.1f} years ago"

        months = days / 30.44  # Average month length
        if months >= 1:
            return f"{int(months)} months ago"

        return f"{days} days ago"
    except:
        return "—"


@st.cache_data
def load_permits_data() -> pd.DataFrame:
    """Load and cache building permits data."""
    permits_path = os.path.join(PERMITS_DIR, 'loudoun_permits_with_infrastructure.csv')
    try:
        df = pd.read_csv(permits_path, encoding='latin-1')
        # Clean coordinates
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Error loading permits: {e}")
        return pd.DataFrame()


@st.cache_data
def load_school_performance() -> pd.DataFrame:
    """Load school performance data for Fairfax County."""
    # Try loading from Fairfax performance data
    perf_path = os.path.join(SCHOOLS_DIR, 'performance', 'processed', 'performance_summary.parquet')
    try:
        if os.path.exists(perf_path):
            df = pd.read_parquet(perf_path)
            return df
        # Fallback to CSV if parquet not available
        csv_path = os.path.join(SCHOOLS_DIR, 'performance', 'raw', 'fairfax_schools_vdoe.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            return df
    except Exception as e:
        print(f"Error loading Fairfax school data: {e}")
    return pd.DataFrame()


@st.cache_data
def load_school_metadata() -> pd.DataFrame:
    """Load school metadata for Fairfax County."""
    # Use facilities data for metadata
    facilities_path = os.path.join(SCHOOLS_DIR, 'processed', 'facilities.parquet')
    try:
        if os.path.exists(facilities_path):
            df = pd.read_parquet(facilities_path)
            return df
    except Exception as e:
        print(f"Error loading school metadata: {e}")
    return pd.DataFrame()


@st.cache_data
def load_road_context() -> Dict:
    """Load road context data with travel times."""
    context_path = os.path.join(DATA_DIR, 'config', 'road_context.json')
    try:
        with open(context_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}


def normalize_road_name(name: str) -> str:
    """Normalize road names for matching with road_context.json keys.

    Handles variations like:
    - "TO SULLY RD NB (VA-28N)" -> "SULLY RD"
    - "TO SULLY RD NB" -> "SULLY RD"
    - "Leesburg Pike" -> "LEESBURG PIKE"
    - "SULLY ROAD" -> "SULLY RD"
    """
    if not name:
        return ""

    name = str(name).upper().strip()

    # Remove route numbers in parentheses (we'll handle separately)
    name = re.sub(r'\s*\([^)]*\)', '', name)

    # Remove "TO" prefix (appears in GIS data)
    name = re.sub(r'^TO\s+', '', name)

    # Remove directional suffixes (NB, SB, EB, WB)
    name = re.sub(r'\s+(NB|SB|EB|WB)$', '', name)

    # Normalize common variations
    name = re.sub(r'\bROAD\b', 'RD', name)
    name = re.sub(r'\bHIGHWAY\b', 'HWY', name)
    name = re.sub(r'\bPARKWAY\b', 'PKWY', name)
    name = re.sub(r'\bBOULEVARD\b', 'BLVD', name)

    # Road name aliases for road_context.json lookup
    ROAD_ALIASES = {
        'DULLES GREENWAY': 'DULLES TOLL RD',
        'GREENWAY': 'DULLES TOLL RD',
        'DULLES ACCESS RD': 'DULLES TOLL RD',
        'HARRY BYRD HWY': 'LEESBURG PIKE',
        'JOHN MOSBY HWY': 'LEE JACKSON HWY',
        'SULLY ROAD': 'SULLY RD',
    }

    # Apply alias mapping
    name = ROAD_ALIASES.get(name, name)

    return name.strip()


def extract_route_number(name: str) -> Optional[str]:
    """Extract route number from highway name if present.

    Examples:
    - "TO SULLY RD NB (VA-28N)" -> "Route 28"
    - "LEESBURG PIKE (US-7)" -> "Route 7"
    - "DULLES TOLL RD (VA-267)" -> "Route 267"

    Returns None if no route number found.
    """
    if not name:
        return None

    # Look for pattern like (VA-28N), (US-7), (VA-267), (SR-28)
    match = re.search(r'\((?:VA-|US-|SR-)?(\d+)(?:N|S|E|W)?\)', str(name))
    if match:
        return f"Route {match.group(1)}"
    return None


def expand_road_name(name: str) -> str:
    """Expand common road abbreviations to full words with proper casing.

    Examples:
    - "SULLY RD" -> "Sully Road"
    - "LEESBURG PIKE" -> "Leesburg Pike"
    - "LOUDOUN COUNTY PKWY" -> "Loudoun County Parkway"
    - "DULLES TOLL RD" -> "Dulles Toll Road"
    """
    if not name:
        return ""

    # Convert to title case first
    name = str(name).title()

    # Expand common abbreviations (must match whole words)
    expansions = {
        r'\bRd\b': 'Road',
        r'\bPkwy\b': 'Parkway',
        r'\bBlvd\b': 'Boulevard',
        r'\bHwy\b': 'Highway',
        r'\bSt\b': 'Street',
        r'\bAve\b': 'Avenue',
        r'\bDr\b': 'Drive',
        r'\bLn\b': 'Lane',
        r'\bCt\b': 'Court',
        r'\bPl\b': 'Place',
        r'\bTer\b': 'Terrace',
        r'\bCir\b': 'Circle',
    }

    for abbrev, full in expansions.items():
        name = re.sub(abbrev, full, name)

    return name


@st.cache_data
def load_cell_towers() -> pd.DataFrame:
    """
    Load and cache cell tower data for Loudoun County.

    Data source: Loudoun County GIS enhanced with FCC carrier data.
    Contains 110 towers with coordinates, heights, and attribution levels.

    Returns:
        DataFrame with columns: tower_id, tower_name, structure_type, height_ft,
        latitude, longitude, entity_name, carrier_category, attribution_level, etc.
    """
    towers_path = os.path.join(CELL_TOWERS_DIR, 'loudoun_towers_enhanced.csv')
    try:
        df = pd.read_csv(towers_path)
        # Validate required columns
        required_cols = ['latitude', 'longitude', 'tower_name', 'attribution_level']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return pd.DataFrame()
        # Clean coordinates
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


def get_nearby_cell_towers(lat: float, lon: float, towers_df: pd.DataFrame, radius_miles: float = 2.0) -> pd.DataFrame:
    """
    Get cell towers within a specified radius of a property.

    Args:
        lat: Property latitude
        lon: Property longitude
        towers_df: DataFrame from load_cell_towers()
        radius_miles: Search radius in miles (default 2.0)

    Returns:
        DataFrame with nearby towers sorted by distance, with distance_mi column added.
    """
    if towers_df.empty:
        return pd.DataFrame()

    # Calculate distance to each tower
    towers_df = towers_df.copy()
    towers_df['distance_mi'] = towers_df.apply(
        lambda row: haversine_distance(lat, lon, row['latitude'], row['longitude']),
        axis=1
    )

    # Filter to radius and sort by distance
    nearby = towers_df[towers_df['distance_mi'] <= radius_miles].copy()
    nearby = nearby.sort_values('distance_mi')

    return nearby


def analyze_cell_tower_coverage(lat: float, lon: float, towers_df: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Analyze cell tower coverage for a property location.

    Args:
        lat: Property latitude
        lon: Property longitude
        towers_df: Optional pre-loaded tower DataFrame

    Returns:
        Dict with coverage analysis including nearby towers, carrier info, and metrics.
    """
    if towers_df is None:
        towers_df = load_cell_towers()

    if towers_df.empty:
        return {'available': False, 'error': 'Cell tower data not available'}

    # Get nearby towers at different radii
    towers_1mi = get_nearby_cell_towers(lat, lon, towers_df, radius_miles=1.0)
    towers_2mi = get_nearby_cell_towers(lat, lon, towers_df, radius_miles=2.0)

    # Count by attribution level
    fcc_matched = len(towers_2mi[towers_2mi['attribution_level'].str.contains('FCC Matched', na=False)])
    local_only = len(towers_2mi[towers_2mi['attribution_level'] == 'Local Only'])

    # Get unique carriers
    carriers = towers_2mi[towers_2mi['carrier_category'].notna()]['carrier_category'].unique().tolist()

    # Find closest tower
    closest_tower = None
    if not towers_2mi.empty:
        closest = towers_2mi.iloc[0]
        # Handle missing tower name - use street address as fallback
        tower_name = closest.get('tower_name')
        if pd.isna(tower_name) or str(tower_name).strip() == '':
            address = closest.get('address', 'Unknown')
            tower_name = str(address).split(',')[0].strip() if address else 'Unknown'
        closest_tower = {
            'name': tower_name,
            'distance_mi': closest['distance_mi'],
            'height_ft': closest.get('height_ft'),
            'structure_type': closest.get('structure_type'),
            'entity_name': closest.get('entity_name'),
            'attribution_level': closest.get('attribution_level')
        }

    return {
        'available': True,
        'towers_within_1mi': len(towers_1mi),
        'towers_within_2mi': len(towers_2mi),
        'fcc_matched_count': fcc_matched,
        'local_only_count': local_only,
        'carriers_detected': carriers,
        'closest_tower': closest_tower,
        'nearby_towers': towers_2mi
    }


@st.cache_data(ttl=86400)  # Cache for 24 hours
def load_parks_data() -> Dict[str, Any]:
    """
    Load parks data from static JSON file.

    The parks.json file contains pre-fetched data from Google Places API
    covering parks and playgrounds across Loudoun County.

    Returns:
        dict: Parks data with 'available', 'parks' list, 'metadata', and 'total_parks'
    """
    try:
        parks_file = os.path.join(DATA_DIR, 'config', 'parks.json')

        if not os.path.exists(parks_file):
            return {"available": False, "error": "Parks data file not found"}

        with open(parks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "available": True,
            "parks": data.get("parks", []),
            "metadata": data.get("_metadata", {}),
            "total_parks": len(data.get("parks", []))
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def get_nearest_parks(lat: float, lon: float, parks_data: Dict[str, Any],
                      limit: int = 5, max_distance: float = 10.0) -> Dict[str, Any]:
    """
    Get nearest parks to a property location.

    Uses haversine formula to calculate straight-line distances from the property
    to all parks in the database, then returns the nearest ones.

    Args:
        lat: Property latitude
        lon: Property longitude
        parks_data: Output from load_parks_data()
        limit: Maximum parks to return (default 5)
        max_distance: Maximum distance in miles to consider (default 10)

    Returns:
        dict: {
            'available': bool,
            'nearest_park': dict or None (closest park with distance),
            'nearby_parks': list (up to 'limit' parks sorted by distance),
            'count_within_5mi': int (parks within 5 miles)
        }
    """
    if not parks_data.get("available"):
        return {"available": False}

    parks = parks_data.get("parks", [])

    if not parks:
        return {"available": False, "error": "No parks in database"}

    # Calculate distances to all parks
    results = []
    for park in parks:
        distance = haversine_distance(
            lat, lon,
            park['latitude'],
            park['longitude']
        )

        if distance <= max_distance:
            results.append({
                **park,
                'distance_miles': round(distance, 2)
            })

    # Sort by distance (nearest first)
    results.sort(key=lambda x: x['distance_miles'])

    # Count parks within 5 miles
    count_5mi = sum(1 for p in results if p['distance_miles'] <= 5.0)

    return {
        "available": True,
        "nearest_park": results[0] if results else None,
        "nearby_parks": results[:limit],
        "count_within_5mi": count_5mi,
        "total_found": len(results)
    }


@st.cache_data
def check_flood_zone(lat: float, lon: float) -> Dict[str, Any]:
    """
    Check if property is in a FEMA flood zone using Loudoun County GIS.

    Uses the official Loudoun County GIS FEMA Flood layer API to determine
    flood zone status. Returns plain English descriptions for homeowner clarity.

    Args:
        lat: Latitude (WGS84)
        lon: Longitude (WGS84)

    Returns:
        Dictionary with flood zone status and details:
        - in_flood_zone: True/False/None (None on error)
        - zone_type: 'AE', 'A', 'FLOODWAY', or None
        - zone_description: Raw description from API
        - insurance_required: True/False/None
        - success: True/False
        - error: Error message if any
    """
    ENDPOINT = "https://logis.loudoun.gov/gis/rest/services/COL/FEMAFlood/MapServer/5/query"

    params = {
        'geometry': f'{lon},{lat}',
        'geometryType': 'esriGeometryPoint',
        'spatialRel': 'esriSpatialRelIntersects',
        'inSR': '4326',  # WGS84
        'outFields': 'COL_DESCRIPTION_DETAIL',
        'returnGeometry': 'false',
        'f': 'json'
    }

    try:
        response = requests.get(ENDPOINT, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        features = data.get('features', [])
        if not features:
            # Not in flood zone - good news!
            return {
                'in_flood_zone': False,
                'zone_type': None,
                'zone_description': None,
                'insurance_required': False,
                'source': 'FEMA FIRM via Loudoun County GIS',
                'success': True,
                'error': None
            }

        # Parse zone type from response
        zone_raw = features[0]['attributes'].get('COL_DESCRIPTION_DETAIL', '')

        # Determine zone type for plain English display
        if 'FLOODWAY' in zone_raw.upper():
            zone_type = 'FLOODWAY'
        elif 'ZONE AE' in zone_raw.upper():
            zone_type = 'AE'
        elif 'ZONE A' in zone_raw.upper():
            zone_type = 'A'
        else:
            zone_type = zone_raw  # Fallback to raw value

        return {
            'in_flood_zone': True,
            'zone_type': zone_type,
            'zone_description': zone_raw,
            'insurance_required': True,
            'source': 'FEMA FIRM via Loudoun County GIS',
            'success': True,
            'error': None
        }

    except requests.Timeout:
        return {
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'source': None,
            'success': False,
            'error': 'Flood zone data temporarily unavailable (timeout)'
        }
    except requests.RequestException as e:
        return {
            'in_flood_zone': None,
            'zone_type': None,
            'zone_description': None,
            'insurance_required': None,
            'source': None,
            'success': False,
            'error': f'Flood zone service error: {str(e)}'
        }


# Known short-name expansions for Fairfax schools where the GIS boundary
# data stores only a surname or abbreviation that differs from the official name.
_FAIRFAX_SCHOOL_NAME_EXPANSIONS = {
    "Carson": "Rachel Carson",
    "Poe": "Edgar Allan Poe",
    "Whitman": "Walt Whitman",
    "Twain": "Mark Twain",
    "Key": "Francis Scott Key",
    "Sandburg": "Carl Sandburg",
    "Thoreau": "Henry David Thoreau",
    "Edison": "Thomas Edison",
    "Jefferson": "Thomas Jefferson",
    "Jackson": "Andrew Jackson",
    "Kennedy": "John F. Kennedy",
    "Luther Jackson": "Luther Jackson",
    "Robinson": "Robinson",
    "Stuart": "J.E.B. Stuart",
    "Lee": "Robert E. Lee",
    "Holmes": "Oliver Wendell Holmes",
    "Kilmer": "Joyce Kilmer",
    "Frost": "Robert Frost",
    "Longfellow": "Henry Wadsworth Longfellow",
    "Whitman": "Walt Whitman",
}

_LEVEL_SUFFIXES = {
    'elementary': 'Elementary School',
    'middle': 'Middle School',
    'high': 'High School',
}


def expand_fairfax_school_name(short_name: str, level: str) -> str:
    """Expand abbreviated GIS school name to full official name.

    The Fairfax GIS boundary parquet files store only the base name
    (e.g. 'Oak Hill', 'Carson', 'Westfield'). This function constructs
    the full display name by applying known expansions and appending the
    school-level suffix.

    Args:
        short_name: Raw school_name from GIS parquet (e.g. "Oak Hill")
        level: One of 'elementary', 'middle', 'high'

    Returns:
        Full school name (e.g. "Oak Hill Elementary School")
    """
    if not short_name:
        return short_name

    # Apply known name expansions (e.g. "Carson" → "Rachel Carson")
    expanded = _FAIRFAX_SCHOOL_NAME_EXPANSIONS.get(short_name, short_name)

    # Append school level suffix
    suffix = _LEVEL_SUFFIXES.get(level, '')
    if suffix:
        return f"{expanded} {suffix}"
    return expanded


def find_assigned_schools(lat: float, lon: float) -> Dict[str, str]:
    """Find assigned schools for a location using Fairfax school zones."""
    # Use Fairfax class-based module
    try:
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        schools_analyzer = FairfaxSchoolsAnalysis()

        result = schools_analyzer.get_assigned_schools(lat, lon)

        if result:
            elem_name = result.get('elementary', {}).get('school_name') if result.get('elementary') else None
            mid_name = result.get('middle', {}).get('school_name') if result.get('middle') else None
            high_name = result.get('high', {}).get('school_name') if result.get('high') else None
            return {
                'elementary': expand_fairfax_school_name(elem_name, 'elementary') if elem_name else None,
                'middle': expand_fairfax_school_name(mid_name, 'middle') if mid_name else None,
                'high': expand_fairfax_school_name(high_name, 'high') if high_name else None,
                '_raw': result  # Keep raw data for additional details
            }
    except Exception as e:
        print(f"Error in Fairfax school lookup: {e}")

    # Return empty if lookup fails
    return {
        'elementary': None,
        'middle': None,
        'high': None
    }


def get_school_performance(school_name: str, performance_df: pd.DataFrame = None) -> Dict[str, Any]:
    """Get performance data for a specific school using Fairfax performance module.

    Tries multiple name variants to handle the mismatch between expanded display
    names (e.g. "Rachel Carson Middle School") and the shorter names stored in the
    performance parquet (e.g. "Carson Middle").
    """
    if not school_name:
        return {}

    try:
        from core.fairfax_school_performance_analysis import FairfaxSchoolPerformanceAnalysis
        perf_analyzer = FairfaxSchoolPerformanceAnalysis()

        # Build name variants to try (most specific → least specific)
        # Performance data uses short names like "Carson Middle" while display
        # names are expanded like "Rachel Carson Middle School"
        variants = [school_name]

        # Strip "School" suffix: "Rachel Carson Middle School" → "Rachel Carson Middle"
        if school_name.endswith(' School'):
            variants.append(school_name[:-len(' School')])

        # Try with last-word-of-base + level: "Rachel Carson Middle" → "Carson Middle"
        for level_word in ('Elementary', 'Middle', 'High'):
            if level_word in school_name:
                base = school_name.split(f' {level_word}')[0]
                last_word = base.split()[-1] if base.split() else base
                short = f"{last_word} {level_word}"
                if short not in variants:
                    variants.append(short)
                break

        for variant in variants:
            performance = perf_analyzer.get_school_performance(variant)
            if performance.get('found', False):
                return {
                    'reading': performance.get('recent_reading_pass_rate', 0),
                    'math': performance.get('recent_math_pass_rate', 0),
                    'science': performance.get('recent_science_pass_rate', 0),
                    'overall': performance.get('recent_overall_pass_rate', 0),
                    'trend': performance.get('trend', 'stable'),
                    '_raw': performance
                }
    except Exception as e:
        print(f"Error getting school performance: {e}")

    return {}


# =============================================================================
# SECTION: SCHOOLS
# =============================================================================

def display_schools_section(lat: float, lon: float):
    """Display school assignments and performance."""
    st.markdown("## 🏫 School Assignments")

    # Get assigned schools
    assignments = find_assigned_schools(lat, lon)
    performance_df = load_school_performance()

    # Short display names for the metric cards (strip level suffix)
    def _short_name(full_name, level):
        suffix = _LEVEL_SUFFIXES.get(level, '')
        if suffix and full_name and full_name.endswith(suffix):
            return full_name[:-len(suffix)].strip()
        return full_name

    # Display assigned schools
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Elementary School", _short_name(assignments['elementary'], 'elementary') or "N/A")
        if assignments['elementary']:
            perf = get_school_performance(assignments['elementary'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    with col2:
        st.metric("Middle School", _short_name(assignments['middle'], 'middle') or "N/A")
        if assignments['middle']:
            perf = get_school_performance(assignments['middle'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    with col3:
        st.metric("High School", _short_name(assignments['high'], 'high') or "N/A")
        if assignments['high']:
            perf = get_school_performance(assignments['high'], performance_df)
            if perf:
                st.caption(
                    f"Reading: {perf.get('reading', 'N/A')}% | Math: {perf.get('math', 'N/A')}%",
                    help="2024-25 Virginia SOL pass rates - percentage of students passing state standardized tests"
                )

    # Performance charts
    # PHASE 1 FIX: Fairfax data is summary format (no yearly trends)
    # Loudoun code expects year-by-year data for line charts, but Fairfax only has summary statistics
    # TODO Phase 2: Build Fairfax-specific charts using summary data columns:
    #   - school_name, recent_reading_pass_rate, recent_math_pass_rate
    #
    # if PLOTLY_AVAILABLE and not performance_df.empty:
    #     st.markdown("### School Performance Trends")
    #
    #     tab1, tab2 = st.tabs(["Reading Proficiency", "Math Proficiency"])
    #
    #     with tab1:
    #         # Get trend data for assigned schools
    #         chart_data = []
    #         for level, school in assignments.items():
    #             if school:
    #                 # Use match function to get exact school name from performance data
    #                 matched_name = match_school_in_performance_data(school, performance_df)
    #                 if matched_name:
    #                     school_data = performance_df[
    #                         performance_df['School_Name'] == matched_name
    #                     ]
    #                     for _, row in school_data.iterrows():
    #                         chart_data.append({
    #                             'School': school,
    #                             'Year': row['Year'],
    #                             'Reading Pass Rate': row.get('Reading_Pass_Rate', 0)
    #                         })
    #
    #         if chart_data:
    #             chart_df = pd.DataFrame(chart_data)
    #             fig = px.line(chart_df, x='Year', y='Reading Pass Rate', color='School',
    #                          title='Reading Proficiency Trends',
    #                          markers=True)
    #             fig.update_layout(yaxis_range=[0, 100])
    #             st.plotly_chart(fig, width='stretch')
    #         else:
    #             st.info("School performance trend data not available for assigned schools.")
    #
    #     with tab2:
    #         chart_data = []
    #         for level, school in assignments.items():
    #             if school:
    #                 # Use match function to get exact school name from performance data
    #                 matched_name = match_school_in_performance_data(school, performance_df)
    #                 if matched_name:
    #                     school_data = performance_df[
    #                         performance_df['School_Name'] == matched_name
    #                     ]
    #                     for _, row in school_data.iterrows():
    #                         chart_data.append({
    #                             'School': school,
    #                             'Year': row['Year'],
    #                             'Math Pass Rate': row.get('Math_Pass_Rate', 0)
    #                         })
    #
    #         if chart_data:
    #             chart_df = pd.DataFrame(chart_data)
    #             fig = px.line(chart_df, x='Year', y='Math Pass Rate', color='School',
    #                          title='Math Proficiency Trends',
    #                          markers=True)
    #             fig.update_layout(yaxis_range=[0, 100])
    #             st.plotly_chart(fig, width='stretch')
    #         else:
    #             st.info("School performance trend data not available for assigned schools.")

    # School Performance Comparison with State Average and Peer Schools
    if PLOTLY_AVAILABLE:
        with st.expander("📊 School Performance vs State & Peers", expanded=False):
            st.markdown("Compare assigned schools to Virginia state averages and nearby peer schools.")

            try:
                # Load enhanced performance data with state averages
                perf_with_state_df = load_performance_with_state_avg()
                coords_df = load_school_coordinates()

                # Create school level tabs
                elem_tab, middle_tab, high_tab = st.tabs([
                    "📚 Elementary School",
                    "🎓 Middle School",
                    "🏫 High School"
                ])

                # Elementary School Tab
                with elem_tab:
                    if assignments.get('elementary'):
                        elem_school = assignments['elementary']
                        # Find 2 nearest peer elementary schools
                        elem_peers = find_peer_schools(
                            elem_school,
                            'Elem',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if elem_peers:
                            st.caption(f"Comparing to: {elem_peers[0][0]} ({elem_peers[0][1]:.1f} mi), {elem_peers[1][0]} ({elem_peers[1][1]:.1f} mi)" if len(elem_peers) >= 2 else f"Comparing to: {elem_peers[0][0]} ({elem_peers[0][1]:.1f} mi)")

                        # Pre-compute charts to skip subjects with no real school data
                        _e_subjects = [
                            ("Math", "Math_Pass_Rate"),
                            ("Reading", "Reading_Pass_Rate"),
                            ("History", "History_Pass_Rate"),
                            ("Science", "Science_Pass_Rate"),
                            ("Overall", "Overall_Pass_Rate"),
                        ]
                        _e_charts = {}
                        for _name, _col in _e_subjects:
                            if not _schools_have_data(elem_school, elem_peers, _col, perf_with_state_df):
                                continue
                            _fig = create_performance_chart(elem_school, elem_peers, _name, _col, "Elem", perf_with_state_df)
                            if _fig:
                                _e_charts[_name] = _fig

                        if _e_charts:
                            _e_tab_names = list(_e_charts.keys())
                            _e_tabs = st.tabs(_e_tab_names)
                            for _tab, _name in zip(_e_tabs, _e_tab_names):
                                with _tab:
                                    st.plotly_chart(_e_charts[_name], width='stretch')
                        else:
                            st.info("No performance data available")
                    else:
                        st.info("No elementary school assigned to this property")

                # Middle School Tab
                with middle_tab:
                    if assignments.get('middle'):
                        mid_school = assignments['middle']
                        mid_peers = find_peer_schools(
                            mid_school,
                            'Middle',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if mid_peers:
                            st.caption(f"Comparing to: {mid_peers[0][0]} ({mid_peers[0][1]:.1f} mi), {mid_peers[1][0]} ({mid_peers[1][1]:.1f} mi)" if len(mid_peers) >= 2 else f"Comparing to: {mid_peers[0][0]} ({mid_peers[0][1]:.1f} mi)")

                        # Pre-compute charts to skip subjects with no real school data
                        _m_subjects = [
                            ("Math", "Math_Pass_Rate"),
                            ("Reading", "Reading_Pass_Rate"),
                            ("History", "History_Pass_Rate"),
                            ("Science", "Science_Pass_Rate"),
                            ("Overall", "Overall_Pass_Rate"),
                        ]
                        _m_charts = {}
                        for _name, _col in _m_subjects:
                            if not _schools_have_data(mid_school, mid_peers, _col, perf_with_state_df):
                                continue
                            _fig = create_performance_chart(mid_school, mid_peers, _name, _col, "Middle", perf_with_state_df)
                            if _fig:
                                _m_charts[_name] = _fig

                        if _m_charts:
                            _m_tab_names = list(_m_charts.keys())
                            _m_tabs = st.tabs(_m_tab_names)
                            for _tab, _name in zip(_m_tabs, _m_tab_names):
                                with _tab:
                                    st.plotly_chart(_m_charts[_name], width='stretch')
                        else:
                            st.info("No performance data available")
                    else:
                        st.info("No middle school assigned to this property")

                # High School Tab
                with high_tab:
                    if assignments.get('high'):
                        high_school = assignments['high']
                        high_peers = find_peer_schools(
                            high_school,
                            'High',
                            lat,
                            lon,
                            coords_df,
                            n=2
                        )

                        if high_peers:
                            st.caption(f"Comparing to: {high_peers[0][0]} ({high_peers[0][1]:.1f} mi), {high_peers[1][0]} ({high_peers[1][1]:.1f} mi)" if len(high_peers) >= 2 else f"Comparing to: {high_peers[0][0]} ({high_peers[0][1]:.1f} mi)")

                        # Pre-compute charts to skip subjects with no real school data
                        _h_subjects = [
                            ("Math", "Math_Pass_Rate"),
                            ("Reading", "Reading_Pass_Rate"),
                            ("History", "History_Pass_Rate"),
                            ("Science", "Science_Pass_Rate"),
                            ("Overall", "Overall_Pass_Rate"),
                        ]
                        _h_charts = {}
                        for _name, _col in _h_subjects:
                            if not _schools_have_data(high_school, high_peers, _col, perf_with_state_df):
                                continue
                            _fig = create_performance_chart(high_school, high_peers, _name, _col, "High", perf_with_state_df)
                            if _fig:
                                _h_charts[_name] = _fig

                        if _h_charts:
                            _h_tab_names = list(_h_charts.keys())
                            _h_tabs = st.tabs(_h_tab_names)
                            for _tab, _name in zip(_h_tabs, _h_tab_names):
                                with _tab:
                                    st.plotly_chart(_h_charts[_name], width='stretch')
                        else:
                            st.info("No performance data available")
                    else:
                        st.info("No high school assigned to this property")

            except Exception as e:
                st.error(f"Error loading school comparison data: {str(e)}")

    st.markdown("---")


# =============================================================================
# SECTION: CRIME & SAFETY (FAIRFAX)
# =============================================================================

def display_crime_section(lat: float, lon: float):
    """Display crime and safety analysis for Fairfax County."""
    st.markdown("## 🚨 Crime & Safety")

    try:
        from core.fairfax_crime_analysis import FairfaxCrimeAnalysis

        crime_analyzer = FairfaxCrimeAnalysis()

        # Get date range from metadata
        import json
        metadata_path = os.path.join(DATA_DIR, 'crime', 'processed', 'metadata.json')

        date_range_text = "Recent crime statistics"
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    date_range = metadata.get('date_range', {})
                    earliest = date_range.get('min', '')
                    latest = date_range.get('max', '')
                    if earliest and latest:
                        date_range_text = f"Crime data: {earliest} to {latest}"
            except:
                pass

        st.markdown(f"*{date_range_text}*")

        # Calculate safety score
        safety_score = crime_analyzer.calculate_safety_score(lat, lon, radius_miles=2.0)

        if safety_score:
            score = safety_score.get('score', 0)
            rating = safety_score.get('rating', 'Unknown')
            total_crimes = safety_score.get('total_crimes', 0)

            # Display score card
            st.markdown("### Safety Score")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Safety Score", f"{score}/100")
            with col2:
                st.metric("Rating", rating)
            with col3:
                st.metric("Incidents", total_crimes)

            # Crime breakdown
            breakdown = safety_score.get('breakdown', {})
            if breakdown:
                st.markdown("### Crime Breakdown (2.0 mile radius)")

                col1, col2, col3 = st.columns(3)
                with col1:
                    violent = breakdown.get('violent', breakdown.get('VIOLENT', 0))
                    st.metric("Violent Crimes", violent)
                with col2:
                    property_crimes = breakdown.get('property', breakdown.get('PROPERTY', 0))
                    st.metric("Property Crimes", property_crimes)
                with col3:
                    other = breakdown.get('other', breakdown.get('OTHER', 0))
                    st.metric("Other Incidents", other)

            # Context messaging
            if total_crimes == 0:
                st.success("✅ **Very Safe** - No reported incidents in the specified time period and radius.")
            elif total_crimes <= 5:
                st.success(f"✅ **Safe** - {total_crimes} reported incidents. Low crime area.")
            elif total_crimes <= 15:
                st.info(f"🟡 **Moderate** - {total_crimes} reported incidents. Average for the area.")
            else:
                st.warning(f"⚠️ **Higher Crime** - {total_crimes} reported incidents. Exercise normal caution.")

            # Incident details with map
            with st.expander("📋 View Individual Incidents"):
                incidents = crime_analyzer.get_crimes_near_point(lat, lon, radius_miles=2.0)

                if len(incidents) > 0:
                    # Build incident map
                    try:
                        import plotly.graph_objects as go

                        color_map = {'violent': 'red', 'property': 'orange', 'other': 'blue'}

                        fig = go.Figure()

                        # Property marker
                        fig.add_trace(go.Scattermapbox(
                            lat=[lat], lon=[lon],
                            mode='markers',
                            marker=dict(size=15, color='green'),
                            text=['Your Property'],
                            name='Property',
                            showlegend=True
                        ))

                        # Incident markers by category
                        for category, color in color_map.items():
                            cat_data = incidents[incidents['category'] == category]
                            if cat_data.empty:
                                continue
                            hover_text = cat_data.apply(
                                lambda row: f"{row['description']}<br>{row['address']}<br>{row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date']}",
                                axis=1
                            )
                            fig.add_trace(go.Scattermapbox(
                                lat=cat_data['latitude'], lon=cat_data['longitude'],
                                mode='markers',
                                marker=dict(size=8, color=color),
                                text=hover_text,
                                name=f'{category.title()} ({len(cat_data)})',
                                showlegend=True
                            ))

                        fig.update_layout(
                            mapbox=dict(
                                style='open-street-map',
                                center=dict(lat=lat, lon=lon),
                                zoom=12
                            ),
                            height=400,
                            margin=dict(l=0, r=0, t=0, b=0),
                            showlegend=True,
                            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)')
                        )

                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass  # Map is optional; table below still shows

                    st.markdown(f"**{len(incidents)} geocoded incidents** within 2 miles")

                    # Display table
                    display_df = incidents[['date', 'description', 'address', 'distance_miles']].copy()
                    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
                    display_df['distance_miles'] = display_df['distance_miles'].round(2)

                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'date': 'Date',
                            'description': 'Type',
                            'address': 'Location',
                            'distance_miles': st.column_config.NumberColumn('Distance (mi)', format="%.2f")
                        }
                    )
                else:
                    st.info("No geocoded incidents found within 2 miles.")

            # Geocoding coverage note
            geocoded_pct = safety_score.get('geocoded_percentage', 0)
            if geocoded_pct > 0 and geocoded_pct < 80:
                st.caption(f"📌 Note: {geocoded_pct:.1f}% of incidents have location data. Some crimes may not be reflected.")

        else:
            st.info("ℹ️ Crime data not available for this location.")

        st.caption("📌 Crime data from Fairfax County Police Department via public API.")

    except FileNotFoundError:
        st.warning("⚠️ Crime data not available for this area")
    except Exception as e:
        st.error(f"❌ Error in crime analysis: {e}")
        with st.expander("Error Details"):
            import traceback
            st.code(traceback.format_exc())


# =============================================================================
# SECTION: LOCATION QUALITY
# =============================================================================

def analyze_location_quality(lat: float, lon: float, address: str) -> Dict[str, Any]:
    """Analyze location quality using GIS data (cached for performance)."""
    try:
        # Use cached analyzer for better performance across property analyses
        analyzer = get_cached_location_analyzer()
        return analyzer.analyze_location(lat, lon, address)
    except Exception as e:
        return {'error': str(e)}


def display_location_section(location_data: Dict[str, Any], power_lines: Dict[str, Any] = None, metro_data: Dict[str, Any] = None, flood_data: Dict[str, Any] = None, parks_data: Dict[str, Any] = None, lat: float = None, lon: float = None):
    """Display location quality summary including flood zone, parks, and other features."""
    st.markdown("## 📍 Location Quality")

    if power_lines is None:
        power_lines = {}
    if metro_data is None:
        metro_data = {}
    if flood_data is None:
        flood_data = {}
    if parks_data is None:
        parks_data = {}

    # Initialize traffic analyzer for ADT data
    traffic_analyzer = None
    try:
        traffic_analyzer = LoudounTrafficVolumeAnalyzer()
    except Exception:
        pass  # Traffic data optional

    if 'error' in location_data:
        st.warning(f"Location analysis unavailable: {location_data['error']}")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Key Location Features:**")

        highlights = []

        # Road classification
        road_class = location_data.get('road_classification', {})
        if isinstance(road_class, dict):
            classification = road_class.get('classification', 'Unknown')
            traffic = road_class.get('traffic_level', 'Unknown')
            highlights.append(f"🛣️ **Road Type:** {classification} ({traffic} traffic)")

        # Highway access with ADT
        hw = location_data.get('highway_proximity', {})
        hw_name = None
        hw_dist = 0
        hw_adt = None
        hw_vdot_route = None
        if isinstance(hw, dict) and hw.get('nearest_highway'):
            hw_name = hw.get('nearest_highway', 'Unknown')
            hw_dist = hw.get('distance_miles', 0)
            hw_level = hw.get('proximity_level', '')
            # Color indicator based on proximity
            if hw_dist < 0.5:
                hw_icon = "🔴"  # Very close - noise concern
            elif hw_dist < 1.0:
                hw_icon = "🟡"  # Close
            else:
                hw_icon = "🟢"  # Good distance

            # Get ADT from traffic analyzer
            if traffic_analyzer and lat and lon:
                hw_traffic = traffic_analyzer.get_traffic_volume(hw_name, lat, lon)
                if hw_traffic:
                    hw_adt = hw_traffic.get('adt')
                    hw_vdot_route = hw_traffic.get('vdot_route')

            # Build display string with optional ADT
            hw_display = f"🚗 **Highway Access:** {hw_icon} {hw_name} ({hw_dist:.1f} mi)"
            if hw_adt:
                hw_display += f" • {traffic_analyzer.format_adt(hw_adt)}"
            highlights.append(hw_display)

        # Collector Roads (major local roads) with ADT
        coll = location_data.get('collector_proximity', {})
        coll_name = None
        coll_dist = 0
        coll_adt = None
        coll_vdot_route = None
        if isinstance(coll, dict) and coll.get('nearest_collector'):
            coll_name = coll.get('nearest_collector', 'Unknown')
            coll_dist = coll.get('distance_miles', 0)
            # Color indicator based on proximity (collectors are local, so different thresholds)
            if coll_dist < 0.3:
                coll_icon = "🔴"  # Very close - traffic concern
            elif coll_dist < 0.75:
                coll_icon = "🟡"  # Close
            else:
                coll_icon = "🟢"  # Good distance

            # Get ADT from traffic analyzer
            if traffic_analyzer and lat and lon:
                coll_traffic = traffic_analyzer.get_traffic_volume(coll_name, lat, lon)
                if coll_traffic:
                    coll_adt = coll_traffic.get('adt')
                    coll_vdot_route = coll_traffic.get('vdot_route')

            # Build display string with optional ADT
            coll_display = f"🛤️ **Major Road:** {coll_icon} {coll_name} ({coll_dist:.1f} mi)"
            if coll_adt:
                coll_display += f" • {traffic_analyzer.format_adt(coll_adt)}"
            highlights.append(coll_display)

        # Airport zone - Plain English display (lead with severity, not zone codes)
        aiod = location_data.get('aiod_status', {})
        if isinstance(aiod, dict):
            if aiod.get('in_aiod'):
                zone = aiod.get('zone', 'Unknown')
                airport = aiod.get('airport', 'Dulles')
                # Translate zone codes to plain English severity
                if 'Ldn 65' in zone or 'LDN65' in zone.upper():
                    severity = "High Aircraft Noise Zone"
                elif 'Ldn 60' in zone or 'LDN60' in zone.upper():
                    if 'Buffer' in zone or 'BUFFER' in zone.upper():
                        severity = "Aircraft Noise Buffer Zone"
                    else:
                        severity = "Moderate Aircraft Noise Zone"
                else:
                    severity = "Aircraft Noise Buffer Zone"
                highlights.append(f"🔔 **{severity}** - Disclosure required ({airport})")
            else:
                highlights.append("✅ **No Aircraft Noise Disclosure** - Outside disclosure zones")

            dulles_dist = aiod.get('distance_to_dulles_miles', 0)
            if dulles_dist:
                highlights.append(f"🛫 **Dulles Airport:** {dulles_dist:.1f} miles")

        # Flood Zone - Plain English display (lead with impact, not zone codes)
        if flood_data and flood_data.get('success'):
            if flood_data.get('in_flood_zone'):
                zone_type = flood_data.get('zone_type', 'Unknown')
                if zone_type == 'FLOODWAY':
                    highlights.append("⚠️ **Flood Insurance Required - Building Restricted** - Property in floodway")
                else:
                    highlights.append("🔔 **Flood Insurance Required** - Property in mapped flood risk area")
            else:
                highlights.append("✅ **No Flood Insurance Required** - Not in mapped flood zone")
        elif flood_data and not flood_data.get('success'):
            # API error - show neutral status
            highlights.append("⚪ **Flood Zone:** Data unavailable")

        # Parks proximity - show nearest park
        if parks_data and parks_data.get('available') and parks_data.get('nearest_park'):
            nearest = parks_data['nearest_park']
            dist = nearest['distance_miles']
            name = nearest['name']

            if dist < 0.5:
                highlights.append(f"🌳 **Parks:** {name} ({dist:.1f} mi) - Walking distance")
            elif dist <= 5.0:
                highlights.append(f"🌳 **Parks:** {name} ({dist:.1f} mi)")
            else:
                highlights.append(f"🌳 **Parks:** Nearest park {dist:.1f} miles away")
        elif parks_data and parks_data.get('available'):
            highlights.append("🌳 **Parks:** Limited park access (>10 mi)")

        # Metro Access
        if metro_data and metro_data.get('available'):
            prox = metro_data.get('proximity', {})
            tier = metro_data.get('tier', {})
            station = prox.get('nearest_station', 'Unknown')
            distance = prox.get('distance_miles', 0)
            tier_name = tier.get('tier', 'Unknown')
            tier_icon = tier.get('icon', '⚪')
            highlights.append(f"🚇 **Metro Access:** {tier_icon} {station} ({distance:.1f} mi) - {tier_name}")

        # Power Infrastructure - conditional display based on impact
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)
            nearest_built = power_lines.get('nearest_built_line')
            nearest_approved = power_lines.get('nearest_approved_line')

            # Determine which line is nearest (built or approved)
            nearest_line = None
            nearest_status = None
            if nearest_built and nearest_approved:
                if nearest_built['distance_miles'] <= nearest_approved['distance_miles']:
                    nearest_line = nearest_built
                    nearest_status = "Built"
                else:
                    nearest_line = nearest_approved
                    nearest_status = "Approved"
            elif nearest_built:
                nearest_line = nearest_built
                nearest_status = "Built"
            elif nearest_approved:
                nearest_line = nearest_approved
                nearest_status = "Approved"

            # For LOW/MODERATE impact (scores 1-3): Add to highlights list (inline)
            if impact_score <= 3:
                if impact_score == 3:
                    if nearest_line:
                        voltage = nearest_line['voltage']
                        dist = nearest_line['distance_miles']
                        highlights.append(f"⚡ **Power Lines:** 🟡 Moderate ({impact_score}/5) - {voltage}kV at {dist:.1f} mi")
                elif impact_score == 2:
                    if nearest_line:
                        voltage = nearest_line['voltage']
                        dist = nearest_line['distance_miles']
                        highlights.append(f"⚡ **Power Lines:** 🟢 Low Impact ({impact_score}/5) - {voltage}kV at {dist:.1f} mi")
                else:  # score 1
                    highlights.append("✅ **Power Lines:** No major lines within 1 mile")

                # Future line if different from nearest (still inline)
                if nearest_approved and nearest_status == "Built":
                    voltage = nearest_approved['voltage']
                    dist = nearest_approved['distance_miles']
                    highlights.append(f"🔮 **Future Power Line:** {voltage}kV approved at {dist:.1f} mi")

        # Render all highlights together
        for h in highlights:
            st.markdown(h)

        # Road Access Details expander (show if we have highway or collector data)
        show_road_expander = hw_name or coll_name
        if show_road_expander:
            with st.expander("ℹ️ Road Access Details"):
                # Load road context for travel times
                road_context = load_road_context()
                roads_data = road_context.get('roads', {})
                destinations = road_context.get('destinations', {})

                if hw_name:
                    # Look up highway in road context (try exact match, then normalized)
                    hw_context = roads_data.get(hw_name)
                    if not hw_context:
                        hw_context = roads_data.get(hw_name.upper())
                    if not hw_context:
                        normalized_hw = normalize_road_name(hw_name)
                        hw_context = roads_data.get(normalized_hw)
                    else:
                        normalized_hw = hw_name.upper()

                    # Display expanded road name if we matched via normalization
                    if hw_context:
                        display_hw_name = expand_road_name(normalized_hw)
                    else:
                        display_hw_name = hw_name

                    # Build final display with route number first if available
                    if hw_context and hw_context.get('route_number'):
                        final_display = f"{hw_context['route_number']} ({display_hw_name})"
                    elif hw_vdot_route and hw_vdot_route != hw_name:
                        final_display = f"{display_hw_name} ({hw_vdot_route})"
                    else:
                        final_display = display_hw_name

                    st.markdown(f"**Highway: {final_display}**")

                    # Add toll info if available
                    if hw_context:
                        if hw_context.get('toll'):
                            st.markdown("- Toll: **Yes** (paid)")
                        else:
                            st.markdown("- Toll: No")

                        # Travel times
                        travel_times = hw_context.get('travel_times', {})
                        if travel_times:
                            route_label = hw_context.get('route_number', 'this highway')
                            st.markdown(f"- **Travel Times** (via {route_label}):")
                            for dest_key, times in travel_times.items():
                                if 'error' not in times:
                                    dest_name = destinations.get(dest_key, {}).get('name', dest_key.title())
                                    rush = times.get('rush_min', 0)
                                    typical = times.get('offpeak_min', 0)
                                    min_time = min(rush, typical)
                                    max_time = max(rush, typical)
                                    st.markdown(f"  - {dest_name}: ~{min_time}-{max_time} min")

                if coll_name:
                    # Look up collector in road context (try exact match, then normalized)
                    coll_context = roads_data.get(coll_name)
                    if not coll_context:
                        coll_context = roads_data.get(coll_name.upper())
                    if not coll_context:
                        normalized_coll = normalize_road_name(coll_name)
                        coll_context = roads_data.get(normalized_coll)
                    else:
                        normalized_coll = coll_name.upper()

                    # Only show Major Road section if we have travel time data
                    if coll_context and coll_context.get('travel_times'):
                        if hw_name:
                            st.markdown("---")

                        # Display expanded road name if we matched via normalization
                        if coll_context:
                            display_coll_name = expand_road_name(normalized_coll)
                        else:
                            display_coll_name = coll_name

                        # Build final display with route number first if available
                        if coll_context and coll_context.get('route_number'):
                            final_display = f"{coll_context['route_number']} ({display_coll_name})"
                        elif coll_vdot_route and coll_vdot_route != coll_name:
                            final_display = f"{display_coll_name} ({coll_vdot_route})"
                        else:
                            final_display = display_coll_name

                        st.markdown(f"**Major Road: {final_display}**")

                        # Add travel times for collectors
                        travel_times = coll_context.get('travel_times', {})
                        if travel_times:
                            route_label = coll_context.get('route_number', 'this road')
                            st.markdown(f"- **Travel Times** (via {route_label}):")
                            for dest_key, times in travel_times.items():
                                if 'error' not in times:
                                    dest_name = destinations.get(dest_key, {}).get('name', dest_key.title())
                                    rush = times.get('rush_min', 0)
                                    typical = times.get('offpeak_min', 0)
                                    min_time = min(rush, typical)
                                    max_time = max(rush, typical)
                                    st.markdown(f"  - {dest_name}: ~{min_time}-{max_time} min")

                st.markdown("---")
                st.caption("Data: VDOT Traffic Volume, Google Distance Matrix")

        # Aircraft Noise Information (expandable) - Plain English display
        if isinstance(aiod, dict):
            with st.expander("✈️ Aircraft Noise Information"):
                if aiod.get('in_aiod'):
                    # Inside a noise disclosure zone
                    zone = aiod.get('zone', 'Unknown')
                    zone_code = aiod.get('zone_code', zone)
                    airport = aiod.get('airport', 'Dulles International')
                    construction_req = aiod.get('construction_requirements', 'None specified')

                    # Determine severity level for plain English display
                    if 'Ldn 65' in zone or 'LDN65' in str(zone_code).upper():
                        severity = "high aircraft noise area"
                        st.markdown(f"""
This property is in a **{severity}** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Frequent aircraft noise expected during arrivals and departures
- Seller must disclose noise impact to buyers
- New residential construction requires sound-reducing features

**Technical Reference:**
- Zone: Ldn 65+ (elevated noise contour)
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                    elif 'Ldn 60' in zone or 'LDN60' in str(zone_code).upper():
                        if 'Buffer' in zone or 'BUFFER' in str(zone_code).upper():
                            # Buffer zone
                            st.markdown(f"""
This property is in an **aircraft noise buffer zone** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Occasional overflight noise possible
- Seller must disclose proximity to airport
- No special construction requirements

**Technical Reference:**
- Zone: 1-Mile Buffer
- Building Requirements: None required
- Disclosure: Required at sale
""")
                        else:
                            # Moderate zone (Ldn 60-65)
                            st.markdown(f"""
This property is in a **moderate aircraft noise area** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Periodic aircraft noise during busy flight times
- Seller must disclose noise impact to buyers
- Sound-reducing construction recommended for new buildings

**Technical Reference:**
- Zone: Ldn 60-65 (moderate noise contour)
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                    else:
                        # Fallback for buffer or unknown zones
                        st.markdown(f"""
This property is in an **aircraft noise buffer zone** near {airport}.
Seller disclosure of aircraft noise is required at sale.

**What This Means:**
- Occasional overflight noise possible
- Seller must disclose proximity to airport
- No special construction requirements

**Technical Reference:**
- Zone: Buffer area
- Building Requirements: {construction_req}
- Disclosure: Required at sale
""")
                else:
                    # Outside all noise disclosure zones
                    dulles_dist = aiod.get('distance_to_dulles_miles', 0)

                    st.markdown(f"""
This property is **not in an aircraft noise disclosure zone**.
No noise-related disclosures required at sale.

**What This Means:**
- No aircraft noise restrictions or disclosures required
- No special construction requirements
- Full flexibility for property development

**Distance to Dulles Airport:** {dulles_dist:.1f} miles
""")

                st.caption("📊 Source: Loudoun County Airport Impact Overlay Districts (Jan 2023)")

        # Flood Zone Details (expandable) - Plain English display
        if flood_data and flood_data.get('success'):
            if flood_data.get('in_flood_zone'):
                zone_type = flood_data.get('zone_type', 'Unknown')

                if zone_type == 'FLOODWAY':
                    with st.expander("⚠️ Flood Insurance Required - Building Restricted"):
                        st.markdown("""
This property is in a regulatory floodway, which is reserved for the
passage of floodwaters. This designation has both financial and
development implications.

**Financial Impact:**
- Flood insurance required by mortgage lenders
- Costs vary based on property specifics and risk level

**Development Restrictions:**
- New dwellings/enclosed structures not permitted
- Cannot place fill material or obstruct flood flow
- Area must remain open for floodwater passage
- Only open-space uses allowed (yards, parking, gardens)

**What This Means:**
The floodway is the river channel plus adjacent land needed to carry
floodwaters. Strict building limitations apply to prevent obstructing
flood flow.

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                elif zone_type == 'AE':
                    with st.expander("🔔 Flood Insurance Required"):
                        st.markdown("""
This property is located in a mapped flood risk area where mortgage
lenders typically require flood insurance.

**What This Means:**
- Federally-backed mortgage lenders require flood insurance in this zone
- Insurance costs vary based on property elevation, value, and other factors
- 1% annual chance of flooding (26% over 30-year mortgage)

**Technical Details:**
- FEMA Zone: AE (detailed flood studies completed)
- Base flood elevations determined for this area

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                elif zone_type == 'A':
                    with st.expander("🔔 Flood Insurance Required"):
                        st.markdown("""
This property is located in a mapped flood risk area where mortgage
lenders typically require flood insurance.

**What This Means:**
- Federally-backed mortgage lenders require flood insurance in this zone
- Insurance costs vary based on property elevation, value, and other factors
- 1% annual chance of flooding (26% over 30-year mortgage)

**Technical Details:**
- FEMA Zone: A (approximate analysis)
- Base flood elevations not yet determined

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

                else:
                    # Fallback for any other zone type
                    with st.expander("🔔 Flood Zone Information"):
                        st.markdown(f"""
This property is located in a mapped flood risk area ({zone_type}).
Mortgage lenders may require flood insurance.

💡 Get actual insurance quotes at [FloodSmart.gov](https://www.floodsmart.gov) or through your insurance agent
""")
                        st.caption(f"📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

            else:
                # Outside all flood zones
                with st.expander("✅ Flood Zone Information"):
                    st.markdown("""
This property is not located in a FEMA-designated flood risk area.
Mortgage lenders do not require flood insurance.

**What This Means:**
- Flood insurance optional but may be advisable
- Approximately 25% of flood claims come from outside mapped zones
- Consider coverage if near streams, ponds, or low-lying areas

💡 Learn more about optional flood insurance at [FloodSmart.gov](https://www.floodsmart.gov)
""")
                    st.caption("📊 Source: FEMA Flood Insurance Rate Map via Loudoun County GIS")

        # Parks & Recreation (expandable)
        if parks_data and parks_data.get('available'):
            with st.expander("🌳 Parks & Recreation"):
                nearby = parks_data.get('nearby_parks', [])
                count_5mi = parks_data.get('count_within_5mi', 0)

                if nearby:
                    nearest = nearby[0]
                    dist = nearest['distance_miles']

                    # Summary statement based on distance
                    if dist < 0.5:
                        st.markdown(f"**{count_5mi} parks within 5 miles**, with {nearest['name']} "
                                  f"just {dist:.1f} miles away - **walking distance**.")
                    elif dist <= 2.0:
                        st.markdown(f"**{count_5mi} parks within 5 miles**, with {nearest['name']} "
                                  f"{dist:.1f} miles away - **short drive**.")
                    else:
                        st.markdown(f"**{count_5mi} parks within 5 miles**. Nearest is {nearest['name']} "
                                  f"at {dist:.1f} miles.")

                    st.markdown("")
                    st.markdown("**Nearest Parks:**")

                    # List up to 5 nearest parks
                    for park in nearby[:5]:
                        # Format park types for display
                        park_types = park.get('types', [])
                        type_labels = []
                        if 'park' in park_types:
                            type_labels.append('Park')
                        if 'playground' in park_types:
                            type_labels.append('Playground')
                        type_str = ", ".join(type_labels) if type_labels else "Recreation"

                        st.markdown(f"• **{park['name']}** - {park['distance_miles']:.1f} mi ({type_str})")

                    st.markdown("")
                    st.caption("📊 Source: Google Places (Dec 2025)")
                else:
                    st.markdown("No parks found within 10 miles of this property.")
                    st.markdown("")
                    st.caption("📊 Source: Google Places (Dec 2025)")

        # Metro Access Details (expandable)
        if metro_data and metro_data.get('available'):
            prox = metro_data.get('proximity', {})
            tier = metro_data.get('tier', {})
            drive_time = metro_data.get('drive_time', {})
            narrative = metro_data.get('narrative', '')

            with st.expander("🚇 Silver Line Metro Access Details"):
                # Metrics row
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Nearest Station", prox.get('nearest_station', 'N/A'))
                with m_col2:
                    st.metric("Distance", f"{prox.get('distance_miles', 0):.1f} mi")
                with m_col3:
                    st.metric("Drive Time", drive_time.get('display', 'N/A'))

                # Tier badge
                tier_icon = tier.get('icon', '⚪')
                tier_name = tier.get('tier', 'Unknown')
                tier_desc = tier.get('tier_description', '')
                st.markdown(f"**Accessibility:** {tier_icon} {tier_name} - {tier_desc}")

                # Narrative
                if narrative:
                    st.markdown(f"_{narrative}_")

                # All stations
                st.markdown("**All Silver Line Stations in Loudoun:**")
                for station in prox.get('all_stations', []):
                    st.markdown(f"• {station['name']}: {station['distance_miles']:.1f} miles")

                st.markdown("---")
                st.caption("The Silver Line connects Loudoun County to Tysons Corner, Arlington, and downtown Washington DC. Walk-to-Metro properties typically command 10-20% premium valuations.")

        # For HIGH impact (scores 4-5): Show separate prominent section AFTER highlights
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)

            if impact_score >= 4:
                nearest_built = power_lines.get('nearest_built_line')
                nearest_approved = power_lines.get('nearest_approved_line')
                lines_within_mile = power_lines.get('lines_within_one_mile', 0)

                # Determine nearest line
                nearest_line = None
                nearest_status = None
                if nearest_built and nearest_approved:
                    if nearest_built['distance_miles'] <= nearest_approved['distance_miles']:
                        nearest_line = nearest_built
                        nearest_status = "Built"
                    else:
                        nearest_line = nearest_approved
                        nearest_status = "Approved"
                elif nearest_built:
                    nearest_line = nearest_built
                    nearest_status = "Built"
                elif nearest_approved:
                    nearest_line = nearest_approved
                    nearest_status = "Approved"

                st.markdown("**⚡ Power Infrastructure/Major Power Lines:**")

                if impact_score == 5:
                    st.error(f"🔴 Very High Impact ({impact_score}/5)")
                else:
                    st.error(f"🔴 High Impact ({impact_score}/5)")

                if nearest_line:
                    voltage = nearest_line['voltage']
                    dist = nearest_line['distance_miles']
                    st.markdown(f"Nearest line: {voltage}kV at {dist:.2f} miles ({nearest_status})")

                if lines_within_mile > 0:
                    st.markdown(f"{lines_within_mile} line(s) within 1 mile")

                # Additional future line if exists and wasn't nearest
                if nearest_approved and nearest_status == "Built":
                    voltage = nearest_approved['voltage']
                    dist = nearest_approved['distance_miles']
                    st.markdown(f"🔮 Additional future line: {voltage}kV approved at {dist:.2f} mi")

    with col2:
        # Quality score (computed from factors)
        quality_score = 8.0  # Base score

        # Adjust based on road type
        road_class = location_data.get('road_classification', {})
        if isinstance(road_class, dict):
            traffic = road_class.get('traffic_level', '')
            if traffic == 'Very Low':
                quality_score += 1.0
            elif traffic == 'High':
                quality_score -= 1.0

        # Adjust for airport zone
        aiod = location_data.get('aiod_status', {})
        if isinstance(aiod, dict) and aiod.get('in_aiod'):
            quality_score -= 0.5

        # Adjust for power line proximity
        if power_lines and 'error' not in power_lines:
            impact_score = power_lines.get('visual_impact_score', 1)
            if impact_score >= 5:
                quality_score -= 1.5  # Very High impact
            elif impact_score >= 4:
                quality_score -= 1.0  # High impact
            elif impact_score >= 3:
                quality_score -= 0.5  # Moderate impact

        quality_score = min(10.0, max(1.0, quality_score))

        st.metric(
            "Location Score",
            f"{quality_score:.1f}/10",
            help="Based on road type, traffic levels, airport proximity, and power infrastructure"
        )

    st.markdown("---")


# =============================================================================
# SECTION: NEIGHBORHOOD AMENITIES
# =============================================================================

def display_neighborhood_section(neighborhood_data: Dict[str, Any]):
    """Display neighborhood amenities analysis."""
    st.markdown("## 🏪 Discover Your Neighborhood")

    if not neighborhood_data or not neighborhood_data.get('available'):
        error = neighborhood_data.get('error', 'Unknown error') if neighborhood_data else 'Data not available'
        st.warning(f"Neighborhood analysis unavailable: {error}")
        return

    amenities = neighborhood_data.get('amenities', {})
    convenience = neighborhood_data.get('convenience', {})
    narrative = neighborhood_data.get('narrative', '')

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        score = convenience.get('score', 0)
        rating = convenience.get('rating', 'Unknown')
        # Color indicator based on rating
        if rating == 'Excellent':
            color_indicator = "🟢"
        elif rating == 'Good':
            color_indicator = "🟡"
        elif rating == 'Fair':
            color_indicator = "🟠"
        else:
            color_indicator = "🔴"
        st.metric(
            "Convenience Score",
            f"{score}/10",
            help="Based on nearby dining, grocery, and shopping options"
        )
        st.markdown(f"{color_indicator} **{rating}**")

    with col2:
        dining = amenities.get('dining', {})
        dining_count = dining.get('count', 0)
        st.metric("Dining Nearby", f"{dining_count} places")

    with col3:
        grocery = amenities.get('grocery', {})
        grocery_nearest = grocery.get('nearest_distance')
        if grocery_nearest is not None:
            st.metric("Nearest Grocery", f"{grocery_nearest:.1f} mi")
        else:
            st.metric("Nearest Grocery", "N/A")

    with col4:
        walkable = amenities.get('summary', {}).get('walkable_count', 0)
        st.metric("Walkable Places", f"{walkable}", help="Places within 0.5 miles")

    # Category tabs
    dining_tab, grocery_tab, shopping_tab = st.tabs(["🍽️ Dining", "🛒 Grocery", "🛍️ Shopping"])

    with dining_tab:
        dining_places = amenities.get('dining', {}).get('places', [])
        if dining_places:
            for place in dining_places[:5]:  # Show top 5
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                price_str = "$" * place.get('price_level', 0) if place.get('price_level') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str} {price_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No restaurants found within 1 mile")

    with grocery_tab:
        grocery_places = amenities.get('grocery', {}).get('places', [])
        if grocery_places:
            for place in grocery_places[:5]:
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No grocery stores found within 1.5 miles")

    with shopping_tab:
        shopping_places = amenities.get('shopping', {}).get('places', [])
        if shopping_places:
            for place in shopping_places[:5]:
                rating_str = f"⭐ {place['rating']}" if place.get('rating') else ""
                st.markdown(f"**{place['name']}** - {place['distance_miles']:.2f} mi {rating_str}")
                if place.get('address'):
                    st.caption(place['address'])
        else:
            st.info("No shopping centers found within 2 miles")

    # Expandable narrative
    if narrative:
        with st.expander("📝 Neighborhood Summary"):
            st.markdown(narrative)

            # Show highlights if available
            highlights = convenience.get('highlights', [])
            if highlights:
                st.markdown("**Key Highlights:**")
                for h in highlights:
                    st.markdown(f"• {h}")

    # Cache status (subtle footer)
    summary = amenities.get('summary', {})
    if summary.get('served_from_cache'):
        st.caption("📦 Data from cache (updated within 7 days)")
    else:
        api_calls = summary.get('api_calls_made', 0)
        if api_calls > 0:
            st.caption(f"🔄 Fresh data ({api_calls} API calls)")

    st.markdown("---")


# =============================================================================
# SECTION: COMMUNITY & HOA
# =============================================================================

def display_community_section(valuation_data: Dict[str, Any], lat: float = None, lon: float = None):
    """Display community/HOA information based on subdivision lookup and optional spatial coordinates."""
    if not COMMUNITY_LOOKUP_AVAILABLE:
        return

    # Get subdivision and hoa_fee from valuation data
    subdivision = valuation_data.get('subdivision') if valuation_data else None
    hoa_fee = valuation_data.get('hoa_fee') if valuation_data else None

    # Skip if no subdivision data available
    if not subdivision:
        return

    # 3-TIER COMMUNITY MATCHING STRATEGY
    community_ctx = None
    match_method = None

    # TIER 1 & 2: Try spatial lookup first (64 communities via GIS)
    if SPATIAL_LOOKUP_AVAILABLE and lat and lon and _COMMUNITY_LOOKUP_INSTANCE:
        try:
            spatial_result = lookup_community(lat, lon)

            if spatial_result:
                display_name = spatial_result.get('name')

                # Try to find rich data for this community
                community_key = _COMMUNITY_LOOKUP_INSTANCE.get_community_key_by_display_name(display_name)

                if community_key:
                    # TIER 1: Spatial + Rich Data (17 communities)
                    summary = _COMMUNITY_LOOKUP_INSTANCE.get_community_summary(community_key)
                    community_ctx = {
                        'community_found': True,
                        'community_key': community_key,
                        'display_name': summary['display_name'],
                        'location': summary.get('location'),
                        'hoa_website': summary.get('hoa_website'),
                        'management_company': summary.get('management_company'),
                        'monthly_fee': hoa_fee or summary.get('monthly_fee'),
                        'fee_source': 'API' if hoa_fee else summary.get('fee_source', 'Community Data'),
                        'fee_year': summary.get('fee_year'),
                        'fee_includes': summary.get('fee_includes', []),
                        'amenities': summary.get('amenities_list', []),
                        'amenities_detail': summary.get('amenities_detail', {}),
                        'total_homes': summary.get('total_homes'),
                        'total_acres': spatial_result.get('area_acres') or summary.get('total_acres'),
                        'gated': summary.get('gated', False),
                        'schools': summary.get('schools', {}),
                        'match_method': 'spatial',
                        'spatial_confidence': spatial_result.get('confidence', 'high'),
                        'data_quality': 'complete'
                    }
                else:
                    # TIER 2: Spatial Only (47 communities - waiting for VA data)
                    community_ctx = {
                        'community_found': True,
                        'display_name': display_name,
                        'total_acres': spatial_result.get('area_acres'),
                        'match_method': 'spatial',
                        'spatial_confidence': spatial_result.get('confidence', 'high'),
                        'data_quality': 'gis_only',
                        'pending_message': 'Community identified via GIS boundaries. Amenity details coming soon.'
                    }
        except Exception as e:
            print(f"Spatial lookup failed: {e}")
            # Continue to pattern fallback

    # TIER 3: Fall back to pattern matching (17 communities via fnmatch)
    if not community_ctx or not community_ctx.get('community_found'):
        pattern_ctx = create_property_community_context(subdivision, hoa_fee)
        if pattern_ctx.get('community_found'):
            community_ctx = pattern_ctx
            community_ctx['match_method'] = 'pattern'
            community_ctx['data_quality'] = 'complete'
        elif not community_ctx:
            # No match from any method
            community_ctx = {'community_found': False}

    # Section header
    st.markdown("## 🏘️ Community & Amenities")

    if community_ctx.get('community_found'):
        # Community found - display full details
        display_name = community_ctx.get('display_name', 'Unknown')
        monthly_fee = community_ctx.get('monthly_fee')
        fee_source = community_ctx.get('fee_source', '')
        hoa_website = community_ctx.get('hoa_website')
        amenities = community_ctx.get('amenities', [])
        is_gated = community_ctx.get('gated', False)

        # Community name header
        gated_badge = " 🔒" if is_gated else ""
        st.markdown(f"### {display_name}{gated_badge}")

        # Metrics row
        col1, col2, col3 = st.columns(3)

        with col1:
            if monthly_fee:
                st.metric("Monthly HOA Fee", f"${monthly_fee:,.0f}")
                if fee_source:
                    st.caption(f"Source: {fee_source}")
            else:
                st.metric("Monthly HOA Fee", "Contact HOA")

        with col2:
            total_homes = community_ctx.get('total_homes')
            if total_homes:
                st.metric("Community Size", f"{total_homes:,} homes")
            else:
                st.metric("Community Size", "—")

        with col3:
            if is_gated:
                st.metric("Access", "Gated Community")
            else:
                st.metric("Access", "Open Community")

        # Amenities
        if amenities:
            st.markdown("#### Amenities")
            # Display amenities in columns for better layout
            amenity_cols = st.columns(2)
            for i, amenity in enumerate(amenities):
                with amenity_cols[i % 2]:
                    st.markdown(f"• {amenity}")

        # HOA website link
        if hoa_website:
            st.markdown(f"🔗 [Visit HOA Website]({hoa_website})")

        # Fee notes if available
        fee_includes = community_ctx.get('fee_includes', [])
        if fee_includes:
            with st.expander("What's included in HOA fees"):
                for item in fee_includes:
                    st.markdown(f"• {item}")

    else:
        # Community not found - graceful fallback
        subdivision_display = community_ctx.get('display_name') or subdivision
        st.markdown(f"### {subdivision_display}")

        col1, col2 = st.columns(2)

        with col1:
            if hoa_fee:
                st.metric("Monthly HOA Fee", f"${hoa_fee:,.0f}")
                st.caption("Source: RentCast API")
            else:
                st.metric("Monthly HOA Fee", "Unknown")

        with col2:
            st.metric("Community Data", "Not Available")

        st.info("ℹ️ Community details not available for this subdivision. "
                "HOA fee shown is from property records.")

    st.markdown("---")


# =============================================================================
# SECTION: DEVELOPMENT & INFRASTRUCTURE
# =============================================================================

def display_cell_towers_section(lat: float, lon: float):
    """Display cell tower coverage for a Fairfax County property."""
    st.markdown("## 📡 Cell Tower Coverage")

    try:
        from core.fairfax_cell_towers_analysis import FairfaxCellTowersAnalysis
        analyzer = FairfaxCellTowersAnalysis()
        coverage = analyzer.calculate_coverage_score(lat, lon)

        if not coverage:
            st.info("Cell tower data not available for this location.")
            return

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Coverage Score", f"{coverage.get('score', 0)}/100")
        with col2:
            st.metric("Rating", coverage.get('rating', 'N/A'))
        with col3:
            st.metric("Towers Within 2 mi", coverage.get('towers_within_2mi', 0))

        # Nearest tower
        nearest = coverage.get('nearest_tower_miles')
        if nearest:
            st.markdown(f"**Nearest tower:** {nearest:.2f} mi ({nearest * 5280:,.0f} ft)")

        # Nearby towers table
        nearby = analyzer.get_towers_near_point(lat, lon, radius_miles=2.0)
        if nearby is not None and len(nearby) > 0:
            with st.expander(f"View All Nearby Towers ({len(nearby)} within 2 mi)", expanded=False):
                display_df = nearby[['structure_type_desc', 'distance_miles', 'height_feet', 'city']].copy()
                display_df.columns = ['Type', 'Distance (mi)', 'Height (ft)', 'City']
                display_df['Distance (mi)'] = display_df['Distance (mi)'].apply(lambda x: f"{x:.2f}")
                display_df['Height (ft)'] = display_df['Height (ft)'].apply(
                    lambda x: f"{x:.0f}" if pd.notna(x) and x > 0 else "—"
                )

                st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.caption(f"📶 Source: FCC Antenna Structure Registration, Fairfax County")

    except Exception as e:
        st.warning(f"Cell tower analysis unavailable: {e}")


def analyze_development(lat: float, lon: float, radius_miles: float = 2.0) -> Dict[str, Any]:
    """Analyze development pressure and nearby permits."""
    permits_df = load_permits_data()

    if permits_df.empty:
        return {'error': 'Could not load permits data'}

    # Calculate distances
    permits_df['distance'] = permits_df.apply(
        lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']),
        axis=1
    )

    # Filter to radius
    nearby = permits_df[permits_df['distance'] <= radius_miles].copy()

    # Calculate metrics
    total_value = nearby['Estimated Construction Cost'].sum()
    datacenter_count = len(nearby[nearby['is_datacenter'] == True])
    fiber_count = len(nearby[nearby['is_fiber'] == True])
    infra_count = len(nearby[nearby['is_infrastructure'] == True])

    # Recent permits (last 6 months)
    try:
        nearby['issue_date'] = pd.to_datetime(nearby['Permit Issue Date'], errors='coerce')
        six_months_ago = datetime.now() - pd.Timedelta(days=180)
        recent = nearby[nearby['issue_date'] >= six_months_ago]
        recent_count = len(recent)
    except:
        recent_count = 0

    return {
        'nearby_permits': nearby,
        'total_permits': len(nearby),
        'total_value': total_value,
        'datacenter_count': datacenter_count,
        'fiber_count': fiber_count,
        'infrastructure_count': infra_count,
        'recent_count': recent_count
    }


def get_marker_radius(value: float, is_datacenter: bool) -> int:
    """Scale marker radius by permit value."""
    if is_datacenter or value >= 10_000_000:  # Data centers or >$10M
        return 12
    elif value >= 5_000_000:  # $5M-$10M
        return 9
    elif value >= 1_000_000:  # $1M-$5M
        return 6
    else:
        return 4  # Fallback


def create_development_map(lat: float, lon: float, nearby_permits: pd.DataFrame) -> folium.Map:
    """Create Folium map with development activity and overlay layers."""
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles=None)
    folium.TileLayer('cartodbpositron', control=False).add_to(m)

    # Property marker
    folium.Marker(
        [lat, lon],
        popup="<b>Your Property</b>",
        icon=folium.Icon(color='blue', icon='home', prefix='fa'),
        tooltip="Subject Property"
    ).add_to(m)

    # 2-mile radius circle
    folium.Circle(
        [lat, lon],
        radius=3218,  # 2 miles in meters
        color='#3388ff',
        fill=False,
        weight=2,
        opacity=0.5,
        tooltip="2-mile radius"
    ).add_to(m)

    # === PERMIT MARKERS (Option 3: Data centers + >$1M) ===
    permits_layer = folium.FeatureGroup(name='🏗️ Major Development (>$1M)')

    value_col = 'Estimated Construction Cost'
    df = nearby_permits.copy()
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce').fillna(0)

    # Filter: data centers OR value >= $1M
    significant_permits = df[
        (df['is_datacenter'] == True) |
        (df[value_col] >= 1_000_000)
    ]

    for _, permit in significant_permits.iterrows():
        # Color by type
        if permit.get('is_datacenter'):
            color = 'red'
        elif permit.get('is_fiber'):
            color = 'orange'
        elif permit.get('is_infrastructure'):
            color = 'purple'
        else:
            color = 'green'

        cost = permit.get(value_col, 0)
        desc = str(permit.get('Permit Description', 'N/A'))[:100]

        # Value-scaled radius
        radius = get_marker_radius(cost, permit.get('is_datacenter', False))

        popup_html = f"""
        <b>{permit.get('Address', 'N/A')}</b><br>
        <b>Cost:</b> ${cost:,.0f}<br>
        <b>Type:</b> {permit.get('Permit Work Class', 'N/A')}<br>
        <b>Description:</b> {desc}...
        """

        folium.CircleMarker(
            location=[permit['Latitude'], permit['Longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.6,
            weight=1
        ).add_to(permits_layer)

    permits_layer.add_to(m)

    # === POWER LINES LAYER ===
    power_layer = folium.FeatureGroup(name='⚡ Power Lines')

    try:
        power_lines_path = os.path.join(DATA_DIR, 'utilities', 'Major_Power_Lines.geojson')
        with open(power_lines_path) as f:
            power_data = json.load(f)

        for feature in power_data['features']:
            coords = feature['geometry']['coordinates']
            # GeoJSON is [lon, lat], Folium wants [lat, lon]
            line_coords = [[c[1], c[0]] for c in coords]

            voltage = feature['properties'].get('MA_VOLTAGE', 'Unknown')

            folium.PolyLine(
                line_coords,
                weight=2,
                color='#FFA500',
                opacity=0.7,
                popup=f"Transmission Line: {voltage}kV",
            ).add_to(power_layer)
    except Exception as e:
        pass  # Silently skip if power lines data unavailable

    power_layer.add_to(m)

    # === METRO STATIONS LAYER ===
    metro_layer = folium.FeatureGroup(name='🚇 Metro Stations')

    metro_stations = [
        {"name": "Ashburn", "lat": 39.0057, "lon": -77.4910},
        {"name": "Loudoun Gateway", "lat": 38.9556, "lon": -77.4377},
        {"name": "Innovation Center", "lat": 38.9614, "lon": -77.4143},
        {"name": "Dulles Airport", "lat": 38.9531, "lon": -77.4483},
    ]

    for station in metro_stations:
        folium.Marker(
            [station['lat'], station['lon']],
            popup=f"🚇 {station['name']} Station (Silver Line)",
            icon=folium.Icon(color='darkblue', icon='train', prefix='fa'),
            tooltip=f"{station['name']} Metro"
        ).add_to(metro_layer)

    # Metro track line (simplified connection)
    track_coords = [[s['lat'], s['lon']] for s in metro_stations]
    folium.PolyLine(
        track_coords,
        weight=4,
        color='#003DA5',
        opacity=0.8,
        dash_array='10',
        popup='Silver Line Metro',
        tooltip='Silver Line'
    ).add_to(metro_layer)

    metro_layer.add_to(m)

    # === SCHOOLS LAYER ===
    school_layer = folium.FeatureGroup(name='🏫 Schools')

    try:
        schools_path = os.path.join(DATA_DIR, 'loudoun_school_coordinates.csv')
        schools_df = pd.read_csv(schools_path)

        for _, school in schools_df.iterrows():
            slat = school.get('Latitude', 0)
            slon = school.get('Longitude', 0)
            name = school.get('School_Name', 'School')
            school_type = school.get('School_Type', '')

            # Only show schools within 2.5 mile radius
            if haversine_distance(lat, lon, slat, slon) <= 2.5:
                # Color by school type, all use graduation-cap icon
                if 'Elem' in str(school_type):
                    icon_color = 'green'
                elif 'Middle' in str(school_type):
                    icon_color = 'orange'
                elif 'High' in str(school_type):
                    icon_color = 'red'
                else:
                    icon_color = 'gray'

                folium.Marker(
                    [slat, slon],
                    popup=f"🏫 {name}",
                    icon=folium.Icon(color=icon_color, icon='graduation-cap', prefix='fa'),
                    tooltip=name
                ).add_to(school_layer)
    except Exception as e:
        pass  # Silently skip if schools data unavailable

    school_layer.add_to(m)

    # === MASTER-PLANNED COMMUNITIES LAYER ===
    communities_layer = folium.FeatureGroup(name='🏘️ Master-Planned Communities')

    try:
        from core.loudoun_community_lookup import CommunityLookup
        lookup = CommunityLookup()

        for comm_key in lookup.list_communities():
            comm_data = lookup.get_community_by_key(comm_key)
            summary = lookup.get_community_summary(comm_key)

            if comm_data and 'latitude' in comm_data and 'longitude' in comm_data:
                clat = comm_data['latitude']
                clon = comm_data['longitude']
                name = summary.get('display_name', comm_key) if summary else comm_key
                homes = summary.get('total_homes', 0) if summary else 0
                gated = summary.get('gated', False) if summary else False
                hoa = summary.get('monthly_fee', 0) if summary else 0

                # Calculate distance to property
                dist = haversine_distance(lat, lon, clat, clon)

                # Build popup
                popup_parts = [f"<b>🏘️ {name}</b>"]
                if homes:
                    popup_parts.append(f"<br>{homes:,} homes")
                if gated:
                    popup_parts.append(" • Gated")
                if hoa:
                    popup_parts.append(f"<br>HOA: ${hoa:.0f}/mo")
                popup_parts.append(f"<br><i>{dist:.1f} mi from property</i>")
                popup_html = "".join(popup_parts)

                folium.Marker(
                    [clat, clon],
                    popup=folium.Popup(popup_html, max_width=200),
                    icon=folium.Icon(color='cadetblue', icon='home', prefix='fa'),
                    tooltip=f"{name} ({dist:.1f} mi)"
                ).add_to(communities_layer)
    except Exception:
        pass  # Silently skip if community data unavailable

    communities_layer.add_to(m)

    # === CELL TOWERS LAYER ===
    # Only show major towers (>= 150 ft) to reduce visual clutter
    towers_layer = folium.FeatureGroup(name='📡 Cell Towers')

    try:
        towers_df = load_cell_towers()
        if not towers_df.empty:
            for _, tower in towers_df.iterrows():
                tlat = tower.get('latitude', 0)
                tlon = tower.get('longitude', 0)
                height = tower.get('height_ft', 0)

                # Filter: only major towers (>= 150 ft) within 3 mile radius
                if height and height >= 150 and haversine_distance(lat, lon, tlat, tlon) <= 3.0:
                    tower_name = tower.get('tower_name', 'Unknown Tower')
                    structure = tower.get('structure_type', 'Unknown')
                    dist = haversine_distance(lat, lon, tlat, tlon)

                    # Build popup HTML - simplified
                    popup_parts = [f"<b>📡 {tower_name}</b>"]
                    popup_parts.append(f"<br>Type: {structure}")
                    popup_parts.append(f"<br>Height: {height:.0f} ft")
                    popup_parts.append(f"<br><b>{dist:.2f} mi from property</b>")
                    popup_html = "".join(popup_parts)

                    folium.Marker(
                        [tlat, tlon],
                        popup=folium.Popup(popup_html, max_width=250),
                        icon=folium.Icon(color='blue', icon='signal', prefix='fa'),
                        tooltip=f"{tower_name} ({dist:.2f} mi)"
                    ).add_to(towers_layer)
    except Exception:
        pass  # Silently skip if cell tower data unavailable

    towers_layer.add_to(m)

    # === HOSPITALS LAYER ===
    hospitals_layer = folium.FeatureGroup(name='🏥 Hospitals')

    # CMS-rated hospitals (hardcoded for reliability - these rarely change)
    cms_hospitals = [
        {
            "name": "Inova Loudoun Hospital",
            "lat": 39.073917871721612,
            "lon": -77.478042919767631,
            "cms_rating": 5,
            "phone": "(703) 858-6600",
            "address": "44045 Riverside Pkwy, Leesburg, VA 20176"
        },
        {
            "name": "StoneSprings Hospital Center",
            "lat": 38.9404382,
            "lon": -77.5424483,
            "cms_rating": 3,
            "phone": "(571) 349-4000",
            "address": "24440 Stone Springs Blvd, Dulles, VA 20166"
        }
    ]

    for hospital in cms_hospitals:
        stars = '⭐' * hospital['cms_rating']
        popup_html = f"""
        <b>🏥 {hospital['name']}</b><br>
        <b>CMS Rating:</b> {stars}<br>
        <b>Phone:</b> {hospital['phone']}<br>
        {hospital['address']}
        """
        folium.Marker(
            [hospital['lat'], hospital['lon']],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color='orange', icon='plus-sign', prefix='glyphicon'),
            tooltip=f"{hospital['name']} ({stars})"
        ).add_to(hospitals_layer)

    hospitals_layer.add_to(m)

    # === LAYER CONTROL ===
    folium.LayerControl(collapsed=False).add_to(m)

    # === LEGEND ===
    legend_html = '''
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
         background: white; padding: 10px; border-radius: 5px; border: 2px solid gray;
         font-size: 12px; font-family: Arial, sans-serif;">
        <b>Development Activity</b><br>
        <i style="background:red; width:12px; height:12px; border-radius:50%; display:inline-block;"></i> Data Center<br>
        <i style="background:orange; width:10px; height:10px; border-radius:50%; display:inline-block;"></i> Fiber/Telecom<br>
        <i style="background:purple; width:8px; height:8px; border-radius:50%; display:inline-block;"></i> Infrastructure<br>
        <i style="background:green; width:6px; height:6px; border-radius:50%; display:inline-block;"></i> Commercial >$1M<br>
        <hr style="margin: 5px 0;">
        <b>Schools</b><br>
        <i class="fa fa-graduation-cap" style="color:#72AF26;"></i> Elementary<br>
        <i class="fa fa-graduation-cap" style="color:#F69730;"></i> Middle<br>
        <i class="fa fa-graduation-cap" style="color:#D63E2A;"></i> High<br>
        <hr style="margin: 5px 0;">
        <i class="fa fa-home" style="color:#436978;"></i> Master-Planned Community<br>
        <span style="color:#FFA500;">━━</span> Power Lines<br>
        <span style="color:#003DA5;">┅┅</span> Silver Line Metro<br>
        <hr style="margin: 5px 0;">
        <i class="fa fa-signal" style="color:#0066CC;"></i> Cell Towers (150+ ft)<br>
        <i class="fa fa-plus-square" style="color:#F69730;"></i> Hospitals (CMS Rated)
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# =============================================================================
# MATERNITY CARE / HEALTHCARE FUNCTIONS
# =============================================================================

def load_maternity_hospitals() -> Dict[str, Any]:
    """Load maternity hospitals data from JSON file."""
    json_path = os.path.join(HEALTHCARE_DIR, 'maternity_hospitals.json')
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'hospitals': [], 'error': 'Maternity hospitals data file not found'}
    except json.JSONDecodeError:
        return {'hospitals': [], 'error': 'Invalid JSON in maternity hospitals file'}


def get_nicu_level_description(level: str) -> str:
    """Get plain-English description for NICU level."""
    descriptions = {
        'I': 'Basic nursery for healthy full-term babies',
        'II': 'Special care for babies 32+ weeks with moderate issues',
        'III': 'Full NICU for premature/seriously ill babies',
        'IV': 'Regional center with surgery & highest-risk care'
    }
    return descriptions.get(level, 'Unknown')


def get_csection_status(rate: float) -> Tuple[str, str]:
    """
    Return color and status for C-section rate.
    Leapfrog standard: 23.6% or less
    """
    if rate <= 0.236:
        return 'green', 'Meets Standard'
    elif rate <= 0.28:
        return 'orange', 'Slightly Above'
    else:
        return 'red', 'Above Standard'


def format_star_rating(rating: int) -> str:
    """Format CMS star rating as emoji stars."""
    if not rating or rating < 1:
        return 'N/A'
    return '⭐' * rating


def load_healthcare_facilities() -> List[Dict[str, Any]]:
    """
    Load hospitals and urgent care facilities from GeoJSON file.

    Returns list of facilities with parsed properties and coordinates.
    """
    geojson_path = os.path.join(HEALTHCARE_DIR, 'Loudoun_Hospitals_and_Urgent_Care (1).geojson')
    try:
        with open(geojson_path, 'r') as f:
            data = json.load(f)

        facilities = []
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])

            facilities.append({
                'name': props.get('FACILITY_NAME', 'Unknown'),
                'type': props.get('FACILITY', 'U'),  # H=Hospital, U=Urgent Care
                'address': props.get('Address', ''),
                'longitude': coords[0],
                'latitude': coords[1],
                'phone': props.get('Phone', ''),
                'cms_rating': props.get('CMS_Rating'),
                'hospital_type': props.get('Hospital_Type', ''),
                'beds': props.get('Beds'),
                'health_system': props.get('Health_System', ''),
                'emergency_services': props.get('Emergency_Services', False)
            })
        return facilities
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def display_hospitals_subsection(facilities: List[Dict[str, Any]], lat: float, lon: float):
    """Display hospitals and emergency centers subsection."""
    st.markdown("### 🏥 Hospitals & Medical Facilities")

    # Filter to hospitals only (type='H')
    hospitals = [f for f in facilities if f.get('type') == 'H']

    if not hospitals:
        st.info("No hospital data available.")
        return

    # Calculate distances
    for h in hospitals:
        h['distance_miles'] = haversine_distance(lat, lon, h['latitude'], h['longitude'])

    # Separate CMS-rated hospitals from others
    cms_rated = [h for h in hospitals if h.get('cms_rating')]
    other_facilities = [h for h in hospitals if not h.get('cms_rating')]

    # Sort each group by distance
    cms_rated_sorted = sorted(cms_rated, key=lambda x: x['distance_miles'])
    other_sorted = sorted(other_facilities, key=lambda x: x['distance_miles'])

    # Display CMS-rated hospitals first with enhanced format
    if cms_rated_sorted:
        st.markdown("**Acute Care Hospitals** (CMS Rated)")
        for h in cms_rated_sorted:
            dist = h['distance_miles']
            name = h['name']
            cms_rating = h.get('cms_rating', 0)
            phone = h.get('phone', '')
            stars = '⭐' * cms_rating if cms_rating else 'N/A'

            # Format: Name — distance | stars | phone
            display_line = f"**{name}** — {dist:.1f} mi | {stars}"
            if phone:
                display_line += f" | {phone}"
            st.markdown(display_line)

            # Second line: Health system, beds, emergency services
            details_parts = []
            if h.get('health_system'):
                details_parts.append(h['health_system'])
            if h.get('beds'):
                details_parts.append(f"{h['beds']} beds")
            if h.get('emergency_services'):
                details_parts.append("Emergency Services")
            if details_parts:
                st.markdown(" • ".join(details_parts))

            st.caption(h['address'])
        st.markdown("---")

    # Display other facilities (ERs, rehab, behavioral, etc.)
    if other_sorted:
        st.markdown(f"**Emergency & Other Medical Facilities** ({len(other_sorted)})")

        # Show nearest facility directly
        nearest = other_sorted[0]
        st.markdown(f"**{nearest['name']}** — {nearest['distance_miles']:.1f} mi")
        st.caption(nearest['address'])

        # Put remaining in expander
        if len(other_sorted) > 1:
            remaining = other_sorted[1:]
            with st.expander(f"View all {len(remaining)} other facilities"):
                for h in remaining:
                    st.markdown(f"**{h['name']}** — {h['distance_miles']:.1f} mi")
                    st.caption(h['address'])
        st.markdown("---")


def display_urgent_care_subsection(facilities: List[Dict[str, Any]], lat: float, lon: float):
    """Display urgent care centers subsection."""
    st.markdown("### 🩺 Urgent Care Centers")

    # Filter to urgent care only (type='U')
    urgent_care = [f for f in facilities if f.get('type') == 'U']

    if not urgent_care:
        st.info("No urgent care data available.")
        return

    # Calculate distances
    for uc in urgent_care:
        uc['distance_miles'] = haversine_distance(lat, lon, uc['latitude'], uc['longitude'])

    urgent_care_sorted = sorted(urgent_care, key=lambda x: x['distance_miles'])

    # Show count and nearest 2
    nearest_2 = urgent_care_sorted[:2]

    st.markdown(f"**{len(urgent_care)} urgent care centers** in Loudoun County")
    st.markdown(f"*Showing {len(nearest_2)} nearest:*")

    for uc in nearest_2:
        dist = uc['distance_miles']
        name = uc['name']
        address = uc['address']
        st.markdown(f"• **{name}** — {dist:.1f} mi")
        st.caption(f"  {address}")

    # Expandable list for all
    if len(urgent_care_sorted) > 2:
        remaining_count = len(urgent_care_sorted) - 2
        with st.expander(f"View all {remaining_count} other urgent care centers"):
            for uc in urgent_care_sorted[2:]:
                dist = uc['distance_miles']
                st.markdown(f"• **{uc['name']}** — {dist:.1f} mi ({uc['address']})")


def display_pharmacies_subsection(pharmacies: list):
    """Display nearby pharmacies from Google Places API."""
    st.markdown("### 💊 Pharmacies")

    if not pharmacies:
        st.info("No pharmacies found within 5 miles")
        return

    # Show count
    st.markdown(f"**{len(pharmacies)} pharmacies** within 5 miles")

    # Highlight 24-hour pharmacies if any
    pharmacies_24hr = [p for p in pharmacies if p.get('is_24_hour')]
    if pharmacies_24hr:
        st.markdown("**🌙 24-Hour Pharmacies:**")
        for p in pharmacies_24hr[:3]:
            rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
            st.markdown(f"• **{p['name']}** — {p['distance_miles']:.1f} mi {rating}")
            st.caption(p['address'])

    # Show 2 nearest (excluding 24-hour already shown)
    shown_names = {p['name'] for p in pharmacies_24hr[:3]}
    regular = [p for p in pharmacies if p['name'] not in shown_names][:2]
    if regular:
        if pharmacies_24hr:
            st.markdown("**Other Nearby Pharmacies:**")
        else:
            st.markdown("**Nearest Pharmacies:**")
        for p in regular:
            rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
            st.markdown(f"• **{p['name']}** — {p['distance_miles']:.1f} mi {rating}")
            st.caption(p['address'])

    # Expander for remaining pharmacies
    total_shown = min(3, len(pharmacies_24hr)) + len(regular)
    if len(pharmacies) > total_shown:
        remaining = len(pharmacies) - total_shown
        with st.expander(f"View all {remaining} other pharmacies"):
            for p in pharmacies[total_shown:]:
                rating = f"⭐{p['rating']:.1f}" if p.get('rating') else ""
                st.markdown(f"• {p['name']} — {p['distance_miles']:.1f} mi {rating}")


def display_economic_indicators_section():
    """Display Economic Indicators section with LFPR, industry mix, and major employers."""
    import plotly.graph_objects as go
    import pandas as pd

    st.markdown("---")
    st.subheader("💼 Economic Indicators")

    # =========================================================================
    # SUMMARY METRICS (Always Visible)
    # =========================================================================

    lfpr_data = get_lfpr_data()
    bls_data = fetch_bls_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        lfpr = lfpr_data.get("fairfax")
        delta = f"+{lfpr_data.get('fairfax_vs_usa')} vs USA" if lfpr_data.get('fairfax_vs_usa') else None
        st.metric(
            label="Labor Force Participation",
            value=f"{lfpr:.1f}%" if lfpr else "N/A",
            delta=delta
        )

    with col2:
        unemp = bls_data.get("unemployment_rate", {})
        unemp_value = unemp.get("value")
        unemp_date = unemp.get("date", "")

        st.metric(
            label="Unemployment Rate",
            value=f"{unemp_value:.1f}%" if unemp_value else "N/A"
        )
        if unemp_date:
            st.caption(f"As of {unemp_date}")

    with col3:
        lf = bls_data.get("labor_force", {})
        lf_value = lf.get("value")
        yoy = lf.get("yoy_change")
        delta_str = None
        if yoy is not None:
            delta_str = f"+{yoy:.1f}% YoY" if yoy > 0 else f"{yoy:.1f}% YoY"
        st.metric(
            label="Labor Force",
            value=f"{lf_value:,.0f}" if lf_value else "N/A",
            delta=delta_str
        )

    st.caption("Sources: Census ACS 5-Year (LFPR) | BLS LAUS (Unemployment, Labor Force)")

    # =========================================================================
    # INDUSTRY EMPLOYMENT MIX (Expander)
    # =========================================================================

    with st.expander("📊 Industry Employment Mix"):
        industry_data = get_industry_mix_data()
        all_industries = industry_data.get("industries", [])
        industries = all_industries[:6]  # Top 6 sectors for chart

        # Use tabs instead of toggle to prevent expander collapse
        tab_chart, tab_table = st.tabs(["Top 6 Sectors", "All 13 Sectors"])

        with tab_chart:
            if industries:
                # Prepare data for grouped horizontal bar chart
                sectors = [ind["sector"] for ind in industries]
                fairfax_vals = [ind["fairfax"] or 0 for ind in industries]
                va_vals = [ind["virginia"] or 0 for ind in industries]
                usa_vals = [ind["usa"] or 0 for ind in industries]

                # Reverse for horizontal bars (top sector at top)
                sectors.reverse()
                fairfax_vals.reverse()
                va_vals.reverse()
                usa_vals.reverse()

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=fairfax_vals,
                    name='Fairfax Co.',
                    orientation='h',
                    marker_color='#1f77b4',
                    text=[f"{v:.1f}%" for v in fairfax_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=va_vals,
                    name='Virginia',
                    orientation='h',
                    marker_color='#ff7f0e',
                    text=[f"{v:.1f}%" for v in va_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.add_trace(go.Bar(
                    y=sectors,
                    x=usa_vals,
                    name='USA',
                    orientation='h',
                    marker_color='#2ca02c',
                    text=[f"{v:.1f}%" for v in usa_vals],
                    textposition='outside',
                    textfont=dict(size=14, color='black')
                ))

                fig.update_layout(
                    barmode='group',
                    height=350,
                    margin=dict(l=180, r=60, t=40, b=40),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5
                    ),
                    xaxis_title="% of Employment",
                    yaxis=dict(tickfont=dict(size=13)),
                    uniformtext=dict(mode='hide', minsize=14)
                )

                st.plotly_chart(fig, width='stretch')

        with tab_table:
            if all_industries:
                df = pd.DataFrame(all_industries)
                df.columns = ["Sector", "Fairfax Co. %", "Virginia %", "USA %"]
                # Format percentages
                df["Fairfax Co. %"] = df["Fairfax Co. %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                df["Virginia %"] = df["Virginia %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                df["USA %"] = df["USA %"].apply(lambda x: f"{x:.1f}%" if x else "N/A")
                st.dataframe(df, width='stretch', hide_index=True)

        st.caption(f"Source: {industry_data.get('source', 'Census ACS')}")

    # =========================================================================
    # MAJOR EMPLOYERS (Expander)
    # =========================================================================

    # PRE-LOAD employer data BEFORE expander for instant opening
    all_employers_data = load_major_employers()

    def format_employer_df(employers_list):
        """Format employer list into display DataFrame."""
        formatted = []
        for emp in employers_list:
            employees = emp.get("employees")
            employees_range = emp.get("employees_range", "")
            formatted.append({
                "Rank": emp.get("rank", 0),
                "Employer": emp.get("name", ""),
                "Employees": f"{employees:,}" if employees else employees_range,
                "% of Total": f"{emp.get('pct', 0):.2f}%",
                "Industry": _infer_employer_industry(emp.get("name", ""))
            })
        return pd.DataFrame(formatted)

    # PRE-CREATE all year DataFrames BEFORE expander for instant tab switching
    employer_year_dfs = {}
    for year in range(2008, 2026):
        year_data = all_employers_data.get("employers_by_year", {}).get(str(year), {})
        employers_list = year_data.get("employers", [])
        if employers_list:
            employer_year_dfs[year] = format_employer_df(employers_list)

    with st.expander("🏢 Major Employers"):
        # Trend highlights from ACFR data
        trends = get_employer_trends()
        fcps = trends.get("fcps_growth", {})
        inova = trends.get("inova_growth", {})

        if fcps.get("start_employees", 0) > 0:
            trend_parts = [
                f"📈 **Key Trends ({fcps.get('start_year', 2009)}-{fcps.get('end_year', 2025)}):** "
                f"FCPS {fcps.get('pct_change', 0):+.0f}% ({fcps.get('start_employees', 0):,} → {fcps.get('end_employees', 0):,})"
            ]
            if inova.get("start_employees", 0) > 0:
                trend_parts.append(
                    f"Inova Health {inova.get('pct_change', 0):+.0f}% ({inova.get('start_employees', 0):,} → {inova.get('end_employees', 0):,})"
                )
            trend_parts.append("Amazon entered top 10 in 2019")
            st.info(" | ".join(trend_parts))
        else:
            st.info("📈 **Major Employers:** Data loading from Fairfax County ACFR")

        # Year tabs
        tab_years = ["2025", "2024", "2023", "2022", "2021"]
        tabs = st.tabs(tab_years + ["Earlier"])

        for i, tab in enumerate(tabs[:-1]):  # All except "Earlier"
            year = int(tab_years[i])
            with tab:
                if year in employer_year_dfs:
                    st.dataframe(employer_year_dfs[year], width='stretch', hide_index=True)
                else:
                    st.write("Data not available for this year.")

        # "Earlier" tab — only show years that actually have data
        with tabs[-1]:
            earlier_years = sorted(
                [y for y in employer_year_dfs if y <= 2020],
                reverse=True,
            )
            if earlier_years:
                earlier_year = st.selectbox(
                    "Select year",
                    earlier_years,
                    key="fairfax_earlier_year_select",
                )
                st.dataframe(
                    employer_year_dfs[earlier_year],
                    width='stretch',
                    hide_index=True,
                )
            else:
                st.info("No earlier employer data available.")

        st.caption("Source: Fairfax County Annual Comprehensive Financial Reports (ACFR)")

    # =========================================================================
    # DATA SOURCES & METHODOLOGY (Expander)
    # =========================================================================

    with st.expander("📋 Data Sources & Methodology"):
        st.markdown("""
**Labor Force Participation Rate (LFPR)**
- Source: Census Bureau American Community Survey (ACS) 5-Year Estimates (2019-2023)
- Definition: Percentage of population 16+ that is in the labor force (employed or actively seeking work)
- Note: 5-Year estimates provide more stable data with lower margin of error than 1-Year estimates

**Unemployment Rate & Labor Force**
- Source: Bureau of Labor Statistics (BLS) Local Area Unemployment Statistics (LAUS)
- Frequency: Monthly (most recent available)
- Note: County-level data is not seasonally adjusted. Year-over-year comparisons are more reliable than month-over-month.

**Industry Employment Mix**
- Source: Census Bureau ACS 5-Year Estimates
- Shows percentage of employed residents by industry sector

**Major Employers**
- Source: Fairfax County Annual Comprehensive Financial Report (ACFR)
- Updated annually (fiscal year ending June 30)
- Employee counts may be ranges; percentages based on total county employment
        """)


def _infer_employer_industry(employer_name: str) -> str:
    """Infer industry category from employer name for display table."""
    name_lower = employer_name.lower()

    if "federal government" in name_lower:
        return "Federal Government"
    elif "school" in name_lower or "fcps" in name_lower:
        return "Education"
    elif "george mason" in name_lower or "university" in name_lower:
        return "Education"
    elif "fairfax county" in name_lower or "county of fairfax" in name_lower:
        return "Government"
    elif "inova" in name_lower or "health system" in name_lower or "hospital" in name_lower or "medical" in name_lower:
        return "Healthcare"
    elif "booz allen" in name_lower:
        return "Professional Services"
    elif "science applications" in name_lower or "saic" in name_lower or "leidos" in name_lower:
        return "Professional Services"
    elif "amazon" in name_lower:
        return "Technology"
    elif "computer science corporation" in name_lower or "mitre" in name_lower:
        return "Technology"
    elif "capital one" in name_lower or "navy federal" in name_lower:
        return "Financial Services"
    elif "federal home loan" in name_lower or "freddie mac" in name_lower:
        return "Financial Services"
    elif "general dynamics" in name_lower or "northrop" in name_lower or "lockheed" in name_lower:
        return "Defense"
    else:
        return "Other"


def display_medical_access_section(lat: float, lon: float):
    """Display healthcare access for a Fairfax County property."""
    st.markdown("## 🏥 Medical Access")

    try:
        from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
        analyzer = FairfaxHealthcareAnalysis()
        score = analyzer.calculate_healthcare_access_score(lat, lon)

        if not score:
            st.info("Healthcare data not available for this location.")
            return

        # Get all nearby facilities
        all_nearby = analyzer.get_facilities_near_point(lat, lon, radius_miles=10.0)
        hospitals = all_nearby[all_nearby['facility_type'] == 'hospital'].copy()
        urgent_care_nearby = analyzer.get_facilities_near_point(lat, lon, radius_miles=3.0)
        urgent_care = urgent_care_nearby[urgent_care_nearby['facility_type'] == 'urgent_care'].copy()

        # Summary metrics
        breakdown = score.get('breakdown', {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Access Score", f"{score.get('score', 0)}/100")
            st.caption(score.get('rating', ''))
        with col2:
            st.metric("Hospitals/ER", len(hospitals))
        with col3:
            st.metric("Urgent Care (3 mi)", len(urgent_care))
        with col4:
            nearest_dist = breakdown.get('nearest_hospital', {}).get('distance_miles')
            st.metric("Nearest Hospital", f"{nearest_dist:.1f} mi" if nearest_dist else "N/A")

        st.markdown("---")

        # ── Hospitals & Emergency subsection ──
        st.markdown("### 🏥 Hospitals & Emergency")

        # Split CMS-rated hospitals from others
        cms_hospitals = hospitals[hospitals['cms_rating'].notna()].copy()
        other_facilities = hospitals[hospitals['cms_rating'].isna()].copy()

        if len(cms_hospitals) > 0:
            for _, h in cms_hospitals.iterrows():
                name = h['name']
                dist = h['distance_miles']
                cms = h.get('cms_rating')
                leap = h.get('leapfrog_grade')
                address = h.get('address', '')
                city = h.get('city', '')
                phone = h.get('phone', '')
                emergency = h.get('emergency_services')
                htype = h.get('hospital_type', '')
                leap_notes = h.get('leapfrog_notes', '')

                # Build star display
                stars = ''
                if cms and not pd.isna(cms):
                    stars = '⭐' * int(float(cms))

                # Leapfrog badge
                leap_badge = ''
                if leap and str(leap) != 'nan':
                    leap_badge = f" | Safety: **{leap}**"

                emergency_badge = " | 🚨 ER" if emergency == 'Yes' else ""

                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                    with col1:
                        st.markdown(f"**{name}**")
                        st.caption(f"📍 {address}, {city}" if address else htype or '')

                    with col2:
                        if stars:
                            st.markdown(f"{stars} ({int(float(cms))}/5)")
                        else:
                            st.markdown("Not rated")

                    with col3:
                        if leap and str(leap) != 'nan':
                            st.markdown(f"Safety: **{leap}**")
                            if leap_notes and str(leap_notes) != 'nan':
                                st.caption(leap_notes)
                        else:
                            st.markdown("—")

                    with col4:
                        st.markdown(f"**{dist:.1f} mi**")
                        if emergency == 'Yes':
                            st.caption("🚨 ER")

                    st.divider()

        if len(other_facilities) > 0:
            with st.expander(f"View {len(other_facilities)} Other Facilities (ERs, Specialty)", expanded=False):
                for _, h in other_facilities.iterrows():
                    name = h['name']
                    dist = h['distance_miles']
                    htype = h.get('hospital_type', '')
                    address = h.get('address', '')
                    city = h.get('city', '')
                    label = htype if htype and str(htype) != 'nan' else 'Facility'
                    st.markdown(f"**{name}** — {dist:.1f} mi")
                    st.caption(f"{label} | {address}, {city}" if address else label)

        # ── Urgent Care subsection ──
        st.markdown("### 🩺 Urgent Care Centers")

        if len(urgent_care) > 0:
            # Show 3 nearest directly
            top_uc = urgent_care.head(3)
            for _, uc in top_uc.iterrows():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{uc['name']}**")
                    addr = uc.get('address', '')
                    city = uc.get('city', '')
                    st.caption(f"📍 {addr}, {city}" if addr else '')
                with col2:
                    st.markdown(f"**{uc['distance_miles']:.1f} mi**")

            # Rest in expander
            if len(urgent_care) > 3:
                remaining = urgent_care.iloc[3:]
                with st.expander(f"View {len(remaining)} More Urgent Care Centers"):
                    uc_display = remaining[['name', 'address', 'city', 'distance_miles']].copy()
                    uc_display['distance_miles'] = uc_display['distance_miles'].round(2)
                    uc_display.columns = ['Name', 'Address', 'City', 'Distance (mi)']
                    st.dataframe(uc_display, use_container_width=True, hide_index=True)
        else:
            st.info("No urgent care centers found within 3 miles.")

        st.caption("Source: Fairfax County GIS, CMS Hospital Compare, Leapfrog Group")

    except Exception as e:
        st.warning(f"Medical access analysis unavailable: {e}")


def _display_maternity_content(lat: float, lon: float):
    """
    Internal function for maternity content display.
    Called from within display_medical_access_section.
    """
    # Load data
    data = load_maternity_hospitals()

    if 'error' in data:
        st.info(f"Maternity hospital data not available: {data['error']}")
        return

    hospitals = data.get('hospitals', [])
    if not hospitals:
        st.info("No maternity hospital data available.")
        return

    # Calculate distances and sort
    for hospital in hospitals:
        coords = hospital.get('coordinates', {})
        h_lat = coords.get('latitude', 0)
        h_lon = coords.get('longitude', 0)
        hospital['distance_miles'] = haversine_distance(lat, lon, h_lat, h_lon)

    hospitals_sorted = sorted(hospitals, key=lambda x: x['distance_miles'])

    # Summary at top
    loudoun_hospitals = [h for h in hospitals_sorted if h.get('in_loudoun_county')]
    nearby_hospitals = [h for h in hospitals_sorted if not h.get('in_loudoun_county')]

    st.markdown(f"""
**{len(loudoun_hospitals)} birthing hospitals in Loudoun County** and **{len(nearby_hospitals)} nearby in Fairfax County**.
All hospitals shown have labor & delivery units, NICUs, and are rated by CMS and Leapfrog for safety.
    """)

    # Display each hospital
    for hospital in hospitals_sorted:
        maternity = hospital.get('maternity', {})
        quality = hospital.get('quality', {})

        distance = hospital['distance_miles']
        name = hospital.get('name', 'Unknown Hospital')
        county_badge = "📍 Loudoun" if hospital.get('in_loudoun_county') else "📍 Fairfax"

        stars = format_star_rating(quality.get('cms_overall_rating'))
        safety_grade = quality.get('leapfrog_safety_grade', 'N/A')

        with st.expander(f"**{name}** — {distance:.1f} mi | {stars} | Safety: {safety_grade}", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Distance", f"{distance:.1f} mi")
                st.caption(county_badge)

            with col2:
                cms_rating = quality.get('cms_overall_rating')
                st.metric("CMS Rating", format_star_rating(cms_rating))
                if quality.get('leapfrog_top_hospital'):
                    st.caption("🏆 Top Hospital")

            with col3:
                st.metric("Safety Grade", safety_grade)
                consecutive = quality.get('leapfrog_consecutive_a_grades')
                if consecutive:
                    st.caption(f"{consecutive} consecutive A's")

            with col4:
                nicu_level = maternity.get('nicu_level', 'N/A')
                st.metric("NICU Level", nicu_level)
                st.caption(get_nicu_level_description(nicu_level))

            st.markdown("---")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Delivery Statistics**")
                births = maternity.get('live_births_annual', 0)
                st.markdown(f"• Births/year: **{births:,}**")

                csection_rate = maternity.get('c_section_rate', 0)
                csection_pct = csection_rate * 100
                color, status = get_csection_status(csection_rate)

                if color == 'green':
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** ✅")
                elif color == 'orange':
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** ⚠️")
                else:
                    st.markdown(f"• C-section rate: **{csection_pct:.1f}%** 🔴")

                st.caption(f"Leapfrog standard: ≤23.6%")

                episiotomy_rate = maternity.get('episiotomy_rate', 0)
                st.markdown(f"• Episiotomy rate: **{episiotomy_rate * 100:.1f}%**")

            with col2:
                st.markdown("**Key Services**")

                if maternity.get('midwives_available'):
                    st.markdown("✅ Certified Nurse-Midwives")
                else:
                    st.markdown("❌ No midwives on staff")

                if maternity.get('vbac_offered'):
                    st.markdown("✅ VBAC (vaginal birth after C-section)")
                else:
                    st.markdown("❌ VBAC not offered")

                lactation = maternity.get('lactation_services', '')
                if lactation == 'hospital_and_outpatient':
                    st.markdown("✅ Lactation support (hospital & outpatient)")
                elif lactation == 'hospital_only':
                    st.markdown("✅ Lactation support (hospital only)")
                else:
                    st.markdown("❌ No lactation services listed")

                if maternity.get('doulas_allowed'):
                    st.markdown("✅ Doulas welcome")

            with col3:
                st.markdown("**Hospital Info**")
                st.markdown(f"• {hospital.get('health_system', 'N/A')}")
                st.markdown(f"• {hospital.get('address', '')}")
                st.markdown(f"• {hospital.get('city', '')}, {hospital.get('state', '')} {hospital.get('zip', '')}")

                if quality.get('magnet_status'):
                    st.markdown("🏅 **Magnet® Recognized** (nursing excellence)")

                if maternity.get('birthing_friendly_cms'):
                    st.markdown("👶 **CMS Birthing-Friendly** designated")

            top_years = quality.get('leapfrog_top_hospital_years', [])
            if top_years:
                years_str = ', '.join(str(y) for y in top_years)
                st.caption(f"🏆 Leapfrog Top Hospital: {years_str}")

    # NICU Level reference
    with st.expander("ℹ️ Understanding NICU Levels", expanded=False):
        st.markdown("""
| Level | Description | Capabilities |
|-------|-------------|--------------|
| **I** | Well-baby nursery | Healthy, full-term babies (35+ weeks) |
| **II** | Special care nursery | Babies 32+ weeks, moderate issues, expected quick recovery |
| **III** | Full NICU | Babies under 32 weeks or 3.3 lbs, serious illness, subspecialty care |
| **IV** | Regional NICU | All Level III + complex surgery, ECMO, regional referral center |

*Inova Fairfax Hospital has Northern Virginia's only Level IV NICU for the highest-risk cases.*
        """)

    # C-section rate context
    with st.expander("ℹ️ Understanding C-Section Rates", expanded=False):
        st.markdown("""
**What the C-section rate measures:**
The rate shown is for first-time mothers with a single baby in head-down position at full term
(NTSV: Nulliparous, Term, Singleton, Vertex). This is the standard comparison metric.

**Leapfrog standard: 23.6% or less**
- ✅ **Green** = Meets or exceeds the standard
- ⚠️ **Yellow** = Slightly above (23.7% - 28%)
- 🔴 **Red** = Significantly above standard (>28%)

Lower rates generally indicate fewer unnecessary C-sections, but individual medical circumstances vary.
        """)


# =============================================================================
# SECTION: DEVELOPMENT ACTIVITY & BUILDING PERMITS
# =============================================================================


def _create_permits_map_plotly(permits_df, property_lat: float, property_lon: float):
    """Create Plotly scatter_mapbox of recent permits, color-coded by category.

    Colors:
        Green:  Residential New Construction
        Blue:   Commercial New Construction
        Orange: Residential Renovation
        Gray:   Commercial Renovation
    """
    if not PLOTLY_AVAILABLE or permits_df.empty:
        return None

    color_map = {
        'residential_new': '#22c55e',
        'commercial_new': '#3b82f6',
        'residential_renovation': '#f97316',
        'commercial_renovation': '#6b7280',
    }

    label_map = {
        'residential_new': 'Residential New',
        'commercial_new': 'Commercial New',
        'residential_renovation': 'Residential Reno',
        'commercial_renovation': 'Commercial Reno',
    }

    # Prepare display data — all calculations before rendering
    map_df = permits_df.copy()
    map_df['category_label'] = map_df['permit_category'].map(label_map).fillna('Other')
    map_df['display_date'] = map_df['issued_date'].apply(
        lambda d: d.strftime('%Y-%m-%d') if pd.notna(d) else 'N/A'
    )
    map_df['display_address'] = map_df['address'].fillna('Address not available')
    map_df['display_type'] = map_df['permit_type'].fillna('Unknown')

    # Build figure
    fig = px.scatter_mapbox(
        map_df,
        lat='centroid_lat',
        lon='centroid_lon',
        color='category_label',
        color_discrete_map={
            'Residential New': '#22c55e',
            'Commercial New': '#3b82f6',
            'Residential Reno': '#f97316',
            'Commercial Reno': '#6b7280',
            'Other': '#9ca3af',
        },
        hover_data={
            'display_type': True,
            'display_date': True,
            'display_address': True,
            'centroid_lat': False,
            'centroid_lon': False,
            'category_label': False,
        },
        labels={
            'display_type': 'Permit Type',
            'display_date': 'Issued',
            'display_address': 'Address',
            'category_label': 'Category',
        },
        zoom=12,
        height=500,
        mapbox_style='open-street-map',
    )

    # Add subject property marker
    fig.add_trace(go.Scattermapbox(
        lat=[property_lat],
        lon=[property_lon],
        mode='markers',
        marker=dict(size=14, color='red', symbol='circle'),
        name='Subject Property',
        hovertext='Subject Property',
        hoverinfo='text',
        showlegend=True,
    ))

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=True,
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.8)",
        ),
    )

    return fig


def display_development_section(lat: float, lon: float):
    """Display neighborhood development activity and building permits."""
    st.markdown("## 🏗 Neighborhood Development Activity")

    try:
        from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

        analyzer = FairfaxPermitsAnalysis()

        # Adaptive radius: expand until we find >= 20 permits (or hit 5mi)
        radius = 2.0
        permits_24mo = analyzer.get_permits_near_point(
            lat, lon, radius_miles=radius, months_back=24
        )
        if len(permits_24mo) < 20:
            radius = 3.0
            permits_24mo = analyzer.get_permits_near_point(
                lat, lon, radius_miles=radius, months_back=24
            )
        if len(permits_24mo) < 20:
            radius = 5.0
            permits_24mo = analyzer.get_permits_near_point(
                lat, lon, radius_miles=radius, months_back=24
            )

        # 6-month window for map
        permits_6mo = analyzer.get_permits_near_point(
            lat, lon, radius_miles=radius, months_back=6
        )

        # Development pressure (recalibrated)
        pressure = analyzer.calculate_development_pressure(
            lat, lon, radius_miles=radius, months_back=24
        )
        score = pressure.get('score', 0)
        rating = pressure.get('rating', 'Unknown')
        trend = pressure.get('trend', 'insufficient_data')

        # Counts
        new_construction = permits_24mo[
            permits_24mo['permit_category'].isin(['residential_new', 'commercial_new'])
        ]
        active_districts = permits_24mo['development_center'].dropna()
        active_districts = active_districts[active_districts != '']
        n_districts = active_districts.nunique()

        # ── 4-column metrics ──
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Development Pressure", f"{score}/100")
            color = {'Very High': '🔴', 'High': '🟠', 'Moderate': '🟡',
                     'Low': '🟢', 'No Activity': '⚪'}.get(rating, '')
            st.caption(f"{color} {rating}")
        with col2:
            st.metric("Permit Activity", f"{len(permits_24mo):,}")
            st.caption(f"Last 24 months · {radius:.0f} mi radius")
        with col3:
            st.metric("New Construction", len(new_construction))
            st.caption("New buildings (24 mo)")
        with col4:
            trend_icon = {'increasing': '📈', 'decreasing': '📉',
                          'stable': '➡️'}.get(trend, 'ℹ️')
            st.metric("Trend", f"{trend_icon} {trend.title()}")
            st.caption("12-month comparison")

        if radius > 2.0:
            st.caption(
                f"ℹ️ Search radius expanded to {radius:.0f} miles "
                f"(fewer than 20 permits within 2 miles — property is near "
                f"the county boundary)."
            )

        # ── Development narrative ──
        st.markdown("### Development Overview")

        if len(permits_24mo) == 0:
            st.info(
                f"**Minimal Development Activity** — No building permits issued "
                f"within {radius:.0f} miles in the past 24 months. This is a very "
                f"stable, established neighborhood."
            )
            st.caption("Source: Fairfax County PLUS Permit Portal, Fairfax County GIS")
            return  # nothing else to show

        if score >= 70:
            st.warning(
                f"**Very High Development Pressure** — {len(permits_24mo):,} permits "
                f"in 24 months, including {len(new_construction)} new construction "
                f"projects. Expect ongoing construction activity and neighborhood "
                f"evolution."
            )
        elif score >= 50:
            st.info(
                f"**High Development Activity** — {len(permits_24mo):,} permits in "
                f"24 months with {len(new_construction)} new construction projects "
                f"alongside renovations."
            )
        elif score >= 30:
            st.success(
                f"**Moderate Development** — Steady activity with "
                f"{len(permits_24mo):,} permits over 24 months, including "
                f"{len(new_construction)} new construction projects."
            )
        else:
            st.success(
                f"**Low Development Pressure** — Limited activity with "
                f"{len(permits_24mo):,} permits. This is a relatively stable "
                f"neighborhood."
            )

        # ── Active planning districts ──
        if n_districts > 0:
            st.markdown("### Active Planning Districts")
            district_counts = active_districts.value_counts().head(5)
            for district, count in district_counts.items():
                pct = count / len(permits_24mo) * 100
                st.markdown(f"**{district}:** {count} permits ({pct:.0f}%)")

            with st.expander("ℹ️ What are Planning Districts?"):
                st.markdown(
                    "**Planning Districts** (officially *Development Centers*) are "
                    "designated growth areas in Fairfax County's Comprehensive Plan. "
                    "They receive focused infrastructure investment and coordinated "
                    "planning. Examples include Dulles Route 28 Corridor, Herndon "
                    "Transit Station Area, and Tysons Corner Urban Center."
                )

        # ── Permit map — adaptive radius, new construction focus ──
        st.markdown("### Recent Construction Activity Map")

        # Adaptive filtering: new construction, expanding radius + time window
        new_construction_cats = ['residential_new', 'commercial_new']
        map_radius = 1.0
        map_permits = pd.DataFrame()
        map_window_months = 12

        def _filter_new_construction(permits_df, _lat, _lon):
            """Filter to new construction and compute distances."""
            if permits_df.empty:
                return pd.DataFrame()
            new_only = permits_df[
                permits_df['permit_category'].isin(new_construction_cats)
            ].copy()
            if new_only.empty:
                return new_only
            if 'centroid_lat' in new_only.columns and 'centroid_lon' in new_only.columns:
                new_only['_dist'] = new_only.apply(
                    lambda r: haversine_distance(_lat, _lon, r['centroid_lat'], r['centroid_lon']),
                    axis=1,
                )
            return new_only

        def _pick_radius_tier(new_only):
            """Return (filtered_df, radius) using expanding distance tiers."""
            if new_only.empty or '_dist' not in new_only.columns:
                return pd.DataFrame(), 2.0
            within_1 = new_only[new_only['_dist'] <= 1.0]
            if len(within_1) >= 5:
                return within_1, 1.0
            within_1_5 = new_only[new_only['_dist'] <= 1.5]
            if len(within_1_5) >= 5:
                return within_1_5, 1.5
            return new_only[new_only['_dist'] <= 2.0], 2.0

        # Try 12-month window first
        permits_12mo = analyzer.get_permits_near_point(
            lat, lon, radius_miles=2.0, months_back=12
        )
        new_12 = _filter_new_construction(permits_12mo, lat, lon)
        map_permits, map_radius = _pick_radius_tier(new_12)

        # If < 5 results, expand to 24-month window
        if len(map_permits) < 5:
            permits_24mo = analyzer.get_permits_near_point(
                lat, lon, radius_miles=2.0, months_back=24
            )
            new_24 = _filter_new_construction(permits_24mo, lat, lon)
            map_permits, map_radius = _pick_radius_tier(new_24)
            map_window_months = 24

        map_count = len(map_permits)
        st.caption(
            f"Showing {map_count:,} new construction permits within "
            f"{map_radius} miles (last {map_window_months} months)"
        )

        if map_count > 0 and PLOTLY_AVAILABLE:
            permit_fig = _create_permits_map_plotly(map_permits, lat, lon)
            if permit_fig:
                st.plotly_chart(permit_fig, width='stretch')

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown("🟢 **Residential New**")
            with col2:
                st.markdown("🔵 **Commercial New**")
            with col3:
                st.markdown("🟠 **Residential Reno**")
            with col4:
                st.markdown("⚫ **Commercial Reno**")
        elif not PLOTLY_AVAILABLE:
            st.info("Map display requires the plotly package.")
        else:
            st.info(
                f"No new construction permits in the last 12 months "
                f"within {map_radius:.0f} miles."
            )

        # ── Permit type breakdown ──
        st.markdown("### Permit Type Breakdown (24 Months)")
        type_counts = permits_24mo['permit_type'].value_counts()
        cols = st.columns(2)
        for idx, (ptype, count) in enumerate(type_counts.items()):
            with cols[idx % 2]:
                pct = count / len(permits_24mo) * 100
                st.markdown(f"**{ptype}:** {count} ({pct:.0f}%)")

        # ── Yearly trend chart ──
        if PLOTLY_AVAILABLE:
            trends = analyzer.get_permit_trends(
                lat, lon, radius_miles=radius, months_back=48
            )
            yearly = trends.get('yearly', {})
            if len(yearly) >= 2:
                st.markdown("### Permit Activity by Year")
                by_cat = trends.get('by_major_category', {})
                chart_rows = []
                for year in sorted(yearly.keys()):
                    cats = by_cat.get(year, {})
                    chart_rows.append({
                        'Year': str(int(year)),
                        'Residential': cats.get('residential', 0),
                        'Commercial': cats.get('commercial', 0),
                    })
                chart_df = pd.DataFrame(chart_rows)
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=chart_df['Year'], y=chart_df['Residential'],
                    name='Residential', marker_color='#22c55e'
                ))
                fig.add_trace(go.Bar(
                    x=chart_df['Year'], y=chart_df['Commercial'],
                    name='Commercial', marker_color='#3b82f6'
                ))
                fig.update_layout(
                    barmode='stack', height=300,
                    margin=dict(l=40, r=20, t=20, b=40),
                    legend=dict(orientation='h', y=-0.15),
                    yaxis_title='Permits',
                )
                st.plotly_chart(fig, use_container_width=True)

        # ── Full permit table ──
        with st.expander(f"📋 View All {len(permits_24mo):,} Permits (24 Months)"):
            tbl = permits_24mo.copy()
            tbl = tbl.sort_values('issued_date', ascending=False)
            tbl['Issued'] = tbl['issued_date'].dt.strftime('%Y-%m-%d')
            tbl['Dist'] = tbl['distance_miles'].round(2).astype(str) + ' mi'

            display_cols = ['Issued', 'permit_type', 'address', 'city',
                            'development_center', 'Dist']
            col_names = ['Date', 'Type', 'Address', 'City',
                         'Planning District', 'Distance']

            show = tbl[display_cols].copy()
            show.columns = col_names
            st.dataframe(show, use_container_width=True, hide_index=True)

        st.caption(
            f"Source: Fairfax County Permit Portal (PLUS System), "
            f"Fairfax County GIS | Search radius: {radius:.0f} miles"
        )

    except FileNotFoundError:
        st.info("Building permits data not available.")
    except Exception as e:
        st.warning(f"Development analysis unavailable: {e}")


# =============================================================================
# SECTION: ZONING
# =============================================================================

def display_zoning_section(address: str, lat: float, lon: float):
    """Display zoning information for Fairfax County properties."""
    st.markdown("## 🏗️ Zoning & Land Use")

    try:
        # Initialize Fairfax zoning analyzer
        zoning_analyzer = FairfaxZoningAnalysis()
        zoning_result = zoning_analyzer.get_zoning(lat, lon)

        if not zoning_result or zoning_result.get('message'):
            st.warning(zoning_result.get('message', 'Unable to load zoning information'))
            return

        # Extract zoning data
        zone_code = zoning_result.get('zone_code', 'N/A')
        zone_type = zoning_result.get('zone_type', 'Unknown')
        zone_type_desc = zoning_result.get('zone_type_description', zone_type)
        zone_description = zoning_result.get('zone_description')
        has_proffer = zoning_result.get('has_proffer', False)
        public_land = zoning_result.get('public_land', False)
        overlays = zoning_result.get('overlays', [])

        # INLINE SUMMARY - Clean and scannable
        st.markdown(f"📍 **Zoning:** {zone_code} • **Type:** {zone_type_desc}")

        # Show special indicators
        if public_land:
            st.info("📍 This property is on **public land**")
        if has_proffer:
            st.info("📋 This property has associated **proffers** (development conditions)")

        # MAIN EXPANDER: What This Means
        with st.expander("📋 Zoning Details", expanded=False):

            # === ZONING FOR THIS PROPERTY ===
            st.markdown("### Zoning for This Property")

            # Generate narrative based on zoning type
            if zone_description:
                st.markdown(f"""
This property is zoned **{zone_code}** ({zone_description}).

**Zone Type:** {zone_type_desc}

This zoning classification determines what can be built on this property,
including permitted uses, building heights, setbacks, and density limits.
""")
            else:
                st.markdown(f"""
This property is zoned **{zone_code}** ({zone_type_desc}).

This zoning classification determines what can be built on this property,
including permitted uses, building heights, setbacks, and density limits.
""")

            # === OVERLAY DISTRICTS ===
            if overlays:
                st.markdown("### Overlay Districts")
                for overlay in overlays:
                    overlay_type = overlay.get('overlay_type', 'Unknown')
                    if overlay_type == 'airport_noise_impact':
                        decibel = overlay.get('decibel_level', 0)
                        st.warning(f"✈️ **Airport Noise Impact Zone** - {decibel} dB")
                        if decibel >= 70:
                            st.markdown("*High aircraft noise - may significantly impact outdoor activities and require noise mitigation.*")
                        elif decibel >= 65:
                            st.markdown("*Moderate aircraft noise - may affect conversations outdoors and sleep with windows open.*")
                        else:
                            st.markdown("*Low-moderate aircraft noise - generally acceptable for residential use.*")
                    else:
                        st.info(f"📍 **{overlay_type}** overlay applies to this property")

            # === RECENT CONSTRUCTION ACTIVITY ===
            st.markdown("### Recent Construction Activity")
            try:
                permits_analyzer = FairfaxPermitsAnalysis()
                nearby_permits = permits_analyzer.get_permits_near_point(lat, lon, radius_miles=1.0, months_back=24)

                if len(nearby_permits) > 0:
                    total_permits = len(nearby_permits)
                    residential_new = len(nearby_permits[nearby_permits['permit_category'] == 'residential_new']) if 'permit_category' in nearby_permits.columns else 0
                    commercial = len(nearby_permits[nearby_permits['permit_category'].str.contains('commercial', na=False)]) if 'permit_category' in nearby_permits.columns else 0

                    st.markdown(f"""
**{total_permits} building permits** issued within 1 mile in the past 24 months.

This indicates {"active" if total_permits > 20 else "moderate" if total_permits > 5 else "low"} construction activity in the area.
""")
                    if residential_new > 0:
                        st.markdown(f"• **{residential_new}** new residential construction permits")
                    if commercial > 0:
                        st.markdown(f"• **{commercial}** commercial permits")
                else:
                    st.info("No recent building permits found within 1 mile (past 24 months).")
            except Exception as e:
                st.caption("💡 Permit data unavailable")

            # Technical Reference
            st.markdown("---")
            st.caption(f"**Technical Reference:** Zoning Code: {zone_code}")
            if zone_description:
                st.caption(zone_description)
            st.caption("Source: Fairfax County GIS, 2025")

        # Development Pressure (based on building permits)
        # Only show section if meaningful permit data is available
        try:
            permits_analyzer = FairfaxPermitsAnalysis()
            dev_pressure = permits_analyzer.calculate_development_pressure(lat, lon, radius_miles=1.0, months_back=24)
            score = dev_pressure.get('score', 0)
            trend = dev_pressure.get('trend', 'stable')

            # Skip entire section if data is insufficient
            if trend != 'insufficient_data' and (score > 0 or dev_pressure.get('total_permits', 0) > 0):
                with st.expander("🔮 Development Pressure", expanded=False):
                    # Display score with color
                    if score < 25:
                        color = "🟢"
                        level = "Low"
                    elif score < 50:
                        color = "🟡"
                        level = "Moderate"
                    elif score < 75:
                        color = "🟠"
                        level = "High"
                    else:
                        color = "🔴"
                        level = "Very High"

                    st.markdown(f"{color} **Development Pressure:** {score}/100 ({level})")
                    st.markdown(f"**Trend:** {trend.title()}")

                    # Show current status
                    st.markdown("**Current Status:**")
                    st.markdown(f"• Zoned: {zone_code} ({zone_type_desc})")

                    # Score breakdown
                    breakdown = dev_pressure.get('breakdown', {})
                    if breakdown:
                        st.markdown("**Score Factors:**")
                        for factor, value in breakdown.items():
                            st.markdown(f"• {factor.replace('_', ' ').title()}: {value}")

                    st.markdown("""
---
**What This Means:**

Development pressure is calculated from building permit activity within 1 mile
over the past 24 months. Higher scores indicate more construction activity,
which may signal:

- **High pressure (60+):** Active development area with significant new construction
- **Moderate (30-59):** Healthy development activity, typical suburban growth
- **Low (0-29):** Established, stable neighborhood with minimal new construction
""")
        except Exception:
            pass  # Silently skip if permits data unavailable

    except Exception as e:
        st.warning(f"Zoning analysis error: {str(e)}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

    st.markdown("---")


# =============================================================================
# SECTION: PROPERTY VALUATION
# =============================================================================

def display_valuation_section(address: str, lat: float, lon: float, sqft_result: dict):
    """Display property valuation section with MLS square footage."""
    st.markdown("## 💰 Property Value Analysis")

    if not VALUATION_AVAILABLE:
        st.info("""
        **Property valuation features require API configuration.**

        Configure ATTOM and RentCast API keys to enable:
        - Current market value estimates
        - Comparable sales analysis
        - Rental value estimates
        - 1/3/5 year forecasts

        API keys location: `/home/claude/.config/newco/api_keys.json`
        """)
        return

    try:
        # Resolve square footage: MLS first, then ATTOM fallback
        sqft = None
        sqft_source = None
        sqft_source_details = None

        # Check MLS result
        if sqft_result and sqft_result.get('mls_sqft'):
            sqft = sqft_result['mls_sqft']
            sources = sqft_result.get('sources_found', [])
            if sources:
                sqft_source = 'MLS'
                sqft_source_details = ', '.join(sources[:3])  # Show up to 3 sources
            else:
                sqft_source = 'MLS'
                sqft_source_details = 'web search'

        with st.spinner("Fetching property valuation data..."):
            orchestrator = PropertyValuationOrchestrator()

            # Get lot size, year built, property type, and ATTOM sqft fallback
            lot_size_acres = None
            attom_sqft = None
            year_built = None
            property_type = None
            if ATTOM_CLIENT:
                try:
                    property_data = ATTOM_CLIENT.get_property_detail(address)
                    if property_data:
                        if property_data.lot_size:
                            lot_size_acres = property_data.lot_size
                        if property_data.sqft:
                            attom_sqft = property_data.sqft
                        if property_data.year_built:
                            year_built = property_data.year_built
                        if property_data.property_type:
                            property_type = property_data.property_type
                except Exception:
                    pass

            # Use ATTOM sqft as fallback if MLS failed
            if not sqft and attom_sqft:
                sqft = attom_sqft
                sqft_source = 'Tax Records'
                sqft_source_details = 'may exclude finished basement'

            # Run valuation with resolved sqft
            val_data = orchestrator.analyze_property(address, lat, lon, sqft)

        # Property Details (sqft and lot size)
        st.markdown("### Property Details")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if sqft:
                if sqft_source == 'MLS':
                    st.metric("📐 Property Size", f"{sqft:,} sqft")
                    st.caption(f"from {sqft_source_details}")
                else:
                    st.metric("📐 Property Size", f"{sqft:,} sqft")
                    st.caption(f"Tax Records - {sqft_source_details}")
            else:
                st.metric("📐 Property Size", "Unavailable")
                st.caption("Could not determine square footage")

        with col2:
            if lot_size_acres:
                st.metric("🌳 Lot Size", f"{lot_size_acres:.2f} acres")

        with col3:
            if year_built:
                st.metric("🏠 Year Built", str(year_built))
            else:
                st.metric("🏠 Year Built", "N/A")

        with col4:
            if property_type:
                st.metric("🏘️ Property Type", property_type)
            else:
                st.metric("🏘️ Property Type", "N/A")

        # === Sales History Section ===
        st.markdown("### 📊 Sales History")

        sales_history = val_data.get('sales_history', {})

        if sales_history.get('error'):
            st.warning(f"⚠️ Could not load sales history: {sales_history['error']}")

        elif sales_history.get('found'):
            sales = sales_history.get('sales', [])

            if not sales:
                st.info("No recorded sales found in county records (2020-2025).")
            else:
                # Build display table (excluding owner names)
                display_data = []
                for sale in sales:
                    date_str = format_sale_date(sale.get('sale_date', ''))
                    time_since = format_time_since_sale(sale.get('sale_date', ''))
                    price_str = format_sale_price(sale.get('sale_price'))
                    type_str = clean_verification_code(sale.get('verification_code', ''))

                    display_data.append({
                        'Sale Date': date_str,
                        'Time Since Sale': time_since,
                        'Price': price_str,
                        'Transaction Type': type_str
                    })

                # Show table
                df = pd.DataFrame(display_data)
                st.dataframe(df, width='stretch', hide_index=True)

                # Appreciation calculation (if multiple sales with prices)
                if len(sales) > 1 and sales[0].get('sale_price') and sales[-1].get('sale_price'):
                    oldest = sales[-1]  # Last in list (oldest chronologically)
                    newest = sales[0]   # First in list (newest chronologically)

                    old_price = oldest['sale_price']
                    new_price = newest['sale_price']
                    appreciation_pct = ((new_price - old_price) / old_price) * 100

                    st.info(f"💡 Appreciation: {format_sale_price(old_price)} ({format_sale_date(oldest.get('sale_date', ''))}) → {format_sale_price(new_price)} ({format_sale_date(newest.get('sale_date', ''))}) = **{appreciation_pct:+.1f}%**")

                # Current Estimated Value comparison (if available)
                current_avm = val_data.get('current_value', {}).get('attom_estimate')
                if current_avm and sales[0].get('sale_price'):
                    latest_sale = sales[0]
                    sale_price = latest_sale['sale_price']
                    avm_vs_sale = ((current_avm - sale_price) / sale_price) * 100
                    st.info(f"📈 Current Estimated Value: {format_sale_price(current_avm)} ({avm_vs_sale:+.1f}% vs. last sale)")

                # Source attribution
                data_range = sales_history.get('data_range', '2020-2025')
                source = sales_history.get('source', 'Loudoun County Commissioner of Revenue')
                st.caption(f"**Source:** {source} • Showing sales from {data_range}")

        else:
            st.info("No recorded sales found in county records (2020-2025).")

        # Current value
        cv = val_data.get('current_value', {})

        st.markdown("### Current Value Estimates")

        # Only show ATTOM column if ATTOM is enabled and has data
        attom_val = cv.get('attom_estimate', 0) if ATTOM_CLIENT else 0
        rentcast_val = cv.get('rentcast_estimate', 0)
        triangulated = cv.get('triangulated_estimate', 0)
        confidence = cv.get('confidence_score', 0)

        if attom_val:
            # Show all 4 columns when ATTOM is available
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ATTOM Estimate", f"${attom_val:,.0f}")
            with col2:
                st.metric("RentCast Estimate", f"${rentcast_val:,.0f}" if rentcast_val else "N/A")
            with col3:
                st.metric("Triangulated Value", f"${triangulated:,.0f}" if triangulated else "N/A")
            with col4:
                st.metric("Confidence", f"{confidence:.1f}/10" if confidence else "N/A")
        else:
            # Show only 3 columns when ATTOM is disabled/unavailable
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("RentCast Estimate", f"${rentcast_val:,.0f}" if rentcast_val else "N/A")
            with col2:
                st.metric("Triangulated Value", f"${triangulated:,.0f}" if triangulated else "N/A")
            with col3:
                st.metric("Confidence", f"{confidence:.1f}/10" if confidence else "N/A")

        # Forecast
        fc = val_data.get('forecast', {})
        if fc:
            st.markdown("### Property Valuation Projection")
            col1, col2, col3 = st.columns(3)

            with col1:
                y1 = fc.get('1_year', {})
                st.metric(
                    "1-Year Forecast",
                    f"${y1.get('value', 0):,.0f}",
                    delta=f"{y1.get('change_pct', 0):+.1f}%"
                )

            with col2:
                y3 = fc.get('3_year', {})
                st.metric(
                    "3-Year Forecast",
                    f"${y3.get('value', 0):,.0f}",
                    delta=f"{y3.get('change_pct', 0):+.1f}%"
                )

            with col3:
                y5 = fc.get('5_year', {})
                st.metric(
                    "5-Year Forecast",
                    f"${y5.get('value', 0):,.0f}",
                    delta=f"{y5.get('change_pct', 0):+.1f}%"
                )

        # Rental analysis
        ra = val_data.get('rental_analysis', {})
        if ra:
            st.markdown("### Investment Analysis")
            col1, col2, col3 = st.columns(3)

            with col1:
                rent = ra.get('estimated_rent_monthly', 0)
                st.metric("Est. Monthly Rent", f"${rent:,.0f}" if rent else "N/A")

            with col2:
                gross_yield = ra.get('gross_yield_pct', 0)
                st.metric("Gross Yield", f"{gross_yield:.1f}%" if gross_yield else "N/A")

            with col3:
                cash_flow = ra.get('cash_flow_potential', 'N/A')
                st.metric("Cash Flow", cash_flow)

        # Comparable sales - Professional table with quality assessment
        comps = val_data.get('comparable_sales', [])
        subject_sqft = sqft or 0  # Subject property sqft for similarity calculation

        if comps:
            with st.expander(f"📋 Comparable Sales ({len(comps)} properties)", expanded=True):
                # Calculate quality scores and build display data
                display_data = []
                for comp in comps:
                    # Quality score calculation
                    quality_scores = []

                    # Distance score: <0.5mi=3, <1mi=2, <2mi=1, >2mi=0
                    dist = comp.get('distance_miles', 99)
                    if dist < 0.5:
                        dist_score = 3
                    elif dist < 1.0:
                        dist_score = 2
                    elif dist < 2.0:
                        dist_score = 1
                    else:
                        dist_score = 0
                    quality_scores.append(dist_score)

                    # Sqft similarity: within 20%=3, 20-40%=2, >40%=1
                    comp_sqft = comp.get('sqft', 0)
                    if subject_sqft > 0 and comp_sqft > 0:
                        sqft_diff_pct = abs(comp_sqft - subject_sqft) / subject_sqft * 100
                        if sqft_diff_pct <= 20:
                            sqft_score = 3
                        elif sqft_diff_pct <= 40:
                            sqft_score = 2
                        else:
                            sqft_score = 1
                    else:
                        sqft_score = 1  # Unknown = fair
                    quality_scores.append(sqft_score)

                    # Sale recency: <6mo=3, 6-12mo=2, >12mo=1
                    sale_date_str = comp.get('sale_date', '')
                    if sale_date_str:
                        try:
                            # Try common date formats
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                                try:
                                    sale_date = datetime.strptime(sale_date_str, fmt)
                                    break
                                except ValueError:
                                    continue
                            else:
                                sale_date = None

                            if sale_date:
                                months_ago = (datetime.now() - sale_date).days / 30
                                if months_ago <= 6:
                                    recency_score = 3
                                elif months_ago <= 12:
                                    recency_score = 2
                                else:
                                    recency_score = 1
                            else:
                                recency_score = 1
                        except Exception:
                            recency_score = 1
                    else:
                        recency_score = 1
                    quality_scores.append(recency_score)

                    # Calculate overall quality (average, then map to label)
                    avg_score = sum(quality_scores) / len(quality_scores)
                    if avg_score >= 2.5:
                        quality_label = "Excellent"
                    elif avg_score >= 1.8:
                        quality_label = "Good"
                    else:
                        quality_label = "Fair"

                    # Format sale date for display (MMM YYYY)
                    display_date = sale_date_str
                    if sale_date_str:
                        try:
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                                try:
                                    parsed = datetime.strptime(sale_date_str, fmt)
                                    display_date = parsed.strftime('%b %Y')
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass

                    # Format beds/baths
                    beds = comp.get('bedrooms')
                    baths = comp.get('bathrooms')
                    if beds and baths:
                        beds_baths = f"{beds}bd/{baths}ba"
                    elif beds:
                        beds_baths = f"{beds}bd"
                    elif baths:
                        beds_baths = f"{baths}ba"
                    else:
                        beds_baths = "—"

                    display_data.append({
                        'Address': comp.get('address', 'N/A'),
                        'Subdivision': comp.get('subdivision') or '—',
                        'Price': f"${comp.get('sale_price', 0):,.0f}",
                        'Sale Date': display_date or '—',
                        'Sqft': f"{comp_sqft:,}" if comp_sqft else '—',
                        '$/Sqft': f"${comp.get('price_per_sqft', 0):,.0f}" if comp.get('price_per_sqft') else '—',
                        'Year': comp.get('year_built') or '—',
                        'Beds/Baths': beds_baths,
                        'Distance': f"{dist:.2f} mi",
                        'Quality': quality_label,
                        '_sort_score': avg_score  # Hidden sort column
                    })

                # Sort by quality (best first)
                display_data.sort(key=lambda x: x['_sort_score'], reverse=True)

                # Remove sort column before display
                for row in display_data:
                    del row['_sort_score']

                # Create DataFrame and display
                df = pd.DataFrame(display_data)

                # Style the quality column with colors
                def style_quality(val):
                    if val == 'Excellent':
                        return 'background-color: #d4edda; color: #155724'
                    elif val == 'Good':
                        return 'background-color: #fff3cd; color: #856404'
                    else:
                        return 'background-color: #f8d7da; color: #721c24'

                # Apply styling and display
                styled_df = df.style.applymap(style_quality, subset=['Quality'])
                st.dataframe(
                    styled_df,
                    width='stretch',
                    hide_index=True,
                    height=min(400, 50 + len(display_data) * 35)  # Dynamic height
                )

                # Quality score legend
                st.caption("**Quality Score:** Based on distance (<0.5mi best), size similarity (within 20% best), and sale recency (<6 months best)")
                st.caption("*Comparable property square footage from tax records. May exclude finished basements. All comps measured consistently for fair comparison.*")

    except Exception as e:
        st.error(f"Valuation error: {e}")

    st.markdown("---")


# =============================================================================
# SECTION: AI ANALYSIS
# =============================================================================

def _generate_power_line_narrative(power_lines: Dict[str, Any]) -> str:
    """
    Generate power infrastructure narrative in direct coffee-chat style.

    No hedging, no weasel words. State facts clearly with specific numbers.
    Acknowledge concerns honestly without dismissing or exaggerating.
    """
    if not power_lines or 'error' in power_lines:
        return ""

    impact_score = power_lines.get('visual_impact_score', 1)
    impact_level = power_lines.get('visual_impact_level', 'None')
    nearest_built = power_lines.get('nearest_built_line')
    nearest_approved = power_lines.get('nearest_approved_line')
    lines_within_mile = power_lines.get('lines_within_one_mile', 0)

    # No impact - brief mention
    if impact_score == 1:
        narrative = "Power infrastructure: Standard residential electrical service. No major transmission lines within a mile."
        if nearest_approved:
            voltage = nearest_approved['voltage']
            dist = nearest_approved['distance_miles']
            narrative += f" Note: A {voltage}kV line is approved at {dist:.1f} miles - not yet built."
        return narrative

    # Get key details
    if not nearest_built:
        return ""

    voltage = nearest_built['voltage']
    dist = nearest_built['distance_miles']
    feet = int(dist * 5280)

    # Very High impact (score 5) - 500kV very close or 230kV extremely close
    if impact_score == 5:
        if voltage >= 500:
            narrative = f"Let's talk about the big one: there's a {voltage}kV ultra-high-voltage transmission line {dist:.2f} miles away - that's about {feet:,} feet. This is serious regional grid infrastructure, not your standard power line. You'll see it from the property. The EMF concerns are real in buyers' minds, even if utilities maintain safety standards. Trade-off to consider. Some buyers walk away, some don't care. Know what you're getting."
        else:
            narrative = f"Power infrastructure: {voltage}kV transmission line sits {dist:.2f} miles out ({feet:,} feet). That's close. At this distance, the towers and lines are visible. Some buyers factor this into their decision, some don't. Be aware of it."

    # High impact (score 4)
    elif impact_score == 4:
        narrative = f"Power infrastructure context: {voltage}kV transmission line at {dist:.2f} miles ({feet:,} feet). Close enough that you might notice it, especially in winter when trees are bare. Part of Loudoun's electrical grid supporting residential and commercial development. Worth a drive-by to see the actual visual impact from the property."

    # Moderate impact (score 3)
    elif impact_score == 3:
        narrative = f"Power infrastructure: {voltage}kV line sits {dist:.2f} miles out. You probably won't see it day-to-day from the house. It's part of Loudoun's electrical grid serving residential and commercial development. At this distance, most buyers don't think twice about it."

    # Low impact (score 2)
    else:
        narrative = f"Power infrastructure: {voltage}kV transmission line at {dist:.1f} miles. Far enough that it's not a visual or practical concern for most buyers."

    # Add context about multiple lines if relevant
    if lines_within_mile > 1:
        narrative += f" There are {lines_within_mile} transmission lines within a mile of this property - this is part of a developed infrastructure corridor."

    # Add future line info (differentiator!)
    if nearest_approved:
        app_voltage = nearest_approved['voltage']
        app_dist = nearest_approved['distance_miles']
        narrative += f"\n\nHeads-up on future infrastructure: There's an approved {app_voltage}kV line planned {app_dist:.2f} miles from this property. Construction timeline unknown, but it's officially in the pipeline. Won't be there when you move in, but it's coming. If you're thinking 10+ years, factor that in."

    # Data center corridor context for high voltage lines in Ashburn area
    if voltage >= 230 and lines_within_mile >= 2:
        narrative += " This infrastructure is part of the electrical backbone supporting Loudoun's position as a global data center hub - the reason the county has world-class fiber infrastructure and stable tech employment."

    return narrative


def display_ai_analysis(
    address: str,
    coords: Tuple[float, float],
    schools_info: Optional[Dict[str, str]] = None,
    valuation_result: Optional[Dict[str, Any]] = None,
    development_2mi: Optional[Dict[str, Any]] = None,
    development_5mi: Optional[Dict[str, Any]] = None,
    demographics: Optional[Dict[str, Any]] = None
):
    """
    Display AI-powered property analysis narrative using Claude API.

    Args:
        address: Full property address
        coords: (latitude, longitude) tuple
        schools_info: Dict with school assignments {elementary, middle, high}
        valuation_result: Dict from property_valuation_orchestrator.analyze_property()
        development_2mi: Dict from analyze_development() with 2mi radius
        development_5mi: Dict from analyze_development() with 5mi radius
        demographics: Dict from calculate_demographics() with Census data
    """
    st.markdown("## 🤖 AI Property Analysis")

    # Session state key for retry functionality
    narrative_key = f"narrative_{address}"

    def generate_narrative():
        """Generate narrative using Claude API."""
        try:
            # Compile all available data
            compiled_data = compile_narrative_data(
                address=address,
                coords=coords,
                sqft=None,  # Intentionally None - not solving basement problem for demo
                schools_info=schools_info,
                valuation_result=valuation_result,
                development_2mi=development_2mi,
                development_5mi=development_5mi,
                demographics=demographics
            )

            # Generate narrative via Claude API
            narrative_result = generate_property_narrative(compiled_data, use_cache=True)
            return narrative_result

        except Exception as e:
            return {'error': str(e)}

    # Check if we need to generate or have cached result
    if narrative_key not in st.session_state or st.session_state.get(f"{narrative_key}_retry"):
        with st.spinner("Generating AI analysis..."):
            result = generate_narrative()
            st.session_state[narrative_key] = result
            st.session_state[f"{narrative_key}_retry"] = False

    result = st.session_state.get(narrative_key, {})

    # Handle errors gracefully
    if 'error' in result or not result.get('sections'):
        error_msg = result.get('error', 'Unknown error')
        metadata = result.get('metadata', {})
        api_error = metadata.get('error', '')

        st.warning("AI narrative temporarily unavailable. Please try again.")

        # Show error details in expander for debugging
        with st.expander("Error Details"):
            if api_error:
                st.text(f"API Error: {api_error}")
            if error_msg and error_msg != api_error:
                st.text(f"Error: {error_msg}")

        # Retry button
        if st.button("🔄 Retry Narrative Generation", key="retry_narrative"):
            st.session_state[f"{narrative_key}_retry"] = True
            st.rerun()

        return

    # Extract sections
    sections = result.get('sections', {})
    metadata = result.get('metadata', {})

    # Helper to escape dollar signs (prevents LaTeX math mode interpretation)
    def escape_dollars(text: str) -> str:
        """Escape dollar signs to prevent Streamlit LaTeX interpretation."""
        return text.replace('$', '\\$') if text else text

    # Display the 6 narrative sections with proper formatting
    section_config = [
        ('what_stands_out', 'What Stands Out'),
        ('schools_reality', 'Schools'),
        ('daily_reality', 'The Daily Reality'),
        ('worth_knowing', 'Worth Knowing'),
        ('investment_lens', 'Development & Investment'),
        ('bottom_line', 'Bottom Line')
    ]

    for key, title in section_config:
        content = sections.get(key, '')
        if content:
            # Escape dollar signs before markdown rendering
            escaped_content = escape_dollars(content)
            st.markdown(f"**{title}:** {escaped_content}")
            st.markdown("")  # Add spacing between sections

    # Metadata footer (subtle)
    if metadata.get('cached'):
        st.caption("📦 Analysis from cache")
    else:
        st.caption("🤖 AI-generated analysis")

    st.markdown("---")


# =============================================================================
# SECTION: TRANSIT / TRANSPORTATION
# =============================================================================

def display_transit_section(lat: float, lon: float):
    """Display transit accessibility for Fairfax County properties.

    Uses FairfaxTransitAnalysis to show Metro station proximity,
    bus route coverage, and an overall transit score.
    """
    st.markdown("## 🚇 Transit & Transportation")

    try:
        transit = FairfaxTransitAnalysis()
    except Exception as e:
        st.warning(f"Transit data not available: {e}")
        return

    try:
        # Get transit score and metro info
        transit_score = transit.calculate_transit_score(lat, lon)
        nearest_metro = transit.get_nearest_metro_station(lat, lon)
        bus_routes = transit.get_nearby_bus_routes(lat, lon, radius_miles=0.5, limit=5)

        # --- Score and Metro metrics row ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            rating = transit_score.get('rating', 'N/A').title()
            st.metric("Transit Score", f"{transit_score.get('score', 0)}/100", help=f"Rating: {rating}")
        with col2:
            station = nearest_metro.get('station_name', 'N/A')
            st.metric("Nearest Metro", station)
        with col3:
            dist = nearest_metro.get('distance_miles', 0)
            st.metric("Metro Distance", f"{dist:.1f} mi")
        with col4:
            walk = nearest_metro.get('walk_time_minutes', 0)
            st.metric("Walk to Metro", f"{walk} min" if walk else "N/A")

        # --- Score breakdown ---
        breakdown = transit_score.get('breakdown', {})
        if breakdown:
            with st.expander("Transit Score Breakdown", expanded=False):
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.metric("Metro Access", f"{breakdown.get('metro_access', 0)}/50")
                with b2:
                    st.metric("Bus Coverage", f"{breakdown.get('bus_coverage', 0)}/30")
                with b3:
                    st.metric("Service Variety", f"{breakdown.get('service_variety', 0)}/20")

        # --- Nearby bus routes ---
        if bus_routes:
            with st.expander(f"Nearby Bus Routes ({len(bus_routes)} within 0.5 mi)", expanded=False):
                for route in bus_routes:
                    st.markdown(
                        f"**{route['route_number']}** — {route['route_name']} "
                        f"({route['service_type']}, {route['distance_miles']:.2f} mi)"
                    )

        st.caption("Source: WMATA Metro Stations, Fairfax Connector Bus Routes, Fairfax County GIS")

    except Exception as e:
        st.warning(f"Transit analysis error: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# =============================================================================
# SECTION: FOOTER
# =============================================================================

def display_footer():
    """Display data sources and footer."""
    st.markdown("## 📊 Data Sources")

    # Dynamic valuation source based on ATTOM availability
    valuation_source = "ATTOM Data Solutions, RentCast API" if ATTOM_CLIENT else "RentCast API"

    st.markdown(f"""
| Category | Source |
|----------|--------|
| Property Valuation | {valuation_source} |
| Area Demographics | U.S. Census Bureau - American Community Survey 2019-2023 |
| Monthly Unemployment | Bureau of Labor Statistics - Local Area Unemployment Statistics |
| Labor Force Participation | U.S. Census Bureau - ACS 5-Year Estimates |
| Industry Employment | U.S. Census Bureau - ACS 5-Year Estimates |
| Major Employers | Fairfax County ACFR (2008-2025) |
| Schools | Fairfax County Public Schools (FCPS) / Fairfax County GIS |
| School Performance | Virginia Department of Education - SOL 5-Year Trends |
| Building Permits | Fairfax County Permit Portal |
| Traffic Volume | VDOT Bidirectional Traffic Volume Database |
| Metro Access | WMATA Metro Stations / Fairfax County GIS |
| Power Infrastructure | Fairfax County Power Infrastructure (GIS) |
| Cell Towers | Fairfax County Telecom Towers (GIS) + FCC Registration Database |
| Medical Facilities | Fairfax County GIS, CMS Hospital Compare, Leapfrog Group |
| Pharmacies | Google Places API |
| Neighborhood Amenities | Google Places API (Real-time) |
| Travel Times | Google Distance Matrix API |
| Parks & Recreation | Google Places API |
| GIS Data | Fairfax County Official Shapefiles |
| Road Network | Fairfax County Roadway Centerlines GIS |
| Zoning | Fairfax County Zoning Districts (GIS) |
| Airport Zones | Fairfax County Airport Overlay Districts |
| Flood Zones | FEMA Flood Insurance Rate Map (via Fairfax County GIS) |
| Community Data | NewCo Private Research, RentCast API |

**Analysis Date:** {datetime.now().strftime('%B %d, %Y')}

---

*Fairfax County Property Intelligence Platform*
*Professional Real Estate Analysis*
""")


# =============================================================================
# MAIN REPORT ENTRY POINT
# =============================================================================

def render_report(address: str, lat: float, lon: float):
    """
    Main entry point called by unified_app.py router.

    Args:
        address: Property address being analyzed
        lat: Property latitude
        lon: Property longitude

    This function orchestrates the complete Loudoun County analysis,
    calling all 13 display sections in sequence.
    """

    # Progress tracking
    progress = st.progress(0)
    status = st.empty()

    # Collect all data
    data = {}

    try:
        # Schools (15%)
        status.text("⏳ Fetching school assignments...")
        progress.progress(15)
        # Pre-compute school assignments for AI narrative
        data['schools'] = find_assigned_schools(lat, lon)

        # =========================================================================
        # PHASE 2: INITIALIZATION CODE (TEMPORARILY DISABLED)
        # These sections use Loudoun-specific modules not yet ported to Fairfax
        # Uncomment after porting in Phase 2/3
        # =========================================================================

        # # Location (30%)
        # status.text("⏳ Analyzing location quality...")
        # progress.progress(30)
        # data['location'] = analyze_location_quality(lat, lon, address)

        # # Power Lines (40%)
        # status.text("⏳ Checking power infrastructure...")
        # progress.progress(40)
        # data['power_lines'] = analyze_power_line_proximity(lat, lon)

        # # Cell Towers (42%)
        # status.text("⏳ Analyzing cell tower coverage...")
        # progress.progress(42)
        # data['cell_towers'] = analyze_cell_tower_coverage(lat, lon)

        # # Metro Access (45%)
        # status.text("⏳ Analyzing Metro access...")
        # progress.progress(45)
        # data['metro'] = analyze_metro_access((lat, lon))

        # # Flood Zone Check (47%)
        # status.text("⏳ Checking flood zone status...")
        # progress.progress(47)
        # data['flood_zone'] = check_flood_zone(lat, lon)

        # # Parks Proximity (48%)
        # status.text("⏳ Finding nearby parks...")
        # progress.progress(48)
        # parks_static_data = load_parks_data()
        # data['parks'] = get_nearest_parks(lat, lon, parks_static_data)

        # # Neighborhood Amenities (50%)
        # status.text("⏳ Discovering neighborhood amenities...")
        # progress.progress(50)
        # data['neighborhood'] = analyze_neighborhood((lat, lon))

        # # Development - Dual Radius (60%)
        # status.text("⏳ Analyzing development activity (2mi + 5mi)...")
        # progress.progress(55)
        # data['development_2mi'] = analyze_development(lat, lon, radius_miles=2.0)
        # progress.progress(60)
        # data['development_5mi'] = analyze_development(lat, lon, radius_miles=5.0)
        # =========================================================================

        # Square Footage - DISABLED for demo
        # MLS web search unreliable (DuckDuckGo: bot detection, Brave: wrong results)
        # Using tax assessor data for consistency - will show as "Tax Records"
        # Future: Direct MLS API integration (Bridge/Zillow) post-demo
        status.text("⏳ Loading property details...")
        progress.progress(70)
        sqft_result = None  # Disabled - use ATTOM/tax records fallback
        data['sqft'] = sqft_result

        # Zoning (75%)
        status.text("⏳ Checking zoning...")
        progress.progress(75)
        # Get zoning data using Fairfax module and store in data dict for AI Summary
        try:
            zoning_analyzer = FairfaxZoningAnalysis()
            data['zoning'] = zoning_analyzer.get_zoning(lat, lon)
        except Exception:
            data['zoning'] = None

        # PHASE 2: Valuation (85%) - TEMPORARILY DISABLED
        data['valuation'] = None
        # if VALUATION_AVAILABLE:
        #     status.text("⏳ Fetching valuations...")
        #     progress.progress(85)
        #     # Pre-compute valuation for AI narrative
        #     try:
        #         orchestrator = PropertyValuationOrchestrator()
        #         data['valuation'] = orchestrator.analyze_property(address, lat, lon, None)
        #     except Exception as val_err:
        #         # Valuation failure shouldn't block the whole analysis
        #         data['valuation'] = None

        # Complete
        progress.progress(100)
        status.text("✓ Analysis complete!")

        # Clear progress indicators
        progress.empty()
        status.empty()

        # Display all sections
        st.success(f"✓ Analysis complete for: **{address}**")
        st.markdown("---")

        # =========================================================================
        # PHASE 1 SECTIONS (ACTIVE) - Schools, Crime, Zoning
        # =========================================================================

        # Schools (uses pre-computed assignments)
        display_schools_section(lat, lon)

        # Crime & Safety (Fairfax-specific)
        display_crime_section(lat, lon)

        # Zoning
        display_zoning_section(address, lat, lon)

        # Transit & Transportation (Fairfax-specific module)
        display_transit_section(lat, lon)

        # =========================================================================
        # END OF PHASE 1 SECTIONS
        # =========================================================================

        # =========================================================================
        # PHASE 2/3 SECTIONS (TEMPORARILY DISABLED)
        # Uncomment after porting Loudoun modules to Fairfax
        # =========================================================================

        # # Location Quality
        # display_location_section(data['location'], data.get('power_lines', {}), data.get('metro', {}), data.get('flood_zone', {}), data.get('parks', {}), lat, lon)

        # Cell Tower Coverage (rewired to Fairfax module)
        display_cell_towers_section(lat, lon)

        # # Neighborhood Amenities
        # display_neighborhood_section(data.get('neighborhood', {}))

        # # Community & HOA Information
        # display_community_section(data.get('valuation', {}), lat, lon)

        # Area Demographics (Census data — Fairfax County FIPS 51059)
        demographics_data = None
        if DEMOGRAPHICS_AVAILABLE:
            st.markdown("## 📈 Area Demographics")
            demographics_data = calculate_demographics(
                lat, lon, address,
                county_fips='059',
                county_name='Fairfax County, VA'
            )
            display_demographics_section(demographics_data, st)

        # Economic Indicators (LFPR, Industry Mix, Major Employers)
        if ECONOMIC_INDICATORS_AVAILABLE:
            display_economic_indicators_section()

        # Medical Access (rewired to Fairfax module)
        display_medical_access_section(lat, lon)

        # Development Activity & Building Permits
        display_development_section(lat, lon)

        # # Valuation (now includes MLS sqft lookup)
        # display_valuation_section(address, lat, lon, sqft_result)

        # # AI Analysis - pass all pre-computed data including demographics
        # display_ai_analysis(
        #     address=address,
        #     coords=(lat, lon),
        #     schools_info=data.get('schools'),
        #     valuation_result=data.get('valuation'),
        #     development_2mi=data.get('development_2mi'),
        #     development_5mi=data.get('development_5mi'),
        #     demographics=demographics_data
        # )
        # =========================================================================

        # Footer
        display_footer()

    except Exception as e:
        st.error(f"Analysis failed: {e}")
        import traceback
        with st.expander("Error Details"):
            st.code(traceback.format_exc())


# =============================================================================
# NOTE: ROUTER INTEGRATION
# =============================================================================
# The following functions were removed when porting to the multi-county router:
# - geocode_address() - handled by unified_app.py via utils/geocoding.py
# - main() - handled by unified_app.py
#
# This module is now called via:
#     from reports.loudoun_report import render_report
#     render_report(address, lat, lon)
#
# See unified_app.py for the main entry point.
# =============================================================================


# Backwards compatibility alias
analyze_property = render_report
