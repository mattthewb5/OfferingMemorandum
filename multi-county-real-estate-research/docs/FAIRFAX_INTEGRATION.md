# Fairfax County - Integration Guide

Complete guide for using Fairfax County analysis modules.

## Available Modules

1. **Crime Analysis** - Safety scoring and crime density
2. **Building Permits Analysis** - Development pressure and construction activity
3. **Healthcare Analysis** - Healthcare access scoring and quality metrics
4. **Subdivisions Analysis** - Neighborhood identification and boundary lookups

## Quick Start

### Crime Analysis
```python
from core.fairfax_crime_analysis import FairfaxCrimeAnalysis

analyzer = FairfaxCrimeAnalysis()

# For a property at lat=38.8462, lon=-77.3064
safety = analyzer.calculate_safety_score(38.8462, -77.3064, radius_miles=0.5)

# Display results
print(f"Safety Score: {safety['score']}/100")
print(f"Rating: {safety['rating']}")
print(f"Nearby crimes (6 months): {safety['total_crimes']}")
print(f"Violent: {safety['breakdown']['violent']}")
print(f"Property: {safety['breakdown']['property']}")
```

### Building Permits Analysis
```python
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis

analyzer = FairfaxPermitsAnalysis()

# For same property
pressure = analyzer.calculate_development_pressure(38.8462, -77.3064, radius_miles=1.0)

# Display results
print(f"Development Pressure: {pressure['score']}/100")
print(f"Trend: {pressure['trend']}")
print(f"Permits (24 months): {pressure['total_permits']}")
```

### Healthcare Analysis
```python
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis

analyzer = FairfaxHealthcareAnalysis()

# Healthcare access score
access = analyzer.calculate_healthcare_access_score(38.8462, -77.3064)

# Display results
print(f"Healthcare Access: {access['score']}/100")
print(f"Rating: {access['rating']}")
print(f"Hospitals within 10mi: {access['hospitals_within_10mi']}")

# Get quality metrics for specific hospital
metrics = analyzer.get_quality_metrics("INOVA FAIRFAX")
print(f"CMS Rating: {metrics['cms_rating']} stars")
print(f"Leapfrog Grade: {metrics['leapfrog_grade']}")
```

### Subdivisions Analysis
```python
from core.fairfax_subdivisions_analysis import FairfaxSubdivisionsAnalysis

analyzer = FairfaxSubdivisionsAnalysis()

# Look up subdivision for a property
subdivision = analyzer.get_subdivision(38.8969, -77.4327)

# Display results
if subdivision['found']:
    print(f"Subdivision: {subdivision['subdivision_name']}")
    print(f"Section: {subdivision['section'] or 'N/A'}")
    print(f"Plat Date: {subdivision['record_date'] or 'N/A'}")
else:
    print(f"Not in recorded subdivision: {subdivision['message']}")

# Find nearby subdivisions
nearby = analyzer.get_nearby_subdivisions(38.8969, -77.4327, radius_miles=1.0)
for sub in nearby[:5]:
    print(f"  {sub['subdivision_name']}: {sub['distance_miles']} mi")

# Search by name
results = analyzer.search_subdivisions("RESTON", limit=10)
```

## Feature Examples

### Property Detail Page
```python
from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
from core.fairfax_subdivisions_analysis import FairfaxSubdivisionsAnalysis

def get_property_intelligence(lat, lon):
    """Get complete property intelligence."""

    crime_analyzer = FairfaxCrimeAnalysis()
    permits_analyzer = FairfaxPermitsAnalysis()
    healthcare_analyzer = FairfaxHealthcareAnalysis()
    subdivisions_analyzer = FairfaxSubdivisionsAnalysis()

    # Crime analysis
    safety = crime_analyzer.calculate_safety_score(lat, lon, 0.5, 6)
    crime_trends = crime_analyzer.get_crime_trends(lat, lon, 0.5, 12)

    # Permits analysis
    development = permits_analyzer.calculate_development_pressure(lat, lon, 1.0, 24)
    permit_trends = permits_analyzer.get_permit_trends(lat, lon, 1.0, 24)

    # Healthcare analysis
    healthcare = healthcare_analyzer.calculate_healthcare_access_score(lat, lon)

    # Subdivision lookup
    subdivision = subdivisions_analyzer.get_subdivision(lat, lon)

    return {
        'safety': {
            'score': safety['score'],
            'rating': safety['rating'],
            'trend': crime_trends['trend']
        },
        'development': {
            'score': development['score'],
            'trend': development['trend'],
            'permits_24mo': development['total_permits']
        },
        'healthcare': {
            'score': healthcare['score'],
            'rating': healthcare['rating'],
            'hospitals_nearby': healthcare['hospitals_within_10mi'],
            'urgent_care_nearby': healthcare['urgent_care_within_3mi']
        },
        'subdivision': {
            'name': subdivision['subdivision_name'],
            'section': subdivision['section'],
            'found': subdivision['found']
        }
    }
```

