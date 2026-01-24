# Fairfax County Data Processing Scripts

## File Size Management

Fairfax County has 3x the population of Loudoun County, resulting in much larger files:
- Sales data: ~500K records vs Loudoun's 47K
- Road network: More complex, larger file
- Parcels: ~400K parcels vs Loudoun's ~140K

**GitHub Limit:** 100 MB per file
**Strategy:** Process and filter BEFORE committing

## Processing Workflow

### 1. Sales Data Processing
```bash
# Input: data/fairfax/sales/raw/sales_data.csv (300-500 MB)
# Output: data/fairfax/sales/processed/combined_sales.parquet (10-20 MB)

python scripts/convert_sales_to_parquet.py \
  --county fairfax \
  --input data/fairfax/sales/raw/sales_data.csv \
  --output data/fairfax/sales/processed/combined_sales.parquet \
  --filter-years 5
```

### 2. GIS Data Processing
```bash
# For each shapefile layer:
# 1. Load with geopandas
# 2. Transform to EPSG:4326
# 3. Filter to essential fields
# 4. Export to GeoJSON (if < 50 MB) or filtered shapefile

python scripts/process_gis_layer.py \
  --input data/fairfax/gis/roads/raw/roadway_centerlines.shp \
  --output data/fairfax/gis/roads/processed/roads.geojson \
  --crs EPSG:4326 \
  --max-size-mb 50
```

### 3. Building Permits Processing
```bash
# Geocode and convert to Parquet
python scripts/process_building_permits.py \
  --county fairfax \
  --input data/fairfax/building_permits/raw/permits.csv \
  --output data/fairfax/building_permits/processed/permits.parquet
```

## Size Verification Before Commit

Always check file sizes before committing:
```bash
# Check processed files
find data/fairfax/*/processed -type f -size +50M
find data/fairfax/*/processed -type f -size +100M

# If any files > 50 MB, review and optimize further
```

## Compression Strategies

### Parquet Format (Tabular Data)
- 100x compression vs CSV/Excel
- Columnar storage for fast queries
- Schema preservation

```python
import pandas as pd

# Read CSV
df = pd.read_csv('large_file.csv')

# Write Parquet with compression
df.to_parquet('output.parquet', compression='snappy')
```

### GeoJSON vs GeoParquet (Spatial Data)
- GeoJSON: Human-readable, good for < 50 MB
- GeoParquet: Better compression for large datasets

```python
import geopandas as gpd

gdf = gpd.read_file('large_shapefile.shp')

# Try GeoJSON first
gdf.to_file('output.geojson', driver='GeoJSON')

# If too large, use GeoParquet
gdf.to_parquet('output.geoparquet')
```

### Simplification for Geometries
```python
# Simplify complex geometries (tolerance in degrees)
gdf['geometry'] = gdf.geometry.simplify(0.0001)
```

## Data Quality Checks

Before committing processed data:

1. **Row count verification**
   ```python
   print(f"Raw: {len(raw_df):,} rows")
   print(f"Processed: {len(processed_df):,} rows")
   ```

2. **Column validation**
   ```python
   required_cols = ['id', 'address', 'date', 'value']
   assert all(col in processed_df.columns for col in required_cols)
   ```

3. **Coordinate check (for spatial data)**
   ```python
   assert gdf.crs.to_epsg() == 4326  # WGS84
   assert gdf.geometry.is_valid.all()
   ```

## Fairfax-Specific Notes

### Sales Data
- Relational structure: sales table joins to parcels by PARID
- Include both residential and commercial sales
- Filter out non-arms-length transactions (family transfers, etc.)

### Zoning Data
- Fairfax zoning codes are complex (e.g., R-1, R-2, PDH, etc.)
- Include Planned Development zones
- Map to general categories (Residential, Commercial, Industrial)

### School Data
- FCPS has regular and AAP (Advanced Academic Program) boundaries
- AAP boundaries may differ from regular attendance zones
- Include pyramid information (ES → MS → HS)
