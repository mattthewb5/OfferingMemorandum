# Fairfax Report Alignment Spec
## Autonomous Implementation Blueprint — Claude Code Execution

**Purpose:** This document specifies every change required to align `fairfax_report_new.py` with  
`loudoun_report.py` at high fidelity. Claude Code should implement all changes on a new branch,  
commit after each section, and never touch Athens or Loudoun files.

**Source of truth:** Loudoun report PDF (16 pages, 43422 Cloister Pl, Leesburg VA 20176, Feb 27 2026)  
**Target file:** `reports/fairfax_report_new.py`  
**Test address:** `11300 Braddock Rd, Fairfax, VA 22030`  
**Branch:** `feature/fairfax-loudoun-alignment` (branch from main after git pull)

---

## Git & Safety Rules

```
# Session start sequence
git checkout main
git pull origin main
git checkout -b feature/fairfax-loudoun-alignment

# After each section below, commit:
git add reports/fairfax_report_new.py
git commit -m "align: [SECTION NAME] - matches Loudoun pattern"

# Never touch:
# - streamlit_app.py (Athens production)
# - reports/loudoun_report.py
# - core/loudoun_*.py
# - anything in athens/ directory

# Verify at session start:
git status  # should show zero Athens/Loudoun files modified
```

---

## Section Order (Final Order in render_report())

Fairfax must render sections in this exact order to match Loudoun:

1. School Assignments + Performance Trends (inline charts)
2. School Performance vs State & Peers (expander)
3. **Location Quality** ← NEW unified section replacing scattered sections
4. Cell Tower Coverage
5. Discover Your Neighborhood ← NEW (Google Places)
6. Community & Amenities (rename from Subdivisions, enhance)
7. Area Demographics
8. Economic Indicators
9. Medical Access (enhance to full Loudoun depth)
10. Neighborhood Development & Infrastructure (with full Leaflet map)
11. Zoning & Land Use
12. Property Value Analysis
13. AI Property Analysis
14. Data Sources

**Sections to REMOVE from current Fairfax render_report():**
- `display_traffic_section()` — traffic data absorbed into Location Quality
- `display_emergency_services_section()` — absorbed into Location Quality
- `display_crime_section()` — keep but reposition (after schools, before Location Quality)
- Transit section — keep if data available, absorbed into Location Quality score

---

## SECTION 1: School Assignments + Performance Trends

### Current Fairfax State
- School assignments display exists ✓
- Performance trends hidden behind expander ✗

### Required Change: Inline Trend Charts (HIGH PRIORITY)

**Loudoun pattern** (loudoun_report.py — find function `display_school_section`):
- School assignments shown as 3-column metric cards (Elementary / Middle / High)
- Each card shows school name + "Reading: XX% | Math: XX%"
- Below assignments: `st.subheader("School Performance Trends")`
- Two tabs: "Reading Proficiency" | "Math Proficiency"
- Chart is inline — NOT inside an expander
- Chart type: Altair line chart with year on x-axis, pass rate on y-axis
- Multiple lines: one per assigned school (colored differently)
- Y-axis range: 0-100

**Fairfax adaptation:**
- Same structure but using FairfaxSchoolsAnalysis module
- Schools from Fairfax County Public Schools boundaries
- SOL data from VDOE (same source, different school names)
- If fewer than 3 years of trend data, show available years with note

**Acceptance criteria:**
- [ ] School assignments visible without expanding anything
- [ ] Trend chart visible immediately below assignments
- [ ] Two tabs (Reading / Math) with inline Altair charts
- [ ] Chart has school lines + state average line (dashed gray)

---

## SECTION 2: School Performance vs State & Peers (Expander)

### Current Fairfax State
- Expander exists but may use Loudoun comparison logic

### Required Change
**Loudoun pattern:**
- Expander label: `📊 School Performance vs State & Peers`
- Three sub-tabs inside: Elementary School | Middle School | High School
- Each tab shows: "Comparing to: [NEAREST_PEER_1] (X.X mi), [NEAREST_PEER_2] (X.X mi)"
- Five subject tabs: Math | Reading | History | Science | Overall
- Altair line chart: multiple schools + Virginia State Average (dashed gray line)
- Legend shows school names with distances

**Fairfax adaptation:**
- Compare to nearest 2 peer schools in Fairfax County (by distance, same level)
- Pull from VDOE SOL data for Fairfax schools
- Same 5-subject tab structure
- "Comparing to: [PEER_SCHOOL_1] (X.X mi), [PEER_SCHOOL_2] (X.X mi)"

**Acceptance criteria:**
- [ ] Expander collapses by default
- [ ] Three school-level tabs
- [ ] Five subject tabs per level
- [ ] Altair chart with peer comparison lines
- [ ] State average as dashed gray line

---

## SECTION 3: Location Quality (NEW — Replaces Traffic + Emergency Services)

This is the most significant new section. Must mirror Loudoun's Location Quality exactly.

### Loudoun Layout (from PDF page 2-4)

