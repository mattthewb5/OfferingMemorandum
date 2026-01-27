# Fairfax County Schools - Processed Data

## Data Source
- **Provider:** Fairfax County GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** January 27, 2026

## Files

### elementary_zones.parquet
School attendance boundaries for elementary schools (grades K-5/K-6).
- **Records:** 142
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| school_name | string | Elementary school name |
| school_type | string | "ES" |
| type_description | string | "Elementary" |
| grades | string | Grade levels (e.g., "K-5", "K-6") |
| street_number | string | School address number |
| street_name | string | School street name |
| city | string | City |
| zip_code | int | ZIP code |
| phone | int | Phone number |
| website | string | School website URL |
| school_year | string | School year (e.g., "2025_26") |
| region | int | FCPS region number |
| level | string | "elementary" |
| geometry | geometry | Attendance zone boundary |

### middle_zones.parquet
School attendance boundaries for middle schools (grades 7-8).
- **Records:** 26
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)

Same fields as elementary_zones with `school_type="MS"` and `level="middle"`.

### high_zones.parquet
School attendance boundaries for high schools (grades 9-12).
- **Records:** 24
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)

Same fields as elementary_zones with `school_type="HS"` and `level="high"`.

### facilities.parquet
School facility point locations for all FCPS schools.
- **Records:** 269
- **Geometry:** Point
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| school_name | string | School name |
| school_type | string | Type code (ES, MS, HS, ALTCT, AC, etc.) |
| type_description | string | Full type name |
| grades | string | Grade levels |
| address | string | Full street address |
| city | string | City |
| zip_code | int | ZIP code |
| website | string | School website URL |
| phone | float | Phone number |
| region | int | FCPS region number |
| school_year | string | School year |
| latitude | float | Latitude (WGS84) |
| longitude | float | Longitude (WGS84) |
| geometry | geometry | Point location |

### School Type Codes
- ES: Elementary School (142)
- MS: Middle School (26)
- HS: High School (27)
- ALTCT: Alternative Center (20)
- AC: Administrative Center (18)
- OTH: Other (11)
- SC: Special Center (8)
- SPED: Special Education (7)
- ALTSC: Alternative School (4)
- SOP: School of Practical Nursing (4)
- PSRES: Preschool Residential (1)
- IAS: Interagency Alternative School (1)

## Usage Example
```python
import geopandas as gpd
from shapely.geometry import Point

# Load school zones
elem = gpd.read_parquet('elementary_zones.parquet')
middle = gpd.read_parquet('middle_zones.parquet')
high = gpd.read_parquet('high_zones.parquet')

# Find assigned schools for a location
lat, lon = 38.8969, -77.4327
point = Point(lon, lat)

for level, zones in [('Elementary', elem), ('Middle', middle), ('High', high)]:
    match = zones[zones.geometry.contains(point)]
    if len(match) > 0:
        print(f"{level}: {match.iloc[0]['school_name']}")
```
