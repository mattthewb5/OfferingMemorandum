# NewCo Data Census: Commercial vs. Residential Coverage

Generated: 2026-03-01

## Summary

| Metric | Count |
|--------|-------|
| Total sections across both counties | 26 (14 Fairfax + 12 Loudoun) |
| Sections covering BOTH property types | 8 |
| Sections RESIDENTIAL ONLY | 4 |
| Sections COMMERCIAL ONLY | 0 |
| Sections AREA-LEVEL (property-type agnostic) | 14 |

**Key Finding:** No section is commercial-only. The system was built with a residential focus, but many modules already ingest commercial data without filtering it out. Zoning, permits, comprehensive plan, and valuation modules all handle commercial properties. The biggest gaps are in sales data (no property type column to distinguish commercial transactions) and the overall UX (report framing assumes residential buyers).

---

## Section-by-Section Census

### 1. Schools Analysis

- **Fairfax module:** `core/fairfax_schools_analysis.py` (FairfaxSchoolsAnalysis), `core/fairfax_school_performance_analysis.py`
- **Loudoun module:** `core/loudoun_school_performance.py`, school zone GeoJSONs in report
- **Data sources:**
  - Fairfax: `data/fairfax/schools/processed/{elementary,middle,high}_zones.parquet`, `facilities.parquet`, `performance/processed/performance_summary.parquet`, `performance_trends.parquet`
  - Loudoun: `data/loudoun/schools/{elementary,middle,high}_zones.geojson`, `school_performance_trends_with_state_avg.csv`, `loudoun_school_coordinates.csv`
- **Coverage:** **Residential Only**
- **Evidence:** School attendance zone boundaries and SOL performance data are exclusively relevant to residential properties (families choosing homes by school district). Columns: `school_name`, `school_level`, `reading_pass_rate`, `math_pass_rate`, `geometry`
- **Commercial gaps:** Schools are irrelevant for commercial OM. However, school quality data could be included as a "workforce quality" indicator for commercial office tenants recruiting employees with families.
- **OM relevance:** Not applicable for standard commercial OM. Could appear in mixed-use or multifamily OM as an amenity.

### 2. Crime & Safety

- **Fairfax module:** `core/fairfax_crime_analysis.py` (FairfaxCrimeAnalysis)
- **Loudoun module:** Not present (Loudoun lacks a public crime API)
- **Data sources:**
  - `data/fairfax/crime/processed/incidents.parquet` — geocoded incidents with `latitude`, `longitude`, `category` (VIOLENT/PROPERTY/OTHER), `date`, `address`
  - `data/fairfax/crime/processed/metadata.json`
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Crime data is geographic, not property-type specific. A 0-100 safety score based on violent + property crimes within 0.5–2.0 mile radius applies equally to residential and commercial properties.
- **Commercial gaps:** Commercial OM might want crime rates specifically for retail theft, vandalism, or auto break-ins. Current categories (VIOLENT/PROPERTY/OTHER) partially support this but don't distinguish commercial-relevant subcategories.
- **OM relevance:** Relevant for all property types. Office tenants care about employee safety; retail tenants care about shoplifting risk; industrial tenants care about property crime.

### 3. Emergency Services (Fairfax Only)

- **Fairfax module:** `core/fairfax_emergency_services_analysis.py` (FairfaxEmergencyServicesAnalysis)
- **Loudoun module:** Not present as standalone section
- **Data sources:**
  - `data/fairfax/emergency_services/processed/fire_stations.parquet` (47 stations)
  - `data/fairfax/emergency_services/processed/police_stations.parquet` (23 stations)
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Fire station proximity determines ISO Fire Protection Classification (distance-based, not property-type-based). Properties >5 miles from fire station = ISO Class 10 (worst). Columns: `station_name`, `address`, `latitude`, `longitude`, `station_type`
- **Commercial gaps:** None significant. ISO classification is already used in commercial insurance underwriting.
- **OM relevance:** Directly relevant for commercial OM — ISO rating affects insurance costs for all property types.

