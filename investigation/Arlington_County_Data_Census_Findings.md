# Arlington County, Virginia — Data Census Findings

**NewCo Platform | County Expansion — Structured Data Inventory**
**FIPS: 51-013 | Census Date: March 7, 2026**

---

## 1. Baseline Comparison Table

Status key: ✅ confirmed and accessible | ⚠️ partial, blocked, or alternate source required | ❓ unconfirmed | — not applicable

### 1.1 GIS / Spatial Datasets

| Dataset | Fairfax | Loudoun | Arlington | Arlington Layer Name / Local Term | Arlington URL | Format | Access Notes |
|---|---|---|---|---|---|---|---|
| Tax Parcels (base layer) | ✅ | ✅ | ✅ | REA Property Polygons | gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::rea-property-polygons | Shapefile, GeoJSON, CSV, FGDB | Native CRS: VA State Plane North NAD83 (WKID 2283); downloads in WGS84 |
| Road Centerlines | ✅ | ✅ | ✅ | Street Centerline (RRCL) Arl Only | gisdata-arlgis.opendata.arcgis.com/datasets/street-centerline-rrcl-arl-only | Shapefile, GeoJSON | Arlington-specific extract of regional road centerlines |
| Zoning Districts (base) | ✅ | ✅ | ✅ | Zoning Polygons | gisdata-arlgis.opendata.arcgis.com/datasets/zoning-polygons-1 | Shapefile, GeoJSON, API | Also available as live ArcGIS REST service. Arlington uses ACZO (Arlington County Zoning Ordinance) with form-based code districts under Article 11 |
| Zoning Overlay Districts | ✅ | ✅ | ⚠️ | (encoded in Zoning Polygons + ACZO Article 11) | See Zoning Polygons above | Shapefile | No separate overlay layer identified. Arlington's overlay/form-based code districts appear to be encoded in the base Zoning Polygons attribute schema or governed by ACZO Article 11. Engineer should inspect zone code attributes for overlay designations |
| School Attendance Areas | ✅ | ✅ | ✅ | Elementary School Boundary; Middle School Boundary; School Boundary Polygons | gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::elementary-school-boundary- AND /datasets/middle-school-boundary-2021 | Shapefile, GeoJSON | Also available as live MapServer at arlgis.arlingtonva.us/arcgis/rest/services/Public_Maps/School_Boundaries/MapServer. High school boundaries likely included in combined layer |
| School Facilities (points) | ✅ | ✅ | ✅ | (included in School Boundary data / address points) | See School Boundaries above + address points layer | Shapefile | School facility points may be bundled with attendance areas or derivable from address points |
| FEMA Flood Zones | ✅ | ✅ | ✅ | FEMA Flood Zone Polygons | gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::fema-flood-zone-polygons | Shapefile, GeoJSON | County-hosted extract of FEMA NFHL data |
| Subdivisions / Communities | ✅ | ✅ | ✅ | Civic Association Polygons; Arlington Neighborhoods Program Areas | gisdata-arlgis.opendata.arcgis.com/datasets/civic-association-polygons AND /datasets/arlington-neighborhoods-program-areas | Shapefile, GeoJSON | Arlington uses "Civic Associations" as its primary community boundary layer (analogous to Fairfax "Subdivisions"). Neighborhoods Program Areas provides an additional boundary set |
| Comp Plan / Future Land Use | ✅ | ✅ | ✅ | General Land Use Plan (GLUP) | data.virginia.gov/dataset/general-land-use-plan AND gisdata-arlgis.opendata.arcgis.com (search "GLUP") | Shapefile, GeoJSON | Arlington's GLUP is the equivalent of Fairfax "Comp Plan Land Units" and Loudoun "Place Types". Also available via MapServer at arlgis.arlingtonva.us/arcgis/rest/services/public/GLUP/MapServer |
| Existing Land Use | ✅ | ⚠️ | ⚠️ | (no standalone layer found) | — | — | No dedicated "Existing Land Use" polygon layer was found. May be encoded as an attribute in REA Property Polygons (use code field). Engineer should inspect parcel attributes. If absent, this is a gap vs. Fairfax |
| Power Lines (Major) | — | ✅ | ⚠️ | (no county layer; use HIFLD federal data) | hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::electric-power-transmission-lines | Shapefile, GeoJSON, CSV, KML | National dataset covering lines ≥100kV. Can be clipped to Arlington boundaries. County does not publish its own layer. Dominion Energy has undergrounded significant segments (3.7 mi Potomac Yards project) |
| Metro / Rail Lines & Stations | ✅ | ✅ | ✅ | Metro Station Areas; Metro Data (Areas, Lines, Stations); Bus Stop Points | gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::metro-station-areas AND /maps/774e7c458bf340c3beb4e63e916e46b5 AND /datasets/bus-stop-points-1 | Shapefile, GeoJSON | Arlington has 11 Metrorail stations (Orange, Blue, Silver lines) — densest coverage of any VA county. WMATA also publishes system-wide data at wmata.com/initiatives/open-data-hub/ and hub.arcgis.com/datasets/be0025ac1f344b39be8cfeedb027b8ea |
| Airport Noise / Impact Overlay | ✅ | ✅ | ✅ | (no county layer; use BTS NTAD Aviation Noise) | bts.gov/geospatial/national-transportation-noise-map AND catalog.data.gov/dataset/noise-data-20201 | ESRI Geodatabase, Shapefile | BTS National Transportation Noise Map includes modeled aviation DNL contours for DCA (Reagan National). Can be clipped to Arlington. For higher resolution: MWAA Part 150 maps available as PDF at flyreagan.com; GIS shapefiles obtainable via direct MWAA request |
| Historic Overlay / Districts | ✅ | — | ✅ | National Historic Districts poly; Arlington Historic poly; Historic Easement pnts | gisdata-arlgis.opendata.arcgis.com/datasets/national-historic-districts-poly AND /datasets/arlington-historic-poly AND /datasets/ArlGIS::historic-easement-pnts | Shapefile, GeoJSON | Both National Register and locally-designated districts available. Virginia DHR statewide backup available via ArcGIS MapServer at vcris.dhr.virginia.gov |
| Zoning Cases / Rezoning Activity | ✅ | — | ⚠️ | Zoning Site Plans Polygons; Development Tracking Points | gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::zoning-site-plans-polygons AND /datasets/ArlGIS::development-tracking-points | Shapefile, GeoJSON | No direct equivalent to Fairfax's "Zoning Cases (post-2000)" layer found. However, Zoning Site Plans Polygons shows CPHD site plan locations, and Development Tracking Points captures broader development activity including rezoning-type actions. Together these approximate the Fairfax baseline |
| Town / Jurisdiction Boundaries | — | ✅ | — | Not applicable | — | — | Arlington is a unified county with no incorporated towns |

