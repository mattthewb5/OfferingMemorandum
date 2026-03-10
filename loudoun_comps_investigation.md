# Loudoun Comparable Sales — Data Layer Investigation

## Date: 2026-03-10

---

### Finding 1: Existing Loudoun GIS Endpoints in Codebase

**A comprehensive Loudoun sales data module already exists and is fully operational.**

**Key files:**
- `multi-county-real-estate-research/core/loudoun_sales_data.py` — Sales transaction lookup (per-parcel by PARID)
- `multi-county-real-estate-research/core/loudoun_sales_data.py` — Loads from Commissioner of Revenue Excel files converted to Parquet
- `core/fairfax_sales_analysis.py` — Fairfax equivalent (proximity-based comps using lat/lon + haversine)

**Sales data already loaded (Loudoun):**
- Source: **Loudoun Commissioner of Revenue** (annual Excel extracts: 2020–2025)
- Format: Combined Parquet at `data/loudoun/sales/combined_sales.parquet`
- **78,300 total records** (~47K arms-length after filtering)
- Columns: `#`, `JUR`, `SALEKEY`, `PARID`, `INSTRUMENT#`, `RECORD DATE`, `PRICE`, `# OF PARCELS`, `OLD OWNER`, `NEW OWNER`, `SALE TYPE`, `SALE VERIFICATION`, `SOURCE_FILE`
- Arms-length filter already implemented: includes "1:MARKET SALE", "2:MARKET LAND SALE", "5:MARKET MULTI-PARCEL SALE", "V:NEW CONSTRUCTION"
- Lookup by PARID (12-digit normalized format, e.g., "110394004000")

**ArcGIS REST endpoints currently used for Loudoun (GIS layers only — no sales layer):**

| Layer | Endpoint | Key Fields |
|-------|----------|------------|
| County Zoning | `logis.loudoun.gov/.../Zoning/MapServer/3/query` | `ZO_ZONE`, `ZD_ZONE_DESC` |
| Leesburg Zoning | `logis.loudoun.gov/.../Zoning/MapServer/0/query` | `LB_ZONE` |
| Purcellville Zoning | `logis.loudoun.gov/.../pol_connect/MapServer/26/query` | `PV_ZONE` |
| Place Types | `logis.loudoun.gov/.../Planning/MapServer/10/query` | `PT_PLACETYPE` |
| Policy Areas | `logis.loudoun.gov/.../Planning/MapServer/8/query` | `PO_POLICY` |
| Town Boundaries | `logis.loudoun.gov/.../CountyBoundary/MapServer/1/query` | `TO_TOWN` |
| FEMA Flood | `logis.loudoun.gov/.../FEMAFlood/MapServer/5/query` | `COL_DESCRIPTION_DETAIL` |
| Parcel Boundaries | `logis.loudoun.gov/.../LandRecords/MapServer/5/query` | `PA_MCPI`, `PA_TYPE` |

**Critical gap vs. Fairfax:** The Loudoun sales module does per-parcel history lookup by PARID. The Fairfax module (`fairfax_sales_analysis.py`) does **proximity-based comparable sales** using lat/lon + haversine distance. Loudoun lacks this proximity comp capability today because the sales data isn't joined with parcel centroids — but the Parcel XY table (layer 9) has coordinates for every MCPI, so joining is straightforward.

---

### Finding 2: GeoHub Bulk Sales Layer — DOES NOT EXIST

**Loudoun GeoHub (geohub-loudoungis.opendata.arcgis.com) does NOT have a bulk sales data layer.**

**Probes performed:**
| Query | Result |
|-------|--------|
| `api/search/v1/items?q=sales` | HTTP 404 — API endpoint not found |
| `api/search/v1/items?q=real+estate+transactions` | HTTP 404 |
| `api/search/v1/items?q=property+transfers` | HTTP 404 |
| `/search?q=sales` (web UI) | No sales-related datasets in results |
| `/datasets` (full catalog) | Categories: Base Layers, Land Records, Planning, Environmental, Census, Elections, Transportation, Utilities — **no sales/transaction category** |

