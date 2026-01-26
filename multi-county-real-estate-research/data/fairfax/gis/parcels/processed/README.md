# Tax Parcels - Processed Files

**These files ARE committed to GitHub**

## Contents

Parcel data may be split due to size:
- `parcels.geoparquet` - GeoParquet format for efficient storage
- Or split by district/area if needed

## Attributes

Key fields preserved:
- `PARCEL_ID` - Unique parcel identifier
- `ADDRESS` - Property address
- `ACREAGE` - Parcel size

## Loading Data

```python
import geopandas as gpd

# GeoParquet format
parcels = gpd.read_parquet('parcels.geoparquet')
print(f"Loaded {len(parcels):,} parcels")
```

## Size Management

Due to ~400K parcels, consider:
- Loading only needed columns
- Filtering to area of interest
- Using spatial indexing
