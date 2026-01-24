# Building Permits - Processed Files

**These files ARE committed to GitHub**

## Contents

- `permits.parquet` - Geocoded and filtered permit data

## Attributes

Key fields preserved:
- `PERMIT_NUMBER` - Unique permit identifier
- `ADDRESS` - Property address
- `PERMIT_TYPE` - Type of work (new construction, renovation, etc.)
- `VALUE` - Estimated project value
- `ISSUE_DATE` - Permit issue date
- `STATUS` - Current permit status
- `LAT`, `LON` - Geocoded coordinates

## Loading Data

```python
import pandas as pd

permits = pd.read_parquet('permits.parquet')
print(f"Loaded {len(permits):,} permits")

# Filter to recent permits
recent = permits[permits.ISSUE_DATE >= '2024-01-01']
```
