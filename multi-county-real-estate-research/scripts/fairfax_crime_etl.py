"""
Fairfax County Crime Data ETL Pipeline.

Fetches crime data from:
1. Weekly API (rolling 7-9 days of current data)
2. FBI NIBRS (historical data - manual download required)

Combines into unified incidents.parquet dataset.

Usage:
    python scripts/fairfax_crime_etl.py --fetch-weekly
    python scripts/fairfax_crime_etl.py --process-fbi
    python scripts/fairfax_crime_etl.py --full-refresh
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from io import StringIO

import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    # Weekly API endpoint
    'weekly_api_url': 'https://www.fairfaxcounty.gov/apps/pfsu/api/file/crimereportsfromsp',

    # Paths
    'base_dir': Path(__file__).parent.parent / 'data' / 'fairfax' / 'crime',
    'raw_weekly_dir': Path(__file__).parent.parent / 'data' / 'fairfax' / 'crime' / 'raw' / 'weekly',
    'raw_fbi_dir': Path(__file__).parent.parent / 'data' / 'fairfax' / 'crime' / 'raw' / 'fbi',
    'geocoded_dir': Path(__file__).parent.parent / 'data' / 'fairfax' / 'crime' / 'raw' / 'geocoded',
    'processed_dir': Path(__file__).parent.parent / 'data' / 'fairfax' / 'crime' / 'processed',

    # Weekly API CSV columns (no header in response)
    'weekly_columns': ['count', 'code', 'description', 'date', 'time', 'address', 'city', 'state', 'zip'],

    # Unified schema
    'unified_schema': [
        'incident_id',      # Unique identifier
        'crime_code',       # Crime classification code
        'description',      # Human-readable description
        'category',         # VIOLENT, PROPERTY, OTHER
        'date',             # Date of incident
        'time',             # Time of incident (HHMM)
        'address',          # Location (100-block anonymized)
        'city',             # City/area
        'state',            # State (VA)
        'zip',              # ZIP code
        'latitude',         # Geocoded latitude (if available)
        'longitude',        # Geocoded longitude (if available)
        'source',           # Data source (weekly_api, fbi_nibrs)
        'ingestion_date',   # When record was ingested
    ],

    # Crime category classification
    'violent_codes': ['ASSLT', 'ROB', 'HOMICIDE', 'RAPE', 'KIDNAP', 'MURDER'],
    'property_codes': ['LARC', 'BURG', 'AUTO', 'DEST', 'FRAUD', 'FORG', 'THEFT', 'ARSON'],

    # Retry settings
    'max_retries': 3,
    'retry_delay_seconds': 2,
}


# ============================================================================
# WEEKLY API FUNCTIONS
# ============================================================================

def fetch_weekly_crimes(save_raw: bool = True) -> pd.DataFrame:
    """
    Fetch current week's crime data from Fairfax County API.

    Args:
        save_raw: If True, save raw CSV to dated file

    Returns:
        DataFrame with parsed crime incidents
    """
    logger.info(f"Fetching weekly crime data from API...")

    url = CONFIG['weekly_api_url']

    for attempt in range(CONFIG['max_retries']):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt < CONFIG['max_retries'] - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                import time
                time.sleep(CONFIG['retry_delay_seconds'] * (attempt + 1))
            else:
                logger.error(f"Failed to fetch data after {CONFIG['max_retries']} attempts")
                raise

    # Save raw CSV if requested
    if save_raw:
        raw_dir = CONFIG['raw_weekly_dir']
        raw_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime('%Y-%m-%d')
        raw_file = raw_dir / f'weekly_{today}.csv'

        with open(raw_file, 'w') as f:
            f.write(response.text)
        logger.info(f"Saved raw data to {raw_file}")

    # Parse CSV
    df = pd.read_csv(
        StringIO(response.text),
        names=CONFIG['weekly_columns'],
        header=None,
        on_bad_lines='skip'
    )

    logger.info(f"Fetched {len(df)} incidents")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")

    return df


def transform_weekly_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform weekly API data to unified schema.

    Args:
        df: Raw DataFrame from weekly API

    Returns:
        DataFrame in unified schema
    """
    logger.info("Transforming weekly data to unified schema...")

    # Create copy
    unified = df.copy()

    # Extract code prefix for categorization
    unified['code_prefix'] = unified['code'].str.split('-').str[0]

    # Classify crime category
    unified['category'] = 'OTHER'
    unified.loc[unified['code_prefix'].isin(CONFIG['violent_codes']), 'category'] = 'VIOLENT'
    unified.loc[unified['code_prefix'].isin(CONFIG['property_codes']), 'category'] = 'PROPERTY'

    # Create incident ID (composite key for deduplication)
    unified['incident_id'] = (
        unified['date'].astype(str) + '_' +
        unified['time'].astype(str) + '_' +
        unified['code'].astype(str) + '_' +
        unified['address'].astype(str).str[:20]  # First 20 chars of address
    )

    # Rename columns
    unified = unified.rename(columns={'code': 'crime_code'})

    # Add metadata
    unified['latitude'] = None
    unified['longitude'] = None
    unified['source'] = 'weekly_api'
    unified['ingestion_date'] = datetime.now().strftime('%Y-%m-%d')

    # Select and order columns
    output_cols = [
        'incident_id', 'crime_code', 'description', 'category',
        'date', 'time', 'address', 'city', 'state', 'zip',
        'latitude', 'longitude', 'source', 'ingestion_date'
    ]

    # Ensure all columns exist
    for col in output_cols:
        if col not in unified.columns:
            unified[col] = None

    unified = unified[output_cols]

    logger.info(f"Transformed {len(unified)} records")

    return unified


