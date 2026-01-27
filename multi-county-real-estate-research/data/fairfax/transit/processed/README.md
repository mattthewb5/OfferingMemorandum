# Fairfax County Transit - Processed Data

## Data Source
- **Provider:** Fairfax County Department of Transportation
- **Metro Data:** Washington Metropolitan Area Transit Authority (WMATA)
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** 2026-01-27

## Files

### bus_routes.parquet
Fairfax Connector bus routes.

- **Records:** 89 routes
- **Geometry:** LineString/MultiLineString
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 1.39 MB

| Field | Type | Description |
|-------|------|-------------|
| route_number | int | Route number (e.g., 101, 305) |
| route_name | string | Route name (e.g., Fort Hunt, Tysons Express) |
| division | string | Operating division |
| service_type | string | Local, Express, Circulator, Feeder |
| length_miles | float | Route length in miles |
| schedule_url | string | URL to route schedule PDF |
| geometry | geometry | Route path |

**Service Types:**
- Local: 50 routes
- Express: 17 routes
- Circulator: 12 routes
- Feeder: 10 routes

**Divisions:**
- West Ox: 39 routes
- Huntington: 28 routes
- Reston Herndon: 22 routes

---

### metro_lines.parquet
Metro rail line segments serving Fairfax County.

- **Records:** 44 segments
- **Geometry:** LineString/MultiLineString
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 35 KB
- **Total Track:** 67.1 miles

| Field | Type | Description |
|-------|------|-------------|
| line_name | string | Metro line (Orange, Silver, Blue, Yellow) |
| line_color | string | Hex color code for the line |
| from_station | string | Origin station name |
| to_station | string | Destination station name |
| year_opened | int | Year segment opened |
| length_miles | float | Segment length in miles |
| geometry | geometry | Track path |

**Metro Lines in Fairfax:**
| Line | Segments | Color |
|------|----------|-------|
| Silver | 17 | #a1a1a1 |
| Blue | 10 | #0076c0 |
| Orange | 9 | #f7941d |
| Yellow | 8 | #ffd200 |

---

### metro_stations.parquet
Metro station locations in Fairfax County area.

- **Records:** 32 stations
- **Geometry:** Point
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 11 KB

| Field | Type | Description |
|-------|------|-------------|
| station_name | string | Station name |
| year_opened | int | Year station opened |
| latitude | float | Station latitude |
| longitude | float | Station longitude |
| geometry | geometry | Station point location |

**Station Timeline:**
- Oldest: 1977 (original Blue/Orange line stations)
- Newest: 2023 (Silver Line Phase 2 extension)

**Sample Stations:**
- VIENNA/ FAIRFAX - GMU
- DUNN LORING - MERRIFIELD
- WEST FALLS CHURCH
- TYSONS (multiple stations)
- RESTON TOWN CENTER
- DULLES AIRPORT

## Usage Example

```python
import geopandas as gpd
from shapely.geometry import Point
import math

# Load transit data
bus_routes = gpd.read_parquet('data/fairfax/transit/processed/bus_routes.parquet')
metro_stations = gpd.read_parquet('data/fairfax/transit/processed/metro_stations.parquet')

# Find transit options near a property
property_lat, property_lon = 38.8462, -77.3064

# Find nearest metro station
def haversine(lat1, lon1, lat2, lon2):
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

metro_stations['distance_mi'] = metro_stations.apply(
    lambda x: haversine(property_lat, property_lon, x['latitude'], x['longitude']), axis=1
)
nearest_metro = metro_stations.nsmallest(1, 'distance_mi').iloc[0]
print(f"Nearest Metro: {nearest_metro['station_name']} ({nearest_metro['distance_mi']:.1f} mi)")

# Find bus routes within 0.25 miles
property_point = Point(property_lon, property_lat)
buffer = gpd.GeoSeries([property_point], crs='EPSG:4326').to_crs('EPSG:32618').buffer(402)  # 0.25 mi
buffer_wgs84 = buffer.to_crs('EPSG:4326')

nearby_buses = bus_routes[bus_routes.intersects(buffer_wgs84.iloc[0])]
print(f"Bus routes within 0.25 mi: {len(nearby_buses)}")
for _, route in nearby_buses.iterrows():
    print(f"  Route {route['route_number']}: {route['route_name']} ({route['service_type']})")
```
