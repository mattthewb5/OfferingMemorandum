# Fairfax County Crime Data

*Last Updated: 2026-01-26*

## Data Sources

### 1. Weekly API (PRIMARY - Ongoing)
- **Endpoint:** `https://www.fairfaxcounty.gov/apps/pfsu/api/file/crimereportsfromsp`
- **Format:** CSV (no header)
- **Coverage:** Rolling ~7-9 days of current incidents
- **Update:** Daily ETL accumulates data over time
- **Authentication:** None required

### 2. FBI NIBRS (SECONDARY - Historical)
- **Source:** FBI Crime Data Explorer (https://cde.ucr.cjis.gov/)
- **Format:** ZIP/CSV (NIBRS incident-level)
- **Coverage:** 2019-2024 (5 years historical)
- **Status:** Manual download required (see instructions below)

## Directory Structure

```
crime/
├── raw/
│   ├── weekly/           # Daily API fetches (date-partitioned)
│   ├── fbi/              # FBI NIBRS downloads (manual)
│   └── geocoded/         # Address geocoding cache
├── processed/
│   ├── incidents.parquet # Unified incident dataset
│   └── metadata.json     # Data provenance tracking
└── README.md
```

## Unified Schema

| Field | Type | Description |
|-------|------|-------------|
| incident_id | string | Unique identifier (date_time_code_address) |
| crime_code | string | Crime classification code (e.g., LARC-23-3) |
| description | string | Human-readable description |
| category | string | VIOLENT, PROPERTY, or OTHER |
| date | date | Date of incident (YYYY-MM-DD) |
| time | string | Time of incident (HHMM 24-hour) |
| address | string | Location (100-block anonymized) |
| city | string | City/area code |
| state | string | State (VA) |
| zip | string | ZIP code |
| latitude | float | Geocoded latitude (if available) |
| longitude | float | Geocoded longitude (if available) |
| source | string | Data source (weekly_api or fbi_nibrs) |
| ingestion_date | date | When record was ingested |

## Crime Categories

**VIOLENT** (codes: ASSLT, ROB, HOMICIDE, RAPE, KIDNAP, MURDER)

**PROPERTY** (codes: LARC, BURG, AUTO, DEST, FRAUD, FORG, THEFT, ARSON)

**OTHER** (service calls, suspicious activity, warrants, etc.)

## Usage

### Load Crime Data
```python
import pandas as pd

crimes = pd.read_parquet('data/fairfax/crime/processed/incidents.parquet')
print(f"Total incidents: {len(crimes)}")
```

### Filter by Category
```python
violent = crimes[crimes['category'] == 'VIOLENT']
property_crimes = crimes[crimes['category'] == 'PROPERTY']
```

### Get Crimes Near Location
```python
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 3956 * 2 * asin(sqrt(a))  # Miles

# Crimes within 0.5 miles
geocoded = crimes[crimes['latitude'].notna()].copy()
geocoded['distance'] = geocoded.apply(
    lambda x: haversine(-77.3064, 38.8462, x['longitude'], x['latitude']), axis=1
)
nearby = geocoded[geocoded['distance'] <= 0.5]
```

## Running the ETL

```bash
# Fetch weekly data
python3 scripts/fairfax_crime_etl.py --fetch-weekly

# With more geocoding
python3 scripts/fairfax_crime_etl.py --fetch-weekly --max-geocode 500

# Show FBI download instructions
python3 scripts/fairfax_crime_etl.py --show-fbi-instructions
```

## Daily Automation

```bash
# Linux cron (6 AM daily)
0 6 * * * /path/to/scripts/run_daily_crime_update.sh >> /var/log/crime_etl.log 2>&1
```

## Privacy Notes

- Addresses are 100-block anonymized by Fairfax County
- Geocoding produces approximate coordinates
- No victim/suspect information available
- Compliant with Fairfax County Trust Policy
