# Fairfax County Zoning - Processed Data

## Data Source
- **Provider:** Fairfax County GIS Open Data
- **URL:** https://data-fairfaxcountygis.opendata.arcgis.com/
- **Processing Date:** January 27, 2026

## Files

### districts.parquet
Zoning district boundaries for all of Fairfax County.
- **Records:** 6,431
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)
- **Unique Zone Codes:** 74

| Field | Type | Description |
|-------|------|-------------|
| zone_code | string | Zoning code (e.g., R-1, C-8, PDH-3) |
| zone_type | string | Category (residential, commercial, industrial, planned_units, tyson, other) |
| has_proffer | bool | Whether proffer conditions apply |
| public_land | bool | Whether designated as public land |
| cluster | string | Cluster designation if applicable |
| geometry | geometry | Zoning district boundary |

### Zone Type Distribution
| Zone Type | Count | Description |
|-----------|-------|-------------|
| residential | 3,962 | Single/multi-family residential |
| planned_units | 1,113 | Planned development districts |
| commercial | 910 | Commercial/retail |
| industrial | 384 | Industrial/manufacturing |
| tyson | 38 | Tysons Corner special district |
| other | 24 | Other/special use |

### Common Zone Codes
- **R-1 to R-8:** Residential (lot size decreases with number)
- **R-C, R-E:** Residential cluster, residential estate
- **C-2 to C-8:** Commercial (intensity increases with number)
- **I-3 to I-6:** Industrial
- **PDH-x:** Planned Development Housing
- **PDC:** Planned Development Commercial

### overlays.parquet
Zoning overlay district boundaries.
- **Records:** 73
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)
- **Unique Overlay Types:** 9

| Field | Type | Description |
|-------|------|-------------|
| overlay_type | string | Type of overlay district |
| decibel_level | float | Noise level (for airport noise overlay) |
| geometry | geometry | Overlay district boundary |

### Overlay Types
| Type | Count | Description |
|------|-------|-------------|
| commercial_development | 16 | Commercial revitalization areas |
| historic | 15 | Historic preservation districts |
| highway_corridor | 14 | Highway corridor overlay |
| sign_control | 8 | Sign regulation areas |
| natural_resource | 7 | Environmental protection |
| heritage_protection | 5 | Heritage resource areas |
| airport_noise_impact | 5 | Dulles Airport noise zones (60-75 dB) |
| commercial_area | 2 | Commercial area overlay |
| water_supply_protection | 1 | Drinking water protection |

## Usage Example
```python
import geopandas as gpd
from shapely.geometry import Point

# Load zoning data
districts = gpd.read_parquet('districts.parquet')
overlays = gpd.read_parquet('overlays.parquet')

# Find zoning for a property
lat, lon = 38.8969, -77.4327
point = Point(lon, lat)

# Check zoning district
zone = districts[districts.geometry.contains(point)]
if len(zone) > 0:
    print(f"Zone: {zone.iloc[0]['zone_code']} ({zone.iloc[0]['zone_type']})")

# Check overlay districts
overlay = overlays[overlays.geometry.contains(point)]
for _, row in overlay.iterrows():
    print(f"Overlay: {row['overlay_type']}")
    if row['decibel_level'] > 0:
        print(f"  Noise level: {row['decibel_level']} dB")
```
