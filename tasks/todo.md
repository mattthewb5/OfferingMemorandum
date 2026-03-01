# Fairfax Crime Geocoding Pipeline Fixes

## Goal
Restore geocoding rate from 16.7% back toward 69.4%+ by fixing 5 root causes
in `multi-county-real-estate-research/scripts/fairfax_crime_etl.py`.

## Protected files (DO NOT TOUCH)
- `streamlit_app.py`
- `athens/`
- `loudoun_report.py`
- `fairfax_report.py`

## Plan

### Fix 1 — Cache: stop permanently caching failures
- [ ] In `geocode_incidents()` (lines 496-503), remove the `else` block that
  writes `quality='not_found'` entries to the cache. Only successful geocodes
  get cached. Failed addresses become retryable on the next run.

### Fix 2 — City abbreviation expansion
- [ ] Add a `CITY_ABBREV` dict at module level (21 entries: ALEX→Alexandria,
  RSTN→Reston, etc.).
- [ ] In `geocode_incidents()`, before building `full_address` (line 448),
  map `df['city']` through `CITY_ABBREV` using `.map().fillna(df['city'])` so
  unknown codes pass through unchanged.

### Fix 3 — ZIP float formatting
- [ ] In `geocode_incidents()` line 451, after `astype(str)`, chain
  `.str.replace('.0', '', regex=False)` to strip the float suffix.

### Fix 4 — Semicolon unit parsing
- [ ] In `geocode_incidents()`, before building `full_address`, apply
  `df['address'].str.replace(r';(\d)', r' APT \1', regex=True)` to convert
  `3300 CANNONGATE RD;102` → `3300 CANNONGATE RD APT 102`.

### Fix 5 — Route number expansion
- [ ] In `geocode_incidents()`, before building `full_address`, apply
  `str.replace(r'\bROUTE (\d+)', r'VA-\1', regex=True)` on the address column
  to convert `ROUTE 50` → `VA-50`.

### Workflow check
- [x] `.github/workflows/fairfax_crime_etl.yml` already has
  `GOOGLE_MAPS_API_KEY: ${{ secrets.GOOGLE_MAPS_API_KEY }}` at line 51.
  No change needed.

### Verification
- [ ] After implementation, run a dry-run test that constructs 5 sample
  `full_address` strings showing before/after for each fix. No live API calls.

### Commit & push
- [ ] Commit all changes and push to `claude/fix-fairfax-geocoding-05Haa`.

## Files to change
1. `multi-county-real-estate-research/scripts/fairfax_crime_etl.py` — all 5 fixes
2. `tasks/todo.md` — this plan file (will be committed with the fix)
