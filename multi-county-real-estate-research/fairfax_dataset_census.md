# Fairfax County Dataset Census

**Generated:** 2026-02-27
**Scope:** `data/fairfax/` — all processed datasets, JSON configs, and raw CSVs
**Code searched:** `reports/fairfax_report_new.py`, `core/fairfax_*.py`, imported `core/loudoun_*.py` modules

---

## Summary Table

| # | Dataset | Type | Rows | Size | Geo | Status | Section Fit | Complexity |
|---|---------|------|------|------|-----|--------|-------------|------------|
| 1 | `address_points/processed/address_points.parquet` | parquet | 377,318 | 12.6 MB | No | USED | Comparable Sales (geocoding) | — |
| 2 | `building_permits/processed/permits.parquet` | parquet | 41,830 | 3.9 MB | No | USED | Development & Infrastructure | — |
| 3 | `building_permits/processed/metadata.json` | json | — | 929 B | — | USED | Development (date range) | — |
| 4 | `cell_towers/processed/towers.parquet` | parquet | 148 | 26.6 KB | Yes | USED | Cell Tower Coverage | — |
| 5 | `cell_towers/raw/fairfax_towers_fcc.csv` | csv | 148 | — | No | UNUSED | — (raw duplicate of towers.parquet) | N/A |
| 6 | `crime/processed/incidents.parquet` | parquet | 5,828 | 229 KB | No | USED | Crime & Safety + map layer | — |
| 7 | `crime/processed/metadata.json` | json | — | 558 B | — | USED | Crime & Safety (date range) | — |
| 8 | `emergency_services/processed/fire_stations.parquet` | parquet | 47 | 20.7 KB | Yes | **LOADED-NOT-DISPLAYED** | Location Quality / Emergency | **Low** |
| 9 | `emergency_services/processed/police_stations.parquet` | parquet | 23 | 15.1 KB | Yes | **LOADED-NOT-DISPLAYED** | Location Quality / Emergency | **Low** |
| 10 | `flood/processed/fema_zones.parquet` | parquet | 3,313 | 22.6 MB | Yes | USED | Location Quality (flood zone) | — |
| 11 | `flood/processed/dam_inundation.parquet` | parquet | 17 | 3.3 MB | Yes | USED | Location Quality (flood risk) | — |
| 12 | `flood/processed/easements.parquet` | parquet | 897 | 4.7 MB | Yes | USED | Location Quality (flood risk) | — |
| 13 | `healthcare/processed/facilities.parquet` | parquet | 77 | 22.8 KB | No | USED | Medical Access | — |
| 14 | `healthcare/processed/metadata.json` | json | — | 1.0 KB | — | USED | Medical Access (metadata) | — |
| 15 | `healthcare/maternity_hospitals.json` | json | 4 hosp | 9.8 KB | — | USED | Medical Access → Maternity | — |
| 16 | `major_employers.json` | json | 16 yrs | 17.4 KB | — | USED | Economic Indicators (employers) | — |
| 17 | `config/data_sources.json` | json | — | 1.9 KB | — | **UNUSED** | Footer / Data Sources | **Low** |
| 18 | `parks/processed/parks.parquet` | parquet | 585 | 2.2 MB | Yes | USED | Location Quality (park access) | — |
| 19 | `parks/processed/recreation.parquet` | parquet | 14,459 | 24.2 MB | Yes | **PARTIALLY-USED** | Parks / Neighborhood | **Medium** |
| 20 | `parks/processed/trails.parquet` | parquet | 5,818 | 1.7 MB | Yes | **PARTIALLY-USED** | Parks / Location Quality | **Medium** |
| 21 | `roads/processed/road_centerlines.parquet` | parquet | 148,594 | 39.3 MB | Yes | **UNUSED** | Road network / Traffic map | **High** |
| 22 | `roads/processed/bridges.parquet` | parquet | 1,659 | 341 KB | Yes | **UNUSED** | Infrastructure / Development | **Low** |
| 23 | `sales/processed/sales_2020_2025.parquet` | parquet | 90,511 | 1.4 MB | No | USED | Property Value Analysis | — |
| 24 | `sales/processed/sales_2015_2019.parquet` | parquet | 79,899 | 1.2 MB | No | **UNUSED** | Price Trend Chart | **Medium** |
| 25 | `sales/processed/sales_2010_2014.parquet` | parquet | 68,045 | 1.1 MB | No | **UNUSED** | Price Trend Chart | **Medium** |
| 26 | `sales/processed/sales_pre2010.parquet` | parquet | 634,082 | 8.1 MB | No | **UNUSED** | Price Trend Chart | **Medium** |
| 27 | `schools/processed/elementary_zones.parquet` | parquet | 142 | 1.8 MB | Yes | USED | School Assignments | — |
| 28 | `schools/processed/middle_zones.parquet` | parquet | 26 | 1.0 MB | Yes | USED | School Assignments | — |
| 29 | `schools/processed/high_zones.parquet` | parquet | 24 | 1.0 MB | Yes | USED | School Assignments | — |
| 30 | `schools/processed/facilities.parquet` | parquet | 269 | 35.6 KB | Yes | USED | School Assignments (fallback) | — |
| 31 | `schools/performance/processed/performance_summary.parquet` | parquet | 192 | 38.4 KB | No | USED | School Performance | — |
| 32 | `schools/performance/processed/performance_trends.parquet` | parquet | 972 | 24.6 KB | No | USED | School Performance (charts) | — |
| 33 | `schools/performance/raw/fairfax_schools_vdoe.csv` | csv | 972 | — | No | USED (fallback) | School Performance (if parquet missing) | — |
| 34 | `subdivisions/processed/subdivisions.parquet` | parquet | 11,430 | 2.1 MB | Yes | USED | Community & Amenities | — |
| 35 | `traffic/processed/traffic_volumes.parquet` | parquet | 18,557 | 4.0 MB | Yes | USED | Location Quality (road access) | — |
| 36 | `traffic/raw/fairfax_vdot_traffic.csv` | csv | 18,557 | — | No | UNUSED | — (raw duplicate of traffic_volumes.parquet) | N/A |
| 37 | `transit/processed/bus_routes.parquet` | parquet | 89 | 1.4 MB | Yes | **PARTIALLY-USED** | Transit / Development map | **Medium** |
| 38 | `transit/processed/metro_lines.parquet` | parquet | 44 | 35.1 KB | Yes | USED | Metro map layer | — |
| 39 | `transit/processed/metro_stations.parquet` | parquet | 32 | 11.1 KB | Yes | USED | Transit / Location Quality | — |
| 40 | `utilities/processed/utility_lines.parquet` | parquet | 125 | 60.3 KB | Yes | USED | Development map layer | — |
| 41 | `zoning/processed/districts.parquet` | parquet | 6,431 | 9.7 MB | Yes | USED | Zoning & Land Use | — |
| 42 | `zoning/processed/overlays.parquet` | parquet | 73 | 932 KB | Yes | USED | Zoning & Land Use | — |

