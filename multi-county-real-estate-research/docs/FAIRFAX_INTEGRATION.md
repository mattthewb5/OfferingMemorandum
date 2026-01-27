# Fairfax County - Integration Guide

Complete guide for using Fairfax County analysis modules.

## Available Modules

1. **Crime Analysis** - Safety scoring and crime density
2. **Building Permits Analysis** - Development pressure and construction activity
3. **Healthcare Analysis** - Healthcare access scoring and quality metrics
4. **Subdivisions Analysis** - Neighborhood identification and boundary lookups
5. **Schools Analysis** - School assignments and facility lookups
6. **Zoning Analysis** - Zoning districts, overlays, and land use
7. **Flood Analysis** - FEMA flood zones, dam inundation, and easements
8. **Utilities Analysis** - Power line, gas, and telephone proximity
9. **Parks Analysis** - Park access scoring, trails, and recreational amenities
10. **Transit Analysis** - Metro and bus accessibility scoring

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

### Schools Analysis
```python
from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis

analyzer = FairfaxSchoolsAnalysis()

# Get assigned schools for a property
schools = analyzer.get_assigned_schools(38.8969, -77.4327)

# Display results
if schools['all_assigned']:
    print(f"Elementary: {schools['elementary']['school_name']}")
    print(f"  Distance: {schools['elementary']['distance_miles']} miles")
    print(f"Middle: {schools['middle']['school_name']}")
    print(f"High: {schools['high']['school_name']}")

# Find nearby elementary schools
nearby = analyzer.get_school_facilities(
    38.8969, -77.4327,
    radius_miles=3.0,
    school_types=['ES'],
    limit=5
)
for school in nearby:
    print(f"  {school['school_name']}: {school['distance_miles']} mi")
```

### Zoning Analysis
```python
from core.fairfax_zoning_analysis import FairfaxZoningAnalysis

analyzer = FairfaxZoningAnalysis()

# Get zoning for a property
zoning = analyzer.get_zoning(38.8969, -77.4327)

# Display results
print(f"Zone Code: {zoning['zone_code']}")
print(f"Zone Type: {zoning['zone_type']}")
print(f"Description: {zoning['zone_description']}")
print(f"Has Proffer: {zoning['has_proffer']}")

# Check for overlays
for overlay in zoning['overlays']:
    print(f"Overlay: {overlay['overlay_type']}")
    if 'decibel_level' in overlay:
        print(f"  Noise Level: {overlay['decibel_level']} dB")

# Check airport noise
noise = analyzer.check_airport_noise(38.8969, -77.4327)
if noise:
    print(f"Airport Noise: {noise['decibel_level']} dB")
```

### Flood Analysis
```python
from core.fairfax_flood_analysis import FairfaxFloodAnalysis

analyzer = FairfaxFloodAnalysis()

# Get comprehensive flood risk
flood = analyzer.get_flood_risk(38.8969, -77.4327)

# Display results
print(f"Overall Risk: {flood['overall_risk']}")
print(f"Insurance Required: {flood['insurance_required']}")

if flood['fema_zone']:
    print(f"FEMA Zone: {flood['fema_zone']['zone_code']}")
    print(f"Risk Level: {flood['fema_zone']['risk_level']}")
    print(f"Description: {flood['fema_zone']['zone_description']}")

# Check dam inundation risks
for dam in flood['dam_inundation_risks']:
    print(f"Dam Risk: {dam['dam_name']}")

# Check floodplain easement
if flood['floodplain_easement']['in_easement']:
    print("Property is in a recorded floodplain easement")
```

### Utilities Analysis
```python
from core.fairfax_utilities_analysis import FairfaxUtilitiesAnalysis

analyzer = FairfaxUtilitiesAnalysis()

# Check proximity to utility lines (for disclosure)
proximity = analyzer.check_proximity(38.8969, -77.4327, distance_threshold_miles=0.1)
if proximity['within_threshold']:
    print(f"Property within 0.1 mi of utility lines:")
    for u in proximity['utilities_within_threshold']:
        print(f"  {u['utility_type']}: {u['distance_miles']} mi")

# Get nearby utilities
nearby = analyzer.get_nearby_utilities(38.8969, -77.4327, radius_miles=0.5)
for utility in nearby[:3]:
    print(f"  {utility['utility_type']}: {utility['operator']} ({utility['distance_miles']} mi)")

# Summary by utility type
by_type = analyzer.get_utility_types_nearby(38.8969, -77.4327, radius_miles=0.5)
print(f"Electric: {by_type['electric']['count']} lines")
print(f"Gas: {by_type['gas']['count']} lines")
```

