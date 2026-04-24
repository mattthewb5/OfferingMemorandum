IMPLEMENTATION SPEC — Financial Engine Phase 1
OfferingMemorandum Repo | Status: Approved for implementation

════════════════════════════════════════════════════════════
OVERVIEW
════════════════════════════════════════════════════════════

Build a property-type-aware financial engine that replaces all ~35 hardcoded
financial keys in context_sample.py with live computed values. Phase 1 fully
implements the multifamily (MF) calculation chain. Office, retail, and
industrial are supported as structured manual-entry types with computation
but without automated data sourcing.

The engine reads broker inputs from a JSON sidecar file (local dev) or S3
object (production) via the existing storage.py abstraction. This is the
same data shape the future Provenance wizard will write — zero rework when
the wizard is built.

════════════════════════════════════════════════════════════
SCOPE
════════════════════════════════════════════════════════════

New files:
  om_generator/financial_context.py       — router + entry point
  om_generator/mf_financials.py           — MF 7-layer calculation engine
  om_generator/commercial_financials.py   — office/retail/industrial manual-entry engine
  om_generator/financial_formatter.py     — numeric → display string formatting
  om_generator/financial_defaults.py      — all default assumptions, county-keyed where applicable
  data/property_inputs/property_<slug>.json     — v1.0 sidecars (replaces test_inputs/financial_inputs_*.json)

Modified files:
  om_generator/generate_om.py             — wire financial engine as builder #17,
                                            shift investment_highlights to #18
  multi-county-real-estate-research/core/rentcast_client.py
                                          — add two new methods
  om_generator/templates/sections/financials.html
                                          — add cash-on-cash + IRR to Key Metrics sidebar
  om_generator/templates/sections/executive_summary.html
                                          — fix unit_mix hard-coded index → loop

════════════════════════════════════════════════════════════
PART 1 — RentCast Client Extensions
════════════════════════════════════════════════════════════

File: multi-county-real-estate-research/core/rentcast_client.py

Add two new methods to the RentCastClient class. Follow existing patterns
exactly — same caching approach, same error handling, same return style.

Method 1: get_market_rent_statistics(zipcode, bedrooms, property_type="Apartment")
  Endpoint: GET /v1/avm/rent/long-term (confirm correct endpoint vs
            /v1/market/rent/long-term in actual RentCast docs — use whichever
            returns aggregate market stats by zip + bedroom count)
  Parameters: zipCode=zipcode, bedrooms=bedrooms, propertyType=property_type
  Returns: dict with keys: avg_rent (int), median_rent (int), min_rent (int),
           max_rent (int), sample_size (int)
  On API error or empty response: return None (caller handles fallback)
  Cache: 7-day file cache, same pattern as existing methods

Method 2: get_market_rent_for_unit_mix(zipcode, unit_mix_inputs)
  Convenience wrapper. Calls get_market_rent_statistics once per unique
  bedroom count in unit_mix_inputs. Returns dict keyed by bedroom count
  (int): { 1: 2340, 2: 2950, 3: 3800 }
  Bedroom count extracted from unit type label using regex:
    "1 BR / 1 BA" → 1, "2 BR / 2 BA" → 2, "Studio" → 0
  On any failure: returns empty dict (caller falls back to broker input
  or reasonable default)

════════════════════════════════════════════════════════════
PART 2 — financial_defaults.py
════════════════════════════════════════════════════════════

File: om_generator/financial_defaults.py

A single dict DEFAULTS keyed by county (lowercase: "fairfax", "loudoun",
"default"). Each entry contains all Tier 2 defaults from the investigation.
When a county-specific key is missing, fall back to "default".

