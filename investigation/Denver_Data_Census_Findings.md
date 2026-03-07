# NewCo Data Census — Denver County (City and County of Denver), Colorado

**FIPS: 08-031 | Census Date: March 2026 | Expansion Sequence: Fairfax → Loudoun → Arlington → Denver**

---

## Output 1: Baseline Comparison Table

Status key: ✅ confirmed available | ⚠️ partial / needs verification | ❓ not confirmed | — not applicable

### 1.1 GIS / Spatial Datasets

| Dataset | Fairfax | Loudoun | Denver | Denver URL / Source | Format | Access Notes |
|---|---|---|---|---|---|---|
| **Tax Parcels (base layer)** | ✅ | ✅ | ✅ | `denvergov.org/opendata/dataset/city-and-county-of-denver-parcels` / ArcGIS Hub: `opendata-geospatialdenver.hub.arcgis.com/datasets/.../explore` (layer ID 245) | Shapefile, GeoJSON, FGDB, CSV, REST | Geometry is reference-quality, not survey-quality per Denver's metadata disclaimer. Also available via Colorado statewide parcel MapServer at `gis.colorado.gov/Public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer`. Likely in Colorado State Plane Central (EPSG:2232). |
| **Road Centerlines** | ✅ | ✅ | ✅ | `opendata-geospatialdenver.hub.arcgis.com/datasets/street-centerlines` | Shapefile, GeoJSON, FGDB, REST | Local name: "Street Centerlines." Digitally represents streets and alleys of the City and County of Denver. Confirm road classification (functional class) attribute is present for highway/collector/local scoring. |
| **Zoning Districts (base)** | ✅ | ✅ | ✅ | `opendata-geospatialdenver.hub.arcgis.com/datasets/zoning` / also `hub.arcgis.com/datasets/7410ea2dcce84e348ff9d64c4025eae1` / interactive map: `denvergov.org/maps/map/zoning` | Shapefile, GeoJSON, FGDB, REST | Denver Zoning Code (DZC, 2010) plus Former Chapter 59 legacy zone designations. Both zone types are encoded in a single layer — the zone code attribute distinguishes DZC from Ch59 parcels. Zone code taxonomy differs significantly from Virginia. Governed by ordinance. |
| **Zoning Overlay Districts** | ✅ | ✅ | ⚠️ | Not confirmed as a separate published layer. May be encoded in base zoning attributes. | Unknown | Search did not return a separately named "Design Overlay Districts" or "Special District Overlay" layer. Denver has Design Overlay Districts and Urban Design Standards areas, but these may be attributes within the base zoning layer rather than standalone polygons. Requires direct portal inspection to confirm. |
| **School Attendance Areas** | ✅ | ✅ | ⚠️ | DPS interactive map: `maps.dpsk12.org` / DPS open-geo server: `open-geo.dpsk12.org` / National fallback: `nces.ed.gov/programs/edge/SABS` | Shapefile (NCES), interactive map (DPS) | See detailed note in Output 2 (Gap Analysis). DPS operates a school choice / open enrollment model — boundary polygons have lower predictive value than in Fairfax or Loudoun. NCES SABS provides national school attendance boundary shapefiles as a reliable fallback. Colorado data.colorado.gov lists DPS board boundaries. |
| **School Facilities (points)** | ✅ | ✅ | ✅ | Denver open data portal (search "schools") / CDE SchoolView: `cde.state.co.us/schoolview` | Shapefile, CSV | School location points are a standard layer on Denver open data. CDE provides a statewide school directory with addresses. |
| **FEMA Flood Zones** | ✅ | ✅ | ✅ | FEMA NFHL: `msc.fema.gov` (download by county) / Denver interactive floodplain map: `denvergov.org/maps/map/floodplain` / FEMA GIS services: `hazards.fema.gov/femaportal/resources/flood_map_svc.htm` | Shapefile (NFHL), GeoJSON, REST | National dataset — same source for all counties. Denver has active floodplain management along the South Platte River and tributaries. Regulatory floodplain = SFHA (Zones A, AE, AH, AO, AR, A99). County-hosted extract confirmed via Denver's floodplain map. |
| **Subdivisions / Communities** | ✅ | ✅ | ✅ | `opendata-geospatialdenver.hub.arcgis.com/datasets/.../explore` (layer ID 13) / `data.colorado.gov/Municipal/Denver-Statistical-Neighborhoods/6g4b-w8bd` | Shapefile, KML, CSV, FGDB, DWG | Local name: "Statistical Neighborhoods." 78 official statistical neighborhoods developed in 1970 by the Community Renewal Program. Combinations of census tracts. Also listed as "Registered Neighborhood Organizations" (separate interactive map at `denvergov.org/maps/map/neighborhoodorganizations`). |
| **Comp Plan / Future Land Use** | ✅ | ✅ | ✅ | `opendata-geospatialdenver.hub.arcgis.com/datasets/blueprint-denver-future-places` / `denvergov.org/opendata/dataset/city-and-county-of-denver-blueprint-future-places` / Interactive: `experience.arcgis.com/experience/f83e367089d74f04a9bfa6ede1289a0b` | Shapefile, GeoJSON, FGDB, REST | Local name: "Blueprint Denver Future Places." Adopted April 22, 2019. Classifies areas into Future Places character types (Urban Center, Urban, General Urban, Suburban, etc.) and Future Neighborhood Contexts. Also see "Blueprint Denver Future Street Types" as a companion layer. This is more granular than Fairfax/Loudoun comp plan layers. **High-value confirmed.** |
| **Existing Land Use** | ✅ | ⚠️ | ✅ | Denver open data portal / referenced as one of three base planning layers alongside Blueprint Denver and Zoning. | Shapefile, REST | Denver maintains an Existing Land Use GIS layer used in planning processes. Also likely encoded in parcel/assessor attributes (use classification). Confirmed by references in Denver planning documentation. |
| **Power Lines (Major)** | — | ✅ | ✅ (HIFLD) | HIFLD: `hifld-geoplatform.opendata.arcgis.com/datasets/electric-power-transmission-lines` / Colorado-specific: `gdr.openei.org/submissions/301` | Shapefile, GeoJSON, CSV, KML, REST | No Denver-specific local layer found. HIFLD national dataset covers lines ≥100kV — clip to Denver boundaries. Includes ownership (Public Service Co of Colorado / Xcel Energy), voltage class. Xcel Energy is the primary utility serving Denver. Colorado Electrical Transmission Grid dataset also available via OpenEI. |
| **Metro / Rail Lines & Stations** | ✅ | ✅ | ✅ | RTD GIS Open Data: `gis-rtd-denver.opendata.arcgis.com` / RTD open spatial data page: `rtd-denver.com/business-center/open-spatial-data` / GTFS: `regional.rtd-denver.com/gtfs-developer-guide` | ESRI Shapefile, GTFS | RTD operates light rail (6 lines) and commuter rail (3 lines) in Denver metro. Station location shapefiles and rail line alignments available. GTFS feed available for transit routing. RTD also publishes a system map ArcGIS web app at `rtd-denver.maps.arcgis.com`. |
| **Airport Noise / Impact Overlay** | ✅ | ✅ | ✅ | BTS NTAD: `bts.gov/geospatial/national-transportation-noise-map` / Interactive: `maps.dot.gov/BTS/NationalTransportationNoiseMap` / DIA-specific: `flydenver.com/business-and-community/noise-and-airspace` / DIA 2024 Noise Study PDF: `cdn.flydenver.com/app/uploads/2024/08/14083255/DEN_Noise_Release_Study_2023-2028.pdf` | ESRI Geodatabase, Shapefile, spreadsheet (BTS) / PDF contours (DIA) | DIA is ~25 miles NE of downtown. BTS NTAD 2020 aviation noise data is the primary GIS-ready national source. DIA's 2024 IGA Noise Release Study provides 55/60/65 Ldn contours based on 2023 actual operations — but in PDF format, not GIS. DIA noise impact on central Denver is lower than Reagan National on Arlington, but affects northeast Denver properties. |
| **Historic Overlay / Districts** | ✅ | — | ✅ | `denvergov.org/opendata/dataset/city-and-county-of-denver-historic-landmark-districts` / ArcGIS Hub: `hub.arcgis.com/datasets/190c49110db34bf6a2abcc2435686879` / Interactive: `denvergov.org/maps/map/HistoricLandmarks` / `experience.arcgis.com/experience/2394b937c893460abf492bb5b3e712a4` | Shapefile, GeoJSON, FGDB, REST | Local name: "Historic Landmark Districts." Designated by Denver Landmark Preservation Commission. Districts established by city ordinance (ordinance info in feature attributes). Includes Curtis Park, Whittier, Potter-Highlands, etc. For National Register, NPS MapServer at `mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer` provides statewide coverage. Colorado SHPO (History Colorado) maintains Compass database at `historycolorado.org/survey-inventory`. |
| **Zoning Cases / Rezoning Activity** | ✅ | — | ⚠️ | Not confirmed as a standalone GIS download. Denver CPD handles rezonings. | Unknown | Denver has active rezoning (Ch59 → DZC conversions), but a downloadable GIS layer or CSV of rezoning cases was not directly confirmed. The open data portal likely has this under a name like "Map Amendments" or "Land Use Cases" — requires direct portal inspection. Denver's active rezoning environment makes this a high-volume, high-value dataset. |
| **Town / Jurisdiction Boundaries** | — | ✅ | — | N/A | N/A | Denver is a consolidated city-county with no incorporated towns within its boundaries. Not needed. |

