#!/usr/bin/env python3
"""
Fairfax County Building Permits ETL Pipeline

Downloads, processes, and stores building permit data from Fairfax County's
Building Records PLUS ArcGIS REST API for development pressure analysis.

Source: https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services/Building_Records_PLUS/FeatureServer/0

Usage:
    python fairfax_permits_etl.py              # Full download (2022-2026)
    python fairfax_permits_etl.py --recent     # Last 30 days only
    python fairfax_permits_etl.py --test       # Download 100 records for testing
"""

import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import math

import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

API_BASE_URL = "https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services/Building_Records_PLUS/FeatureServer/0"
MAX_RECORDS_PER_REQUEST = 2000
REQUEST_DELAY_SECONDS = 1.5  # Be polite to the API
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # Exponential backoff multiplier

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data" / "fairfax" / "building_permits"
RAW_DIR = DATA_DIR / "raw" / "api"
PROCESSED_DIR = DATA_DIR / "processed"

# CRS transformation constants (Virginia State Plane North - EPSG:2283 to WGS84)
# The API uses Virginia State Plane North (feet)
# These are approximate conversion factors for Fairfax County area
VIRGINIA_SP_NORTH_FALSE_EASTING = 11482916.667  # feet
VIRGINIA_SP_NORTH_FALSE_NORTHING = 6561666.667  # feet

# =============================================================================
# PERMIT CATEGORIZATION
# =============================================================================

PERMIT_CATEGORIES = {
    'residential_new': [
        'Residential New',
    ],
    'residential_renovation': [
        'Residential Addition/Alteration',
        'Residential Electrical',
        'Residential Mechanical',
        'Residential Plumbing',
        'Residential Solar',
        'Residential Retaining Wall',
        'Residential Miscellaneous',
    ],
    'residential_demolition': [
        'Residential Demolition',
    ],
    'commercial_new': [
        'Commercial New',
    ],
    'commercial_renovation': [
        'Commercial Addition/Alteration',
        'Commercial Addition-Alteration',
        'Commercial Electrical',
        'Commercial Mechanical',
        'Commercial Plumbing',
        'Commercial Solar',
        'Commercial Retaining Wall',
        'Commercial Miscellaneous',
    ],
    'commercial_demolition': [
        'Commercial Demolition',
    ],
    'certificate': [
        'Certificate of Occupancy',
        'Certificate of Occupancy (Non-RUP)',
    ],
    'elevator': [
        'Elevator Equipment',
        'Elevator Installation Permit',
        'Elevator Maintenance Permit',
    ],
    'other': [
        'Amusement Device',
        'Building Height Certification',
        'Building Permit Amendment',
        'Code Appeal',
        'Code Modification',
        'Critical Structures',
        'Cross Connection',
        'Damage Report',
        'Household Appliance',
        'Masterfile',
        'Separation Permit',
        'Seperation ',
    ]
}

# Create reverse lookup
PERMIT_TYPE_TO_CATEGORY = {}
for category, types in PERMIT_CATEGORIES.items():
    for ptype in types:
        PERMIT_TYPE_TO_CATEGORY[ptype] = category

# High-level categories for analysis
MAJOR_CATEGORIES = {
    'residential': ['residential_new', 'residential_renovation', 'residential_demolition'],
    'commercial': ['commercial_new', 'commercial_renovation', 'commercial_demolition'],
    'other': ['certificate', 'elevator', 'other']
}


def categorize_permit(permit_type: str) -> Tuple[str, str]:
    """
    Categorize a permit type into detailed and major categories.

    Returns:
        Tuple of (detailed_category, major_category)
    """
    detailed = PERMIT_TYPE_TO_CATEGORY.get(permit_type, 'other')

    for major, detailed_list in MAJOR_CATEGORIES.items():
        if detailed in detailed_list:
            return detailed, major

    return detailed, 'other'


# =============================================================================
# GEOMETRY PROCESSING
# =============================================================================