**LOGIS Open Data Layers page** (`logis.loudoun.gov/loudoun/opendata_layers.html`) lists all available layers:
- Land Records: Tile Boundaries, ZIP Codes, Address Points, Road Centerline, Parcel Boundaries, Subdivisions
- Districts, Elections, Environmental, Planning, Public Safety, Schools, Utilities, Zoning
- **No layers containing "sales", "transaction", "transfer", "deed", "price", or "assessment"**

**LandRecords MapServer** has 10 layers/tables total (0–9):
- Layer 0: Tile Boundaries
- Layer 1: ZIP Codes
- Layer 2: Address Points
- Layer 3: Road Centerline
- Layer 4: Parcel Boundaries Labels
- Layer 5: Parcel Boundaries (fields: `PA_TYPE`, `PA_MCPI`, `PA_LEGAL_ACRE` — no sales fields)
- Layer 6: Subdivisions Labels
- Layer 7: Subdivisions
- Table 8: Master Address List (33 address fields — no sales fields)
- Table 9: Parcel XY (coordinates by MCPI — no sales fields)

**Conclusion: There is no ArcGIS-hosted bulk sales layer for Loudoun County comparable to Fairfax's `Tax_Admin_RE_Sales` FeatureServer.**

---

### Finding 3: Parcel Database Sales Fields

**The Loudoun parcel assessment system (iasWorld/Tyler Technologies) at `reparcelasmt.loudoun.gov` contains sales data but is a web UI only — not an API.**

- URL redirects from `loudoun.gov/parceldatabase` → `reparcelasmt.loudoun.gov/pt/search/commonsearch.aspx`
- System was **down for maintenance** during this investigation (2026-03-10)
- Page metadata confirms it provides: "ownership, deed information, legal descriptions, **sales data**, and assessment values"
- Data updated weekly, current as of 2026-03-05
- Contact: (703) 777-0260, realestate@loudoun.gov
- Backend: SOAP-based web services (`WS_ACCESS_MANAGER`, `WS_PUBLIC`) — not REST/ArcGIS
- Search modes: ADDRESS, PARID, TAXMAP, BLQ, REALPROP

**ArcGIS parcel layer fields probed (layer 5):**
- `PA_TYPE`, `PA_UNITS`, `PA_PLAT_NUM`, `PA_PLAT_LOT`, `PA_LEGAL_ACRE`, `PA_SUBD_NAME`, `PA_MCPI`, etc.
- **No sale price, sale date, assessment value, or owner fields in the GIS layer**

**Direct parcel query attempted:**
- `gis.loudoun.gov/arcgis/rest/services/LandRecords/Parcels/MapServer/0/query` — returned HTTP 403 (blocked)

**Conclusion: Sales data exists per-parcel in the iasWorld web portal but is NOT exposed via any queryable REST API. It cannot be bulk-queried programmatically.**

---

### Finding 4: Fairfax Baseline Fields (for comparison)

**Fairfax sales data source:** Commissioner of Revenue Excel extracts (same pattern as Loudoun), processed to Parquet.

**Fairfax sales Parquet columns (`sales_2020_2025.parquet`):**

| Field | Type | Example |
|-------|------|---------|
| `PARID` | string | "0271 12010030" |
| `SALE_DATE` | timestamp | 2023-03-16 |
| `SALE_PRICE` | float | 930,000.00 |
| `SALE_TYPE` | string | "Valid and verified sale" |
| `DEED_BOOK` | string | "27865" |
| `DEED_PAGE` | string | "1603" |
| `SALE_YEAR` | int | 2023 |

- **90,511 total records** (2020–2025)
- The Fairfax comps module (`fairfax_sales_analysis.py`) joins sales with `address_points.parquet` (369,010 parcel centroids with lat/lon) to enable proximity-based search via haversine distance

**Note:** The Fairfax `Tax_Admin_RE_Sales` ArcGIS FeatureServer endpoint referenced in the task returned HTTP 400 "Invalid URL" on all attempts. The production Fairfax comps module does NOT use an ArcGIS API — it uses local Parquet files from Commissioner of Revenue bulk data, identical in pattern to the Loudoun approach.

---

### Finding 5: Treasurer CSV Contents

**The Loudoun Treasurer's monthly CSV is a TAX PAYMENTS file, NOT a sales data file.**

**Source:** `interwapp22.loudoun.gov/TreasurerPublicFiles/public/`

