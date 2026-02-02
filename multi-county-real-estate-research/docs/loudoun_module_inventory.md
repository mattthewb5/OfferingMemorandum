# Loudoun County Module Inventory
Generated: 2026-02-02

## Summary
- **Total modules:** 12
- **Fully functional:** 12
- **Needs work:** 0
- **Total data sources:** 15+ data files

## Module Details

---

### 1. Metro Analysis
- **File:** `core/loudoun_metro_analysis.py`
- **Size:** 12.4 KB (376 lines)
- **Status:** ✅ Functional
- **Primary Function:** Silver Line Metro station proximity analysis with distance calculation, accessibility tier classification, and drive time estimates
- **Data Dependencies:** None (hardcoded Metro station coordinates)
- **Key Outputs:**
  - Nearest station name and distance
  - Accessibility tier (Walk-to-Metro, Bike-to-Metro, Metro-Accessible, Metro-Available, Metro-Distant)
  - Estimated drive time
  - Professional narrative
- **Integration Priority:** 🔴 Critical
- **Complexity:** Low
- **Notes:** Standalone module, no external APIs required. Tested and working.

---

### 2. School Percentiles
- **File:** `core/loudoun_school_percentiles.py`
- **Size:** 19.2 KB (571 lines)
- **Status:** ✅ Functional
- **Primary Function:** Provides county and state percentile rankings, trajectory analysis, and narrative-ready school context
- **Data Dependencies:**
  - `data/loudoun/schools/school_performance_trends.csv`
  - `data/loudoun/schools/school_metadata.csv`
- **Key Outputs:**
  - County/state percentile rankings
  - Performance bucket (top_10, top_25, middle, bottom_25)
  - Trajectory direction (improving, declining, stable)
  - Narrative helpers and descriptors
- **Integration Priority:** 🔴 Critical
- **Complexity:** Medium
- **Notes:** Requires pandas. Handles school name normalization robustly.

---

### 3. School Performance
- **File:** `core/loudoun_school_performance.py`
- **Size:** 14.4 KB (443 lines)
- **Status:** ✅ Functional
- **Primary Function:** School performance comparison charts, peer school finding, and coordinate-based school matching
- **Data Dependencies:**
  - `data/loudoun/school_performance_trends_with_state_avg.csv`
  - `data/loudoun/loudoun_school_coordinates.csv`
- **Key Outputs:**
  - Performance trend charts (Plotly)
  - Peer school list with distances
  - School matching by name
- **Integration Priority:** 🟡 Important
- **Complexity:** Medium
- **Notes:** Requires pandas and plotly. Creates visual charts for UI.

---

### 4. Zoning Analysis
- **File:** `core/loudoun_zoning_analysis.py`
- **Size:** 105.6 KB (2700+ lines)
- **Status:** ✅ Functional
- **Primary Function:** Comprehensive zoning analysis including Place Types (2019 Comp Plan), development probability scoring, jurisdiction detection, and town-specific zoning
- **Data Dependencies:**
  - Live API: Loudoun County LOGIS GIS services
  - `data/loudoun/config/placetype_translations.json`
  - `data/loudoun/config/zoning_translations.json`
  - `data/loudoun/building_permits/*.csv`
- **Key Outputs:**
  - Place type and policy area
  - Development probability score (0-100)
  - Risk classification
  - Building permit characterization
  - Zoning/permit narratives
- **Integration Priority:** 🔴 Critical
- **Complexity:** High
- **Notes:** Most comprehensive module. Supports Leesburg and Purcellville town zoning. Has extensive test functions.

---

### 5. Valuation Context
- **File:** `core/loudoun_valuation_context.py`
- **Size:** 14.5 KB (419 lines)
- **Status:** ✅ Functional
- **Primary Function:** Extracts narrative-ready valuation context from PropertyValuationOrchestrator output
- **Data Dependencies:** None (processes orchestrator output)
- **Key Outputs:**
  - Formatted estimate
  - Confidence level/score
  - Price per sqft analysis
  - Comps summary
  - Narrative helpers
- **Integration Priority:** 🔴 Critical
- **Complexity:** Low
- **Notes:** Helper module for narrative generation. No external dependencies.

---

