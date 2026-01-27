# Fairfax County Utilities - Processed Data

## Data Source
- **Provider:** Fairfax County GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** 2026-01-27

## Files

### utility_lines.parquet
Major utility transmission lines including electric, gas, and telephone infrastructure.

- **Records:** 125
- **Geometry:** LineString
- **CRS:** EPSG:4326 (WGS84)
- **File Size:** 60 KB

| Field | Type | Description |
|-------|------|-------------|
| object_id | int | Unique identifier |
| operator | string | Utility operator (Virginia Power, Colonial Gas, etc.) |
| utility_type | string | Type: electric, gas, telephone |
| length_ft | float | Line length in feet |
| length_miles | float | Line length in miles |
| geometry | geometry | Line path |

### Summary Statistics
| Utility Type | Count | Total Miles |
|--------------|-------|-------------|
| gas | 65 | 129.6 |
| electric | 56 | 107.2 |
| telephone | 4 | 14.1 |

### Operators
- Virginia Power (55 lines)
- Plantation Gas (19 lines)
- Colonial Gas (14 lines)
- Columbia Gas (10 lines)
- Transcontinental Gas (5 lines)
- AT&T (4 lines)
- Others (18 lines)

## Usage Example

```python
import geopandas as gpd
from shapely.geometry import Point

# Load utility lines
utilities = gpd.read_parquet('data/fairfax/utilities/processed/utility_lines.parquet')

# Find utility lines within 500 feet of a property
property_point = Point(-77.3064, 38.8462)
property_buffer = gpd.GeoSeries([property_point], crs='EPSG:4326').to_crs('EPSG:32618').buffer(152.4)  # 500 ft
property_buffer_wgs84 = property_buffer.to_crs('EPSG:4326')

nearby = utilities[utilities.intersects(property_buffer_wgs84.iloc[0])]
print(f"Utility lines within 500 ft: {len(nearby)}")
for _, line in nearby.iterrows():
    print(f"  {line['utility_type']}: {line['operator']}")
```
