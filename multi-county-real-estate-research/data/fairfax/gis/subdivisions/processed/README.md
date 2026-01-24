# Subdivisions - Processed Files

**These files ARE committed to GitHub**

## Contents

- `subdivisions.geojson` - Recorded subdivision boundaries

## Attributes

Key fields preserved:
- `SUBDIV_NAME` - Official subdivision name
- `PLAT_DATE` - Recording date
- `SECTION` - Section number within subdivision

## Loading Data

```python
import geopandas as gpd

subdivisions = gpd.read_file('subdivisions.geojson')
print(f"Loaded {len(subdivisions):,} subdivisions")
```

## Community Lookup

Use to identify community/HOA membership:
```python
from shapely.geometry import Point

point = Point(lon, lat)
for _, subdiv in subdivisions.iterrows():
    if subdiv.geometry.contains(point):
        print(f"Subdivision: {subdiv.SUBDIV_NAME}")
```
