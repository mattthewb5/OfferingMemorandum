# County Auto-Detection Strategy

## Problem Statement

Given an address input (e.g., "6560 Braddock Rd, Alexandria, VA 22312"), automatically determine whether the property is in Loudoun County or Fairfax County to route to the appropriate analysis modules.

## Geographic Bounds Reference

### Loudoun County (from config/loudoun.py)
```python
county_bounds = {
    'min_lat': 38.8,
    'max_lat': 39.3,
    'min_lon': -78.0,
    'max_lon': -77.3
}
```

### Fairfax County (from data analysis)
```python
county_bounds = {
    'min_lat': 38.6,
    'max_lat': 39.0,
    'min_lon': -77.6,
    'max_lon': -77.1
}
```

### Overlap Zone
The counties share a boundary region:
- Latitude: 38.8° - 39.0°N
- Longitude: -77.6° - -77.3°W

**Critical**: This overlap zone means bounding box alone is NOT sufficient for accurate detection.

---

## Detection Options Analysis

### Option A: Coordinate-Based Detection (Bounding Box)

**Implementation:**
```python
LOUDOUN_BOUNDS = {'min_lat': 38.8, 'max_lat': 39.3, 'min_lon': -78.0, 'max_lon': -77.3}
FAIRFAX_BOUNDS = {'min_lat': 38.6, 'max_lat': 39.0, 'min_lon': -77.6, 'max_lon': -77.1}

def detect_county_bounds(lat: float, lon: float) -> Optional[str]:
    """Rough detection via bounding box."""
    in_loudoun = (LOUDOUN_BOUNDS['min_lat'] <= lat <= LOUDOUN_BOUNDS['max_lat'] and
                  LOUDOUN_BOUNDS['min_lon'] <= lon <= LOUDOUN_BOUNDS['max_lon'])
    in_fairfax = (FAIRFAX_BOUNDS['min_lat'] <= lat <= FAIRFAX_BOUNDS['max_lat'] and
                  FAIRFAX_BOUNDS['min_lon'] <= lon <= FAIRFAX_BOUNDS['max_lon'])

    if in_loudoun and not in_fairfax:
        return 'loudoun'
    elif in_fairfax and not in_loudoun:
        return 'fairfax'
    elif in_loudoun and in_fairfax:
        return None  # Overlap zone - need more precise detection
    else:
        return None  # Outside both counties
```

**Pros:**
- Simple, fast
- No external dependencies
- Works offline

**Cons:**
- Cannot handle overlap zone (significant area)
- May misclassify edge cases
- Bounding boxes are rectangular, counties are not

**Accuracy Estimate**: ~70-80%

---

### Option B: Address String Parsing

**Implementation:**
```python
LOUDOUN_CITIES = [
    'LEESBURG', 'ASHBURN', 'STERLING', 'PURCELLVILLE', 'MIDDLEBURG',
    'HAMILTON', 'LOVETTSVILLE', 'ROUND HILL', 'HILLSBORO', 'ALDIE',
    'BRAMBLETON', 'SOUTH RIDING', 'LANSDOWNE', 'BROADLANDS'
]

FAIRFAX_CITIES = [
    'FAIRFAX', 'VIENNA', 'MCLEAN', 'FALLS CHURCH', 'ANNANDALE',
    'SPRINGFIELD', 'RESTON', 'HERNDON', 'BURKE', 'CENTREVILLE',
    'CHANTILLY', 'OAKTON', 'TYSONS', 'GREAT FALLS', 'LORTON',
    'ALEXANDRIA'  # Note: Alexandria proper is independent, but Fairfax parts exist
]

SHARED_CITIES = ['CHANTILLY', 'CENTREVILLE']  # Cross county boundaries

def detect_county_string(address: str) -> Optional[str]:
    """Parse address for city/town indicators."""
    address_upper = address.upper()

    # Check for exclusive cities first
    for city in LOUDOUN_CITIES:
        if city in address_upper and city not in SHARED_CITIES:
            return 'loudoun'

    for city in FAIRFAX_CITIES:
        if city in address_upper and city not in SHARED_CITIES:
            return 'fairfax'

    # Check ZIP codes for definitive detection
    loudoun_zips = ['20175', '20176', '20177', '20178', '20180', '20147', '20148', '20152']
    fairfax_zips = ['22030', '22031', '22032', '22033', '22180', '22182', '22124', '22101']

    for zip_code in loudoun_zips:
        if zip_code in address:
            return 'loudoun'

    for zip_code in fairfax_zips:
        if zip_code in address:
            return 'fairfax'

    return None  # Unable to determine
```

