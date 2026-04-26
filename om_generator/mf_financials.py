"""
Multifamily Financial Engine — 7-layer calculation chain.

All computation in float/int. All output as pre-formatted strings
via financial_formatter.py. No API calls — receives market_rents dict
as a parameter (caller fetches from RentCast).
"""

import re
from financial_formatter import (
    fmt_dollar, fmt_dollar_short, fmt_dollar_medium,
    fmt_pct, fmt_int, fmt_ratio,
)


# ============================================================================
# HELPERS
# ============================================================================

def _extract_bedrooms(unit_type: str) -> int:
    """Extract bedroom count from unit type label.

    "1 BR / 1 BA" → 1, "2 BR / 2 BA" → 2, "Studio" → 0, "—" → -1
    """
    if unit_type.lower().startswith('studio'):
        return 0
    match = re.search(r'(\d+)\s*BR', unit_type, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return -1


def _assess_utility(per_unit: float, low: float, high: float) -> str:
    """Assess utility expense relative to benchmark range."""
    if per_unit < low:
        return "Below Benchmark"
    elif per_unit > high:
        return "Above Benchmark"
    return "Within Normal Range"


def _monthly_payment(principal: float, annual_rate: float,
                     amort_years: int) -> float:
    """Standard amortization monthly payment: P × r / (1 − (1+r)^(−n))"""
    r = annual_rate / 12
    n = amort_years * 12
    if r == 0:
        return principal / n
    return principal * r / (1 - (1 + r) ** (-n))


def solve_irr(cash_flows: list, lo: float = 0.0, hi: float = 5.0,
              tol: float = 1e-6, max_iter: int = 1000):
    """Bisection solver for IRR. Pure Python — no external dependencies.

    Returns float (e.g. 0.1423 for 14.23%) or None if no solution in range.
    """
    def npv(rate, flows):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))

    # Check that solution exists in range
    npv_lo = npv(lo, cash_flows)
    npv_hi = npv(hi, cash_flows)
    if npv_lo * npv_hi > 0:
        # Try expanding range
        lo, hi = -0.5, 10.0
        npv_lo = npv(lo, cash_flows)
        npv_hi = npv(hi, cash_flows)
        if npv_lo * npv_hi > 0:
            return None

    for _ in range(max_iter):
        mid = (lo + hi) / 2
        npv_mid = npv(mid, cash_flows)
        if abs(npv_mid) < tol:
            return mid
        if npv_lo * npv_mid < 0:
            hi = mid
        else:
            lo = mid
            npv_lo = npv_mid

    return (lo + hi) / 2


def build_sensitivity_table(equity, pf_noi, hold_period,
                            annual_debt_svc, asking_price,
                            base_exit_cap, base_rent_growth):
    """Build 3×3 IRR sensitivity grid varying exit cap and rent growth."""

    exit_cap_offsets = [-0.0025, 0.0, 0.0025]
    rent_growth_offsets = [-0.005, 0.0, 0.005]

    rows = []
    for ec_offset in exit_cap_offsets:
        for rg_offset in rent_growth_offsets:
            ec = base_exit_cap + ec_offset
            rg = base_rent_growth + rg_offset

            scenario_yr_nois = {}
            for yr in range(1, hold_period + 1):
                scenario_yr_nois[yr] = pf_noi * (1 + rg) ** (yr - 1)

            exit_yr_noi = scenario_yr_nois[hold_period]
            selling_cost = asking_price * 0.02
            rev = (exit_yr_noi / ec - selling_cost) if ec > 0 else 0

            cf_list = [-equity]
            for yr in range(1, hold_period + 1):
                cf = scenario_yr_nois[yr] - annual_debt_svc
                if yr == hold_period:
                    cf += rev
                cf_list.append(cf)

            scenario_irr = solve_irr(cf_list)

            rows.append({
                "exit_cap": fmt_pct(ec),
                "rent_growth": fmt_pct(rg),
                "irr": fmt_pct(scenario_irr) if scenario_irr is not None else "N/A",
                "irr_raw": round(scenario_irr, 4) if scenario_irr is not None else None,
            })
    return rows