### Parks Analysis
```python
from core.fairfax_parks_analysis import FairfaxParksAnalysis

analyzer = FairfaxParksAnalysis()

# Calculate park access score
score = analyzer.calculate_park_access_score(38.8462, -77.3064)
print(f"Park Access Score: {score['score']}/100 ({score['rating']})")
print(f"Parks within 1 mi: {score['parks_within_1mi']}")
print(f"Trail miles within 1 mi: {score['trail_miles_within_1mi']}")
print(f"Playgrounds within 0.5 mi: {score['playgrounds_within_half_mi']}")

# Get nearby parks
nearby = analyzer.get_nearby_parks(38.8462, -77.3064, radius_miles=1.0)
for park in nearby[:3]:
    print(f"  {park['park_name']}: {park['distance_miles']} mi")

# Get trail access
trails = analyzer.get_trail_access(38.8462, -77.3064, radius_miles=1.0)
print(f"Trail segments: {trails['trails_within_radius']}")
print(f"Total miles: {trails['total_trail_miles']}")

# Find playgrounds
playgrounds = analyzer.get_recreational_amenities(
    38.8462, -77.3064,
    radius_miles=0.5,
    amenity_types=['PLAYGROUND']
)
print(f"Playgrounds nearby: {len(playgrounds)}")
```

### Transit Analysis
```python
from core.fairfax_transit_analysis import FairfaxTransitAnalysis

analyzer = FairfaxTransitAnalysis()

# Calculate transit score
score = analyzer.calculate_transit_score(38.8777, -77.2714)
print(f"Transit Score: {score['score']}/100 ({score['rating']})")
print(f"Metro distance: {score['nearest_metro_distance']} mi")
print(f"Walk time: {score['metro_walk_time']} min")
print(f"Bus routes: {score['bus_routes_within_quarter_mi']}")

# Get nearest Metro station
metro = analyzer.get_nearest_metro_station(38.8777, -77.2714)
print(f"Station: {metro['station_name']}")
print(f"Distance: {metro['distance_miles']} mi")
print(f"Walk time: {metro['walk_time_minutes']} min")
print(f"Bike time: {metro['bike_time_minutes']} min")

# Get nearby bus routes
routes = analyzer.get_nearby_bus_routes(38.8777, -77.2714, radius_miles=0.5)
for route in routes[:3]:
    print(f"  Route {route['route_number']}: {route['route_name']}")

# Get commute options summary
commute = analyzer.get_commute_options(38.8777, -77.2714)
print(f"Metro accessible: {commute['metro']['accessible']}")
print(f"Bus routes: {commute['bus']['routes_count']}")
print(f"Overall: {commute['overall_accessibility']}")
```

## Feature Examples

