# Fairfax County Data Inventory

*Last Updated: 2026-01-26*
*Total Datasets: 22*
*Verification Status: 100% Complete*
*Total Records: 1,417,763 across all datasets*
*Total Storage: ~620 MB (raw + processed)*

## Executive Summary

### Current State
- **18 spatial datasets** verified and ready for integration
- **4 sales data files** with 872,537 transaction records (pre-2010 to 2025)
- **369,010 parcels** with boundary geometry
- **Strong school data** (5 layers including attendance boundaries)
- **Complete flood risk coverage** (FEMA zones, dam break, easements)
- **Multi-utility infrastructure** (electric, gas, telephone lines)

### Key Differentiators vs Loudoun
| Advantage | Fairfax | Loudoun |
|-----------|---------|---------|
| Natural Gas Lines | ✅ 65 segments | ❌ None |
| Telephone Lines | ✅ 4 segments | ❌ None |
| Parcel Count | 369,010 | Not available |
| Sales Records | 872,537 | 78,300 |
| School Regions | ✅ 6 regions | ❌ None |
| Metro Stations | 32 stations | 4 stations |
| Road Segments | 148,594 | 29,217 |
| Zoning Overlay | ✅ 73 districts | ❌ None |

### Critical Gaps (vs Loudoun)
1. **Building Permits** - Loudoun has 1,259 permits; Fairfax has none
2. ~~**Cell Towers**~~ - ✅ RESOLVED: Fairfax now has 148 FCC-registered towers
3. **Healthcare Facilities** - Loudoun has 29 facilities; Fairfax has none
4. **Airport Impact Districts** - Loudoun has AIOD; Fairfax has none
5. **Crime Data** - Neither county has this (high-value opportunity)

### Recommended Next Steps
1. **Acquire Building Permits** - Critical for development pressure analysis
2. **Acquire Crime Data** - Major competitive differentiator
3. **Build Parcel Lookup Module** - Foundation for all other features
4. **Build School Assignment Module** - High user demand feature

---

## Extraction Summary

| Category | ZIP Files | Extracted | Status |
|----------|-----------|-----------|--------|
| Parcels | 1 | ✅ | Complete |
| Zoning | 2 | ✅ | Complete |
| Schools | 5 | ✅ | Complete |
| Subdivisions | 2 | ✅ | Complete |
| Flood | 3 | ✅ | Complete |
| Electrical | 1 | ✅ | Complete |
| Transit | 2 | ✅ | Complete |
| **Total** | **16** | **16** | **100%** |

---

## Dataset Catalog

### CORE PROPERTY DATA

#### Tax Parcels
- **Location:** `data/fairfax/gis/parcels/raw/Parcels.shp`
- **Source:** Parcels.zip (83 MB)
- **Format:** Shapefile
- **Records:** 369,010
- **CRS:** EPSG:3857 (Web Mercator)
- **Key Fields:** PIN, PARCEL_KEY, PARCEL_TYP (ORDINARY/CONDO)
- **Status:** ✅ Verified
- **Quality Notes:** 135 invalid geometries (0.04%), fixable with buffer(0). Winding order warning auto-corrected.
- **Platform Features:** Property lookup, boundary display, spatial joins
- **Integration Priority:** HIGH
- **Implementation:** EASY
- **Differentiation:** ★★ (parity with most platforms)
- **Example Use:** "Look up any Fairfax County property by address or PIN"

#### Sales Records
- **Location:** `data/fairfax/sales/processed/sales_*.parquet` (4 files)
- **Format:** Parquet (compressed)
- **Records:** 872,537 total
  - sales_pre2010.parquet: 634,082 records (8.15 MB)
  - sales_2010_2014.parquet: 68,045 records (1.07 MB)
  - sales_2015_2019.parquet: 79,899 records (1.22 MB)
  - sales_2020_2025.parquet: 90,511 records (1.38 MB)
- **Key Fields:** PARID, SALE_DATE, SALE_PRICE, SALE_TYPE, DEED_BOOK, DEED_PAGE, SALE_YEAR
- **Status:** ✅ Verified
- **Quality Notes:** PARID joins to parcels PIN field
- **Platform Features:** Price history, comparable sales, market trends
- **Integration Priority:** HIGH
- **Implementation:** EASY
- **Differentiation:** ★★ (parity - all competitors have this)
- **Example Use:** "View complete sales history for any property since 2000"