def polygon_centroid(rings: List[List[List[float]]]) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate the centroid of an ArcGIS polygon (in Virginia State Plane coordinates).

    Args:
        rings: ArcGIS polygon rings (list of coordinate arrays)

    Returns:
        Tuple of (x, y) centroid in source CRS, or (None, None) if invalid
    """
    if not rings or not rings[0]:
        return None, None

    # Use the first (outer) ring
    coords = rings[0]
    if len(coords) < 3:
        return None, None

    # Simple centroid calculation (average of vertices)
    # For more accuracy, could use the polygon centroid formula
    x_sum = sum(c[0] for c in coords)
    y_sum = sum(c[1] for c in coords)
    n = len(coords)

    return x_sum / n, y_sum / n


def virginia_sp_to_wgs84(x: float, y: float) -> Tuple[float, float]:
    """
    Convert Virginia State Plane North (EPSG:2283, feet) to WGS84 (EPSG:4326).

    This uses an approximate transformation suitable for Fairfax County.
    For production use, consider using pyproj for exact transformation.

    Args:
        x: Easting in Virginia State Plane feet
        y: Northing in Virginia State Plane feet

    Returns:
        Tuple of (longitude, latitude) in WGS84
    """
    # Approximate transformation parameters for Fairfax County area
    # These are derived from known control points

    # Convert feet to meters
    x_m = x * 0.3048
    y_m = y * 0.3048

    # Approximate transformation (linear for small areas)
    # Central meridian: -77.5, latitude of origin: 38.0
    # Scale factors approximate for Fairfax County

    # Reference point: roughly center of Fairfax County
    # x=11800000 ft, y=7000000 ft -> approximately -77.3, 38.85

    ref_x = 11800000 * 0.3048  # meters
    ref_y = 7000000 * 0.3048   # meters
    ref_lon = -77.3
    ref_lat = 38.85

    # Approximate scale (meters per degree at this latitude)
    meters_per_deg_lon = 85000  # approximate at 39N
    meters_per_deg_lat = 111000  # approximate

    lon = ref_lon + (x_m - ref_x) / meters_per_deg_lon
    lat = ref_lat + (y_m - ref_y) / meters_per_deg_lat

    return lon, lat


def extract_centroid_coords(geometry: Dict) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract centroid coordinates from ArcGIS geometry and convert to WGS84.

    Args:
        geometry: ArcGIS geometry dict with 'rings' for polygons

    Returns:
        Tuple of (longitude, latitude) in WGS84, or (None, None) if invalid
    """
    if not geometry or 'rings' not in geometry:
        return None, None

    x, y = polygon_centroid(geometry['rings'])
    if x is None or y is None:
        return None, None

    return virginia_sp_to_wgs84(x, y)


# =============================================================================
# API CLIENT
# =============================================================================

def fetch_permits_page(
    where_clause: str = "1=1",
    offset: int = 0,
    max_records: int = MAX_RECORDS_PER_REQUEST,
    out_fields: str = "*",
    return_geometry: bool = True
) -> Dict[str, Any]:
    """
    Fetch a single page of permits from the ArcGIS API.

    Args:
        where_clause: SQL WHERE clause for filtering
        offset: Result offset for pagination
        max_records: Maximum records to return
        out_fields: Fields to return (* for all)
        return_geometry: Whether to include geometry

    Returns:
        API response as dict

    Raises:
        requests.RequestException: On API error after retries
    """
    params = {
        'where': where_clause,
        'outFields': out_fields,
        'returnGeometry': 'true' if return_geometry else 'false',
        'resultOffset': offset,
        'resultRecordCount': max_records,
        'f': 'json'
    }

    url = f"{API_BASE_URL}/query"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            # Check for API error
            if 'error' in data:
                raise requests.RequestException(f"API error: {data['error']}")

            return data

        except (requests.RequestException, json.JSONDecodeError) as e:
            wait_time = RETRY_BACKOFF ** attempt
            logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise

    return {}


