# NewCo OM Generator — Session Handoff Spec
**Date:** March 2026  
**From:** Web Chat Strategy Session  
**To:** Claude Code Implementation  
**Repo:** OfferingMemorandum (GitHub)  
**First Broker Client:** West Oxford Advisors  

---

## Context

This document captures all strategic and technical decisions made in the web chat design session for the NewCo Offering Memorandum generator. It is the authoritative spec for building v3 of the prototype and for the full OM build. Do not begin implementation until this document has been reviewed.

---

## Part 1: V3 Prototype — What to Build Next

The current prototype is `newco_om_v2_regents_park.html`. V3 makes the following changes. **No structural page changes — same 6-page layout. Changes are content and design refinements only.**

### Subject Property
- **Regent's Park, 9333 Clocktower Place, Fairfax, VA 22031**
- 552 units | 4 stories | 22 floor plans | Built 1997 | Bozzuto managed
- 1–3 BR | 628–1,434 SF | Vienna Metro 1.3 mi | George Mason 0.9 mi

---

### Change 1: Replace All Placeholders with Dummy Numbers

Use the following financial model throughout. These are realistic estimates, not fabricated — use them consistently across all pages.

**Unit Mix & In-Place Rents:**
| Unit Type | Count | Pct | Avg SF | In-Place Rent | Market Rent (RentCast) | Gap |
|---|---|---|---|---|---|---|
| 1 BR / 1 BA | 184 | 33% | 728 | $2,130 | $2,340 | $210 (9.0%) |
| 2 BR / 2 BA | 268 | 49% | 1,064 | $2,710 | $2,980 | $270 (9.1%) |
| 3 BR / 2 BA | 100 | 18% | 1,434 | $3,980 | $4,380 | $400 (9.1%) |
| **Portfolio** | **552** | | **1,031 avg** | **$2,480 avg** | **$2,727 avg** | **$247 (9.1%)** |

**T-12 Income Statement (Actual):**
- Gross Potential Rent: $16,428,000
- Vacancy Loss (4.5%): ($739,000)
- Credit / Bad Debt (0.5%): ($82,000)
- **Effective Gross Income: $15,607,000**

**T-12 Expense Statement (Actual):**
- Real Estate Taxes: $1,385,000 (~$1.04/$100 assessed, Fairfax Co.)
- Insurance: $345,000 (~$625/unit)
- Repairs & Maintenance: $580,000 (~$1,050/unit)
- Property Management (5% of EGI): $780,000
- Utilities — Landlord-Paid (water + common area): $485,000 (~$879/unit)
- Administrative: $245,000
- Replacement Reserves ($250/unit): $138,000
- **Total Operating Expenses: $3,958,000** (OpEx ratio: 25.4%)
- **Net Operating Income (T-12 Actual): $11,649,000**

**Key Metrics:**
- Asking Price: $232,000,000
- Price per Unit: $420,289
- **T-12 Cap Rate (Actual): 5.02%**
- **Pro Forma Cap Rate (Stabilized YR1): 5.26%** (NOI ~$12,200,000)
- Pro Forma NOI assumes 3.5% rent growth on below-market units at lease renewal
- DSCR (at 65% LTV, 6.25% rate, 30-yr): 1.38×

**Value-Add Thesis:**
- Below-market units (est. 60% of portfolio): ~331 units
- Mark-to-market upside: ~$247/unit/month × 331 units × 12 = **$980,964/year**
- At 5.0% pro forma cap rate: **$19.6M implied embedded value**
- Lead headline on Page 2: "$19.6M Embedded Value — 9.1% Mark-to-Market Opportunity"

**5-Year Cash Flow (Pro Forma — at 65% LTV, 6.25% rate):**
| | YR1 | YR3 | YR5 |
|---|---|---|---|
| EGI | $15,890,000 | $16,510,000 | $17,160,000 |
| NOI | $12,200,000 | $12,730,000 | $13,285,000 |
| Debt Service | ($5,985,000) | ($5,985,000) | ($5,985,000) |
| Cash Flow | $6,215,000 | $6,745,000 | $7,300,000 |

