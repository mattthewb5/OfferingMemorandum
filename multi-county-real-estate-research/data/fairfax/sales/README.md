# Sales Data

Property sales transaction data for Fairfax County.

## Data Source

Fairfax County Tax Administration Real Estate Sales Data:
https://data-fairfaxcountygis.opendata.arcgis.com/datasets/tax-administrations-real-estate-sales-data

## Directory Structure

- `raw/` - Original downloads (LOCAL ONLY - not committed)
- `processed/` - Optimized Parquet files (committed to GitHub)

## Expected Data Volume

Fairfax County has ~500K+ sales records historically, compared to Loudoun's ~47K.
Raw downloads may be 300-500 MB. Processed files should be 10-20 MB.

## Processing Workflow

See `raw/README.md` for download and processing instructions.
