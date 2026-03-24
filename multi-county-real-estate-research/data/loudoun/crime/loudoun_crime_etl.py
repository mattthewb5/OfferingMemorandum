#!/usr/bin/env python3
"""
Loudoun County Crime Data ETL Pipeline.

Ingests FOIA crime data from Loudoun County Sheriff's Office XLSX,
normalizes, maps offense categories, geocodes addresses, and outputs
a unified incidents.parquet compatible with the multi-county crime analysis module.

Source: 20260205 RMS FOIA Crime Data 2023-2026 YTD
Format: Excel (.xlsx), sheet "2023-2026 YTD"

Usage:
    python etl/loudoun_crime_etl.py                    # Full run (no geocoding)
    python etl/loudoun_crime_etl.py --sample 500       # Process first 500 rows only
    python etl/loudoun_crime_etl.py --geocode           # Run with geocoding
    python etl/loudoun_crime_etl.py --geocode --max-geocode 100  # Limit geocoding
"""

import os
import sys
import re
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PATHS
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent / "data" / "loudoun" / "crime"
FOIA_FILENAME = "20260205_-_RMS_-_FOIA_Crime_Data_2023-2026_YTD_-_Final.xlsx"
FOIA_PATH = BASE_DIR / FOIA_FILENAME
CACHE_PATH = BASE_DIR / "geocode_cache.parquet"
PROCESSED_DIR = BASE_DIR / "processed"
OUTPUT_PATH = PROCESSED_DIR / "incidents.parquet"

# ============================================================================
# OFFENSE CATEGORY MAPPING (Loudoun 18-category → 3-tier)
# ============================================================================

OFFENSE_CATEGORY_MAP = {
    # VIOLENT
    "SIMPLE ASSAULT": "VIOLENT",
    "ASSAULT": "VIOLENT",
    "RAPE": "VIOLENT",
    "ROBBERY": "VIOLENT",
    "HOMICIDE": "VIOLENT",
    "WEAPON VIOL.": "VIOLENT",
    # PROPERTY
    "LARCENY": "PROPERTY",
    "AUTO THEFT": "PROPERTY",
    "BURGLARY": "PROPERTY",
    "DEST. OF PROPERTY": "PROPERTY",
    # OTHER
    "NARC. RELATED": "OTHER",
    "DUI": "OTHER",
    "DIS. CONDUCT": "OTHER",
    "DIP": "OTHER",
    "RUNAWAY": "OTHER",
    "LIQUOR LAW VIOL.": "OTHER",
    "PEEPING TOM": "OTHER",
    "Animal Cruelty": "OTHER",
}

# Normalized version (all upper) for matching
_OFFENSE_MAP_UPPER = {k.upper(): v for k, v in OFFENSE_CATEGORY_MAP.items()}


def map_offense_to_category(offense: str) -> str:
    """Map a Loudoun offense category to the 3-tier system (VIOLENT/PROPERTY/OTHER)."""
    if pd.isna(offense):
        return "OTHER"
    result = _OFFENSE_MAP_UPPER.get(offense.upper().strip())
    if result is None:
        logger.warning(f"Unmapped offense category: {repr(offense)}")
        return "OTHER"
    return result


# ============================================================================
# STEP 1: INGEST
# ============================================================================

def ingest(sample: Optional[int] = None) -> pd.DataFrame:
    """Read the FOIA xlsx and return raw dataframe."""
    logger.info(f"Reading {FOIA_PATH.name} ...")
    df = pd.read_excel(
        FOIA_PATH,
        sheet_name="2023-2026 YTD",
        engine="openpyxl",
        nrows=sample,
    )
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns: {list(df.columns)}")
    return df


