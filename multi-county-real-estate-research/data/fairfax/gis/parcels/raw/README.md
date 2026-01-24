# Tax Parcels - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download parcel boundary shapefiles from Fairfax County GIS.

Expected files:
- Parcels shapefile + associated files
- **Warning**: This is typically the LARGEST file (~400K parcels)
- Total size: 200+ MB

## Processing Steps

1. **Download** parcel layer from county GIS portal

2. **Load and transform**:
   ```python
   import geopandas as gpd
   parcels = gpd.read_file('raw/parcels.shp')
   parcels = parcels.to_crs(epsg=4326)
   ```

3. **Filter** to relevant fields:
   - Keep: geometry, parcel ID, address, acreage
   - Drop: detailed assessment data (join from other sources)

4. **Consider subsetting**:
   - May need to split by geographic area
   - Or export to GeoParquet format for better compression

## File Locations

- Raw shapefiles: Stay here (local only)
- Processed files: ../processed/ (may require special handling due to size)
