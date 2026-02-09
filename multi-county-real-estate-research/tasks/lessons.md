# Lessons Learned - Multi-County Platform

## Key Insight: Port > Rebuild

**Major lesson:** When a complete working app exists, **port it** rather than rebuilding from scratch.

- Phase 1B rebuild: 5 sections, ~800 lines, partial functionality
- Original app port: 13 sections, 4,968 lines, 100% functionality
- Port took ~30 minutes vs days of rebuilding

**Pattern:** Minimal surgical changes (remove page_config, rename entry point) preserve working code.

## Phase 1A Findings
- All 12 Loudoun modules functional, no blockers
- GIS polygon detection > rectangular bounds (99%+ accuracy)
- Quick wins: Metro, Valuation, Community, Sales (low complexity)

## Patterns to Follow
- Test address: 43422 Cloister Pl, Leesburg, VA 20176
- Preserve working display functions - don't "improve" them
- Minimal changes for router integration
- Keep backwards compatibility aliases

## Patterns to Avoid
- Don't modify unified_app.py or router infrastructure
- Don't rebuild working code from scratch
- Don't force everything into shared_components.py unnecessarily
- Don't change the section order

## Port Changes Summary

### Removed (handled by unified_app.py)
- `st.set_page_config()` - router handles page config
- `geocode_address()` - router uses utils/geocoding.py
- `main()` - router is the entry point

### Renamed
- `analyze_property()` → `render_report()` - match router convention

### Added
- Updated docstring for multi-county framework
- Backwards compatibility alias: `analyze_property = render_report`
- Router integration notes at end of file

### Fixed (Path Resolution)
- `DATA_DIR` used `os.path.dirname(__file__)` which resolved to `reports/` not repo root
- Changed to `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` (go up one level)
- All derived paths (SCHOOLS_DIR, PERMITS_DIR, etc.) now resolve correctly

## All 13 Sections (Original App)

| Section | Lines | Features |
|---------|-------|----------|
| Schools | 1175-1486 | Charts, percentiles, peer comparison |
| Location | 1487-2161 | Roads, airports, flood, parks, Metro |
| Neighborhood | 2162-2278 | Google Places, convenience scoring |
| Community | 2279-2443 | HOA fees, amenities |
| Cell Towers | 2444-2520 | Coverage maps |
| Economic | 3134-3400 | BLS, LFPR, employers |
| Medical | 3401-3630 | Hospitals, urgent care, maternity |
| Development | 3631-3719 | Permits map, tech infrastructure |
| Zoning | 3720-4148 | Place types, dev probability |
| Valuation | 4149-4615 | ATTOM/RentCast, forecasts |
| AI Analysis | 4616-4734 | Claude narrative |
| Footer | 4735-4776 | Data sources |
| Entry Point | 4783-4949 | render_report() orchestrator |

## Module Dependencies (Original App)

The original app has its own module loading with feature flags:
- VALUATION_AVAILABLE
- DEMOGRAPHICS_AVAILABLE
- ECONOMIC_INDICATORS_AVAILABLE
- COMMUNITY_LOOKUP_AVAILABLE
- FOLIUM_AVAILABLE
- PLOTLY_AVAILABLE
- GEOPANDAS_AVAILABLE

These are set based on successful imports.

## Fairfax Report Lessons (2026-02-09)

### Root Cause: Hardcoded County Filters
- Core modules (`loudoun_school_performance.py`, `demographics_calculator.py`) hardcode `Division_Name == 'Loudoun County'`
- Fix pattern: Add `division_name` / `county_fips` parameter with Loudoun default for backward compat
- Then create Fairfax wrappers that pass the correct county
- This pattern is reusable for all future county expansions

### Root Cause: GIS Data Abbreviations
- Fairfax school GIS boundary parquets store abbreviated names ("Oak Hill", "Carson")
- The `school_name` column is the base name only, no level suffix
- `type_description` and `level` columns exist but aren't passed through `get_assigned_schools()`
- Fix: Name expansion function at the report level, not the core module level
- Special cases (e.g., "Carson" → "Rachel Carson") require a manual lookup dict

### Pattern: Wrapper Functions Over Core Modifications
- Import with alias: `from core.module import func as _original_func`
- Create local wrapper that adds county-specific parameters
- Zero changes needed at call sites throughout the report
- Example: `create_performance_chart` wrapper passes `division_name='Fairfax County'`

### Pattern: Standalone Section vs. Uncomment Approach
- Demographics: Simple uncomment + pass FIPS (underlying function accepts params)
- Transit: Created new `display_transit_section()` using Fairfax-specific module directly
- Don't try to match Loudoun's data structure if Fairfax has its own module with a different API

### Test Address: Fairfax County
- 13172 Ruby Lace Ct, Herndon, VA 20170 (38.919085, -77.401652)
- Schools: Oak Hill Elementary, Rachel Carson Middle, Westfield High
- Nearest Metro: Herndon (2.5 mi)
- Transit Score: 20/100 (suburban area)

## Next Steps

1. **Test in Streamlit**: `streamlit run unified_app.py`
2. **Verify all sections**: Enter 43422 Cloister Pl, Leesburg, VA
3. **Check dark mode**: Toggle should work
4. **Monitor for errors**: Check error handling in each section