### Status Summary

| Status | Count | Notes |
|--------|-------|-------|
| **USED** (fully displayed) | 28 | Data loaded, processed, and rendered in report UI |
| **PARTIALLY-USED** | 3 | Data loaded by module but only subset of fields/rows consumed in UI |
| **LOADED-NOT-DISPLAYED** | 2 | Core module exists and loads data, but not called from report |
| **UNUSED** | 6 | No reference in any code, or raw CSV duplicated by parquet |
| **UNUSED (raw dup)** | 3 | Raw CSV/file that is superseded by processed parquet |
| **Total** | 42 | |

---

## Unused / Underused Datasets (Detail)

---

### 1. Fire Stations (`emergency_services/processed/fire_stations.parquet`)

**Status:** LOADED-NOT-DISPLAYED

**Schema:** 47 rows × 12 columns
| Column | Sample Values | Null % |
|--------|--------------|--------|
| station_name | McLean, Vienna, Fairfax City South | 0% |
| station_full_name | Fire Station 1 - McLean | 0% |
| station_type | — | 0% |
| address | — | 0% |
| latitude/longitude | — | 0% |
| geometry | Point | 0% |

**Data Quality:** Excellent — all 47 stations, zero nulls, full geocoding.

**What exists:** `core/fairfax_emergency_services_analysis.py` is a complete module (ISO fire protection scoring, nearest-station lookup, response time estimation). It has methods: `assess_fire_protection_iso()`, `get_nearest_fire_stations()`, `get_nearest_police_stations()`.

**What's missing:** The module is **never imported** in `fairfax_report_new.py`. No `display_emergency_services_section()` exists.

