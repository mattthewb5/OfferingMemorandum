# Loudoun & Fairfax Comparable Sales — Property Type Investigation

## Top-Line Answer

**Do the Loudoun and Fairfax sales datasets contain identifiable commercial transactions (multifamily, office, retail, industrial), and if so, how are they distinguished from residential sales?**

**NO. Neither dataset contains a property type or land use code field.** Both the Loudoun `combined_sales.parquet` (78,300 records) and Fairfax `sales_2020_2025.parquet` (90,511 records) contain only transaction-level data — price, date, parties, deed reference — with zero property classification fields. There is no USE_CODE, LAND_USE, PROP_CLASS, BLDG_TYPE, or equivalent in either dataset. Commercial and residential sales are commingled with no distinguishing field.

However, commercial transactions are clearly present in both datasets (data center land sales at $709M in Loudoun, multi-parcel office/retail sales at $275M in Fairfax). The only current way to identify them is by price magnitude, owner name patterns (LLC, LP, CORP), or external join to zoning/assessment data.

**No parcel assessment parquet files exist in either county's data directory** that would provide property classification. The only path to property type filtering is: (A) spatial join with existing zoning polygon data, (B) FOIA/download of assessor property class codes, or (C) ATTOM API lookup per-parcel.

## Date: 2026-03-10

---

### Finding 1: Loudoun Sales — Column Schema & Property Type Gap

**File:** `multi-county-real-estate-research/data/loudoun/sales/combined_sales.parquet`
**Shape:** 78,300 rows × 13 columns

| Column | Dtype | Nulls | Description |
|--------|-------|-------|-------------|
| `#` | int64 | 0 | Row number |
| `JUR` | str | 0 | Jurisdiction code |
| `SALEKEY` | float64 | 34,466 | Internal reference (many nulls) |
| `PARID` | int64 | 0 | 12-digit parcel ID |
| `INSTRUMENT#` | str | 0 | Deed recording number |
| `RECORD DATE` | datetime64 | 0 | Sale date |
| `PRICE` | float64 | 407 | Sale price |
| `# OF PARCELS` | int64 | 0 | Parcels in transaction |
| `OLD OWNER` | str | 100 | Previous owner |
| `NEW OWNER` | str | 83 | New owner |
| `SALE TYPE` | str | 17,594 | Land/Building/Both (NOT property type) |
| `SALE VERIFICATION` | str | 0 | Arms-length classification |
| `SOURCE_FILE` | str | 0 | Source Excel file year |

**SALE TYPE values** (what the sale included, not property classification):

| Value | Count |
|-------|-------|
| 2:Land & Building | 55,505 |
| 1:Land | 5,194 |
| 3:Building | 7 |
| (null) | 17,594 |

**SALE VERIFICATION values** (arms-length classification):

| Value | Count | Arms-Length? |
|-------|-------|-------------|
| 1:MARKET SALE | 31,364 | Yes |
| 0:N/A | 25,228 | No |
| V:NEW CONSTRUCTION | 9,486 | Yes |
| 5:MARKET MULTI-PARCEL SALE | 5,216 | Yes |
| K:UNABLE TO VERIFY | 2,250 | No |
| 2:MARKET LAND SALE | 1,025 | Yes |
| 3:NON-MARKET SALE | 750 | No |
| N:OUTLIER NON-REPRESENTATIVE PRICE | 532 | No |
| 5B:NON-MARKET MULTI-PRCL SALE | 409 | No |
| C:ADU SALE | 396 | No |
| 7:RELATED PARTIES | 351 | No |
| P:NOT YET VERIFIED | 324 | No |
| 4:NON-MARKET LAND SALE | 279 | No |
| G:CHANGES AFTER SALE | 229 | No |
| Z:FORECLOSURE | 152 | No |
| (15 more codes) | <55 each | No |

**Property type fields: NONE.** No USE_CODE, LAND_USE, PROP_CLASS, BLDG_TYPE, PROPERTY_TYPE, CLASS, CATEGORY, or similar field exists.

