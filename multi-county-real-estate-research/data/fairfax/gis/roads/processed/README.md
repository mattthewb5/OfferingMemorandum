# Road Centerlines - Processed Files

**These files ARE committed to GitHub**

## Contents

- `roads.geojson` - Road centerlines in WGS84 coordinates

## Attributes

Key fields preserved:
- `FULLNAME` - Full street name
- `ROUTE_NUMBER` - Route designation (if applicable)
- `FUNCTIONAL_CLASS` - Road classification
- `SPEED_LIMIT` - Posted speed limit

## Loading Data

```python
import geopandas as gpd

roads = gpd.read_file('roads.geojson')
print(f"Loaded {len(roads):,} road segments")
```