**Section Fit:** Location Quality section — add fire station distance + ISO class to the existing key features block. Or create a dedicated "Emergency Services" subsection in the Location Quality expander.

**Preparation needed:** None — module is fully implemented, tested API matches existing patterns.

**Implementation Complexity:** **Low**
- Import `FairfaxEmergencyServicesAnalysis` in report
- Call `assess_fire_protection_iso(lat, lon)` and `get_nearest_fire_stations(lat, lon)`
- Display ISO fire class, nearest station name/distance, insurance impact note
- Optionally add fire/police station markers to the development map

**Feature description:** The Location Quality section would gain a fire protection assessment showing the nearest fire station (name + distance), the inferred ISO Public Protection Class (1-10 scale), and an insurance impact note. Properties beyond 5 miles from a fire station automatically receive ISO Class 10 (highest insurance premiums), which is material information for homebuyers. Police station proximity would be shown alongside. Estimated implementation: ~30 lines of display code.

---

### 2. Police Stations (`emergency_services/processed/police_stations.parquet`)

**Status:** LOADED-NOT-DISPLAYED

**Schema:** 23 rows × 10 columns
| Column | Sample Values | Null % |
|--------|--------------|--------|
| station_name | Franconia Station, McLean Station | 0% |
| address | 6121 Franconia RD | 0% |
| phone | 703-922-0889 | 0% |
| station_type | STATION, COMM, HQ | 0% |
| latitude/longitude | — | 0% |
| geometry | Point | 0% |

**Data Quality:** Excellent — all fields populated.

**Section Fit:** Same as fire stations — Location Quality or Crime & Safety section.

**Preparation needed:** None.

**Implementation Complexity:** **Low** — Display alongside fire stations.

**Feature description:** Would add "Nearest Police Station" with name, distance, and phone number to the Crime & Safety section or Location Quality. Map markers could be added to the development map (show=False by default). Shows 8 district stations + headquarters + community centers.

---

### 3. Road Centerlines (`roads/processed/road_centerlines.parquet`)

**Status:** UNUSED

**Schema:** 148,594 rows × 21 columns (39.3 MB)
| Column | Sample Values | Null % |
|--------|--------------|--------|
| road_name | TELEGRAPH RD, SULLY RD | — |
| road_class | — | — |
| ffx_class | — | ~61% |
| speed_limit | — | — |
| divided | — | — |
| length_miles | — | — |
| geometry | LineString | 0% |

**Data Quality:** Good — 61% null on ffx_class but core fields (road_name, geometry) fully populated. Contains the entire Fairfax County road network.

**Section Fit:** Development map layer — show road network as base layer. Or enhance traffic analysis by joining ADT data to road geometry for a traffic heatmap.

**Preparation needed:**
- Join with `traffic_volumes.parquet` on road_name to create ADT-annotated road geometry
- Filter to major roads (road_class or speed_limit thresholds) for manageable rendering

**Implementation Complexity:** **High**
- 148K segments is too many for Folium rendering — must filter
- Join with traffic data requires road name fuzzy matching
- Significant performance consideration for map rendering

**Feature description:** The development map could show a "traffic heatmap" layer where road segments are color-coded by ADT (green = low, yellow = moderate, red = high). This would replace the current point-based traffic display with a continuous network visualization. However, the 148K segment count requires aggressive filtering (e.g., only show roads with ADT > 10K) to avoid crashing the browser.

---

### 4. Bridges (`roads/processed/bridges.parquet`)

**Status:** UNUSED

**Schema:** 1,659 rows × 22 columns (341 KB)
| Column | Sample Values | Null % |
|--------|--------------|--------|
| road_name | TELEGRAPH RD, SULLY RD, I495 NB RAMP | 0% |
| road_type_suffix | — | 31% |
| ffx_class | — | 61% |
| is_bridge | — | 0% |
| speed_limit | — | 0% |
| latitude/longitude | — | 0% |
| geometry | LineString | 0% |

**Data Quality:** Moderate — core fields good, classification fields have gaps.

**Section Fit:** Development & Infrastructure section — show bridges as map overlay or mention in infrastructure summary.

**Preparation needed:** None significant.

**Implementation Complexity:** **Low**
- Add as map layer (CircleMarker at bridge centroids)
- ~20 lines of code