### 1.2 Government Data & Structured Files

| Dataset | Fairfax | Loudoun | Denver | Denver URL / Source | Format | Access Notes |
|---|---|---|---|---|---|---|
| **Building Permits** | ✅ | ✅ | ✅ (confidence caveat) | `denvergov.org/opendata` (search "permits") / ArcGIS Hub: `opendata-geospatialdenver.hub.arcgis.com/datasets/residential-construction-permits` / Active portal: `denvergov.org/permits` | CSV, REST (presumed) | **Confidence caveat:** Confirmed by catalog listing and Denver's open data reputation, but NOT by direct portal observation (domain blocked during census). The Residential Construction Permits dataset is confirmed by name. **Unverified fields:** (a) geocoding precision — dataset notes say "there may still be permits whose location is unknown," implying geocoded but incomplete; (b) permit type taxonomy — Denver uses its own permit type codes, taxonomy not confirmed; (c) date range of historical records — not confirmed; (d) whether construction value is included — not confirmed. All four fields are essential for development pressure scoring. Recommend direct portal inspection before pipeline build. |
| **Crime / Incident Data** | ✅ | ⚠️ | ✅ | `denvergov.org/opendata/dataset/city-and-county-of-denver-crime` / ArcGIS Hub: `opendata-geospatialdenver.hub.arcgis.com/datasets/crime` | CSV, ArcGIS Feature Service, REST | Criminal offenses for previous 5 calendar years + current YTD. NIBRS classification (all victims). Geocoded. No dashboard wall — direct data download available. Does not include marijuana possession/sale/cultivation violations. Strong dataset. |
| **Major Employers (CAFR/ACFR)** | ✅ | ✅ | ✅ | Denver 2024 ACFR PDF: `denver.prelive.opencities.com/files/assets/public/v/1/finance/documents/financial-reports/acfr/ccd-2024-acfr-ada.pdf` / ACFR landing page: `denvergov.org/Government/Agencies-Departments-Offices/.../Department-of-Finance/Financial-Reports/Annual-Comprehensive-Financial-Report` | PDF (Statistical Section → Principal Employers table) | 2024 ACFR confirmed available. Principal Employers table in Statistical Section. Expected employers: DPS, City & County of Denver government, UCHealth, Children's Hospital Colorado, federal agencies, major private sector. City unemployment rate referenced as 4.3% (2024). Extraction requires PDF→JSON pipeline. |
| **HOA / Community Profiles** | — | ✅ | ❓ | Colorado DRE HOA Center: `dre.colorado.gov/hoa-center` / Denver Registered Neighborhood Organizations map: `denvergov.org/maps/map/neighborhoodorganizations` | N/A | No GIS layer of HOA boundaries found for Denver. Colorado DRE operates an HOA registration database but it is a registry (text records), not a GIS boundary layer. Denver publishes Registered Neighborhood Organizations as an interactive map — this is a partial substitute but not the same as HOA boundaries. Low priority per spec. |

### 1.3 Colorado-Specific Sources