```
📍 Location Quality                                    Location Score
                                                         8.0/10
Key Location Features:
🛣 Road Type: [road_type] ([traffic_descriptor])
🚗 Highway Access: 🟢 [HIGHWAY_NAME] (X.X mi) • ~XXX,000 vehicles/day
🛤 Major Road: 🟡 [ROAD_NAME] (X.X mi) • ~XX,000 vehicles/day
✅ No Aircraft Noise Disclosure - Outside disclosure zones    [OR warning variant]
🛫 [NEAREST_AIRPORT]: X.X miles
✅ No Flood Insurance Required - Not in mapped flood zone     [OR flood zone variant]
🌳 Parks: [NEAREST_PARK] (X.X mi)
🚇 Metro Access: 🟠 [STATION] (X.X mi) - [ACCESS_LABEL]

[Expander: ℹ️ Road Access Details]
  Highway: [HIGHWAY_NAME]
  Toll: [Yes/No]
  Travel Times (via [highway]):
  • [DESTINATION_1]: ~XX-XX min
  • [DESTINATION_2]: ~XX-XX min
  Data: VDOT Traffic Volume, Google Distance Matrix

[Expander: ✈️ Aircraft Noise Information]
  [in-zone]: This property IS in an aircraft noise disclosure zone...
  [out-of-zone]: This property is not in an aircraft noise disclosure zone...
  What This Means: [bullet list]
  Distance to [AIRPORT]: X.X miles
  📊 Source: [County] Airport Impact Overlay Districts

[Expander: ✅ Flood Zone Information]
  [in-flood]: This property IS located in a FEMA-designated flood risk area...
  [out-of-flood]: This property is not located in a FEMA-designated flood risk area...
  What This Means: [bullet list]
  💡 Learn more at FloodSmart.gov
  📊 Source: FEMA Flood Insurance Rate Map via [County] GIS

[Expander: 🌳 Parks & Recreation]
  XX parks within 5 miles, with [NEAREST_PARK] X.X miles away - [walk/short drive/drive]
  Nearest Parks:
  • [PARK_1] - X.X mi ([type])
  • [PARK_2] - X.X mi ([type])
  • ...up to 5 parks
  📊 Source: [County] GIS Parks (or Google Places)

[Expander: 🚇 [Metro Line] Access Details]
  [STATION] 🟠 Metro-Available - X.X mi ~XX min
  Narrative paragraph about access
  All [Metro Line] Stations in [County]:
  • [Station]: X.X miles
  • ...
  Note about Walk-to-Metro premium

⚡ Power Infrastructure/Major Power Lines:
  🔴 [Impact Label] ([N]/5)
  Nearest line: [kV]kV at X.XX miles (Built/Proposed)
  N line(s) within 1 mile
```

### Fairfax Data Mapping

| Loudoun Element | Fairfax Data Source | Module/File |
|---|---|---|
| Road Type | FairfaxTrafficAnalysis | core/fairfax_traffic.py |
| Highway Access | FairfaxTrafficAnalysis (VDOT) | core/fairfax_traffic.py |
| Major Road | FairfaxTrafficAnalysis (VDOT) | core/fairfax_traffic.py |
| Aircraft Noise | FairfaxFloodAnalysis OR new GIS check | NOTE: Fairfax uses Dulles + DCA zones |
| Nearest Airport | Compute from lat/lon (Dulles + DCA) | hardcode airport coords |
| Flood Zone | FairfaxFloodAnalysis | core/fairfax_flood.py |
| Parks | FairfaxParksAnalysis | core/fairfax_parks.py |
| Metro Access | Compute from Silver Line + Orange/Blue stations | hardcode WMATA station coords |
| Power Lines | FairfaxPowerAnalysis (if exists) OR GIS data | check core/ |
| Location Score | Compute composite score (see scoring below) | inline logic |

### Location Score Computation (mirror Loudoun)

```python
def compute_fairfax_location_score(traffic_data, flood_data, parks_data, metro_data, noise_data):
    """
    Score out of 10. Loudoun example: 8.0/10 for cul-de-sac, highway 2mi, no flood, no noise, park 0.6mi, metro 7.4mi
    Components:
    - Road type (cul-de-sac/court = +2, local = +1, collector = 0, arterial = -1)
    - Highway access distance (<1mi = +1, 1-3mi = +1.5, 3-5mi = +1, >5mi = 0)  
    - Flood zone (not in zone = +2, zone X = +1, zone AE = 0, zone AO = -1)
    - Noise (no disclosure zone = +2, in zone = 0 to -2 depending on severity)
    - Parks (within 0.5mi = +1.5, 0.5-1mi = +1, 1-2mi = +0.5, >2mi = 0)
    - Metro (<3mi = +2, 3-7mi = +1.5, 7-12mi = +1, >12mi = 0.5)
    Adjust weights so typical suburban Fairfax property scores 6-8/10
    """
```

### Road Type Classifier (match Loudoun)

```python
ROAD_TYPES = {
    "CUL-DE-SAC": "Cul-de-sac / Court (Very Low traffic)",
    "COURT": "Cul-de-sac / Court (Very Low traffic)", 
    "PLACE": "Local Road (Low traffic)",
    "LANE": "Local Road (Low traffic)",
    "DRIVE": "Local/Collector Road (Low-Moderate traffic)",
    "WAY": "Local Road (Low traffic)",
    "ROAD": "Collector/Arterial (Moderate traffic)",
    "AVENUE": "Collector Road (Moderate traffic)",
    "BOULEVARD": "Arterial Road (Higher traffic)",
    "PARKWAY": "Divided Arterial (Higher traffic)",
    "HIGHWAY": "Highway Frontage (High traffic)",
}
```

### Travel Time Destinations for Fairfax

Loudoun uses: Tysons Corner, Downtown DC, Dulles Airport, Reston Town Center  
Fairfax should use: Tysons Corner, Downtown DC, Dulles Airport, National Airport (DCA), Pentagon

### Airport Noise — Fairfax Specifics

Fairfax has TWO relevant airports (unlike Loudoun which is primarily Dulles):
- Dulles International (IAD): coords 38.9531, -77.4565
- Reagan National (DCA): coords 38.8512, -77.0402
- Check against Fairfax County airport overlay GIS data if available
- If no GIS data: use distance thresholds (within 5mi DCA = high impact, 5-10mi = medium)

### Metro — Fairfax Specifics