### Property Detail Page
```python
from core.fairfax_crime_analysis import FairfaxCrimeAnalysis
from core.fairfax_permits_analysis import FairfaxPermitsAnalysis
from core.fairfax_healthcare_analysis import FairfaxHealthcareAnalysis
from core.fairfax_subdivisions_analysis import FairfaxSubdivisionsAnalysis
from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
from core.fairfax_flood_analysis import FairfaxFloodAnalysis
from core.fairfax_utilities_analysis import FairfaxUtilitiesAnalysis
from core.fairfax_parks_analysis import FairfaxParksAnalysis
from core.fairfax_transit_analysis import FairfaxTransitAnalysis

def get_property_intelligence(lat, lon):
    """Get complete property intelligence."""

    crime_analyzer = FairfaxCrimeAnalysis()
    permits_analyzer = FairfaxPermitsAnalysis()
    healthcare_analyzer = FairfaxHealthcareAnalysis()
    subdivisions_analyzer = FairfaxSubdivisionsAnalysis()
    schools_analyzer = FairfaxSchoolsAnalysis()
    zoning_analyzer = FairfaxZoningAnalysis()
    flood_analyzer = FairfaxFloodAnalysis()

    # Crime analysis
    safety = crime_analyzer.calculate_safety_score(lat, lon, 0.5, 6)
    crime_trends = crime_analyzer.get_crime_trends(lat, lon, 0.5, 12)

    # Permits analysis
    development = permits_analyzer.calculate_development_pressure(lat, lon, 1.0, 24)

    # Healthcare analysis
    healthcare = healthcare_analyzer.calculate_healthcare_access_score(lat, lon)

    # Subdivision lookup
    subdivision = subdivisions_analyzer.get_subdivision(lat, lon)

    # School assignments
    schools = schools_analyzer.get_assigned_schools(lat, lon)

    # Zoning
    zoning = zoning_analyzer.get_zoning(lat, lon)

    # Flood risk
    flood = flood_analyzer.get_flood_risk(lat, lon)

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
        },
        'schools': {
            'elementary': schools['elementary']['school_name'] if schools['elementary'] else None,
            'middle': schools['middle']['school_name'] if schools['middle'] else None,
            'high': schools['high']['school_name'] if schools['high'] else None,
            'all_assigned': schools['all_assigned']
        },
        'zoning': {
            'zone_code': zoning['zone_code'],
            'zone_type': zoning['zone_type'],
            'overlays': [o['overlay_type'] for o in zoning['overlays']]
        },
        'flood': {
            'risk_level': flood['overall_risk'],
            'insurance_required': flood['insurance_required'],
            'fema_zone': flood['fema_zone']['zone_code'] if flood['fema_zone'] else None
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

### FairfaxSchoolsAnalysis

#### `get_assigned_schools(lat, lon)`

Get school assignments for elementary, middle, and high schools.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'elementary': {
        'school_name': 'Lees Corner',
        'grades': 'K-6',
        'address': '13001 RIDGEFAIR DR',
        'city': 'FAIRFAX',
        'distance_miles': 1.25,
        'region': 5
    },
    'middle': {
        'school_name': 'Franklin',
        'grades': '7-8',
        'distance_miles': 0.97
    },
    'high': {
        'school_name': 'Chantilly',
        'grades': '9-12',
        'distance_miles': 1.82
    },
    'all_assigned': True,
    'message': None
}
```

#### `get_school_facilities(lat, lon, radius_miles=5.0, school_types=None, limit=10)`

Find nearby school facilities.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 5.0 miles)
- `school_types`: Optional list of type codes (ES, MS, HS, etc.)
- `limit`: Maximum results (default: 10)

**Returns:**
```python
[
    {
        'school_name': 'Brookfield',
        'school_type': 'ES',
        'type_description': 'Elementary',
        'grades': 'K-6',
        'address': '4200 LEES CORNER RD',
        'city': 'CHANTILLY',
        'distance_miles': 1.24
    },
    ...
]
```

#### `search_schools(query, limit=10)`

Search schools by name.

**Parameters:**
- `query`: Search string (case-insensitive partial match)
- `limit`: Maximum results (default: 10)

**Returns:** List of matching schools with details.

#### `get_statistics()`

Get summary statistics about the school dataset.

**Returns:**
```python
{
    'attendance_zones': {
        'elementary': 142,
        'middle': 26,
        'high': 24,
        'total': 192
    },
    'facilities': {
        'total': 269,
        'by_type': {'ES': 142, 'MS': 26, 'HS': 27, ...}
    },
    'geographic_bounds': {...}
}
```

### FairfaxZoningAnalysis

#### `get_zoning(lat, lon)`