### Map Visualization
```python
import numpy as np

def get_area_heatmap_data(bounds, resolution=0.1):
    """Generate heatmap data for map overlay."""

    analyzer = FairfaxCrimeAnalysis()

    points = []
    for lat in np.arange(bounds['south'], bounds['north'], resolution):
        for lon in np.arange(bounds['west'], bounds['east'], resolution):
            safety = analyzer.calculate_safety_score(lat, lon, 0.25, 6)
            points.append({
                'lat': lat,
                'lon': lon,
                'safety_score': safety['score']
            })

    return points
```

## API Reference

### FairfaxCrimeAnalysis

#### `calculate_safety_score(lat, lon, radius_miles=0.5, months_back=6)`

Calculate a safety score (0-100) for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 0.5 miles)
- `months_back`: Time period to analyze (default: 6 months)

**Returns:**
```python
{
    'score': 94,           # 0-100 (higher = safer)
    'rating': 'Very Safe', # Rating string
    'total_crimes': 12,
    'breakdown': {
        'violent': 0,
        'property': 0,
        'other': 12
    },
    'radius_miles': 0.5,
    'months_back': 6
}
```

#### `get_crime_trends(lat, lon, radius_miles=0.5, months_back=12)`

Analyze crime trends over time.

**Returns:**
```python
{
    'trend': 'stable',      # 'increasing', 'stable', 'decreasing', 'insufficient_data'
    'first_half_count': 5,
    'second_half_count': 7,
    'change_pct': 40.0,
    'total_crimes': 12
}
```

#### `get_crime_breakdown(lat, lon, radius_miles=0.5, months_back=6)`

Get detailed crime breakdown by category.

**Returns:**
```python
{
    'total': 12,
    'violent': {'count': 0, 'percentage': 0.0},
    'property': {'count': 0, 'percentage': 0.0},
    'other': {'count': 12, 'percentage': 100.0}
}
```

#### `get_crimes_near_point(lat, lon, radius_miles=0.5, months_back=None, category_filter=None)`

Get crimes within radius of a point.

**Returns:** DataFrame with nearby crimes, sorted by distance.

### FairfaxPermitsAnalysis

#### `calculate_development_pressure(lat, lon, radius_miles=1.0, months_back=24)`

Calculate a development pressure score (0-100) for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 1.0 miles)
- `months_back`: Time period to analyze (default: 24 months)

**Returns:**
```python
{
    'score': 85,              # 0-100 (higher = more activity)
    'trend': 'increasing',    # 'increasing', 'stable', 'decreasing', 'insufficient_data'
    'total_permits': 246,
    'breakdown': {
        'residential_new': {'count': 94, 'weight': 10, 'contribution': 940},
        'commercial_renovation': {'count': 65, 'weight': 5, 'contribution': 325},
        ...
    },
    'radius_miles': 1.0,
    'months_back': 24
}
```

#### `get_permit_trends(lat, lon, radius_miles=1.0, months_back=24)`

Get permit trends by year and category.

**Returns:**
```python
{
    'yearly': {2024: 129, 2025: 113, 2026: 4},
    'by_category': {2024: {'residential_new': 50, ...}, ...},
    'by_major_category': {2024: {'residential': 80, 'commercial': 49}, ...}
}
```

#### `get_permit_breakdown(lat, lon, radius_miles=1.0, months_back=24)`

Get detailed permit breakdown by type.

**Returns:**
```python
{
    'total': 246,
    'by_major_category': {
        'residential': {'count': 159, 'percentage': 64.6},
        'commercial': {'count': 87, 'percentage': 35.4}
    },
    'by_detailed_category': {
        'residential_new': {'count': 94, 'percentage': 38.2},
        ...
    }
}
```

#### `get_permits_near_point(lat, lon, radius_miles=1.0, months_back=None, category_filter=None)`

Get permits within radius of a point.

**Returns:** DataFrame with nearby permits, sorted by distance.

### FairfaxHealthcareAnalysis

#### `calculate_healthcare_access_score(lat, lon)`

