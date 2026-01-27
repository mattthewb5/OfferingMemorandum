# Fairfax County Flood Data - Processed

## Data Sources
- **FEMA Flood Zones:** FEMA Flood Risk Database (FRD_51059C), July 2021
- **Dam Inundation:** Fairfax County GIS (Non-DPWES dams)
- **Easements:** Fairfax County Recorded Floodplain Easements
- **Processing Date:** January 27, 2026

## Files

### fema_zones.parquet
FEMA flood zone boundaries from the Flood Risk Database.
- **Records:** 3,313
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| zone_code | string | FEMA flood zone code (A, AE, AH, A99, X) |
| zone_subtype | string | Zone subtype if applicable |
| previous_zone | string | Previous flood zone designation |
| sfha_change | string | Special Flood Hazard Area change indicator |
| risk_level | string | Risk classification (high, moderate, minimal) |
| description | string | Human-readable zone description |
| geometry | geometry | Flood zone boundary |

### FEMA Zone Codes
| Zone | Risk | Count | Description |
|------|------|-------|-------------|
| X | Minimal | 2,110 | Areas outside the 0.2% annual chance flood |
| AE | High | 677 | 1% annual chance flood with Base Flood Elevation |
| A | High | 515 | 1% annual chance flood, no BFE determined |
| A99 | Moderate | 7 | Protected by federal flood protection system |
| AH | High | 4 | 1% annual chance shallow flooding (1-3 ft ponding) |

### Risk Level Distribution
- **High:** 1,196 zones (A, AE, AH)
- **Moderate:** 7 zones (A99)
- **Minimal:** 2,110 zones (X)

### dam_inundation.parquet
Dam break inundation zones for non-DPWES regulated dams.
- **Records:** 17
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)
- **Unique Dams:** 16

| Field | Type | Description |
|-------|------|-------------|
| dam_name | string | Name of the dam |
| dam_owner | string | Dam owner/operator |
| break_type | string | Failure scenario (e.g., PMF Overtopping) |
| geometry | geometry | Inundation zone boundary |

### Dams Included
- Burke Lake Dam
- Fox Lake Dam
- Lake Accotink Dam
- Lake Anne Dam
- Lake Audoban Dam
- Lake Barcroft Dam
- Lake Fairfax
- Lake Newport Dam
- Lake Thoreau Dam
- North Twin Lake / South Twin Lake
- NVCC Annandale Campus Lake Dam
- Reston Town Center Western BMP Dam
- Upper Occoquan Dam
- And others...

### easements.parquet
Recorded floodplain easements.
- **Records:** 897
- **Geometry:** Polygon/MultiPolygon
- **CRS:** EPSG:4326 (WGS84)

| Field | Type | Description |
|-------|------|-------------|
| easement_id | int | Unique easement identifier |
| easement_type | string | "floodplain" |
| geometry | geometry | Easement boundary |

## Usage Example
```python
import geopandas as gpd
from shapely.geometry import Point

# Load flood data
fema = gpd.read_parquet('fema_zones.parquet')
dams = gpd.read_parquet('dam_inundation.parquet')
easements = gpd.read_parquet('easements.parquet')

# Check flood risk for a property
lat, lon = 38.8969, -77.4327
point = Point(lon, lat)

# FEMA flood zone
flood = fema[fema.geometry.contains(point)]
if len(flood) > 0:
    zone = flood.iloc[0]
    print(f"Flood Zone: {zone['zone_code']} ({zone['risk_level']} risk)")
    print(f"  {zone['description']}")

# Dam inundation check
dam_risk = dams[dams.geometry.contains(point)]
if len(dam_risk) > 0:
    for _, row in dam_risk.iterrows():
        print(f"Dam Inundation Risk: {row['dam_name']}")

# Easement check
in_easement = easements[easements.geometry.contains(point)]
if len(in_easement) > 0:
    print(f"Property is within {len(in_easement)} floodplain easement(s)")
```

## Risk Assessment Notes
- **High Risk (A, AE, AH):** Properties require flood insurance if federally-backed mortgage
- **Moderate Risk (A99):** Lower premiums due to federal protection, but still recommended
- **Minimal Risk (X):** Flood insurance not required but recommended
- **Dam Inundation:** Not FEMA-regulated but important for emergency planning
