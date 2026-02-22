"""
Convert Fairfax County Parcels shapefile to address_points.parquet.

Since the original fairfax_address_points.csv (154MB, Git LFS) is unavailable,
this script extracts parcel centroids from the Parcels.zip shapefile (EPSG:3857)
and converts them to WGS84 lat/lon coordinates.

The PIN field in parcels maps directly to PARID in the sales data.

Output: data/fairfax/address_points/processed/address_points.parquet
Columns: PARID, lat, lon
"""

import geopandas as gpd
import pandas as pd
from pathlib import Path
import time

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
PARCELS_ZIP = BASE_DIR / "data" / "fairfax" / "gis" / "parcels" / "raw" / "Parcels.zip"
OUTPUT_PATH = BASE_DIR / "data" / "fairfax" / "address_points" / "processed" / "address_points.parquet"


def convert_parcels_to_address_points():
    print("=" * 60)
    print("CONVERT PARCELS TO ADDRESS POINTS")
    print("=" * 60)

    # Step 1: Load parcels shapefile
    print(f"\n1. Loading parcels from {PARCELS_ZIP}...")
    start = time.time()
    gdf = gpd.read_file(PARCELS_ZIP)
    print(f"   Loaded {len(gdf):,} parcels in {time.time() - start:.1f}s")
    print(f"   CRS: {gdf.crs}")
    print(f"   Columns: {list(gdf.columns)}")

    # Step 2: Compute centroids in the source CRS (EPSG:3857) for accuracy
    print("\n2. Computing parcel centroids...")
    start = time.time()
    centroids = gdf.geometry.centroid
    print(f"   Computed {len(centroids):,} centroids in {time.time() - start:.1f}s")

    # Step 3: Create GeoDataFrame with centroids and reproject to WGS84
    print("\n3. Reprojecting centroids to WGS84 (EPSG:4326)...")
    start = time.time()
    centroid_gdf = gpd.GeoDataFrame(
        {'PIN': gdf['PIN']},
        geometry=centroids,
        crs=gdf.crs
    )
    centroid_wgs84 = centroid_gdf.to_crs(epsg=4326)
    print(f"   Reprojected in {time.time() - start:.1f}s")

    # Step 4: Extract lat/lon from geometry
    print("\n4. Extracting lat/lon coordinates...")
    result = pd.DataFrame({
        'PARID': centroid_wgs84['PIN'],
        'lat': centroid_wgs84.geometry.y,
        'lon': centroid_wgs84.geometry.x,
    })

    # Drop rows with null PARID or coordinates
    before = len(result)
    result = result.dropna(subset=['PARID', 'lat', 'lon'])
    if before != len(result):
        print(f"   Dropped {before - len(result)} rows with null values")

    print(f"   Final rows: {len(result):,}")

    # Step 5: Save to parquet
    print(f"\n5. Saving to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUTPUT_PATH, index=False)
    file_size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"   Saved ({file_size:.1f} MB)")

    # Step 6: Verify
    print("\n6. Verification:")
    verify = pd.read_parquet(OUTPUT_PATH)
    print(f"   Row count: {len(verify):,}")
    print(f"   Columns: {list(verify.columns)}")
    print(f"   Dtypes:\n{verify.dtypes}")
    print(f"\n   Sample 5 rows:")
    print(verify.head(5).to_string())
    print(f"\n   Lat range: {verify['lat'].min():.6f} to {verify['lat'].max():.6f}")
    print(f"   Lon range: {verify['lon'].min():.6f} to {verify['lon'].max():.6f}")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    convert_parcels_to_address_points()