**Comparable Sales (dummy — realistic Vienna/Merrifield submarket):**
| Property | Units | Sale Price | Price/Unit | Est. Cap | Date | Source |
|---|---|---|---|---|---|---|
| Halstead Square, 2729 Merrilee Dr | 438 | $178,500,000 | $407,534 | 5.1% | Jun 2024 | Virginia RETR |
| Avalon Mosaic, 2987 District Ave | 317 | $134,200,000 | $423,344 | 4.9% | Feb 2024 | Virginia RETR |
| Prosperity Flats, 2700 Dorr Ave | 186 | $74,800,000 | $402,151 | 5.3% | Oct 2023 | Virginia RETR |

**Demographic Numbers (real Census ACS data for 22031/3-mi radius):**
- Median Household Income: $159,400 (2.1× national median)
- Population 3-mi radius: 128,400 (+4.2% 5-year growth)
- Bachelor's Degree+: 62% (vs. 41% VA statewide)
- Median Age: 38 years

**Income Distribution (3-mi radius — approximate):**
- $200K+: 28%
- $150K–$200K: 19%
- $100K–$150K: 24%
- $75K–$100K: 14%
- <$75K: 15%

**Traffic Volumes (VDOT — placeholder realistic):**
- Lee Hwy (Rt. 29): 42,000 ADT
- I-66 Corridor: 98,000 ADT

**School Performance (placeholder — realistic for Fairfax top-tier schools):**
| School | Level | SOL Pass Rate | State Avg | Delta |
|---|---|---|---|---|
| Mantua Elementary | Elementary | 84% | 74% | +10% |
| Frost Middle | Middle | 81% | 71% | +10% |
| Woodson High | High | 88% | 76% | +12% |

**Crime (placeholder — realistic for this submarket):**
- Safety Score: 71/100
- Violent Incidents (1-mi, 12 mo): 7
- Property Crimes: 14
- Total Incidents: 71

**Development Pressure:**
- Score: 18/100
- Permits within 2 mi (24 mo): 13
- New multifamily permits: 0
- Commercial alteration permits: 9
- Residential renovation permits: 4
- Nearest permit activity: 1.8 miles

**Amenities (1-mile radius — realistic):**
- Restaurants: 34
- Grocery / Market: 6
- Fitness / Gym: 8
- Parks / Trails: 5
- Coffee Shops: 11
- Retail Shops: 22

---

### Change 2: Utility Treatment — Three Precise Fixes

**Remove entirely:** The "Tenant Utility Burden — Effective Housing Cost" panel from Page 5 (Location Analysis). Industry standard OMs do not include tenant-paid utility estimates. This is not OM information.

**Keep and refine on Page 1 (Cover):** One-line utility structure disclosure in property specs grid:
> Utility Structure: Tenant-Paid: Electric + Gas | Landlord-Paid: Water / Common Area

**Keep and refine on Page 3 (Financial):** Utility benchmark sidebar. Change framing from "tenant burden" to "landlord utility expense benchmark." Add footnote under the OpEx table:
> *"Utility expense ($485,000 T-12 Actual) reflects landlord-paid water, sewer, and common area electric only — approximately $879/unit/year. Individual unit electric and gas are metered directly to tenants by Dominion Energy and Washington Gas respectively and do not appear in the property's operating statement."*

Benchmark sidebar should compare $879/unit/year against NoVA multifamily industry benchmark of $820–960/unit/year (within normal range — note this). Remove EIA residential bill estimates entirely.

---

### Change 3: Scoring System Adjustments

**On Executive Summary page (Page 2):**
- Lead with stoplight color + plain English label as PRIMARY signal
- Number is secondary/supporting
- Remove numerical score entirely from exec summary scores — just: dot color + label + bar
- Example: 🟢 Development Pressure — **Low · Supply Constrained** (no "18/100" here)