### 1.2 Government Data & Structured Files

| Dataset | Fairfax | Loudoun | Arlington | Source / URL | Format | Access Notes |
|---|---|---|---|---|---|---|
| Building Permits | ✅ | ✅ | ✅ | catalog.data.gov/dataset/permits-applications-216b9 (all applications) AND catalog.data.gov/dataset/valuation-related-building-permits (value-impacting) AND catalog.data.gov/dataset/permit-application-history (historical) | CSV | Bulk download available. Multiple datasets covering different scopes. Also on Virginia Open Data Portal. Geocoding status (lat/lon vs. address-only) needs engineer verification. Permit portal at permits.arlingtonva.us |
| Crime / Incident Data | ✅ | ⚠️ | ⚠️ | catalog.data.gov/dataset/police-department-incidents (2015–June 2022, static CSV) AND arlingtonva.us/Government/Departments/Police-Department/Crime-Data-Hub (current, dashboard) | CSV (historical); Dashboard (current) | Historical CSV on data.gov covers 2015–June 2022 but is no longer updated. Current data available only via Crime Data Hub dashboard (launched Aug 2024, updated weekly, NIBRS classification). No ArcGIS API or Socrata feed confirmed for current data. Similar to Loudoun "Power BI wall" pattern |
| Major Employers (CAFR/ACFR) | ✅ | ✅ | ✅ | arlingtonva.us/files/sharedassets/public/v/2/budget/documents/accounting-reporting-and-control/final-acfr-fy2024_12-13-2024-online.pdf (FY2024) AND budget.arlingtonva.us/cafr/ (archive, FY2001–present) | PDF | FY2024 ACFR published Dec 13, 2024. Statistical Section contains Principal Employers table. Historical ACFRs available back to FY2001. Requires PDF extraction (same pipeline as Fairfax/Loudoun) |
| HOA / Community Profiles | — | ✅ | ❓ | — | — | No structured county source found. Civic Association Polygons provide boundary data but not community profile/HOA information. Low priority per spec |