---

### ZONING & PLANNING

#### Base Zoning Districts
- **Location:** `data/fairfax/gis/zoning/raw/Zoning.shp`
- **Source:** Zoning.zip (7.6 MB)
- **Format:** Shapefile
- **Records:** 6,431
- **CRS:** EPSG:3857 (Web Mercator)
- **Key Fields:** ZONECODE, ZONETYPE, PROFFER, PUBLIC_LAN, JURISDICTI, CLUSTER_
- **Status:** ✅ Verified
- **Quality Notes:** Direct CRS match with parcels - no transformation needed
- **Platform Features:** Zoning lookup, use restrictions, development potential
- **Integration Priority:** HIGH
- **Implementation:** EASY
- **Differentiation:** ★★ (standard feature)
- **Example Use:** "Instantly see zoning code and allowed uses for any parcel"

#### Zoning Overlay Districts
- **Location:** `data/fairfax/gis/zoning/raw/Zoning_Overlay_Districts.shp`
- **Source:** Zoning_Overlay_Districts (1).zip (696 KB)
- **Format:** Shapefile
- **Records:** 73
- **CRS:** EPSG:3857 (Web Mercator)
- **Key Fields:** ODTYPE, DECIBEL
- **Status:** ✅ Verified
- **Quality Notes:** Includes noise impact overlays (airport)
- **Platform Features:** Additional restrictions, noise zones
- **Integration Priority:** MEDIUM
- **Implementation:** EASY
- **Differentiation:** ★★★ (Loudoun lacks this)
- **Example Use:** "Check if property is in airport noise impact zone"

---

### EDUCATION

#### Elementary School Attendance Areas
- **Location:** `data/fairfax/gis/schools/raw/Elementary_School_Attendance_Areas.shp`
- **Source:** Elementary_School_Attendance_Areas (1).zip (1.1 MB)
- **Format:** Shapefile
- **Records:** 142
- **CRS:** EPSG:2283 (VA State Plane North, feet)
- **Key Fields:** SCHOOL_NAM, SCHOOL_TYP, GRADES, STREET_NUM, STREET_NAM, CITY, ZIP, PHONE, HOME_URL, REGION
- **Status:** ✅ Verified
- **Quality Notes:** 2 invalid geometries (fixable)
- **Platform Features:** School assignment lookup
- **Integration Priority:** HIGH
- **Implementation:** MEDIUM (requires CRS transform)
- **Differentiation:** ★★ (standard feature)
- **Example Use:** "Which elementary school serves this address?"

#### Middle School Attendance Areas
- **Location:** `data/fairfax/gis/schools/raw/Middle_School_Attendance_Areas.shp`
- **Source:** Middle_School_Attendance_Areas (1).zip (555 KB)
- **Format:** Shapefile
- **Records:** 26
- **CRS:** EPSG:2283
- **Key Fields:** Same as Elementary
- **Status:** ✅ Verified
- **Integration Priority:** HIGH
- **Implementation:** MEDIUM

#### High School Attendance Areas
- **Location:** `data/fairfax/gis/schools/raw/High_School_Attendance_Areas.shp`
- **Source:** High_School_Attendance_Areas (1).zip (550 KB)
- **Format:** Shapefile
- **Records:** 24
- **CRS:** EPSG:2283
- **Key Fields:** Same as Elementary
- **Status:** ✅ Verified
- **Integration Priority:** HIGH
- **Implementation:** MEDIUM

#### School Facilities
- **Location:** `data/fairfax/gis/schools/raw/School_Facilities.shp`
- **Source:** School_Facilities (1).zip (23 KB)
- **Format:** Shapefile
- **Records:** 269 (Point geometry)
- **CRS:** EPSG:2283
- **Key Fields:** SCHOOL_NAM, SCHOOL_TYP, TYPE_DESC
- **Status:** ✅ Verified
- **Quality Notes:** Includes all school types (elementary, middle, high, special)
- **Platform Features:** School locations, distance calculations
- **Integration Priority:** MEDIUM
- **Implementation:** EASY