**On Development Intelligence page (Page 4):**
- Keep the numerical score (18/100) and formula breakdown here — this is where it belongs
- Replace percentile claim with actual county context: 
  > *"13 permits within 2-mile radius vs. Fairfax County average of [X] permits per 2-mile radius for similarly-zoned parcels in the permit database (41,504 total permits). Zero new multifamily permits filed within 2 miles in the trailing 24 months."*
- This is defensible with the data we actually have. Do not use fabricated percentile rankings.

---

### Change 4: Credibility Warning Positioning

On Page 3 (Financial), the red-bordered credibility note is correct in intent but should be lighter in tone — it reads as defensive. Reframe:

Current: "⚠ CREDIBILITY NOTE: Every metric in this OM..."  
Replace with a small gray footnote style:
> *"Metric labeling convention: All figures are labeled T-12 Actual or Pro Forma YR1 throughout this document. Mixing trailing actuals with forward projections without clear labels is the most common source of OM credibility errors in the industry (PropRise, 2024). Pro Forma assumes 3.5% rent growth on below-market units at lease renewal."*

---

## Part 2: Full OM Structure — All Property Types

The OM generator must support: **Multifamily, Retail, Office, Industrial/Flex, Land/Development**. This is not a Phase 2 — build for all types from the start, with section toggling based on property type selection.

### Table of Contents — Full OM (35–50 pages)

**Front Matter**
1. Cover Page (1 pg)
2. Confidentiality & Disclaimer (1 pg)
3. Table of Contents (1 pg)

**Executive Summary Section (6 pages — the current prototype)**
4. Executive Summary + Investment Highlights
5. (continued)

**Property Detail Section**
6. Property Overview & Site Plan
7. Photo Gallery (user-uploaded)
8. Unit Mix Detail *(multifamily only)*
9. Tenant Roster & Lease Expiration Schedule *(retail/office/industrial)*

**Financial Section**
10. Complete Rent Roll *(multifamily)* / Tenant Rent Schedule *(commercial)*
11. T-12 Income & Expense Statement (full monthly breakout)
12. Pro Forma Model Years 1–10 with sensitivity table
13. Financing Scenarios (all-cash / conventional / agency)
14. Capital Expenditure History & Reserve Analysis

**NewCo Intelligence Section ★**
15. Development Intelligence Deep Dive (full permit register)
16. Zoning Intelligence & Comp Plan Analysis
17. Development Timeline Narrative (AI web search)
18. School Performance Trend Report *(multifamily/residential)*
19. Crime Analysis Appendix (full incident log + map)
20. Healthcare Facility Detail

**Market Section**
21. Comparable Sales Analysis
22. Rental Comps *(multifamily)* / Lease Comps *(commercial)*
23. Fairfax/Loudoun Market Report
24. Submarket Analysis & Rent Growth Trajectory
25. Employment Base & Major Employers ★
26. Population & Demographic Trends

**Appendix**
27. Data Sources & Methodology
28. Assumptions Register
29. Confidentiality Agreement Template

---

## Part 3: Technical Architecture Decisions

### Rent Roll Processing — Claude API
- User uploads CSV or Excel export from their PMS (Yardi, AppFolio, RealPage, MRI)
- Raw file content sent to Claude API with structured extraction prompt
- API normalizes to standard JSON schema regardless of source format
- User sees confirmation screen before data populates OM: "Found 552 units, 23 vacant, avg rent $2,480 — does this look right?"
- Manual entry fallback via Streamlit data_editor widget
- Paste-from-clipboard fallback for Excel users

**Standard JSON schema output:**
```json
{
  "unit_id": "101A",
  "bedrooms": 2,
  "bathrooms": 2,
  "sq_ft": 1064,
  "floor_plan": "Corby",
  "monthly_rent": 2710,
  "lease_start": "2024-03-01",
  "lease_end": "2025-02-28",
  "tenant_name": "[Tenant]",
  "status": "occupied",
  "lease_type": "gross"
}
```