### 1.3 Virginia-Specific Sources

| Dataset | Fairfax | Loudoun | Arlington | Source / URL | Format | Notes |
|---|---|---|---|---|---|---|
| Traffic Volumes (VDOT ADT) | VA★ | VA★ | ✅ | data.virginia.gov/dataset/aadt-2024-arlington-county AND virginiaroads.org/datasets/traffic-volume | REST API, CSV | Same statewide VDOT API. Bidirectional data 1986–2024. Note: GW Parkway is NPS-maintained and may not have VDOT counts. Verify count station density in dense urban grid |
| School Performance (VA DOE SOL) | VA★ | VA★ | ✅ | Same VA DOE statewide API/CSV | API, CSV | Same statewide source. Arlington Public Schools included. No modification needed |
| Sales Comps (Virginia RETR) | VA★ | VA★ | ✅ | Same Virginia RETR statewide source | CSV | Virginia is a non-disclosure state. ATTOM provides estimated prices only; actual sale prices come from Virginia RETR deed records. Same endpoint covers Arlington |

---

## 2. Gap Analysis

### ⚠️ Zoning Overlay Districts
**Barrier:** No separate overlay layer identified. Arlington encodes overlay and form-based code districts within the base Zoning Polygons layer and governs them under ACZO Article 11, rather than publishing a standalone overlay shapefile like Fairfax.
**Recommended path:** Engineer should download the Zoning Polygons layer and inspect the attribute schema for overlay-type zone codes (e.g., "C-O" districts, special district designations). If overlay attributes are present in the base layer, this gap is resolved at ingestion. If not, the ACZO PDF (arlingtonva.us/files/sharedassets/public/v/1/building/documents/codes-and-ordinances/aczo_effective_12.16.2023.pdf) documents all overlay districts and could be manually cross-referenced.

### ⚠️ Existing Land Use
**Barrier:** No standalone "Existing Land Use" polygon layer was found. Fairfax publishes this as a separate GIS layer (Row 180 in their catalog). Arlington may encode actual use as an attribute within REA Property Polygons.
**Recommended path:** Engineer should inspect the REA Property Polygons attribute table for a land use or property use code field. If present, this can be extracted as a derived layer. If absent, the closest alternative is the GLUP (which shows planned, not actual, use) combined with the Zoning Polygons (which shows permitted use). A FOIA request to the Arlington Real Estate Assessment office for a property use classification table is a fallback.

### ⚠️ Power Lines
**Barrier:** Arlington County does not publish a dedicated power lines GIS layer. This is partly because Dominion Energy has undergrounded significant segments in the county.
**Recommended path:** Use the HIFLD national Electric Power Transmission Lines dataset (hifld-geoplatform.opendata.arcgis.com/datasets/geoplatform::electric-power-transmission-lines), which covers lines ≥100kV nationwide. Clip to Arlington County boundaries. Note that underground segments may have incomplete coverage in HIFLD.

### ⚠️ Zoning Cases / Rezoning Activity
**Barrier:** No direct equivalent to Fairfax's dedicated "Zoning Cases (post-2000)" shapefile. Arlington tracks development activity through a combination of Zoning Site Plans Polygons and Development Tracking Points, which together cover site plan approvals and broader development activity but may not isolate pure rezoning cases.
**Recommended path:** Combine Zoning Site Plans Polygons + Development Tracking Points as the primary source. For historical rezoning cases specifically, check Arlington County Board records at arlingtonva.us or submit a data request to CPHD for a rezoning case extract. The Development Tracking quarterly reports (available as PDFs) contain detailed case-by-case data.