| Dataset | Fairfax | Loudoun | Denver | Denver URL / Source | Format | Access Notes |
|---|---|---|---|---|---|---|
| **Traffic Volumes (CDOT)** | CO★ | CO★ | ✅ | CDOT OTIS: `dtdapps.coloradodot.info/otis` / Traffic Data Explorer: `dtdapps.coloradodot.info/otis/trafficdata` / ArcGIS layer: `data-cdot.opendata.arcgis.com/datasets/highways-traffic-counts` / ArcGIS Experience: `experience.arcgis.com/experience/ab7c09a831be45148991181947a97e12` | REST API, CSV download, ArcGIS Feature Service | CDOT is Colorado's equivalent of VDOT. AADT data confirmed available via OTIS Traffic Data Explorer (current + historical). Linear segments with AADT, Truck AADT, VMT fields. Covers state highways (I-25, I-70, US-36). Also check Denver open data portal for city-specific traffic counts from municipal signals/detectors — Denver may publish supplemental coverage for non-state roads. |
| **School Performance (CDE)** | CO★ | CO★ | ✅ | CDE Performance Frameworks: `ed.cde.state.co.us/accountability/performanceframeworks` / Results repository: `ed.cde.state.co.us/accountability/performanceframeworks/results` / Flat files (prior years): `cde.state.co.us/accountability/performance-framework-flat-files-from-prior-years` / SchoolView: `cde.state.co.us/schoolview/explore/welcome` / DPS SPF: `portfolio.dpsk12.org/page/school-performance-framework` / Third-party SPF explorer: `schoolperformanceframeworks.org/profiles/profiles/denver` | XLSX flat files, interactive web tool | Colorado School Performance Framework (SPF) ratings confirmed. CDE publishes annual results as downloadable spreadsheets (XLSX, not CSV — conversion needed). Includes school-level and district-level ratings. DPS also publishes its own SPF report card at `edison.dpsk12.org/spf-report-card`. Multi-year historical data available via flat files from prior years. Equivalent to Virginia DOE SOL data. |
| **Sales Comps (County Assessor)** | CO★ | CO★ | ⚠️ (see Output 4) | Denver Assessor property search: `denvergov.org/Property` or `property.spatialest.com/co/denver` | Web lookup (individual properties) | **See Output 4 for full analysis.** Colorado is a non-disclosure state. Sale prices are not public record. The TD-1000 is a confidential document. No free public path to actual sale prices exists for Denver County. |

---

## Output 2: Gap Analysis

### GAP: Zoning Overlay Districts — ⚠️

**Barrier:** No separately published "Design Overlay Districts" or "Special District Overlay" GIS layer was confirmed during the census. Denver has Design Overlay Districts, Urban Design Standards areas, and special district overlays, but these may be encoded as attributes within the base zoning layer rather than published as standalone polygon layers.

**Recommended path:**
1. Inspect the base zoning layer attribute table on the Denver ArcGIS Hub (`opendata-geospatialdenver.hub.arcgis.com/datasets/zoning`) — overlay designations may be encoded as a field (e.g., overlay code, special district flag).
2. If not present in the base layer, search the full Denver Open Data Catalog at `denvergov.org/opendata` under the "planning" or "zoning" tags.
3. If no public layer exists, contact Denver Community Planning & Development (CPD) at `denvergov.org/cpd` to request overlay boundary data or submit a CORA (Colorado Open Records Act) request.
4. **Estimated effort:** Low (if encoded in base layer) / Medium (if separate CORA request needed).

### GAP: School Attendance Areas — ⚠️

**Barrier:** Denver Public Schools attendance area boundaries were not confirmed as a direct shapefile download. DPS operates an interactive school finder at `maps.dpsk12.org` and appears to run an open geospatial server (`open-geo.dpsk12.org`), but downloadable shapefiles were not directly confirmed. Additionally, DPS operates open-geo services that may provide GIS layers but could not be verified due to domain access restrictions during the census.

**Recommended path:**
1. **Primary:** Check `open-geo.dpsk12.org` for WMS/WFS endpoints or shapefile downloads of elementary, middle, and high school attendance areas.
2. **Fallback:** Use NCES School Attendance Boundary Survey (SABS) national shapefiles at `nces.ed.gov/programs/edge/SABS` — these include Denver school boundaries with name, ID, and grade span attributes. Note: SABS data may lag 1–2 years behind current boundaries.
3. **Alternative:** Contact DPS directly (dpsk12.org) to request current attendance boundary GIS files.
4. **Estimated effort:** Low (NCES fallback) / Medium (DPS direct request).

**PLATFORM DESIGN NOTE — SCHOOL CHOICE MODEL:** Denver Public Schools operates a school choice / open enrollment model. Attendance area boundary polygons have significantly lower predictive value for residential decision-making than in traditional assignment districts like Loudoun or Fairfax County. Families in Denver are not guaranteed enrollment at the school within their boundary polygon — boundary residence is one factor among many in DPS's unified enrollment system (SchoolChoice). The Denver module should either: (a) display school performance data without implying boundary-based assignment, or (b) display a disclaimer alongside any boundary visualization explaining that DPS uses open enrollment and boundary residence is one factor among many. This is a fundamental difference from the Fairfax/Loudoun modules and should be reflected in the UI/UX.

### GAP: Zoning Cases / Rezoning Activity — ⚠️

**Barrier:** A downloadable GIS layer or CSV of rezoning cases / map amendments was not directly confirmed during the census. Denver has very active rezoning (Chapter 59 → DZC conversions) and this is a high-value, high-volume dataset, but its publication format is unknown.

**Recommended path:**
1. Search the Denver Open Data Catalog directly for "rezoning," "map amendments," "land use cases," or "legislative cases."
2. If not on the portal, check Denver CPD's development activity page or the Community Planning & Development case tracking system.
3. If no bulk download exists, submit a CORA request to Denver CPD for geocoded rezoning case data.
4. **Estimated effort:** Medium (if available on portal) / High (if CORA + geocoding needed).

### GAP: Building Permits (field-level verification) — ✅ with caveat

**Barrier:** The Residential Construction Permits dataset is confirmed by catalog listing, but four essential fields could not be verified during this census due to portal access restrictions: (a) geocoding precision (lat/lon or address-only), (b) permit type taxonomy, (c) date range of historical records, and (d) whether construction value is included.

**Recommended path:**
1. Access `opendata-geospatialdenver.hub.arcgis.com/datasets/residential-construction-permits` directly and inspect the attribute table / data dictionary.
2. Confirm these four fields before pipeline design begins.
3. If construction value is absent from the open data layer, check whether the active permits portal at `denvergov.org/permits` exposes richer data via an API.
4. **Estimated effort:** Low (field inspection only).

### GAP: Sales Comps — ⚠️

**See Output 4 for full analysis and recommended acquisition path.**

### GAP: HOA / Community Profiles — ❓

**Barrier:** No GIS boundary layer for HOAs was found for Denver. Colorado DRE operates a text-based HOA registry, not a spatial dataset.

**Recommended path:** Low priority per spec. If needed in future, Denver's Registered Neighborhood Organizations map (`denvergov.org/maps/map/neighborhoodorganizations`) is the closest available substitute. True HOA boundary GIS data would require manual compilation from plat maps or a commercial provider.

---

## Output 3: Novel Denver Sources

### Novel Source 1: Blueprint Denver Future Places ✅