def fetch_all_permits(
    where_clause: str = "1=1",
    return_geometry: bool = True,
    progress_callback: Optional[callable] = None
) -> List[Dict]:
    """
    Fetch all permits matching the where clause, handling pagination.

    Args:
        where_clause: SQL WHERE clause for filtering
        return_geometry: Whether to include geometry
        progress_callback: Optional callback(current_count, message) for progress

    Returns:
        List of all feature dicts
    """
    all_features = []
    offset = 0

    while True:
        logger.info(f"Fetching permits at offset {offset}...")

        data = fetch_permits_page(
            where_clause=where_clause,
            offset=offset,
            return_geometry=return_geometry
        )

        features = data.get('features', [])

        if not features:
            break

        all_features.extend(features)

        if progress_callback:
            progress_callback(len(all_features), f"Downloaded {len(all_features)} permits...")

        logger.info(f"Downloaded {len(all_features)} permits so far...")

        # Check if we've reached the end
        if len(features) < MAX_RECORDS_PER_REQUEST:
            break

        offset += MAX_RECORDS_PER_REQUEST

        # Be polite to the API
        time.sleep(REQUEST_DELAY_SECONDS)

    return all_features


def get_record_count(where_clause: str = "1=1") -> int:
    """Get the total count of records matching the where clause."""
    params = {
        'where': where_clause,
        'returnCountOnly': 'true',
        'f': 'json'
    }

    url = f"{API_BASE_URL}/query"
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    return data.get('count', 0)


# =============================================================================
# DATA PROCESSING
# =============================================================================

