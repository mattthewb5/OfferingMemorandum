# Crime Data - Raw Files (LOCAL ONLY)

**Files in this directory are NOT committed to GitHub**

## What Goes Here

Download crime incident data from Fairfax County sources.

Expected files:
- Crime incident CSV exports
- Multiple years of historical data

## Processing Steps

1. **Download** crime data from county portal

2. **Clean and standardize**:
   - Normalize crime type categories
   - Parse dates consistently
   - Validate coordinates

3. **Filter** to relevant fields:
   - Keep: date, crime type, location (generalized), severity
   - Drop: case numbers, victim/suspect details

4. **Convert to Parquet**:
   ```python
   import pandas as pd
   crime = pd.read_csv('raw/crime_incidents.csv')
   crime.to_parquet('../processed/crime.parquet')
   ```

## File Locations

- Raw files: Stay here (local only)
- Processed files: ../processed/ (committed to GitHub)