#### School Regions
- **Location:** `data/fairfax/gis/schools/raw/School_Regions.shp`
- **Source:** School_Regions (1).zip (396 KB)
- **Format:** Shapefile
- **Records:** 6
- **CRS:** EPSG:2283
- **Key Fields:** REGION
- **Status:** ✅ Verified
- **Quality Notes:** Administrative regions (unique to Fairfax)
- **Platform Features:** Regional context
- **Integration Priority:** LOW
- **Differentiation:** ★★★ (Loudoun lacks this)

---

### INFRASTRUCTURE

#### Roadway Centerlines
- **Location:** `data/fairfax/gis/roads/raw/Roadway_Centerlines.shp`
- **Format:** Shapefile (pre-extracted)
- **Records:** 148,594
- **CRS:** EPSG:2283 (VA State Plane North, feet)
- **Key Fields:** FULLNAME, RW_PREFIX, RW_NAME, RW_TYPE_US, L_JURISDIC, R_JURISDIC, TRANS_ID
- **Status:** ✅ Verified
- **Quality Notes:** Very detailed network, 5x more segments than Loudoun
- **Platform Features:** Address geocoding support, routing context
- **Integration Priority:** LOW (geocoding usually via external API)
- **Implementation:** HARD
- **Differentiation:** ★★ (standard)

#### Major Utility Lines
- **Location:** `data/fairfax/gis/electrical/raw/Major_Utility_Lines.shp`
- **Source:** Major_Utility_Lines (1).zip (36 KB)
- **Format:** Shapefile
- **Records:** 125 (LineString)
- **CRS:** EPSG:2283
- **Key Fields:** NAME, TYPE (electric/gas/telephone)
- **Breakdown:**
  - Electric: 56 segments (Virginia Power)
  - Gas: 65 segments
  - Telephone: 4 segments
- **Status:** ✅ Verified
- **Quality Notes:** Multi-utility coverage (unique advantage)
- **Platform Features:** Utility proximity, infrastructure assessment
- **Integration Priority:** LOW
- **Implementation:** MEDIUM
- **Differentiation:** ★★★ (Loudoun only has electric; no gas/telephone)
- **Example Use:** "Show all properties within 500 feet of gas transmission lines"

#### Metrorail Stations
- **Location:** `data/fairfax/transit/metro/raw/Metrorail_Stations.shp`
- **Source:** Metrorail_Stations (2).zip (3.5 KB)
- **Format:** Shapefile
- **Records:** 32 (Point geometry)
- **CRS:** EPSG:2283
- **Key Fields:** NAME, STATION, NODE, YEAR_
- **Status:** ✅ Verified
- **Quality Notes:** Includes POTOMAC YARD (2023), all 4 Loudoun stations
- **Platform Features:** Transit accessibility, TOD scoring
- **Integration Priority:** MEDIUM
- **Implementation:** EASY
- **Differentiation:** ★★ (similar coverage)
- **Example Use:** "Calculate walk time to nearest Metro station"

#### Metrorail Tracks
- **Location:** `data/fairfax/transit/metro/raw/Metrorail.shp`
- **Source:** Metrorail (1).zip (20 KB)
- **Format:** Shapefile
- **Records:** 44 (LineString/MultiLineString)
- **CRS:** EPSG:2283
- **Status:** ✅ Verified
- **Quality Notes:** Track alignment, useful for visualization
- **Integration Priority:** LOW

---

### ENVIRONMENTAL

#### FEMA Flood Hazard Areas
- **Location:** `data/fairfax/gis/flood/raw/FEMA_Flood_Hazard_Areas.geojson`
- **Format:** GeoJSON (16 MB)
- **Records:** 299 polygons
- **CRS:** EPSG:3857
- **Key Fields:** FLD_ZONE, SFHA_TF, FLOODWAY, STATIC_BFE, ZONE_SUBTY
- **Zone Distribution:**
  - A: 114 (high risk, no BFE)
  - AE: 58 (high risk, with BFE)
  - AH: 2 (shallow flooding)
  - X: 123 (moderate/low risk)
- **Status:** ✅ Verified
- **Quality Notes:** Complete county coverage, 1.39% of parcels in SFHA
- **Platform Features:** Flood risk assessment, insurance requirements
- **Integration Priority:** HIGH
- **Implementation:** EASY (same CRS as parcels)
- **Differentiation:** ★★ (standard feature)
- **Example Use:** "Instantly check if property is in a flood zone"

