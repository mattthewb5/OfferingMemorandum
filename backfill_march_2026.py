#!/usr/bin/env python3
"""
One-time backfill script for Fairfax crime and building permits data.

Covers the gap from March 3-9, 2026 when GitHub Actions scheduled
workflows were not firing.

IMPORTANT — Crime API limitation:
The Fairfax crime API (crimereportsfromsp) returns a ROLLING WINDOW of
the most recent ~7-9 days. It does NOT support date-range queries. This
means we cannot fetch historical day-by-day data. However:

  - The Mar 7 manual dispatch already captured incidents dated Mar 1-7
    (820 records ingested that day, covering the rolling window).
  - This script fetches the CURRENT rolling window (roughly Mar 2-10
    as of today), deduplicates against existing data, and adds any new
    incidents — primarily Mar 8-9 data that no run ever captured.

For permits, the ArcGIS API supports date-range queries, so we fetch
all permits issued since Feb 1, 2026 (wider than the gap to catch
anything the Mar 2 incremental run might have missed).

Usage:
    # Dry run — show what would change without writing
    python backfill_march_2026.py --dry-run

    # Actual backfill
    python backfill_march_2026.py

    # Skip geocoding (faster, coordinates filled on next daily run)
    python backfill_march_2026.py --skip-geocode
"""

import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths — identical to the ETL scripts
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent
DATA_DIR = REPO_ROOT / "multi-county-real-estate-research" / "data" / "fairfax"

CRIME_PROCESSED = DATA_DIR / "crime" / "processed"
CRIME_INCIDENTS = CRIME_PROCESSED / "incidents.parquet"
CRIME_METADATA = CRIME_PROCESSED / "metadata.json"
CRIME_RAW_DIR = DATA_DIR / "crime" / "raw" / "weekly"
GEOCODE_CACHE = DATA_DIR / "crime" / "raw" / "geocoded" / "address_cache.parquet"

PERMITS_PROCESSED = DATA_DIR / "building_permits" / "processed"
PERMITS_FILE = PERMITS_PROCESSED / "permits.parquet"
PERMITS_METADATA = PERMITS_PROCESSED / "metadata.json"

# ---------------------------------------------------------------------------
# Crime config — copied from fairfax_crime_etl.py
# ---------------------------------------------------------------------------
CRIME_API_URL = "https://www.fairfaxcounty.gov/apps/pfsu/api/file/crimereportsfromsp"
WEEKLY_COLUMNS = ['count', 'code', 'description', 'date', 'time',
                  'address', 'city', 'state', 'zip']

VIOLENT_CODES = ['ASSLT', 'ROB', 'HOMICIDE', 'RAPE', 'KIDNAP', 'MURDER']
PROPERTY_CODES = ['LARC', 'BURG', 'AUTO', 'DEST', 'FRAUD', 'FORG',
                  'THEFT', 'ARSON']

CITY_ABBREV = {
    'ALEX': 'Alexandria', 'RSTN': 'Reston', 'FLCH': 'Falls Church',
    'FRFX': 'Fairfax', 'SFLD': 'Springfield', 'ANDL': 'Annandale',
    'CENT': 'Centreville', 'MCLN': 'McLean', 'HRND': 'Herndon',
    'VNNA': 'Vienna', 'CHAN': 'Chantilly', 'LRTN': 'Lorton',
    'BRKE': 'Burke', 'GTFL': 'Great Falls', 'CLFT': 'Clifton',
    'OKTN': 'Oakton', 'FXST': 'Fairfax Station', 'FTBV': 'Fort Belvoir',
    'DUNN': 'Dunn Loring', 'LOCO': 'Lorton', 'ARLN': 'Arlington',
}

# ---------------------------------------------------------------------------
# Permits config — copied from fairfax_permits_etl.py
# ---------------------------------------------------------------------------
PERMITS_API_URL = (
    "https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services/"
    "Building_Records_PLUS/FeatureServer/0"
)
MAX_RECORDS_PER_REQUEST = 2000
REQUEST_DELAY = 1.5