Get zoning district and overlays for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'zone_code': 'I-3',
    'zone_type': 'industrial',
    'zone_type_description': 'Industrial - Manufacturing and warehousing',
    'zone_description': 'Industrial, Light-general',
    'has_proffer': False,
    'public_land': False,
    'cluster': None,
    'overlays': [
        {'overlay_type': 'water_supply_protection'},
        {'overlay_type': 'highway_corridor'},
        {'overlay_type': 'airport_noise_impact', 'decibel_level': 60.0}
    ],
    'message': None
}
```

#### `get_overlays(lat, lon)`

Get all overlay districts for a location.

**Returns:**
```python
[
    {'overlay_type': 'highway_corridor'},
    {
        'overlay_type': 'airport_noise_impact',
        'decibel_level': 60.0,
        'noise_description': 'Low-moderate aircraft noise - Background noise level'
    }
]
```

#### `check_airport_noise(lat, lon)`

Check if location is in an airport noise impact zone.

**Returns:**
```python
{
    'in_noise_zone': True,
    'decibel_level': 60.0,
    'description': 'Low-moderate aircraft noise - Background noise level'
}
```
Returns `None` if not in a noise zone.

#### `search_zones(zone_code_pattern, limit=20)`

Search for zoning districts by code pattern.

**Returns:**
```python
[
    {'zone_code': 'R-1', 'zone_type': 'residential', 'description': '...', 'district_count': 1163},
    {'zone_code': 'R-12', 'zone_type': 'residential', 'description': '...', 'district_count': 90},
    ...
]
```

#### `get_statistics()`

Get summary statistics about the zoning dataset.

**Returns:**
```python
{
    'districts': {
        'total': 6431,
        'unique_zone_codes': 74,
        'by_type': {'residential': 3962, 'commercial': 910, ...}
    },
    'overlays': {
        'total': 73,
        'by_type': {'commercial_development': 16, 'historic': 15, ...}
    }
}
```

### FairfaxUtilitiesAnalysis

#### `check_proximity(lat, lon, distance_threshold_miles=0.1)`

Check if property is within threshold of any utility line.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `distance_threshold_miles`: Distance threshold (default: 0.1 miles / 528 ft)

**Returns:**
```python
{
    'within_threshold': True,
    'threshold_miles': 0.1,
    'closest_utility': {
        'utility_type': 'electric',
        'operator': 'DOMINION ENERGY',
        'distance_miles': 0.05
    },
    'utilities_within_threshold': [
        {'utility_type': 'electric', 'operator': 'DOMINION ENERGY', 'distance_miles': 0.05},
        {'utility_type': 'gas', 'operator': 'WASHINGTON GAS', 'distance_miles': 0.08}
    ],
    'message': None
}
```

#### `get_nearby_utilities(lat, lon, radius_miles=0.5, utility_types=None, limit=20)`

Find utility lines within radius of a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 0.5 miles)
- `utility_types`: Optional filter by type (electric, gas, telephone)
- `limit`: Maximum number of results (default: 20)

**Returns:**
```python
[
    {
        'utility_type': 'electric',
        'operator': 'DOMINION ENERGY',
        'length_miles': 1.25,
        'distance_miles': 0.12,
        'object_id': 12345
    },
    ...
]
```

#### `get_utility_types_nearby(lat, lon, radius_miles=0.5)`

Get summary of utility types within radius.

**Returns:**
```python
{
    'electric': {'count': 3, 'operators': ['DOMINION ENERGY'], 'total_miles': 2.5, 'closest_distance': 0.12},
    'gas': {'count': 2, 'operators': ['WASHINGTON GAS'], 'total_miles': 1.8, 'closest_distance': 0.15},
    'telephone': {'count': 0, 'operators': [], 'total_miles': 0, 'closest_distance': None}
}
```

#### `get_statistics()`

Get summary statistics about the utility dataset.

**Returns:**
```python
{
    'total_lines': 125,
    'by_type': {'electric': 56, 'gas': 65, 'telephone': 4},
    'miles_by_type': {'electric': 45.2, 'gas': 38.7, 'telephone': 3.1},
    'operators_by_type': {'electric': ['DOMINION ENERGY'], 'gas': ['WASHINGTON GAS'], ...},
    'total_miles': 87.0,
    'geographic_bounds': {...}
}
```

### FairfaxParksAnalysis

#### `calculate_park_access_score(lat, lon)`

Calculate a park access score (0-100) for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'score': 85,                      # 0-100 (higher = better access)
    'rating': 'Excellent',            # Rating string
    'breakdown': {
        'park_proximity': 28,         # Max 30 pts - parks within 0.5mi
        'trail_access': 22,           # Max 25 pts - trails within 0.5mi
        'amenities': 18,              # Max 20 pts - playgrounds, courts within 0.5mi
        'variety': 17                 # Max 25 pts - different park types
    },
    'parks_within_1mi': 5,
    'trail_miles_within_1mi': 2.3,
    'playgrounds_within_half_mi': 2
}
```

#### `get_nearby_parks(lat, lon, radius_miles=1.0, park_types=None, limit=10)`

Find parks within radius of a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 1.0 miles)
- `park_types`: Optional filter by jurisdiction (county, non-county)
- `limit`: Maximum number of results (default: 10)

**Returns:**
```python
[
    {
        'park_name': 'Burke Lake Park',
        'jurisdiction': 'county',
        'acres': 888.0,
        'distance_miles': 0.45
    },
    ...
]
```

#### `get_trail_access(lat, lon, radius_miles=1.0)`

Get trail access information for a location.