# ============================================================================
# FBI NIBRS FUNCTIONS
# ============================================================================

def get_fbi_download_instructions() -> str:
    """
    Return instructions for downloading FBI NIBRS data.

    FBI Crime Data Explorer doesn't have a simple bulk download API,
    so we provide manual instructions.
    """
    instructions = """
    ═══════════════════════════════════════════════════════════════════════
    FBI NIBRS DATA DOWNLOAD INSTRUCTIONS
    ═══════════════════════════════════════════════════════════════════════

    FBI Crime Data Explorer doesn't provide a simple bulk download API.
    Follow these steps to download historical data:

    1. Go to: https://cde.ucr.cjis.gov/

    2. Click "Downloads" in the navigation

    3. For NIBRS Data:
       - Select "NIBRS" tab
       - Choose years: 2019, 2020, 2021, 2022, 2023, 2024
       - Select state: Virginia
       - Download each year's ZIP file

    4. For Agency-Level Data:
       - Alternatively, go to "Explore" → "State" → "Virginia"
       - Find "Fairfax County Police Department" (ORI: VA0590000)
       - Also check: Fairfax City Police (VA0590200)
       - Download agency-specific data

    5. Place downloaded files in:
       data/fairfax/crime/raw/fbi/

    6. Expected file structure:
       raw/fbi/
       ├── nibrs_2019.zip
       ├── nibrs_2020.zip
       ├── nibrs_2021.zip
       ├── nibrs_2022.zip
       ├── nibrs_2023.zip
       └── nibrs_2024.zip

    7. Run: python scripts/fairfax_crime_etl.py --process-fbi

    ═══════════════════════════════════════════════════════════════════════

    ALTERNATIVE: FBI Crime Data API

    The FBI also provides an API, but it requires registration:
    - API Docs: https://crime-data-explorer.fr.cloud.gov/api
    - Rate limits apply
    - Registration required for API key

    For initial setup, manual download is recommended.

    ═══════════════════════════════════════════════════════════════════════
    """
    return instructions


def process_fbi_data() -> Optional[pd.DataFrame]:
    """
    Process FBI NIBRS data files if available.

    Returns:
        DataFrame with FBI data in unified schema, or None if no files found
    """
    fbi_dir = CONFIG['raw_fbi_dir']

    if not fbi_dir.exists():
        logger.warning(f"FBI data directory not found: {fbi_dir}")
        print(get_fbi_download_instructions())
        return None

    # Look for ZIP or CSV files
    zip_files = list(fbi_dir.glob('*.zip'))
    csv_files = list(fbi_dir.glob('*.csv'))

    if not zip_files and not csv_files:
        logger.warning("No FBI data files found")
        print(get_fbi_download_instructions())
        return None

    logger.info(f"Found {len(zip_files)} ZIP files and {len(csv_files)} CSV files")

    # TODO: Implement FBI NIBRS parsing when files are available
    # The FBI NIBRS format is complex with multiple related tables
    # This is a placeholder for when data is downloaded

    logger.info("FBI data processing: Awaiting file download")
    print(get_fbi_download_instructions())

    return None


# ============================================================================
# GEOCODING FUNCTIONS
# ============================================================================