### 4. Location Quality (Unified Section)

- **Fairfax module:** `core/fairfax_traffic_analysis.py`, `core/fairfax_flood_analysis.py`, `core/fairfax_parks_analysis.py`, `core/fairfax_transit_analysis.py`, `core/fairfax_utilities_analysis.py`
- **Loudoun module:** `core/location_quality_analyzer.py`, `core/loudoun_traffic_volume.py`, `core/loudoun_metro_analysis.py`, `core/loudoun_utilities_analysis.py`, FEMA API
- **Data sources:**
  - Fairfax traffic: `data/fairfax/traffic/processed/traffic_volumes.parquet` (148,594 road segments with ADT)
  - Fairfax flood: `data/fairfax/flood/processed/fema_zones.parquet`, `dam_inundation.parquet`, `easements.parquet`
  - Fairfax parks: `data/fairfax/parks/processed/parks.parquet`, `trails.parquet`, `recreation.parquet`
  - Fairfax transit: `data/fairfax/transit/processed/metro_stations.parquet` (32 stations), `metro_lines.parquet`, `bus_routes.parquet`
  - Fairfax utilities: `data/fairfax/utilities/processed/utility_lines.parquet`
  - Loudoun traffic: `data/loudoun/gis/traffic/vdot_traffic_volume.geojson`
  - Loudoun config: `data/loudoun/config/road_context.json`, `parks.json`
  - Loudoun utilities: `data/loudoun/utilities/Major_Power_Lines.geojson`
  - Hardcoded airport coordinates for noise disclosure zones
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Traffic ADT, flood zones, transit access, power line proximity, and airport noise are all geographic factors that apply to any property type. Key columns: `road_name`, `adt`, `zone_code` (FEMA: A, AE, AO, X, etc.), `station_name`, `distance_miles`
- **Commercial gaps:** Traffic ADT data is **highly valuable** for retail/restaurant commercial — it's already there. Missing: walkability/pedestrian traffic counts, parking ratio analysis, loading dock access, intersection signalization data.
- **OM relevance:** Critical for commercial OM. Traffic counts drive retail site selection. Flood zones affect insurance. Transit access affects office tenant recruitment. Airport noise affects all property types.

### 5. Cell Tower Coverage

- **Fairfax module:** `core/fairfax_cell_towers_analysis.py` (FairfaxCellTowersAnalysis)
- **Loudoun module:** Report helper function (inline)
- **Data sources:**
  - Fairfax: `data/fairfax/cell_towers/processed/towers.parquet` (FCC Antenna Structure Registration)
  - Loudoun: `data/loudoun/Cell-Towers/loudoun_towers_enhanced.csv`, `fcc_virginia_towers_active.csv`
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Cell tower proximity is geographic. Columns: `latitude`, `longitude`, `height_feet`, `structure_type`, `carrier`
- **Commercial gaps:** Commercial tenants care about cellular coverage quality (not just tower proximity). Missing: carrier-specific coverage maps, indoor signal strength estimates, fiber/broadband availability data.
- **OM relevance:** Relevant for office and data center OM. Fiber connectivity data would be more valuable than cell towers for commercial.

### 6. Neighborhood Amenities

- **Fairfax module:** `core/loudoun_places_analysis.py` (shared — `analyze_neighborhood()`)
- **Loudoun module:** `core/loudoun_places_analysis.py` (`analyze_neighborhood()`)
- **Data sources:** Google Places API (New) — live queries for restaurants, bars, groceries, coffee shops, parks, pharmacies, schools, gyms within 1.5–5 miles. Cached 7 days.
- **Coverage:** **Residential Only** (in current framing)
- **Evidence:** Categories queried are residential-oriented: grocery stores, pharmacies, gyms, coffee shops. Convenience scoring weights these equally.
- **Commercial gaps:** Commercial tenants need different amenity categories: lunch restaurants (not just all restaurants), conference centers, hotels, banks, shipping/logistics (FedEx, UPS), coworking spaces, childcare centers. Current Google Places queries don't cover these.
- **OM relevance:** Partially relevant. Restaurants and retail amenities matter for office tenant recruitment. Would need reframing and additional categories for commercial OM.