**Returns:**
```python
{
    'trails_within_radius': 12,
    'total_trail_miles': 5.7,
    'closest_trail_distance': 0.15,
    'trail_types': ['paved', 'natural']
}
```

#### `get_recreational_amenities(lat, lon, radius_miles=0.5, amenity_types=None, limit=20)`

Find recreational amenities near a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 0.5 miles)
- `amenity_types`: Optional filter (PLAYGROUND, TENNIS, BASKETBALL, etc.)
- `limit`: Maximum results (default: 20)

**Returns:**
```python
[
    {
        'amenity_type': 'PLAYGROUND',
        'park_name': 'Wakefield Park',
        'distance_miles': 0.25
    },
    ...
]
```

#### `get_statistics()`

Get summary statistics about the parks dataset.

**Returns:**
```python
{
    'parks': {'total': 585, 'county': 421, 'non_county': 164, 'total_acres': 23456.7},
    'trails': {'total_segments': 5818, 'total_miles': 347.2},
    'recreation': {'total_features': 14459, 'by_type': {'PLAYGROUND': 234, 'TENNIS': 189, ...}},
    'geographic_bounds': {...}
}
```

### FairfaxTransitAnalysis

#### `calculate_transit_score(lat, lon)`

Calculate a transit access score (0-100) for a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'score': 92,                          # 0-100 (higher = better access)
    'rating': 'Excellent',                # Rating string
    'breakdown': {
        'metro_access': 48,               # Max 50 pts - Metro station proximity
        'bus_coverage': 28,               # Max 30 pts - Bus route coverage
        'service_variety': 16             # Max 20 pts - Multiple transit options
    },
    'nearest_metro_distance': 0.3,
    'metro_walk_time': 6,
    'bus_routes_within_quarter_mi': 4
}
```

#### `get_nearest_metro_station(lat, lon)`

Get the nearest Metro station.

**Returns:**
```python
{
    'station_name': 'Vienna',
    'line': 'Orange',
    'distance_miles': 0.35,
    'walk_time_minutes': 7,
    'bike_time_minutes': 2,
    'accessible': True
}
```
Returns `None` if no Metro station within 5 miles.

#### `get_nearby_bus_routes(lat, lon, radius_miles=0.5, limit=10)`

Find bus routes near a location.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude
- `radius_miles`: Search radius (default: 0.5 miles)
- `limit`: Maximum results (default: 10)

**Returns:**
```python
[
    {
        'route_number': '401',
        'route_name': 'FAIRFAX - PENTAGON',
        'operator': 'Fairfax Connector',
        'distance_miles': 0.15
    },
    ...
]
```

#### `get_commute_options(lat, lon)`

Get summary of commute options for a location.

**Returns:**
```python
{
    'metro': {
        'accessible': True,
        'station_name': 'Vienna',
        'distance_miles': 0.35,
        'walk_time': 7
    },
    'bus': {
        'routes_count': 4,
        'operators': ['Fairfax Connector', 'Metrobus']
    },
    'overall_accessibility': 'Excellent'
}
```

#### `get_statistics()`

Get summary statistics about the transit dataset.

**Returns:**
```python
{
    'bus_routes': {'total': 89, 'operators': ['Fairfax Connector']},
    'metro': {
        'lines': 44,
        'stations': 32,
        'station_names': ['Vienna', 'Dunn Loring', 'West Falls Church', ...]
    },
    'geographic_bounds': {...}
}
```

### FairfaxFloodAnalysis

#### `get_flood_risk(lat, lon)`

Get comprehensive flood risk assessment.

**Parameters:**
- `lat`: Latitude
- `lon`: Longitude

**Returns:**
```python
{
    'fema_zone': {
        'zone_code': 'AE',
        'zone_subtype': None,
        'risk_level': 'high',
        'risk_description': 'High flood risk - Properties require flood insurance...',
        'zone_description': '1% annual chance flood zone with Base Flood Elevation',
        'insurance_required': True
    },
    'dam_inundation_risks': [
        {'dam_name': 'Lake Accotink Dam', 'dam_owner': '...', 'break_type': 'PMF Overtopping'}
    ],
    'floodplain_easement': {
        'in_easement': False,
        'easement_count': 0
    },
    'overall_risk': 'high',
    'overall_risk_description': 'High flood risk - Properties require flood insurance...',
    'insurance_required': True,
    'message': None
}
```

#### `get_fema_zone(lat, lon)`

Get FEMA flood zone for a location.

**Returns:**
```python
{
    'zone_code': 'AE',
    'risk_level': 'high',
    'zone_description': '1% annual chance flood zone with Base Flood Elevation',
    'insurance_required': True
}
```

#### `get_dam_inundation_risk(lat, lon)`

Check if location is in any dam break inundation zones.

**Returns:**
```python
[
    {'dam_name': 'Burke Lake Dam', 'dam_owner': 'Fairfax County', 'break_type': 'PMF Overtopping'}
]
```

#### `check_floodplain_easement(lat, lon)`

Check if location is within a recorded floodplain easement.

**Returns:**
```python
{
    'in_easement': True,
    'easement_count': 1,
    'easements': [{'easement_id': 12345, 'easement_type': 'floodplain'}]
}
```

#### `get_dams()`

Get list of all dams with inundation data.

**Returns:** Sorted list of dam names.

#### `get_statistics()`

Get summary statistics about the flood dataset.

**Returns:**
```python
{
    'fema_zones': {
        'total': 3313,
        'by_risk_level': {'high': 1196, 'moderate': 7, 'minimal': 2110},
        'by_zone_code': {'X': 2110, 'AE': 677, 'A': 515, ...}
    },
    'dam_inundation': {
        'total_zones': 17,
        'unique_dams': 16,
        'dam_names': ['Burke Lake Dam', 'Fox Lake Dam', ...]
    },
    'easements': {'total': 897}
}
```

## Data Refresh

All modules automatically use the latest data:
- **Crime**: Updated daily via GitHub Actions
- **Permits**: Updated weekly via GitHub Actions
- **Healthcare**: Base data annual, CMS quarterly, Leapfrog bi-annual
- **Subdivisions**: Static (boundaries rarely change)
- **Schools**: Updated annually (school year boundaries)
- **Zoning**: Updated as zoning changes occur
- **Flood**: FEMA data updated periodically
- **Utilities**: Static (major infrastructure rarely changes)
- **Parks**: Updated annually (park boundaries and amenities)
- **Transit**: Updated quarterly (route changes and schedules)

No manual refresh needed - just reload the module.

## Performance Notes

- Crime module: ~1,000 incidents (fast queries)
- Permits module: ~41,000 permits (slightly slower, still <1 sec)
- Healthcare module: ~77 facilities (fast queries)
- Subdivisions module: ~11,430 polygons with spatial indexing (fast point-in-polygon)
- Schools module: 192 attendance zones + 269 facilities with spatial indexing
- Zoning module: 6,431 districts + 73 overlays with spatial indexing
- Flood module: 3,313 FEMA zones + 17 dam zones + 897 easements with spatial indexing
- Utilities module: 125 utility lines with spatial indexing (fast line-to-point distance)
- Parks module: 585 parks + 5,818 trail segments + 14,459 recreation features with spatial indexing
- Transit module: 89 bus routes + 44 Metro lines + 32 Metro stations with spatial indexing
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

### Park Access Score
| Score | Rating | Description |
|-------|--------|-------------|
| 85-100 | Excellent | Multiple parks and trails within walking distance |
| 70-84 | Very Good | Good park access with recreational amenities |
| 55-69 | Good | Reasonable park access |
| 40-54 | Fair | Limited park options nearby |
| 0-39 | Poor | Few parks or recreational facilities |

### Transit Score
| Score | Rating | Description |
|-------|--------|-------------|
| 85-100 | Excellent | Metro station within walking distance, multiple bus routes |
| 70-84 | Very Good | Metro accessible, good bus coverage |
| 55-69 | Good | Reasonable transit options available |
| 40-54 | Fair | Limited transit, may require driving |
| 0-39 | Poor | Minimal public transit access |

## Testing

Run the test suite to verify modules:
```bash
cd multi-county-real-estate-research
python tests/test_fairfax_analysis.py
```

Expected output:
```
Crime Analysis Module:        PASS
Permits Analysis Module:      PASS
Healthcare Analysis Module:   PASS
Subdivisions Analysis Module: PASS
Schools Analysis Module:      PASS
Zoning Analysis Module:       PASS
Flood Analysis Module:        PASS
Utilities Analysis Module:    PASS
Parks Analysis Module:        PASS
Transit Analysis Module:      PASS
ALL 10 MODULES PASSED - Ready for integration!
```
