# GIS Data

Geographic Information System data layers for Fairfax County.

## Data Source

Fairfax County GIS Open Data Portal:
https://data-fairfaxcountygis.opendata.arcgis.com/

## Subdirectories

- `roads/` - Road centerlines and classification
- `zoning/` - Zoning districts and land use
- `parcels/` - Tax parcel boundaries
- `schools/` - School attendance zones
- `flood/` - FEMA flood zones
- `subdivisions/` - Recorded subdivision boundaries

## Processing Notes

All GIS layers should be:
1. Transformed to EPSG:4326 (WGS84) for web compatibility
2. Simplified if needed to reduce file size
3. Exported to GeoJSON format (if < 50 MB)
4. Stored in Parquet/GeoParquet for larger datasets

## Coordinate Reference System

- Source: Various (often Virginia State Plane)
- Target: EPSG:4326 (WGS84 lat/lon)

Always transform to EPSG:4326 before committing processed files.