**Pros:**
- Fast, no geocoding needed
- ZIP codes are definitive
- Works before geocoding

**Cons:**
- May fail on addresses without city/ZIP
- Shared cities cause ambiguity
- Misspellings cause failures

**Accuracy Estimate**: ~85-90% (when city/ZIP present)

---

### Option C: Google Geocoding Response Parsing (Recommended)

**Implementation:**
```python
def detect_county_from_geocode(address: str, api_key: str) -> Tuple[Optional[str], Optional[Tuple[float, float]]]:
    """
    Geocode address and extract county from Google's response.

    Google Maps Geocoding API returns administrative_area components
    that include county information.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': address, 'key': api_key}

    response = requests.get(url, params=params, timeout=5)
    data = response.json()

    if data['status'] != 'OK':
        return None, None

    result = data['results'][0]
    location = result['geometry']['location']
    coords = (location['lat'], location['lng'])

    # Parse address components for county
    for component in result['address_components']:
        types = component['types']

        if 'administrative_area_level_2' in types:  # County level
            county_name = component['long_name'].upper()

            if 'LOUDOUN' in county_name:
                return 'loudoun', coords
            elif 'FAIRFAX' in county_name:
                return 'fairfax', coords

    return None, coords
```

**Pros:**
- Highly accurate (uses Google's authoritative data)
- Returns both county AND coordinates in one call
- Handles edge cases and ambiguous addresses
- Already integrated (app uses Google geocoding)

**Cons:**
- Requires Google Maps API call
- Costs money (though already paying for geocoding)
- Requires network connectivity

**Accuracy Estimate**: ~99%+

---

### Option D: Polygon Containment (GIS-Based)

**Implementation:**
```python
import geopandas as gpd
from shapely.geometry import Point

# Load county boundary polygons (pre-processed GeoJSON)
LOUDOUN_BOUNDARY = gpd.read_file('data/boundaries/loudoun_county.geojson').geometry[0]
FAIRFAX_BOUNDARY = gpd.read_file('data/boundaries/fairfax_county.geojson').geometry[0]

def detect_county_polygon(lat: float, lon: float) -> Optional[str]:
    """Precise detection via polygon containment."""
    point = Point(lon, lat)  # Note: Shapely uses (lon, lat) order

    if LOUDOUN_BOUNDARY.contains(point):
        return 'loudoun'
    elif FAIRFAX_BOUNDARY.contains(point):
        return 'fairfax'
    else:
        return None
```

**Pros:**
- Most precise geographic method
- Works offline after initial load
- Handles irregular county boundaries
- Can be cached for performance

**Cons:**
- Requires county boundary data files
- Requires GeoPandas/Shapely dependencies
- Slightly slower than bounding box

**Accuracy Estimate**: ~99.9%

---

## Recommended Strategy: Cascading Detection

Use multiple methods in order of cost/accuracy:

```python
def detect_county(address: str, lat: float = None, lon: float = None,
                  google_api_key: str = None) -> Tuple[str, Tuple[float, float]]:
    """
    Detect county using cascading strategy.

    Returns: (county_name, (lat, lon))
    """
    # Step 1: Quick string parsing (free, instant)
    county = detect_county_string(address)
    if county and not has_shared_city(address):
        if lat and lon:
            return county, (lat, lon)
        # Still need to geocode for coordinates

    # Step 2: Geocode and extract county (most reliable)
    if google_api_key:
        county, coords = detect_county_from_geocode(address, google_api_key)
        if county:
            return county, coords
        elif coords:
            lat, lon = coords

    # Step 3: Polygon containment fallback (if geocoding didn't return county)
    if lat and lon:
        county = detect_county_polygon(lat, lon)
        if county:
            return county, (lat, lon)

    # Step 4: Bounding box last resort
    if lat and lon:
        county = detect_county_bounds(lat, lon)
        if county:
            return county, (lat, lon)

    # Unable to determine
    return None, (lat, lon) if lat and lon else (None, None)
```

---

## Implementation Recommendation

### Primary Method: Google Geocoding Response Parsing

**Rationale:**
1. App already uses Google Geocoding - zero additional API calls
2. Google returns `administrative_area_level_2` which IS the county
3. 99%+ accuracy from authoritative source
4. Single function handles both geocoding and county detection

### Fallback: Polygon Containment

**Rationale:**
1. Handles cases where Google doesn't return county component
2. Works if API is temporarily unavailable
3. Already have GeoDataFrames loaded for other analysis

### Data Files Needed

```
data/boundaries/
├── loudoun_county.geojson    # Loudoun boundary polygon
├── fairfax_county.geojson    # Fairfax boundary polygon
└── va_counties.geojson       # Optional: all VA counties
```

---

## Error Handling Strategy

```python
def detect_county_with_error_handling(address: str, api_key: str) -> Dict:
    """
    Comprehensive county detection with error handling.

    Returns:
        {
            'county': 'loudoun' | 'fairfax' | None,
            'confidence': 'high' | 'medium' | 'low',
            'lat': float,
            'lon': float,
            'detection_method': str,
            'error': str | None
        }
    """
    result = {
        'county': None,
        'confidence': None,
        'lat': None,
        'lon': None,
        'detection_method': None,
        'error': None
    }

    try:
        # Try Google geocoding
        county, coords = detect_county_from_geocode(address, api_key)

        if county:
            result['county'] = county
            result['confidence'] = 'high'
            result['lat'], result['lon'] = coords
            result['detection_method'] = 'google_geocode'
            return result

        # Geocoding worked but no county returned
        if coords:
            result['lat'], result['lon'] = coords

            # Try polygon containment
            county = detect_county_polygon(coords[0], coords[1])
            if county:
                result['county'] = county
                result['confidence'] = 'high'
                result['detection_method'] = 'polygon_containment'
                return result

            # Try bounding box
            county = detect_county_bounds(coords[0], coords[1])
            if county:
                result['county'] = county
                result['confidence'] = 'medium'
                result['detection_method'] = 'bounding_box'
                return result

        result['error'] = 'Unable to determine county'
        result['confidence'] = 'low'

    except Exception as e:
        result['error'] = str(e)

        # Try string parsing as last resort
        county = detect_county_string(address)
        if county:
            result['county'] = county
            result['confidence'] = 'low'
            result['detection_method'] = 'string_parsing'

    return result
```

---

## User Experience for Unsupported Counties

```python
def handle_unsupported_county(detection_result: Dict) -> None:
    """Display appropriate message for unsupported counties."""

    if detection_result['county'] is None:
        st.error("""
        **Unable to determine county**

        This tool currently supports:
        - **Loudoun County, VA**
        - **Fairfax County, VA**

        Please verify your address is within one of these counties.
        """)
    elif detection_result['county'] not in ['loudoun', 'fairfax']:
        st.warning(f"""
        **{detection_result['county'].title()} County is not yet supported**

        This tool currently supports Loudoun and Fairfax counties.
        Support for {detection_result['county'].title()} County may be added in the future.
        """)
```

---

## Summary

| Method | Speed | Accuracy | Cost | Recommended |
|--------|-------|----------|------|-------------|
| String Parsing | Instant | 85-90% | Free | Pre-filter |
| Bounding Box | Instant | 70-80% | Free | Last resort |
| Google Geocode | 50-200ms | 99%+ | API call | **Primary** |
| Polygon GIS | 10-50ms | 99.9% | Free (offline) | Fallback |

**Final Recommendation**: Use Google Geocoding response as primary (already doing geocoding, just parse county from response), with polygon containment as fallback.
