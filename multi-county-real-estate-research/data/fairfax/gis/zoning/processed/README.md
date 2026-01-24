# Zoning Districts - Processed Files

**These files ARE committed to GitHub**

## Contents

- `zoning.geojson` - Zoning district boundaries in WGS84 coordinates

## Attributes

Key fields preserved:
- `ZONE_CODE` - Official zoning designation
- `ZONE_DESC` - Zone description
- `CATEGORY` - General land use category (Residential, Commercial, etc.)

## Loading Data

```python
import geopandas as gpd

zoning = gpd.read_file('zoning.geojson')
print(f"Loaded {len(zoning):,} zoning districts")
```