# ============================================================================
# STEP 2: NORMALIZE
# ============================================================================

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names, types, and values."""
    # Rename to snake_case
    df = df.rename(columns={
        "Case Number": "case_number",
        "Occurred Date/Time": "occurred_datetime",
        "Block Address": "block_address",
        "City": "city",
        "Offense Category": "offense_category",
        "Station": "station",
        "Beat": "beat",
    })

    # Normalize city casing
    df["city"] = df["city"].astype(str).str.upper().str.strip()

    # Normalize beat to string
    df["beat"] = df["beat"].astype(str).str.strip()

    # Parse datetime, extract date and year
    df["occurred_datetime"] = pd.to_datetime(df["occurred_datetime"], errors="coerce")
    df["date"] = df["occurred_datetime"].dt.strftime("%Y-%m-%d")
    df["year"] = df["occurred_datetime"].dt.year

    # Add source column
    df["source"] = "loudoun_foia"

    logger.info(f"Normalized {len(df)} rows")
    return df


# ============================================================================
# STEP 3: CATEGORY MAPPING
# ============================================================================

def apply_category_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """Map offense categories to 3-tier VIOLENT/PROPERTY/OTHER."""
    df["category"] = df["offense_category"].apply(map_offense_to_category)

    counts = df["category"].value_counts()
    logger.info(f"Category mapping: {counts.to_dict()}")

    # Check for unmapped
    unmapped = df[df["offense_category"].str.upper().str.strip().apply(
        lambda x: x not in _OFFENSE_MAP_UPPER
    )]
    if len(unmapped) > 0:
        logger.warning(f"{len(unmapped)} records with unmapped offense categories")

    return df


# ============================================================================
# STEP 4: GEOCODING
# ============================================================================

def clean_address_for_geocoding(block_address: str) -> Tuple[str, str]:
    """
    Clean a Loudoun block address for geocoding.

    Returns (cleaned_address, status) where status is:
    - "ready": address is ready for geocoding
    - "intersection_skipped": intersection format, skip geocoding
    - "approx_ready": approximate location, cleaned for geocoding
    """
    if pd.isna(block_address):
        return ("", "null_address")

    addr = str(block_address).strip()

    # Intersection format: "Street1 / Street2"
    if " / " in addr:
        return (addr, "intersection_skipped")

    # Remove "BLOCK" prefix
    addr = re.sub(r'\bBLOCK\b\s*', '', addr, flags=re.IGNORECASE).strip()

    # Remove "Approx Loc:" prefix
    addr = re.sub(r'^Approx\s+Loc:\s*', '', addr, flags=re.IGNORECASE).strip()

    # Clean up double spaces
    addr = re.sub(r'\s+', ' ', addr).strip()

    if not addr:
        return ("", "empty_after_clean")

    return (addr, "ready")


def load_geocode_cache() -> pd.DataFrame:
    """Load existing geocode cache or return empty frame."""
    if CACHE_PATH.exists():
        cache = pd.read_parquet(CACHE_PATH)
        logger.info(f"Loaded geocode cache with {len(cache)} entries")
        return cache
    return pd.DataFrame(columns=["address_key", "latitude", "longitude", "geocode_status", "geocoded_date"])


def save_geocode_cache(cache: pd.DataFrame):
    """Save geocode cache to parquet."""
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    cache.to_parquet(CACHE_PATH, index=False)
    logger.info(f"Saved geocode cache with {len(cache)} entries")


def geocode_address_google(address: str, city: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a single address using Google Maps Geocoding API.

    Requires GOOGLE_MAPS_API_KEY environment variable.
    """
    import requests

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not set")
        return None

    full_address = f"{address}, {city}, VA"
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": full_address,
            "key": api_key,
            "components": "country:US|administrative_area:VA",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK" and data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            lat, lng = loc["lat"], loc["lng"]
            # Sanity check: must be in Loudoun County area
            if 38.7 <= lat <= 39.4 and -78.1 <= lng <= -77.2:
                return (lat, lng)
            else:
                logger.debug(f"Out-of-bounds result for {full_address}: ({lat}, {lng})")
                return None
        return None
    except Exception as e:
        logger.debug(f"Geocoding failed for {full_address}: {e}")
        return None