def load_geocode_cache() -> pd.DataFrame:
    """Load existing geocoding cache."""
    cache_file = CONFIG['geocoded_dir'] / 'address_cache.parquet'

    if cache_file.exists():
        return pd.read_parquet(cache_file)
    else:
        return pd.DataFrame(columns=['address', 'latitude', 'longitude', 'quality', 'geocoded_date'])


def save_geocode_cache(cache_df: pd.DataFrame):
    """Save geocoding cache."""
    cache_dir = CONFIG['geocoded_dir']
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_file = cache_dir / 'address_cache.parquet'
    cache_df.to_parquet(cache_file, index=False)
    logger.info(f"Saved geocode cache with {len(cache_df)} addresses")


def geocode_address_census(address: str, city: str, state: str, zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address using Census Bureau Geocoder (free, no API key).

    Note: This is a single-address lookup. For batch processing,
    use the Census batch geocoder upload.

    Args:
        address: Street address
        city: City name
        state: State abbreviation
        zip_code: ZIP code

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    # Build full address
    full_address = f"{address}, {city}, {state} {zip_code}"

    # Census Geocoder API
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        'address': full_address,
        'benchmark': 'Public_AR_Current',
        'format': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        matches = data.get('result', {}).get('addressMatches', [])

        if matches:
            coords = matches[0]['coordinates']
            return (coords['y'], coords['x'])  # lat, lon
        else:
            return None

    except Exception as e:
        logger.debug(f"Geocoding failed for {full_address}: {e}")
        return None


def geocode_address_google(address: str, city: str, state: str, zip_code: str) -> Optional[Tuple[float, float]]:
    """
    Geocode an address using Google Maps Geocoding API (fallback).

    Requires GOOGLE_MAPS_API_KEY in environment or .env file.

    Args:
        address: Street address
        city: City name
        state: State abbreviation
        zip_code: ZIP code

    Returns:
        Tuple of (latitude, longitude) or None if geocoding fails
    """
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from core.api_config import get_api_key
            api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        except Exception:
            pass

    if not api_key:
        return None

    full_address = f"{address}, {city}, {state} {zip_code}"

    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': full_address,
            'key': api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get('status') != 'OK' or not data.get('results'):
            return None

        location = data['results'][0]['geometry']['location']
        lat, lon = location['lat'], location['lng']

        # Validate coordinates are in Virginia area
        if 36.5 <= lat <= 39.5 and -83.7 <= lon <= -75.2:
            return (lat, lon)
        else:
            logger.debug(f"Google Maps returned out-of-bounds coords for {full_address}")
            return None

    except Exception as e:
        logger.debug(f"Google Maps geocoding failed for {full_address}: {e}")
        return None


def geocode_incidents(df: pd.DataFrame, max_geocode: int = 500) -> pd.DataFrame:
    """
    Geocode addresses in incident DataFrame.

    Uses cache to avoid redundant API calls.

    Args:
        df: DataFrame with address, city, state, zip columns
        max_geocode: Maximum new addresses to geocode per run

    Returns:
        DataFrame with latitude/longitude filled where possible
    """
    logger.info("Geocoding incident addresses...")

    # Load cache
    cache = load_geocode_cache()
    cached_addresses = set(cache['address'].tolist()) if len(cache) > 0 else set()

    # Get unique addresses to geocode - ensure string types
    df['full_address'] = (
        df['address'].astype(str).fillna('') + ', ' +
        df['city'].astype(str).fillna('') + ', ' +
        df['state'].astype(str).fillna('') + ' ' +
        df['zip'].astype(str).fillna('')
    )

    unique_addresses = df['full_address'].unique()
    new_addresses = [a for a in unique_addresses if a not in cached_addresses]

    logger.info(f"Total unique addresses: {len(unique_addresses)}")
    logger.info(f"Already cached: {len(unique_addresses) - len(new_addresses)}")
    logger.info(f"New to geocode: {len(new_addresses)}")

    # Geocode new addresses (limited per run)
    geocoded_count = 0
    google_count = 0
    new_cache_entries = []

    for address in new_addresses[:max_geocode]:
        # Parse address components (basic parsing)
        parts = address.split(',')
        if len(parts) >= 3:
            street = parts[0].strip()
            city = parts[1].strip()
            state_zip = parts[2].strip().split()
            state = state_zip[0] if state_zip else 'VA'
            zip_code = state_zip[1] if len(state_zip) > 1 else ''

            # Try Census geocoder first (free, no API key)
            coords = geocode_address_census(street, city, state, zip_code)
            source = 'census'

            # Fall back to Google Maps if Census fails
            if not coords:
                coords = geocode_address_google(street, city, state, zip_code)
                source = 'google'

            if coords:
                new_cache_entries.append({
                    'address': address,
                    'latitude': coords[0],
                    'longitude': coords[1],
                    'quality': f'matched_{source}',
                    'geocoded_date': datetime.now().strftime('%Y-%m-%d')
                })
                geocoded_count += 1
                if source == 'google':
                    google_count += 1
            else:
                new_cache_entries.append({
                    'address': address,
                    'latitude': None,
                    'longitude': None,
                    'quality': 'not_found',
                    'geocoded_date': datetime.now().strftime('%Y-%m-%d')
                })

    logger.info(f"Geocoded {geocoded_count} new addresses (Census: {geocoded_count - google_count}, Google: {google_count})")

    # Update cache
    if new_cache_entries:
        new_cache_df = pd.DataFrame(new_cache_entries)
        cache = pd.concat([cache, new_cache_df], ignore_index=True)
        save_geocode_cache(cache)

    # Merge geocoded coordinates back to incidents
    df = df.merge(
        cache[['address', 'latitude', 'longitude']].rename(
            columns={'address': 'full_address', 'latitude': 'geo_lat', 'longitude': 'geo_lon'}
        ),
        on='full_address',
        how='left'
    )

    # Update lat/lon columns
    df['latitude'] = df['geo_lat']
    df['longitude'] = df['geo_lon']

    # Clean up
    df = df.drop(columns=['full_address', 'geo_lat', 'geo_lon'], errors='ignore')

    geocoded_pct = (df['latitude'].notna().sum() / len(df)) * 100
    logger.info(f"Geocoding coverage: {geocoded_pct:.1f}%")

    return df


# ============================================================================
# STORAGE AND DEDUPLICATION
# ============================================================================

def load_existing_incidents() -> pd.DataFrame:
    """Load existing incidents from processed Parquet file."""
    incidents_file = CONFIG['processed_dir'] / 'incidents.parquet'

    if incidents_file.exists():
        return pd.read_parquet(incidents_file)
    else:
        return pd.DataFrame()


def save_incidents(df: pd.DataFrame):
    """Save incidents to processed Parquet file."""
    processed_dir = CONFIG['processed_dir']
    processed_dir.mkdir(parents=True, exist_ok=True)

    incidents_file = processed_dir / 'incidents.parquet'
    df.to_parquet(incidents_file, index=False)

    logger.info(f"Saved {len(df)} incidents to {incidents_file}")

    # Update metadata
    update_metadata(df)


def deduplicate_incidents(new_df: pd.DataFrame, existing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate new incidents against existing data.

    Args:
        new_df: New incidents to add
        existing_df: Existing incidents

    Returns:
        Combined DataFrame with duplicates removed
    """
    if len(existing_df) == 0:
        logger.info(f"No existing data. Adding all {len(new_df)} new incidents.")
        return new_df

    existing_ids = set(existing_df['incident_id'].tolist())
    new_unique = new_df[~new_df['incident_id'].isin(existing_ids)]

    duplicates_found = len(new_df) - len(new_unique)
    logger.info(f"Found {duplicates_found} duplicate incidents (skipped)")
    logger.info(f"Adding {len(new_unique)} new unique incidents")

    combined = pd.concat([existing_df, new_unique], ignore_index=True)
    combined = combined.sort_values('date').reset_index(drop=True)

    return combined


def update_metadata(df: pd.DataFrame):
    """Update metadata.json with current dataset statistics."""
    metadata_file = CONFIG['processed_dir'] / 'metadata.json'

    metadata = {
        'last_updated': datetime.now().isoformat(),
        'total_incidents': len(df),
        'date_range': {
            'min': str(df['date'].min()),
            'max': str(df['date'].max())
        },
        'sources': df['source'].value_counts().to_dict(),
        'categories': df['category'].value_counts().to_dict(),
        'geocoding': {
            'total': len(df),
            'geocoded': int(df['latitude'].notna().sum()),
            'pct_geocoded': round((df['latitude'].notna().sum() / len(df)) * 100, 1)
        },
        'cities': df['city'].value_counts().head(10).to_dict()
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Updated metadata: {metadata_file}")


# ============================================================================
# MAIN ETL FUNCTIONS
# ============================================================================

def run_weekly_etl(geocode: bool = True, max_geocode: int = 100):
    """
    Run weekly API ETL pipeline.

    1. Fetch weekly data
    2. Transform to unified schema
    3. Geocode new addresses
    4. Deduplicate and append
    5. Save to Parquet
    """
    logger.info("=" * 60)
    logger.info("STARTING WEEKLY ETL PIPELINE")
    logger.info("=" * 60)

    # Fetch
    raw_df = fetch_weekly_crimes(save_raw=True)

    # Transform
    unified_df = transform_weekly_to_unified(raw_df)

    # Geocode
    if geocode:
        unified_df = geocode_incidents(unified_df, max_geocode=max_geocode)

    # Load existing and deduplicate
    existing_df = load_existing_incidents()
    combined_df = deduplicate_incidents(unified_df, existing_df)

    # Save
    save_incidents(combined_df)

    # Summary
    print_summary(combined_df)

    logger.info("WEEKLY ETL COMPLETE")

    return combined_df


def run_full_refresh(geocode: bool = True, max_geocode: int = 500):
    """
    Run full refresh: FBI historical + Weekly current.
    """
    logger.info("=" * 60)
    logger.info("STARTING FULL REFRESH PIPELINE")
    logger.info("=" * 60)

    all_incidents = []

    # Process FBI data if available
    fbi_df = process_fbi_data()
    if fbi_df is not None:
        all_incidents.append(fbi_df)

    # Fetch weekly data
    raw_df = fetch_weekly_crimes(save_raw=True)
    unified_df = transform_weekly_to_unified(raw_df)
    all_incidents.append(unified_df)

    # Combine
    if all_incidents:
        combined_df = pd.concat(all_incidents, ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['incident_id'])
        combined_df = combined_df.sort_values('date').reset_index(drop=True)

        # Geocode
        if geocode:
            combined_df = geocode_incidents(combined_df, max_geocode=max_geocode)

        # Save
        save_incidents(combined_df)

        # Summary
        print_summary(combined_df)

        return combined_df

    return None


def print_summary(df: pd.DataFrame):
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("FAIRFAX CRIME DATA PIPELINE - SUMMARY")
    print("=" * 60)

    print(f"\nTotal Incidents: {len(df):,}")
    print(f"Date Range: {df['date'].min()} to {df['date'].max()}")

    print("\nBy Source:")
    for source, count in df['source'].value_counts().items():
        pct = 100 * count / len(df)
        print(f"  {source}: {count:,} ({pct:.1f}%)")

    print("\nBy Category:")
    for cat, count in df['category'].value_counts().items():
        pct = 100 * count / len(df)
        print(f"  {cat}: {count:,} ({pct:.1f}%)")

    geocoded = df['latitude'].notna().sum()
    geo_pct = 100 * geocoded / len(df)
    print(f"\nGeocoding: {geocoded:,} / {len(df):,} ({geo_pct:.1f}%)")

    print(f"\nTop 5 Cities:")
    for city, count in df['city'].value_counts().head(5).items():
        print(f"  {city}: {count:,}")

    print("\n" + "=" * 60)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Fairfax County Crime Data ETL')
    parser.add_argument('--fetch-weekly', action='store_true',
                        help='Fetch weekly API data and append to dataset')
    parser.add_argument('--process-fbi', action='store_true',
                        help='Process FBI NIBRS data files')
    parser.add_argument('--full-refresh', action='store_true',
                        help='Full refresh: FBI + Weekly')
    parser.add_argument('--no-geocode', action='store_true',
                        help='Skip geocoding step')
    parser.add_argument('--max-geocode', type=int, default=500,
                        help='Maximum addresses to geocode per run (default: 500)')
    parser.add_argument('--show-fbi-instructions', action='store_true',
                        help='Show FBI data download instructions')

    args = parser.parse_args()

    geocode = not args.no_geocode

    if args.show_fbi_instructions:
        print(get_fbi_download_instructions())
        return

    if args.fetch_weekly:
        run_weekly_etl(geocode=geocode, max_geocode=args.max_geocode)
    elif args.process_fbi:
        process_fbi_data()
    elif args.full_refresh:
        run_full_refresh(geocode=geocode, max_geocode=args.max_geocode)
    else:
        # Default: run weekly ETL
        run_weekly_etl(geocode=geocode, max_geocode=args.max_geocode)


if __name__ == '__main__':
    main()