**Arms-length sales > $5M (Loudoun): 1,135 records** — clearly contains commercial/industrial:

| PARID | Price | Date | Old Owner | New Owner | Inferred Type |
|-------|-------|------|-----------|-----------|---------------|
| 44282013000 | $709,000,000 | 2022-05-19 | SENTINEL ASHBURN II LLC | GI TC LOUDOUN LLC | Data center |
| 38250641000 | $205,000,000 | 2023-06-26 | SREIT BROAD VISTA TERRACE LLC | SDK ACADIA LLC | Multifamily/commercial |
| 151360620000 | $195,000,000 | 2025-04-16 | LUCK STONE CORP | AMAZON DATA SERVICES INC. | Data center land |
| 83359224000 | $185,000,000 | 2024-02-09 | BELMONT LAND LP | BELMONT-RTE 7 LLC | Land |
| 113372932000 | $180,000,000 | 2022-03-31 | BARCROFT ASSOCIATES LP | VANTAGE DATA CENTERS VA3 LLC | Data center land |
| 57361562000 | $158,500,000 | 2021-01-08 | SPUS8 ASHBOROUGH LP | HART ASHBURN LLC | Commercial |

---

### Finding 2: Fairfax Sales — Column Schema & Property Type Gap

**File:** `multi-county-real-estate-research/data/fairfax/sales/processed/sales_2020_2025.parquet`
**Shape:** 90,511 rows × 7 columns

| Column | Dtype | Nulls | Description |
|--------|-------|-------|-------------|
| `PARID` | str | 0 | Parcel ID (e.g., "0271 12010030") |
| `SALE_DATE` | datetime64[ms] | 0 | Sale date |
| `SALE_PRICE` | float64 | 0 | Sale price |
| `SALE_TYPE` | str | 0 | Arms-length classification |
| `DEED_BOOK` | str | 0 | Deed book number |
| `DEED_PAGE` | str | 0 | Deed page number |
| `SALE_YEAR` | int32 | 0 | Sale year |

**SALE_TYPE values:**

| Value | Count |
|-------|-------|
| Valid and verified sale | 87,489 |
| Valid and verified multi-parcel sale | 2,920 |
| Portfolio/Bulk Sale | 57 |
| Sale from lender - valid sale price | 38 |
| Multi-parcel lender sale - valid price | 7 |

**Property type fields: NONE.** Even leaner schema than Loudoun — only 7 columns, all transaction-level. No owner names, no property classification, no land use code.

**Arms-length sales > $5M (Fairfax): 1,019 records** — also clearly contains commercial:

| PARID | Price | Date | Sale Type |
|-------|-------|------|-----------|
| 0702 01 0026 | $275,500,000 | 2022-07-20 | Multi-parcel |
| 0161 01 0010 | $249,992,250 | 2024-10-01 | Multi-parcel |
| 0491 32 0003 | $227,500,000 | 2020-12-16 | Multi-parcel |
| 0902 01 0062A | $207,000,000 | 2024-09-30 | Multi-parcel |

---

### Finding 3: All Parquet Files in Both County Data Directories

**Loudoun (`data/loudoun/`):** Only 1 parquet file exists:
- `sales/combined_sales.parquet` — 78,300 rows, 13 cols (no property type)

**Fairfax (`data/fairfax/`):** 26 parquet files across 14 subdirectories:

| File | Rows | Property-Type-Relevant Fields? |
|------|------|-------------------------------|
| `sales/processed/sales_2020_2025.parquet` | 90,511 | No — only SALE_TYPE (verification) |
| `sales/processed/sales_2015_2019.parquet` | 79,899 | No |
| `sales/processed/sales_2010_2014.parquet` | 68,045 | No |
| `sales/processed/sales_pre2010.parquet` | 634,082 | No |
| `address_points/processed/address_points.parquet` | 377,318 | No — address, lat/lon only |
| `building_permits/processed/permits.parquet` | 41,913 | **YES** — `permit_major_category`: residential (30,529) / commercial (11,384) |
| `zoning/processed/districts.parquet` | 6,431 | **YES** — `zone_type`: residential (3,962), commercial (910), industrial (384), planned_units (1,113) |
| Other files (schools, parks, roads, etc.) | Various | Not relevant |

