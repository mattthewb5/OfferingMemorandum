# Unified Architecture Proposal

## Executive Summary

This document proposes an architecture for integrating Fairfax County support into the existing Loudoun Streamlit app without requiring a county selector. The recommended approach uses a **Module Adapter Pattern** with dynamic module loading based on detected county.

---

## Architecture Options Comparison

### Option A: Module Adapter Pattern (Recommended)

Create unified adapter classes that wrap county-specific modules with a consistent API.

**Structure:**
```
core/
├── adapters/
│   ├── __init__.py
│   ├── base_adapter.py        # Abstract base class
│   ├── schools_adapter.py     # Unified schools interface
│   ├── zoning_adapter.py      # Unified zoning interface
│   ├── transit_adapter.py     # Unified transit interface
│   └── ... (other adapters)
├── fairfax_*.py               # Existing Fairfax modules
├── loudoun_*.py               # Existing Loudoun modules
└── ...
```

**Code Example:**
```python
# core/adapters/base_adapter.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class BaseAnalysisAdapter(ABC):
    """Base class for county-agnostic analysis adapters."""

    def __init__(self, county: str):
        self.county = county.lower()
        self._initialize_backend()

    @abstractmethod
    def _initialize_backend(self) -> None:
        """Initialize the county-specific backend."""
        pass

# core/adapters/schools_adapter.py
from .base_adapter import BaseAnalysisAdapter

class UnifiedSchoolsAdapter(BaseAnalysisAdapter):
    """Unified interface for school analysis across counties."""

    def _initialize_backend(self) -> None:
        if self.county == 'loudoun':
            from core.school_lookup import SchoolLookup
            from config.loudoun import LOUDOUN_CONFIG
            self._backend = SchoolLookup(LOUDOUN_CONFIG)
            self._is_class_based = True
        elif self.county == 'fairfax':
            from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
            self._backend = FairfaxSchoolsAnalysis()
            self._is_class_based = True
        else:
            raise ValueError(f"Unsupported county: {self.county}")

    def get_assigned_schools(self, lat: float, lon: float, address: str = None) -> Dict:
        """Get school assignments for a location."""
        if self.county == 'loudoun':
            # Loudoun requires address
            result = self._backend.get_schools(address or "", lat, lon)
            # Transform to common format
            return {
                'elementary': {
                    'school_name': result.elementary.name if result.elementary else None,
                    'distance_miles': result.elementary.distance if result.elementary else None
                },
                'middle': {
                    'school_name': result.middle.name if result.middle else None,
                    'distance_miles': result.middle.distance if result.middle else None
                },
                'high': {
                    'school_name': result.high.name if result.high else None,
                    'distance_miles': result.high.distance if result.high else None
                },
                'all_assigned': all([result.elementary, result.middle, result.high])
            }
        else:  # fairfax
            return self._backend.get_assigned_schools(lat, lon)
```

**Pros:**
- Clean separation of concerns
- County-specific logic isolated in adapters
- Existing modules unchanged
- Easy to add new counties
- Testable in isolation

**Cons:**
- More code to write initially
- Need to maintain adapters as modules evolve
- Some performance overhead (wrapper layer)

**Effort**: 30-40 hours

---

### Option B: Factory Pattern

Create factory functions that return county-specific module instances.

**Code Example:**
```python
# core/module_factory.py
def get_schools_analyzer(county: str):
    """Factory to create county-specific schools analyzer."""
    if county == 'loudoun':
        from core.school_lookup import SchoolLookup
        from config.loudoun import LOUDOUN_CONFIG
        return SchoolLookup(LOUDOUN_CONFIG)
    elif county == 'fairfax':
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis
        return FairfaxSchoolsAnalysis()
    raise ValueError(f"Unsupported county: {county}")

def get_zoning_analyzer(county: str):
    """Factory to create county-specific zoning analyzer."""
    if county == 'loudoun':
        # Return wrapper for function-based module
        from core.loudoun_zoning_analysis import analyze_property_zoning_loudoun
        return LoudounZoningWrapper()
    elif county == 'fairfax':
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis
        return FairfaxZoningAnalysis()
    raise ValueError(f"Unsupported county: {county}")
```

**Usage in Streamlit:**
```python
# In analyze_property():
schools_analyzer = get_schools_analyzer(county)
zoning_analyzer = get_zoning_analyzer(county)

# Problem: Different APIs require different calls
if county == 'loudoun':
    schools = schools_analyzer.get_schools(address, lat, lon)
else:
    schools = schools_analyzer.get_assigned_schools(lat, lon)
```