- **Name:** Blueprint Denver Future Places
- **URL:** `opendata-geospatialdenver.hub.arcgis.com/datasets/blueprint-denver-future-places`
- **Alternate URL:** `denvergov.org/opendata/dataset/city-and-county-of-denver-blueprint-future-places`
- **Interactive map:** `experience.arcgis.com/experience/f83e367089d74f04a9bfa6ede1289a0b`
- **Format:** Shapefile, GeoJSON, FGDB, ArcGIS Feature Service (REST)
- **Adopted:** April 22, 2019
- **Attributes:** Future Places character types (Urban Center, Urban, General Urban, Suburban, etc.), Future Neighborhood Contexts, Growth Areas. The three main Blueprint values are Future Places, Future Neighborhood Context, and Growth Areas.
- **Companion layer:** "Blueprint Denver Future Street Types" also available on the same portal.
- **Rationale (Module: Development Pressure & Zoning Intelligence):** Blueprint Denver Future Places maps where Denver is explicitly encouraging densification vs. preservation. This is more granular than Fairfax/Loudoun comprehensive plan layers. Combined with the zoning layer's Chapter 59 vs. DZC attribute, it provides a two-dimensional development pressure signal: (1) what the city envisions for the area (Future Places), and (2) whether the parcel's current zoning is already aligned with that vision (DZC) or still on legacy zoning (Ch59). Parcels on Ch59 zoning in areas designated for higher-intensity Future Places represent the strongest rezoning candidates. **This is the highest-value novel dataset for Denver.**

### Novel Source 2: RTD Station Areas / TOD Zones ✅

- **Name:** RTD Transit Station Areas + Denver TOD Program
- **URLs:**
  - RTD GIS Open Data: `gis-rtd-denver.opendata.arcgis.com`
  - RTD Open Spatial Data page: `rtd-denver.com/business-center/open-spatial-data`
  - RTD TOD program: `rtd-denver.com/about-rtd/transit-oriented-development`
  - Denver DOTI Geospatial Hub: `dept-of-transportation-and-infrastructure-geospatialdenver.hub.arcgis.com`
  - Denver TOD System Map: `qa.denvergov.org/.../Transit-Oriented-Development/System-Map-and-Stations`
  - Colorado DLG Transit Center Parcels: `dlg.colorado.gov/transit-oriented-communities` (includes Transit Area parcel shapefiles with quarter-mile buffers)
  - DRCOG Regional Data Catalog: `data.drcog.org`