def geocode_address_census(address: str, city: str) -> Optional[Tuple[float, float]]:
    """
    Geocode using Census Bureau geocoder (free, no API key).
    """
    import requests

    full_address = f"{address}, {city}, VA"
    try:
        url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        params = {
            "address": full_address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        matches = data.get("result", {}).get("addressMatches", [])
        if matches:
            coords = matches[0]["coordinates"]
            lat, lng = coords["y"], coords["x"]
            if 38.7 <= lat <= 39.4 and -78.1 <= lng <= -77.2:
                return (lat, lng)
        return None
    except Exception as e:
        logger.debug(f"Census geocoding failed for {full_address}: {e}")
        return None


def _build_address_table(df: pd.DataFrame) -> pd.DataFrame:
    """Build unique address table with cleaned addresses and keys."""
    addr_info = df[["block_address", "city"]].drop_duplicates()
    addr_info["cleaned_address"], addr_info["addr_status"] = zip(
        *addr_info["block_address"].apply(clean_address_for_geocoding)
    )
    addr_info["address_key"] = addr_info["cleaned_address"] + ", " + addr_info["city"] + ", VA"
    return addr_info


def _run_geocoder_pass(addresses_to_geocode: pd.DataFrame,
                       cache: pd.DataFrame,
                       geocoder_fn,
                       geocoder_name: str,
                       save_every: int = 200,
                       log_every: int = 500) -> Tuple[pd.DataFrame, int]:
    """
    Run a single geocoder pass over a list of addresses.

    Args:
        addresses_to_geocode: DataFrame with cleaned_address, city, address_key columns
        cache: Current geocode cache
        geocoder_fn: Function(address, city) -> Optional[Tuple[float, float]]
        geocoder_name: Name for logging (e.g., "Census", "Google")
        save_every: Save cache every N addresses
        log_every: Print progress every N addresses

    Returns:
        (updated_cache, success_count)
    """
    import time

    total = len(addresses_to_geocode)
    if total == 0:
        logger.info(f"  {geocoder_name}: No addresses to process")
        return cache, 0

    logger.info(f"  {geocoder_name}: Processing {total} addresses...")
    success_count = 0
    fail_count = 0
    new_rows = []

    for i, (_, row) in enumerate(addresses_to_geocode.iterrows()):
        cleaned = row["cleaned_address"]
        city = row["city"]
        addr_key = row["address_key"]

        coords = geocoder_fn(cleaned, city)

        status_tag = f"geocoded_{geocoder_name.lower()}"
        if coords:
            new_rows.append({
                "address_key": addr_key,
                "latitude": coords[0],
                "longitude": coords[1],
                "geocode_status": status_tag,
                "geocoded_date": datetime.now().strftime("%Y-%m-%d"),
            })
            success_count += 1
        else:
            new_rows.append({
                "address_key": addr_key,
                "latitude": None,
                "longitude": None,
                "geocode_status": "failed",
                "geocoded_date": datetime.now().strftime("%Y-%m-%d"),
            })
            fail_count += 1

        # Save cache periodically
        processed = i + 1
        if processed % save_every == 0:
            batch = pd.DataFrame(new_rows)
            cache = pd.concat([cache, batch], ignore_index=True)
            new_rows = []
            save_geocode_cache(cache)

        # Progress reporting
        if processed % log_every == 0 or processed == total:
            logger.info(
                f"  {geocoder_name}: {processed}/{total} "
                f"(success: {success_count}, failed: {fail_count})"
            )

        # Rate limit: Census is slow enough; Google needs throttling
        if geocoder_name.lower() == "google":
            time.sleep(0.05)

    # Save remaining
    if new_rows:
        batch = pd.DataFrame(new_rows)
        cache = pd.concat([cache, batch], ignore_index=True)
        save_geocode_cache(cache)

    logger.info(f"  {geocoder_name} complete: {success_count} success, {fail_count} failed")
    return cache, success_count


def load_beat_centroids() -> Dict[str, Tuple[float, float]]:
    """
    Load sheriff patrol sector centroids from GeoJSON.

    Returns dict mapping PS_PD_AREA (beat code) -> (lat, lon).
    """
    import json

    geojson_path = BASE_DIR / "sheriff_patrol_sectors.geojson"
    if not geojson_path.exists():
        logger.warning(f"Beat shapefile not found: {geojson_path}")
        return {}

    with open(geojson_path) as f:
        data = json.load(f)

    centroids = {}
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        beat_code = props.get("PS_PD_AREA", "")
        geom = feature.get("geometry", {})

        if geom.get("type") == "Polygon" and geom.get("coordinates"):
            # Compute centroid from exterior ring
            ring = geom["coordinates"][0]
            n = len(ring)
            if n > 0:
                cx = sum(pt[0] for pt in ring) / n
                cy = sum(pt[1] for pt in ring) / n
                centroids[beat_code] = (cy, cx)  # (lat, lon)
        elif geom.get("type") == "MultiPolygon" and geom.get("coordinates"):
            # Use first polygon's ring
            ring = geom["coordinates"][0][0]
            n = len(ring)
            if n > 0:
                cx = sum(pt[0] for pt in ring) / n
                cy = sum(pt[1] for pt in ring) / n
                centroids[beat_code] = (cy, cx)

    logger.info(f"Loaded {len(centroids)} beat centroids from patrol sectors GeoJSON")
    return centroids


def geocode_dataframe(df: pd.DataFrame,
                      max_geocode: int = 0,
                      run_google: bool = True,
                      run_beat_fallback: bool = True) -> pd.DataFrame:
    """
    Two-pass geocoding with beat centroid fallback.

    Pass 1: Census geocoder (free) for all geocodable addresses
    Pass 2: Google Maps API for Census failures (if key available)
    Pass 3: Beat centroid fallback for remaining failures
    """
    cache = load_geocode_cache()
    cached_keys = set(cache["address_key"].tolist()) if len(cache) > 0 else set()

    # Build address table
    addr_info = _build_address_table(df)
    geocodable = addr_info[addr_info["addr_status"] == "ready"].copy()
    intersections = addr_info[addr_info["addr_status"] == "intersection_skipped"]
    new_to_geocode = geocodable[~geocodable["address_key"].isin(cached_keys)]

    logger.info(f"Unique addresses: {len(addr_info)}")
    logger.info(f"  Geocodable: {len(geocodable)}")
    logger.info(f"  Intersections (skip): {len(intersections)}")
    logger.info(f"  Already cached: {len(geocodable) - len(new_to_geocode)}")
    logger.info(f"  New to geocode: {len(new_to_geocode)}")

    # Limit if requested (0 = unlimited)
    targets = new_to_geocode if max_geocode == 0 else new_to_geocode.head(max_geocode)

    # ---- PASS 1: Census ----
    logger.info("=" * 50)
    logger.info("PASS 1: Census Geocoder")
    logger.info("=" * 50)
    cache, census_hits = _run_geocoder_pass(
        targets, cache, geocode_address_census, "Census",
        save_every=200, log_every=500
    )

    # ---- PASS 2: Google (for Census failures) ----
    if run_google and os.environ.get("GOOGLE_MAPS_API_KEY"):
        # Find ALL failed addresses in cache (including from previous runs)
        failed_mask = (cache["geocode_status"] == "failed")
        failed_keys = set(cache.loc[failed_mask, "address_key"].tolist())
        # Match failed keys back to geocodable address table for city/cleaned_address info
        failed_addrs = geocodable[geocodable["address_key"].isin(failed_keys)]

        logger.info("=" * 50)
        logger.info(f"PASS 2: Google Maps API ({len(failed_addrs)} addresses)")
        logger.info("=" * 50)

        if len(failed_addrs) > 0:
            # Remove failed entries from cache before re-geocoding
            cache = cache[~((cache["address_key"].isin(failed_keys)) & (cache["geocode_status"] == "failed"))]
            cache, google_hits = _run_geocoder_pass(
                failed_addrs, cache, geocode_address_google, "Google",
                save_every=200, log_every=500
            )
        else:
            google_hits = 0
    else:
        if run_google:
            logger.info("PASS 2: Skipped (GOOGLE_MAPS_API_KEY not set)")
        google_hits = 0

    # ---- Merge cache to dataframe ----
    df["_cleaned_addr"], df["_addr_status"] = zip(
        *df["block_address"].apply(clean_address_for_geocoding)
    )
    df["_address_key"] = df["_cleaned_addr"] + ", " + df["city"] + ", VA"

    cache_lookup = cache[["address_key", "latitude", "longitude", "geocode_status"]].drop_duplicates(
        subset=["address_key"], keep="last"
    )
    df = df.merge(cache_lookup, left_on="_address_key", right_on="address_key", how="left")

    # Mark intersection rows
    df.loc[df["_addr_status"] == "intersection_skipped", "geocode_status"] = "intersection_skipped"
    df.loc[df["geocode_status"].isna(), "geocode_status"] = "failed"

    # ---- PASS 3: Beat centroid fallback ----
    beat_centroid_count = 0
    if run_beat_fallback:
        logger.info("=" * 50)
        logger.info("PASS 3: Beat Centroid Fallback")
        logger.info("=" * 50)

        still_missing = df["latitude"].isna() & (df["geocode_status"] != "intersection_skipped")
        beat_centroids = load_beat_centroids()

        if beat_centroids and still_missing.any():
            for idx in df.index[still_missing]:
                beat = df.at[idx, "beat"]
                if beat in beat_centroids:
                    lat, lon = beat_centroids[beat]
                    df.at[idx, "latitude"] = lat
                    df.at[idx, "longitude"] = lon
                    df.at[idx, "geocode_status"] = "beat_centroid"
                    beat_centroid_count += 1

        logger.info(f"Beat centroid fallback: {beat_centroid_count} records assigned")

    # Clean up temp columns
    df = df.drop(columns=["_cleaned_addr", "_addr_status", "_address_key", "address_key"], errors="ignore")

    geocoded_total = df["latitude"].notna().sum()
    logger.info(f"Final geocoding coverage: {geocoded_total}/{len(df)} ({100*geocoded_total/len(df):.1f}%)")

    return df


# ============================================================================
# STEP 5: OUTPUT
# ============================================================================

def save_output(df: pd.DataFrame):
    """Save processed dataframe to parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Select and order output columns
    output_cols = [
        "case_number", "occurred_datetime", "date", "year",
        "block_address", "city", "offense_category", "category",
        "station", "beat", "source",
    ]
    # Add geocoding columns if present
    if "latitude" in df.columns:
        output_cols.extend(["latitude", "longitude", "geocode_status"])

    df_out = df[[c for c in output_cols if c in df.columns]]
    df_out.to_parquet(OUTPUT_PATH, index=False)
    logger.info(f"Saved {len(df_out)} rows to {OUTPUT_PATH}")


def print_summary(df: pd.DataFrame):
    """Print final ETL summary."""
    print("\n" + "=" * 60)
    print("LOUDOUN CRIME ETL — SUMMARY")
    print("=" * 60)
    print(f"Total rows:    {len(df):,}")
    print(f"Date range:    {df['date'].min()} to {df['date'].max()}")
    print(f"Years:         {sorted(df['year'].dropna().unique().astype(int).tolist())}")
    print(f"Unique cases:  {df['case_number'].nunique():,}")

    print(f"\nCategory breakdown:")
    for cat, count in df["category"].value_counts().items():
        print(f"  {cat}: {count:,} ({100*count/len(df):.1f}%)")

    print(f"\nOffense categories (top 10):")
    for cat, count in df["offense_category"].value_counts().head(10).items():
        print(f"  {cat}: {count:,}")

    print(f"\nStations:")
    for s, count in df["station"].value_counts().items():
        print(f"  {s}: {count:,}")

    if "latitude" in df.columns:
        geocoded = df["latitude"].notna().sum()
        print(f"\nGeocoding:")
        print(f"  Geocoded:  {geocoded:,} ({100*geocoded/len(df):.1f}%)")
        if "geocode_status" in df.columns:
            for status, count in df["geocode_status"].value_counts().items():
                print(f"  {status}: {count:,}")

    print("=" * 60)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Loudoun County Crime Data ETL")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only first N rows (for smoke testing)")
    parser.add_argument("--geocode", action="store_true",
                        help="Enable geocoding (Census + Google + beat fallback)")
    parser.add_argument("--max-geocode", type=int, default=0,
                        help="Max addresses to geocode (0 = unlimited, default: 0)")
    parser.add_argument("--no-google", action="store_true",
                        help="Skip Google Maps API pass")
    parser.add_argument("--no-beat-fallback", action="store_true",
                        help="Skip beat centroid fallback")
    args = parser.parse_args()

    logger.info("Starting Loudoun Crime ETL")
    if args.sample:
        logger.info(f"SAMPLE MODE: processing first {args.sample} rows only")

    # Step 1: Ingest
    df = ingest(sample=args.sample)

    # Step 2: Normalize
    df = normalize(df)

    # Step 3: Category mapping
    df = apply_category_mapping(df)

    # Step 4: Geocoding (optional)
    if args.geocode:
        df = geocode_dataframe(
            df,
            max_geocode=args.max_geocode,
            run_google=not args.no_google,
            run_beat_fallback=not args.no_beat_fallback,
        )
    else:
        logger.info("Geocoding skipped (use --geocode to enable)")
        df["latitude"] = None
        df["longitude"] = None
        df["geocode_status"] = "not_attempted"

    # Step 5: Output
    save_output(df)
    print_summary(df)

    logger.info("ETL complete")


if __name__ == "__main__":
    main()