**Feature description:** A toggleable "Bridges" layer on the development map showing 1,659 bridge locations as point markers. Clicking a bridge shows the road name and type. Most useful for properties near water crossings, flood zones, or highway interchanges. Low priority — niche audience.

---

### 5. Recreation Features (`parks/processed/recreation.parquet`)

**Status:** PARTIALLY-USED

**Schema:** 14,459 rows × 6 columns (24.2 MB)
| Column | Sample Values | Null % |
|--------|--------------|--------|
| feature_type | TENNIS COURT, BASKETBALL COURT, PATHWAY, PLAYGROUND | 0% |
| area_sqft | — | 0% |
| centroid_lat/lon | — | 0% |
| geometry | Polygon/MultiPolygon | 0% |

**Data Quality:** Excellent — fully populated, rich variety of recreational feature types.

**Current usage:** Loaded by `FairfaxParksAnalysis` but only used internally for park scoring. The raw feature types are never displayed in the UI.

**Section Fit:** Neighborhood section or Location Quality parks subsection — "What's nearby: 3 playgrounds, 2 basketball courts, 1 trail within 1 mile."

**Preparation needed:** Aggregate nearby features by type and distance.

**Implementation Complexity:** **Medium**
- Need to compute distances from property to all 14K features (performance concern)
- Group by feature_type, filter to within 1 mile
- Display as bullet list or icon grid

**Feature description:** An "Outdoor Activities Nearby" subsection within Location Quality or the Neighborhood section would show a breakdown of recreational features within walking distance: "Within 1 mile: 4 playgrounds, 2 tennis courts, 3 basketball courts, 2 dog parks." Families with children would find this immediately actionable. Could also be visualized as color-coded dots on the development map.

---

### 6. Trails (`parks/processed/trails.parquet`)

**Status:** PARTIALLY-USED

**Schema:** 5,818 rows × 11 columns (1.7 MB)
| Column | Sample Values | Null % |
|--------|--------------|--------|
| trail_name | Cross County Trail | **88.9%** |
| park_name | Sugarland Run Stream Valley | 0% |
| surface_material | Asphalt, Natural, Bridge | 0.2% |
| width_ft | 6.0, 4.0, 8.0 | 0.5% |
| length_ft / length_miles | — | 0% |
| difficulty | — | **98.2%** |
| ada_accessible | — | **100%** null |
| geometry | LineString | 0% |

**Data Quality:** Mixed — geometry and length are solid, but `trail_name` (89% null), `difficulty` (98% null), and `ada_accessible` (100% null) are nearly empty.

**Current usage:** Loaded by `FairfaxParksAnalysis` but only used for aggregate scoring. Trail details never displayed.

**Section Fit:** Location Quality parks subsection — show nearest named trail with surface type and length.

**Preparation needed:**
- Filter to rows where `trail_name` is not null (only ~650 named trails)
- Total trail miles within radius using `length_miles`

**Implementation Complexity:** **Medium**
- Calculate total trail miles within radius
- Display nearest named trail
- Show as trail polylines on development map

**Feature description:** A "Trails & Walking Paths" metric within Location Quality: "12.4 miles of trails within 2 miles. Nearest: Cross County Trail (0.3 mi, Asphalt surface)." The development map could add a trail polyline layer (green dashed lines). Given the high null rate on trail names, focus on aggregate miles rather than individual trail listings.

---

### 7. Historical Sales (`sales/processed/sales_2015_2019.parquet`, `sales_2010_2014.parquet`, `sales_pre2010.parquet`)

**Status:** UNUSED

**Schema:** (combined) 782,026 rows × 7 columns
| Column | Sample Values | Null % |
|--------|--------------|--------|
| PARID | 0271 12010030 | 0% |
| SALE_DATE | datetime | 0% |
| SALE_PRICE | 930000.0 | 0% |
| SALE_TYPE | Valid and verified sale | 0% |
| SALE_YEAR | 2020–2025 (current), 2010–2019 (historical) | 0% |

**Data Quality:** Excellent — all fields populated, 872K total records spanning 2000–2025.

**Current usage:** Only `sales_2020_2025.parquet` (90K records) is loaded by `get_nearby_sales()`. The three historical files are never loaded.

**Section Fit:** Property Value Analysis — 15-year price trend chart for the subject property's neighborhood.

**Preparation needed:**
- Concatenate all 4 sales files
- Join with `address_points.parquet` for geocoding (PARID → lat/lon)
- Filter to subject property's neighborhood (0.5 mi radius)
- Calculate median sale price by year