PERMIT_CATEGORIES = {
    'residential_new': ['Residential New'],
    'residential_renovation': [
        'Residential Addition/Alteration', 'Residential Electrical',
        'Residential Mechanical', 'Residential Plumbing',
        'Residential Solar', 'Residential Retaining Wall',
        'Residential Miscellaneous',
    ],
    'residential_demolition': ['Residential Demolition'],
    'commercial_new': ['Commercial New'],
    'commercial_renovation': [
        'Commercial Addition/Alteration', 'Commercial Addition-Alteration',
        'Commercial Electrical', 'Commercial Mechanical',
        'Commercial Plumbing', 'Commercial Solar',
        'Commercial Retaining Wall', 'Commercial Miscellaneous',
    ],
    'commercial_demolition': ['Commercial Demolition'],
    'certificate': ['Certificate of Occupancy',
                    'Certificate of Occupancy (Non-RUP)'],
    'elevator': ['Elevator Equipment', 'Elevator Installation Permit',
                 'Elevator Maintenance Permit'],
    'other': [
        'Amusement Device', 'Building Height Certification',
        'Building Permit Amendment', 'Code Appeal', 'Code Modification',
        'Critical Structures', 'Cross Connection', 'Damage Report',
        'Household Appliance', 'Masterfile', 'Separation Permit',
        'Seperation ',
    ]
}
PERMIT_TYPE_TO_CATEGORY = {}
for _cat, _types in PERMIT_CATEGORIES.items():
    for _pt in _types:
        PERMIT_TYPE_TO_CATEGORY[_pt] = _cat

MAJOR_CATEGORIES = {
    'residential': ['residential_new', 'residential_renovation',
                    'residential_demolition'],
    'commercial': ['commercial_new', 'commercial_renovation',
                   'commercial_demolition'],
    'other': ['certificate', 'elevator', 'other'],
}


# ===================================================================
# CRIME BACKFILL
# ===================================================================