#### FEMA Change Areas (S_CSLF)
- **Location:** `data/fairfax/gis/flood/raw/ArcShape/S_CSLF_Ar.shp`
- **Source:** FRD_51059C_Shapefiles_20210716.zip (24 MB)
- **Format:** Shapefile
- **Records:** 3,313
- **CRS:** EPSG:4269 (NAD83)
- **Status:** ✅ Verified
- **Quality Notes:** Shows flood zone CHANGES, not current zones. Use FEMA_Flood_Hazard_Areas for current data.
- **Integration Priority:** LOW

#### Dam Break Inundation Zones
- **Location:** `data/fairfax/gis/flood/raw/Non_DPWES_Dam_Break_Inundation_Zones.shp`
- **Source:** Non_DPWES_Dam_Break_Inundation_Zones_-7261305456851086412.zip (2.6 MB)
- **Format:** Shapefile
- **Records:** 17 (representing 16 dams)
- **CRS:** EPSG:2283
- **Status:** ✅ Verified
- **Quality Notes:** Shows inundation areas if specific dams fail
- **Platform Features:** Additional flood risk context
- **Integration Priority:** LOW
- **Differentiation:** ★★★ (unique dataset)
- **Example Use:** "Show properties at risk if Burke Lake Dam fails"

#### Recorded Floodplain Easements
- **Location:** `data/fairfax/gis/flood/raw/Recorded_Floodplain_Easements.shp`
- **Source:** Recorded_Floodplain_Easements (1).zip (3.7 MB)
- **Format:** Shapefile
- **Records:** 897
- **CRS:** EPSG:3857
- **Status:** ✅ Verified
- **Quality Notes:** Legal easements with recorded deed references
- **Integration Priority:** LOW
- **Differentiation:** ★★★ (unique dataset)

---

### COMMUNITY

#### Subdivisions
- **Location:** `data/fairfax/gis/subdivisions/raw/Subdivisions.shp`
- **Source:** Subdivisions (2).zip (12 MB)
- **Format:** Shapefile
- **Records:** 11,430
- **CRS:** EPSG:3857
- **Key Fields:** SUB_NAME, SUB_SECTION, SUB_PHASE, SUB_BLOCK, SUB_ID, DEED_BOOK, DEED_PAGE, RECORD_DAT
- **Status:** ✅ Verified
- **Quality Notes:** 4,927 unique subdivision names, 96.6% parcel coverage
- **Platform Features:** Community/neighborhood identification
- **Integration Priority:** MEDIUM
- **Implementation:** EASY (same CRS as parcels)
- **Differentiation:** ★★ (both counties have)
- **Example Use:** "Identify subdivision name and recording info for any parcel"

#### Subdivision Blocks
- **Location:** `data/fairfax/gis/subdivisions/raw/Subdivision_Blocks.shp`
- **Source:** Subdivision_Blocks (1).zip (5.4 MB)
- **Format:** Shapefile
- **Records:** 4,494
- **CRS:** EPSG:3857
- **Status:** ✅ Verified
- **Quality Notes:** Grid reference system, NOT subdivision boundaries. Use Subdivisions.shp instead.
- **Integration Priority:** LOW

---

## Data Gaps Analysis

### Critical Gaps (HIGH Priority)

| Dataset | Why Critical | Loudoun Has? | Difficulty |
|---------|--------------|--------------|------------|
| **Crime Data** | Safety scoring, major differentiator | ❌ No | HARD |
| **Building Permits** | Development pressure, new construction | ✅ Yes (1,259) | MEDIUM |
| **Property Valuations** | Assessed values, tax estimates | Unknown | MEDIUM |

### Important Gaps (MEDIUM Priority)

| Dataset | Why Important | Loudoun Has? | Difficulty |
|---------|---------------|--------------|------------|
| **Cell Towers** | Infrastructure coverage, 5G | ✅ Yes (110) | EASY |
| **Healthcare Facilities** | Amenity proximity | ✅ Yes (29) | EASY |
| **Airport Impact Districts** | Noise overlay | ✅ Yes (9) | MEDIUM |
| **Comprehensive Plan** | Future land use | Unknown | MEDIUM |

### Nice-to-Have Gaps (LOW Priority)