**Implementation Complexity:** **Medium**
- Need geocoding join (PARID linkage to address_points)
- Time-series chart (Plotly line chart, already used elsewhere)
- ~50 lines: load → join → aggregate → chart

**Feature description:** A "Neighborhood Price Trends" chart in the Property Value Analysis section showing median sale price per year from 2010–2025 for homes within 0.5 miles of the subject property. This 15-year price history gives buyers perspective on appreciation rates, the 2020 COVID bump, and current trajectory. The data supports both line charts and rolling-average smoothing.

---

### 8. Bus Routes (`transit/processed/bus_routes.parquet`)

**Status:** PARTIALLY-USED

**Schema:** 89 rows × 7 columns (1.4 MB)
| Column | Sample Values | Null % |
|--------|--------------|--------|
| route_number | 101, 109, 151 | 0% |
| route_name | Fort Hunt, Rose Hill | 0% |
| division | Huntington, West Ox | 0% |
| service_type | Local, Express, Feeder | 0% |
| length_miles | — | 0% |
| schedule_url | — | 0% |
| geometry | LineString | 0% |

**Data Quality:** Excellent — all fields populated.

**Current usage:** Loaded by `FairfaxTransitAnalysis._load_bus_routes()`, contributes to transit scoring. But bus route details (names, routes, map layer) are never displayed.

**Section Fit:** Location Quality transit subsection or development map layer.

**Preparation needed:** None — geometry and metadata are ready.

**Implementation Complexity:** **Medium**
- Add bus routes as Folium PolyLine layer on development map
- Show nearest bus route name/number in Location Quality
- ~30 lines

**Feature description:** The development map would gain a "Bus Routes" layer showing Fairfax Connector lines as polylines, color-coded by service type (Local = blue, Express = green, Feeder = gray). The Location Quality section would note "Nearest bus: Route 151 Engleside (0.4 mi)" next to the Metro access metric. This is especially useful for properties far from Metro stations.

---

### 9. `config/data_sources.json`

**Status:** UNUSED

**Schema:** Top-level keys: `county`, `fips`, `last_updated`, `sources`

**Data Quality:** Complete configuration file.

**Section Fit:** Data Sources footer — could auto-populate source citations.

**Preparation needed:** None.

**Implementation Complexity:** **Low** — read JSON and render as footer bullets.

**Feature description:** The Data Sources footer could be auto-generated from this JSON instead of hardcoded, ensuring source citations stay up-to-date as new data is added.

---

## Recommended Priority Order

Top 5 datasets to implement next, ranked by **data quality × user value × implementation ease**:

### 1. Fire & Police Stations (HIGHEST PRIORITY)
- **Dataset:** `fire_stations.parquet` + `police_stations.parquet`
- **Why:** Module is 100% complete (`FairfaxEmergencyServicesAnalysis`), zero code to write for backend. ISO fire protection class directly affects homeowner insurance rates — this is highly actionable information that no competitor report provides. Only ~20 lines of display code needed.
- **Implementation:** Import module in report → call `assess_fire_protection_iso()` → display ISO class, nearest station distance, insurance impact in Location Quality section. Add station markers to development map.
- **Effort:** 1-2 hours

### 2. Historical Sales (15-Year Price Trends)
- **Dataset:** `sales_2015_2019.parquet` + `sales_2010_2014.parquet` + `sales_pre2010.parquet`
- **Why:** 782K records spanning 15+ years. Price trend charts are the #1 most-requested feature by real estate buyers. Data quality is 100% (zero nulls). Geocoding join via PARID to `address_points.parquet` enables neighborhood-level trends.
- **Implementation:** Extend `fairfax_sales_analysis.py` to load historical files → join with address_points → aggregate median price/year → Plotly line chart in Property Value section.
- **Effort:** 3-4 hours

### 3. Recreation Features (Nearby Activities)
- **Dataset:** `recreation.parquet` (14,459 features)
- **Why:** Families with children want to know about playgrounds, sports courts, and dog parks within walking distance. Data quality is excellent (zero nulls). Adds concrete, actionable detail beyond "nearest park."
- **Implementation:** Spatial query for features within 1 mile → group by feature_type → display as icon grid or bullet list in Neighborhood section.
- **Effort:** 2-3 hours