### 7. Community/HOA

- **Fairfax module:** `core/community_spatial_lookup.py`, RentCast API for HOA data
- **Loudoun module:** `core/loudoun_community_lookup.py` (CommunityLookup), `core/community_spatial_lookup.py`
- **Data sources:**
  - Loudoun: `data/loudoun/config/communities.json` (17 rich profiles), `data/loudoun/gis/community_boundaries.geojson` (64 boundaries)
  - RentCast API (HOA fees, subdivision data)
- **Coverage:** **Residential Only**
- **Evidence:** HOA fees, subdivision amenities (pools, tennis courts), gated community status, management company — all residential concepts. Key fields: `monthly_fee`, `amenities_list`, `total_homes`, `gated`
- **Commercial gaps:** Commercial properties have CAM (Common Area Maintenance) charges and property management fees instead of HOA. Would need commercial-equivalent data: CAM/sqft, management company, parking ratios, building class (A/B/C).
- **OM relevance:** Not applicable for commercial OM. CAM charges are a completely different data source.

### 8. Demographics

- **Fairfax module:** `core/census_api.py`, `core/demographics_calculator.py`
- **Loudoun module:** Same shared modules
- **Data sources:** Census ACS 5-Year (2023) at block group level, TIGERweb API for geographic boundaries
  - Variables: B01003 (population), B01002 (median age), B01001 (age distribution), plus income, education, housing, race/ethnicity tables
  - Analysis radii: 1-mile and 3-mile from property
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Population demographics are geographic — they apply to any property type in the area. No property-type filtering.
- **Commercial gaps:** Commercial OM would benefit from additional Census variables: daytime population (workers, not residents), commute patterns, consumer spending data, educational attainment (workforce quality). Current residential-focused variables (household income, owner-occupied housing) are less relevant.
- **OM relevance:** Partially relevant. Population and income data useful for retail site selection. Education/workforce data useful for office. Would need reframing for commercial context.

### 9. Economic Indicators

- **Fairfax module:** `core/fairfax_economic_indicators.py`
- **Loudoun module:** `core/economic_indicators.py`
- **Data sources:**
  - Major employers: `data/fairfax/major_employers.json`, `data/loudoun/major_employers.json` (CAFR data)
  - BLS LAUS: County unemployment rate, labor force, employment
    - Fairfax series: `LAUCN510590000000003/5/6`
    - Loudoun series: `LAUCN511070000000003/5/6`
  - Census ACS: Labor Force Participation Rate, industry mix
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Unemployment rates, major employers, industry mix — all area-level economic indicators. Columns: `rank`, `name`, `employees`, `pct_of_total`
- **Commercial gaps:** Missing: office vacancy rates, asking rents/sqft by submarket, absorption rates, cap rate trends, new supply pipeline. These are the core economic indicators for commercial OM. CoStar/CBRE data would fill this gap.
- **OM relevance:** Partially relevant. Major employers and unemployment data support commercial investment thesis. Missing commercial-specific market metrics.

### 10. Medical Access

- **Fairfax module:** `core/fairfax_healthcare_analysis.py` (FairfaxHealthcareAnalysis)
- **Loudoun module:** Report helper functions + Google Places API for pharmacies
- **Data sources:**
  - Fairfax: `data/fairfax/healthcare/processed/facilities.parquet` (hospitals, urgent care with CMS ratings, Leapfrog grades)
  - Loudoun: `data/loudoun/healthcare/Loudoun_Hospitals_and_Urgent_Care.geojson`, `maternity_hospitals.json`, `CMS_Hospital_28dec25.csv`
  - Google Places API for pharmacies