| Dataset | Why Useful | Loudoun Has? | Difficulty |
|---------|------------|--------------|------------|
| **Bike/Pedestrian Network** | Walkability scores | Unknown | MEDIUM |
| **Parks/Recreation** | Amenity mapping | Unknown | EASY |
| **Historic Districts** | Development constraints | Unknown | EASY |

---

## County Comparison Matrix

| Dataset | Athens | Loudoun | Fairfax | Winner |
|---------|--------|---------|---------|--------|
| Parcels | N/A | ❌ | ✅ 369K | **Fairfax** |
| Sales Data | N/A | ✅ 78K | ✅ 872K | **Fairfax** |
| Zoning | N/A | ✅ 1,263 | ✅ 6,431 | **Fairfax** |
| Zoning Overlays | N/A | ❌ | ✅ 73 | **Fairfax** |
| School Boundaries | N/A | ✅ 93 | ✅ 192 | **Fairfax** |
| School Facilities | N/A | ✅ 103 | ✅ 269 | **Fairfax** |
| Subdivisions | N/A | ✅ 4,753 | ✅ 11,430 | **Fairfax** |
| Road Centerlines | N/A | ✅ 29K | ✅ 148K | **Fairfax** |
| FEMA Flood | N/A | ⚠️ (ZIP) | ✅ 299 | **Fairfax** |
| Metro Stations | N/A | ✅ 4 | ✅ 32 | **Fairfax** |
| Power Lines | N/A | ✅ 80 | ✅ 56 | Loudoun |
| Gas Lines | N/A | ❌ | ✅ 65 | **Fairfax** |
| Telephone Lines | N/A | ❌ | ✅ 4 | **Fairfax** |
| Building Permits | N/A | ✅ 1,259 | ❌ | Loudoun |
| Cell Towers | N/A | ✅ 110 | ❌ | Loudoun |
| Healthcare | N/A | ✅ 29 | ❌ | Loudoun |
| Crime | N/A | ❌ | ❌ | Neither |

*Note: Athens data directory is empty/not available*

---

## Unique Fairfax Advantages

1. **Multi-Utility Infrastructure** - Electric + Gas + Telephone lines in single dataset (Loudoun only has electric)
2. **Massive Sales History** - 872K records vs Loudoun's 78K (11x more data)
3. **Complete Parcel Coverage** - 369K parcels with geometry (Loudoun lacks this)
4. **School Regions** - Administrative region boundaries (unique)
5. **Dam Break Inundation** - Risk modeling for 16 dams (unique)
6. **Floodplain Easements** - Recorded legal easements (unique)
7. **Zoning Overlays** - 73 overlay districts including airport noise zones

---

## Integration Roadmap

### Phase 1: Core Features (Ready Now)
| Module | Priority | Complexity | Differentiation |
|--------|----------|------------|-----------------|
| Parcels + Sales | HIGH | EASY | ★★ |
| School Assignment | HIGH | MEDIUM | ★★ |
| Zoning Lookup | HIGH | EASY | ★★ |
| Flood Risk | HIGH | EASY | ★★ |
| Subdivision Lookup | MEDIUM | EASY | ★★ |
| Metro/Transit Proximity | MEDIUM | EASY | ★★ |

### Phase 2: Differentiation (After Data Acquisition)
| Module | Priority | Blocked On | Differentiation |
|--------|----------|------------|-----------------|
| Crime/Safety Score | HIGH | Crime data | ★★★ |
| Development Pressure | HIGH | Building permits | ★★★ |
| Healthcare Proximity | MEDIUM | Healthcare data | ★★ |

### Phase 3: Enhancement
| Module | Priority | Complexity | Differentiation |
|--------|----------|------------|-----------------|
| Utility Proximity | LOW | MEDIUM | ★★★ |
| Dam Break Risk | LOW | EASY | ★★★ |
| Zoning Overlay Analysis | LOW | EASY | ★★★ |

---

## Technical Notes

### CRS Standards
| CRS | Datasets | Notes |
|-----|----------|-------|
| EPSG:3857 | Parcels, Zoning, Subdivisions, FEMA Flood, Easements | Web Mercator - primary for parcels |
| EPSG:2283 | Schools, Roads, Utilities, Transit, Dam Break | VA State Plane North (feet) |
| EPSG:4269 | FEMA Change Areas | NAD83 - rarely used |
| EPSG:4326 | Target output | WGS84 for web display |

