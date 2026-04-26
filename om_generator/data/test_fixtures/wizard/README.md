# Wizard Fixture Corpus

Tracked test fixtures captured deliberately for regression testing.
Distinct from `data/audit_trail/` (auto-generated, gitignored,
30-day rolling) and `data/property_inputs/` (live wizard latest-
state, gitignored).

## Filename convention

<YYYY-MM-DD>_<slug>_<short-label>.json

Examples:
  2026-04-26_21001-sycolin-rd-ashburn-va-20147_office-POR-bug.json
  2026-04-26_9333-clocktower-pl-fairfax-va-22031_baseline-mf.json

The label captures *why* the fixture was preserved — the bug it
represents, the property type, or the test case it covers.

## How to add a new fixture

After completing a wizard run worth preserving, copy the matching
wizard.json from data/audit_trail/ to this directory with the
dated filename above. Commit with a message describing what the
fixture demonstrates.