**Pros:**
- Simple to implement
- Existing modules unchanged
- Clear module instantiation

**Cons:**
- Calling code still needs county-specific logic
- API differences leak into app code
- More conditionals throughout

**Effort**: 15-20 hours initially, but more maintenance

---

### Option C: Conditional Imports (Simplest)

Use dynamic imports based on detected county.

**Code Example:**
```python
# At the top of analyze_property() or in a setup function
def setup_modules(county: str):
    """Setup module aliases based on county."""
    global SchoolsAnalyzer, ZoningAnalyzer, TransitAnalyzer

    if county == 'loudoun':
        from core.school_lookup import SchoolLookup as SchoolsAnalyzer
        from core.loudoun_zoning_analysis import LoudounZoningAnalyzer as ZoningAnalyzer
        from core.loudoun_metro_analysis import analyze_metro_access as transit_func
    else:
        from core.fairfax_schools_analysis import FairfaxSchoolsAnalysis as SchoolsAnalyzer
        from core.fairfax_zoning_analysis import FairfaxZoningAnalysis as ZoningAnalyzer
        from core.fairfax_transit_analysis import FairfaxTransitAnalysis as TransitAnalyzer

# Problem: APIs are still different even with same name
```

**Pros:**
- Minimal code changes
- No new files
- Fast to implement

**Cons:**
- APIs still differ
- Lots of conditionals needed anyway
- Hard to maintain
- Global state is problematic

**Effort**: 10-15 hours, but tech debt accumulates

---

## Recommended Architecture: Hybrid Adapter + Factory

Combine adapters for complex modules with factories for simpler ones.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     unified_streamlit_app.py                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  County Detection Layer                    │  │
│  │   detect_county(address) → 'loudoun' | 'fairfax'          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                  Analysis Orchestrator                     │  │
│  │   analyze_property(address, lat, lon, county)             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                     Adapter Layer                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          │  │
│  │  │ Schools │ │ Zoning  │ │ Transit │ │  Crime  │ ...      │  │
│  │  │ Adapter │ │ Adapter │ │ Adapter │ │ Adapter │          │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘          │  │
│  └───────┼───────────┼───────────┼───────────┼───────────────┘  │
│          │           │           │           │                   │
└──────────┼───────────┼───────────┼───────────┼───────────────────┘
           │           │           │           │
     ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐ ┌───▼───┐
     │  Loudoun  │ │Loudoun│ │  Loudoun  │ │Loudoun│
     │  Schools  │ │Zoning │ │  Transit  │ │ Crime │
     └───────────┘ └───────┘ └───────────┘ └───────┘
           │           │           │           │
     ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐ ┌───▼───┐
     │  Fairfax  │ │Fairfax│ │  Fairfax  │ │Fairfax│
     │  Schools  │ │Zoning │ │  Transit  │ │ Crime │
     └───────────┘ └───────┘ └───────────┘ └───────┘
```

### Module Priority for Adapter Creation

**Must Have Adapters (Core functionality):**
1. Schools Adapter - Different APIs, return formats
2. Zoning Adapter - Function vs class, complex differences
3. Transit Adapter - Metro-only vs full transit
4. Crime Adapter - Config-based vs standalone

**Simple Wrappers (Similar APIs):**
5. Parks Adapter - Similar concept, normalize output
6. Utilities Adapter - Normalize scope (power-only vs multi-utility)
7. Flood Adapter - Expand Loudoun inline to module

**Passthrough (Fairfax-only, no Loudoun equivalent):**
8. Emergency Services - Fairfax only
9. Cell Towers - Fairfax only
10. School Performance - Fairfax only
11. Traffic - Fairfax only
12. Subdivisions - Fairfax only

### Integration Code Flow

```python
# unified_streamlit_app.py

def main():
    st.title("🏘️ Northern Virginia Property Intelligence")

    # 1. Get address input
    address = st.text_input("Enter an address:", placeholder="e.g., 123 Main St, Vienna, VA 22180")

    if st.button("🔍 Analyze Property"):
        # 2. Detect county
        county_result = detect_county(address, GOOGLE_MAPS_KEY)

        if county_result['county'] is None:
            st.error("Address must be in Loudoun or Fairfax County")
            return

        county = county_result['county']
        lat, lon = county_result['lat'], county_result['lon']

        st.success(f"✓ Detected: **{county.title()} County** ({lat:.6f}, {lon:.6f})")

        # 3. Analyze using adapters
        analyze_property(address, lat, lon, county)


