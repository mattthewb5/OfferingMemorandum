# Sales Data - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download raw sales data from Fairfax County Tax Administration:
- `tax_administrations_real_estate_sales_data.csv` (full download)
- Any Excel exports from county systems

Expected size: 200-500 MB (too large for GitHub)

## Processing Steps

1. **Download** sales data from:
   https://data-fairfaxcountygis.opendata.arcgis.com/datasets/tax-administrations-real-estate-sales-data

2. **Filter** to recent years:
   - Keep sales from 2020-2025 (last 5 years)
   - Remove non-arms-length transactions
   - Expected reduction: ~500 MB → ~100 MB

3. **Convert to Parquet**:
   ```bash
   python scripts/convert_sales_to_parquet.py --county fairfax --input sales/raw/file.csv --output sales/processed/combined_sales.parquet
   ```

4. **Result**: Parquet file ~10-20 MB (100x compression)

## File Locations

- Raw files: Stay here (local only)
- Processed files: ../processed/ (committed to GitHub)