Structure:
  DEFAULTS = {
    "fairfax": {
      "vacancy_pct": 0.045,
      "credit_loss_pct": 0.005,
      "mgmt_pct": 0.05,
      "real_estate_tax_rate": 0.01040,   # per $1 of assessed value
      "insurance_per_unit": 625,
      "repairs_per_unit": 1050,
      "utility_per_unit": 879,
      "utility_benchmark_low": 820,
      "utility_benchmark_high": 960,
      "admin_pct_of_egi": 0.016,
      "reserves_per_unit": 250,
      "rent_growth_assumption": 0.035,
      "financing_ltv": 0.65,
      "financing_interest_rate": 0.0625,
      "financing_amortization": 30,
      "exit_cap_spread": 0.0025,         # exit cap = going-in cap + this spread
      "hold_period": 5,
      "below_market_threshold_pct": 0.97 # unit is "below market" if in_place < market × this
    },
    "loudoun": {
      # Same structure — clone fairfax values as starting point.
      # Loudoun real_estate_tax_rate: 0.00875
    },
    "default": {
      # Same structure — use fairfax values as the national default
      # until county-specific data is researched
    }
  }

def get_defaults(county: str) -> dict:
    """Return merged defaults: county-specific over default."""
    base = DEFAULTS.get("default", {}).copy()
    base.update(DEFAULTS.get(county.lower(), {}))
    return base

════════════════════════════════════════════════════════════
PART 3 — financial_formatter.py
════════════════════════════════════════════════════════════

File: om_generator/financial_formatter.py

All numeric → string formatting lives here. No formatting logic anywhere else.
The engine always computes with Python float/int, then calls these functions
on output.

Required functions:

fmt_dollar(n: float, decimals=0) -> str
  Rounds to nearest dollar, formats with $ prefix and comma separator.
  Examples: 11649000 → "$11,649,000", 420289.86 → "$420,290"

fmt_dollar_short(n: float) -> str
  Abbreviates to M with 2 decimal places.
  Examples: 11649000 → "$11.65M", 5985000 → "$5.99M"
  Rule: always M (never K or B) for CRE context

fmt_dollar_medium(n: float) -> str
  Abbreviates with one decimal, no trailing zero.
  Examples: 232000000 → "$232M", 19600000 → "$19.6M"

fmt_pct(n: float, decimals=2) -> str
  Multiplies by 100 if n < 1, appends %.
  Examples: 0.0502 → "5.02%", 0.035 → "3.5%", 0.091 → "9.1%"

fmt_int(n: float) -> str
  Integer with no formatting — for counts.
  Examples: 552 → "552", 331 → "331"

fmt_ratio(n: float, decimals=2) -> str
  Plain decimal ratio — for DSCR, IRR, multiples.
  Examples: 1.38 → "1.38", 0.0765 → "0.08" (if used for IRR as decimal)
  Note: IRR should use fmt_pct, DSCR uses fmt_ratio

parse_dollar(s: str) -> float
  Inverse of fmt_dollar. Strips $, commas, M suffix (multiplies by 1e6 if M).
  Used when reading broker inputs that may arrive pre-formatted.
  Examples: "$11,649,000" → 11649000.0, "$11.65M" → 11650000.0

parse_pct(s: str) -> float
  Strips % suffix, divides by 100.
  Examples: "5.02%" → 0.0502, "65" → 0.65 (handles both forms)

════════════════════════════════════════════════════════════
PART 4 — financial_defaults.py sidecar loader
════════════════════════════════════════════════════════════

Add to financial_defaults.py:

def load_property_inputs(address: str, county: str, path: str = None) -> PropertyInputs:
    """
    Load broker property inputs for this property (v1.0 schema).

    (load_financial_inputs is kept as a deprecated alias returning the flat
    .financial dict; new code should use load_property_inputs.)

    Search order:
    1. data/property_inputs/property_{slug}.json (v1.0 canonical) where slug
       is address lowercased, spaces→underscores, non-alphanumeric stripped
       e.g. "21001 Sycolin Rd, Ashburn VA" → "21001_sycolin_rd_ashburn_va"
    2. test_inputs/financial_inputs_{slug}.json (legacy, emits DeprecationWarning)
    3. test_inputs/financial_inputs_{county}.json (legacy county fallback)
    4. Return PropertyInputs with empty identity and defaults-only financials.

    In production (STORAGE_BACKEND=s3), this function will call
    storage.read(f"sessions/{firm_id}/{session_id}/property_inputs/property_{slug}.json")
    instead. The dict shape is identical.

    The returned PropertyInputs.financial is merged over defaults:
      inputs = get_defaults(county)
      inputs.update(loaded_json)  ← broker values win over defaults
    """