### ⚠️ Crime / Incident Data (current)
**Barrier:** Historical data (2015–June 2022) is available as a static CSV on data.gov but is no longer updated. Current crime data is only available via the Crime Data Hub dashboard (launched August 2024), which is an interactive visualization tool without a confirmed bulk data API or download option. This mirrors the Loudoun "Power BI wall" pattern.
**Recommended path (tiered):**
1. **Immediate:** Ingest the historical CSV from data.gov for 2015–2022 coverage.
2. **Current data — FOIA:** Submit a FOIA request to Arlington County Police Department (ACPD) for bulk incident data from July 2022 to present, requesting geocoded CSV format with NIBRS offense codes.
3. **Fallback:** Virginia State Police NIBRS data provides county-level crime statistics but at lower spatial resolution (no geocoding). Third-party aggregators (CrimeGrade, SpotCrime) provide some coverage but are not authoritative.

### ❓ Specialized School Program Boundaries
**Barrier:** No evidence of GIS layers for specialized program attendance areas (IB, Montessori, gifted/talented) analogous to Fairfax AAP boundaries.
**Recommended path:** Contact Arlington Public Schools (APS) directly. APS operates specialized programs (Arlington Traditional School, Montessori) with county-wide enrollment rather than geographic attendance zones, which may explain the absence of boundary polygons. If geographic zones exist, APS GIS staff would be the source. Low priority — note for future enhancement.

### ❓ HOA / Community Profiles
**Barrier:** No structured county source found for HOA data.
**Recommended path:** Low priority per spec. Civic Association Polygons provide community boundary data. For HOA-specific information, Virginia SCC (State Corporation Commission) business entity records can be queried, but this requires manual compilation. Defer unless a structured county or state source emerges.

---

## 3. Novel Arlington Sources

### Novel Source 1: Development Tracking Points ✅
**Dataset:** Development Tracking Points
**URL:** gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::development-tracking-points
**Format:** Shapefile, GeoJSON, CSV (via ArcGIS Open Data)
**Description:** Geocoded point layer maintained by Arlington CPHD showing development projects across the county. Tracks projects by permit type code: B-R (By-right), FBC (Form Based Code), PROF (Proffer), UP (Use Permit), URD (Unified Residential Development), UCMUD (Unified Commercial Mixed Use Development). Updated via quarterly Development Tracking Reports derived from County Board actions, CO permits, building permits, and demolition permits.
**Module supported:** **Development Pressure & Zoning Intelligence** (primary). This is a live pipeline of approved/active development projects with geocoded locations and permit type classifications. Neither Fairfax nor Loudoun publishes a comparable single GIS layer combining site plan approvals, use permits, and by-right projects. Secondary value for **Location Quality Scoring** (proximity to active development) and **Economic & Employment Context** (pipeline density signals economic momentum).

### Novel Source 2: Bike Route Lines ✅
**Dataset:** Bike Route Lines
**URL:** gisdata-arlgis.opendata.arcgis.com/datasets/bike-route-lines-1 AND data.virginia.gov/dataset/bike-route-lines
**Format:** Shapefile, GeoJSON, CSV, KML, FGDB, GeoServices REST API
**Description:** Arlington's bike and trail network including the W&OD Trail, Four Mile Run Trail, Custis Trail, and the county's extensive on-street bike lane network. Arlington is nationally recognized for bicycle infrastructure and this layer is substantially richer than anything available for Fairfax or Loudoun.
**Module supported:** **Infrastructure & Amenities Access**. Directly supports walkability/bikeability scoring for transit-oriented properties. Arlington's density and trail connectivity make this a meaningful differentiator for property valuation — proximity to trail access points and separated bike infrastructure is a feature buyers and investors value in this market.