def analyze_property(address: str, lat: float, lon: float, county: str):
    """Orchestrate property analysis using county-specific modules."""

    progress = st.progress(0)

    # Initialize adapters for detected county
    schools_adapter = UnifiedSchoolsAdapter(county)
    zoning_adapter = UnifiedZoningAdapter(county)
    transit_adapter = UnifiedTransitAdapter(county)
    crime_adapter = UnifiedCrimeAdapter(county)
    parks_adapter = UnifiedParksAdapter(county)

    # Common analysis (both counties)
    progress.progress(10)
    schools = schools_adapter.get_assigned_schools(lat, lon, address)

    progress.progress(25)
    zoning = zoning_adapter.get_zoning(lat, lon)

    progress.progress(40)
    transit = transit_adapter.get_transit_score(lat, lon)

    progress.progress(55)
    crime = crime_adapter.get_safety_score(lat, lon)

    progress.progress(70)
    parks = parks_adapter.get_park_access(lat, lon)

    # Fairfax-only analysis
    if county == 'fairfax':
        progress.progress(80)
        cell_towers = FairfaxCellTowersAnalysis().calculate_coverage_score(lat, lon)
        school_performance = FairfaxSchoolPerformanceAnalysis().get_school_performance(
            schools['elementary']['school_name'])
        traffic = FairfaxTrafficAnalysis().calculate_traffic_exposure_score(lat, lon)
    else:
        cell_towers = None
        school_performance = None
        traffic = None

    progress.progress(100)

    # Display results (common UI)
    display_results(county, schools, zoning, transit, crime, parks,
                   cell_towers, school_performance, traffic)
```

---

## Migration Path

### Phase 1: Foundation (Week 1)
1. Create `core/adapters/` directory structure
2. Implement county detection module
3. Create base adapter class
4. Add county boundary data files

### Phase 2: Core Adapters (Week 2)
1. Schools adapter (highest priority)
2. Zoning adapter
3. Transit adapter
4. Crime adapter

### Phase 3: Secondary Adapters (Week 3)
1. Parks adapter
2. Utilities adapter
3. Healthcare adapter
4. Flood adapter

### Phase 4: Integration (Week 4)
1. Create unified_streamlit_app.py
2. Integrate county detection
3. Wire up adapters
4. Handle Fairfax-only features
5. Testing and polish

---

## File Changes Summary

### New Files to Create
```
core/adapters/__init__.py
core/adapters/base_adapter.py
core/adapters/schools_adapter.py
core/adapters/zoning_adapter.py
core/adapters/transit_adapter.py
core/adapters/crime_adapter.py
core/adapters/parks_adapter.py
core/adapters/utilities_adapter.py
core/adapters/healthcare_adapter.py
core/adapters/flood_adapter.py
core/county_detection.py
data/boundaries/loudoun_county.geojson
data/boundaries/fairfax_county.geojson
unified_streamlit_app.py
tests/test_adapters.py
```

### Files to Modify
- None initially (adapters wrap existing modules)
- Later: Could rename `loudoun_streamlit_app.py` → archive

### Files Unchanged
- All existing `fairfax_*.py` modules
- All existing `loudoun_*.py` modules
- All existing config files

---

## Pros/Cons Summary

| Aspect | Adapter Pattern (Recommended) |
|--------|------------------------------|
| Code Clarity | ✅ High - clean separation |
| Maintainability | ✅ High - changes isolated |
| Testing | ✅ Easy - adapters testable in isolation |
| Performance | ⚠️ Slight overhead (negligible) |
| Initial Effort | ⚠️ More upfront work |
| Future Counties | ✅ Easy to add |
| Existing Code | ✅ Unchanged |

---

## Recommendation

**Proceed with the Hybrid Adapter + Factory approach:**

1. Use full adapters for complex modules (Schools, Zoning, Transit, Crime)
2. Use simple wrappers for similar modules (Parks, Utilities)
3. Pass through Fairfax-only modules directly
4. Keep existing module code unchanged
5. New unified app file coordinates everything

This approach provides the best balance of clean architecture, maintainability, and reasonable implementation effort.