def build_financing_scenarios(asking_price, noi, pf_noi, hold_period,
                              t12_cap_rate_raw, default_rent_growth=0.035):
    """Build All-Cash / Conventional / Agency financing scenario comparison."""

    scenarios = [
        ("All Cash",     0.0,  0.0,    0),
        ("Conventional", 0.65, 0.0625, 30),
        ("Agency",       0.75, 0.055,  30),
    ]
    exit_cap_spread = 0.0025
    exit_cap = t12_cap_rate_raw + exit_cap_spread

    results = []
    for label, s_ltv, s_rate, s_amort in scenarios:
        loan = asking_price * s_ltv
        equity_s = asking_price - loan

        if s_ltv == 0:
            debt_svc = 0
            dscr_s = None
            coc = noi / asking_price if asking_price > 0 else 0
            equity_denom = asking_price
        else:
            debt_svc = _monthly_payment(loan, s_rate, s_amort) * 12
            dscr_s = noi / debt_svc if debt_svc > 0 else 0
            coc = (noi - debt_svc) / equity_s if equity_s > 0 else 0
            equity_denom = equity_s

        # IRR + equity multiple
        scenario_yr_nois = {}
        for yr in range(1, hold_period + 1):
            scenario_yr_nois[yr] = pf_noi * (1 + default_rent_growth) ** (yr - 1)

        exit_yr_noi = scenario_yr_nois[hold_period]
        selling_cost = asking_price * 0.02
        rev = (exit_yr_noi / exit_cap - selling_cost) if exit_cap > 0 else 0

        cf_list = [-equity_denom]
        total_annual_cf = 0
        for yr in range(1, hold_period + 1):
            cf = scenario_yr_nois[yr] - debt_svc
            total_annual_cf += cf
            if yr == hold_period:
                cf += rev
            cf_list.append(cf)

        scenario_irr = solve_irr(cf_list)
        em = (total_annual_cf + rev) / equity_denom if equity_denom > 0 else 0

        results.append({
            "label": label,
            "ltv": "All Cash" if s_ltv == 0 else fmt_pct(s_ltv),
            "rate": "\u2014" if s_ltv == 0 else fmt_pct(s_rate),
            "loan_amount": fmt_dollar(loan),
            "equity_required": fmt_dollar(equity_denom),
            "annual_debt_svc": "\u2014" if s_ltv == 0 else fmt_dollar(debt_svc),
            "dscr": "N/A" if dscr_s is None else fmt_ratio(dscr_s),
            "cash_on_cash": fmt_pct(coc),
            "irr": fmt_pct(scenario_irr) if scenario_irr is not None else "N/A",
            "equity_multiple": fmt_ratio(em),
        })
    return results


# ============================================================================
# MAIN ENGINE
# ============================================================================