- **Coverage:** **Residential Only** (in current framing)
- **Evidence:** Maternity hospitals, urgent care proximity, pharmacy access — these are residential buyer concerns. Key columns: `facility_type`, `cms_rating`, `leapfrog_grade`, `emergency_services`
- **Commercial gaps:** Not relevant for standard commercial OM. Could be tangentially relevant for senior living or medical office building OM.
- **OM relevance:** Not applicable for most commercial property types.

### 11. Development & Infrastructure (Building Permits)

- **Fairfax module:** `core/fairfax_permits_analysis.py` (FairfaxPermitsAnalysis)
- **Loudoun module:** Report helper `analyze_development()` (inline)
- **Data sources:**
  - Fairfax: `data/fairfax/building_permits/processed/permits.parquet` — 41,830 permits
    - `permit_major_category`: residential (30,473) vs commercial (11,357)
    - `permit_category`: residential_renovation (24,745), commercial_renovation (9,461), residential_new (5,728), commercial_new (1,896)
  - Loudoun: `data/loudoun/building_permits/loudoun_permits_with_infrastructure.csv` — 15,752 permits
    - `Permit Type`: Building (Residential) 10,147 / Building (Commercial) 5,338
    - `Structure Type`: Data Center (332), Other-Commercial (2,132), Residential types (11,740+)
    - Special flags: `is_datacenter` (360), `is_fiber` (3), `is_infrastructure` (487)
- **Coverage:** **Both (Residential + Commercial)**
- **Evidence:** Both counties' permit data explicitly classify permits as residential vs commercial. Fairfax `permit_major_category` = "commercial" (27% of permits). Loudoun `Permit Type` = "Building (Commercial)" (34% of permits). Data center detection is commercial-specific.
- **Commercial gaps:** Already well-covered. Could add: permit dollar value analysis by commercial subcategory, data center MW capacity tracking, tenant improvement permit trends.
- **OM relevance:** Highly relevant for commercial OM. Development pipeline and data center activity directly affect market analysis.

### 12. Zoning & Land Use

- **Fairfax module:** `core/fairfax_zoning_analysis.py` (FairfaxZoningAnalysis), `core/fairfax_comprehensive_plan_analysis.py`
- **Loudoun module:** `core/loudoun_zoning_analysis.py` (live Loudoun GIS API)
- **Data sources:**
  - Fairfax: `data/fairfax/zoning/processed/districts.parquet` (6,431 zone polygons), `overlays.parquet`
    - zone_type breakdown: residential (3,962), planned_units (1,113), commercial (910), industrial (384), tyson (38), other (24)
  - Fairfax Comp Plan: `data/fairfax/Comprehensive_Plan/processed/comp_plan_base_recommendation.geoparquet`, `comp_plan_land_units.geoparquet`
    - Land use types: Residential, Commercial/Employment, Mixed Use, Parks & Open Space, Public Facilities
  - Loudoun: Loudoun County Zoning GIS API (live)
    - Endpoints: Zoning (MapServer/3), Place Types (MapServer/10), Policy Areas (MapServer/8), town-specific layers
    - Config: `data/loudoun/config/zoning_translations.json`, `placetype_translations.json`
- **Coverage:** **Both (Residential + Commercial)**
- **Evidence:**
  - Fairfax zone codes: R-1 to R-30 (residential), **C-1 to C-8 (commercial)**, **I-1 to I-6 (industrial)**, PDC (Planned Development Commercial), PRM (Planned Residential Mixed-use)
  - `ZONE_TYPE_DESCRIPTIONS` dict explicitly defines: `'commercial': 'Commercial - Retail, office, and business uses'`, `'industrial': 'Industrial - Manufacturing and warehousing'`
  - Comprehensive Plan includes `"02": "Commercial/Employment"` and `"05": "Mixed Use"` categories
  - Loudoun GIS returns zoning codes for all types including commercial designations
- **Commercial gaps:** Zoning data is comprehensive. Could add: by-right vs special exception uses, FAR/density allowances, parking requirements, signage regulations — all important for commercial OM.
- **OM relevance:** Critical for commercial OM. Zoning determines permitted uses, density, and development potential.

