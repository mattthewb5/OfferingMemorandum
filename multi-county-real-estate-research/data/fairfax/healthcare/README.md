# Fairfax County Healthcare Facilities

Healthcare facility data including hospitals and urgent care centers with quality ratings.

## Data Source

**Primary:** Fairfax County GIS - Hospitals and Urgent Care Facilities (2026-01-26)
**Quality Data:** CMS Hospital Compare (2025-12-28), Leapfrog Hospital Safety Grade (Fall 2024)

## Current Dataset

| Metric | Value |
|--------|-------|
| Total Facilities | 77 |
| Hospitals | 13 |
| Urgent Care | 64 |
| With CMS Ratings | 6 hospitals |
| With Leapfrog Grades | 6 hospitals |

### Hospital Quality Ratings

| Hospital | CMS Rating | Leapfrog Grade | Notes |
|----------|------------|----------------|-------|
| Inova Fairfax Hospital | ⭐⭐⭐⭐⭐ (5) | A | 27+ consecutive A |
| Inova Fair Oaks Hospital | ⭐⭐⭐⭐⭐ (5) | A | 27+ consecutive A |
| Virginia Hospital Center | ⭐⭐⭐⭐⭐ (5) | A | Top Hospital |
| Inova Alexandria Hospital | ⭐⭐⭐⭐ (4) | A | |
| Reston Hospital Center | ⭐⭐⭐ (3) | A | 5 consecutive A |
| Inova Mount Vernon Hospital | ⭐⭐⭐ (3) | B | |

### Facilities Without Ratings

The following facilities don't have CMS ratings (typically specialty or military facilities):
- Dominion Hospital (Psychiatric)
- Fort Belvoir Community Hospital (Military)
- Inova Emergency Care Centers (ER only, not full hospitals)

## Directory Structure

```
healthcare/
├── extracted/                    # Extracted shapefile data
│   └── Hospitals_and_Urgent_Care_Facilities.*
├── processed/
│   ├── facilities.parquet        # Main dataset with quality ratings
│   └── metadata.json             # Data provenance and statistics
└── README.md
```

## Schema

| Field | Type | Description |
|-------|------|-------------|
| facility_id | int | Unique identifier |
| name | string | Facility name |
| facility_type | string | 'hospital' or 'urgent_care' |
| address | string | Street address |
| city | string | City |
| state | string | State (VA) |
| zip_code | string | ZIP code |
| phone | string | Phone number |
| website | string | Website URL |
| latitude | float | WGS84 latitude |
| longitude | float | WGS84 longitude |
| cms_facility_id | string | CMS Medicare Provider ID |
| cms_rating | int | CMS star rating (1-5) |
| leapfrog_grade | string | Leapfrog safety grade (A-F) |
| leapfrog_date | string | Grade period (e.g., 'Fall 2024') |
| leapfrog_notes | string | Additional notes (e.g., 'Top Hospital') |
| emergency_services | string | 'Yes' or 'No' |
| hospital_type | string | CMS hospital classification |

## Analysis Module

Python module: `core/fairfax_healthcare_analysis.py`

### Usage

```python
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis

analyzer = FairfaxHealthcareAnalysis()

# Healthcare access score
access = analyzer.calculate_healthcare_access_score(lat=38.8462, lon=-77.3064)
print(f"Access: {access['score']}/100 ({access['rating']})")

# Quality metrics for specific hospital
metrics = analyzer.get_quality_metrics("INOVA FAIRFAX")
print(f"Rating: {metrics['cms_rating']} stars, Grade: {metrics['leapfrog_grade']}")

# Compare nearby hospitals
comparison = analyzer.compare_facilities(lat=38.8462, lon=-77.3064, top_n=5)
```

### Functions

- `get_facilities_near_point()` - Spatial query for nearby facilities
- `calculate_healthcare_access_score()` - Access score (0-100) with rating
- `get_quality_metrics()` - CMS/Leapfrog quality data for facility
- `compare_facilities()` - Ranked comparison by quality & distance

## Access Score Interpretation

| Score | Rating | Description |
|-------|--------|-------------|
| 85-100 | Excellent Access | Multiple quality hospitals nearby |
| 70-84 | Good Access | Hospital within 5 miles |
| 55-69 | Moderate Access | Hospital within 10 miles |
| 40-54 | Limited Access | Distant from hospitals |
| 0-39 | Poor Access | Very limited options |

## Data Quality

- **Geographic:** 100% facilities have valid coordinates (WGS84)
- **CMS Coverage:** 6 of 13 hospitals matched (remaining are specialty/military)
- **Leapfrog Coverage:** 6 hospitals with safety grades
- **Contact Info:** 100% have phone numbers
- **Websites:** 100% have website URLs

## Refresh Schedule

- **Base Facilities:** Annual (stable data)
- **CMS Ratings:** Quarterly (follows CMS release schedule)
- **Leapfrog Grades:** Bi-annual (Spring/Fall releases)

## Data Sources

### CMS Hospital Compare
- Website: https://data.cms.gov/provider-data/
- Update Frequency: Quarterly
- Key Metrics: Overall rating (1-5 stars), mortality, safety, readmission, patient experience

### Leapfrog Hospital Safety Grade
- Website: https://www.hospitalsafetygrade.org/
- Update Frequency: Twice yearly (Spring/Fall)
- Key Metrics: Safety grade (A-F), infection rates, medication safety

## Use Cases

1. **Property Assessment** - Healthcare access score for any location
2. **Hospital Selection** - Compare quality ratings of nearby hospitals
3. **Urgent Care Finder** - Find nearest urgent care facilities
4. **Investment Analysis** - Areas with better healthcare access may command premium pricing
