# Module API Compatibility Analysis

## Overview

This analysis compares the APIs of Loudoun and Fairfax county modules to determine compatibility for a unified Streamlit app. Key finding: **APIs are NOT directly compatible** - different design patterns, method signatures, and module structures.

## Pattern Summary

| Aspect | Loudoun Modules | Fairfax Modules |
|--------|-----------------|-----------------|
| Architecture | Mixed: Functions + Classes | Uniform: Class-based |
| Instantiation | Function calls or class instances | Class instances |
| Parameter Style | Mixed (tuples, separate params) | Consistent (lat, lon) |
| Data Loading | At function call time | At class instantiation |
| Caching | External `@st.cache_data` | Internal to class |

---

## Module-by-Module Comparison

### 1. Schools Module

**Loudoun**: `school_lookup.py` - Class-based with API/CSV fallback
```python
class SchoolLookup:
    def __init__(self, county_config: CountyConfig)
    def get_schools(self, address: str, lat: float, lon: float) -> SchoolAssignment
    def get_school_performance(self, school: School) -> School
```

**Fairfax**: `fairfax_schools_analysis.py` - GeoDataFrame-based spatial lookup
```python
class FairfaxSchoolsAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_assigned_schools(self, lat: float, lon: float) -> Dict
    def get_school_facilities(self, lat, lon, radius_miles=5.0, school_types=None, limit=10) -> List[Dict]
    def search_schools(self, query: str, limit: int = 10) -> List[Dict]
    def get_statistics(self) -> Dict
```

**Compatibility: ❌ DIFFERENT**
- Method names differ (`get_schools` vs `get_assigned_schools`)
- Loudoun requires `address` param, Fairfax only needs lat/lon
- Return types differ (SchoolAssignment class vs Dict)
- **Adapter needed**: Yes

---

### 2. Zoning Module

**Loudoun**: `loudoun_zoning_analysis.py` - Function-based with development probability
```python
def analyze_property_zoning_loudoun(lat: float, lon: float) -> Dict[str, Any]
def get_zoning_data_loudoun(lat: float, lon: float) -> Dict[str, Any]
def calculate_development_probability_loudoun(current_zoning, place_type) -> Dict
def classify_development_risk(score: int) -> str
```

**Fairfax**: `fairfax_zoning_analysis.py` - Class-based
```python
class FairfaxZoningAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_zoning(self, lat: float, lon: float) -> Dict
    def get_overlays(self, lat: float, lon: float) -> List[Dict]
    def check_airport_noise(self, lat: float, lon: float) -> Optional[Dict]
    def search_zones(self, zone_code_pattern: str, limit: int = 20) -> List[Dict]
    def get_statistics(self) -> Dict
```

**Compatibility: ❌ DIFFERENT**
- Loudoun uses functions, Fairfax uses class
- Loudoun has extensive development probability analysis
- Method names differ (`analyze_property_zoning_loudoun` vs `get_zoning`)
- **Adapter needed**: Yes - significant wrapper required

---

### 3. Flood Module

**Loudoun**: Function embedded in app - `check_flood_zone(lat, lon)`
```python
# In loudoun_streamlit_app.py (not a separate module)
def check_flood_zone(lat: float, lon: float) -> Dict
```

**Fairfax**: `fairfax_flood_analysis.py` - Full class-based module
```python
class FairfaxFloodAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_flood_risk(self, lat: float, lon: float) -> Dict
    def get_fema_zone(self, lat: float, lon: float) -> Optional[Dict]
    def get_dam_inundation_risk(self, lat: float, lon: float) -> List[Dict]
    def check_floodplain_easement(self, lat: float, lon: float) -> Dict
    def get_statistics(self) -> Dict
```

**Compatibility: ❌ DIFFERENT**
- Loudoun has inline function, Fairfax has full module
- Fairfax is much more comprehensive
- **Adapter needed**: Yes - Loudoun needs refactor to match

---

### 4. Crime Module