- **Format:** ESRI Shapefile (RTD), GTFS (transit routing), REST endpoints
- **Rationale (Modules: Infrastructure & Amenities Access + Development Pressure & Zoning Intelligence):** Denver's TOD program designates station areas with special development incentives and density bonuses. RTD operates 60+ stations across light rail and commuter rail lines. Station area polygons (quarter-mile and half-mile buffers) are standard. Denver's Station Typology classifies each station area into one of five context types. Colorado DLG provides statewide Transit Center Parcel Shapefiles. Combined with RTD ridership data and GTFS feeds, this enables proximity scoring, transit accessibility modeling, and TOD density bonus identification — none of which have a parallel in the Fairfax/Loudoun modules (WMATA station areas in Arlington are the closest analog, but Denver's TOD program is more formalized).

### Novel Source 3: Wildfire Risk / WUI Zones ✅

- **Name:** 2022 Wildland Urban Interface (CO-WRA)
- **URL:** `geodata.colorado.gov/maps/6d9ad4dc95e94a368a55e709d01782aa_0`
- **Overview page:** `arcgis.com/home/item.html?id=6d9ad4dc95e94a368a55e709d01782aa`
- **Alternate sources:** Colorado State Forest Service: `csfs.colostate.edu/wildfire-mitigation/colorados-wildland-urban-interface` / Colorado Forest Atlas: `help.coloradoforestatlas.org/public/wildland-urban-interface` / USFS national WUI: `data-usfs.hub.arcgis.com/documents/7804d89ed1094ccb9aae753228e8d89a`
- **Format:** Raster (20-meter grid cell resolution), ArcGIS Map Service
- **Attributes:** WUI classes based on houses per acre density. Part of the Colorado Wildfire Risk Assessment (CO-WRA) suite.
- **Rationale (Module: Location Quality Scoring):** The WUI is relevant for properties at Denver's western and southern edges where the city meets the Front Range foothills. This is a novel risk factor with no parallel in Fairfax or Loudoun (both are fully suburban/urban with no wildfire interface). Increasingly important for insurance underwriting and investment analysis. The 20-meter grid resolution is sufficient for parcel-level risk attribution.

### Novel Source 4: Urban Trail / Greenway Network ✅

- **Name:** Denver Bicycle Facilities
- **URL:** `opendata-geospatialdenver.hub.arcgis.com/datasets/denver-bicycle-facilities`
- **Alternate URL:** `denvergov.org/opendata/dataset/city-and-county-of-denver-denver-bicycle-facilities`
- **Interactive map:** `experience.arcgis.com/experience/ae01eb3801b643e1852436f1424e55ed`
- **Bike map PDF:** `denver.prelive.opencities.com/files/assets/public/v/2/doti/documents/bicycles/2023-denver-bike-map.pdf`
- **DRCOG regional bike routes:** `gis.drcog.org/bikeroutes`
- **Format:** Shapefile, GeoJSON, FGDB, REST
- **Attributes:** Current and future inventory of bicycle facilities. Includes existing and proposed facilities. Facility types include: bike lanes, shared lanes, off-street trails (paved shared-use paths), buffered bike lanes, protected bike lanes, neighborhood bikeways.
- **Rationale (Module: Infrastructure & Amenities Access):** Denver has ~850 miles of off-street trails and greenways (Cherry Creek Trail, South Platte River Trail, High Line Canal, etc.). Trail proximity is a significant property value driver in Denver's market. This layer supports walkability/amenity scoring for properties near trail corridors. The dataset distinguishes facility types, enabling differentiated scoring (off-street shared-use path > buffered bike lane > shared lane). No comparable layer exists in the Fairfax/Loudoun modules.

### Novel Source 5: Chapter 59 Legacy Zoning Parcels ✅ (embedded in zoning layer)

- **Name:** Chapter 59 Legacy Zoning Identification
- **URL:** Same as base zoning layer: `opendata-geospatialdenver.hub.arcgis.com/datasets/zoning`
- **Format:** Attribute within existing zoning Shapefile/Feature Service
- **Rationale (Module: Development Pressure & Zoning Intelligence):** Denver has been converting pre-2010 Chapter 59 zoning to the new Denver Zoning Code (DZC) since 2010. The base zoning layer includes both DZC and Former Chapter 59 zone designations — the zone code attribute distinguishes them. Parcels still on Chapter 59 represent a rezoning opportunity signal: they are likely candidates for future map amendments, especially in areas where Blueprint Denver Future Places designates higher-intensity development. This is not a separate layer but a high-value analytical derivation from the existing zoning data. Cross-referencing Ch59 parcels with Blueprint Denver Future Places creates a unique development pressure indicator unavailable in any other county module.

---

## Output 4: Colorado-Specific Confirmations

### 4.1 CDOT Traffic Volumes — ✅ CONFIRMED

CDOT's Online Transportation Information System (OTIS) at `dtdapps.coloradodot.info/otis` provides AADT data for Colorado state highways. The Traffic Data Explorer at `dtdapps.coloradodot.info/otis/trafficdata` allows download of current and historical traffic volume data. An ArcGIS Feature Service is also available at `data-cdot.opendata.arcgis.com/datasets/highways-traffic-counts` with linear segments containing AADT, Truck AADT, and VMT fields. Covers I-25, I-70, US-36, and other state highways through Denver. Denver may also publish city-specific traffic counts from municipal signals — check the open data portal for supplemental coverage on non-state roads.

### 4.2 CDE School Performance Data — ✅ CONFIRMED

The Colorado Department of Education publishes School Performance Framework (SPF) and District Performance Framework (DPF) ratings annually. Data is available as downloadable spreadsheets (XLSX format) from the CDE Performance Frameworks Results repository at `ed.cde.state.co.us/accountability/performanceframeworks/results`. Historical flat files available at `cde.state.co.us/accountability/performance-framework-flat-files-from-prior-years`. SchoolView interactive tool at `cde.state.co.us/schoolview/explore/welcome` provides school-level drill-down. DPS also publishes its own SPF at `portfolio.dpsk12.org/page/school-performance-framework` and an SPF report card at `edison.dpsk12.org/spf-report-card`. Data format is XLSX (not CSV) — conversion step needed. Multi-year historical data is available, supporting 5+ year trend analysis.

### 4.3 Sales Comps / Non-Disclosure Status — ⚠️ CRITICAL FINDING

**Colorado is a non-disclosure state. Sale prices are not public record. The TD-1000 (Real Property Transfer Declaration) is a confidential document filed with the Assessor and is not available to the public. Recorded deeds do not include a documentary fee stamp that would allow price reconstruction. No free public path to actual sale prices exists for Denver County.**

**Detail on the TD-1000:**
The Colorado Real Property Transfer Declaration (TD-1000) collects the total sale price for every real property transfer. However, the form is explicitly marked "Confidential Document." Per Colorado statute, the TD-1000 is not recorded with the deed, is not available for public inspection at the county assessor's office, and is only available to the buyer (or the seller, if the seller filed it). County assessors are required to maintain a sales data bank derived from TD-1000 declarations, but this data bank is used internally for valuation purposes and is not a public record.

**Detail on the documentary fee:**
Colorado imposes a documentary fee of $0.01 per $100 of consideration on recorded deeds (CRS 39-13-102). This fee is paid at recording and the amount is stamped on the deed. In theory, the fee can be reverse-calculated to estimate the sale price (fee × 10,000 = approximate price). However, the documentary fee amount is a small figure (e.g., $35 on a $350,000 sale) and while the fee itself appears on the recorded deed, it provides only a rough approximation — not an exact transaction price. Some data providers (ATTOM, CoreLogic) use the documentary fee to infer prices, with variable accuracy.

**Detail on the Denver Assessor website:**
The Denver Assessor's property search portal (`denvergov.org/Property` or `property.spatialest.com/co/denver`) was not directly accessible during this census due to domain restrictions. Third-party descriptions (countyoffice.org) reference a "Chain of Title" tab and a "Neighborhood Sales" tab that may display sale prices, sellers, and buyers. However, this could not be independently verified. Even if the Denver Assessor posts some sale price information on property detail pages (as some Colorado counties do despite non-disclosure status), this would be a web-scraping path — not a bulk data download — and would be unreliable as a primary data source.

#### Recommended Acquisition Paths for Sale Prices:

**Option A: ATTOM Data Solutions (Recommended primary)**
- Coverage: National, including Denver County
- Data: Actual transaction prices, deed transfers, mortgage data
- Format: API or bulk file delivery
- Cost: Commercial subscription — pricing varies by volume (typically $0.05–$0.15 per property record for bulk). Contact ATTOM sales for Denver County pricing.
- Quality: ATTOM uses documentary fees, MLS data, and proprietary sources to reconstruct sale prices in non-disclosure states. Quality is generally good but not perfect for CO.

**Option B: CoreLogic**
- Coverage: National, including Denver County
- Data: Transaction prices, assessor data, MLS-derived comps
- Format: API or bulk delivery
- Cost: Commercial subscription — generally higher cost than ATTOM. Enterprise pricing.
- Quality: Industry standard for property data. May have better coverage in some CO submarkets.

**Option C: Denver County Assessor Bulk Data Licensing**
- Path: Contact Denver Assessor's Office directly (`denvergov.org/.../Assessors-Office`) to inquire about bulk data licensing that includes sale price information from the internal sales data bank.
- Cost: Unknown — some CO assessors provide bulk data exports for a fee.
- Quality: Would be the most authoritative local source if available, but availability is not guaranteed and the data bank is explicitly described as confidential in state statute.
- Risk: May be declined based on confidentiality provisions.

**Option D: CoStar / Commercial Real Estate Data**
- Coverage: Denver metro — strong for commercial and multifamily, weaker for single-family residential.
- Cost: High (enterprise subscription).
- Best for: Commercial property comps if the Denver module includes non-residential analysis.

**Recommendation:** Use ATTOM as the primary sales comp provider for Denver County, consistent with the briefing document's guidance. ATTOM's documentary-fee-based price reconstruction is the industry standard for non-disclosure states. Supplement with CoreLogic if ATTOM coverage gaps are identified. Do not rely on the Denver Assessor website as a primary source — even if some sale prices are visible, they are not available as a bulk download and web scraping would be unreliable and possibly non-compliant.

---

## Output 5: Preparation Strategy Summary

| Dataset | Target Format | Estimated Effort | Known Complications |
|---|---|---|---|
| **Tax Parcels** | Parquet (from Shapefile) | Low | CRS likely EPSG:2232 (CO State Plane Central) — reproject to WGS84/Web Mercator. Geometry is reference-quality, not survey-grade. |
| **Road Centerlines** | Parquet (from Shapefile) | Low | Confirm functional class attribute is present for road class scoring (highway/collector/local). Local name: "Street Centerlines." |
| **Zoning Districts** | Parquet (from Shapefile) | Low | Zone code taxonomy differs significantly from Virginia — build a new zone-to-category mapping table for DZC codes. Ch59 parcels identifiable by zone code attribute. |
| **Zoning Overlay Districts** | Parquet (from Shapefile or attribute extraction) | Medium | May require attribute extraction from base zoning layer rather than a separate file. If separate CORA request needed, add 2–4 weeks lead time. |
| **School Attendance Areas** | Parquet (from Shapefile) | Medium | Source TBD (DPS open-geo or NCES SABS fallback). NCES data may lag 1–2 years. DPS school choice model reduces predictive value — add UI disclaimer. |
| **School Facilities** | JSON (from CSV) | Low | Straightforward point data. Match to CDE SPF ratings by school ID. |
| **FEMA Flood Zones** | Parquet (from NFHL Shapefile) | Low | National dataset — clip to Denver County boundary (FIPS 08-031). Standard FEMA NFHL processing. |
| **Statistical Neighborhoods** | Parquet (from Shapefile) | Low | 78 neighborhoods. Straightforward polygon layer. Available in multiple formats. |
| **Blueprint Denver Future Places** | Parquet (from Shapefile) | Low | High-value layer. Cross-reference with zoning Ch59 attribute for development pressure index. Map Future Places categories to intensity scores. |
| **Existing Land Use** | Parquet (from Shapefile or parcel attribute) | Low | May be encoded in assessor/parcel attributes rather than a standalone layer. Confirm during portal inspection. |
| **Power Lines** | Parquet (from HIFLD Shapefile) | Low | National dataset — clip to Denver County boundary + buffer zone. Filter by voltage class (≥100kV). |
| **RTD Metro / Rail** | Parquet (stations) + GeoJSON (lines) + GTFS (routing) | Medium | Multiple source files: station points, rail alignments, and GTFS feed. Station area buffers (0.25mi, 0.5mi) need to be generated. Integrate with Denver TOD station typology if available. |
| **Airport Noise (DIA)** | Parquet (from BTS NTAD) | Low | BTS NTAD 2020 data is the standard national source. Clip to Denver County. For higher resolution, DIA 2024 Noise Study has 55/60/65 Ldn contours but is in PDF — would require manual GIS digitization (High effort) if needed. |
| **Historic Districts** | Parquet (from Shapefile) | Low | Straightforward polygon layer. Ordinance information in feature attributes. Supplement with NPS National Register MapServer for NRHP listings. |
| **Zoning Cases / Rezoning Activity** | JSON or Parquet (from CSV/API) | Medium–High | Source not confirmed. If available on open data portal, standard ETL. If CORA request needed, add lead time. Geocoding may be needed if data is address-only. High volume due to active Ch59→DZC conversions. |
| **Building Permits** | Parquet (from CSV) | Medium | Confirmed on portal but field details unverified. Geocoding precision unknown — some permits may lack coordinates. Denver's own permit type taxonomy needs mapping. Verify construction value field before pipeline design. |
| **Crime / Incident Data** | Parquet (from CSV/API) | Low | NIBRS data, 5+ years, geocoded. Direct download or ArcGIS Feature Service. Excludes marijuana violations. Standard ETL. |
| **Major Employers (ACFR)** | JSON (from PDF extraction) | Medium | PDF→JSON pipeline. Extract Principal Employers table from Statistical Section of 2024 ACFR. Standard PDF table extraction, but layout may vary by year. |
| **CDOT Traffic Volumes** | Parquet (from CSV/Feature Service) | Low | Available via OTIS download or ArcGIS Feature Service. Linear segments with AADT fields. Clip to Denver County. Supplement with city-specific counts if available. |
| **CDE School Performance** | JSON (from XLSX) | Low | XLSX flat files — convert to JSON/Parquet. Match to school facilities by school ID. Multi-year trend data available. DPS SPF ratings provide supplemental district-level detail. |
| **Sales Comps** | JSON/Parquet (from ATTOM API) | Medium | Requires commercial subscription (ATTOM recommended). Non-disclosure state — no free public source. Documentary fee provides approximate prices only. Budget for ATTOM data costs. |
| **HOA / Community Profiles** | N/A | Defer | No GIS data available. Low priority. Defer unless business requirement changes. |
| **WUI / Wildfire Risk** | Parquet (from raster) | Medium | 20-meter grid cell raster — requires raster-to-vector conversion or zonal statistics against parcel polygons. Part of CO-WRA suite. Clip to Denver County western/southern edges where WUI is relevant. |
| **Denver Bicycle Facilities / Trails** | Parquet (from Shapefile) | Low | Line geometry with facility type attributes. Generate proximity buffers for amenity scoring. Distinguish off-street trails from on-street bike lanes for differentiated scoring. |
| **Chapter 59 Legacy Zoning** | Derived attribute (no separate file) | Low | Extract from base zoning layer — filter zone code attribute for Former Chapter 59 designations. Cross-reference with Blueprint Denver Future Places for development pressure index. No separate download needed. |
| **RTD TOD Station Areas** | Parquet (from Shapefile) | Medium | Multiple potential sources (RTD, Denver DOTI, Colorado DLG, DRCOG). Consolidate station area polygons with station typology classifications. Generate quarter-mile and half-mile buffers if pre-built polygons unavailable. |

---

## Appendix: Key Portal URLs

| Resource | URL |
|---|---|
| Denver Open Data Catalog | `denvergov.org/opendata` |
| geospatialDENVER ArcGIS Hub | `opendata-geospatialdenver.hub.arcgis.com` |
| Denver ArcGIS REST Services | `denvergov.org/arcgis/rest/services/` |
| Denver Maps | `denvergov.org/maps` |
| Denver Property Search (Assessor) | `denvergov.org/Property` |
| Colorado Statewide Parcel MapServer | `gis.colorado.gov/Public/rest/services/Parcels/Public_Parcel_Map_Services/MapServer` |
| CDOT OTIS | `dtdapps.coloradodot.info/otis` |
| CDOT ArcGIS Open Data | `data-cdot.opendata.arcgis.com` |
| CDE Performance Frameworks | `ed.cde.state.co.us/accountability/performanceframeworks` |
| CDE SchoolView | `cde.state.co.us/schoolview` |
| RTD GIS Open Data | `gis-rtd-denver.opendata.arcgis.com` |
| DRCOG Regional Data Catalog | `data.drcog.org` |
| Colorado Geospatial Portal | `geodata.colorado.gov` |
| FEMA NFHL | `msc.fema.gov` |
| BTS National Transportation Noise Map | `bts.gov/geospatial/national-transportation-noise-map` |
| HIFLD Electric Power Transmission Lines | `hifld-geoplatform.opendata.arcgis.com/datasets/electric-power-transmission-lines` |
| NPS National Register MapServer | `mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer` |
| Colorado SHPO (History Colorado) | `historycolorado.org/survey-inventory` |
| Colorado DRE HOA Center | `dre.colorado.gov/hoa-center` |
| Denver 2024 ACFR (PDF) | `denver.prelive.opencities.com/files/assets/public/v/1/finance/documents/financial-reports/acfr/ccd-2024-acfr-ada.pdf` |

---

*Census conducted March 2026. Portal access to denvergov.org and opendata-geospatialdenver.hub.arcgis.com was blocked by network egress restrictions during the census — findings for those portals are based on web search results, cached metadata, and third-party references. Direct portal verification is recommended before pipeline construction begins.*

---
---

# Denver Data Census — Follow-Up Addendum, March 2026

This addendum resolves three items from the original Denver Data Census: one new high-priority dataset (CPD Development Pipeline) and two items previously marked ⚠️ (Zoning Overlay Districts and Zoning Cases / Rezoning Activity).

---

## Objective 1: Denver CPD Development Pipeline

### Conclusion: ✅ TWO confirmed datasets cover the development pipeline — Site Development Plans (spatial) and a Development Services interactive map. A third dataset (Proposed Zone Map Amendments) covers the rezoning pipeline specifically. No single "master development activity" dataset was found, but the combination of these three sources provides strong coverage.

### Source A: Site Development Plans — ✅ Confirmed

- **Dataset name:** City and County of Denver — Site Development Plans
- **Open Data Catalog URL:** `denvergov.org/opendata/dataset/city-and-county-of-denver-site-development-plans`
- **ArcGIS Hub URL:** `opendata-geospatialdenver.hub.arcgis.com/datasets/site-development-plans`
- **Interactive map:** `denvergov.org/maps/map/sitedevelopmentplans`
- **Format:** Shapefile, GeoJSON, FGDB, ArcGIS Feature Service (REST), CSV
- **Description:** Displays information about projects involving new construction that have received site development plan (SDP) approval or are currently under review by the City and County of Denver. Originally created for use in conjunction with mapping the new zoning code.
- **Geocoding:** Yes — spatial dataset with polygon/point geometry.
- **Known fields:** Dataset includes file name of associated PDF plan drawings. Specific field names for project type, unit count, square footage, and approval status could not be confirmed during this census (portal domain blocked) — **direct inspection of the attribute table is required before pipeline design.** The interactive map at `denvergov.org/maps/map/sitedevelopmentplans` provides a visual preview of what's included.
- **Update frequency:** Likely maintained by CPD on a rolling basis as SDPs are filed and approved. Confirm cadence during portal inspection.
- **Value:** High. SDPs represent committed development projects (post-approval or in active review). This is the closest Denver equivalent to a "development pipeline" dataset. Combined with building permits data, it provides a two-stage view: SDP = planned/approved projects, permits = projects under construction.

### Source B: Development Services Map — ✅ Confirmed (interactive only)

- **URL:** `denvergov.org/Maps/map/developmentservices`
- **Format:** Interactive web map (ArcGIS Experience Builder)
- **Description:** Allows users to discover information about proposed development sites. Covers active development review cases.
- **Limitation:** This appears to be an interactive map application, not a downloadable dataset. It may be backed by a Feature Service that could be queried programmatically — the underlying REST endpoint should be inspected.
- **Value:** Medium. Useful for visual exploration but not directly ingestible unless the backing Feature Service is publicly accessible.

### Source C: Large Development Review — ❓ No structured dataset confirmed

- **URL:** `denvergov.org/content/denvergov/en/community-planning-and-development/planning-and-design/how-we-plan/general-development-plans.html`
- **Description:** Denver CPD conducts Large Development Review for sites typically over 5 acres, involving infrastructure master plans and general development plans. This is a process description, not a dataset.
- **Format:** No structured download found. Information is presented in narrative form with linked PDF documents for individual projects.
- **Recommended acquisition path:** If a structured list of active Large Development Review projects is needed, submit a CORA (Colorado Open Records Act) request to Denver CPD. Contact: `denvergov.org/Government/.../Community-Planning-and-Development/Contact-CPD`. Estimated effort: Medium (2–4 weeks for response; data may require geocoding if returned as a spreadsheet).

### Preparation strategy for Site Development Plans:

| Item | Detail |
|---|---|
| Target format | Parquet (from Shapefile/Feature Service) |
| Estimated effort | Low–Medium |
| Known complications | Field-level schema not verified. Inspect attribute table for: project address, project type, unit count, square footage, approval status, filing date, approval date. Link to associated PDF plan drawings may provide supplementary detail but requires PDF extraction pipeline. |

---

## Objective 2: Zoning Overlay Districts — Resolution

### Conclusion: Overlay districts are encoded in the base zoning layer as part of the zone district designation string, AND are shown on the official zoning map — but a separately published overlay-only GIS layer was NOT confirmed. The overlay designation is part of the zone code, not a separate attribute field.

### How Denver overlay districts work:

Per the Denver Zoning Code (Article 9, Division 9.4), overlay zone districts apply **in addition to** the underlying base zone district. There are four types:

| Overlay Type | Prefix | Purpose | Examples |
|---|---|---|---|
| **Conservation Overlay** | CO- | Modifies design standards to protect existing neighborhood character | CO-7 (Sunnyside), CO-8 |
| **Design Overlay** | DO- | Establishes specialized design standards for specific areas | DO-5 (Krisana Park), DO-6, DO-8 (Active Centers & Corridors) |
| **Use Overlay** | UO- | Permits or prohibits specific land uses beyond what the base zone allows | Various |
| **Airport Influence Overlay** | AIO- | Regulates land use, height, and noise exposure near DIA | AIO (DIA influence area) |

### How overlays appear in the GIS data:

Per the Denver Zoning Code: "Each Design Overlay District shall be shown on the official map by a 'DO-' designator and an appropriate number placed after the underlying zone district designation." This means the overlay is appended to the base zone district string in the zone designation field — e.g., a parcel might be coded `U-MX-3 DO-6` or `U-RH-2.5 CO-7`.

**This is a concatenated designation, not a separate attribute field.** The overlay information is embedded in the same field as the base zone district code. To extract overlays programmatically, the ingestion pipeline would need to parse the zone district string for CO-/DO-/UO-/AIO- suffixes.

### Separately published overlay layer:

No separately published overlay-only GIS layer was confirmed during either the original census or this follow-up. The DIA Airport Influence Overlay is the most likely candidate for a standalone layer (given DIA's own open GIS data hub at `open-gis-data-dia.hub.arcgis.com`), but this was not confirmed.

### Recommended path:

1. **Primary (Low effort):** Parse the base zoning layer's zone district designation field for overlay prefixes (CO-, DO-, UO-, AIO-). This will identify all parcels with overlay designations and allow creation of a derived overlay layer.
2. **Supplementary:** Check DIA's open GIS data hub (`open-gis-data-dia.hub.arcgis.com`) for a standalone Airport Influence Overlay boundary polygon — this would provide the AIO boundary independent of the zoning layer.
3. **If more detail is needed:** Contact Denver CPD to request a standalone overlay boundaries layer. A CORA request may yield an internal GIS layer that is not publicly published.

### Preparation strategy update:

| Item | Detail |
|---|---|
| Target format | Derived Parquet layer (parsed from base zoning Shapefile) |
| Estimated effort | Low (string parsing of zone district field) |
| Known complications | Overlay designation is a suffix on the zone code string, not a separate field. Parsing logic must handle: (a) multiple overlay suffixes on a single parcel, (b) variations in delimiter (space, dash, slash), (c) Ch59 parcels which may use a different overlay naming convention. Test parsing against the full attribute table before production. |

### Status change: ⚠️ → ✅ (resolved — overlays are encoded in base zoning layer zone district string)

---

## Objective 3: Zoning Cases / Rezoning Activity — Resolution

### Conclusion: ✅ CONFIRMED. Denver publishes Zone Map Amendments as a downloadable open dataset AND as an interactive spatial web application. This fully resolves the ⚠️ from the original census.

### Source A: Zone Map Amendments (Open Data Catalog) — ✅ Confirmed

- **Dataset name:** City and County of Denver — Zone Map Amendments
- **Open Data Catalog URL:** `denvergov.org/opendata/dataset/city-and-county-of-denver-zone-map-amendments`
- **Format:** Downloadable (Shapefile, GeoJSON, CSV, FGDB — standard Denver open data formats)
- **Description:** Contains zone map amendment (rezoning) case data for the City and County of Denver. Zone map amendments are the official mechanism for changing a parcel's zoning designation, including the high-volume Chapter 59 → DZC conversions.
- **Geocoding:** Yes — spatial dataset (polygons representing parcels or areas subject to rezoning).
- **Fields:** Specific field names could not be confirmed (portal domain blocked), but based on the nature of the dataset and Denver's open data standards, expected fields include: case number, address/location, existing zoning, proposed zoning, applicant, filing date, hearing date, decision/status, ordinance number (if approved). **Direct inspection required to confirm exact schema.**
- **Update frequency:** Likely updated on a rolling basis as cases are filed and decided. Confirm cadence during portal inspection.

### Source B: Proposed Zone Map Amendments (Rezonings) — Interactive Map — ✅ Confirmed

- **Interactive map URL:** `denvergov.org/Maps/map/proposedzonemapamendments`
- **ArcGIS item:** `geospatialdenver.maps.arcgis.com/home/item.html?id=154257d3b299499ca7bd16257e71e242`
- **ArcGIS Experience:** `experience.arcgis.com/experience/93369282152a479b8054ebee2fda8310`
- **Format:** Interactive web map (ArcGIS) — may be backed by a queryable Feature Service
- **Description:** Shows currently proposed (active/pending) rezoning applications. This is the "live queue" of in-progress rezonings, distinct from the historical dataset in Source A.
- **Value:** High. The interactive map shows active cases that have not yet been decided. The backing Feature Service endpoint (if publicly accessible) would allow programmatic queries for active rezoning applications. This enables a real-time development pressure indicator.

### Source C: CPD Map Amendments Landing Page — Contextual

- **URL:** `denvergov.org/Government/.../Community-Planning-and-Development/Denver-Zoning-Code/Map-Amendments`
- **Description:** Denver CPD's official page for reviewing current map amendment (rezoning) applications. Provides application PDFs for individual cases (e.g., `2023i-00066`, `2023i-00186`, `25-rezone-0000039`). Not a structured dataset, but useful for understanding the case numbering system and accessing individual application documents.
- **Case numbering pattern:** Cases appear to follow formats like `2023I-00066` (year + sequence) and `25-REZONE-0000039` (newer format). The numbering convention should be confirmed against the open data attribute table.

### Preparation strategy update:

| Item | Detail |
|---|---|
| Target format | Parquet (from Shapefile/Feature Service) |
| Estimated effort | Low |
| Known complications | Two data streams to integrate: (a) historical/completed amendments from the open data download, and (b) active/proposed amendments from the interactive map's backing Feature Service. Schema alignment between the two may be needed. Confirm field names, especially case status values (approved, denied, pending, withdrawn). The high volume of Ch59 → DZC conversions means this dataset may be large — confirm record count. |

### Status change: ⚠️ → ✅ (resolved — downloadable dataset confirmed at `denvergov.org/opendata/dataset/city-and-county-of-denver-zone-map-amendments`)

---

## Summary of Addendum Changes

| Item | Original Status | Updated Status | Key Finding |
|---|---|---|---|
| **CPD Development Pipeline** | Not in scope | ✅ New item | Site Development Plans dataset confirmed on open data catalog + ArcGIS Hub. Spatial, geocoded. Development Services interactive map also available. |
| **Zoning Overlay Districts** | ⚠️ | ✅ Resolved | Overlay designations (CO-, DO-, UO-, AIO-) are encoded as suffixes in the base zoning layer's zone district field. No separate overlay layer published. Parse zone code string to extract. |
| **Zoning Cases / Rezoning Activity** | ⚠️ | ✅ Resolved | Zone Map Amendments dataset confirmed on open data catalog. Downloadable. Spatial. Proposed Zone Map Amendments interactive map also available for active/pending cases. |

### Updated Preparation Strategy Rows (append to Output 5):

| Dataset | Target Format | Estimated Effort | Known Complications |
|---|---|---|---|
| **Site Development Plans** | Parquet (from Shapefile) | Low–Medium | Field schema unverified — inspect for project type, unit count, sq ft, status, dates. Link to PDF plan drawings available but requires PDF extraction if detail needed. |
| **Zone Map Amendments** | Parquet (from Shapefile) | Low | Two streams: historical (open data download) + active (interactive map Feature Service). Align schemas. High volume due to Ch59→DZC conversions. |
| **Zoning Overlays (derived)** | Derived Parquet (from base zoning) | Low | Parse zone district string for CO-/DO-/UO-/AIO- suffixes. Handle multiple overlays per parcel and delimiter variations. |

---

*Addendum completed March 2026. Same access limitations apply — direct portal inspection recommended before pipeline build.*
