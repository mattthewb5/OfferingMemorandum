# Lessons Learned - Multi-County Platform

## Phase 1A Findings
- All 12 Loudoun modules functional, no blockers
- GIS polygon detection > rectangular bounds (99%+ accuracy)
- Quick wins: Metro, Valuation, Community, Sales (low complexity)

## Patterns to Follow
- Test address: 43422 Cloister Pl, Leesburg, VA 20176
- Always use shared_components.py for display
- Progressive disclosure: summary → details
- Defensive programming: handle missing data

## Patterns to Avoid
- Don't modify unified_app.py or router infrastructure
- Don't hardcode styling in reports
- Don't skip error handling

## Phase 1B Notes

### API Structure Discovery
- `analyze_property_zoning_loudoun()` returns nested structure:
  - `place_type` is a dict with `success`, `place_type`, `policy_area`
  - `current_zoning` is a dict with `success`, `zoning`, `zoning_description`
  - No top-level `success` flag - check nested dicts
  - `development_probability` has `component_reasons` (dict), not `reasons` (list)

### Module Performance (43422 Cloister Pl test)
| Module | Time | Notes |
|--------|------|-------|
| Metro Analysis | 0.02s | Pure Python, hardcoded coords |
| Zoning Analysis | 1.34s | Live API calls to LOGIS GIS |
| Valuation Context | <0.01s | Data transformation only |

### Integration Patterns
1. **Section-level error isolation**: Each section wrapped in try/except
2. **Graceful degradation**: Show info message when data unavailable
3. **Manual input fallbacks**: Allow testing without full data pipeline
4. **Shared components**: All display via render_* functions

### Conversion Helpers
- `_convert_metro_to_score()`: Maps tier to 0-100 score + rating
- `_convert_school_to_score()`: Maps percentile to score + rating
- Pattern: Transform module output → shared component format

### Module Dependencies
- Metro: None (standalone, hardcoded station coords)
- Zoning: Live LOGIS API (internet required)
- Schools: pandas + CSV files
- Sales: pandas + Parquet file
- Valuation: None (processes orchestrator output)

### Caching Strategy
- Module-level caching (e.g., `get_cached_loudoun_sales_data()`)
- Session caching via Streamlit `@st.cache_resource`
- Sales data: 47K records, ~2-3s first load, instant after

### Next Steps for Phase 2
1. School charts require plotly + school_performance module
2. Community lookup needs communities.json config
3. Places analysis needs Google API key
4. Narrative generation needs Anthropic API key