def compute_mf_financials(inputs: dict, defaults: dict,
                           market_rents: dict) -> dict:
    """
    Multifamily 7-layer calculation engine.

    inputs: merged broker inputs (load_financial_inputs output)
    defaults: county defaults (get_defaults output)
    market_rents: {bedroom_count: avg_rent} from RentCast
                  (empty dict if API unavailable)
    Returns: dict of all ~35 financial ctx keys, all pre-formatted strings.

    POR mode (price_upon_request=True AND asking_price is null AND
    cap_rate_override is set) yields a price-on-request FinancialContext:
    asking_price_display='Price on request', price_per_unit hidden,
    t12_cap_rate from override, pro_forma_cap_rate hidden, Embedded Value
    skipped. The downstream cash-flow / financing / IRR chain still runs
    against a synthesized asking_price = NOI / cap_rate_override so that
    the rest of the OM has self-consistent numbers.
    """

    # ── LAYER 0 — POR detection + input validation ─────────────────────
    from exceptions import OMFinancialEngineInputError

    price_upon_request = bool(inputs.get("price_upon_request", False))
    cap_rate_override = inputs.get("cap_rate_override")
    asking_price_raw = inputs.get("asking_price")
    asking_price_provided = (
        asking_price_raw is not None and float(asking_price_raw or 0) > 0
    )

    if price_upon_request and cap_rate_override is None:
        raise OMFinancialEngineInputError(
            "Price-on-request mode requires cap_rate_override. "
            "Sidecar has POR=true but no override."
        )
    if not asking_price_provided and cap_rate_override is None:
        raise OMFinancialEngineInputError(
            "Engine requires either asking_price or cap_rate_override "
            "to compute cap rate display. Sidecar has neither."
        )

    is_por_mode = (
        price_upon_request
        and not asking_price_provided
        and cap_rate_override is not None
    )

    unit_mix_raw = inputs.get("unit_mix") or []
    if not unit_mix_raw:
        raise OMFinancialEngineInputError(
            "Multifamily engine requires unit_mix. Sidecar has none. "
            "Use commercial engine for non-MF property types or "
            "supply unit_mix."
        )

    # In POR mode, asking_price is unknown until NOI is computed —
    # we'll synthesize it from cap_rate_override below. Initialise to
    # 0 so the tax fallback (asking_price * rate) yields 0 instead of
    # raising; the broker is expected to supply t12.real_estate_taxes
    # directly when running POR.
    if is_por_mode:
        asking_price = 0.0
    else:
        asking_price = float(asking_price_raw)

    # Build enriched unit_mix (work with floats/ints)
    unit_mix = []
    for u in unit_mix_raw:
        unit_mix.append({
            "type": u.get("type", "—"),
            "count": int(u.get("count", 0)),
            "avg_sf": int(u.get("avg_sf", 0)),
            "in_place_rent": float(u.get("in_place_rent", 0)),
        })

    # Compute total_units from unit_mix (do not trust input)
    total_units = sum(u["count"] for u in unit_mix)
    if total_units <= 0:
        raise ValueError("total_units must be > 0 (sum of unit_mix counts)")

    # Pad unit_mix to minimum 3 elements
    while len(unit_mix) < 3:
        unit_mix.append({
            "type": "\u2014",
            "count": 0,
            "avg_sf": 0,
            "in_place_rent": 0,
            "market_rent": 0,
        })

    # ── LAYER 1 — Unit mix enrichment (market rents + gap) ──────────────
    threshold = defaults.get("below_market_threshold_pct", 0.97)
    market_rent_override = inputs.get("market_rent_override", {})
    used_fallback = False

    for u in unit_mix:
        br = _extract_bedrooms(u["type"])
        # Market rent priority: RentCast → broker override → 10% premium fallback
        mr = market_rents.get(br)
        if mr is None:
            mr = market_rent_override.get(str(br))
        if mr is None and u["in_place_rent"] > 0:
            mr = u["in_place_rent"] * 1.10
            used_fallback = True
        if mr is None:
            mr = 0

        u["market_rent"] = float(mr)
        u["gap_dollar"] = max(0, u["market_rent"] - u["in_place_rent"])
        u["gap_pct"] = (
            u["gap_dollar"] / u["in_place_rent"]
            if u["in_place_rent"] > 0 else 0
        )

    # Portfolio-level aggregations (only count units with count > 0)
    active_units = [u for u in unit_mix if u["count"] > 0]

    avg_monthly_rent = (
        sum(u["count"] * u["in_place_rent"] for u in active_units) / total_units
    )
    portfolio_avg_market_rent = (
        sum(u["count"] * u["market_rent"] for u in active_units) / total_units
    )
    portfolio_avg_gap = (
        sum(u["count"] * u["gap_dollar"] for u in active_units) / total_units
    )
    portfolio_rent_gap_pct = (
        portfolio_avg_gap / avg_monthly_rent if avg_monthly_rent > 0 else 0
    )

    below_market_units = sum(
        u["count"] for u in active_units
        if u["in_place_rent"] < u["market_rent"] * threshold
    )
    annual_noi_potential = below_market_units * portfolio_avg_gap * 12

    avg_unit_sf = (
        sum(u["count"] * u["avg_sf"] for u in active_units) / total_units
    )
    total_rentable_sf = sum(u["count"] * u["avg_sf"] for u in active_units)
    active_sfs = [u["avg_sf"] for u in active_units if u["avg_sf"] > 0]
    min_unit_sf = min(active_sfs) if active_sfs else 0
    max_unit_sf = max(active_sfs) if active_sfs else 0

    # ── LAYER 2 — T-12 income ──────────────────────────────────────────
    t12_data = inputs.get("t12", {})

    gpr = t12_data.get("gpr")
    if gpr is None:
        gpr = sum(u["count"] * u["in_place_rent"] * 12 for u in active_units)
    gpr = float(gpr)

    vacancy_pct = float(t12_data.get("vacancy_pct", defaults["vacancy_pct"]))
    vacancy_loss = gpr * vacancy_pct

    credit_loss_pct = float(t12_data.get("credit_loss_pct", defaults["credit_loss_pct"]))
    credit_loss = gpr * credit_loss_pct

    egi = gpr - vacancy_loss - credit_loss

    # ── LAYER 3 — T-12 expenses ────────────────────────────────────────
    mgmt_pct = float(t12_data.get("mgmt_pct", defaults["mgmt_pct"]))

    real_estate_taxes = float(
        t12_data.get("real_estate_taxes",
                     asking_price * defaults["real_estate_tax_rate"])
    )
    insurance = float(
        t12_data.get("insurance", total_units * defaults["insurance_per_unit"])
    )
    repairs = float(
        t12_data.get("repairs", total_units * defaults["repairs_per_unit"])
    )
    management = egi * mgmt_pct
    utilities = float(
        t12_data.get("utilities", total_units * defaults["utility_per_unit"])
    )
    admin = float(
        t12_data.get("admin", egi * defaults["admin_pct_of_egi"])
    )
    reserves = total_units * defaults["reserves_per_unit"]

    total_opex = (real_estate_taxes + insurance + repairs + management
                  + utilities + admin + reserves)
    noi = egi - total_opex
    opex_ratio = total_opex / egi if egi > 0 else 0

    # ── LAYER 4 — Valuation metrics ────────────────────────────────────
    if is_por_mode:
        # Synthesize asking_price so the downstream cash-flow / financing
        # chain has a self-consistent price. Display tokens are overridden
        # at ctx assembly to surface "Price on request" instead.
        asking_price = noi / float(cap_rate_override) if cap_rate_override else 0
        t12_cap_rate = float(cap_rate_override)
    else:
        t12_cap_rate = noi / asking_price if asking_price > 0 else 0
    price_per_unit = asking_price / total_units if total_units > 0 else 0

    if is_por_mode:
        # Wave 2: Embedded Value is skipped entirely in POR mode.
        value_cap_rate = 0
        embedded_value = 0
    else:
        value_cap_rate = defaults.get("value_cap_rate", t12_cap_rate)
        if value_cap_rate == 0:
            value_cap_rate = t12_cap_rate
        embedded_value = (annual_noi_potential / value_cap_rate
                          if value_cap_rate > 0 else 0)

    # ── LAYER 5 — Pro forma Year 1 ─────────────────────────────────────
    rent_growth = float(
        inputs.get("rent_growth_assumption", defaults["rent_growth_assumption"])
    )

    # PF GPR: below-market units get bumped to market rent, at-market stay
    pf_gpr = 0
    for u in active_units:
        if u["in_place_rent"] < u["market_rent"] * threshold:
            # Below market — use market rent
            pf_gpr += u["count"] * u["market_rent"] * 12
        else:
            # At market — apply rent growth
            pf_gpr += u["count"] * u["in_place_rent"] * (1 + rent_growth) * 12

    pf_vacancy_loss = pf_gpr * vacancy_pct
    pf_credit_loss = pf_gpr * credit_loss_pct
    pf_egi = pf_gpr - pf_vacancy_loss - pf_credit_loss

    pf_management = pf_egi * mgmt_pct
    pf_admin = pf_egi * defaults["admin_pct_of_egi"]
    pf_total_opex = (real_estate_taxes + insurance + repairs + pf_management
                     + utilities + pf_admin + reserves)
    pf_noi = pf_egi - pf_total_opex
    proforma_cap_rate = pf_noi / asking_price if asking_price > 0 else 0

    # ── LAYER 6 — Financing & returns ──────────────────────────────────
    financing_data = inputs.get("financing", {})
    ltv = float(financing_data.get("ltv", defaults["financing_ltv"]))
    rate = float(financing_data.get("interest_rate", defaults["financing_interest_rate"]))
    amort = int(financing_data.get("amortization", defaults["financing_amortization"]))

    loan_amount = asking_price * ltv
    equity = asking_price - loan_amount
    monthly_pmt = _monthly_payment(loan_amount, rate, amort)
    annual_debt_svc = monthly_pmt * 12
    dscr = noi / annual_debt_svc if annual_debt_svc > 0 else 0
    yr1_cashflow = noi - annual_debt_svc
    cash_on_cash = yr1_cashflow / equity if equity > 0 else 0

    # Utility benchmark
    t12_utilities_per_unit = utilities / total_units if total_units > 0 else 0
    utility_benchmark_low = defaults["utility_benchmark_low"]
    utility_benchmark_high = defaults["utility_benchmark_high"]
    utility_assessment = _assess_utility(
        t12_utilities_per_unit, utility_benchmark_low, utility_benchmark_high
    )

    # ── LAYER 7 — N-year projections + IRR ─────────────────────────────
    hold_period = int(inputs.get("hold_period", defaults["hold_period"]))
    exit_cap_spread = float(
        inputs.get("exit_cap_spread", defaults["exit_cap_spread"])
    )
    exit_cap = t12_cap_rate + exit_cap_spread

    # Compute NOI/EGI/cashflow for each year 1-N
    yr_nois = {}
    yr_egis = {}
    yr_cashflows_raw = {}
    for yr in range(1, hold_period + 1):
        yr_noi = pf_noi * (1 + rent_growth) ** (yr - 1)
        yr_egi = pf_egi * (1 + rent_growth) ** (yr - 1)
        yr_cf = yr_noi - annual_debt_svc
        yr_nois[yr] = yr_noi
        yr_egis[yr] = yr_egi
        yr_cashflows_raw[yr] = yr_cf

    # Reversion at exit year
    exit_yr_noi = yr_nois.get(hold_period, pf_noi)
    selling_cost = asking_price * 0.02
    reversion = (exit_yr_noi / exit_cap - selling_cost) if exit_cap > 0 else 0

    # IRR cash flows
    cash_flows_irr = [-equity]
    for yr in range(1, hold_period + 1):
        cf = yr_cashflows_raw[yr]
        if yr == hold_period:
            cf += reversion
        cash_flows_irr.append(cf)

    irr = solve_irr(cash_flows_irr)

    # Equity multiple
    total_cf = sum(yr_cashflows_raw[yr] for yr in range(1, hold_period + 1))
    equity_multiple = (total_cf + reversion) / equity if equity > 0 else 0

    # ── LAYER 8 — Sensitivity table + financing scenarios ──────────────
    sensitivity_table = build_sensitivity_table(
        equity, pf_noi, hold_period,
        annual_debt_svc, asking_price,
        base_exit_cap=exit_cap,
        base_rent_growth=rent_growth,
    )
    financing_scenarios = build_financing_scenarios(
        asking_price, noi, pf_noi, hold_period, t12_cap_rate,
        default_rent_growth=rent_growth,
    )

    # ── OUTPUT — build and return ctx_update dict ───────────────────────
    # All values are pre-formatted strings

    # Unit mix list
    unit_mix_formatted = []
    for u in unit_mix:
        pct = (u["count"] / total_units * 100) if total_units > 0 and u["count"] > 0 else 0
        unit_mix_formatted.append({
            "type": u["type"],
            "count": fmt_int(u["count"]) if u["count"] > 0 else "0",
            "pct": f"{int(round(pct))}%" if u["count"] > 0 else "0%",
            "avg_sf": f"{int(u['avg_sf']):,}" if u["avg_sf"] > 0 else "0",
            "in_place_rent": fmt_dollar(u["in_place_rent"]) if u["in_place_rent"] > 0 else "$0",
            "market_rent": fmt_dollar(u["market_rent"]) if u["market_rent"] > 0 else "$0",
            "gap_dollar": fmt_dollar(u["gap_dollar"]),
            "gap_pct": fmt_pct(u["gap_pct"]) if u["gap_pct"] > 0 else "0%",
        })

    # T-12 dict
    t12_formatted = {
        "gpr": fmt_dollar(gpr),
        "vacancy_pct": fmt_pct(vacancy_pct),
        "vacancy_loss": fmt_dollar(vacancy_loss),
        "credit_loss_pct": fmt_pct(credit_loss_pct),
        "credit_loss": fmt_dollar(credit_loss),
        "egi": fmt_dollar(egi),
        "real_estate_taxes": fmt_dollar(real_estate_taxes),
        "insurance": fmt_dollar(insurance),
        "repairs": fmt_dollar(repairs),
        "mgmt_pct": fmt_pct(mgmt_pct),
        "management": fmt_dollar(management),
        "utilities": fmt_dollar(utilities),
        "admin": fmt_dollar(admin),
        "reserves": fmt_dollar(reserves),
        "noi": fmt_dollar(noi),
    }

    # Pro forma dict
    pf_formatted = {
        "gpr": fmt_dollar(pf_gpr),
        "vacancy_pct": fmt_pct(vacancy_pct),
        "vacancy_loss": fmt_dollar(pf_vacancy_loss),
        "credit_loss_pct": fmt_pct(credit_loss_pct),
        "credit_loss": fmt_dollar(pf_credit_loss),
        "egi": fmt_dollar(pf_egi),
        "real_estate_taxes": fmt_dollar(real_estate_taxes),
        "insurance": fmt_dollar(insurance),
        "repairs": fmt_dollar(repairs),
        "mgmt_pct": fmt_pct(mgmt_pct),
        "management": fmt_dollar(pf_management),
        "utilities": fmt_dollar(utilities),
        "admin": fmt_dollar(pf_admin),
        "reserves": fmt_dollar(reserves),
        "noi": fmt_dollar(pf_noi),
    }

    # Cashflow years list — one dict per year, 1 through hold_period
    cashflow_years = []
    for yr in range(1, hold_period + 1):
        cashflow_years.append({
            "year": yr,
            "egi": fmt_dollar(yr_egis.get(yr, pf_egi)),
            "noi": fmt_dollar(yr_nois.get(yr, pf_noi)),
            "debt_svc": fmt_dollar(annual_debt_svc),
            "cashflow": fmt_dollar(yr_cashflows_raw.get(yr, yr1_cashflow)),
            "is_exit_year": yr == hold_period,
        })

    # Financing dict
    financing_formatted = {
        "ltv": fmt_pct(ltv),
        "interest_rate": fmt_pct(rate),
        "amortization": str(amort),
        "dscr": fmt_ratio(dscr),
    }

    # POR-mode display tokens. The hidden flags (None) signal templates
    # to skip the corresponding rows; Wave 2 C4 wires the {% if %} guards.
    if is_por_mode:
        asking_price_display = "Price on request"
        price_per_unit_display = None
        proforma_cap_rate_display = None
        embedded_value_display = None
    else:
        asking_price_display = fmt_dollar(asking_price)
        price_per_unit_display = fmt_dollar(price_per_unit)
        proforma_cap_rate_display = fmt_pct(proforma_cap_rate)
        embedded_value_display = fmt_dollar_medium(embedded_value)

    ctx = {
        # Property type marker
        "property_type": "multifamily",
        "is_por_mode": is_por_mode,

        # Scalar financial keys
        "asking_price_display": asking_price_display,
        "asking_price_full": asking_price_display,
        "asking_price_short": (asking_price_display
                               if is_por_mode else fmt_dollar_medium(asking_price)),
        "price_per_unit_display": price_per_unit_display,
        "t12_cap_rate": fmt_pct(t12_cap_rate),
        "proforma_cap_rate": proforma_cap_rate_display,
        "t12_noi_short": fmt_dollar_short(noi),
        "avg_monthly_rent": fmt_dollar(avg_monthly_rent),
        "opex_ratio": fmt_pct(opex_ratio),

        # Value-add / rent gap (Embedded Value computation skipped in POR)
        "embedded_value_display": embedded_value_display,
        "portfolio_rent_gap_pct": fmt_pct(portfolio_rent_gap_pct),
        "below_market_units": fmt_int(below_market_units),
        "avg_gap_per_unit": fmt_dollar(portfolio_avg_gap),
        "annual_noi_potential": fmt_dollar(annual_noi_potential),
        "value_cap_rate": fmt_pct(value_cap_rate) if not is_por_mode else None,
        "portfolio_avg_market_rent": fmt_dollar(portfolio_avg_market_rent),
        "portfolio_avg_gap": fmt_dollar(portfolio_avg_gap),

        # Property specs (computed)
        "total_units": f"{int(total_units):,}",
        "avg_unit_sf": f"{int(avg_unit_sf):,}",
        "total_rentable_sf": f"{int(total_rentable_sf):,}",
        "min_unit_sf": f"{int(min_unit_sf):,}",
        "max_unit_sf": f"{int(max_unit_sf):,}",

        # Unit mix
        "unit_mix": unit_mix_formatted,

        # T-12 and Pro Forma
        "t12": t12_formatted,
        "pf": pf_formatted,

        # Utility benchmark
        "utility_per_unit": fmt_dollar(t12_utilities_per_unit),
        "utility_benchmark_low": fmt_dollar(utility_benchmark_low),
        "utility_benchmark_high": fmt_dollar(utility_benchmark_high),
        "utility_assessment": utility_assessment,
        "reserves_per_unit": fmt_dollar(defaults["reserves_per_unit"]),
        "rent_growth_assumption": fmt_pct(rent_growth),

        # Cash flow projection — list of dicts, one per year
        "cashflow_years": cashflow_years,

        # Financing
        "financing": financing_formatted,

        # Return metrics
        "cash_on_cash": fmt_pct(cash_on_cash),
        "irr": fmt_pct(irr) if irr is not None else "N/A",
        "hold_period": str(hold_period),
        "equity_multiple": fmt_ratio(equity_multiple),
        "equity_multiple_raw": round(equity_multiple, 2),

        # Sensitivity & scenario analysis
        "sensitivity_table": sensitivity_table,
        "sensitivity_exit_caps": [fmt_pct(exit_cap + o)
                                  for o in [-0.0025, 0.0, 0.0025]],
        "sensitivity_rent_growths": [fmt_pct(rent_growth + o)
                                     for o in [-0.005, 0.0, 0.005]],
        "financing_scenarios": financing_scenarios,
    }

    return ctx