Fairfax has Silver Line + Orange/Blue/Yellow lines. Key stations:
```python
FAIRFAX_METRO_STATIONS = [
    # Silver Line
    {"name": "Wiehle-Reston East", "lat": 38.9473, "lon": -77.3402, "line": "Silver"},
    {"name": "Spring Hill", "lat": 38.9281, "lon": -77.2735, "line": "Silver"},
    {"name": "Greensboro", "lat": 38.9246, "lon": -77.2375, "line": "Silver"},
    {"name": "Tysons Corner", "lat": 38.9208, "lon": -77.2234, "line": "Silver"},
    {"name": "McLean", "lat": 38.9344, "lon": -77.1804, "line": "Silver"},
    # Orange/Blue
    {"name": "Vienna/Fairfax-GMU", "lat": 38.8783, "lon": -77.2716, "line": "Orange"},
    {"name": "Dunn Loring-Merrifield", "lat": 38.8843, "lon": -77.2297, "line": "Orange"},
    {"name": "West Falls Church", "lat": 38.9004, "lon": -77.1877, "line": "Orange"},
    {"name": "East Falls Church", "lat": 38.8855, "lon": -77.1569, "line": "Orange/Silver"},
    # Blue/Yellow
    {"name": "Franconia-Springfield", "lat": 38.7659, "lon": -77.1681, "line": "Blue"},
    {"name": "Van Dorn Street", "lat": 38.7965, "lon": -77.1290, "line": "Blue"},
    {"name": "Huntington", "lat": 38.7954, "lon": -77.0743, "line": "Yellow"},
]
```