### Novel Source 3: Form-Based Code Projects ✅
**Dataset:** Form Based Code Projects
**URL:** gisdata-arlgis.opendata.arcgis.com/datasets/form-based-code-projects
**Format:** Shapefile, GeoJSON (via ArcGIS Open Data)
**Description:** Boundaries of Form-Based Code (FBC) development projects in Arlington. Arlington's FBC areas (Columbia Pike, parts of Rosslyn-Ballston corridor) use a fundamentally different development approval framework than traditional Euclidean zoning — this layer identifies where that framework applies and what projects have been approved under it.
**Module supported:** **Development Pressure & Zoning Intelligence**. FBC areas have different development rules, density allowances, and approval processes than standard zoning districts. This layer provides a more granular version of zoning intelligence that has no parallel in Fairfax or Loudoun's traditional zoning frameworks. High value for identifying areas with flexible development potential.

### Novel Source 4: Sectors (GLUP Companion Layer) ✅
**Dataset:** Sectors
**URL:** gisdata-arlgis.opendata.arcgis.com/datasets/sectors AND data.virginia.gov/dataset/sectors
**Format:** Shapefile, GeoJSON
**Description:** Arlington's Sector Plan boundaries covering specific corridors (Rosslyn, Courthouse, Clarendon, Virginia Square, Ballston, Crystal City, Pentagon City, Columbia Pike, etc.) with unique development rules and planning frameworks. This is a more granular overlay on top of the GLUP that defines corridor-specific development standards.
**Module supported:** **Development Pressure & Zoning Intelligence**. Sector Plans are Arlington's primary mechanism for managing development in transit corridors. Each sector has distinct height limits, density bonuses, and design standards. This provides corridor-level development intelligence that goes beyond what the GLUP alone reveals. No equivalent granularity exists in Fairfax or Loudoun.

### Novel Source 5: Parking Meter Points + Curb Management Data ✅
**Dataset:** Parking Meter Points; Curb Management Data; Curb Zones; Permit Parking; Metered Parking Transactions
**URLs:**
- Parking Meter Points: gisdata-arlgis.opendata.arcgis.com/maps/ac5ab5a45b274e4798943e167afeb0f5
- Parking Meters: gisdata-arlgis.opendata.arcgis.com/maps/ArlGIS::parking-meters
- Curb Management Data: gisdata-arlgis.opendata.arcgis.com/maps/ArlGIS::curb-management-data
- Curb Zones: gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::curb-zones
- Permit Parking: gisdata-arlgis.opendata.arcgis.com/datasets/ArlGIS::permit-parking
- Metered Parking Transactions (since 2015): catalog.data.gov/dataset/metered-parking-transactions
- Parking Meters Rate History: data.virginia.gov/dataset/parking-meters-rate-history
**Format:** Shapefile, GeoJSON, CSV (multiple datasets)
**Description:** Arlington publishes an unusually rich suite of parking data: meter locations (points), curb management zones (policy-level curb allocation), permit parking areas, and transaction-level meter usage data going back to 2015. This reflects Arlington's aggressive parking management as part of transit-oriented development policy.
**Module supported:** **Infrastructure & Amenities Access** (primary) and **Development Pressure & Zoning Intelligence** (secondary). Parking supply constraints directly affect commercial and mixed-use property value. Transaction data reveals utilization patterns. Curb management zones show where the county is actively reallocating curb space away from parking — a leading indicator of transit-oriented policy direction. No comparable suite exists for Fairfax or Loudoun.

### Novel Source 6: National Landing Development Pipeline (partial — dashboard only)
**Dataset:** National Landing Development Map
**URL:** nationallanding.org/our-downtown/development-map
**Format:** Interactive web map (not GIS-downloadable)
**Description:** The National Landing BID (Crystal City, Pentagon City, Potomac Yard) maintains an interactive development map showing approved, under-construction, and planned projects including Amazon HQ2 phases, Virginia Tech Innovation Campus, and 10,000+ residential units in the pipeline. However, this is a dashboard visualization, not a downloadable GIS layer or API.
**Module supported:** **Economic & Employment Context** and **Development Pressure & Zoning Intelligence**. National Landing is the most significant real estate development story in Northern Virginia.
**Recommended path:** The Development Tracking Points layer (Novel Source 1) already captures many of these projects in GIS-downloadable format. For National Landing-specific context, the Arlington Economic Development office (arlingtoneconomicdevelopment.com) publishes additional data on HQ2 employment and investment commitments. A supplementary data extract could be compiled from county planning documents and the ACFR employer data. No standalone GIS layer specific to "National Landing" exists separately from the county-wide Development Tracking dataset.