JSON schema for test fixtures and future wizard output:

{
  "property_type": "multifamily",        // required: multifamily|office|retail|industrial
  "asking_price": 232000000,             // required
  "total_units": 552,                    // required for MF
  "unit_mix": [                          // required for MF, min 3 elements
    {
      "type": "1 BR / 1 BA",
      "count": 184,
      "avg_sf": 728,
      "in_place_rent": 2130
    },
    {
      "type": "2 BR / 2 BA",
      "count": 268,
      "avg_sf": 1012,
      "in_place_rent": 2710
    },
    {
      "type": "3 BR / 2 BA",
      "count": 100,
      "avg_sf": 1380,
      "in_place_rent": 3980
    }
  ],
  "t12": {                               // optional: broker T-12 actuals override defaults
    "gpr": 16428000,                     // if omitted, engine computes from unit_mix
    "vacancy_pct": 0.045,
    "credit_loss_pct": 0.005,
    "real_estate_taxes": 1385000,
    "insurance": 345000,
    "repairs": 580000,
    "mgmt_pct": 0.05,
    "utilities": 485000,
    "admin": 245000
  },
  "financing": {                         // optional: overrides defaults
    "ltv": 0.65,
    "interest_rate": 0.0625,
    "amortization": 30
  },
  "rent_growth_assumption": 0.035,       // optional: overrides default
  "exit_cap_spread": 0.0025,             // optional: overrides default
  "hold_period": 5                       // optional: overrides default
}

Note: market_rent per unit type is NOT in the sidecar — it always comes
from RentCast API (with broker override as a fallback only if API fails
and no live data is available). This keeps market rent data fresh on
every OM generation.

════════════════════════════════════════════════════════════
PART 5 — mf_financials.py
════════════════════════════════════════════════════════════

File: om_generator/mf_financials.py

The MF calculation engine. All computation in float/int. All output as
pre-formatted strings via financial_formatter.py. No API calls — receives
market_rents dict as a parameter (caller fetches from RentCast).

def compute_mf_financials(inputs: dict, defaults: dict,
                           market_rents: dict) -> dict:
    """
    inputs: merged broker inputs (load_property_inputs(...).financial output)
    defaults: county defaults (get_defaults output)
    market_rents: {bedroom_count: avg_rent} from RentCast
                  (empty dict if API unavailable)
    Returns: dict of all ~35 financial ctx keys, all pre-formatted strings
    """

Implementation — follow these seven layers in order:

LAYER 0 — Parse and validate inputs
  - asking_price (float): required, raise ValueError if missing
  - unit_mix: list of dicts, each with type/count/avg_sf/in_place_rent as ints
  - total_units: sum of unit_mix counts (compute, do not trust input)
  - Pad unit_mix to minimum 3 elements if fewer provided:
    append {"type": "—", "count": 0, "avg_sf": 0, "in_place_rent": 0,
            "market_rent": 0} as many times as needed