def parse_timestamp(ts: Optional[int]) -> Optional[datetime]:
    """Convert ArcGIS timestamp (milliseconds since epoch) to datetime."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000)
    except (ValueError, OSError):
        return None


def process_features(features: List[Dict]) -> pd.DataFrame:
    """
    Process raw API features into a structured DataFrame.

    Args:
        features: List of feature dicts from API

    Returns:
        Processed DataFrame
    """
    records = []

    for feature in features:
        attrs = feature.get('attributes', {})
        geometry = feature.get('geometry')

        # Extract centroid
        centroid_lon, centroid_lat = extract_centroid_coords(geometry)

        # Categorize permit
        permit_type = attrs.get('APPTYPEALIAS', '')
        detailed_category, major_category = categorize_permit(permit_type)

        # Parse dates
        submitted_date = parse_timestamp(attrs.get('SUBMITTED_DATE'))
        accepted_date = parse_timestamp(attrs.get('ACCEPTED_DATE'))
        issued_date = parse_timestamp(attrs.get('ISSUED_DATE'))
        closed_date = parse_timestamp(attrs.get('CLOSED_DATE'))
        approved_date = parse_timestamp(attrs.get('APPROVED_DATE'))

        record = {
            'permit_id': attrs.get('RECORDID'),
            'permit_type': permit_type,
            'permit_category': detailed_category,
            'permit_major_category': major_category,
            'project_name': attrs.get('PROJECT_NAME'),
            'status': attrs.get('RECORD_STATUS'),
            'parcel_id': attrs.get('PARCEL_ID'),
            'address': attrs.get('MAR_ADDRESS') or attrs.get('ADDRESS_1'),
            'address_1': attrs.get('ADDRESS_1'),
            'address_2': attrs.get('ADDRESS_2'),
            'city': attrs.get('CITY'),
            'state': attrs.get('STATE'),
            'zip_code': attrs.get('ZIP_CODE'),
            'submitted_date': submitted_date,
            'accepted_date': accepted_date,
            'issued_date': issued_date,
            'closed_date': closed_date,
            'approved_date': approved_date,
            'supervisor_district': attrs.get('SUPERVISOR_DISTRICT'),
            'development_center': attrs.get('DEVELOPMENT_CENTER'),
            'document_url': attrs.get('DOCUMENT_URL'),
            'link_url': attrs.get('LINK_URL'),
            'centroid_lon': centroid_lon,
            'centroid_lat': centroid_lat,
            'has_geometry': geometry is not None and 'rings' in (geometry or {}),
            'ingestion_date': datetime.now()
        }

        records.append(record)

    df = pd.DataFrame(records)

    # Convert date columns
    date_cols = ['submitted_date', 'accepted_date', 'issued_date', 'closed_date', 'approved_date', 'ingestion_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    return df


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in miles.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def get_permits_near_point(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    radius_miles: float = 1.0
) -> pd.DataFrame:
    """
    Get permits within a radius of a point.

    Args:
        df: Permits DataFrame with centroid_lat, centroid_lon
        lat: Center point latitude
        lon: Center point longitude
        radius_miles: Search radius in miles

    Returns:
        Filtered DataFrame with distance column
    """
    # Filter to permits with coordinates
    df_geo = df.dropna(subset=['centroid_lat', 'centroid_lon']).copy()

    if df_geo.empty:
        return df_geo

    # Calculate distances
    df_geo['distance_miles'] = df_geo.apply(
        lambda row: haversine_distance(lat, lon, row['centroid_lat'], row['centroid_lon']),
        axis=1
    )

    # Filter by radius
    return df_geo[df_geo['distance_miles'] <= radius_miles].sort_values('distance_miles')


def calculate_development_pressure(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    radius_miles: float = 1.0,
    lookback_months: int = 24
) -> Dict[str, Any]:
    """
    Calculate a development pressure score for an area.

    Higher scores indicate more development activity.

    Args:
        df: Permits DataFrame
        lat: Center point latitude
        lon: Center point longitude
        radius_miles: Search radius in miles
        lookback_months: How many months back to consider

    Returns:
        Dict with score (0-100) and breakdown
    """
    # Get nearby permits
    nearby = get_permits_near_point(df, lat, lon, radius_miles)

    if nearby.empty:
        return {
            'score': 0,
            'total_permits': 0,
            'breakdown': {},
            'trend': 'no_data'
        }

    # Filter to recent permits
    cutoff_date = datetime.now() - timedelta(days=lookback_months * 30)

    # Use issued_date preferentially, fall back to submitted_date
    recent = nearby[
        (nearby['issued_date'] >= cutoff_date) |
        ((nearby['issued_date'].isna()) & (nearby['submitted_date'] >= cutoff_date))
    ]

    # Weight by permit type
    weights = {
        'residential_new': 10,
        'commercial_new': 15,
        'residential_renovation': 3,
        'commercial_renovation': 5,
        'residential_demolition': 8,  # Often precedes new construction
        'commercial_demolition': 10,
        'certificate': 2,
        'elevator': 1,
        'other': 1
    }

    # Calculate weighted score
    weighted_sum = 0
    breakdown = {}

    for category in PERMIT_CATEGORIES.keys():
        count = len(recent[recent['permit_category'] == category])
        weight = weights.get(category, 1)
        weighted_sum += count * weight
        if count > 0:
            breakdown[category] = {
                'count': count,
                'weight': weight,
                'contribution': count * weight
            }

    # Normalize score (0-100)
    # Calibrated so ~50 weighted points = score of 50
    score = min(100, int(weighted_sum * 1.0))

    # Calculate trend (compare first half vs second half of period)
    mid_date = cutoff_date + timedelta(days=lookback_months * 15)
    first_half = len(recent[recent['issued_date'] < mid_date])
    second_half = len(recent[recent['issued_date'] >= mid_date])

    if first_half == 0 and second_half == 0:
        trend = 'no_activity'
    elif first_half == 0:
        trend = 'increasing'
    elif second_half == 0:
        trend = 'decreasing'
    elif second_half > first_half * 1.2:
        trend = 'increasing'
    elif second_half < first_half * 0.8:
        trend = 'decreasing'
    else:
        trend = 'stable'

    return {
        'score': score,
        'total_permits': len(recent),
        'breakdown': breakdown,
        'trend': trend,
        'lookback_months': lookback_months,
        'radius_miles': radius_miles
    }


def get_permit_trends(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    radius_miles: float = 1.0
) -> Dict[str, Any]:
    """
    Get permit trends over time for an area.

    Args:
        df: Permits DataFrame
        lat: Center point latitude
        lon: Center point longitude
        radius_miles: Search radius in miles

    Returns:
        Dict with yearly counts and trends
    """
    nearby = get_permits_near_point(df, lat, lon, radius_miles)

    if nearby.empty:
        return {'yearly': {}, 'by_category': {}}

    # Add year column
    nearby = nearby.copy()
    nearby['year'] = nearby['issued_date'].dt.year

    # Yearly counts
    yearly = nearby.groupby('year').size().to_dict()

    # By category per year
    by_category = nearby.groupby(['year', 'permit_major_category']).size().unstack(fill_value=0).to_dict('index')

    return {
        'yearly': yearly,
        'by_category': by_category
    }


# =============================================================================
# STORAGE
# =============================================================================

def save_permits(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save permits DataFrame to Parquet file.

    Args:
        df: Permits DataFrame
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert datetime columns for Parquet
    df_copy = df.copy()

    # Save to Parquet
    df_copy.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)

    logger.info(f"Saved {len(df)} permits to {output_path}")


def create_metadata(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create metadata dict for the permits dataset.

    Args:
        df: Permits DataFrame

    Returns:
        Metadata dict
    """
    # Count by category
    by_category = df['permit_major_category'].value_counts().to_dict()
    by_detailed_category = df['permit_category'].value_counts().to_dict()

    # Count by year (using issued_date)
    df_with_year = df.dropna(subset=['issued_date']).copy()
    df_with_year['year'] = df_with_year['issued_date'].dt.year
    by_year = df_with_year['year'].value_counts().sort_index().to_dict()
    by_year = {str(int(k)): v for k, v in by_year.items()}

    # Count by status
    by_status = df['status'].value_counts().to_dict()

    # Geometry stats
    has_geometry = df['has_geometry'].sum()
    has_centroid = df['centroid_lat'].notna().sum()

    # Parcel linkage
    has_parcel = df['parcel_id'].notna().sum()

    # Date range
    min_date = df['issued_date'].min()
    max_date = df['issued_date'].max()

    return {
        'last_updated': datetime.now().isoformat(),
        'total_permits': len(df),
        'date_range': {
            'min': min_date.strftime('%Y-%m-%d') if pd.notna(min_date) else None,
            'max': max_date.strftime('%Y-%m-%d') if pd.notna(max_date) else None
        },
        'by_major_category': by_category,
        'by_detailed_category': by_detailed_category,
        'by_year': by_year,
        'by_status': dict(list(by_status.items())[:10]),  # Top 10 statuses
        'geometry': {
            'has_polygon': int(has_geometry),
            'has_centroid': int(has_centroid),
            'pct_geocoded': round(has_centroid / len(df) * 100, 1) if len(df) > 0 else 0
        },
        'parcel_linkage': {
            'has_parcel_id': int(has_parcel),
            'pct_linked': round(has_parcel / len(df) * 100, 1) if len(df) > 0 else 0
        }
    }


