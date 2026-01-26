# School Boundaries - Processed Files

**These files ARE committed to GitHub**

## Contents

- `elementary_zones.geojson` - Elementary school attendance areas
- `middle_zones.geojson` - Middle school attendance areas
- `high_zones.geojson` - High school attendance areas
- `aap_zones.geojson` - Advanced Academic Program boundaries (if available)

## Attributes

Key fields preserved:
- `SCHOOL_NAME` - Official school name
- `SCHOOL_ID` - School identifier
- `LEVEL` - Elementary/Middle/High

## Loading Data

```python
import geopandas as gpd

elementary = gpd.read_file('elementary_zones.geojson')
middle = gpd.read_file('middle_zones.geojson')
high = gpd.read_file('high_zones.geojson')
```

## School Zone Lookup

Use point-in-polygon to find schools for an address:
```python
from shapely.geometry import Point

point = Point(lon, lat)
for _, zone in elementary.iterrows():
    if zone.geometry.contains(point):
        print(f"Elementary: {zone.SCHOOL_NAME}")
```
