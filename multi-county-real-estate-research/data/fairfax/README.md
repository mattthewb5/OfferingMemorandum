# Fairfax County Data Directory

**County:** Fairfax County, Virginia (FIPS: 51059)
**Population:** ~1.15 million (2020 Census)
**Area:** 406 square miles

## File Size Management Strategy

Due to GitHub's 100 MB file size limit, this directory uses a two-tier system:

### Local Only (Not Committed)
- `*/raw/` directories contain original downloads
- Large shapefiles, Excel files, unprocessed data
- These files stay on your local machine only (gitignored)

### Committed to GitHub
- `*/processed/` directories contain optimized files
- Parquet format (100x smaller than Excel)
- Filtered/subset data within size limits
- Small configuration files

## Data Sources

All data sourced from:
- **Fairfax County GIS**: https://data-fairfaxcountygis.opendata.arcgis.com/
- **Fairfax County Tax Administration**: https://www.fairfaxcounty.gov/taxes/
- **Virginia Department of Education**: https://schoolquality.virginia.gov/
- **Virginia Department of Transportation**: https://www.virginiadot.org/info/data.asp

## Directory Structure

- `sales/` - Property sales history
- `gis/` - Geographic data layers (roads, zoning, parcels, etc.)
- `building_permits/` - Development activity
- `crime/` - Public safety data
- `schools/` - School performance and boundaries
- `transit/` - Metro and transit data
- `config/` - Configuration and lookup tables

## Last Updated
[Date will be updated as data is added]

## Data Processing Notes

1. **Sales Data**: Download → Filter to 3-5 years → Convert to Parquet → Commit processed/
2. **GIS Layers**: Download → Transform to EPSG:4326 → Simplify if needed → Export to GeoJSON → Commit processed/
3. **Building Permits**: Download → Geocode → Filter date range → Convert to Parquet → Commit processed/

See individual README files in subdirectories for specific processing instructions.
