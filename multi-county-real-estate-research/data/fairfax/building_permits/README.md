# Fairfax County Building Permits

Building permit data for Fairfax County development activity analysis.

## Data Source

**Source:** Building Records PLUS ArcGIS API
**API Endpoint:** https://services1.arcgis.com/ioennV6PpG5Xodq0/ArcGIS/rest/services/Building_Records_PLUS/FeatureServer/0
**Authentication:** None required (public data)
**Update Frequency:** Nightly (source), Weekly refresh recommended

## Current Dataset

| Metric | Value |
|--------|-------|
| Total Permits | 41,504 |
| Date Range | 2022-01-03 to 2026-01-23 |
| File Size | ~4 MB |
| Geometry Coverage | 100% |
| Parcel Linkage | 100% |

### By Category
- **Residential:** 30,213 (72.8%)
  - New Construction: 5,687
  - Renovations: 24,526
- **Commercial:** 11,291 (27.2%)
  - New Construction: 1,891
  - Renovations: 9,400

### By Year
| Year | Permits |
|------|---------|
| 2022 | 11,901 |
| 2023 | 10,584 |
| 2024 | 9,601 |
| 2025 | 9,131 |
| 2026 | 287 |

## Directory Structure

```
building_permits/
├── raw/
│   └── api/              # API responses (LOCAL ONLY - not committed)
├── processed/
│   ├── permits.parquet   # Main dataset with geometry
│   └── metadata.json     # Data provenance and statistics
└── README.md
```

## Schema

| Field | Type | Description |
|-------|------|-------------|
| permit_id | string | Unique permit identifier (RECORDID) |
| permit_type | string | Specific permit type (36 types) |
| permit_category | string | Detailed category (residential_new, commercial_renovation, etc.) |
| permit_major_category | string | Major category (residential, commercial, other) |
| project_name | string | Project name if provided |
| status | string | Current status (Issued, Closed, etc.) |
| parcel_id | string | Links to tax parcel data |
| address | string | Property address |
| city | string | City name |
| state | string | State (VA) |
| zip_code | string | ZIP code |
| submitted_date | datetime | Date submitted |
| accepted_date | datetime | Date accepted |
| issued_date | datetime | Date issued |
| closed_date | datetime | Date closed |
| approved_date | datetime | Date approved |
| supervisor_district | string | Fairfax County supervisor district |
| document_url | string | Link to permit documents |
| centroid_lon | float | Longitude (WGS84) |
| centroid_lat | float | Latitude (WGS84) |
| has_geometry | bool | Whether polygon geometry exists |
| ingestion_date | datetime | Date of ETL processing |

## Permit Types

### Residential (36 types total)
- Residential New
- Residential Addition/Alteration
- Residential Demolition
- Residential Electrical
- Residential Mechanical
- Residential Plumbing
- Residential Solar
- Residential Retaining Wall
- Residential Miscellaneous

### Commercial
- Commercial New
- Commercial Addition/Alteration
- Commercial Demolition
- Commercial Electrical
- Commercial Mechanical
- Commercial Plumbing
- Commercial Solar
- Commercial Retaining Wall
- Commercial Miscellaneous

### Other
- Certificate of Occupancy
- Elevator permits
- Building Permit Amendment
- Code Appeal/Modification
- Damage Report

## Usage Examples

### Load Data
```python
import pandas as pd

# Load permits
df = pd.read_parquet('data/fairfax/building_permits/processed/permits.parquet')

# Filter to residential new construction
new_homes = df[df['permit_category'] == 'residential_new']
```

### Get Permits Near a Location
```python
from scripts.fairfax_permits_etl import get_permits_near_point

# Load data
df = pd.read_parquet('data/fairfax/building_permits/processed/permits.parquet')

# Get permits within 1 mile of a point
nearby = get_permits_near_point(df, lat=38.9, lon=-77.3, radius_miles=1.0)
```

### Calculate Development Pressure
```python
from scripts.fairfax_permits_etl import calculate_development_pressure

pressure = calculate_development_pressure(df, lat=38.9, lon=-77.3)
print(f"Development Pressure Score: {pressure['score']}/100")
print(f"Trend: {pressure['trend']}")
```

## ETL Script

**Script:** `scripts/fairfax_permits_etl.py`

```bash
# Full download (2022-present)
python scripts/fairfax_permits_etl.py

# Incremental update (last 30 days)
python scripts/fairfax_permits_etl.py --recent

# Test mode (100 records)
python scripts/fairfax_permits_etl.py --test

# Analyze a location
python scripts/fairfax_permits_etl.py --analyze 38.9 -77.3
```

## Use Cases

1. **Development Pressure Analysis**
   - Count permits in an area
   - Weight by type (new construction vs renovation)
   - Track trends over time

2. **Property Research**
   - Find permits for a specific property via parcel_id
   - Check renovation history
   - Identify new construction nearby

3. **Market Intelligence**
   - Track new construction activity by area
   - Identify hot spots for development
   - Monitor commercial vs residential trends

4. **Investment Analysis**
   - Areas with high renovation activity may indicate gentrification
   - New construction clusters may indicate growth areas
   - Demolition permits may signal redevelopment

## Processing Notes

- Coordinates are converted from Virginia State Plane North (EPSG:2283) to WGS84 (EPSG:4326)
- Polygon centroids are used for distance calculations
- Permits without issued_date fall back to submitted_date
- The ETL respects API rate limits with 1.5s delays between requests

## Refresh Schedule

- **Recommended:** Weekly refresh via `--recent` flag
- **Full Refresh:** Monthly or as needed
- **Source Updates:** Nightly from Fairfax County
