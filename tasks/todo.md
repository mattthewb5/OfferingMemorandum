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
- [x] In `geocode_incidents()`, removed the `else` block that wrote
  `quality='not_found'` entries to the cache. Only successful geocodes
  get cached. Failed addresses become retryable on the next run.

### Fix 2 — City abbreviation expansion
- [x] Added `CITY_ABBREV` dict at module level (21 entries: ALEX→Alexandria,
  RSTN→Reston, etc.).
- [x] In `geocode_incidents()`, before building `full_address`,
  mapped `df['city']` through `CITY_ABBREV` using `.map().fillna()` so
  unknown codes pass through unchanged.

### Fix 3 — ZIP float formatting
- [x] In `geocode_incidents()`, after `astype(str)`, chained
  `.str.replace('.0', '', regex=False)` to strip the float suffix.

### Fix 4 — Semicolon unit parsing
- [x] In `geocode_incidents()`, before building `full_address`, applied
  `.str.replace(r';(\d)', r' APT \1', regex=True)` to convert
  `3300 CANNONGATE RD;102` → `3300 CANNONGATE RD APT 102`.

### Fix 5 — Route number expansion
- [x] In `geocode_incidents()`, before building `full_address`, applied
  `.str.replace(r'\bROUTE (\d+)', r'VA-\1', regex=True)` on the address column
  to convert `ROUTE 50` → `VA-50`.

### Workflow check
- [x] `.github/workflows/fairfax_crime_etl.yml` already has
  `GOOGLE_MAPS_API_KEY: ${{ secrets.GOOGLE_MAPS_API_KEY }}` at line 51.
  No change needed.

### Verification
- [x] Dry-run test passed — 5 sample addresses verified (no live API calls).

### Commit & push
- [x] Committed and pushed to `claude/fix-fairfax-geocoding-05Haa`.

## Files to change
1. `multi-county-real-estate-research/scripts/fairfax_crime_etl.py` — all 5 fixes
2. `tasks/todo.md` — this plan file (will be committed with the fix)