LAYER 1 — Unit mix enrichment (market rents + gap)
  For each unit in unit_mix:
    - Extract bedroom count from type label via regex
    - market_rent = market_rents.get(bedroom_count) or
                    inputs.get("market_rent_override", {}).get(str(bedroom_count)) or
                    in_place_rent × 1.10 (10% premium fallback — flag in output)
    - gap_dollar = market_rent − in_place_rent  (floor at 0)
    - gap_pct = gap_dollar / in_place_rent  (floor at 0)

  Portfolio-level:
    - total_units = sum of counts
    - avg_monthly_rent = weighted avg of in_place_rent by count
    - portfolio_avg_market_rent = weighted avg of market_rent by count
    - portfolio_avg_gap = weighted avg of gap_dollar by count
    - portfolio_rent_gap_pct = portfolio_avg_gap / avg_monthly_rent
    - below_market_units = count of units where in_place < market × threshold
    - annual_noi_potential = below_market_units × portfolio_avg_gap × 12
    - avg_unit_sf = weighted avg of avg_sf by count
    - total_rentable_sf = sum of (count × avg_sf)
    - min_unit_sf = min avg_sf in unit_mix
    - max_unit_sf = max avg_sf in unit_mix

LAYER 2 — T-12 income
  If broker provided t12.gpr: use it
  Else compute: gpr = sum(unit.count × unit.in_place_rent × 12)
  vacancy_pct = inputs.get("t12.vacancy_pct") or defaults["vacancy_pct"]
  vacancy_loss = gpr × vacancy_pct
  credit_loss_pct = inputs.get("t12.credit_loss_pct") or defaults["credit_loss_pct"]
  credit_loss = gpr × credit_loss_pct
  egi = gpr − vacancy_loss − credit_loss

LAYER 3 — T-12 expenses
  Resolve each line item: broker input → county default
  real_estate_taxes = inputs.get or asking_price × defaults["real_estate_tax_rate"]
  insurance = inputs.get or total_units × defaults["insurance_per_unit"]
  repairs = inputs.get or total_units × defaults["repairs_per_unit"]
  management = egi × mgmt_pct
  utilities = inputs.get or total_units × defaults["utility_per_unit"]
  admin = inputs.get or egi × defaults["admin_pct_of_egi"]
  reserves = total_units × defaults["reserves_per_unit"]
  total_opex = sum of all seven expense lines
  noi = egi − total_opex
  opex_ratio = total_opex / egi

LAYER 4 — Valuation metrics
  t12_cap_rate = noi / asking_price
  price_per_unit = asking_price / total_units
  value_cap_rate = defaults.get("value_cap_rate") or t12_cap_rate
  embedded_value = annual_noi_potential / value_cap_rate

LAYER 5 — Pro forma Year 1
  rent_growth = inputs.get or defaults["rent_growth_assumption"]
  Compute pf using same structure as t12 but apply rent_growth to below-market
  units' GPR contribution:
    pf_gpr = (market_rent_units GPR) + (at_market_units GPR)
    Keep vacancy_pct, credit_loss_pct, expense structure same as t12
    (broker can override any pf line individually in Phase 2)
  pf_noi = pf_egi − pf_opex
  proforma_cap_rate = pf_noi / asking_price

LAYER 6 — Financing & returns
  ltv = inputs.get or defaults["financing_ltv"]
  rate = inputs.get or defaults["financing_interest_rate"]
  amort = inputs.get or defaults["financing_amortization"]
  loan_amount = asking_price × ltv
  equity = asking_price − loan_amount
  Monthly payment formula: P × r / (1 − (1+r)^(−n))
    where P = loan_amount, r = rate/12, n = amort × 12
  annual_debt_svc = monthly_payment × 12
  dscr = noi / annual_debt_svc
  yr1_cashflow = noi − annual_debt_svc
  cash_on_cash = yr1_cashflow / equity

  Utility benchmark:
    utility_per_unit = inputs.get or defaults["utility_per_unit"]
    utility_benchmark_low = defaults["utility_benchmark_low"]
    utility_benchmark_high = defaults["utility_benchmark_high"]
    utility_assessment = assess_utility(t12_utilities_per_unit,
                                        utility_benchmark_low,
                                        utility_benchmark_high)
      → "Within Normal Range" | "Above Benchmark" | "Below Benchmark"