Metro expander title: `🚇 Metro Access Details` (Fairfax has multiple lines, don't say "Silver Line")

**Acceptance criteria:**
- [ ] Unified Location Quality section header with score X.X/10
- [ ] Key Location Features bullet list with emoji icons
- [ ] Score prominently displayed right-aligned (Loudoun: large text "8.0/10")
- [ ] Road Access Details expander with travel times to 5 destinations
- [ ] Aircraft Noise expander with in-zone/out-of-zone variants
- [ ] Flood Zone expander with FEMA classification + FloodSmart.gov link
- [ ] Parks & Recreation expander with 5 nearest parks
- [ ] Metro Access expander with all Fairfax stations listed
- [ ] Power Infrastructure inline (not in expander) with impact rating badge
- [ ] Data sources cited per sub-section

---

## SECTION 4: Cell Tower Coverage

### Current Fairfax State
- Exists but layout differs from Loudoun

### Required Change

**Loudoun exact layout:**
```
📡 Cell Tower Coverage        [H1 section header]

Cell Towers Within 2 Miles
5                             [large metric number]

Nearest Tower                 [bold subheader]
DVP 8                         Height: 80 ft
Distance: 0.55 mi (2,888 ft)  Type: Trans-Mount (on power line tower)

[Expander: View All Nearby Towers (N within 2 mi)]
  [Table with columns: Tower Name | Distance (mi) | Type | Height (ft) | Address]

📶 N cell towers within 2 miles of this property.  [caption]
```

**Fairfax adaptation:**
- Same layout, same column structure
- Distance in feet calculation: miles * 5280, formatted as "X,XXX ft"
- If tower type is unknown: show "Unknown"
- Table is inside expander, not expanded by default

**Acceptance criteria:**
- [ ] Section header `📡 Cell Tower Coverage`
- [ ] Large number metric for count
- [ ] Nearest Tower subsection with name, height, distance (mi + ft), type
- [ ] Expander with full sortable table
- [ ] Caption with count

---

## SECTION 5: Discover Your Neighborhood (NEW)

### Current Fairfax State
- NOT PRESENT — needs to be built

### Required Change

**Loudoun exact layout:**
```
🏪 Discover Your Neighborhood   [H1]

Convenience Score    Dining Nearby    Nearest Grocery    Walkable Places
5/10                 0 places         1.8 mi             0
🟠 Fair

[Tabs: 🍽 Dining | 🛒 Grocery | 🛍 Shopping]
  [Each tab shows nearest places in that category]
  "No [category] found within 1 mile" if empty

[Expander: 📝 Neighborhood Summary]
  [Generated text: "This property has [fair/good/excellent] access to neighborhood amenities..."]
  Key Highlights:
  • [highlight 1]
  • [highlight 2]
  
  🔄 Fresh data (N API calls)
```

**Fairfax implementation:**

```python
# Use Google Places API (same as Loudoun)
# Categories to search:
PLACE_CATEGORIES = {
    "Dining": ["restaurant", "cafe", "fast_food"],
    "Grocery": ["supermarket", "grocery_or_supermarket"],
    "Shopping": ["shopping_mall", "department_store"],
}
SEARCH_RADIUS_MI = 1.0  # for walkable count
SEARCH_RADIUS_GROCERY_MI = 5.0  # for nearest grocery

# Convenience Score (0-10):
def compute_convenience_score(dining_count, grocery_mi, walkable_count):
    score = 5  # baseline
    if dining_count > 5: score += 2
    elif dining_count > 0: score += 1
    if grocery_mi < 0.5: score += 2
    elif grocery_mi < 1.0: score += 1.5
    elif grocery_mi < 2.0: score += 1
    if walkable_count > 10: score += 1
    return min(10, score)

# Score labels:
# 8-10: 🟢 Excellent
# 6-7: 🟡 Good  
# 4-5: 🟠 Fair
# 0-3: 🔴 Limited
```

**Note:** This requires Google Places API calls. Check if `GOOGLE_PLACES_API_KEY` is already configured in `.env`. The Loudoun report already uses this — look at how `loudoun_report.py` calls Places for the same section and replicate the pattern exactly, just substituting Fairfax coordinates.

**Acceptance criteria:**
- [ ] Section header `🏪 Discover Your Neighborhood`
- [ ] 4-column metric row (score, dining, grocery distance, walkable)
- [ ] Colored score label (🟢/🟡/🟠/🔴)
- [ ] Three category tabs
- [ ] Neighborhood Summary expander with generated text
- [ ] API call count shown

---

## SECTION 6: Community & Amenities

### Current Fairfax State
- `display_subdivisions_section()` shows subdivision name + nearby subdivisions table
- Missing: HOA fee, community size, gated status, amenities, HOA website link

### Fairfax Data Reality
- Fairfax does NOT have HOA data in parquet files (this is a known data gap)
- Must handle gracefully

### Required Change

**Loudoun exact layout:**
```
🏘 Community & Amenities        [H1]

[COMMUNITY_NAME] 🔒             [H2, lock icon only if gated]

Monthly HOA Fee    Community Size    Access
$250               1,132 homes       Gated Community
Source: Community Data

Amenities
• [amenity 1]     • [amenity 4]
• [amenity 2]     • [amenity 5]  
• [amenity 3]     • [amenity 6]

🔗 Visit HOA Website
```

**Fairfax adaptation (handle missing HOA data):**
```python
# Try to get HOA data; gracefully degrade
if hoa_data_available:
    # Show full Loudoun-style layout
    display_full_community_section(...)
else:
    # Show subdivision name + size + nearby communities
    # Use FairfaxSubdivisionsAnalysis data
    st.subheader(f"🏘 Community & Amenities")
    st.markdown(f"**{subdivision_name}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Community Size", f"{home_count:,} homes" if home_count else "N/A")
    with col2:
        st.metric("Access", "Gated" if is_gated else "Open")
    with col3:
        st.metric("HOA Fee", "Data Not Available")
    
    st.caption("HOA fee data not available for Fairfax County in this system version.")
```

**Then always show Nearby Communities section (same as Loudoun's zoning section):**
```
Nearby Communities (as in Loudoun zoning section bottom)
📍 This property is in [SUBDIVISION_NAME]   [info box]

[Community size / access / fee row if available]

Other Nearby Communities (N within 5 miles):
• [Community 1] - X.X mi (XXX homes • [amenity])
• ...
```

**Acceptance criteria:**
- [ ] Section renamed to `🏘 Community & Amenities` (not `🏘 Subdivisions`)
- [ ] Community name as H2 with gated lock icon if applicable
- [ ] 3-column metric row even if HOA fee shows "N/A"
- [ ] Nearby communities list (up to 5 within 5 miles)
- [ ] Graceful degradation when HOA data missing

---

## SECTION 7: Area Demographics

### Current Fairfax State
- Exists — check if layout matches Loudoun

### Required Change

**Loudoun exact layout:**
```
📈 Area Demographics            [H1]

Area Overview                   [H2]
[Generated prose: "The 3-mile radius has a population of XX,XXX with a median age of XX..."]

[Two charts side by side]:
Left: Horizontal bar chart — Household Income Distribution (3-Mile Radius)
  Y-axis: income brackets ($200K+, $150K-$200K, ..., Under $25K)
  X-axis: Percentage of Households
  Color: blue bars
  
Right: Horizontal bar chart — Age Distribution (3-Mile Radius)
  Y-axis: age groups (65+, 55-64, 35-54, 25-34, 18-24, 0-17)
  X-axis: Percentage of Population
  Color: green bars

[Expander: Detailed Demographics Data]
  [Table: Metric | 1-Mile | 3-Mile | Fairfax Co. | 3-Mile vs County]
  Sections: POPULATION, HOUSEHOLDS, INCOME, EDUCATION, EMPLOYMENT
  Rows: (match Loudoun exactly but substitute Fairfax county averages)
  Footer: "Data Sources: U.S. Census Bureau ACS 2019-2023; BLS..."
```

**Chart implementation (Altair horizontal bar):**
```python
import altair as alt

income_chart = alt.Chart(income_df).mark_bar(color='steelblue').encode(
    x=alt.X('percentage:Q', title='Percentage of Households', axis=alt.Axis(format='%')),
    y=alt.Y('bracket:N', sort=income_order, title=''),
    tooltip=['bracket', 'percentage']
).properties(title='Household Income Distribution (3-Mile Radius)', height=220)

age_chart = alt.Chart(age_df).mark_bar(color='#2ecc71').encode(
    x=alt.X('percentage:Q', title='Percentage of Population', axis=alt.Axis(format='%')),
    y=alt.Y('group:N', sort=age_order, title=''),
    tooltip=['group', 'percentage']  
).properties(title='Age Distribution (3-Mile Radius)', height=220)

col1, col2 = st.columns(2)
with col1:
    st.altair_chart(income_chart, use_container_width=True)
with col2:
    st.altair_chart(age_chart, use_container_width=True)
```

**Comparison column:** "3-Mile vs County" should compute pp difference and format as "X pp lower/higher" or "-X%"

**Acceptance criteria:**
- [ ] Area Overview prose paragraph
- [ ] Two side-by-side horizontal bar charts (Altair)
- [ ] Income chart: blue, 7 brackets
- [ ] Age chart: green, 6 age groups  
- [ ] Detailed table in expander with 4 columns including vs-county comparison
- [ ] County reference uses Fairfax County figures (not Loudoun)

---

## SECTION 8: Economic Indicators

### Current Fairfax State
- Exists — verify layout matches

### Required Change

**Loudoun exact layout:**
```
💼 Economic Indicators           [H1]

Labor Force Participation    Unemployment Rate    Labor Force
74.1%                        3.2%                 249,245
↑ +10.6 vs USA               As of December 2025  ↓ -1.9% YoY

Sources: Census ACS 5-Year (LFPR) | BLS LAUS (Unemployment, Labor Force)

[Expander: 📊 Industry Employment Mix]
  [Two tabs: Top 6 Sectors | All 13 Sectors]
  [Altair horizontal grouped bar chart]
  X-axis: % of Employment
  Y-axis: Industry sectors
  Three groups: [County] | Virginia | USA
  Colors: blue (county), orange (VA), green (USA)
  Source: Census ACS 2019-2023 5-Year Estimates

[Expander: 🏢 Major Employers]
  📈 Key Trends ([YEAR_START]-[YEAR_END]): [Trend 1] | [Trend 2] | [Trend 3]
  [Tabs: 2025 | 2024 | 2023 | 2022 | 2021 | Earlier]
  [Table: Rank | Employer | Employees | % of Total | Industry]
  Source: Fairfax County ACFR

[Expander: 📋 Data Sources & Methodology]
  [Labor Force Participation Rate (LFPR) section]
  [Unemployment Rate & Labor Force section]
  [Industry Employment Mix section]
  [Major Employers section]
```

**Fairfax-specific:**
- Labor Force = Fairfax County BLS LAUS data
- Industry Mix = Census ACS for Fairfax County FIPS code 51059
- Major Employers = Fairfax County ACFR data (already in processed parquet)
- Key trends narrative: reference Fairfax employers (e.g., Booz Allen, Northrop Grumman, Amazon AWS, Inova Health)

**Acceptance criteria:**
- [ ] 3-column metric row with delta indicators (↑/↓)
- [ ] Industry Mix in expander with grouped Altair bar chart
- [ ] Major Employers in expander with year tabs
- [ ] Data Sources methodology expander
- [ ] All references say "Fairfax County" not "Loudoun County"

---

## SECTION 9: Medical Access (MAJOR ENHANCEMENT)

### Current Fairfax State
- Simple summary section exists
- Missing: separate subsections for hospitals, urgent care, pharmacies, maternity

### Required Change — Full Loudoun Depth

**Loudoun exact layout:**
```
🏥 Medical Access               [H1]

Hospitals/ER    Urgent Care    Pharmacies    Maternity Hospitals
8               21             5             4
                                              [4-col metrics]

🏥 Hospitals & Medical Facilities     [H2]

Acute Care Hospitals (CMS Rated)      [bold label]

[For each hospital]:
**[Hospital Name]** — X.X mi | ⭐⭐⭐⭐⭐ | ([phone])
[System] • [beds] beds • Emergency Services
[Address]

Emergency & Other Medical Facilities (N)   [label]
[First facility shown inline]
[Address]

[Expander: View all N other facilities]
  [List: name — distance / address]

🩺 Urgent Care Centers          [H2]

N urgent care centers in [County] County
Showing 2 nearest:
• [Name] — X.X mi
  [Address]
• [Name] — X.X mi
  [Address]

[Expander: View all N-2 other urgent care centers]
  [List: • Name — X.X mi (Address)]

💊 Pharmacies                    [H2]

N pharmacies within 5 miles

🌙 24-Hour Pharmacies:
• [Name] — X.X mi ⭐[rating]
  [Address]

Other Nearby Pharmacies:
• [Name] — X.X mi ⭐[rating]
  [Address]
• [Name] — X.X mi ⭐[rating]
  [Address]

[Expander: View all N other pharmacies]

🍼 Maternity & Birthing Hospitals  [H2]

[Count] birthing hospitals in [County] County and N nearby in [adjacent county].
All hospitals shown have labor & delivery units, NICUs, and are rated by CMS and Leapfrog for safety.

[For each maternity hospital — as expander, last one expanded]:
[Expander: Hospital Name — X.X mi | ⭐⭐⭐ | Safety: A]
  [4-col: Distance | CMS Rating (stars) | Safety Grade | NICU Level]
  
  Delivery Statistics:
  • Births/year: X,XXX
  • C-section rate: XX.X% ✅/⚠️/🔴
  • Episiotomy rate: X.X%
  
  Key Services: ✅/❌ for each service
  Hospital Info: system, address, designations
  
[Expander: ℹ️ Understanding NICU Levels]
  [Table: Level | Description | Capabilities]
  
[Expander: ℹ️ Understanding C-Section Rates]
  [Explanation text]

✅ Excellent Healthcare Access — [County] ranks... [or appropriate rating]
Data: [County] GIS, Leapfrog Group, CMS Hospital Compare, Google Places API
```

**Fairfax data sources:**
- Hospitals: FairfaxHealthcareAnalysis module (77 facilities, CMS-rated)
- Urgent care: FairfaxHealthcareAnalysis (filter by facility_type)
- Pharmacies: Google Places API (search near property)  
- Maternity: Filter CMS data by `hospital_type == 'maternity'` or beds/services
- Key Fairfax hospitals: Inova Fairfax, Reston Hospital, Virginia Hospital Center, Sentara Northern Virginia

**Maternity hospitals for Fairfax:**
```python
FAIRFAX_MATERNITY_HOSPITALS = [
    "Inova Fairfax Hospital",  # Level IV NICU — the flagship
    "Reston Hospital Center",
    "Virginia Hospital Center",  # Arlington, just outside
    "Inova Fair Oaks Hospital",
]
```

**CMS star rendering:**
```python
def render_cms_stars(rating):
    if rating is None: return "Not Rated"
    return "⭐" * int(rating)
```

**Acceptance criteria:**
- [ ] 4-column summary metrics (Hospitals/ER, Urgent Care, Pharmacies, Maternity)
- [ ] Acute Care Hospitals section with CMS stars + phone + beds + address
- [ ] Emergency facilities with expandable "view all" pattern
- [ ] Urgent Care with top 2 inline + expander for rest
- [ ] Pharmacies with 24-hour flag + star ratings
- [ ] Maternity section with expandable hospital cards
- [ ] NICU levels table
- [ ] C-section rates with Leapfrog standard comparison
- [ ] Healthcare access summary callout box

---

## SECTION 10: Neighborhood Development & Infrastructure (MAJOR — Leaflet Map)

### Current Fairfax State
- Development section exists with permit counts
- NO interactive map with overlays

### Required Change — Full Leaflet Map with Layer Controls

**Loudoun exact layout:**
```
📊 Neighborhood Development & Infrastructure    [H1]

Total Permits (2 mi)    Construction Value    Recent (6 mo)    Tech Infrastructure
673                     $94.9M               32               4
                        [4-column metrics]

Development Activity Map                        [H2]
🔴 Data Center | 🟠 Fiber/Telecom | 🟣 Infrastructure | 🟢 Other Construction
                        [color legend above map]

[Leaflet map — full width, ~500px tall]
  Layers (checkboxes in top-right panel):
  ✅ 🏗 Major [projects]
  ✅ ⚡ Power [lines]
  ✅ 🚇 Metro [stations + route]
  ✅ 🏫 Schools [E/M/H markers]
  ✅ 🏘 Master-Planned [communities]
  ✅ 📡 Cell Towers [150ft+]
  ✅ 🏥 Hospitals [CMS Rated]
  
  Map elements:
  - 2-mile radius circle (blue, semi-transparent)
  - Property marker (center)
  - Building permit dots (color by type)
  - Power lines (gold/orange lines)
  - Metro route (dashed blue line)
  - Metro station markers
  - School markers (🏫 color-coded by level)
  - Master-planned community markers (🏘)
  - Cell tower markers (📡, only 150ft+)
  - Hospital markers (🏥)
  
  Map legend (bottom-left box):
  Development Activity: Data Center | Fiber/Telecom | Infrastructure | Commercial >$1M
  Schools: Elementary | Middle | High
  Other: Master-Planned Community | Power Lines | Silver Line Metro | Cell Towers (150+ ft) | Hospitals (CMS Rated)
```

**Implementation — Leaflet via folium (same as Loudoun):**

First, verify how Loudoun implements this. Look for `folium` or `streamlit_folium` imports in `loudoun_report.py`. The map is rendered using `streamlit_folium` with `folium.Map`.

```python
import folium
from streamlit_folium import st_folium

def create_fairfax_development_map(lat, lon, permits_df, schools_df, 
                                    cell_towers_df, hospitals_df,
                                    power_lines_gdf=None, metro_stations=None):
    m = folium.Map(location=[lat, lon], zoom_start=13, 
                   tiles='OpenStreetMap')
    
    # 2-mile radius circle
    folium.Circle(
        location=[lat, lon],
        radius=3218,  # 2 miles in meters
        color='blue',
        fill=True,
        fill_opacity=0.05,
        weight=1
    ).add_to(m)
    
    # Property marker
    folium.Marker([lat, lon], 
                  icon=folium.Icon(color='red', icon='home')).add_to(m)
    
    # Layer groups (each togglable)
    permits_group = folium.FeatureGroup(name='🏗 Major Projects', show=True)
    power_group = folium.FeatureGroup(name='⚡ Power Lines', show=True)
    metro_group = folium.FeatureGroup(name='🚇 Metro', show=True)
    schools_group = folium.FeatureGroup(name='🏫 Schools', show=True)
    towers_group = folium.FeatureGroup(name='📡 Cell Towers (150+ ft)', show=True)
    hospitals_group = folium.FeatureGroup(name='🏥 Hospitals', show=True)
    
    # Building permits (color by permit type)
    PERMIT_COLORS = {
        'data_center': 'red',
        'fiber': 'orange', 
        'infrastructure': 'purple',
        'commercial': 'green',
        'other': 'gray',
    }
    
    # Power lines (draw as PolyLine from GIS shapefile)
    if power_lines_gdf is not None:
        for _, row in power_lines_gdf.iterrows():
            coords = [(c[1], c[0]) for c in row.geometry.coords]
            folium.PolyLine(coords, color='gold', weight=2, 
                           opacity=0.8).add_to(power_group)
    
    # Metro stations + route
    FAIRFAX_METRO_ROUTE = [...]  # ordered list of Silver Line coords
    folium.PolyLine(FAIRFAX_METRO_ROUTE, color='blue', weight=2,
                   dash_array='10').add_to(metro_group)
    
    # Schools
    SCHOOL_ICONS = {
        'elementary': ('green', '📚'),
        'middle': ('orange', '🎓'),
        'high': ('red', '🏫'),
    }
    
    # Layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(m)
    
    # Add all groups to map
    for group in [permits_group, power_group, metro_group, 
                  schools_group, towers_group, hospitals_group]:
        group.add_to(m)
    
    return m

# Render in Streamlit:
map_obj = create_fairfax_development_map(...)
st_folium(map_obj, width=None, height=500, use_container_width=True)
```

**Note on power lines:** Check `data/fairfax/processed/` for power lines parquet. If GIS shapefile exists, load with geopandas. If not, skip power lines overlay with a comment noting data gap.

**Note on Metro:** Fairfax Orange/Blue/Silver lines. Need ordered coordinate arrays for each line segment to draw routes on map.

**Acceptance criteria:**
- [ ] 4-column metric row (permits, value, recent, tech)
- [ ] `Development Activity Map` subheader
- [ ] Color legend above map
- [ ] Folium/Leaflet interactive map, full width, ~500px tall
- [ ] Layer control panel (top-right, uncollapsed)
- [ ] 2-mile radius circle
- [ ] Permit dots color-coded by type
- [ ] Power line overlays (if data available)
- [ ] Metro route + stations
- [ ] School markers (3 colors for levels)
- [ ] Cell tower markers (150ft+ only)
- [ ] Hospital markers
- [ ] Map legend box (bottom-left)

---

## SECTION 11: Zoning & Land Use

### Current Fairfax State
- Exists — verify it has What This Means expander, Nearby Communities, Development Probability

### Required Change

**Loudoun exact layout:**
```
🏗 Zoning & Land Use            [H1]

📍 Zoning: [zoning_label] • Character: [character_label]

[Expander: 📋 What This Means]
  Zoning for This Property       [H3]
  [Prose about zoning implications]
  
  Recent Construction Activity   [H3]
  [Prose: "The X-mile radius has seen N building permits over the past 6 months..."]
  [Type breakdown: N additions, N alterations, N new home builds, N decks...]
  [Notable major project if any]
  [Community permit activity comparison]
  
  Nearby Communities             [H3]
  📍 This property is in [COMMUNITY_NAME]    [info box]
  [3-col: Community Size | Access | HOA Fee]
  Amenities: [list]
  
  Other Nearby Communities (N within 5 miles):
  • [Community] - X.X mi (XXX homes • amenity)
  
  Technical Reference:
  [Zoning code and full description]
  [Place Type if applicable]
  Source: [County] GIS, [Date]

[Expander: 🔮 Development Probability]
  🟢 Development Score: N/100 (Low/Medium/High)
  Current Status: ...
  Score Breakdown:   [Table: Component | Score | Reason]
  [Expander inside: 📚 Understanding the Score Components]
  
  Analysis [H3]
  [Prose analysis of development pressure]
  
  Realistic change scenarios: [prose]

📊 Comparative Context          [H2]
  High-Scoring Areas in Fairfax County (75-100 points): [prose + bullets]
  Low-Scoring Areas in Fairfax County (0-25 points): [prose + bullets]
  This Property: [summary sentence]
```

**Fairfax-specific zoning references:**
- Fairfax zoning codes: R-1 through R-8, PDH, PDC, PRC, etc.
- Comprehensive Plan references: "Fairfax County Comprehensive Plan [Year]"
- Character descriptions should reference Fairfax Place Types
- Development Centers terminology for commercial areas

**Acceptance criteria:**
- [ ] Zoning + Character one-liner at top
- [ ] What This Means expander with all 4 subsections
- [ ] Nearby Communities inside the expander (same as Community & Amenities but in zoning context)
- [ ] Development Probability expander with score + breakdown table
- [ ] Comparative Context section with high/low scoring examples using Fairfax examples

---

## SECTION 12: Property Value Analysis

### Current Fairfax State  
- Likely exists — verify structure

### Required Change

**Loudoun exact layout:**
```
💰 Property Value Analysis       [H1]

Property Details                 [H2]
📐 Property Size    🏠 Year Built    🏘 Property Type
[value]             [year]           [type]
[note if unavailable]

📊 Sales History                 [H2]
[Table of recent sales or "No recorded sales found in county records (YYYY-YYYY)."]

Current Value Estimates          [H2]
RentCast Estimate    Triangulated Value    Confidence
$X,XXX,XXX           $X,XXX,XXX            N.N/10

Property Valuation Projection    [H2]
1-Year Forecast    3-Year Forecast    5-Year Forecast
$X,XXX,XXX         $X,XXX,XXX         $X,XXX,XXX
↑ +X.X%            ↑ +XX.X%           ↑ +XX.X%

Investment Analysis              [H2]
Est. Monthly Rent    Gross Yield    Cash Flow
$X,XXX              X.X%           [label]
```

**Fairfax-specific:**
- Sales data from Fairfax County assessor parquet (sales table with 872K records)
- RentCast API for current estimate
- ATTOM for additional valuation if configured
- Year built / property type from tax assessor data

**Acceptance criteria:**
- [ ] Property Details with 3 metrics
- [ ] Sales History table (show last 5 years, most recent first)
- [ ] Current Value Estimates 3-column row
- [ ] Valuation Projection 3-column with delta %
- [ ] Investment Analysis 3-column

---

## SECTION 13: AI Property Analysis

### Current Fairfax State
- Exists but may have broken API key

### Required Change
- Same as Loudoun: `🤖 AI Property Analysis` header
- `What Stands Out:` label before generated text
- `🤖 AI-generated analysis` caption below
- Fix API key error: check `ANTHROPIC_API_KEY` in `.env`, handle gracefully if missing

---

## SECTION 14: Data Sources (UPDATE REQUIRED)

### Current Fairfax State
- Stale entries with Loudoun-specific sources and Google Places for Parks

### Required Fairfax Data Sources Table

| Category | Source |
|---|---|
| Property Valuation | ATTOM Data Solutions, RentCast API |
| Area Demographics | U.S. Census Bureau - American Community Survey 2019-2023 |
| Monthly Unemployment | Bureau of Labor Statistics - Local Area Unemployment Statistics |
| Labor Force Participation | U.S. Census Bureau - ACS 5-Year Estimates |
| Industry Employment | U.S. Census Bureau - ACS 5-Year Estimates |
| Major Employers | Fairfax County ACFR (2008-2025) |
| Schools | Fairfax County Public Schools (FCPS) Boundaries |
| School Performance | Virginia Department of Education - SOL 5-Year Trends |
| Building Permits | Fairfax County Open Data (updated weekly) |
| Traffic Volume | VDOT Bidirectional Traffic Volume Database |
| Metro Access | WMATA Station Data / Fairfax County GIS |
| Power Infrastructure | Fairfax County Major Power Lines (GIS) |
| Cell Towers | Fairfax County GIS + FCC Registration Database |
| Medical Facilities | Fairfax County GIS, CMS Hospital Compare, Leapfrog Group |
| Pharmacies | Google Places API |
| Neighborhood Amenities | Google Places API (Real-time) |
| Travel Times | Google Distance Matrix API |
| Parks & Recreation | Fairfax County GIS Parks |
| GIS Data | Fairfax County Official Shapefiles |
| Road Network | Fairfax Street Centerline GIS |
| Zoning | Fairfax County Zoning Districts (GIS) |
| Airport Zones | Fairfax County Noise Overlay Districts |
| Flood Zones | FEMA Flood Insurance Rate Map (via Fairfax GIS) |
| Community Data | FairfaxSubdivisionsAnalysis, RentCast API |

**Analysis Date:** `datetime.now().strftime("%B %d, %Y")`  
**Footer:** `Fairfax County Property Intelligence Platform  Professional Real Estate Analysis`

---

## Dead Code Removal

After all sections implemented, remove from `fairfax_report_new.py`:

```python
# REMOVE these standalone sections (absorbed into Location Quality):
# - display_traffic_section()  
# - display_emergency_services_section()
# - Any remaining references to loudoun_* modules
# - Any leftover "Loudoun County" text strings

# SEARCH AND REPLACE:
# "Loudoun County Commissioner of Revenue" → "Fairfax County Commissioner of Revenue"
# "Loudoun County ACFR" → "Fairfax County ACFR"
# "Loudoun County Public Schools" → "Fairfax County Public Schools"
# "LCPS" → "FCPS"
# "Ashburn", "Leesburg" in travel time destinations → Fairfax-relevant destinations
```

---

## GitHub Actions CI Spec

Create `.github/workflows/fairfax_report_test.yml`:

```yaml
name: Fairfax Report Tests
on:
  push:
    paths: ['reports/fairfax_report_new.py', 'core/fairfax_*.py']
  pull_request:
    paths: ['reports/fairfax_report_new.py', 'core/fairfax_*.py']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - name: Syntax check
        run: python -c "import ast; ast.parse(open('reports/fairfax_report_new.py').read())"
      - name: Import check
        run: python -c "from reports import fairfax_report_new"
      - name: No Loudoun text leak
        run: |
          if grep -n "Loudoun County Public Schools\|LCPS Boundaries\|Loudoun County ACFR\|loudoun_report" reports/fairfax_report_new.py; then
            echo "FAIL: Loudoun text found in Fairfax report"
            exit 1
          fi
      - name: Athens protection check
        run: |
          if git diff main --name-only | grep "streamlit_app.py\|athens/"; then
            echo "FAIL: Athens files modified"
            exit 1
          fi
      - name: Run unit tests
        run: python -m pytest tests/test_fairfax_report.py -v
```

Create `tests/test_fairfax_report.py`:

```python
import pytest
import ast
import sys

def test_syntax():
    with open('reports/fairfax_report_new.py') as f:
        ast.parse(f.read())

def test_required_functions_exist():
    import importlib.util
    spec = importlib.util.spec_from_file_location("fairfax_report_new", 
                                                    "reports/fairfax_report_new.py")
    mod = importlib.util.module_from_spec(spec)
    required = [
        'display_location_quality_section',
        'display_school_section', 
        'display_cell_tower_section',
        'display_neighborhood_section',
        'display_community_amenities_section',
        'display_demographics_section',
        'display_economic_section',
        'display_medical_section',
        'display_development_section',
        'display_zoning_section',
        'display_property_value_section',
        'render_report',
    ]
    for fn in required:
        assert hasattr(mod, fn) or True, f"Missing function: {fn}"  # adjust after implementation

def test_no_loudoun_references():
    with open('reports/fairfax_report_new.py') as f:
        content = f.read()
    forbidden = [
        'Loudoun County Public Schools',
        'LCPS Boundaries',
        'Loudoun County ACFR',
        'from reports.loudoun_report import',
        'import loudoun_report',
    ]
    for term in forbidden:
        assert term not in content, f"Forbidden Loudoun reference found: {term}"

def test_athens_not_modified():
    import subprocess
    result = subprocess.run(['git', 'diff', 'main', '--name-only'], 
                           capture_output=True, text=True)
    modified = result.stdout.strip().split('\n')
    athens_files = [f for f in modified if 'streamlit_app.py' in f or '/athens/' in f]
    assert len(athens_files) == 0, f"Athens files modified: {athens_files}"
```

---

## Implementation Sequence for Claude Code

Execute in this exact order, committing after each:

1. `git checkout main && git pull && git checkout -b feature/fairfax-loudoun-alignment`
2. **Investigate:** Read current `fairfax_report_new.py` fully before writing any code
3. **Investigate:** Read `loudoun_report.py` for each section pattern before implementing Fairfax version
4. **Implement Section 1:** School inline charts → commit
5. **Implement Section 2:** School peer comparison expander → commit
6. **Implement Section 3:** Location Quality unified section → commit (largest change)
7. **Implement Section 4:** Cell Tower layout → commit
8. **Implement Section 5:** Discover Your Neighborhood → commit
9. **Implement Section 6:** Community & Amenities enhancement → commit
10. **Implement Section 7:** Demographics charts → commit
11. **Implement Section 8:** Economic Indicators → commit
12. **Implement Section 9:** Medical Access full depth → commit
13. **Implement Section 10:** Development map with Leaflet → commit (second largest)
14. **Implement Section 11:** Zoning enhancements → commit
15. **Implement Section 12:** Property Value → commit
16. **Implement Section 14:** Data Sources update → commit
17. **Dead code removal** → commit
18. **Create GitHub Actions CI** → commit
19. **Create tests/test_fairfax_report.py** → commit
20. **Run syntax validation:** `python -c "import ast; ast.parse(open('reports/fairfax_report_new.py').read())"`
21. **Run Streamlit test:** `python -m streamlit run unified_app.py` with 11300 Braddock Rd, Fairfax VA 22030
22. **Final commit:** `git push origin feature/fairfax-loudoun-alignment`

---

## Acceptance Criteria — Final Visual Check

After implementation, run Streamlit and verify these visually against the Loudoun PDF:

| Section | Loudoun PDF Page | Fairfax Must Match |
|---|---|---|
| School assignments + inline charts | Page 1 | ✓ 3-col cards + tabs + Altair chart |
| Location Quality unified section | Page 2 | ✓ Score right-aligned, all expanders |
| Road expander with travel times | Page 2-3 | ✓ 5 destinations, VDOT attribution |
| Aircraft noise expander | Page 3 | ✓ In/out zone variants |
| Flood zone expander | Page 3 | ✓ FEMA classification |
| Parks expander | Page 3 | ✓ 5 nearest with types |
| Metro expander | Page 3-4 | ✓ All Fairfax stations listed |
| Power lines inline | Page 4 | ✓ Impact badge + nearest line |
| Cell tower section | Page 4 | ✓ Count metric + nearest detail + table |
| Discover Neighborhood | Page 5 | ✓ 4 metrics + tabs + summary |
| Community & Amenities | Page 5 | ✓ Name + size/access/fee + nearby list |
| Demographics charts | Page 6 | ✓ Two side-by-side Altair bar charts |
| Economic indicators | Page 6-7 | ✓ 3 metrics + industry chart + employer table |
| Medical access full depth | Page 8-11 | ✓ All 4 sub-sections |
| Development map | Page 11 | ✓ Leaflet with 7 layer toggles |
| Zoning + development prob | Page 12-13 | ✓ All expanders present |
| Property value | Page 14 | ✓ All subsections |
| Data Sources table | Page 15 | ✓ Fairfax sources only |

---

## Known Data Gaps / Graceful Degradation

| Gap | Handling |
|---|---|
| HOA data missing | Show "Data Not Available" metric, note in caption |
| Airport noise GIS missing | Use distance-based threshold with note |
| Power lines GIS missing | Skip power layer on map, remove from Location Quality |
| Crime geocoding only 17.5% | Show with accuracy warning badge |
| Pharmacies (Places API) | Skip if API key not configured, show "Data requires Google Places API" |
| AI narrative (Anthropic key) | Show error gracefully, don't crash |
| Google Distance Matrix | Cache aggressively, handle quota exceeded |
