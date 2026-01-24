# Crime Data - Processed Files

**These files ARE committed to GitHub**

## Contents

- `crime.parquet` - Processed crime incident data

## Attributes

Key fields preserved:
- `DATE` - Incident date
- `CRIME_TYPE` - Standardized crime category
- `LOCATION` - Generalized location (block level)
- `LAT`, `LON` - Approximate coordinates

## Loading Data

```python
import pandas as pd

crime = pd.read_parquet('crime.parquet')
print(f"Loaded {len(crime):,} incidents")

# Analyze by type
crime.groupby('CRIME_TYPE').size().sort_values(ascending=False)
```

## Privacy Considerations

Location data is generalized to protect privacy.
Use for aggregate analysis only.
