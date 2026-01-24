# Zoning Districts - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download zoning district shapefiles from Fairfax County GIS Open Data Portal.

Expected files:
- Zoning shapefile + associated files (.shx, .dbf, .prj)
- Total size varies

## Processing Steps

1. **Download** zoning layer from county GIS portal

2. **Load and transform**:
   ```python
   import geopandas as gpd
   zoning = gpd.read_file('raw/zoning.shp')
   zoning = zoning.to_crs(epsg=4326)
   ```

3. **Filter** to relevant fields:
   - Keep: geometry, zone code, zone description, category
   - Drop: internal IDs, approval dates, etc.

4. **Export optimized**:
   ```python
   zoning.to_file('../processed/zoning.geojson', driver='GeoJSON')
   ```

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed GeoJSON: ../processed/ (committed if < 50 MB)
