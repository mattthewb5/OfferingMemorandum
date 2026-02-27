# Fairfax Report Phase 2 — Bug Fixes, Restorations & Map Enhancements
## Autonomous Implementation Blueprint — Claude Code Execution

**Branch from:** `main` (Phase 1 already merged)
**Target file:** `reports/fairfax_report_new.py`
**Test addresses:**
- `13172 Ruby Lace Ct, Herndon, VA 20171` (used in Phase 1 testing — has known bugs)
- `11300 Braddock Rd, Fairfax, VA 22030` (secondary test)

**New branch:** `feature/fairfax-phase2-fixes`

---

## Git & Safety Rules

```bash
git checkout main
git pull origin main
git checkout -b feature/fairfax-phase2-fixes

# NEVER touch:
# - streamlit_app.py (Athens production)
# - reports/loudoun_report.py
# - core/loudoun_*.py
# - anything in athens/ directory

# Verify at session start:
git status  # must show zero Athens/Loudoun files modified
```

---

## STEP 0: Investigation Phase (NO CODE CHANGES)

Read and report on the following before touching any code. Present findings as a numbered list.

### 0A. Road/Traffic Classifier Investigation
- Find `FairfaxTrafficAnalysis` in `core/fairfax_traffic.py`
- Understand how it returns nearest roads: what fields are returned, how results are sorted
- For test address 13172 Ruby Lace Ct (lat ~38.895, lon ~-77.388), print what roads are in the result set — specifically: are Fairfax County Parkway and Route 28 present?
- Identify why the classifier is picking Ruby Lace Ct (2,000 ADT) as "highway access" instead of filtering for high-ADT roads
- Check if there is an ADT threshold filter applied before selecting "nearest highway" vs "nearest major road"

### 0B. Metro GIS Data Investigation
- Search `data/fairfax/` and `data/` for any metro-related files: `.parquet`, `.geojson`, `.shp`, `.csv` containing "metro", "wmata", "silver", "orange", "blue" in filename or path
- Check if Loudoun has metro line geometry files and where they live
- Report: do we have metro LINE geometry (polylines) or only STATION points?
- Check `core/fairfax_transit.py` for what metro data it uses

### 0C. Pharmacy Section Investigation
- Find where pharmacies are displayed in `fairfax_report_new.py`
- Find where `GOOGLE_PLACES_API_KEY` is checked for the pharmacy section
- Compare: how does `display_neighborhood_section` (working) access Google Places vs how the pharmacy section accesses it
- Identify exact failure point — is it a missing key check, wrong env variable name, or different code path?

### 0D. AI Property Analysis Investigation
- Find the AI narrative section in `fairfax_report_new.py`
- Find where `ANTHROPIC_API_KEY` is loaded (which `.env` file, which config)
- The error shows 401 invalid key — determine if this is a hardcoded key, env variable, or config file issue
- Check if the key variable name matches what's in the `.env` file exactly
- Report the exact variable name used in code vs what's in `.env`

### 0E. Crime Module Investigation
- Find `FairfaxCrimeAnalysis` in `core/fairfax_crime.py` — confirm it exists
- Search `fairfax_report_new.py` for any crime-related function calls — were they removed or were they never wired?
- Find where crime was displayed in the old `fairfax_report.py` (legacy) for reference
- Report: what does `FairfaxCrimeAnalysis` return? What display function existed?

### 0F. Maternity Data Investigation
- Search `data/loudoun/` for how maternity hospital data is stored (filename, format, columns)
- Search `data/fairfax/` for any existing maternity or hospital data files
- Check `core/fairfax_healthcare.py` — does it have a maternity method? What does it expect?
- Report the exact file path and column schema used by Loudoun's maternity section

### 0G. Demographics "Loudoun County" Reference
- Search `fairfax_report_new.py` for "Loudoun County" in the detailed demographics table
- Report exact line number and context

### 0H. Cell Tower Address/Location Data
- Check `FairfaxCellTowerAnalysis` return data — does it include lat/lon for each tower?
- If yes, we can reverse-display as coordinates or use Google reverse geocoding
- Report what location fields are available per tower record

