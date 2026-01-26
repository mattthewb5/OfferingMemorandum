# Flood Zones - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download FEMA flood zone shapefiles from Fairfax County GIS or FEMA MSC.

Expected files:
- Flood hazard zones shapefile + associated files
- May include multiple zone types (AE, X, etc.)

## Processing Steps

1. **Download** flood zone layer

2. **Load and transform**:
   ```python
   import geopandas as gpd
   flood = gpd.read_file('raw/flood_zones.shp')
   flood = flood.to_crs(epsg=4326)
   ```

3. **Filter** to relevant fields:
   - Keep: geometry, flood zone designation, base flood elevation
   - Drop: study metadata, panel numbers

4. **Export optimized**:
   ```python
   flood.to_file('../processed/flood_zones.geojson', driver='GeoJSON')
   ```

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed GeoJSON: ../processed/