### Novel Source 7: Federal Employment Density (OPM FedScope) — structured, non-GIS
**Dataset:** OPM FedScope / Federal Workforce Data
**URL:** fedscope.opm.gov AND data.opm.gov
**Format:** Interactive query tool; CSV bulk downloads via data.gov (catalog.data.gov/dataset/fedscope-employment-cubes-ffdfd)
**Description:** OPM's FedScope provides federal civilian employment data queryable by duty station location, agency, occupation, salary level, and other dimensions. Arlington County (including the Pentagon, Crystal City federal corridor, and numerous agency offices) has one of the highest federal civilian employment concentrations in the country. FedScope provides 5 years of historical data with location-level granularity.
**Module supported:** **Economic & Employment Context**. The Pentagon and Crystal City federal corridor represent a massive employment concentration with no parallel in Fairfax or Loudoun suburbs. Federal employment density data would enrich the employer profile beyond what the ACFR Principal Employers table provides — it adds agency-level detail, salary distributions, and trend data. Note: FedScope data is tabular (not GIS) and would need to be joined to Arlington geography by duty station location codes.
**Recommended path:** Query FedScope for Arlington County duty station data. Cross-reference with the ACFR Principal Employers table. For Pentagon/DoD facility boundaries specifically, no public GIS layer exists (security restrictions). The Pentagon's footprint can be approximated using building outlines from the Arlington GIS building outlines layer.

---

## 4. Virginia-Specific Confirmations

### VDOT Traffic Volumes — ✅ Confirmed for Arlington
VDOT publishes AADT data for Arlington County via the same statewide API and data portal used for Fairfax and Loudoun. Bidirectional traffic volume data is available from 1986–2024. Arlington-specific datasets confirmed on data.virginia.gov (AADT 2023 and 2024 Arlington County editions). No new endpoint or data source is needed. Coverage quality note: Arlington's road network is denser and shorter than Loudoun or rural Fairfax; engineer should verify count station density in the urban grid, particularly near I-66/I-395 interchanges and the GW Parkway (NPS-maintained, may lack VDOT counts).

### VA DOE School Performance (SOL) — ✅ Confirmed for Arlington
Same statewide Virginia DOE source covers Arlington Public Schools. 5-year SOL pass rate data is accessible via the same API/CSV endpoints. No modification needed.

### Virginia RETR Sales Comps — ✅ Confirmed for Arlington
Same statewide deed recordation database covers Arlington County. Virginia is a non-disclosure state — ATTOM provides estimated prices only; actual sale prices come from Virginia RETR deed records. No new source or endpoint needed.

### State Disclosure Status Note
**Virginia is a non-disclosure state.** This applies equally to Arlington, Fairfax, and Loudoun. Sale prices are not publicly available from county recorder records. Actual transaction prices must be obtained from Virginia RETR (statewide deed recordation database) or paid commercial providers (ATTOM, CoreLogic). This status is confirmed and unchanged from the Fairfax/Loudoun baseline.

---

## 5. Preparation Strategy Summary

