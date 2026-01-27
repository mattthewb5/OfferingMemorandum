# Fairfax County Roads Infrastructure - Processed Data

## Data Source
- **Provider:** Fairfax County GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** 2026-01-27

## Files

### road_centerlines.parquet
Complete road centerline network for Fairfax County and surrounding areas.
- **Records:** 148,594
- **Geometry:** LineString
- **CRS:** EPSG:4326 (WGS84)
- **Total Miles:** 13,937.1

| Field | Type | Description |
|-------|------|-------------|
| object_id | int | Object identifier |
| trans_id | int | Transportation ID |
| road_name | string | Full road name (e.g., "TELEGRAPH RD") |
| road_base_name | string | Base road name without suffix |
| road_type_suffix | string | Road type suffix (RD, ST, AVE, etc.) |
| road_class | string | Original road classification code |
| road_type | string | Standardized road type |
| ffx_class | string | Fairfax classification |
| is_bridge | string | Y/N - segment is a bridge |
| low_water_crossing | string | Y/N - low water crossing |
| status | string | Road status |
| speed_limit | int | Posted speed limit (mph) |
| one_way | string | Y/N - one-way road |
| divided | string | Y/N - divided road |
| length_miles | float | Segment length in miles |
| left_jurisdiction | int | Left side jurisdiction code |
| right_jurisdiction | int | Right side jurisdiction code |
| left_zip | int | Left side ZIP code |
| right_zip | int | Right side ZIP code |
| global_id | string | Unique identifier |
| geometry | geometry | Road centerline path |

**Road Types:**
| Code | Type | Count | Miles |
|------|------|-------|-------|
| LOC | local | 108,803 | 7,847 |
| PRI | primary | 10,213 | 1,821 |
| SEC | secondary | 10,166 | 1,598 |
| TER | tertiary | 8,572 | 1,387 |
| RMP | ramp | 4,058 | 395 |
| INT | interstate | 3,379 | 584 |
| other | other | 3,403 | 305 |

### bridges.parquet
Road segments that cross over waterways, railways, or other roads.
- **Records:** 1,659
- **Geometry:** LineString
- **CRS:** EPSG:4326 (WGS84)
- **Total Bridge Miles:** 108.4

Includes same fields as road_centerlines plus:
| Field | Type | Description |
|-------|------|-------------|
| latitude | float | Bridge centroid latitude |
| longitude | float | Bridge centroid longitude |

**Bridge Distribution by Road Type:**
- Ramp: 393 (24%)
- Local: 393 (24%)
- Primary: 340 (20%)
- Interstate: 300 (18%)
- Tertiary: 124 (7%)
- Secondary: 107 (6%)

## Usage Example
```python
import geopandas as gpd
from shapely.geometry import Point

# Load roads data
roads = gpd.read_parquet('data/fairfax/roads/processed/road_centerlines.parquet')
bridges = gpd.read_parquet('data/fairfax/roads/processed/bridges.parquet')

print(f"Total road segments: {len(roads):,}")
print(f"Total road miles: {roads['length_miles'].sum():,.1f}")

# Find roads within 0.25 miles of a property
property_point = Point(-77.3064, 38.8462)
buffer_meters = 0.25 * 1609.344  # Convert miles to meters

# Create buffer in projected CRS
property_gdf = gpd.GeoDataFrame({'geometry': [property_point]}, crs='EPSG:4326')
property_gdf = property_gdf.to_crs('EPSG:32618')
buffer = property_gdf.buffer(buffer_meters)
buffer_wgs84 = buffer.to_crs('EPSG:4326')

nearby_roads = roads[roads.intersects(buffer_wgs84.iloc[0])]
print(f"\nRoads within 0.25 mi: {len(nearby_roads)}")
print(f"Road types: {nearby_roads['road_type'].value_counts().to_dict()}")

# Calculate road density (miles per square mile)
area_sqmi = 3.14159 * 0.25 * 0.25  # Circle area
road_density = nearby_roads['length_miles'].sum() / area_sqmi
print(f"Road density: {road_density:.1f} mi/sq mi")

# Find nearby bridges
nearby_bridges = bridges[bridges.intersects(buffer_wgs84.iloc[0])]
print(f"\nBridges within 0.25 mi: {len(nearby_bridges)}")

# Find major roads (interstate, primary, secondary)
major_roads = nearby_roads[nearby_roads['road_type'].isin(['interstate', 'primary', 'secondary'])]
if len(major_roads) > 0:
    print(f"\nMajor roads nearby:")
    for _, road in major_roads.head(5).iterrows():
        print(f"  {road['road_name']} ({road['road_type']})")
```

## Processing Notes
- Original CRS (EPSG:2283 Virginia State Plane North) converted to WGS84
- Road lengths calculated in miles using UTM projection for accuracy
- Bridges extracted from road centerlines where BRIDGE='Y'
- Bridge centroids calculated for point-based distance queries
- All geometries validated (100% valid)
- Dataset extends beyond Fairfax County boundaries to include connecting roads

## Performance Considerations
- Large dataset (41.2 MB) - consider filtering by road_type for analysis
- Use spatial indexing (built into GeoParquet) for efficient spatial queries
- For area-based analysis, filter to relevant road types first