LAYER 7 — 5-year projections + IRR
  hold_period = inputs.get or defaults["hold_period"]  # always 5 for Phase 1
  exit_cap = t12_cap_rate + (inputs.get or defaults["exit_cap_spread"])
  For yr in [1, 3, 5]:
    yr_noi = pf_noi × (1 + rent_growth)^(yr−1)
    yr_egi = pf_egi × (1 + rent_growth)^(yr−1)  [simplified linear growth]
    yr_cashflow = yr_noi − annual_debt_svc
  reversion_yr5 = (yr5_noi / exit_cap) − (asking_price × 0.02)
    [2% selling cost deducted from reversion — standard CRE assumption]
  cash_flows = [−equity, yr1_cashflow, yr2_cashflow, yr3_cashflow,
                yr4_cashflow, yr5_cashflow + reversion_yr5]
  IRR: implement bisection solver (no external dependencies):
    def solve_irr(cash_flows, lo=0.0, hi=5.0, tol=1e-6, max_iter=1000)
    Returns float (e.g. 0.1423 for 14.23%) or None if no solution in range

OUTPUT — build and return ctx_update dict:
  All keys must be pre-formatted strings using financial_formatter.py.
  Return the complete dict matching the exact key names from context_sample.py
  plus two new keys: cash_on_cash, irr

  unit_mix list: each element is a dict of pre-formatted strings:
    {type, count, pct, avg_sf, in_place_rent, market_rent, gap_dollar, gap_pct}
  t12 dict: pre-formatted strings for all 14 keys
  pf dict: pre-formatted strings for all 14 keys (same structure as t12)
  cashflow dict: 12 keys — yr1/yr3/yr5 for egi/noi/debt_svc/cashflow
  financing dict: 4 keys — ltv/interest_rate/amortization/dscr
  All scalar financial keys (asking_price_display, t12_cap_rate, etc.)

════════════════════════════════════════════════════════════
PART 6 — commercial_financials.py
════════════════════════════════════════════════════════════

File: om_generator/commercial_financials.py

Manual-entry engine for office, retail, and industrial. Broker provides
rent roll and key financials; engine formats and computes NOI, cap rate,
WALT. No automated data sourcing in Phase 1.

def compute_commercial_financials(inputs: dict, defaults: dict,
                                   property_type: str) -> dict:
  """
  property_type: "office" | "retail" | "industrial"
  inputs: broker-provided rent roll + financials
  Returns: dict of ctx keys — different key set from MF
  """

Input schema for commercial types (flat fields in the v1.0 property sidecar):
  {
    "property_type": "office",
    "asking_price": 25000000,
    "total_sf": 85000,
    "rent_roll": [
      {
        "tenant": "Acme Corp",
        "sf": 12000,
        "annual_rent_psf": 42.50,
        "lease_expiry": "2028-06",
        "lease_type": "NNN"
      }
    ],
    "vacancy_sf": 8500,              // vacant SF (not leased)
    "operating_expenses": 380000,    // annual total OpEx (NNN: landlord share only)
    "financing": { ... }             // same structure as MF
  }

Computation (Phase 1 scope):
  total_sf = inputs["total_sf"]
  occupied_sf = sum of rent_roll[i].sf
  vacancy_pct = (total_sf − occupied_sf) / total_sf
  gross_revenue = sum(tenant.sf × tenant.annual_rent_psf for tenant in rent_roll)
  egi = gross_revenue (NNN leases: expenses pass through to tenants)
  noi = egi − operating_expenses
  t12_cap_rate = noi / asking_price
  price_per_sf = asking_price / total_sf
  walt = weighted avg lease term remaining, weighted by SF
    lease_months_remaining = months from today to lease_expiry
    walt = sum(tenant.sf × lease_months_remaining) / occupied_sf / 12
  avg_rent_psf = gross_revenue / occupied_sf
  dscr, debt_svc, cashflow, IRR: same formulas as MF (Layer 6-7)