### 13. Property Valuation

- **Fairfax module:** `core/fairfax_sales_analysis.py`, `core/property_valuation_orchestrator.py`, `core/attom_client.py`, `core/rentcast_client.py`, `core/comparable_analyzer.py`, `core/forecast_engine.py`
- **Loudoun module:** `core/loudoun_sales_data.py`, `core/loudoun_valuation_context.py`, same shared orchestrator/API clients
- **Data sources:**
  - Fairfax sales: `data/fairfax/sales/processed/sales_2020_2025.parquet` (90,511 sales)
    - Columns: `PARID`, `SALE_DATE`, `SALE_PRICE`, `SALE_TYPE`, `SALE_YEAR`
    - `SALE_TYPE` values: "Valid and verified sale" (87,489), "Multi-parcel sale" (2,920), "Portfolio/Bulk Sale" (57)
    - **No property type column** — cannot distinguish residential from commercial sales
  - Fairfax address points: `data/fairfax/address_points/processed/address_points.parquet` (377,318 parcels)
    - Columns: `Parcel Identification Number`, `Address Line 1`, `City`, `Zip Code`, `Subdivision Name`, `lat`, `lon`
    - **No property type or use code column**
  - Loudoun sales: `data/loudoun/sales/combined_sales.parquet` (~60,706 records)
    - Columns: `PARID`, `RECORD DATE`, `PRICE`, `SALE VERIFICATION`, `SALE TYPE`
    - `SALE TYPE`: "Land & Building" (55,505), "Land" (5,194), "Building" (7)
    - **No property type column** — cannot distinguish residential from commercial sales
  - ATTOM API: Property detail, AVM, assessment, comparable sales — **no property type filter applied** but `proptype` field returned
  - RentCast API: Rental estimates, property value — **no property type filter applied** but `propertyType` field returned
  - Forecast engine: 4% default appreciation, no type-specific rates
- **Coverage:** **Both (de facto)** — but primarily **Residential in practice**
- **Evidence:** Neither county's sales data includes a property type column. ATTOM and RentCast APIs accept any address without filtering by property type. The valuation orchestrator applies the same triangulation logic (ATTOM 40%, RentCast 30%, Comps 30%) regardless of property type. Price filters ($100K–$5M) would exclude most large commercial transactions. The forecast engine uses a flat 4% appreciation rate with no commercial-specific adjustment.
- **Commercial gaps:** Major gaps:
  - No property type column in sales data to isolate commercial transactions
  - Price ceiling ($5M) filters out most commercial deals
  - No cap rate analysis (NOI / Purchase Price)
  - No rent roll or lease abstract data
  - No price/sqft by commercial subcategory (office, retail, industrial)
  - No commercial-specific appreciation rates
  - Forecast engine doesn't account for commercial cycles
- **OM relevance:** Partially relevant. ATTOM/RentCast can return commercial property data. But valuation methodology is residential-oriented. Commercial OM needs income approach (cap rate, NOI), not comparable sales approach.

### 14. AI Property Analysis

- **Fairfax module:** Anthropic Claude API (claude-sonnet-4-20250514) called directly
- **Loudoun module:** `core/loudoun_narrative_generator.py` (`generate_property_narrative()`)
- **Data sources:** All pre-computed section data is compiled and sent as context to Claude API. Cached 24 hours.
- **Coverage:** **Both (adaptive)**
- **Evidence:** The AI narrative is generated from whatever data is available. If a commercial property is analyzed, Claude would receive zoning (commercial zone), permits (commercial activity), etc. and could adapt its narrative accordingly. No residential-only constraints in the prompt.
- **Commercial gaps:** The system prompt likely frames analysis for residential buyers. Would need a commercial-specific prompt template for OM-style narrative generation (investment thesis, tenant profile, market positioning).
- **OM relevance:** Highly relevant if prompt is adapted. Claude can generate commercial narratives, investment summaries, and market analysis from the same underlying data.

