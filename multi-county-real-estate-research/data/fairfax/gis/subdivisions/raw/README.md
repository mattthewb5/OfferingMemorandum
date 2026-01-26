# Subdivisions - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download subdivision boundary shapefiles from:
https://data-fairfaxcountygis.opendata.arcgis.com/datasets/subdivisions

Expected files:
- Subdivisions shapefile + associated files

## Processing Steps

1. **Download** subdivision layer

2. **Load and transform**:
   ```python
   import geopandas as gpd
   subdivisions = gpd.read_file('raw/subdivisions.shp')
   subdivisions = subdivisions.to_crs(epsg=4326)
   ```

3. **Filter** to relevant fields:
   - Keep: geometry, subdivision name, plat date, section
   - Drop: internal IDs, approval metadata

4. **Export optimized**:
   ```python
   subdivisions.to_file('../processed/subdivisions.geojson', driver='GeoJSON')
   ```

## Use Cases

- Identify HOA/community membership
- Group properties for market analysis
- Historical development patterns

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed GeoJSON: ../processed/