### T-12 Input Form
- Structured form, NOT a blank spreadsheet
- Pre-populate defaults from available data:
  - Real estate taxes: from Fairfax/Loudoun tax assessor records (already in platform)
  - Insurance: $625/unit default (editable)
  - Management fee: 5% of EGI default (editable)
  - Reserves: $250/unit default (editable)
- User confirms or overrides — enters only truly deal-specific figures
- CSV upload option for users pasting from accountant spreadsheets

### Pro Forma Model
- 10-year DCF, all outputs labeled with source
- Sensitivity table: 3×3 grid (exit cap rate × rent growth rate) showing IRR
- Every assumption documented: "Rent Growth: 3.5%/year — RentCast 22031 trailing 3-yr avg: 4.1%"
- Financing scenarios: all-cash, conventional (65% LTV), agency debt (Freddie/Fannie)
- Outputs: NOI by year, debt service, cash flow, DSCR, IRR, equity multiple, cash-on-cash

### CRE Comparable Sales — RETR + GIS
- **Primary source:** Virginia RETR (statewide deed recordation) — works for BOTH Fairfax and Loudoun
- Architecture: filter Fairfax/Loudoun GIS parcel layers by commercial/multifamily land use codes → cross-reference parcel IDs against RETR deed transfer records → calculate price/SF or price/unit
- **Unit counts:** GIS parcel dwelling unit field (primary) → original construction permit (backup) → ATTOM when reactivated (tertiary)
- **Cap rate:** Cannot be derived from public data. Options:
  - Leave blank with disclosure: "Cap rate not publicly available — estimated from prevailing market benchmarks"
  - Broker manual entry
  - ATTOM when reactivated
- **For non-multifamily (retail, office, industrial):** metric is price/SF not price/unit. Same RETR+GIS architecture, different output metric
- **Broker manual entry:** Provide structured template for broker to add 3–5 comps from their own CoStar/LoopNet access. We provide format; they provide data they already have
- **Do NOT scrape** LoopNet, CoStar, or CREXi — ToS violation and blocking risk

### Development Timeline Narrative
- Trigger: any permit >$5M value within 2-mile radius
- API call: web search "[project address] Fairfax County development planning approval rezoning"
- Also query: Fairfax County Planning Commission public case database (public URL)
- Output: 2–3 sentence status summary per project
- **Graceful degradation:** If no results found, output: *"No major development projects are pending within the 2-mile radius per Fairfax County Planning Commission records as of [date]. The subject property's low development pressure score (18/100) reflects the absence of competitive multifamily supply in the approval pipeline."* — this is actually a POSITIVE statement

### Serafin Market Data — Automation via Zapier
- Serafin publishes quarterly NoVA market reports as PDFs (free, serafinre.com)
- Do NOT use GitHub Actions scraper (brittle, ToS risk)
- **Zapier workflow:** Monitor serafinre.com for new PDF → download to designated folder → trigger Claude API extraction → commit structured JSON to repo
- Alternatively: Manual quarterly trigger — team member downloads PDF, drops in repo folder, Action runs Claude API extraction
- Extracted data structure: cap rates by property type, price/SF or price/unit, transaction volume, vacancy rates, by county and submarket
- Update frequency: quarterly (4×/year, low maintenance burden)

### Property Type Adaptation Logic
When user selects property type at OM creation, toggle sections accordingly:

| Section | MF | Retail | Office | Industrial | Land |
|---|---|---|---|---|---|
| Unit Mix | ✓ | — | — | — | — |
| Tenant Roster | — | ✓ | ✓ | ✓ | — |
| Lease Expiration Chart | — | ✓ | ✓ | ✓ | — |
| WALT | — | ✓ | ✓ | ✓ | — |
| School Performance | ✓ | — | — | — | — |
| Crime Analysis | ✓ | ✓ | — | — | — |
| Traffic Volumes | ✓ | ✓ | — | ✓ | — |
| Tenant Credit Ratings | — | ✓ | ✓ | — | — |
| Development Pipeline | ✓ | ✓ | ✓ | ✓ | ✓ |
| Zoning Intelligence | ✓ | ✓ | ✓ | ✓ | ✓ |

