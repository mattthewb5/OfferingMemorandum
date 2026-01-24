# School Boundaries - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download school attendance zone shapefiles from Fairfax County GIS.

Multiple layers:
- Elementary school boundaries
- Middle school boundaries
- High school boundaries
- AAP (Advanced Academic Program) boundaries

## Processing Steps

1. **Download** each school level boundary layer

2. **Load and transform**:
   ```python
   import geopandas as gpd
   elementary = gpd.read_file('raw/elementary_zones.shp')
   elementary = elementary.to_crs(epsg=4326)
   ```

3. **Standardize** field names across levels

4. **Export optimized**:
   ```python
   elementary.to_file('../processed/elementary_zones.geojson', driver='GeoJSON')
   ```

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed GeoJSON: ../processed/