### 15. Transit (Fairfax Only — also part of Location Quality)

- **Fairfax module:** `core/fairfax_transit_analysis.py`
- **Data sources:** `data/fairfax/transit/processed/metro_stations.parquet`, `metro_lines.parquet`, `bus_routes.parquet`
- **Coverage:** **Area-Level (Both)**
- **Evidence:** Metro station proximity, walk times, bus routes — geographic data applicable to all property types.
- **Commercial gaps:** None. Transit access is a key commercial metric (office tenant recruitment, retail foot traffic).
- **OM relevance:** Directly relevant for commercial OM.

### 16. Data Sources Footer

- **Both counties:** Static text listing data sources and disclaimers
- **Coverage:** N/A (informational)

---

## Commercial Data Assets Found

The following commercial-specific data already exists in the repository:

| Asset | Location | Details |
|-------|----------|---------|
| Commercial permits (Fairfax) | `data/fairfax/building_permits/processed/permits.parquet` | 11,357 commercial permits (27% of total); categories: commercial_new (1,896), commercial_renovation (9,461) |
| Commercial permits (Loudoun) | `data/loudoun/building_permits/loudoun_permits_with_infrastructure.csv` | 5,338 commercial permits (34%); Structure types include Data Center (332), Other-Commercial (2,132) |
| Data center detection | Loudoun permits | `is_datacenter` flag on 360 permits; `infrastructure_categories` column tracks datacenter, telecom, fiber |
| Commercial zoning districts (Fairfax) | `data/fairfax/zoning/processed/districts.parquet` | 910 commercial zones (C-1 to C-8), 384 industrial zones (I-1 to I-6) |
| Commercial zoning descriptions | `core/fairfax_zoning_analysis.py` | Full C-1 through C-8 and I-1 through I-6 descriptions with use types |
| Commercial/Employment land use | Fairfax Comprehensive Plan geoparquets | Land use type "02": Commercial/Employment; type "05": Mixed Use |
| Loudoun commercial zoning | Loudoun GIS API (live) | Full commercial/industrial zoning codes via MapServer queries |
| ATTOM property type | `core/attom_client.py` | Returns `proptype` field — can identify commercial properties; no type filter applied |
| RentCast property type | `core/rentcast_client.py` | Returns `propertyType` field — can identify commercial properties |
| Traffic ADT data | Both counties | Average Daily Traffic counts — key retail site selection metric |
| Portfolio/Bulk sales | Fairfax sales data | 57 "Portfolio/Bulk Sale" transactions — likely commercial |
| Tenant Fit-Up permits | Loudoun permits | 561 "Tenant Fit-Up" work class entries — commercial-specific |

---

## Commercial Data Gaps

### Critical Gaps (Required for Commercial OM)

| Gap | Description | Potential Source |
|-----|-------------|-----------------|
| **Property type on sales** | Neither county's sales parquet has a property type column; cannot isolate commercial transactions | County assessor data (use codes), ATTOM `proptype` field, cross-reference with zoning |
| **Cap rate / NOI data** | No income data for investment analysis | CoStar, CBRE, Real Capital Analytics, or manual entry |
| **Rent roll / lease data** | No tenant, lease term, or rental rate data | CoStar, LoopNet, or manual entry from landlord |
| **Office/retail vacancy rates** | No submarket vacancy or absorption data | CoStar, CBRE MarketFlash, Cushman & Wakefield |
| **Asking rents by submarket** | No commercial rental rate benchmarks | CoStar, RentCast (if commercial supported), CBRE |
| **Building class (A/B/C)** | No quality classification for commercial buildings | CoStar, BOMA, manual assessment |
| **CAM/operating expenses** | No Common Area Maintenance or OpEx data | CoStar, building management records |
| **Parking ratios** | No parking space counts or ratios per sqft | County GIS (parking lots), manual assessment |

### Secondary Gaps (Nice-to-Have for Commercial OM)