**Files available (as of 2026-02-27):**
1. `OutstandingRealEstate_022026_includesDelinquentAmts_GoodThru_06052026.CSV` — 10.4 MB, 44,696 rows
2. `LAYOUT_REAL_ESTATE_PAYMENTS_PUBLIC_SHARE_022026.xlsx` — Layout guide (15 KB)

**CSV columns (from layout guide):**

| Field ID | Name | Description |
|----------|------|-------------|
| B1 | Account Number | County account number |
| B2 | Item Number | Parcel Identification Number (PIN) |
| B3 | Account Name | Owner name |
| B4 | Item Description | Property description |
| B5 | Invoice/Bill Reference | Bill reference |
| B6 | Invoice/Tax Year | Tax year |
| B7 | Invoice/Bill Number | Bill number |
| B8 | Bill Installment | First or second half |
| B9 | Supplement Flag | Y if supplement |
| B10 | Due Date | mm/dd/yyyy |
| B11 | Total Due as of Date | Penalty/interest calc date |
| B12 | Total Tax Due | Amount |
| B13 | Tax Relief Amount | Relief amount |
| + additional payment/penalty fields | | |

**No sale price, sale date, or transaction history fields.** This file tracks outstanding tax obligations and payment status — useful for identifying delinquent properties but not for comparable sales analysis.

---

### Recommendation

## **Answer: OPTION A — BULK DATA ALREADY EXISTS. Build Loudoun comps module using existing pattern.**

The investigation reveals that **Loudoun comparable sales data is already available in the codebase** and the path to a proximity-based comps module is straightforward:

### What Already Exists:
1. **78,300 sales records** (2020–2025) in `data/loudoun/sales/combined_sales.parquet` from Commissioner of Revenue
2. **Arms-length filtering** already implemented in `loudoun_sales_data.py`
3. **Parcel centroid coordinates** available via LOGIS Parcel XY table (layer 9: `PA_MCPI`, `POINT_X`, `POINT_Y`)
4. **Working Fairfax implementation** to use as template (`fairfax_sales_analysis.py`)

### What Needs to Be Built:
1. **Join sales data with parcel coordinates** — Match `PARID` from sales Parquet to `PA_MCPI` in Parcel XY layer (or download address_points equivalent)
2. **Create `loudoun_sales_analysis.py`** mirroring `fairfax_sales_analysis.py` pattern:
   - Load joined sales + coordinates from cached Parquet
   - Implement `get_nearby_sales(lat, lon, radius_miles)` using haversine distance
   - Filter by arms-length verification codes
   - Return sorted by distance with sale price, date, type, PARID
3. **Wire into OM Generator** comparable sales section

### Key Differences from Fairfax:
| Aspect | Fairfax | Loudoun |
|--------|---------|--------|
| Sales source | Commissioner of Revenue Parquet | Commissioner of Revenue Parquet (already have) |
| Sale columns | PARID, SALE_DATE, SALE_PRICE, SALE_TYPE, DEED_BOOK, DEED_PAGE | PARID, RECORD DATE, PRICE, SALE TYPE, SALE VERIFICATION, INSTRUMENT#, OLD/NEW OWNER |
| Coordinates | address_points.parquet (369K records) | Need to download/cache Parcel XY from LOGIS layer 9 |
| Records | 90,511 | 78,300 |
| Arms-length filter | SALE_TYPE = "Valid and verified sale" | SALE VERIFICATION in ["1:MARKET SALE", "2:MARKET LAND SALE", "5:MARKET MULTI-PARCEL SALE", "V:NEW CONSTRUCTION"] |

### No GIS API Needed:
Unlike what was hypothesized, **neither county uses an ArcGIS REST API for sales data**. Both use Commissioner of Revenue bulk extracts processed to Parquet. The only new data needed is a Parcel XY coordinate download to enable proximity search — this is a single bulk download from LOGIS layer 9.

### FOIA Contact (if additional data needed):
- Loudoun Commissioner of Revenue: (703) 777-0260, realestate@loudoun.gov
- Data updated weekly in iasWorld system
- Current sales extracts (2020–2025) already obtained

### Estimated Effort:
- Download Parcel XY coordinates → join with sales → create `loudoun_sales_analysis.py` → integrate into OM Generator
- Pattern is identical to working Fairfax implementation
- Primary engineering work is column name mapping and coordinate join