| Dataset | Target Format | Effort | Complications |
|---|---|---|---|
| **Tax Parcels (REA Property Polygons)** | Parquet (from Shapefile) | Low | CRS conversion from WGS84 download to project CRS. Verify attribute schema matches Fairfax/Loudoun parcel model |
| **Road Centerlines** | Parquet (from Shapefile) | Low | Straightforward. Verify road classification attribute for highway/collector/local scoring |
| **Zoning Districts** | Live API preferred; Parquet backup | Low | Live ArcGIS REST endpoint available. Record unique zone code taxonomy (ACZO codes differ from Fairfax) |
| **Zoning Overlay Districts** | Derived from Zoning Polygons | Medium | Not a separate layer — requires attribute inspection of Zoning Polygons to identify overlay codes. May require manual mapping of ACZO Article 11 overlay types to NewCo canonical overlay categories |
| **School Attendance Areas** | Parquet (from Shapefile) | Low | Elem + Middle confirmed. High school likely in combined layer. Verify all three levels present. Live MapServer also available |
| **School Facilities (points)** | Parquet (from Shapefile) | Low | May need to extract from attendance area data or address points |
| **FEMA Flood Zones** | Parquet (from Shapefile) | Low | County-hosted extract. Standard FEMA schema |
| **Subdivisions / Communities** | Parquet (from Shapefile) | Low | Use Civic Association Polygons as primary. Cross-reference with Neighborhoods Program Areas for completeness |
| **Comp Plan / GLUP** | Parquet (from Shapefile) | Low | Straightforward. Also available via MapServer. Note: Arlington uses "GLUP" terminology |
| **Existing Land Use** | Derived from REA Property Polygons | Medium | Requires attribute inspection. If use-code field exists, extract as derived layer. If absent, FOIA to Real Estate Assessment office |
| **Power Lines** | Parquet (from HIFLD Shapefile) | Low | Clip national HIFLD dataset to Arlington boundaries. Low segment count expected for this small, urban county |
| **Metro / Rail** | Parquet (from Shapefile) | Low | Multiple sources available (county GIS + WMATA). Arlington county layer includes station areas with planning context |
| **Airport Noise Overlay** | Parquet (from BTS Geodatabase/Shapefile) | Medium | Clip BTS NTAD aviation noise data to Arlington boundaries. If higher resolution needed for DCA-specific contours, direct request to MWAA for Part 150 shapefiles |
| **Historic Districts** | Parquet (from Shapefile) | Low | Both National Register and local districts available as separate layers. Merge or keep separate per product requirements |
| **Zoning Cases / Rezoning Activity** | Parquet (from Shapefile) | Medium | Combine Zoning Site Plans Polygons + Development Tracking Points. May require field mapping to match Fairfax zoning cases schema |
| **Building Permits** | Parquet (from CSV) | Medium | Multiple CSV datasets with different scopes. Geocoding status unknown — may require address geocoding. Reconcile overlapping datasets (all applications vs. valuation-related vs. historical) |
| **Crime / Incident Data** | Parquet (from CSV + future FOIA) | High | Historical CSV (2015–2022) is straightforward. Current data requires FOIA to ACPD. Allow 2–4 weeks for FOIA response. Geocoding quality of FOIA data unknown until received |
| **Major Employers (ACFR)** | JSON (from PDF extraction) | Medium | Same PDF→JSON pipeline as Fairfax/Loudoun. FY2024 ACFR available. Historical ACFRs back to FY2001 |
| **VDOT Traffic Volumes** | Live API | Low | Same statewide endpoint. No new work |
| **VA DOE School Performance** | Live API / CSV | Low | Same statewide endpoint. No new work |
| **Virginia RETR Sales Comps** | CSV / Parquet | Low | Same statewide source. No new work |
| **Development Tracking Points** (Novel) | Parquet (from Shapefile) | Low | Direct download. Rich attribute schema with permit type codes. Quarterly update cadence |
| **Bike Route Lines** (Novel) | Parquet (from Shapefile) | Low | Direct download in multiple formats including GeoServices REST API |
| **Form-Based Code Projects** (Novel) | Parquet (from Shapefile) | Low | Direct download. Cross-reference with Sectors layer for corridor context |
| **Sectors** (Novel) | Parquet (from Shapefile) | Low | Direct download. Companion to GLUP — ingest together |
| **Parking Data Suite** (Novel) | Parquet (from Shapefile + CSV) | Medium | Multiple datasets to reconcile: meter points (GIS), curb zones (GIS), transaction data (CSV since 2015), rate history (CSV). Meter points and curb zones are GIS-ready; transaction data requires joining to spatial locations |
| **Federal Employment (FedScope)** (Novel) | JSON / Parquet (from CSV) | Medium | Tabular data — no native geometry. Requires geocoding or joining to Arlington geography by duty station. Query FedScope for Arlington-specific extract |

---

*Census completed March 7, 2026. All URLs verified via web search; direct portal access was blocked by network egress restrictions during this session. Engineer should verify all URLs resolve and inspect attribute schemas before pipeline development.*