**Key finding:** No parcel assessment/property class parquet exists in either county. The closest proxies are:
1. **Building permits** — classifies projects as residential vs. commercial, but only covers properties with recent permits
2. **Zoning districts** — spatial polygons that classify land as residential/commercial/industrial, joinable via lat/lon

---

### Finding 4: OM Generator Current Comps Usage

**Primary comp retrieval:** `core/fairfax_sales_analysis.py` → `get_nearby_sales(lat, lon, radius_miles=0.5, limit=10, min_price=100_000, max_price=5_000_000)`

**Data pipeline:**
1. Loads `sales_2020_2025.parquet` (90,511 records)
2. Joins on PARID with `address_points.parquet` (377,318 parcels with lat/lon)
3. Filters to radius using haversine distance
4. Returns list of dicts with: `parid`, `address`, `sale_price`, `sale_date`, `sale_type`, `distance_miles`, `lat`, `lon`

**Display in OM** (`reports/fairfax_report_new.py`, lines 5648–5796, function `display_comparable_sales_section`):

| Column | Source |
|--------|--------|
| Address | From address_points join |
| Price | $X,XXX,XXX format |
| Sale Date | "Mon YYYY" format |
| Distance | "X.XX mi" |
| Sale Type | From county records |
| Quality | Calculated: Excellent/Good/Fair based on recency + distance |

**Property type in display: NO.** The code checks `s.get('property_type')` for the subject property only (line 5671) but this field is never populated. It is not returned by `get_nearby_sales()` and not available in any joined data source.

**Property type filtering: NONE.** No filter parameter exists. No zoning join. No land use lookup. All sales within radius are returned regardless of whether they're residential or commercial.

**Price filtering only:** The default `min_price=100_000` and `max_price=5_000_000` range inadvertently excludes most large commercial sales, acting as a crude residential filter. But this is a side effect, not intentional property type filtering.

**ComparableAnalyzer class** (`core/comparable_analyzer.py`): Designed for ATTOM API data, includes similarity scoring on sqft, year_built, subdivision, distance — but still no property type filter.

---

### Finding 5: Comparison Table — Loudoun vs. Fairfax Sales Schema

| Aspect | Loudoun | Fairfax |
|--------|---------|---------|
| **File** | `combined_sales.parquet` | `sales_2020_2025.parquet` |
| **Records** | 78,300 | 90,511 |
| **Date range** | 2020–2025 | 2020–2025 |
| **Parcel ID field** | `PARID` (int64, 12-digit) | `PARID` (str, space-formatted) |
| **Price field** | `PRICE` (float64) | `SALE_PRICE` (float64) |
| **Date field** | `RECORD DATE` (datetime64) | `SALE_DATE` (datetime64) |
| **Arms-length field** | `SALE VERIFICATION` (29 codes) | `SALE_TYPE` (5 codes) |
| **Deed reference** | `INSTRUMENT#` | `DEED_BOOK` + `DEED_PAGE` |
| **Owner names** | Yes (`OLD OWNER`, `NEW OWNER`) | No |
| **Property type** | **None** | **None** |
| **Land use code** | **None** | **None** |
| **Building type** | **None** | **None** |
| **Coordinate join** | Needs Parcel XY from LOGIS layer 9 | `address_points.parquet` (377K records with lat/lon) |
| **Sales > $5M** | 1,135 (clearly commercial) | 1,019 (clearly commercial) |

---

### Finding 6: Paths to Property Type Classification

Since neither dataset has a native property type field, here are the viable approaches:

#### Option A: Spatial Join with Zoning Polygons (Fastest, already in codebase)

Both counties have zoning polygon data already loaded:
- **Fairfax:** `data/fairfax/zoning/processed/districts.parquet` — 6,431 polygons with `zone_type` (residential/commercial/industrial/planned_units)
- **Loudoun:** Live ArcGIS layers at `logis.loudoun.gov/.../Zoning/MapServer/3/query` with `ZO_ZONE` codes

**Approach:** For each comp sale, spatial join its lat/lon against zoning polygons → derive property type from zone code.

**Pros:** Data already available, no external API, deterministic
**Cons:** Zoning ≠ actual use (a house in a commercial zone is still residential). Loudoun requires live API call per-comp (no cached polygons). Mixed-use zones are ambiguous.

#### Option B: FOIA Request for Assessor Property Class Codes

Both county Commissioners of Revenue maintain property class codes (required by Virginia Code § 58.1-3228):
- Loudoun: Contact realestate@loudoun.gov / (703) 777-0260
- Fairfax: Contact tax@fairfaxcounty.gov / (703) 222-8234

Request: "Parcel-level property class/use code file with PARID, matching your annual sales extract format"

**Pros:** Authoritative classification (assessor knows if a parcel is multifamily vs. office vs. SFR). Bulk file, joinable on PARID.
**Cons:** FOIA response time (5–10 business days typical for VA). Needs annual refresh. May require data use agreement.

#### Option C: Price-Based Heuristic (Crude but immediate)

For OM Generator comps, the current `max_price=5_000_000` default already filters out most large commercial sales. Could add a second tier:
- Residential comps: $100K–$5M (current default)
- Commercial comps: $1M+ with no upper bound
- Let OM Generator user select mode

**Pros:** Zero new data needed. Works today.
**Cons:** Misclassifies expensive homes as commercial and cheap commercial as residential. Not suitable for reliable analysis.

#### Option D: Owner Name Pattern Matching (Loudoun only)

Loudoun's `OLD OWNER` / `NEW OWNER` fields enable entity detection:
- LLC, LP, CORP, INC, TRUST → likely commercial/investment
- Individual names → likely residential

**Pros:** Available in current data for Loudoun. Surprisingly effective for large commercial sales.
**Cons:** Not available for Fairfax (no owner names). False positives (individuals buy investment property; LLCs hold personal residences). Maintenance burden.

#### Option E: ATTOM API (When reactivated)

ATTOM's property detail endpoint returns standardized property type codes. Already integrated in `comparable_analyzer.py`.

**Pros:** Standardized taxonomy, national coverage, per-parcel detail including sqft/year_built
**Cons:** Per-call cost. API currently inactive. Rate limits for bulk lookups.

---

### Recommendation

**For the Loudoun comps module build, proceed in two phases:**

**Phase 1 (Immediate — no new data needed):**
Build `loudoun_sales_analysis.py` mirroring the Fairfax pattern:
- Join `combined_sales.parquet` with Parcel XY coordinates (download from LOGIS layer 9)
- Implement `get_nearby_sales(lat, lon)` with haversine distance
- Use the existing `min_price` / `max_price` parameters as the property type proxy
- Map column names: `RECORD DATE` → sale_date, `PRICE` → sale_price, `SALE VERIFICATION` → sale_type
- This gives us feature parity with Fairfax today

**Phase 2 (Property type enrichment — both counties):**
Submit parallel FOIA requests to both Commissioners of Revenue for parcel-level property class code files. When received:
- Create a shared `property_class.parquet` per county, keyed on PARID
- Add `property_type` field to `get_nearby_sales()` output
- Add property type filter parameter and display column to OM Generator
- Enable separate residential and commercial comp searches

**Phase 2 is not a blocker for Phase 1.** The OM Generator can ship Loudoun comps with price-range filtering (matching current Fairfax behavior) while property class enrichment is pursued separately for both counties simultaneously.