def fetch_crime_rolling_window() -> pd.DataFrame:
    """Fetch the current rolling window from the Fairfax crime API."""
    logger.info(f"Fetching crime data from {CRIME_API_URL}")

    for attempt in range(3):
        try:
            resp = requests.get(CRIME_API_URL, timeout=30)
            resp.raise_for_status()
            break
        except requests.RequestException as exc:
            if attempt < 2:
                wait = 2 * (attempt + 1)
                logger.warning(f"Attempt {attempt+1} failed: {exc}. "
                               f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

    # Save raw CSV
    CRIME_RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = CRIME_RAW_DIR / f"backfill_{datetime.now():%Y-%m-%d}.csv"
    raw_file.write_text(resp.text)
    logger.info(f"Saved raw CSV to {raw_file}")

    df = pd.read_csv(
        StringIO(resp.text),
        names=WEEKLY_COLUMNS,
        header=None,
        on_bad_lines='skip',
    )
    logger.info(f"Fetched {len(df)} incidents "
                f"(dates {df['date'].min()} to {df['date'].max()})")
    return df


def transform_crime(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw crime CSV to unified schema (mirrors ETL logic)."""
    out = df.copy()
    out['code_prefix'] = out['code'].str.split('-').str[0]

    out['category'] = 'OTHER'
    out.loc[out['code_prefix'].isin(VIOLENT_CODES), 'category'] = 'VIOLENT'
    out.loc[out['code_prefix'].isin(PROPERTY_CODES), 'category'] = 'PROPERTY'

    out['incident_id'] = (
        out['date'].astype(str) + '_' +
        out['time'].astype(str) + '_' +
        out['code'].astype(str) + '_' +
        out['address'].astype(str).str[:20]
    )

    out = out.rename(columns={'code': 'crime_code'})
    out['latitude'] = None
    out['longitude'] = None
    out['source'] = 'weekly_api'
    out['ingestion_date'] = datetime.now().strftime('%Y-%m-%d')

    cols = [
        'incident_id', 'crime_code', 'description', 'category',
        'date', 'time', 'address', 'city', 'state', 'zip',
        'latitude', 'longitude', 'source', 'ingestion_date',
    ]
    for c in cols:
        if c not in out.columns:
            out[c] = None
    return out[cols]


def geocode_new_incidents(df: pd.DataFrame,
                          max_geocode: int = 200) -> pd.DataFrame:
    """
    Geocode new addresses using the existing cache + Census geocoder.
    Mirrors the logic in fairfax_crime_etl.py without importing it.
    """
    # Load cache
    if GEOCODE_CACHE.exists():
        cache = pd.read_parquet(GEOCODE_CACHE)
        cached_set = set(cache['address'].tolist())
    else:
        cache = pd.DataFrame(
            columns=['address', 'latitude', 'longitude',
                     'quality', 'geocoded_date'])
        cached_set = set()

    # Build full address strings
    addr_clean = df['address'].astype(str).fillna('')
    addr_clean = addr_clean.str.replace(r';(\d)', r' APT \1', regex=True)
    addr_clean = addr_clean.str.replace(
        r'\bROUTE (\d+)', r'VA-\1', regex=True)

    city_clean = (df['city'].astype(str).fillna('')
                  .map(CITY_ABBREV)
                  .fillna(df['city'].astype(str).fillna('')))
    zip_clean = (df['zip'].astype(str).fillna('')
                 .str.replace('.0', '', regex=False))

    df = df.copy()
    df['full_address'] = (
        addr_clean + ', ' + city_clean + ', ' +
        df['state'].astype(str).fillna('') + ' ' + zip_clean
    )

    new_addrs = [a for a in df['full_address'].unique()
                 if a not in cached_set]

    logger.info(f"Geocoding: {len(new_addrs)} new addresses "
                f"(max {max_geocode})")

    new_entries = []
    for addr in new_addrs[:max_geocode]:
        parts = addr.split(',')
        if len(parts) < 3:
            continue
        street = parts[0].strip()
        city = parts[1].strip()
        state_zip = parts[2].strip().split()
        state = state_zip[0] if state_zip else 'VA'
        zipcode = state_zip[1] if len(state_zip) > 1 else ''

        coords = _geocode_census(street, city, state, zipcode)
        if coords:
            new_entries.append({
                'address': addr,
                'latitude': coords[0],
                'longitude': coords[1],
                'quality': 'matched_census',
                'geocoded_date': datetime.now().strftime('%Y-%m-%d'),
            })

    if new_entries:
        cache = pd.concat([cache, pd.DataFrame(new_entries)],
                          ignore_index=True)
        GEOCODE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        cache.to_parquet(GEOCODE_CACHE, index=False)
        logger.info(f"Geocoded {len(new_entries)} new addresses, "
                    f"cache now {len(cache)} total")

    # Merge coordinates back
    df = df.merge(
        cache[['address', 'latitude', 'longitude']].rename(
            columns={'address': 'full_address',
                     'latitude': 'geo_lat',
                     'longitude': 'geo_lon'}),
        on='full_address', how='left',
    )
    df['latitude'] = df['geo_lat']
    df['longitude'] = df['geo_lon']
    df.drop(columns=['full_address', 'geo_lat', 'geo_lon'],
            errors='ignore', inplace=True)

    pct = (df['latitude'].notna().sum() / len(df)) * 100
    logger.info(f"Geocoding coverage: {pct:.1f}%")
    return df


def _geocode_census(street, city, state, zipcode):
    """Single-address Census geocoder lookup."""
    full = f"{street}, {city}, {state} {zipcode}"
    try:
        resp = requests.get(
            "https://geocoding.geo.census.gov/geocoder/locations/"
            "onelineaddress",
            params={'address': full, 'benchmark': 'Public_AR_Current',
                    'format': 'json'},
            timeout=10,
        )
        resp.raise_for_status()
        matches = resp.json().get('result', {}).get('addressMatches', [])
        if matches:
            c = matches[0]['coordinates']
            return (c['y'], c['x'])
    except Exception:
        pass
    return None


def backfill_crime(dry_run: bool = False,
                   skip_geocode: bool = False) -> dict:
    """
    Fetch the current crime rolling window and merge into the existing
    incidents.parquet, deduplicating by incident_id.

    Returns a summary dict.
    """
    # Load existing
    existing = pd.read_parquet(CRIME_INCIDENTS)
    existing_ids = set(existing['incident_id'].tolist())
    logger.info(f"Existing incidents: {len(existing)} "
                f"(dates {existing['date'].min()} – "
                f"{existing['date'].max()})")

    # Fetch and transform
    raw = fetch_crime_rolling_window()
    new = transform_crime(raw)

    # Deduplicate
    truly_new = new[~new['incident_id'].isin(existing_ids)]
    dupes = len(new) - len(truly_new)
    logger.info(f"API returned {len(new)} incidents: "
                f"{dupes} duplicates, {len(truly_new)} new")

    if len(truly_new) == 0:
        logger.info("No new incidents to add.")
        return {'new_incidents': 0, 'duplicates': dupes}

    # Show what dates the new records cover
    date_counts = truly_new['date'].value_counts().sort_index()
    logger.info(f"New incidents by date:\n{date_counts.to_string()}")

    if dry_run:
        logger.info("DRY RUN — not writing anything.")
        return {
            'new_incidents': len(truly_new),
            'duplicates': dupes,
            'date_breakdown': date_counts.to_dict(),
            'dry_run': True,
        }

    # Geocode
    if not skip_geocode:
        truly_new = geocode_new_incidents(truly_new)

    # Merge and save
    combined = pd.concat([existing, truly_new], ignore_index=True)
    combined = combined.sort_values('date').reset_index(drop=True)
    combined.to_parquet(CRIME_INCIDENTS, index=False)

    # Update metadata
    metadata = {
        'last_updated': datetime.now().isoformat(),
        'total_incidents': len(combined),
        'date_range': {
            'min': str(combined['date'].min()),
            'max': str(combined['date'].max()),
        },
        'sources': combined['source'].value_counts().to_dict(),
        'categories': combined['category'].value_counts().to_dict(),
        'geocoding': {
            'total': len(combined),
            'geocoded': int(combined['latitude'].notna().sum()),
            'pct_geocoded': round(
                combined['latitude'].notna().sum() / len(combined) * 100, 1),
        },
        'cities': combined['city'].value_counts().head(10).to_dict(),
        'backfill_note': (
            f"Backfilled {len(truly_new)} incidents on "
            f"{datetime.now():%Y-%m-%d} covering gap Mar 3-9"
        ),
    }
    with open(CRIME_METADATA, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved {len(combined)} total incidents to "
                f"{CRIME_INCIDENTS}")

    return {
        'new_incidents': len(truly_new),
        'duplicates': dupes,
        'total_after': len(combined),
        'date_breakdown': date_counts.to_dict(),
    }


# ===================================================================
# PERMITS BACKFILL
# ===================================================================

def fetch_permits_page(where_clause: str, offset: int = 0) -> dict:
    """Fetch one page of permits from ArcGIS REST API."""
    params = {
        'where': where_clause,
        'outFields': '*',
        'returnGeometry': 'true',
        'resultOffset': offset,
        'resultRecordCount': MAX_RECORDS_PER_REQUEST,
        'f': 'json',
    }
    url = f"{PERMITS_API_URL}/query"

    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            if 'error' in data:
                raise requests.RequestException(f"API error: {data['error']}")
            return data
        except (requests.RequestException, json.JSONDecodeError) as exc:
            wait = 2 ** attempt
            logger.warning(f"Permits request failed (attempt {attempt+1}): "
                           f"{exc}")
            if attempt < 2:
                time.sleep(wait)
            else:
                raise
    return {}


def fetch_all_permits(where_clause: str) -> list:
    """Paginate through all matching permits."""
    all_features = []
    offset = 0

    while True:
        logger.info(f"Fetching permits at offset {offset}...")
        data = fetch_permits_page(where_clause, offset)
        features = data.get('features', [])
        if not features:
            break

        all_features.extend(features)
        logger.info(f"Downloaded {len(all_features)} permits so far")

        if len(features) < MAX_RECORDS_PER_REQUEST:
            break

        offset += MAX_RECORDS_PER_REQUEST
        time.sleep(REQUEST_DELAY)

    return all_features


def parse_timestamp(ts):
    """Convert ArcGIS epoch-ms timestamp to datetime."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000)
    except (ValueError, OSError):
        return None


def polygon_centroid(rings):
    """Average-vertex centroid of the outer ring."""
    if not rings or not rings[0] or len(rings[0]) < 3:
        return None, None
    coords = rings[0]
    n = len(coords)
    return sum(c[0] for c in coords) / n, sum(c[1] for c in coords) / n


def va_sp_to_wgs84(x, y):
    """Approximate Virginia State Plane North (ft) → WGS84."""
    x_m = x * 0.3048
    y_m = y * 0.3048
    ref_x = 11800000 * 0.3048
    ref_y = 7000000 * 0.3048
    lon = -77.3 + (x_m - ref_x) / 85000
    lat = 38.85 + (y_m - ref_y) / 111000
    return lon, lat


def process_permit_features(features: list) -> pd.DataFrame:
    """Convert raw ArcGIS features to DataFrame (mirrors ETL logic)."""
    records = []
    for feat in features:
        attrs = feat.get('attributes', {})
        geom = feat.get('geometry')

        # Centroid
        c_lon, c_lat = None, None
        if geom and 'rings' in geom:
            cx, cy = polygon_centroid(geom['rings'])
            if cx is not None:
                c_lon, c_lat = va_sp_to_wgs84(cx, cy)

        ptype = attrs.get('APPTYPEALIAS', '')
        detailed = PERMIT_TYPE_TO_CATEGORY.get(ptype, 'other')
        major = 'other'
        for maj, dlist in MAJOR_CATEGORIES.items():
            if detailed in dlist:
                major = maj
                break

        records.append({
            'permit_id': attrs.get('RECORDID'),
            'permit_type': ptype,
            'permit_category': detailed,
            'permit_major_category': major,
            'project_name': attrs.get('PROJECT_NAME'),
            'status': attrs.get('RECORD_STATUS'),
            'parcel_id': attrs.get('PARCEL_ID'),
            'address': attrs.get('MAR_ADDRESS') or attrs.get('ADDRESS_1'),
            'address_1': attrs.get('ADDRESS_1'),
            'address_2': attrs.get('ADDRESS_2'),
            'city': attrs.get('CITY'),
            'state': attrs.get('STATE'),
            'zip_code': attrs.get('ZIP_CODE'),
            'submitted_date': parse_timestamp(attrs.get('SUBMITTED_DATE')),
            'accepted_date': parse_timestamp(attrs.get('ACCEPTED_DATE')),
            'issued_date': parse_timestamp(attrs.get('ISSUED_DATE')),
            'closed_date': parse_timestamp(attrs.get('CLOSED_DATE')),
            'approved_date': parse_timestamp(attrs.get('APPROVED_DATE')),
            'supervisor_district': attrs.get('SUPERVISOR_DISTRICT'),
            'development_center': attrs.get('DEVELOPMENT_CENTER'),
            'document_url': attrs.get('DOCUMENT_URL'),
            'link_url': attrs.get('LINK_URL'),
            'centroid_lon': c_lon,
            'centroid_lat': c_lat,
            'has_geometry': geom is not None and 'rings' in (geom or {}),
            'ingestion_date': datetime.now(),
        })

    df = pd.DataFrame(records)
    date_cols = ['submitted_date', 'accepted_date', 'issued_date',
                 'closed_date', 'approved_date', 'ingestion_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    return df


def backfill_permits(dry_run: bool = False) -> dict:
    """
    Fetch permits issued since Feb 1, 2026 and merge into the existing
    permits.parquet, deduplicating by permit_id.
    """
    # Fetch permits issued since Feb 1 — wider than the gap to catch
    # anything the last successful Mar 2 run may have missed
    where = "ISSUED_DATE >= DATE '2026-02-01'"

    # Get count first
    count_params = {
        'where': where, 'returnCountOnly': 'true', 'f': 'json'
    }
    resp = requests.get(f"{PERMITS_API_URL}/query",
                        params=count_params, timeout=30)
    resp.raise_for_status()
    total = resp.json().get('count', 0)
    logger.info(f"Permits matching query (issued >= 2026-02-01): {total}")

    if dry_run:
        logger.info("DRY RUN — not fetching full dataset.")
        return {'matching_count': total, 'dry_run': True}

    # Fetch all matching
    features = fetch_all_permits(where)
    new_df = process_permit_features(features)
    logger.info(f"Fetched and processed {len(new_df)} permits")

    # Load existing and merge
    existing = pd.read_parquet(PERMITS_FILE)
    logger.info(f"Existing permits: {len(existing)}")

    # Remove old versions of any permits that appear in the new data
    existing_keep = existing[
        ~existing['permit_id'].isin(new_df['permit_id'])]
    combined = pd.concat([existing_keep, new_df], ignore_index=True)

    added = len(combined) - len(existing)
    updated = len(existing) - len(existing_keep)

    logger.info(f"Result: {added} added, {updated} updated, "
                f"{len(combined)} total")

    # Save
    combined.to_parquet(PERMITS_FILE, engine='pyarrow',
                        compression='snappy', index=False)

    # Metadata
    df_year = combined.dropna(subset=['issued_date']).copy()
    df_year['year'] = df_year['issued_date'].dt.year
    by_year = {str(int(k)): v for k, v in
               df_year['year'].value_counts().sort_index().items()}

    metadata = {
        'last_updated': datetime.now().isoformat(),
        'total_permits': len(combined),
        'date_range': {
            'min': (combined['issued_date'].min().strftime('%Y-%m-%d')
                    if pd.notna(combined['issued_date'].min()) else None),
            'max': (combined['issued_date'].max().strftime('%Y-%m-%d')
                    if pd.notna(combined['issued_date'].max()) else None),
        },
        'by_major_category':
            combined['permit_major_category'].value_counts().to_dict(),
        'by_detailed_category':
            combined['permit_category'].value_counts().to_dict(),
        'by_year': by_year,
        'by_status':
            dict(list(combined['status'].value_counts().items())[:10]),
        'geometry': {
            'has_polygon': int(combined['has_geometry'].sum()),
            'has_centroid': int(combined['centroid_lat'].notna().sum()),
            'pct_geocoded': round(
                combined['centroid_lat'].notna().sum()
                / len(combined) * 100, 1) if len(combined) else 0,
        },
        'parcel_linkage': {
            'has_parcel_id': int(combined['parcel_id'].notna().sum()),
            'pct_linked': round(
                combined['parcel_id'].notna().sum()
                / len(combined) * 100, 1) if len(combined) else 0,
        },
        'backfill_note': (
            f"Backfilled on {datetime.now():%Y-%m-%d}: "
            f"{added} added, {updated} updated"
        ),
    }
    with open(PERMITS_METADATA, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved {len(combined)} total permits to {PERMITS_FILE}")

    return {
        'added': added,
        'updated': updated,
        'total_after': len(combined),
    }


# ===================================================================
# MAIN
# ===================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="One-time backfill for Mar 3-9, 2026 data gap")
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would change without writing')
    parser.add_argument('--skip-geocode', action='store_true',
                        help='Skip geocoding new crime addresses')
    parser.add_argument('--crime-only', action='store_true',
                        help='Only backfill crime data')
    parser.add_argument('--permits-only', action='store_true',
                        help='Only backfill permits data')
    args = parser.parse_args()

    do_crime = not args.permits_only
    do_permits = not args.crime_only

    print("=" * 60)
    print("FAIRFAX DATA BACKFILL — March 3-9, 2026 Gap")
    print("=" * 60)

    if args.dry_run:
        print("\n*** DRY RUN MODE — no files will be modified ***\n")

    results = {}

    if do_crime:
        print("\n--- CRIME DATA BACKFILL ---")
        try:
            results['crime'] = backfill_crime(
                dry_run=args.dry_run,
                skip_geocode=args.skip_geocode,
            )
            c = results['crime']
            print(f"\nCrime result: {c.get('new_incidents', 0)} new, "
                  f"{c.get('duplicates', 0)} duplicates")
            if 'date_breakdown' in c:
                print("New incidents by date:")
                for date, count in sorted(c['date_breakdown'].items()):
                    print(f"  {date}: {count}")
        except Exception as exc:
            logger.error(f"Crime backfill failed: {exc}")
            results['crime'] = {'error': str(exc)}

    if do_permits:
        print("\n--- PERMITS DATA BACKFILL ---")
        try:
            results['permits'] = backfill_permits(dry_run=args.dry_run)
            p = results['permits']
            if 'added' in p:
                print(f"\nPermits result: {p['added']} added, "
                      f"{p['updated']} updated, "
                      f"{p['total_after']} total")
            elif 'matching_count' in p:
                print(f"\nPermits available: {p['matching_count']}")
        except Exception as exc:
            logger.error(f"Permits backfill failed: {exc}")
            results['permits'] = {'error': str(exc)}

    print("\n" + "=" * 60)
    print("BACKFILL COMPLETE")
    print("=" * 60)

    if not args.dry_run:
        print("\nNext steps:")
        print("  git add multi-county-real-estate-research/data/fairfax/")
        print("  git commit -m 'data: backfill Fairfax crime + permits "
              "for Mar 3-9 gap'")
        print("  git push origin main")

    return results


if __name__ == '__main__':
    main()
