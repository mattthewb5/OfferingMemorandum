"""
Loudoun County Sales Analysis Module

Provides proximity-based comparable sales lookups by joining sales transaction
data with parcel centroid coordinates.

Data Sources:
- combined_sales.parquet: 78,300 sales records (Loudoun Commissioner of Revenue)
- parcel_xy.parquet: 132,208 parcel centroids from LOGIS ArcGIS (layer 9)
- logis_addresses.parquet: 141,971 addresses from LOGIS Master Address List (table 8)

Usage:
    from core.loudoun_sales_analysis import get_nearby_sales

    comps = get_nearby_sales(lat=39.1125, lon=-77.4974)
    for sale in comps:
        print(f"{sale['parid']} - ${sale['sale_price']:,.0f} - {sale['distance_miles']:.2f}mi")
"""

import pandas as pd
import math
import time
from pathlib import Path
from typing import List, Dict, Optional

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data" / "loudoun"

SALES_PATH = DATA_DIR / "sales" / "combined_sales.parquet"
PARCEL_XY_PATH = DATA_DIR / "parcels" / "parcel_xy.parquet"
ADDRESS_PATH = DATA_DIR / "addresses" / "logis_addresses.parquet"
CACHE_DIR = DATA_DIR / "sales" / "cache"

# Cache TTL: 30 days in seconds
CACHE_TTL = 30 * 24 * 60 * 60

# Earth's radius in miles
EARTH_RADIUS_MI = 3959.0