**After investigation, present all findings. Wait — do not write any code until findings are presented.**

---

## STEP 1: Fix Road Type & Traffic Classifier (HIGH PRIORITY)

**Problem:** The classifier picks Ruby Lace Ct (the property's own street, 2,000 ADT) as "highway access" and "major road." Fairfax County Parkway is the nearest major road and Route 28 (VA-28) is the nearest highway. The location score is stuck at 10/10 as a result.

**Fix logic:**

```python
# Road classification by ADT threshold (apply BEFORE distance sort)
# Highway: ADT >= 40,000 (interstates, primary state routes)
# Major road: ADT >= 10,000 (county parkways, secondary routes)  
# Collector: ADT 3,000-9,999
# Local: ADT < 3,000

def classify_road_by_adt(adt):
    if adt >= 40000: return "Highway"
    if adt >= 10000: return "Major Road"
    if adt >= 3000: return "Collector"
    return "Local"

# When selecting "nearest highway" — filter results WHERE adt >= 40000, THEN sort by distance
# When selecting "nearest major road" — filter results WHERE adt >= 10000, THEN sort by distance
# Do NOT just take the nearest road regardless of ADT
```

**Road Type label** (what the property's own street is):
- Look up the street suffix of the property address
- CUL-DE-SAC / COURT / PLACE / WAY → "Cul-de-sac / Court (Very Low traffic)"
- DRIVE / CIRCLE / LANE → "Local Road (Low traffic)"
- ROAD / AVENUE / STREET → "Collector Road (Moderate traffic)"
- BOULEVARD / PARKWAY → "Arterial Road (Higher traffic)"
- HIGHWAY / PIKE / FREEWAY → "Highway (High traffic)"

The road type label should describe the **property's street**, not the nearest road in the VDOT database.

**Location Score fix** — after fixing road detection, recalibrate scoring:
```python
def compute_location_score(road_type, highway_mi, flood_zone, noise_zone, 
                            park_mi, metro_mi):
    score = 5.0  # baseline
    
    # Road type (property's own street)
    road_bonuses = {
        "cul-de-sac": 2.0, "court": 2.0, "place": 1.5,
        "local": 1.0, "collector": 0.0, "arterial": -0.5, "highway": -1.0
    }
    score += road_bonuses.get(road_type.lower(), 0)
    
    # Highway ACCESS distance (nearest highway >= 40k ADT)
    if highway_mi < 1: score += 0.5    # too close is bad
    elif highway_mi < 3: score += 1.5  # sweet spot
    elif highway_mi < 5: score += 1.0
    else: score += 0.5
    
    # Flood zone
    if not flood_zone or flood_zone == "X": score += 1.5
    elif flood_zone in ["AE", "A"]: score -= 1.0
    
    # Aircraft noise
    if not noise_zone: score += 1.0
    else: score -= 0.5  # proximity warning, not in disclosure zone
    
    # Parks
    if park_mi < 0.25: score += 1.5
    elif park_mi < 0.5: score += 1.0
    elif park_mi < 1.0: score += 0.5
    
    # Metro
    if metro_mi < 1: score += 2.0
    elif metro_mi < 3: score += 1.5
    elif metro_mi < 7: score += 1.0
    elif metro_mi < 12: score += 0.5
    
    return round(min(10.0, max(1.0, score)), 1)
```

**Acceptance criteria:**
- [ ] Ruby Lace Ct test: Road Type shows "Cul-de-sac / Court (Very Low traffic)" NOT "Collector/Arterial"
- [ ] Highway Access shows Fairfax County Parkway or Route 28, NOT Ruby Lace Ct
- [ ] ADT shown for highway matches VDOT data for that actual road
- [ ] Location score is NOT 10.0/10 for a suburban cul-de-sac near an airport noise zone
- [ ] Score is in reasonable range (6-8/10 for typical suburban Fairfax)

**Commit:** `fix: road classifier uses ADT threshold filter, location score recalibrated`

---

## STEP 2: Fix Travel Times

**Problem:** Travel times show destination labels but no actual minutes. The Google Distance Matrix API call is either not executing or the result is not being displayed.

**Fix:**
- Find the travel times code in the Road Access Details expander
- Check if `GOOGLE_MAPS_API_KEY` or `GOOGLE_DISTANCE_MATRIX_API_KEY` is properly loaded
- The Loudoun report has working travel times — find that function and replicate exactly for Fairfax
- Destinations for Fairfax (replace any "Fairfax" label that was in the header):

```python
FAIRFAX_TRAVEL_DESTINATIONS = [
    ("Tysons Corner", "Tysons Corner Center, McLean, VA"),
    ("Downtown DC", "Washington, DC"),
    ("Dulles Airport", "Washington Dulles International Airport, VA"),
    ("Reagan National", "Ronald Reagan Washington National Airport, VA"),
    ("Pentagon", "The Pentagon, Arlington, VA"),
]
```

- Remove "Travel Time Destinations (Fairfax):" label — just show "Travel Times:" 
- Format as Loudoun does: `• Tysons Corner: ~XX-XX min`
- If API call fails gracefully: show "Travel times unavailable" rather than empty bullet list

**Acceptance criteria:**
- [ ] Travel times show actual minutes for all 5 destinations
- [ ] No "(Fairfax)" in the label
- [ ] Graceful fallback if API unavailable

**Commit:** `fix: travel times wired to Distance Matrix API with Fairfax destinations`

---

## STEP 3: Fix Demographics "Loudoun County" Reference

**From investigation 0G:** Find and replace the exact line where the detailed demographics table references "Loudoun County" instead of "Fairfax County."

Simple text replacement — one line fix.

**Acceptance criteria:**
- [ ] Detailed Demographics table shows "Fairfax Co." not "Loudoun Co." in comparison column header

**Commit:** `fix: demographics table comparison column references Fairfax County`

---

## STEP 4: Fix Cell Tower Display (Names + Location)

**Problem:** All tower names show "Unknown." The table has a Name column with no useful data.

**Fix based on investigation 0H:**
- If towers have lat/lon: add a "Location" column showing formatted coordinates or nearest address if reverse geocode is available
- If all names are null/unknown: **remove the Tower Name column entirely** from both the Nearest Tower display and the full table
- Replace with whatever identifying info IS available: Type + Height is sufficient for "Nearest Tower" display
- Full table columns when names unknown: `Distance (mi) | Type | Height (ft) | City` (City column was visible in Phase 1 output — use it)

```python
# If > 80% of tower names are null/unknown, drop the name column
name_coverage = towers_df['name'].notna().mean()
show_name_col = name_coverage > 0.2

# Always show city if available
cols = ['distance_mi', 'type', 'height_ft']
if show_name_col: cols.insert(0, 'name')
if 'city' in towers_df.columns: cols.append('city')
if 'lat' in towers_df.columns and 'lon' in towers_df.columns:
    towers_df['coords'] = towers_df.apply(
        lambda r: f"{r['lat']:.4f}, {r['lon']:.4f}", axis=1)
    cols.append('coords')
```

**Acceptance criteria:**
- [ ] No "Unknown" tower name column when names are unavailable
- [ ] Nearest Tower section still shows distance (mi + ft), height, type
- [ ] Full table shows City column
- [ ] Coordinates shown if lat/lon available in data

**Commit:** `fix: cell tower display removes empty name column, adds available location data`

---

## STEP 5: Fix Pharmacies Section

**From investigation 0C:** Identify why pharmacies fail despite Google Places working for Discover Your Neighborhood.

**Most likely fix:** The pharmacy section checks for a different env variable name or has a separate API key check that fails before the call. Match exactly how `display_neighborhood_section` loads the Google Places key.

```python
# Pattern to match from working neighborhood section:
import os
google_api_key = os.getenv('GOOGLE_PLACES_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
if not google_api_key:
    st.info("Pharmacy data requires Google Places API. Configure GOOGLE_PLACES_API_KEY in .env.")
    return
```

Search for pharmacies within 5 miles of property using Places API:
- Type: `pharmacy`
- Show: name, distance, rating, 24-hour flag, address
- Match Loudoun layout: 24-hour pharmacies first, then others, "View all N" expander

**Acceptance criteria:**
- [ ] Pharmacies section shows real data (not "requires API key" message)
- [ ] 24-hour pharmacies flagged with 🌙
- [ ] Star ratings shown
- [ ] Matches Loudoun pharmacy section layout

**Commit:** `fix: pharmacy section uses consistent Google Places API key loading`

---

## STEP 6: Restore Crime & Safety Module

**From investigation 0E:** Re-wire `FairfaxCrimeAnalysis` back into `render_report()`.

**Section placement:** After School sections, before Location Quality (same position it had before Phase 1 alignment displaced it).

**Display function** — recreate matching Loudoun's crime section style if it was deleted, or restore from legacy `fairfax_report.py`:

```python
def display_crime_section(lat, lon, crime_data):
    st.header("🚨 Crime & Safety")
    
    if crime_data is None or crime_data.get('error'):
        st.info("Crime data unavailable for this location.")
        return
    
    # Summary metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Crime Index", crime_data.get('crime_index', 'N/A'))
    with col2:
        st.metric("Incidents (1 mi)", crime_data.get('incidents_1mi', 0))
    with col3:
        st.metric("Incidents (3 mi)", crime_data.get('incidents_3mi', 0))
    with col4:
        st.metric("vs County Avg", crime_data.get('vs_county', 'N/A'))
    
    # Crime type breakdown
    if 'by_type' in crime_data:
        st.subheader("Incidents by Type")
        # horizontal bar chart, Altair, matching demographics chart style
    
    # Nearest incidents table
    if 'nearest' in crime_data:
        with st.expander("📋 Recent Nearby Incidents"):
            st.dataframe(crime_data['nearest'])
    
    st.caption("Data: Fairfax County Police Department (geocoded incidents)")
```

**Add Crime to Data Sources table:**
```python
{"Category": "Crime & Safety", 
 "Source": "Fairfax County Police Department — Incident Reports"},
```

**Acceptance criteria:**
- [ ] Crime & Safety section appears in report after schools
- [ ] Summary metrics (crime index, incident counts, vs county avg)
- [ ] Incident type breakdown chart
- [ ] Crime data in Data Sources table
- [ ] Section renders gracefully when data unavailable

**Commit:** `restore: crime and safety module wired back into render_report`

---

## STEP 7: Rebuild Maternity Hospital Data

**From investigation 0F:** Determine Loudoun's maternity data file format, then build equivalent Fairfax file.

**If Loudoun uses a CSV/parquet file**, build `data/fairfax/healthcare/fairfax_maternity_hospitals.csv` (or .parquet) with the same schema.

**Fairfax maternity hospitals** (research these — find CMS ratings, Leapfrog grades, NICU levels, delivery stats from public sources):

```python
FAIRFAX_MATERNITY_HOSPITALS = [
    {
        "name": "Inova Fairfax Hospital",
        "address": "3300 Gallows Rd, Falls Church, VA 22042",
        "system": "Inova Health System",
        "distance_placeholder": True,  # compute at runtime from lat/lon
        "cms_rating": 4,
        "leapfrog_safety": "A",
        "nicu_level": "IV",  # Northern Virginia's only Level IV
        "beds": 923,
        "births_per_year": 6800,
        "csection_rate": 24.1,
        "episiotomy_rate": 1.8,
        "services": ["Certified Nurse-Midwives", "VBAC", 
                     "Lactation support", "Doulas welcome"],
        "designations": ["Magnet Recognized", "CMS Birthing-Friendly",
                         "Leapfrog Top Hospital"],
        "lat": 38.8521, "lon": -77.2217,
        "phone": "(703) 776-4001",
        "county": "Fairfax"
    },
    {
        "name": "Reston Hospital Center",
        "address": "1850 Town Center Pkwy, Reston, VA 20190",
        "system": "HCA Virginia",
        "cms_rating": 3,
        "leapfrog_safety": "A",
        "nicu_level": "II",
        "beds": 199,
        "births_per_year": 2100,
        "csection_rate": 26.3,
        "episiotomy_rate": 2.1,
        "services": ["VBAC", "Lactation support"],
        "designations": ["CMS Birthing-Friendly"],
        "lat": 38.9582, "lon": -77.3574,
        "phone": "(703) 689-9000",
        "county": "Fairfax"
    },
    {
        "name": "Virginia Hospital Center",
        "address": "1701 N George Mason Dr, Arlington, VA 22205",
        "system": "Virginia Hospital Center",
        "cms_rating": 4,
        "leapfrog_safety": "A",
        "nicu_level": "III",
        "beds": 342,
        "births_per_year": 3200,
        "csection_rate": 22.8,
        "episiotomy_rate": 1.2,
        "services": ["Certified Nurse-Midwives", "VBAC", 
                     "Lactation support", "Doulas welcome"],
        "designations": ["Magnet Recognized", "CMS Birthing-Friendly"],
        "lat": 38.8849, "lon": -77.1232,
        "phone": "(703) 558-5000",
        "county": "Arlington"
    },
    {
        "name": "Inova Fair Oaks Hospital",
        "address": "3600 Joseph Siewick Dr, Fairfax, VA 22033",
        "system": "Inova Health System",
        "cms_rating": 5,
        "leapfrog_safety": "A",
        "leapfrog_consecutive_as": 27,
        "nicu_level": "III",
        "beds": 182,
        "births_per_year": 3461,
        "csection_rate": 23.0,
        "episiotomy_rate": 2.9,
        "services": ["Certified Nurse-Midwives", "VBAC", 
                     "Lactation support", "Doulas welcome"],
        "designations": ["Magnet Recognized", "CMS Birthing-Friendly",
                         "Leapfrog Top Hospital 2022-2025"],
        "lat": 38.8754, "lon": -77.3847,
        "phone": "(703) 391-3600",
        "county": "Fairfax"
    },
]
```

**Note:** Verify all stats against current CMS Hospital Compare and Leapfrog data before writing the file. These are estimates — do not hardcode without verification. If public sources confirm different numbers, use those.

**Display:** Match Loudoun's maternity section exactly:
- Each hospital as an expander
- 4-column metrics: Distance | CMS Stars | Safety Grade | NICU Level
- Delivery Statistics, Key Services, Hospital Info sections
- NICU levels reference table
- C-section rates reference table

**Acceptance criteria:**
- [ ] Maternity data file exists at correct path
- [ ] All 4 hospitals display with expandable cards
- [ ] CMS stars rendered correctly
- [ ] NICU level explainer table present
- [ ] C-section rate color coding (✅/⚠️/🔴)

**Commit:** `restore: maternity hospital data file and display matching Loudoun format`

---

## STEP 8: Development Map Enhancements

### 8A: Add Metro Line Routes to Map

**From investigation 0B:** Use whatever line geometry exists in the repo. If only station points exist, draw straight-line segments between consecutive stations as an approximation (acceptable for this use case).

```python
# If line GeoJSON/shapefile found — use it directly as folium GeoJson layer
# If only station points — connect them in order:

FAIRFAX_METRO_LINES = {
    "Silver": {
        "color": "#A0522D",  # silver/brown
        "stations_ordered": [
            (38.9473, -77.3402),  # Wiehle-Reston East
            (38.9281, -77.2735),  # Spring Hill
            (38.9246, -77.2375),  # Greensboro
            (38.9208, -77.2234),  # Tysons Corner
            (38.9344, -77.1804),  # McLean
            # continues to DC...
        ]
    },
    "Orange": {
        "color": "#FF7700",
        "stations_ordered": [
            (38.8783, -77.2716),  # Vienna/Fairfax-GMU
            (38.8843, -77.2297),  # Dunn Loring
            (38.9004, -77.1877),  # West Falls Church
            (38.8855, -77.1569),  # East Falls Church
        ]
    },
    "Blue": {
        "color": "#0000FF",
        "stations_ordered": [
            (38.7659, -77.1681),  # Franconia-Springfield
            (38.7965, -77.1290),  # Van Dorn Street
        ]
    },
    "Yellow": {
        "color": "#FFD700",
        "stations_ordered": [
            (38.7954, -77.0743),  # Huntington
        ]
    },
}

# Add to metro_group FeatureGroup:
for line_name, line_data in FAIRFAX_METRO_LINES.items():
    folium.PolyLine(
        locations=line_data["stations_ordered"],
        color=line_data["color"],
        weight=3,
        opacity=0.8,
        dash_array=None,  # solid line for metro routes
        tooltip=f"{line_name} Line"
    ).add_to(metro_group)
```

**If repo has actual route geometry files** (preferred): load with geopandas and add as GeoJson layer — will follow actual track alignment rather than straight segments.

### 8B: Add Crime Incidents to Map

```python
crime_group = folium.FeatureGroup(name='🚨 Crime Incidents', show=False)
# Default show=False — don't clutter map by default, user opts in

CRIME_COLORS = {
    'theft': '#FF8C00',
    'burglary': '#FF4500', 
    'assault': '#DC143C',
    'vandalism': '#9370DB',
    'vehicle': '#4682B4',
    'other': '#808080',
}

# Only show crimes within the search radius (2 or 3 miles)
# Use small circle markers, semi-transparent
for _, crime in crimes_in_radius.iterrows():
    crime_type = crime.get('offense_category', 'other').lower()
    color = CRIME_COLORS.get(crime_type, '#808080')
    folium.CircleMarker(
        location=[crime['lat'], crime['lon']],
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.6,
        popup=f"{crime.get('offense_description', 'Incident')}<br>{crime.get('date', '')}",
        tooltip=crime.get('offense_category', 'Incident')
    ).add_to(crime_group)

crime_group.add_to(m)
```

**Add to map legend:**
```
🚨 Crime Incidents (toggle on)
  🟠 Theft  🔴 Burglary  ❤️ Assault  🟣 Vandalism  🔵 Vehicle  ⚫ Other
```

### 8C: Add Electric/Gas Lines to Map

```python
utilities_group = folium.FeatureGroup(name='⚡ Electric/Gas Lines', show=True)

# Check data/fairfax/processed/ for power lines parquet
# Check data/fairfax/ for any GIS utility line files

# Power lines (existing from Phase 1):
if power_lines_gdf is not None:
    for _, row in power_lines_gdf.iterrows():
        voltage = row.get('voltage', 0)
        color = '#FF0000' if voltage >= 230 else '#FFA500' if voltage >= 69 else '#FFD700'
        weight = 3 if voltage >= 230 else 2
        coords = extract_line_coords(row.geometry)
        folium.PolyLine(
            coords, color=color, weight=weight, opacity=0.7,
            tooltip=f"{voltage}kV Power Line"
        ).add_to(utilities_group)

# Gas lines (if data exists):
if gas_lines_gdf is not None:
    for _, row in gas_lines_gdf.iterrows():
        coords = extract_line_coords(row.geometry)
        folium.PolyLine(
            coords, color='#FF6B35', weight=2, 
            opacity=0.6, dash_array='5',
            tooltip="Gas Line"
        ).add_to(utilities_group)

utilities_group.add_to(m)
```

**Layer control label:** `⚡ Electric/Gas Lines`

**Map legend additions:**
```
⚡ Power Lines: ━━ 230kV+ (red)  ━━ 69-229kV (orange)  ━━ <69kV (yellow)
🟠 Gas Lines (dashed orange)
```

### 8D: Update Layer Control Order

Final layer control order (top to bottom in panel):
1. 🏗 Major Projects
2. ⚡ Electric/Gas Lines  
3. 🚇 Metro (stations + lines)
4. 🏫 Schools
5. 🏘 Master-Planned Communities
6. 📡 Cell Towers (150+ ft)
7. 🏥 Hospitals
8. 🚨 Crime Incidents (default OFF)

**Acceptance criteria:**
- [ ] Metro lines drawn on map connecting stations (color-coded by line)
- [ ] Crime incidents as toggleable layer (default off)
- [ ] Electric/gas lines visible as colored polylines
- [ ] Layer control panel updated with all new layers
- [ ] Map legend updated

**Commit:** `feat: development map adds metro lines, crime incidents, electric/gas layers`

---

## STEP 9: Fix Development Pressure Score

**Problem:** 84/100 for an established residential subdivision (EMERALD CHASE) is too high. The radius expanded to 3 miles and picked up Dulles Corridor commercial activity that doesn't reflect the property's neighborhood.

**Fix:**
- When radius is expanded from 2mi to 3mi due to low permit count, apply a **dampening factor** to the score (commercial activity 3 miles away in a different planning district should not pressure a residential property)
- Separate scoring for residential vs commercial permits — a residential subdivision with homeowner renovations should score differently than an area with active commercial development
- Check if the planning district assignment (`Dulles Route 28 Corridor Suburban Center`) is the property's actual district or a nearby one

```python
def compute_development_pressure(permits_df, search_radius_mi, 
                                 property_planning_district):
    base_score = calculate_raw_score(permits_df)
    
    # Dampening when radius was expanded
    if search_radius_mi > 2:
        radius_penalty = 0.7  # reduce score when using expanded radius
        base_score *= radius_penalty
    
    # Filter: only count permits in SAME planning district as property
    # for primary score; permits in adjacent districts are secondary
    same_district = permits_df[
        permits_df['planning_district'] == property_planning_district
    ]
    adjacent_district = permits_df[
        permits_df['planning_district'] != property_planning_district
    ]
    
    # Weight same-district permits more heavily
    score = (len(same_district) * 1.0 + len(adjacent_district) * 0.3) / normalizer
    
    return min(100, round(score))
```

**Acceptance criteria:**
- [ ] Established residential subdivision without nearby commercial scores < 50
- [ ] Score narrative correctly reflects "expanded radius" caveat when applicable
- [ ] Dulles Corridor commercial activity doesn't inflate suburban residential scores

**Commit:** `fix: development pressure score dampened for expanded radius and cross-district permits`

---

## STEP 10: Fix GitHub Actions CI

**Problem:** CI fails on "No Loudoun text leak" check because it catches developer comments like `# Template: loudoun_report.py`.

**Fix the grep to exclude comment lines:**

```yaml
# In .github/workflows/fairfax_report_test.yml
- name: No Loudoun text leak
  run: |
    # Exclude comment-only lines (lines where first non-whitespace is #)
    if grep -n "Loudoun County Public Schools\|LCPS Boundaries\|Loudoun County ACFR\|from reports.loudoun_report import\|import loudoun_report" reports/fairfax_report_new.py | grep -v "^\s*[0-9]*:\s*#"; then
      echo "FAIL: Loudoun text found in non-comment code"
      exit 1
    fi
```

Also fix the unit test that checks for forbidden terms — same exclusion for comment lines.

**Acceptance criteria:**
- [ ] CI passes on a clean push to the branch
- [ ] Developer comments referencing Loudoun as template don't trigger failure
- [ ] Actual Loudoun imports or user-visible text still fail correctly

**Commit:** `fix: CI Loudoun text leak check excludes developer comments`

---

## STEP 11: AI Property Analysis — Troubleshoot & Improve Error Handling

**From investigation 0D:** The 401 error means the Anthropic API key is invalid or missing.

**Code fix** (regardless of key status):
```python
def generate_ai_narrative(property_data):
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        return None, "AI analysis unavailable: ANTHROPIC_API_KEY not configured in .env"
    
    if api_key.startswith('sk-ant-'):
        # Key format looks valid, attempt call
        try:
            # ... existing API call ...
        except anthropic.AuthenticationError:
            return None, "AI analysis unavailable: API key authentication failed. Check ANTHROPIC_API_KEY in .env"
        except Exception as e:
            return None, f"AI analysis unavailable: {str(e)}"
    else:
        return None, "AI analysis unavailable: ANTHROPIC_API_KEY format invalid"

# Display:
narrative, error = generate_ai_narrative(property_data)
if narrative:
    st.markdown(f"**What Stands Out:** {narrative}")
    st.caption("🤖 AI-generated analysis")
elif error:
    st.info("🤖 AI Property Analysis temporarily unavailable.")
    # Don't show raw error JSON to users — log it instead
    print(f"[AI Narrative Error] {error}")  # server-side log only
```

**Note:** The actual API key fix requires Matt to update `.env` with a valid key. Claude Code cannot fix the key itself but can improve error handling so it fails gracefully rather than showing raw JSON errors to users.

**Acceptance criteria:**
- [ ] Raw JSON 401 error never shown to users
- [ ] Clean "temporarily unavailable" message shown instead
- [ ] Server-side logging of actual error for debugging
- [ ] If key is valid: narrative generates correctly

**Commit:** `fix: AI narrative error handling shows clean user message, logs error server-side`

---

## Implementation Sequence

Execute in this order, commit after each:

1. `git checkout main && git pull && git checkout -b feature/fairfax-phase2-fixes`
2. **INVESTIGATE** — complete all 0A-0H investigation tasks, report findings
3. **STEP 1** — Road classifier + location score fix → commit
4. **STEP 2** — Travel times → commit
5. **STEP 3** — Demographics Loudoun reference → commit
6. **STEP 4** — Cell tower display → commit
7. **STEP 5** — Pharmacies fix → commit
8. **STEP 6** — Restore crime module → commit
9. **STEP 7** — Rebuild maternity data → commit
10. **STEP 8** — Map enhancements (metro lines, crime, electric/gas) → commit
11. **STEP 9** — Development pressure score → commit
12. **STEP 10** — CI fix → commit
13. **STEP 11** — AI error handling → commit
14. **Syntax validation:** `python -c "import ast; ast.parse(open('reports/fairfax_report_new.py').read())"`
15. **Run tests:** `python -m pytest tests/test_fairfax_report.py -v`
16. **Push:** `git push origin feature/fairfax-phase2-fixes`

---

## Protection Rules (repeat every session)

```bash
# Verify before starting:
git diff main --name-only | grep -E "streamlit_app.py|/athens/" 
# Must return empty

# Never import from:
# - reports.loudoun_report
# - core.loudoun_*

# Test address: 13172 Ruby Lace Ct, Herndon, VA 20171
# Secondary: 11300 Braddock Rd, Fairfax, VA 22030
# Loudoun test (verify no regression): 43422 Cloister Pl, Leesburg, VA 20176
```

---

## Acceptance Criteria — Final Visual Check

After all steps, run Streamlit with `13172 Ruby Lace Ct, Herndon, VA 20171` and verify:

| Section | Expected |
|---|---|
| Location Quality — Road Type | "Cul-de-sac / Court (Very Low traffic)" |
| Location Quality — Highway | Route 28 or Fairfax County Pkwy, NOT Ruby Lace Ct |
| Location Quality — Score | 6.0-8.5/10 (not 10.0) |
| Travel Times | Actual minutes for all 5 destinations |
| Cell Towers | No "Unknown" name column; City shown |
| Pharmacies | Real pharmacy data from Google Places |
| Crime & Safety | Section present with metrics |
| Medical — Maternity | 4 Fairfax-area hospitals with expandable cards |
| Development Map | Metro lines drawn; crime toggle; electric/gas lines |
| Development Pressure | < 50/100 for established residential subdivision |
| AI Analysis | Clean "unavailable" message (not raw JSON) |
| Demographics table | "Fairfax Co." not "Loudoun Co." |
| CI | Green on push |

Also run `43422 Cloister Pl, Leesburg, VA 20176` — Loudoun report must be **completely unchanged**.