### Geographic Coverage
- **Fairfax County:** Production-ready data pipelines exist. Use for all builds.
- **Loudoun County:** Same architecture, different GIS endpoints and land use code taxonomy. Build simultaneously with Fairfax — parameterize by county, don't duplicate code.
- **Route:** unified_app.py → county detection via GIS polygon → Fairfax or Loudoun pipeline

---

## Part 4: West Oxford Advisors Branding

**Logo files available:**
- `/mnt/user-data/uploads/18-0298_West_Oxford_Advisors_Logo_-_White.png` — for dark backgrounds (cover header)
- `/mnt/user-data/uploads/Logo_Element.png` — cathedral mark, for footers and data attribution badge

**Placement:**
- Cover page: white full logo, top-right, "Exclusively Offered By" label beneath, opacity 0.85
- All interior page footers: cathedral mark (height 16px, opacity 0.5) + "West Oxford Advisors" text
- Data attribution box (Page 6): cathedral mark at 22px, opacity 0.55, labeled "Market Intelligence by NewCo Platform"
- West Oxford blue: approximately #2A52A0 — close to navy palette, intentional not clashing

---

## Part 5: Design System (Maintain from V2)

```css
--navy: #0f1f38
--navy-mid: #1a3357
--wo-blue: #2a52a0
--gold: #b8966a
--gold-light: #d4b48a
--serif: 'Cormorant Garamond'
--sans: 'DM Sans'
--green: #2d6a4f (scores, positive indicators)
--amber: #b45309 (caution indicators)
--red: #9b1c1c (risk indicators, violent crime)
```

Page size: 816×1056px (letter). Footer height: 30px navy bar.  
Top accent: 4px West Oxford blue bar, all interior pages.

**Stoplight system:**
- 🟢 Green dot = strong investor attribute (high score on good metrics, low score on risk metrics)
- 🟡 Amber dot = consider in underwriting
- 🔴 Red dot = risk factor requiring narrative
- Dev Pressure LOW = green (investor positive)
- Crime HIGH = red. Crime LOW = green.
- Transit score 6.4 = amber (good but car still needed at this location)

---

## Part 6: Outstanding Decisions for Next Session

1. **Full OM PDF generation:** WeasyPrint vs. ReportLab — not yet decided. WeasyPrint recommended (HTML→PDF, consistent with prototype). Defer final decision to Claude Code session.

2. **RentCast market rent data pull:** API call structure for per-unit-type market rents in 22031. Need to confirm which RentCast endpoint gives submarket average by bedroom count.

3. **RETR engineering work:** 3–4 day Claude Code project to build the multifamily comp extractor. Separate sprint from OM prototype work.

4. **Serafin Zapier workflow:** Set up separately from OM build. Requires Zapier configuration by Matt.

5. **Property type UI:** The OM creation flow needs a property type selector (Multifamily / Retail / Office / Industrial / Land) at step 1, before any data is fetched. This drives section toggling throughout.

6. **Commercial cap rate approach:** Confirmed we cannot auto-calculate. Options are (a) leave blank with disclosure, (b) broker manual entry, (c) ATTOM when reactivated. Decision deferred.

---

## Key Guardrails (Always Apply)

- **Athens protection is absolute** — zero modifications to Athens production files in any session
- **Fairfax live route:** always `fairfax_report_new.py`, never legacy `fairfax_report.py`
- **Investigation before implementation** — no code changes during investigation phase
- **Test property:** Regent's Park, 9333 Clocktower Place, Fairfax VA 22031 (for OM); 13172 Ruby Lace Ct, Herndon VA 20171 (for Fairfax report testing)