# Arms-length transaction codes (reliable market indicators)
ARMS_LENGTH_CODES = {
    '1:MARKET SALE',
    '2:MARKET LAND SALE',
    '5:MARKET MULTI-PARCEL SALE',
    'V:NEW CONSTRUCTION',
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in miles between two points."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_MI * 2 * math.asin(math.sqrt(a))


def _get_cache_path() -> Path:
    """Get path for the cached joined dataset."""
    return CACHE_DIR / "joined_sales.parquet"


def _cache_is_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is within TTL."""
    if not cache_path.exists():
        return False
    age = time.time() - cache_path.stat().st_mtime
    return age < CACHE_TTL


def _load_address_lookup() -> Dict[str, str]:
    """
    Load LOGIS Master Address List as a dict mapping PA_MCPI -> street address.

    Returns empty dict if address file is missing (graceful degradation).
    """
    if not ADDRESS_PATH.exists():
        return {}
    addr_df = pd.read_parquet(ADDRESS_PATH)
    # Build lookup: AM_MCPI -> "43422 CLOISTER PL, LEESBURG, VA 20176"
    lookup = {}
    for _, row in addr_df.iterrows():
        mcpi = row.get("AM_MCPI", "")
        street = str(row.get("AM_STD_FULL_ADDRESS", "")).strip()
        town = str(row.get("AM_TOWN", "")).strip()
        zipcode = row.get("AM_ZIP")
        if mcpi and street:
            if town and zipcode:
                lookup[mcpi] = f"{street}, {town}, VA {int(zipcode)}"
            elif town:
                lookup[mcpi] = f"{street}, {town}"
            else:
                lookup[mcpi] = street
    return lookup


# Module-level lazy cache for address lookup
_address_lookup_cache: Optional[Dict[str, str]] = None


def _get_address(mcpi: str) -> str:
    """Look up street address for a parcel ID. Falls back to formatted parcel ID."""
    global _address_lookup_cache
    if _address_lookup_cache is None:
        _address_lookup_cache = _load_address_lookup()
    addr = _address_lookup_cache.get(mcpi, "")
    if addr:
        return addr.title()
    return f"Parcel {mcpi}" if mcpi else "Unknown"


def _load_joined_data() -> pd.DataFrame:
    """
    Load and join sales + parcel centroid data, with file-based caching.

    Joins sales (PARID as int64) with parcel_xy (PA_MCPI as 12-digit string)
    after normalizing PARID to zero-padded 12-digit string.

    Filters to arms-length transactions only.

    Returns DataFrame with columns: PARID, RECORD DATE, PRICE,
    SALE VERIFICATION, INSTRUMENT#, OLD OWNER, NEW OWNER, lat, lon
    """
    cache_path = _get_cache_path()

    if _cache_is_valid(cache_path):
        return pd.read_parquet(cache_path)

    # Load source data
    sales = pd.read_parquet(SALES_PATH)
    parcel_xy = pd.read_parquet(PARCEL_XY_PATH)

    # Filter to arms-length transactions
    sales = sales[sales['SALE VERIFICATION'].isin(ARMS_LENGTH_CODES)].copy()

    # Normalize PARID: int64 -> zero-padded 12-digit string
    sales['PARID_STR'] = sales['PARID'].astype(str).str.zfill(12)

    # Join on normalized PARID
    joined = sales.merge(parcel_xy, left_on='PARID_STR', right_on='PA_MCPI', how='inner')

    # Drop rows missing coordinates or price
    joined = joined.dropna(subset=["lat", "lon", "PRICE"])
    joined = joined[joined["PRICE"] > 0]

    # Ensure RECORD DATE is datetime
    joined['RECORD DATE'] = pd.to_datetime(joined['RECORD DATE'], errors='coerce')

    # Save cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    joined.to_parquet(cache_path, index=False)

    return joined


def get_nearby_sales(
    lat: float,
    lon: float,
    radius_miles: float = 0.5,
    limit: int = 10,
    min_price: float = 100_000,
    max_price: float = 5_000_000,
    commercial_mode: bool = False,
) -> List[Dict]:
    """
    Find comparable sales near a given location.

    Args:
        lat: Latitude of the subject property
        lon: Longitude of the subject property
        radius_miles: Search radius in miles (default 0.5)
        limit: Maximum number of results to return (default 10)
        min_price: Minimum sale price filter (default $100,000)
        max_price: Maximum sale price filter (default $5,000,000)
        commercial_mode: If True, use min_price=1,000,000 with no upper bound

    Returns:
        List of dicts sorted by distance, each containing:
        - parid: Parcel identification number
        - sale_price: Sale price in dollars
        - sale_date: Sale date as string (YYYY-MM-DD)
        - sale_type: Sale verification description
        - instrument_number: Instrument number
        - old_owner: Previous owner
        - new_owner: Current owner
        - distance_miles: Distance from subject property in miles
        - lat: Parcel latitude
        - lon: Parcel longitude
    """
    if commercial_mode:
        min_price = 1_000_000
        max_price = float('inf')

    df = _load_joined_data()

    # Filter by price range
    df = df[df["PRICE"] >= min_price]
    if max_price != float('inf'):
        df = df[df["PRICE"] <= max_price]

    # Rough bounding box filter first (much faster than computing haversine for all rows)
    lat_margin = radius_miles / 69.0
    lon_margin = radius_miles / (69.0 * math.cos(math.radians(lat)))

    df = df[
        (df["lat"] >= lat - lat_margin)
        & (df["lat"] <= lat + lat_margin)
        & (df["lon"] >= lon - lon_margin)
        & (df["lon"] <= lon + lon_margin)
    ]

    if len(df) == 0:
        return []

    # Compute exact distances
    df = df.copy()
    df["distance_miles"] = df.apply(
        lambda r: _haversine(lat, lon, r["lat"], r["lon"]), axis=1
    )

    # Filter by radius
    df = df[df["distance_miles"] <= radius_miles]

    # Sort by distance
    df = df.sort_values("distance_miles")

    # Build result list
    results = []
    for _, row in df.head(limit).iterrows():
        sale_date = row["RECORD DATE"]
        if pd.notna(sale_date):
            sale_date = pd.Timestamp(sale_date).strftime("%Y-%m-%d")
        else:
            sale_date = None

        mcpi = row.get("PARID_STR", row.get("PA_MCPI", ""))
        results.append({
            "parid": mcpi,
            "address": _get_address(mcpi),
            "sale_price": float(row["PRICE"]),
            "sale_date": sale_date,
            "sale_type": row.get("SALE VERIFICATION", ""),
            "instrument_number": row.get("INSTRUMENT#", ""),
            "old_owner": row.get("OLD OWNER", ""),
            "new_owner": row.get("NEW OWNER", ""),
            "distance_miles": round(row["distance_miles"], 3),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        })

    return results


def get_nearby_sales_summary(
    lat: float,
    lon: float,
    radius_miles: float = 0.5,
    min_price: float = 100_000,
    max_price: float = 5_000_000,
    commercial_mode: bool = False,
) -> Dict:
    """
    Get summary statistics for all sales within a radius.

    Returns:
        Dict with: total_count, median_price, min_price, max_price,
        most_recent_date, sales (list of all matching sales dicts)
    """
    if commercial_mode:
        min_price = 1_000_000
        max_price = float('inf')

    df = _load_joined_data()

    # Filter by price range
    df = df[df["PRICE"] >= min_price]
    if max_price != float('inf'):
        df = df[df["PRICE"] <= max_price]

    # Bounding box
    lat_margin = radius_miles / 69.0
    lon_margin = radius_miles / (69.0 * math.cos(math.radians(lat)))
    df = df[
        (df["lat"] >= lat - lat_margin)
        & (df["lat"] <= lat + lat_margin)
        & (df["lon"] >= lon - lon_margin)
        & (df["lon"] <= lon + lon_margin)
    ]

    if len(df) == 0:
        return {
            "total_count": 0,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "most_recent_date": None,
            "sales": [],
        }

    df = df.copy()
    df["distance_miles"] = df.apply(
        lambda r: _haversine(lat, lon, r["lat"], r["lon"]), axis=1
    )
    df = df[df["distance_miles"] <= radius_miles].sort_values("distance_miles")

    if len(df) == 0:
        return {
            "total_count": 0,
            "median_price": None,
            "min_price": None,
            "max_price": None,
            "most_recent_date": None,
            "sales": [],
        }

    # Build full sales list
    sales = []
    for _, row in df.iterrows():
        sale_date = row["RECORD DATE"]
        if pd.notna(sale_date):
            sale_date = pd.Timestamp(sale_date).strftime("%Y-%m-%d")
        else:
            sale_date = None

        mcpi = row.get("PARID_STR", row.get("PA_MCPI", ""))
        sales.append({
            "parid": mcpi,
            "address": _get_address(mcpi),
            "sale_price": float(row["PRICE"]),
            "sale_date": sale_date,
            "sale_type": row.get("SALE VERIFICATION", ""),
            "instrument_number": row.get("INSTRUMENT#", ""),
            "old_owner": row.get("OLD OWNER", ""),
            "new_owner": row.get("NEW OWNER", ""),
            "distance_miles": round(row["distance_miles"], 3),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        })

    most_recent = df["RECORD DATE"].max()
    if pd.notna(most_recent):
        most_recent = pd.Timestamp(most_recent).strftime("%Y-%m-%d")
    else:
        most_recent = None

    return {
        "total_count": len(df),
        "median_price": float(df["PRICE"].median()),
        "min_price": float(df["PRICE"].min()),
        "max_price": float(df["PRICE"].max()),
        "most_recent_date": most_recent,
        "sales": sales,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("LOUDOUN SALES ANALYSIS — Test")
    print("=" * 60)

    # Test: 43422 Cloister Pl, Leesburg, VA 20176
    test_lat, test_lon = 39.11249052, -77.49741425
    print(f"\nTest location: {test_lat}, {test_lon} (43422 Cloister Pl)")

    print("\n--- get_nearby_sales (limit=10) ---")
    comps = get_nearby_sales(test_lat, test_lon, radius_miles=0.5, limit=10)
    for c in comps:
        print(
            f"  {c['address']:<40s}  ${c['sale_price']:>12,.0f}  "
            f"{c['sale_date']}  {c['distance_miles']:.3f}mi  "
            f"{c['sale_type']}"
        )

    print("\n--- get_nearby_sales_summary ---")
    summary = get_nearby_sales_summary(test_lat, test_lon, radius_miles=0.5)
    print(f"  Total sales: {summary['total_count']}")
    print(f"  Median price: ${summary['median_price']:,.0f}" if summary['median_price'] else "  Median price: N/A")
    print(f"  Price range: ${summary['min_price']:,.0f} - ${summary['max_price']:,.0f}" if summary['min_price'] else "  Price range: N/A")
    print(f"  Most recent: {summary['most_recent_date']}")

    print("\n--- commercial_mode test ---")
    comps_commercial = get_nearby_sales(test_lat, test_lon, radius_miles=1.0, limit=5, commercial_mode=True)
    print(f"  Commercial comps found: {len(comps_commercial)}")
    for c in comps_commercial:
        print(
            f"  PARID={c['parid']}  ${c['sale_price']:>12,.0f}  "
            f"{c['sale_date']}  {c['distance_miles']:.3f}mi"
        )

    print("\n" + "=" * 60)
