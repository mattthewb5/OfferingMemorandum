# Road Centerlines - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download road centerline shapefiles from:
https://data-fairfaxcountygis.opendata.arcgis.com/datasets/roadway-centerlines

Expected files:
- `roadway_centerlines.shp` + associated files (.shx, .dbf, .prj)
- Total size: ~50-100 MB (shapefile format)

## Processing Steps

1. **Download** as Shapefile format

2. **Load and transform**:
   ```python
   import geopandas as gpd
   roads = gpd.read_file('raw/roadway_centerlines.shp')
   roads = roads.to_crs(epsg=4326)  # Transform to WGS84
   ```

3. **Filter** to relevant fields only:
   - Keep: geometry, street name, route number, classification, speed limit
   - Drop: internal IDs, maintenance codes, etc.

4. **Export optimized**:
   ```python
   roads.to_file('../processed/roads.geojson', driver='GeoJSON')
   # Or if too large, subset to highways/collectors only
   ```

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed GeoJSON: ../processed/ (committed if < 50 MB)
