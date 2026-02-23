"""
Fairfax County Sales Analysis Module

Provides proximity-based comparable sales lookups by joining sales transaction
data with parcel centroid coordinates.

Data Sources:
- sales_2020_2025.parquet: 90,511 sales records (Fairfax Commissioner of Revenue)
- address_points.parquet: 369,010 parcel centroids with WGS84 lat/lon

Usage:
    from core.fairfax_sales_analysis import get_nearby_sales

    comps = get_nearby_sales(lat=38.918914, lon=-77.401634)
    for sale in comps:
        print(f"{sale['parid']} - ${sale['sale_price']:,.0f} - {sale['distance_miles']:.2f}mi")
"""

import pandas as pd
import math
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data" / "fairfax"

SALES_PATH = DATA_DIR / "sales" / "processed" / "sales_2020_2025.parquet"
ADDRESS_PATH = DATA_DIR / "address_points" / "processed" / "address_points.parquet"
CACHE_DIR = DATA_DIR / "sales" / "cache"

# Cache TTL: 30 days in seconds
CACHE_TTL = 30 * 24 * 60 * 60

# Earth's radius in miles
EARTH_RADIUS_MI = 3959.0


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


def _load_joined_data() -> pd.DataFrame:
    """
    Load and join sales + address data, with file-based caching.

    Returns DataFrame with columns: PARID, SALE_DATE, SALE_PRICE, SALE_TYPE,
    SALE_YEAR, lat, lon
    """
    cache_path = _get_cache_path()

    if _cache_is_valid(cache_path):
        return pd.read_parquet(cache_path)

    # Load source data
    sales = pd.read_parquet(SALES_PATH)
    addresses = pd.read_parquet(ADDRESS_PATH)

    # Normalize column name: address_points uses "Parcel Identification Number"
    addresses = addresses.rename(columns={"Parcel Identification Number": "PARID"})

    # Join on PARID — preserve spacing, don't strip
    joined = sales.merge(addresses, on="PARID", how="inner")

    # Drop rows missing coordinates or price
    joined = joined.dropna(subset=["lat", "lon", "SALE_PRICE"])

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

    Returns:
        List of dicts sorted by distance, each containing:
        - parid: Parcel identification number
        - sale_price: Sale price in dollars
        - sale_date: Sale date as string (YYYY-MM-DD)
        - sale_type: Sale type description
        - distance_miles: Distance from subject property in miles
        - lat: Parcel latitude
        - lon: Parcel longitude
    """
    df = _load_joined_data()

    # Filter by price range
    df = df[(df["SALE_PRICE"] >= min_price) & (df["SALE_PRICE"] <= max_price)]

    # Rough bounding box filter first (much faster than computing haversine for all rows)
    # 1 degree latitude ≈ 69 miles, 1 degree longitude ≈ 54 miles at this latitude
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
        sale_date = row["SALE_DATE"]
        if pd.notna(sale_date):
            sale_date = pd.Timestamp(sale_date).strftime("%Y-%m-%d")
        else:
            sale_date = None

        # Build formatted address from address_points fields
        addr_line = row.get("Address Line 1", "")
        city = row.get("City", "")
        zipcode = row.get("Zip Code", "")
        if addr_line and city:
            address = f"{addr_line}, {city}, VA {zipcode}".strip()
        elif addr_line:
            address = str(addr_line)
        else:
            address = row["PARID"]

        results.append({
            "parid": row["PARID"],
            "address": address,
            "sale_price": float(row["SALE_PRICE"]),
            "sale_date": sale_date,
            "sale_type": row.get("SALE_TYPE", ""),
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
) -> Dict:
    """
    Get summary statistics for all sales within a radius.

    Returns:
        Dict with: total_count, median_price, min_price, max_price,
        most_recent_date, sales (list of all matching sales dicts)
    """
    df = _load_joined_data()

    # Filter by price range
    df = df[(df["SALE_PRICE"] >= min_price) & (df["SALE_PRICE"] <= max_price)]

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
        sale_date = row["SALE_DATE"]
        if pd.notna(sale_date):
            sale_date = pd.Timestamp(sale_date).strftime("%Y-%m-%d")
        else:
            sale_date = None

        # Build formatted address
        addr_line = row.get("Address Line 1", "")
        city = row.get("City", "")
        zipcode = row.get("Zip Code", "")
        if addr_line and city:
            address = f"{addr_line}, {city}, VA {zipcode}".strip()
        elif addr_line:
            address = str(addr_line)
        else:
            address = row["PARID"]

        sales.append({
            "parid": row["PARID"],
            "address": address,
            "sale_price": float(row["SALE_PRICE"]),
            "sale_date": sale_date,
            "sale_type": row.get("SALE_TYPE", ""),
            "distance_miles": round(row["distance_miles"], 3),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
        })

    most_recent = df["SALE_DATE"].max()
    if pd.notna(most_recent):
        most_recent = pd.Timestamp(most_recent).strftime("%Y-%m-%d")
    else:
        most_recent = None

    return {
        "total_count": len(df),
        "median_price": float(df["SALE_PRICE"].median()),
        "min_price": float(df["SALE_PRICE"].min()),
        "max_price": float(df["SALE_PRICE"].max()),
        "most_recent_date": most_recent,
        "sales": sales,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("FAIRFAX SALES ANALYSIS — Test")
    print("=" * 60)

    # Test: 13172 Ruby Lace Ct, Herndon, VA 20170
    test_lat, test_lon = 38.918914, -77.401634
    print(f"\nTest location: {test_lat}, {test_lon} (13172 Ruby Lace Ct)")

    print("\n--- get_nearby_sales (limit=10) ---")
    comps = get_nearby_sales(test_lat, test_lon, radius_miles=0.5, limit=10)
    for c in comps:
        print(
            f"  PARID={c['parid']}  ${c['sale_price']:>12,.0f}  "
            f"{c['sale_date']}  {c['distance_miles']:.3f}mi"
        )

    print("\n--- get_nearby_sales_summary ---")
    summary = get_nearby_sales_summary(test_lat, test_lon, radius_miles=0.5)
    print(f"  Total sales: {summary['total_count']}")
    print(f"  Median price: ${summary['median_price']:,.0f}" if summary['median_price'] else "  Median price: N/A")
    print(f"  Price range: ${summary['min_price']:,.0f} - ${summary['max_price']:,.0f}" if summary['min_price'] else "  Price range: N/A")
    print(f"  Most recent: {summary['most_recent_date']}")

    print("\n" + "=" * 60)
