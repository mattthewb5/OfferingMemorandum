# Fairfax County Emergency Services - Processed Data

## Data Source
- **Provider:** Fairfax County GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** 2026-01-27

## Files

### fire_stations.parquet
Fire station locations throughout Fairfax County.
- **Records:** 47
- **Geometry:** Point
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| station_name | string | Short station name (e.g., "MCLEAN") |
| station_full_name | string | Full station name (e.g., "Fire Station 1 - McLean") |
| station_code | string | Station code/label (e.g., "401") |
| company_number | int | Company number |
| station_type | string | Type of facility (all are "Station") |
| address | string | Full street address |
| jurisdiction | string | Operating jurisdiction |
| latitude | float | Station latitude |
| longitude | float | Station longitude |
| created_date | date | Record creation date |
| last_edited | date | Last edit date |
| global_id | string | Unique identifier |
| geometry | geometry | Station location point |

**Jurisdictions:**
- Fairfax County: 41 stations
- Fort Belvoir: 4 stations
- City of Fairfax: 2 stations

### police_stations.parquet
Police stations and facilities throughout Fairfax County.
- **Records:** 23
- **Geometry:** Point
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| station_name | string | Station/facility name |
| address | string | Street address |
| phone | string | Phone number |
| station_type | string | Facility type |
| latitude | float | Station latitude |
| longitude | float | Station longitude |
| created_date | date | Record creation date |
| last_edited | date | Last edit date |
| global_id | string | Unique identifier |
| geometry | geometry | Station location point |

**Station Types:**
- STATION: 14 (District stations)
- HQ: 3 (Headquarters facilities)
- COMM: 2 (Communications centers)
- HELO: 1 (Helicopter unit)
- ANML/ANIML: 2 (Animal services)
- ACADEMY: 1 (Police academy)

## Usage Example
```python
import geopandas as gpd
import math

# Load emergency services data
fire_stations = gpd.read_parquet('data/fairfax/emergency_services/processed/fire_stations.parquet')
police_stations = gpd.read_parquet('data/fairfax/emergency_services/processed/police_stations.parquet')

# Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# Find nearest fire station to a property
property_lat, property_lon = 38.8462, -77.3064

fire_stations['distance'] = fire_stations.apply(
    lambda x: haversine(property_lat, property_lon, x['latitude'], x['longitude']), axis=1
)
nearest_fire = fire_stations.nsmallest(1, 'distance').iloc[0]
print(f"Nearest fire station: {nearest_fire['station_full_name']}")
print(f"Distance: {nearest_fire['distance']:.2f} miles")
print(f"Address: {nearest_fire['address']}")

# Find nearest police station
police_stations['distance'] = police_stations.apply(
    lambda x: haversine(property_lat, property_lon, x['latitude'], x['longitude']), axis=1
)
nearest_police = police_stations.nsmallest(1, 'distance').iloc[0]
print(f"\nNearest police station: {nearest_police['station_name']}")
print(f"Distance: {nearest_police['distance']:.2f} miles")
print(f"Phone: {nearest_police['phone']}")
```

## Processing Notes
- Original CRS (EPSG:2283 Virginia State Plane North) converted to WGS84
- Latitude/longitude extracted for efficient distance calculations
- All geometries validated (100% valid)