### Join Keys
| Dataset | Key Field | Format | Example |
|---------|-----------|--------|---------|
| Parcels | PIN | XXXX XX  XXXX | 0102 14  0231 |
| Sales | PARID | XXXX XX  XXXX | 0102 14  0231 |
| Zoning | ZONECODE | Alphanumeric | R-1, C-5, PDH-2 |

**PIN-PARID Compatibility:** Direct match - 91.5% of sales join successfully to parcels

### File Size Management
| Strategy | Implementation |
|----------|----------------|
| Large files | ZIP committed, raw/ gitignored |
| Parquet | 33x compression on sales data |
| GitHub limit | 100 MB per file |
| Total raw | ~620 MB (gitignored) |
| Total committed | ~140 MB (ZIPs + processed) |

### Spatial Join Strategy
| Join Type | CRS Handling |
|-----------|--------------|
| Parcels ↔ Zoning | Direct (both 3857) |
| Parcels ↔ Schools | Transform schools 2283→3857 |
| Parcels ↔ Flood | Direct (both 3857) |
| Parcels ↔ Roads | Transform roads 2283→3857 |
| Parcels ↔ Utilities | Transform utilities 2283→3857 |
| Parcels ↔ Subdivisions | Direct (both 3857) |

---

## Summary Statistics

```
FAIRFAX COUNTY DATA SUMMARY
═══════════════════════════════════════════════════════════════
Total Datasets:           22
Verified Complete:        22 (100%)
Needs Verification:       0 (0%)
Missing (Critical):       3 (Crime, Permits, Valuations)
Missing (Medium):         4 (Cell Towers, Healthcare, AIOD, Comp Plan)
Missing (Low):            3 (Bike/Ped, Parks, Historic)
───────────────────────────────────────────────────────────────
Total Records:            1,417,763 across all datasets
  - Spatial Records:      545,226
  - Sales Records:        872,537
Total File Size:          ~620 MB (raw + processed)
ZIP Files:                16
Extracted:                16 (100%)
───────────────────────────────────────────────────────────────
CRS Distribution:
  EPSG:3857:              7 datasets
  EPSG:2283:              10 datasets
  EPSG:4269:              1 dataset
───────────────────────────────────────────────────────────────
Format Distribution:
  Shapefile:              17
  Parquet:                4
  GeoJSON:                1
═══════════════════════════════════════════════════════════════
```

---

## Actionable Recommendations

### Immediate Priorities (This Week)

1. **Acquire Building Permits Data**
   - Reason: Loudoun has 1,259 permits; critical for development analysis
   - Expected Impact: Enable "new construction nearby" and development pressure features
   - Source: Fairfax County permits portal

2. **Build Parcel Lookup Module**
   - Reason: Foundation for all other features
   - Expected Impact: Enable property search, boundary display, all spatial joins
   - Data Ready: ✅ Yes

3. **Build School Assignment Module**
   - Reason: High user demand, data complete
   - Expected Impact: "Which schools serve this address" feature
   - Data Ready: ✅ Yes

### Module Creation Readiness

**Ready to Build Now:**
- Parcel lookup (parcels + sales)
- Zoning lookup (zoning + overlays)
- School assignment (all 5 school layers)
- Flood risk assessment (FEMA + dam break + easements)
- Subdivision lookup (subdivisions)
- Transit proximity (Metro stations)

**Blocked on Data:**
- Crime/safety scoring (no crime data)
- Development pressure (no building permits)
- Healthcare proximity (no healthcare data)

**Optional Enhancements:**
- Utility proximity (data ready, lower priority)
- Dam break risk (unique but niche)
- Zoning overlay analysis (airport noise, etc.)

### Data Acquisition Priorities

| Priority | Dataset | Source | Difficulty | Impact |
|----------|---------|--------|------------|--------|
| 1 | Building Permits | Fairfax County Portal | MEDIUM | HIGH |
| 2 | Crime Data | Police/FBI UCR | HARD | VERY HIGH |
| 3 | Property Valuations | Tax Records | MEDIUM | HIGH |
| 4 | Cell Towers | FCC Database | EASY | MEDIUM |
| 5 | Healthcare Facilities | CMS/State Data | EASY | MEDIUM |

---

*Document generated: 2026-01-26*
*Next review: After new data acquisition*