Output keys (different from MF — commercial template section):
  rent_roll (list of dicts, formatted)
  total_sf_display, occupied_sf_display, vacancy_pct_display
  gross_revenue_display, noi_display
  t12_cap_rate, proforma_cap_rate (same keys as MF — shared template)
  price_per_sf_display
  walt_display (e.g. "4.2 years")
  avg_rent_psf_display (e.g. "$42.50 / SF")
  cash_on_cash, irr, dscr (same keys as MF)
  asking_price_display, asking_price_full, asking_price_short (same keys)

Phase 1 constraint: commercial types do NOT populate unit_mix, t12, pf,
cashflow dicts (those are MF-only). The template will need conditional
sections (Part 8 below) to handle the different display.

════════════════════════════════════════════════════════════
PART 7 — financial_context.py
════════════════════════════════════════════════════════════

File: om_generator/financial_context.py

The router. Entry point called from generate_om.py.

def build_financial_context(address: str, lat: float, lon: float,
                             county: str, ctx: dict) -> dict:
  """
  Loads inputs, fetches market rents, routes to correct engine.
  Returns ctx_update dict ready for ctx.update().
  Uses sys.path.insert + from core.xxx import pattern.
  Accesses RENTCAST_API_KEY via get_secret('RENTCAST_API_KEY').
  """

  1. Load inputs:
     defaults = get_defaults(county)
     inputs = load_property_inputs(address, county).financial
     property_type = inputs.get("property_type", "multifamily")

  2. Fetch market rents (MF only):
     If property_type == "multifamily":
       zipcode = ctx.get("property_zip")
       rentcast = RentCastClient(api_key=get_secret("RENTCAST_API_KEY"))
       market_rents = rentcast.get_market_rent_for_unit_mix(
           zipcode, inputs.get("unit_mix", []))
       # On any exception: market_rents = {} (fallback to 10% premium)
       # Log warning if market_rents is empty

  3. Route to engine:
     If property_type == "multifamily":
       return compute_mf_financials(inputs, defaults, market_rents)
     Elif property_type in ("office", "retail", "industrial"):
       return compute_commercial_financials(inputs, defaults, property_type)
     Else:
       raise ValueError(f"Unknown property_type: {property_type}")

════════════════════════════════════════════════════════════
PART 8 — Template Modifications
════════════════════════════════════════════════════════════

File A: om_generator/templates/sections/financials.html

Change 1 — Add cash-on-cash and IRR to Key Metrics sidebar.
Locate the Key Metrics sidebar block (the div containing asking_price_full,
price_per_unit_display, t12_cap_rate, proforma_cap_rate, opex_ratio).
Add two new rows after opex_ratio:

  <div class="metric-row">
    <span class="metric-label">Cash-on-Cash (YR1)</span>
    <span class="metric-value">{{ cash_on_cash }}</span>
  </div>
  <div class="metric-row">
    <span class="metric-label">IRR ({{ hold_period }}yr)</span>
    <span class="metric-value">{{ irr }}</span>
  </div>

Match exact CSS class names already used by adjacent metric rows.
Add hold_period to the scalar outputs from mf_financials.py
(e.g. "5" as a string — used only in this label).