**Loudoun**: `crime_analysis.py` - Uses county config
```python
class CrimeAnalysis:
    def __init__(self, county_config: CountyConfig)
    def get_crime_data(self, address: str, lat: float, lon: float,
                       radius_miles: float = 0.5) -> CrimeAnalysisResult
```

**Fairfax**: `fairfax_crime_analysis.py` - Standalone
```python
class FairfaxCrimeAnalysis:
    def __init__(self, data_path: Optional[Path] = None)
    def get_crimes_near_point(self, lat, lon, radius_miles=0.5, months_back=None, category_filter=None) -> pd.DataFrame
    def calculate_safety_score(self, lat, lon, radius_miles=0.5, months_back=6) -> Dict
    def get_crime_trends(self, lat, lon, radius_miles=0.5, months_back=12) -> Dict
    def get_crime_breakdown(self, lat, lon, radius_miles=0.5, months_back=6) -> Dict
```

**Compatibility: ❌ DIFFERENT**
- Loudoun needs `address`, Fairfax doesn't
- Loudoun uses config injection
- Method names and return types differ
- **Adapter needed**: Yes

---

### 5. Permits/Development Module

**Loudoun**: `development_pressure_analyzer.py` + inline functions
```python
# In app - analyze_development(lat, lon, radius_miles=2.0)
def analyze_development(lat: float, lon: float, radius_miles: float = 2.0) -> Dict
```

**Fairfax**: `fairfax_permits_analysis.py`
```python
class FairfaxPermitsAnalysis:
    def __init__(self, data_path: Optional[Path] = None)
    def calculate_development_pressure(self, lat, lon, radius_miles=1.0, months_back=24) -> Dict
    def get_permits_near_point(self, lat, lon, radius_miles=1.0, months_back=None, category_filter=None) -> pd.DataFrame
    def get_permit_trends(self, lat, lon, radius_miles=1.0, months_back=24) -> Dict
```

**Compatibility: ⚠️ SIMILAR CONCEPT**
- Both analyze development pressure
- Method names differ
- Radius defaults differ (2.0 vs 1.0 miles)
- **Adapter needed**: Yes - moderate effort

---

### 6. Healthcare Module

**Loudoun**: `display_medical_access_section()` in app + inline functions
```python
# In loudoun_streamlit_app.py
def display_medical_access_section(lat: float, lon: float)
# Uses inline hospital data loading
```

**Fairfax**: `fairfax_healthcare_analysis.py`
```python
class FairfaxHealthcareAnalysis:
    def __init__(self, data_path: Optional[Path] = None)
    def calculate_healthcare_access_score(self, lat: float, lon: float) -> Dict
    def get_facilities_near_point(self, lat, lon, radius_miles=10.0, facility_type=None) -> pd.DataFrame
    def get_quality_metrics(self, facility_name: str) -> Dict
    def compare_facilities(self, lat, lon, radius_miles=10.0, facility_type='hospital', top_n=5) -> pd.DataFrame
```

**Compatibility: ❌ DIFFERENT**
- Loudoun has inline code, Fairfax has full module
- **Adapter needed**: Yes - Loudoun needs refactor

---

### 7. Subdivisions Module

**Loudoun**: Not available as separate module
- Community lookup exists (`loudoun_community_lookup.py`) but different concept

**Fairfax**: `fairfax_subdivisions_analysis.py`
```python
class FairfaxSubdivisionsAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_subdivision(self, lat: float, lon: float) -> Dict
    def get_nearby_subdivisions(self, lat, lon, radius_miles=1.0, limit=10) -> List[Dict]
    def search_subdivisions(self, name_pattern: str, limit: int = 20) -> List[Dict]
    def get_statistics(self) -> Dict
```

**Compatibility: ❌ NO LOUDOUN EQUIVALENT**
- Fairfax-specific feature
- **Adapter needed**: N/A - display conditionally

---

### 8. Utilities Module