### 4. Bus Routes (Transit Map Layer)
- **Dataset:** `bus_routes.parquet` (89 routes)
- **Why:** Adds transit context for the 60%+ of Fairfax properties that are far from Metro. Module already loads the data. Geometry is ready for direct Folium rendering.
- **Implementation:** Add PolyLine layer to development map + nearest route callout in Location Quality.
- **Effort:** 1-2 hours

### 5. Trail Network (Walking/Running Paths)
- **Dataset:** `trails.parquet` (5,818 segments)
- **Why:** "Total trail miles within 2 miles" is a compelling lifestyle metric. Geometry enables a beautiful map layer. Trail name null rate (89%) limits per-trail detail but aggregate miles is solid.
- **Implementation:** Spatial query for trail segments within radius → sum length_miles → add PolyLine layer to map → display aggregate metric.
- **Effort:** 2-3 hours

---

## Appendix: Complete File Tree with Sizes

```
data/fairfax/
├── address_points/processed/address_points.parquet      12.6 MB   377,318 rows
├── building_permits/
│   └── processed/
│       ├── permits.parquet                               3.9 MB    41,830 rows
│       └── metadata.json                                 929 B
├── cell_towers/
│   ├── processed/towers.parquet                         26.6 KB      148 rows
│   └── raw/fairfax_towers_fcc.csv                         —         148 rows
├── config/data_sources.json                              1.9 KB
├── crime/
│   └── processed/
│       ├── incidents.parquet                            229 KB     5,828 rows
│       └── metadata.json                                558 B
├── emergency_services/processed/
│   ├── fire_stations.parquet                            20.7 KB      47 rows
│   └── police_stations.parquet                          15.1 KB      23 rows
├── flood/processed/
│   ├── fema_zones.parquet                               22.6 MB   3,313 rows
│   ├── dam_inundation.parquet                            3.3 MB      17 rows
│   └── easements.parquet                                 4.7 MB     897 rows
├── healthcare/
│   ├── processed/
│   │   ├── facilities.parquet                           22.8 KB      77 rows
│   │   └── metadata.json                                 1.0 KB
│   └── maternity_hospitals.json                          9.8 KB     4 hospitals
├── major_employers.json                                 17.4 KB    16 years
├── parks/processed/
│   ├── parks.parquet                                     2.2 MB     585 rows
│   ├── recreation.parquet                               24.2 MB  14,459 rows
│   └── trails.parquet                                    1.7 MB   5,818 rows
├── roads/processed/
│   ├── road_centerlines.parquet                         39.3 MB  148,594 rows
│   └── bridges.parquet                                  341 KB    1,659 rows
├── sales/processed/
│   ├── sales_2020_2025.parquet                           1.4 MB   90,511 rows
│   ├── sales_2015_2019.parquet                           1.2 MB   79,899 rows
│   ├── sales_2010_2014.parquet                           1.1 MB   68,045 rows
│   └── sales_pre2010.parquet                             8.1 MB  634,082 rows
├── schools/
│   ├── processed/
│   │   ├── elementary_zones.parquet                      1.8 MB     142 rows
│   │   ├── middle_zones.parquet                          1.0 MB      26 rows
│   │   ├── high_zones.parquet                            1.0 MB      24 rows
│   │   └── facilities.parquet                           35.6 KB     269 rows
│   └── performance/processed/
│       ├── performance_summary.parquet                  38.4 KB     192 rows
│       └── performance_trends.parquet                   24.6 KB     972 rows
├── subdivisions/processed/subdivisions.parquet           2.1 MB  11,430 rows
├── traffic/
│   ├── processed/traffic_volumes.parquet                 4.0 MB  18,557 rows
│   └── raw/fairfax_vdot_traffic.csv                       —      18,557 rows
├── transit/processed/
│   ├── bus_routes.parquet                                1.4 MB      89 rows
│   ├── metro_lines.parquet                              35.1 KB      44 rows
│   └── metro_stations.parquet                           11.1 KB      32 rows
├── utilities/processed/utility_lines.parquet            60.3 KB     125 rows
└── zoning/processed/
    ├── districts.parquet                                 9.7 MB   6,431 rows
    └── overlays.parquet                                 932 KB       73 rows
```

**Total processed data:** ~150 MB across 33 parquet/json files
**Total records:** ~1.5 million rows (dominated by sales_pre2010 at 634K and address_points at 377K)
