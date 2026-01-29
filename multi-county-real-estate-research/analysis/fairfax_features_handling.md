# Fairfax-Only Features Handling

## Overview

Fairfax County has 3 analysis modules that have no equivalent in Loudoun County:

1. **Cell Towers Analysis** - FCC ASR tower data with coverage scoring
2. **School Performance Analysis** - 5-year VDOE SOL trends
3. **Traffic Analysis** - VDOT ADT exposure scoring

This document outlines strategies for handling these features in a unified app.

---

## Option Analysis

### Option 1: Conditional Display (Recommended)

Display sections only when they're available for the detected county.

```python
def display_results(county: str, **data):
    """Display all analysis results with conditional sections."""

    # === COMMON SECTIONS (Both Counties) ===
    st.header("🎓 Schools")
    display_schools_section(data['schools'])

    st.header("🏗️ Zoning & Land Use")
    display_zoning_section(data['zoning'])

    st.header("🚇 Transit Access")
    display_transit_section(data['transit'])

    st.header("🛡️ Safety Analysis")
    display_crime_section(data['crime'])

    st.header("🌳 Parks & Recreation")
    display_parks_section(data['parks'])

    # === FAIRFAX-ONLY SECTIONS ===
    if county == 'fairfax':
        st.header("📡 Cell Tower Coverage")
        display_cell_towers_section(data.get('cell_towers'))

        st.header("📊 School Performance Trends")
        display_school_performance_section(data.get('school_performance'))

        st.header("🚗 Traffic Exposure")
        display_traffic_section(data.get('traffic'))
```

**UI Mockup:**

```
┌──────────────────────────────────────────────────────────────┐
│  🏘️ Northern Virginia Property Intelligence                  │
│  Address: 6560 Braddock Rd, Alexandria, VA 22312             │
│  ✓ Detected: Fairfax County                                  │
├──────────────────────────────────────────────────────────────┤
│  🎓 Schools                                [Common Section]   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Elementary: Terraset Elementary (0.5 mi)               │  │
│  │ Middle: Longfellow Middle School (1.2 mi)              │  │
│  │ High: Thomas Jefferson HS (2.1 mi)                     │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  📊 School Performance Trends        [FAIRFAX ONLY SECTION]  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Thomas Jefferson HS: 100% pass rate (Excellent)        │  │
│  │ Quality Score: 100/100                                 │  │
│  │ 5-Year Trend: Stable at excellence ceiling             │  │
│  │ [📈 Performance Chart]                                 │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│  🚗 Traffic Exposure                 [FAIRFAX ONLY SECTION]  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Exposure Score: 65/100 (Fair)                          │  │
│  │ Nearest high-traffic road: Braddock Rd (23,000 ADT)   │  │
│  │ Analysis: Moderate traffic exposure...                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Pros:**
- Clean UI - only shows relevant information
- No confusion about unavailable features
- Fairfax users get enhanced experience
- Loudoun users don't see empty sections

**Cons:**
- Different report lengths for different counties
- Users may not know what they're missing

---

### Option 2: Graceful Degradation with Notice

Always show section headers, but display "Not Available" for Loudoun.

```python
def display_cell_towers_section(county: str, data: Dict = None):
    """Display cell tower analysis or availability notice."""
    st.header("📡 Cell Tower Coverage")

    if county == 'fairfax' and data:
        st.metric("Coverage Score", f"{data['score']}/100 ({data['rating']})")
        st.write(f"Nearest tower: {data['nearest_tower_miles']:.2f} mi")
        st.write(f"Towers within 2mi: {data['towers_within_2mi']}")
    else:
        st.info("""
        📍 **Cell tower analysis available for Fairfax County only**

        This feature uses FCC Antenna Structure Registration (ASR) data
        to analyze cellular coverage quality at a property location.
        """)
```

**UI Mockup:**

```
┌──────────────────────────────────────────────────────────────┐
│  For Loudoun County address:                                  │
├──────────────────────────────────────────────────────────────┤
│  📡 Cell Tower Coverage                                       │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ℹ️ Cell tower analysis available for Fairfax County only │  │
│  │                                                         │  │
│  │ This feature uses FCC Antenna Structure Registration    │  │
│  │ (ASR) data to analyze cellular coverage quality at a    │  │
│  │ property location.                                      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

**Pros:**
- Users know what features exist
- Consistent report structure
- May drive interest in expanding to Loudoun

**Cons:**
- Takes up screen space for non-functional content
- Could be confusing
- Clutters the report

---

### Option 3: Future-Proof Placeholders with Coming Soon

Show sections with "Coming Soon" messaging for Loudoun.

```python
def display_traffic_section(county: str, data: Dict = None):
    """Display traffic analysis or coming soon notice."""
    st.header("🚗 Traffic Exposure")

    if county == 'fairfax' and data:
        # Full Fairfax display
        st.metric("Exposure Score", f"{data['score']}/100")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Nearest Road:** {data['nearest_road']}")
        with col2:
            st.write(f"**ADT:** {data['nearest_adt']:,}")
    elif county == 'loudoun':
        st.info("""
        🚧 **Traffic analysis coming soon for Loudoun County**

        We're working on integrating VDOT traffic count data for
        Loudoun County. Check back for updates!

        *Interested? Contact us to prioritize this feature.*
        """)
        # Show placeholder metrics
        st.metric("Exposure Score", "—", help="Coming soon")
```