| Gap | Description | Potential Source |
|-----|-------------|-----------------|
| Daytime population | Workers in area (vs. residents) | Census LEHD/LODES data |
| Consumer spending | Retail spending potential by category | Esri Business Analyst, Census CBP |
| Walkability/pedestrian counts | Foot traffic for retail | StreetLight Data, Placer.ai |
| Fiber/broadband availability | Internet connectivity for office/data center | FCC broadband map, local ISPs |
| Environmental (Phase I/II) | Environmental contamination risk | EPA databases, state DEQ |
| ADA compliance | Building accessibility | Manual assessment |
| Signage visibility/regulations | Sign allowances by zoning | County zoning code (already partially in zoning module) |

---

## Recommendations

### Sections That Already Work for Commercial (No Changes Needed)

1. **Zoning & Land Use** — Full commercial zone support (C-1 to C-8, I-1 to I-6, PDC). Already distinguishes commercial vs residential zones with descriptions. Comprehensive plan includes Commercial/Employment designation.
2. **Development & Infrastructure** — Already classifies permits as commercial vs residential. Data center detection built in. Development pressure scoring includes commercial activity.
3. **Emergency Services** — ISO classification applies to all property types.
4. **Location Quality** — Traffic ADT, flood zones, transit, utilities — all area-level and commercial-relevant.
5. **Crime & Safety** — Area-level safety scoring works for commercial.
6. **Demographics** — Population data applies to all types (useful for retail trade area analysis).
7. **Economic Indicators** — Major employers, unemployment, industry mix — all commercial-relevant.
8. **AI Analysis** — Claude can adapt narrative to commercial context if prompt is updated.

### Sections That Need Modification for Commercial

1. **Property Valuation** — Needs income approach (cap rate, NOI) alongside comparable sales approach. Price ceiling ($5M) needs to be configurable. Forecast engine needs commercial-specific appreciation rates.
2. **Neighborhood Amenities** — Needs commercial-relevant categories (lunch restaurants, hotels, conference centers, banks, shipping/logistics). Google Places queries can be adapted.
3. **Community/HOA** — Needs commercial equivalent: CAM charges, building management, tenant directory, parking ratios.
4. **AI Analysis** — Needs commercial-specific prompt template for OM-style output.

### Sections to Skip for Commercial OM

1. **Schools** — Not relevant (unless multifamily or mixed-use).
2. **Medical Access** — Not relevant (unless medical office building).

### New Data Sources Needed

| Priority | Data Source | Purpose | Cost |
|----------|-----------|---------|------|
| P0 | County assessor use codes | Property type classification on existing sales/parcel data | Free (FOIA) |
| P0 | ATTOM `proptype` enrichment | Tag existing sales with property type via API | Included in current ATTOM subscription |
| P1 | CoStar API or data feed | Vacancy, asking rents, cap rates, building class, tenant data | $$$$ (enterprise license) |
| P1 | Manual rent roll input | Allow user to input rent roll for custom OM | Free (UI feature) |
| P2 | Census LEHD/LODES | Daytime population, commute patterns | Free (Census API) |
| P2 | FCC Broadband Map | Fiber/broadband availability | Free (FCC API) |
| P3 | Esri Business Analyst | Consumer spending, trade area analysis | $$$ (license) |
| P3 | StreetLight / Placer.ai | Pedestrian/vehicle traffic patterns | $$$ (subscription) |

### Quick Wins (Minimal Effort, High Value)

1. **Cross-reference sales with zoning** — Join sales parquet with zoning districts parquet by lat/lon to tag each sale as residential/commercial/industrial. No new data needed.
2. **Expose ATTOM `proptype`** — Already returned by API but not surfaced. Display in valuation section.
3. **Add property type filter to comparable sales** — Use zoning overlay to exclude commercial comps from residential analysis (and vice versa).
4. **Configurable price ceiling** — Allow >$5M for commercial property searches.
5. **Commercial amenity categories** — Add Google Places queries for hotels, conference centers, banks alongside existing residential categories.
