# Fairfax County - Integration Guide

Complete guide for using Fairfax County analysis modules.

## Available Modules

1. **Crime Analysis** - Safety scoring and crime density
2. **Building Permits Analysis** - Development pressure and construction activity

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

## Feature Examples

### Property Detail Page
```python
def get_property_intelligence(lat, lon):
    """Get complete property intelligence."""

    crime_analyzer = FairfaxCrimeAnalysis()
    permits_analyzer = FairfaxPermitsAnalysis()

    # Crime analysis
    safety = crime_analyzer.calculate_safety_score(lat, lon, 0.5, 6)
    crime_trends = crime_analyzer.get_crime_trends(lat, lon, 0.5, 12)

    # Permits analysis
    development = permits_analyzer.calculate_development_pressure(lat, lon, 1.0, 24)
    permit_trends = permits_analyzer.get_permit_trends(lat, lon, 1.0, 24)

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

## Data Refresh

Both modules automatically use the latest data:
- **Crime**: Updated daily via GitHub Actions
- **Permits**: Updated weekly via GitHub Actions

No manual refresh needed - just reload the module.

## Performance Notes

- Crime module: ~1,000 incidents (fast queries)
- Permits module: ~41,000 permits (slightly slower, still <1 sec)
- Both use in-memory DataFrames (no database required)
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

## Testing

Run the test suite to verify modules:
```bash
cd multi-county-real-estate-research
python tests/test_fairfax_analysis.py
```

Expected output:
```
Crime Analysis Module:    PASS
Permits Analysis Module:  PASS
ALL MODULES PASSED - Ready for integration!
```