Change 2 — Add commercial rent roll section (conditional).
After the unit mix table block, add:

  {% if property_type in ['office', 'retail', 'industrial'] %}
  <table class="rent-roll-table">
    <thead>
      <tr>
        <th>Tenant</th><th>SF</th><th>Rent / SF</th>
        <th>Annual Rent</th><th>Lease Expiry</th><th>Type</th>
      </tr>
    </thead>
    <tbody>
      {% for tenant in rent_roll %}
      <tr>
        <td>{{ tenant.name }}</td>
        <td class="r">{{ tenant.sf_display }}</td>
        <td class="r">{{ tenant.rent_psf_display }}</td>
        <td class="r">{{ tenant.annual_rent_display }}</td>
        <td class="r">{{ tenant.lease_expiry }}</td>
        <td class="r">{{ tenant.lease_type }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  <p class="footnote">WALT: {{ walt_display }} &nbsp;|&nbsp;
  Avg Rent: {{ avg_rent_psf_display }}</p>
  {% endif %}

Wrap existing unit_mix table in:
  {% if property_type == 'multifamily' %}
  ... existing unit mix table ...
  {% endif %}

Add property_type to the output dict in both mf_financials.py and
commercial_financials.py (pre-formatted string, same as input value).

File B: om_generator/templates/sections/executive_summary.html

Fix unit_mix hard-coded index access. Locate the three blocks that
access unit_mix[0], unit_mix[1], unit_mix[2] by index. Replace with
a {% for unit in unit_mix %} loop that renders the same fields.
Preserve all existing CSS classes and layout. The loop must render
at most 3 rows regardless of list length (use loop.index and break
equivalent: {% if loop.index > 3 %}{% break %}{% endif %} — note
Jinja2 does not support break; use slice instead: unit_mix[:3]).

════════════════════════════════════════════════════════════
PART 9 — generate_om.py Wiring
════════════════════════════════════════════════════════════

File: om_generator/generate_om.py

1. Add import at top (follow existing sys.path.insert pattern):
   from financial_context import build_financial_context

2. Insert financial engine as builder #17, before investment highlights:
   financial_ctx = build_financial_context(address, lat, lon, county, ctx)
   ctx.update(financial_ctx)

3. investment_highlights_context call shifts to builder #18 (no other
   changes to that call).

4. No other changes to generate_om.py.

════════════════════════════════════════════════════════════
PART 10 — Test Fixtures
════════════════════════════════════════════════════════════

Test fixtures live under data/property_inputs/ in v1.0 schema.

File: data/property_inputs/property_9333_clocktower_place_fairfax_va_22031.json
  MF fixture for Fairfax test property. Use values consistent with
  the Regent's Park hardcoded data in context_sample.py as the starting
  point. All numeric values as int/float (not formatted strings).

File: data/property_inputs/property_21001_sycolin_rd_ashburn_va.json
  MF fixture for Loudoun test property. Use same structure.
  Scale financial values proportionally — Sycolin Rd is industrial/
  commercial zoned, so use a hypothetical MF scenario for testing
  (this fixture is for engine testing only).

════════════════════════════════════════════════════════════
IMPLEMENTATION NOTES
════════════════════════════════════════════════════════════

Import convention: All new files use sys.path.insert + from core.xxx import.
Never use package-prefix imports. Follow existing builders exactly.

Secret access: get_secret("RENTCAST_API_KEY") — never os.getenv() directly.

No scipy, no numpy: The IRR bisection solver must be pure Python.
The amortization formula is pure math — no financial library needed.

context_sample.py: Do NOT remove any financial keys from context_sample.py.
The hardcoded values remain as the final fallback if financial_context.py
raises an exception. The engine overwrites them; it does not delete them.

Error handling: financial_context.py must catch all exceptions and log them.
On any failure, return {} so ctx.update({}) is a no-op and the hardcoded
seed values remain in ctx. The OM renders with dummy data rather than
crashing. Log the failure clearly.

Branch name: Claude Code will auto-create a branch. Report the branch name.
No pull request. Matt controls all merges to main.

════════════════════════════════════════════════════════════
VERIFICATION STEPS (run after implementation)
════════════════════════════════════════════════════════════

1. Run generate_om.py against Clocktower Place test address.
   Verify: t12_cap_rate, price_per_unit_display, cash_on_cash, irr
   are populated with computed values (not the Regent's Park dummy values).

2. Run against Loudoun test address (Sycolin Rd).
   Verify: same financial keys populated, county defaults used correctly
   (Loudoun tax rate vs Fairfax tax rate).

3. Run without any test fixture file present.
   Verify: engine runs on defaults only, no crash, OM renders.

4. Confirm unit_mix in rendered HTML contains computed values, not
   hardcoded Regent's Park data.

5. Confirm cash_on_cash and irr appear in the Key Metrics sidebar
   in the rendered financials page.

6. Confirm executive_summary unit mix renders via loop (not index).
