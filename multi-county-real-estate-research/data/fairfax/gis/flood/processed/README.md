# Flood Zones - Processed Files

**These files ARE committed to GitHub**

## Contents

- `flood_zones.geojson` - FEMA flood hazard areas

## Attributes

Key fields preserved:
- `FLOOD_ZONE` - FEMA zone designation (AE, X, etc.)
- `BFE` - Base Flood Elevation (where applicable)
- `ZONE_DESC` - Zone description

## FEMA Zone Codes

- **AE**: 100-year flood zone with BFE determined
- **A**: 100-year flood zone without BFE
- **X**: 500-year flood zone or minimal risk
- **VE**: Coastal flood zone with wave action

## Loading Data

```python
import geopandas as gpd

flood = gpd.read_file('flood_zones.geojson')
high_risk = flood[flood.FLOOD_ZONE.str.startswith('A')]
```