**Pros:**
- Sets expectations for future features
- Consistent structure
- Marketing opportunity

**Cons:**
- May disappoint users expecting functionality
- "Coming soon" can feel like broken promises
- Requires follow-through

---

## Recommended Approach: Hybrid Strategy

Use a combination based on section importance:

### Tier 1: Conditional Display (Essential Sections)
For core analysis that both counties should eventually have:

- **Cell Towers**: Show only for Fairfax (not commonly needed)
- **Traffic**: Show only for Fairfax (can add to Loudoun later)

### Tier 2: Enhanced Section (School Performance)
School performance is tightly coupled with school assignments, so integrate:

```python
def display_schools_section(county: str, schools: Dict, performance: Dict = None):
    """Display schools with optional performance data."""
    st.header("🎓 Schools")

    # Basic school assignments (both counties)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Elementary", schools['elementary']['school_name'])
    with col2:
        st.metric("Middle", schools['middle']['school_name'])
    with col3:
        st.metric("High", schools['high']['school_name'])

    # Performance analysis (Fairfax only)
    if county == 'fairfax' and performance:
        with st.expander("📊 School Performance Analysis", expanded=True):
            for school_type, school_name in [
                ('Elementary', schools['elementary']['school_name']),
                ('Middle', schools['middle']['school_name']),
                ('High', schools['high']['school_name'])
            ]:
                perf = get_school_performance(school_name)
                if perf:
                    st.subheader(f"{school_name}")
                    st.write(f"Pass Rate: {perf['recent_overall_pass_rate']:.1f}%")
                    st.write(f"Quality Score: {perf['quality_score']}/100")
                    st.write(f"5-Year Trend: {perf['trend']}")
```

---

## Implementation Details

### Section Visibility Configuration

```python
# config/feature_flags.py

COUNTY_FEATURES = {
    'loudoun': {
        'schools': True,
        'zoning': True,
        'transit': True,
        'crime': True,
        'parks': True,
        'utilities': True,
        'flood': True,
        'healthcare': True,
        'cell_towers': False,          # Not available
        'school_performance': False,   # Not available
        'traffic': False,              # Not available
        'emergency_services': False,   # Not available
        'subdivisions': False,         # Not available
    },
    'fairfax': {
        'schools': True,
        'zoning': True,
        'transit': True,
        'crime': True,
        'parks': True,
        'utilities': True,
        'flood': True,
        'healthcare': True,
        'cell_towers': True,           # ✓ Available
        'school_performance': True,    # ✓ Available
        'traffic': True,               # ✓ Available
        'emergency_services': True,    # ✓ Available
        'subdivisions': True,          # ✓ Available
    }
}

def is_feature_available(county: str, feature: str) -> bool:
    """Check if a feature is available for the given county."""
    return COUNTY_FEATURES.get(county, {}).get(feature, False)
```

### Dynamic Section Rendering

```python
def render_analysis_sections(county: str, data: Dict):
    """Render all analysis sections based on county availability."""

    # Define section order and handlers
    sections = [
        ('schools', '🎓 Schools', display_schools_section),
        ('zoning', '🏗️ Zoning', display_zoning_section),
        ('transit', '🚇 Transit', display_transit_section),
        ('crime', '🛡️ Safety', display_crime_section),
        ('parks', '🌳 Parks', display_parks_section),
        ('healthcare', '🏥 Healthcare', display_healthcare_section),
        ('cell_towers', '📡 Cell Towers', display_cell_towers_section),
        ('school_performance', '📊 Performance', display_school_performance_section),
        ('traffic', '🚗 Traffic', display_traffic_section),
        ('emergency_services', '🚒 Emergency', display_emergency_section),
    ]

    for feature_key, header, display_func in sections:
        if is_feature_available(county, feature_key):
            st.header(header)
            display_func(data.get(feature_key))
```

---

## Report Summary Section

Add a summary showing what features were analyzed:

```python
def display_analysis_summary(county: str):
    """Show summary of analysis features."""
    st.sidebar.markdown("### Analysis Features")

    features = {
        'schools': ('🎓', 'School Assignments'),
        'zoning': ('🏗️', 'Zoning Analysis'),
        'transit': ('🚇', 'Transit Access'),
        'crime': ('🛡️', 'Safety Score'),
        'parks': ('🌳', 'Park Access'),
        'cell_towers': ('📡', 'Cell Coverage'),
        'school_performance': ('📊', 'School Performance'),
        'traffic': ('🚗', 'Traffic Exposure'),
    }

    for key, (icon, name) in features.items():
        available = is_feature_available(county, key)
        status = "✓" if available else "—"
        st.sidebar.write(f"{icon} {name}: {status}")

    # Count
    total = len(features)
    available = sum(1 for k in features if is_feature_available(county, k))
    st.sidebar.markdown(f"**{available}/{total} features available**")
```

---

## Recommendation Summary

| Feature | Recommended Handling |
|---------|---------------------|
| Cell Towers | Conditional (Fairfax only) |
| School Performance | Integrated with Schools section |
| Traffic | Conditional (Fairfax only) |
| Emergency Services | Conditional (Fairfax only) |
| Subdivisions | Conditional (Fairfax only) |

**Key Principles:**
1. Don't show empty sections
2. Integrate related features (school + performance)
3. Keep sidebar summary showing what's available
4. No "coming soon" unless actually planned with timeline

This approach provides the cleanest user experience while maximizing the value of Fairfax's additional features.