**Loudoun**: `loudoun_utilities_analysis.py` - Power line focus
```python
class PowerLineAnalyzer:
    def __init__(self, geojson_path: Optional[str] = None)
    def analyze_proximity(self, lat: float, lon: float, radius_miles: float = 2.0) -> Dict

def analyze_power_line_proximity(lat: float, lon: float) -> Dict
```

**Fairfax**: `fairfax_utilities_analysis.py` - Multiple utility types
```python
class FairfaxUtilitiesAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_nearby_utilities(self, lat, lon, radius_miles=0.5, utility_types=None, limit=20) -> List[Dict]
    def check_proximity(self, lat, lon, distance_threshold_miles=0.1) -> Dict
    def get_utility_types_nearby(self, lat, lon, radius_miles=0.5) -> Dict
    def get_statistics(self) -> Dict
```

**Compatibility: ⚠️ PARTIAL**
- Both analyze utility proximity
- Loudoun focuses on power lines only
- Fairfax includes gas and telephone
- **Adapter needed**: Yes - wrapper to normalize API

---

### 9. Parks Module

**Loudoun**: Inline in app - `get_nearest_parks()`
```python
# In loudoun_streamlit_app.py
def load_parks_data() -> List[Dict]
def get_nearest_parks(lat, lon, parks_data) -> List[Dict]
```

**Fairfax**: `fairfax_parks_analysis.py`
```python
class FairfaxParksAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_nearby_parks(self, lat, lon, radius_miles=1.0, park_types=None, limit=10) -> List[Dict]
    def get_trail_access(self, lat, lon, radius_miles=1.0) -> Dict
    def get_recreational_amenities(self, lat, lon, radius_miles=0.5, amenity_types=None, limit=20) -> List[Dict]
    def calculate_park_access_score(self, lat, lon) -> Dict
    def get_statistics(self) -> Dict
```

**Compatibility: ⚠️ PARTIAL**
- Similar concept, different implementation
- Fairfax is much more comprehensive
- **Adapter needed**: Yes

---

### 10. Transit Module

**Loudoun**: `loudoun_metro_analysis.py` - Metro-focused functions
```python
def analyze_metro_access(property_coords: Tuple[float, float]) -> Dict
def calculate_metro_proximity(property_coords: Tuple[float, float]) -> Dict
def generate_metro_narrative(proximity_data: Dict, tier_data: Dict) -> str
```

**Fairfax**: `fairfax_transit_analysis.py` - Full class with bus + Metro
```python
class FairfaxTransitAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def calculate_transit_score(self, lat: float, lon: float) -> Dict
    def get_nearest_metro_station(self, lat: float, lon: float) -> Dict
    def get_nearby_bus_routes(self, lat, lon, radius_miles=0.5, service_type=None, limit=10) -> List[Dict]
    def get_commute_options(self, lat: float, lon: float) -> Dict
    def get_statistics(self) -> Dict
```

**Compatibility: ⚠️ PARTIAL**
- Loudoun uses tuple `(lat, lon)`, Fairfax uses separate params
- Fairfax includes bus routes, Loudoun is Metro-only
- **Adapter needed**: Yes

---

### 11. Emergency Services Module

**Loudoun**: Not available as separate module

**Fairfax**: `fairfax_emergency_services_analysis.py`
```python
class FairfaxEmergencyServicesAnalysis:
    def __init__(self, data_dir: Optional[Path] = None)
    def get_nearest_fire_station(self, lat: float, lon: float) -> Dict
    def get_nearest_police_station(self, lat: float, lon: float) -> Dict
    def assess_fire_protection_iso(self, lat: float, lon: float) -> Dict
    def get_emergency_services_coverage(self, lat, lon, fire_radius_miles=5.0, police_radius_miles=5.0) -> Dict
    def get_response_time_estimates(self, lat: float, lon: float) -> Dict
    def get_statistics(self) -> Dict
```

**Compatibility: ❌ NO LOUDOUN EQUIVALENT**
- Fairfax-specific feature
- **Adapter needed**: N/A - display conditionally

---

## Fairfax-Only Modules (No Loudoun Equivalent)

