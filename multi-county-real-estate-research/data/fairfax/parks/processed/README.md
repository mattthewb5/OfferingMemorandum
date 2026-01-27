# Fairfax County Parks & Recreation - Processed Data

## Data Source
- **Provider:** Fairfax County Park Authority / GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** 2026-01-27

## Files

### parks.parquet
County and non-county park boundaries.

- **Records:** 585
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 2.32 MB

| Field | Type | Description |
|-------|------|-------------|
| park_name | string | Park name |
| park_class | string | Park classification (Local, District, etc.) |
| jurisdiction | string | Managing entity (county, nova_parks, etc.) |
| supervisor_district | string | Fairfax supervisor district |
| planning_district | string | Planning district |
| maintenance_area | string | Maintenance area (county parks only) |
| area_acres | float | Park area in acres |
| geometry | geometry | Park boundary |

**Jurisdictions:**
- county: 424 parks
- reston: 65 parks
- city of fairfax: 33 parks
- golf_club: 15 parks
- nova parks: 13 parks
- town of vienna: 11 parks
- Other: 24 parks

---

### trails.parquet
Park trails and multi-use paths.

- **Records:** 5,818
- **Geometry:** LineString/MultiLineString
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 1.84 MB
- **Total Length:** 347.4 miles

| Field | Type | Description |
|-------|------|-------------|
| trail_name | string | Trail name (if named) |
| park_name | string | Associated park |
| surface_material | string | Surface type (Asphalt, Natural, etc.) |
| width_ft | float | Trail width in feet |
| length_ft | float | Segment length in feet |
| length_miles | float | Segment length in miles |
| difficulty | string | Difficulty rating (if available) |
| ada_accessible | string | ADA accessibility status |
| supervisor_district | string | Supervisor district |
| geometry | geometry | Trail path |

**Surface Types:**
- Asphalt: 2,438 segments
- Natural: 1,287 segments
- Concrete: 743 segments
- Gravel: 487 segments
- Bridge: 430 segments

---

### recreation.parquet
Recreational features and amenities (courts, fields, playgrounds).

- **Records:** 14,459
- **Geometry:** Polygon
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 25.37 MB

| Field | Type | Description |
|-------|------|-------------|
| feature_type | string | Type of recreational feature |
| data_source | string | Data source/capture method |
| centroid_lat | float | Feature centroid latitude |
| centroid_lon | float | Feature centroid longitude |
| area_sqft | float | Feature area in square feet |
| geometry | geometry | Feature boundary |

**Top Feature Types:**
| Type | Count |
|------|-------|
| PATHWAY | 5,215 |
| PLAYGROUND | 2,578 |
| BASKETBALL COURT | 1,629 |
| TENNIS COURT | 1,225 |
| BLEACHER | 1,178 |
| OTHER | 1,104 |
| GRASS RECTANGLE FIELD | 418 |
| 60 FOOT DIAMOND FIELD | 384 |

## Usage Example

```python
import geopandas as gpd
from shapely.geometry import Point

# Load parks data
parks = gpd.read_parquet('data/fairfax/parks/processed/parks.parquet')
trails = gpd.read_parquet('data/fairfax/parks/processed/trails.parquet')
recreation = gpd.read_parquet('data/fairfax/parks/processed/recreation.parquet')

# Find parks within 1 mile of a property
property_point = Point(-77.3064, 38.8462)
buffer_1mi = gpd.GeoSeries([property_point], crs='EPSG:4326').to_crs('EPSG:32618').buffer(1609.34)
buffer_wgs84 = buffer_1mi.to_crs('EPSG:4326')

nearby_parks = parks[parks.intersects(buffer_wgs84.iloc[0])]
print(f"Parks within 1 mile: {len(nearby_parks)}")
for _, park in nearby_parks.iterrows():
    print(f"  {park['park_name']} ({park['area_acres']:.1f} acres)")

# Find playgrounds nearby
playgrounds = recreation[recreation['feature_type'] == 'PLAYGROUND']
nearby_playgrounds = playgrounds[playgrounds.intersects(buffer_wgs84.iloc[0])]
print(f"Playgrounds within 1 mile: {len(nearby_playgrounds)}")
```
