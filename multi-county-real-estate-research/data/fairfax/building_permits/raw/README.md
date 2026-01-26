# Building Permits - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download building permit data from Fairfax County sources.

Expected files:
- Permit CSV/Excel exports
- May include multiple years or permit types

## Processing Steps

1. **Download** permit data from county portal

2. **Geocode** if needed:
   - Add lat/lon coordinates from permit addresses
   - Use county geocoding service or batch geocoder

3. **Filter** to relevant fields:
   - Keep: permit number, address, type, value, date, status
   - Drop: internal tracking fields, inspector notes

4. **Convert to Parquet**:
   ```python
   import pandas as pd
   permits = pd.read_csv('raw/permits.csv')
   permits.to_parquet('../processed/permits.parquet')
   ```

## File Locations

- Raw files: Stay here (local only)
- Processed files: ../processed/ (committed to GitHub)