def save_metadata(metadata: Dict, output_path: Path) -> None:
    """Save metadata to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved metadata to {output_path}")


# =============================================================================
# MAIN ETL FUNCTIONS
# =============================================================================

def run_full_etl(
    start_year: int = 2022,
    end_year: int = 2026,
    test_mode: bool = False
) -> pd.DataFrame:
    """
    Run the full ETL pipeline.

    Args:
        start_year: Start year for data (inclusive)
        end_year: End year for data (inclusive)
        test_mode: If True, only download 100 records

    Returns:
        Processed DataFrame
    """
    logger.info(f"Starting Fairfax Building Permits ETL ({start_year}-{end_year})")

    # Build where clause
    where_clause = f"ISSUED_DATE >= DATE '{start_year}-01-01'"

    # Get count first
    total_count = get_record_count(where_clause)
    logger.info(f"Total permits matching filter: {total_count:,}")

    if test_mode:
        logger.info("TEST MODE: Limiting to 100 records")
        where_clause += " AND OBJECTID < 100"

    # Fetch all permits
    logger.info("Downloading permits from API...")
    start_time = time.time()

    features = fetch_all_permits(where_clause=where_clause)

    download_time = time.time() - start_time
    logger.info(f"Downloaded {len(features):,} permits in {download_time:.1f} seconds")

    # Process features
    logger.info("Processing permit data...")
    df = process_features(features)

    # Save to parquet
    output_path = PROCESSED_DIR / "permits.parquet"
    save_permits(df, output_path)

    # Create and save metadata
    metadata = create_metadata(df)
    metadata_path = PROCESSED_DIR / "metadata.json"
    save_metadata(metadata, metadata_path)

    # Print summary
    print_summary(df, metadata)

    return df


def run_incremental_update(days: int = 7) -> pd.DataFrame:
    """
    Run an incremental update for recent permits.

    Args:
        days: Number of days back to fetch

    Returns:
        Updated DataFrame
    """
    logger.info(f"Running incremental update for last {days} days")

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    where_clause = f"ISSUED_DATE >= DATE '{cutoff_date}'"

    # Get new permits
    features = fetch_all_permits(where_clause=where_clause)
    new_df = process_features(features)

    # Load existing data
    existing_path = PROCESSED_DIR / "permits.parquet"
    if existing_path.exists():
        existing_df = pd.read_parquet(existing_path)

        # Remove any existing records that will be updated
        existing_df = existing_df[~existing_df['permit_id'].isin(new_df['permit_id'])]

        # Combine
        df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        df = new_df

    # Save
    save_permits(df, existing_path)

    # Update metadata
    metadata = create_metadata(df)
    save_metadata(metadata, PROCESSED_DIR / "metadata.json")

    logger.info(f"Added/updated {len(new_df):,} permits. Total: {len(df):,}")

    return df


def print_summary(df: pd.DataFrame, metadata: Dict) -> None:
    """Print a formatted summary of the ETL results."""
    print("\n" + "=" * 60)
    print("FAIRFAX BUILDING PERMITS - ETL COMPLETE")
    print("=" * 60)

    print(f"\nDownloaded:            {metadata['total_permits']:,} permits")
    print(f"Date Range:            {metadata['date_range']['min']} to {metadata['date_range']['max']}")

    # File size
    output_path = PROCESSED_DIR / "permits.parquet"
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"File Size:             {size_mb:.1f} MB")

    print("\nBy Major Category:")
    for cat, count in metadata['by_major_category'].items():
        pct = count / metadata['total_permits'] * 100
        print(f"  {cat.capitalize():20} {count:,} ({pct:.1f}%)")

    print("\nBy Year:")
    for year, count in sorted(metadata['by_year'].items()):
        print(f"  {year}:                {count:,}")

    print("\nBy Status (Top 5):")
    for status, count in list(metadata['by_status'].items())[:5]:
        print(f"  {status[:25]:25} {count:,}")

    print("\nGeometry:")
    geo = metadata['geometry']
    print(f"  Valid polygons:      {geo['has_polygon']:,} ({geo['pct_geocoded']:.1f}%)")
    print(f"  Centroids extracted: {geo['has_centroid']:,} ({geo['pct_geocoded']:.1f}%)")

    print("\nParcel Linkage:")
    parcel = metadata['parcel_linkage']
    print(f"  Matched:             {parcel['has_parcel_id']:,} ({parcel['pct_linked']:.1f}%)")

    ready = geo['pct_geocoded'] > 90 and parcel['pct_linked'] > 50
    print(f"\nReady for Development Pressure Analysis: {'YES' if ready else 'NEEDS REVIEW'}")
    print("=" * 60 + "\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fairfax County Building Permits ETL Pipeline"
    )
    parser.add_argument(
        '--recent',
        action='store_true',
        help='Only fetch permits from last 30 days (incremental update)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: download only 100 records'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2022,
        help='Start year for full download (default: 2022)'
    )
    parser.add_argument(
        '--analyze',
        nargs=2,
        type=float,
        metavar=('LAT', 'LON'),
        help='Run analysis for a location (lat lon)'
    )

    args = parser.parse_args()

    if args.analyze:
        # Load existing data and run analysis
        lat, lon = args.analyze
        df = pd.read_parquet(PROCESSED_DIR / "permits.parquet")

        print(f"\nAnalysis for location ({lat}, {lon}):")

        # Get nearby permits
        nearby = get_permits_near_point(df, lat, lon, radius_miles=1.0)
        print(f"\nPermits within 1 mile: {len(nearby)}")

        if not nearby.empty:
            print("\nRecent permits:")
            cols = ['permit_id', 'permit_type', 'status', 'issued_date', 'address', 'distance_miles']
            print(nearby[cols].head(10).to_string())

        # Development pressure
        pressure = calculate_development_pressure(df, lat, lon)
        print(f"\nDevelopment Pressure Score: {pressure['score']}/100")
        print(f"Trend: {pressure['trend']}")
        print(f"Total permits (last 24 months): {pressure['total_permits']}")

    elif args.recent:
        run_incremental_update(days=30)
    else:
        run_full_etl(start_year=args.start_year, test_mode=args.test)


if __name__ == "__main__":
    main()