Calculate a healthcare access score (0-100) for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'score': 100,                    # 0-100 (higher = better access)
    'rating': 'Excellent Access',    # Rating string
    'hospitals_within_10mi': 7,
    'urgent_care_within_3mi': 5,
    'breakdown': {
        'nearest_hospital': {
            'name': 'INOVA FAIR OAKS HOSPITAL',
            'distance_miles': 2.5,
            'cms_rating': 5,
            'leapfrog_grade': 'A'
        },
        'urgent_care_nearby': {'count_within_3mi': 5}
    }
}
```

#### `get_quality_metrics(facility_name)`

Get quality metrics for a specific facility.

**Returns:**
```python
{
    'name': 'INOVA FAIRFAX HOSPITAL',
    'facility_type': 'hospital',
    'cms_facility_id': '490063',
    'cms_rating': 5,
    'leapfrog_grade': 'A',
    'leapfrog_notes': '27+ consecutive A',
    'emergency_services': 'Yes',
    'address': '3300 GALLOWS RD',
    'city': 'FALLS CHURCH',
    'phone': '(703) 776-4001'
}
```

#### `compare_facilities(lat, lon, radius_miles=10.0, facility_type='hospital', top_n=5)`

Compare nearby facilities ranked by quality and distance.

**Returns:** DataFrame with ranked facilities including composite scores.

#### `get_facilities_near_point(lat, lon, radius_miles=10.0, facility_type=None)`

Get healthcare facilities within radius of a point.

**Returns:** DataFrame with nearby facilities, sorted by distance.

### FairfaxSubdivisionsAnalysis

#### `get_subdivision(lat, lon)`

Get the subdivision containing a point.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'found': True,                         # Whether point is in a subdivision
    'subdivision_name': 'DULLES BUSINESS PARK',
    'section': None,                       # Section number if available
    'phase': None,                         # Phase if available
    'block': None,                         # Block if available
    'record_date': '2005-03-15',          # Plat recording date
    'deed_book': 'DB1234',                # Deed book reference
    'deed_page': '567',                   # Deed page reference
    'message': None                        # Error message if not found
}
```

#### `get_nearby_subdivisions(lat, lon, radius_miles=1.0, limit=10)`

Get subdivisions near a point (by centroid distance).

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 1.0 miles)
- `limit`: Maximum number of results (default: 10)

**Returns:**
```python
[
    {
        'subdivision_name': 'RESTON',
        'distance_miles': 0.25,
        'section': '39',
        'phase': None,
        'record_date': '1985-06-20'
    },
    ...
]
```

#### `get_subdivision_stats()`

Get summary statistics about the subdivision dataset.

**Returns:**
```python
{
    'total_features': 11430,
    'unique_subdivision_names': 4927,
    'top_subdivisions_by_sections': {
        'RESTON': 439,
        'NORTH SPRINGFIELD': 62,
        ...
    },
    'geographic_bounds': {
        'min_longitude': -77.537,
        'min_latitude': 38.617,
        'max_longitude': -77.042,
        'max_latitude': 39.058
    },
    'date_range': {
        'earliest': '1870-06-01',
        'latest': '2025-12-30'
    },
    'features_with_section': 3052,
    'features_with_phase': 201
}
```

#### `search_subdivisions(name_pattern, limit=20)`

Search for subdivisions by name (case-insensitive partial match).

**Returns:**
```python
[
    {'subdivision_name': 'RESTON', 'section_count': 439},
    {'subdivision_name': 'GLADE CLUSTER - RESTON', 'section_count': 3},
    ...
]
```

## Data Refresh

All modules automatically use the latest data:
- **Crime**: Updated daily via GitHub Actions
- **Permits**: Updated weekly via GitHub Actions
- **Healthcare**: Base data annual, CMS quarterly, Leapfrog bi-annual
- **Subdivisions**: Static (boundaries rarely change)

No manual refresh needed - just reload the module.

## Performance Notes

- Crime module: ~1,000 incidents (fast queries)
- Permits module: ~41,000 permits (slightly slower, still <1 sec)
- Healthcare module: ~77 facilities (fast queries)
- Subdivisions module: ~11,430 polygons with spatial indexing (fast point-in-polygon)
- All use in-memory DataFrames/GeoDataFrames (no database required)
- Consider caching results for frequently-queried locations

## Error Handling
```python
try:
    analyzer = FairfaxCrimeAnalysis()
    safety = analyzer.calculate_safety_score(lat, lon)
except FileNotFoundError:
    print("Crime data not available")
except Exception as e:
    print(f"Analysis error: {e}")
```

## Score Interpretation

### Safety Score (Crime)
| Score | Rating | Description |
|-------|--------|-------------|
| 85-100 | Very Safe | Minimal crime activity |
| 70-84 | Safe | Low crime activity |
| 50-69 | Moderate | Average crime activity |
| 30-49 | Caution Advised | Above average crime |
| 0-29 | High Crime Area | Significant crime activity |

### Development Pressure Score (Permits)
| Score | Level | Description |
|-------|-------|-------------|
| 75-100 | Very High | Major development activity |
| 50-74 | High | Significant construction |
| 25-49 | Moderate | Average activity |
| 0-24 | Low | Minimal construction |

### Healthcare Access Score
| Score | Rating | Description |
|-------|--------|-------------|
| 85-100 | Excellent Access | Multiple quality hospitals nearby |
| 70-84 | Good Access | Hospital within 5 miles |
| 55-69 | Moderate Access | Hospital within 10 miles |
| 40-54 | Limited Access | Distant from hospitals |
| 0-39 | Poor Access | Very limited options |

## Testing

Run the test suite to verify modules:
```bash
cd multi-county-real-estate-research
python tests/test_fairfax_analysis.py
```

Expected output:
```
Crime Analysis Module:       PASS
Permits Analysis Module:     PASS
Healthcare Analysis Module:  PASS
Subdivisions Analysis Module: PASS
ALL MODULES PASSED - Ready for integration!
```