### 6. Community Lookup
- **File:** `core/loudoun_community_lookup.py`
- **Size:** 15.5 KB (424 lines)
- **Status:** ✅ Functional
- **Primary Function:** Matches subdivisions to communities, returns HOA info and amenities
- **Data Dependencies:**
  - `data/loudoun/config/communities.json`
- **Key Outputs:**
  - Community display name
  - HOA fees and website
  - Amenities list (pools, trails, fitness, etc.)
  - Gated status
- **Integration Priority:** 🟡 Important
- **Complexity:** Low
- **Notes:** Pattern-based subdivision matching with exclusion support.

---

### 7. GIS Data (Cached)
- **File:** `core/loudoun_gis_data.py`
- **Size:** 15.8 KB (494 lines)
- **Status:** ✅ Functional
- **Primary Function:** Cached loading of GIS shapefiles for roads, AIOD zones, and power lines
- **Data Dependencies:**
  - `data/loudoun/gis/roads/*.shp`
  - `data/loudoun/gis/aiod/*.shp`
  - `data/loudoun/utilities/Major_Power_Lines.geojson`
- **Key Outputs:**
  - Road GeoDataFrames (all roads, highways, collectors)
  - AIOD zones GeoDataFrame
  - Power lines list
- **Integration Priority:** 🟡 Important
- **Complexity:** Medium
- **Notes:** Uses Streamlit @cache_resource for performance. Requires geopandas.

---

### 8. Places Analysis
- **File:** `core/loudoun_places_analysis.py`
- **Size:** 21.9 KB (709 lines)
- **Status:** ✅ Functional
- **Primary Function:** Neighborhood amenity analysis using Google Places API (New)
- **Data Dependencies:**
  - Live API: Google Places API
  - Cache: `data/loudoun/cache/places/*.json`
- **Key Outputs:**
  - Nearby dining, grocery, shopping, pharmacy
  - Convenience score (0-10)
  - Walkability count
  - Neighborhood narrative
- **Integration Priority:** 🟡 Important
- **Complexity:** Medium
- **Notes:** Has 7-day file-based caching for cost optimization. Detects 24-hour pharmacies.

---

### 9. Sales Data
- **File:** `core/loudoun_sales_data.py`
- **Size:** 19.3 KB (526 lines)
- **Status:** ✅ Functional
- **Primary Function:** Property sales history lookup from Commissioner of Revenue records (2020-2025)
- **Data Dependencies:**
  - `data/loudoun/sales/combined_sales.parquet`
- **Key Outputs:**
  - Sales history by PARID
  - Arms-length transaction filtering
  - Sale price, date, verification code
  - Ownership transfer details
- **Integration Priority:** 🔴 Critical
- **Complexity:** Medium
- **Notes:** Uses Parquet for 105x faster loading vs Excel. ~47K arms-length records.

---

### 10. Traffic Volume
- **File:** `core/loudoun_traffic_volume.py`
- **Size:** 13.0 KB (391 lines)
- **Status:** ✅ Functional
- **Primary Function:** VDOT Average Daily Traffic (ADT) analysis for highways and collectors
- **Data Dependencies:**
  - `data/loudoun/gis/traffic/vdot_traffic_volume.geojson`
  - `data/loudoun/config/vdot_road_mapping.json`
- **Key Outputs:**
  - ADT count for nearby roads
  - VDOT route identification
  - Formatted traffic display
- **Integration Priority:** 🟢 Nice-to-have
- **Complexity:** Medium
- **Notes:** Supports both mapping-based and coordinate-based lookup.

---

### 11. Utilities Analysis
- **File:** `core/loudoun_utilities_analysis.py`
- **Size:** 17.1 KB (490 lines)
- **Status:** ✅ Functional
- **Primary Function:** Power line proximity analysis with voltage-based visual impact scoring
- **Data Dependencies:**
  - `data/loudoun/utilities/Major_Power_Lines.geojson`
- **Key Outputs:**
  - Nearest power line (built/approved)
  - Distance at various radii
  - Visual impact score (1-5)
  - Voltage-based analysis (138kV, 230kV, 500kV)
- **Integration Priority:** 🟢 Nice-to-have
- **Complexity:** Medium
- **Notes:** Point-to-line segment distance calculation. 80 power line segments.

---