### 12. Cell Towers Analysis
```python
class FairfaxCellTowersAnalysis:
    def calculate_coverage_score(self, lat: float, lon: float) -> Dict
    def get_nearest_towers(self, lat, lon, limit=5) -> List[Dict]
    def get_towers_by_city(self, city: str) -> pd.DataFrame
    def get_statistics(self) -> Dict
```

### 13. School Performance Analysis
```python
class FairfaxSchoolPerformanceAnalysis:
    def get_school_performance(self, school_name: str) -> Dict
    def calculate_school_quality_score(self, school_name: str) -> Dict
    def get_school_trends(self, school_name: str, years: int = 5) -> Dict
    def compare_schools(self, school_names: List[str]) -> pd.DataFrame
    def get_statistics(self) -> Dict
```

### 14. Traffic Analysis
```python
class FairfaxTrafficAnalysis:
    def calculate_traffic_exposure_score(self, lat: float, lon: float) -> Dict
    def get_nearby_traffic(self, lat, lon, radius_miles=0.5) -> List[Dict]
    def get_road_traffic(self, road_name: str, limit=50) -> List[Dict]
    def analyze_commute_corridor(self, lat, lon, direction='east') -> Dict
    def get_statistics(self) -> Dict
```

---

## Summary Table

| Module | API Compatible? | Adapter Complexity | Notes |
|--------|-----------------|-------------------|-------|
| Schools | ❌ | HIGH | Method names, params, return types differ |
| Zoning | ❌ | HIGH | Function vs class, extensive differences |
| Flood | ❌ | MEDIUM | Loudoun inline, Fairfax modular |
| Crime | ❌ | MEDIUM | Config injection vs standalone |
| Permits | ⚠️ | MEDIUM | Similar concept, different API |
| Healthcare | ❌ | HIGH | Loudoun inline, Fairfax modular |
| Subdivisions | N/A | N/A | Fairfax only |
| Utilities | ⚠️ | LOW | Similar, scope differs |
| Parks | ⚠️ | MEDIUM | Similar concept, Fairfax more comprehensive |
| Transit | ⚠️ | MEDIUM | Tuple vs separate params |
| Emergency Services | N/A | N/A | Fairfax only |
| Cell Towers | N/A | N/A | Fairfax only |
| School Performance | N/A | N/A | Fairfax only |
| Traffic | N/A | N/A | Fairfax only |

---

## Recommendations

### Option A: Create Unified Interface Layer (Recommended)
Create adapter classes that provide a consistent API for both counties:

```python
class UnifiedSchoolsAnalyzer:
    def __init__(self, county: str):
        if county == 'loudoun':
            self._analyzer = LoudounSchoolsAdapter()
        else:
            self._analyzer = FairfaxSchoolsAnalysis()

    def get_assigned_schools(self, lat: float, lon: float) -> Dict:
        return self._analyzer.get_assigned_schools(lat, lon)
```

### Option B: County-Specific Conditional Logic
Use if/else in the Streamlit app for each module call:

```python
if county == 'loudoun':
    schools = school_lookup.get_schools(address, lat, lon)
    # Transform to common format
else:
    analyzer = FairfaxSchoolsAnalysis()
    schools = analyzer.get_assigned_schools(lat, lon)
```

### Option C: Refactor Loudoun Modules
Bring Loudoun modules up to Fairfax's class-based pattern (significant effort).

---

## Estimated Adapter Effort

| Module | Effort (hours) | Priority |
|--------|---------------|----------|
| Schools | 4-6 | HIGH |
| Zoning | 6-8 | HIGH |
| Crime | 3-4 | HIGH |
| Transit | 3-4 | HIGH |
| Parks | 2-3 | MEDIUM |
| Utilities | 2-3 | MEDIUM |
| Flood | 3-4 | MEDIUM |
| Healthcare | 4-5 | MEDIUM |
| Permits | 3-4 | MEDIUM |

**Total Adapter Development: ~30-40 hours**