### 12. Narrative Generator
- **File:** `core/loudoun_narrative_generator.py`
- **Size:** 35.8 KB (945 lines)
- **Status:** ✅ Functional
- **Primary Function:** AI-powered property narrative generation using Claude API
- **Data Dependencies:**
  - Requires: All other analyzers' outputs
  - API: Anthropic Claude API
  - Cache: `cache/narratives/*.json`
- **Key Outputs:**
  - 6-section narrative (what_stands_out, schools_reality, daily_reality, worth_knowing, investment_lens, bottom_line)
  - Token usage tracking
  - 24-hour cache TTL
- **Integration Priority:** 🟡 Important
- **Complexity:** High
- **Notes:** Orchestration module that compiles data from all other analyzers. Requires ANTHROPIC_API_KEY.

---

## Integration Roadmap

### Phase 1: Core Features (Must-Have)
1. **loudoun_metro_analysis** - Metro proximity (standalone, no deps)
2. **loudoun_zoning_analysis** - Zoning & development probability
3. **loudoun_school_percentiles** - School rankings
4. **loudoun_sales_data** - Sales history
5. **loudoun_valuation_context** - Valuation helper

### Phase 2: Important Features
6. **loudoun_school_performance** - School charts
7. **loudoun_community_lookup** - HOA/amenities
8. **loudoun_gis_data** - Cached GIS loading
9. **loudoun_places_analysis** - Neighborhood amenities
10. **loudoun_narrative_generator** - AI narratives

### Phase 3: Enhancement Features
11. **loudoun_traffic_volume** - VDOT ADT data
12. **loudoun_utilities_analysis** - Power line proximity

---

## Dependencies Map

```
loudoun_narrative_generator
├── loudoun_metro_analysis
├── loudoun_school_percentiles
├── loudoun_places_analysis
├── loudoun_valuation_context
└── location_quality_analyzer (not loudoun-specific)

loudoun_utilities_analysis
└── loudoun_gis_data (for cached power lines)

loudoun_school_performance
└── No cross-module deps (standalone)

loudoun_zoning_analysis
└── No cross-module deps (standalone, uses live APIs)

loudoun_sales_data
└── No cross-module deps (standalone)

loudoun_community_lookup
└── No cross-module deps (standalone)

loudoun_traffic_volume
└── No cross-module deps (standalone)
```

---

## Data Requirements

### Local Data Files (data/loudoun/)

| Category | Files | Used By |
|----------|-------|---------|
| **Schools** | `school_performance_trends.csv`, `school_metadata.csv`, `loudoun_school_coordinates.csv` | school_percentiles, school_performance |
| **Sales** | `sales/combined_sales.parquet` | sales_data |
| **Config** | `communities.json`, `placetype_translations.json`, `zoning_translations.json`, `vdot_road_mapping.json` | community_lookup, zoning_analysis, traffic_volume |
| **GIS** | `roads/*.shp`, `aiod/*.shp`, `traffic/vdot_traffic_volume.geojson` | gis_data, traffic_volume |
| **Utilities** | `utilities/Major_Power_Lines.geojson` | utilities_analysis, gis_data |
| **Permits** | `building_permits/*.csv` | zoning_analysis |

### External APIs

| API | Used By | Cost |
|-----|---------|------|
| Loudoun County LOGIS GIS | zoning_analysis | Free |
| Google Places API (New) | places_analysis | Pay-per-use (cached) |
| Anthropic Claude API | narrative_generator | Pay-per-use (cached) |

---

## Estimated LOC for Comprehensive loudoun_report.py

Based on the existing `reports/loudoun_report.py` POC structure and the full module inventory:

- **Current POC:** ~450 lines
- **Full integration estimate:** 800-1200 lines
- **Key additions needed:**
  - Full zoning section with development probability
  - Complete school section with charts
  - Neighborhood amenities section
  - Power line/utilities section
  - Traffic volume display
  - AI narrative integration
  - Sales history display

---

## Quick Wins

1. **Metro Analysis** - Already working, no external deps
2. **Valuation Context** - Simple helper, no deps
3. **Community Lookup** - Low complexity, just needs JSON config
4. **Sales Data** - Works with Parquet file, fast loading

## Potential Blockers

1. **Google Places API** - Requires API key and has costs
2. **Claude API** - Requires API key for narrative generation
3. **GeoJSON/Shapefile loading** - Requires geopandas for full GIS features
