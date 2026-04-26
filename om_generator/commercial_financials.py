"""
Commercial Financial Engine — office, retail, and industrial.

Manual-entry engine for commercial property types. Broker provides
rent roll and key financials; engine formats and computes NOI, cap rate,
WALT. No automated data sourcing in Phase 1.

POR mode (price_upon_request=True AND asking_price absent AND
cap_rate_override set) yields a price-on-request FinancialContext
mirroring the multifamily engine: asking_price_display='Price on
request', price_per_unit_display / proforma_cap_rate hidden, t12_cap_rate
formatted from the override, is_por_mode=True. The downstream financing
/ IRR chain still runs against a synthesized
asking_price = NOI / cap_rate_override so the OM has self-consistent
numbers; the synthesized value is never surfaced as a display token.
"""

from datetime import datetime
from exceptions import OMFinancialEngineInputError
from financial_formatter import (
    fmt_dollar, fmt_dollar_short, fmt_dollar_medium,
    fmt_pct, fmt_int, fmt_ratio,
)
from mf_financials import _monthly_payment, solve_irr, build_financing_scenarios


def compute_commercial_financials(inputs: dict, defaults: dict,
                                   property_type: str) -> dict:
    """
    Commercial financial engine for office, retail, and industrial.

    property_type: "office" | "retail" | "industrial"
    inputs: broker-provided rent roll + financials
    Returns: dict of ctx keys for commercial template sections
    """

    # ── POR detection + input validation ────────────────────────────
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

    total_sf = int(inputs.get("total_sf", 0))
    if total_sf <= 0:
        raise OMFinancialEngineInputError(
            "Commercial engine requires total_sf. Sidecar has none. "
            "Capture total rentable SF in the wizard property-details "
            "step."
        )

    if is_por_mode:
        # Same pattern as MF engine: synthesize asking_price after NOI
        # is computed so the financing / IRR chain has a price to work
        # against. Display tokens are overridden at ctx assembly.
        asking_price = 0.0
    else:
        asking_price = float(asking_price_raw)

    rent_roll_raw = inputs.get("rent_roll", [])
    vacancy_sf = float(inputs.get("vacancy_sf", 0))
    operating_expenses = float(inputs.get("operating_expenses", 0))

    # ── Rent roll processing ────────────────────────────────────────────
    rent_roll = []
    occupied_sf = 0
    gross_revenue = 0
    weighted_months = 0
    now = datetime.now()

    for tenant in rent_roll_raw:
        sf = float(tenant.get("sf", 0))
        annual_rent_psf = float(tenant.get("annual_rent_psf", 0))
        annual_rent = sf * annual_rent_psf
        lease_expiry = tenant.get("lease_expiry", "")
        lease_type = tenant.get("lease_type", "Gross")

        occupied_sf += sf
        gross_revenue += annual_rent

        # WALT: months remaining from today to lease_expiry
        months_remaining = 0
        if lease_expiry:
            try:
                # Parse "YYYY-MM" format
                parts = lease_expiry.split("-")
                exp_year = int(parts[0])
                exp_month = int(parts[1]) if len(parts) > 1 else 12
                exp_date = datetime(exp_year, exp_month, 1)
                delta = exp_date - now
                months_remaining = max(0, delta.days / 30.44)
            except (ValueError, IndexError):
                months_remaining = 0

        weighted_months += sf * months_remaining

        rent_roll.append({
            "name": tenant.get("tenant", ""),
            "sf_display": f"{int(sf):,}",
            "rent_psf_display": f"${annual_rent_psf:.2f}",
            "annual_rent_display": fmt_dollar(annual_rent),
            "lease_expiry": lease_expiry,
            "lease_type": lease_type,
        })

    # ── Computed metrics ────────────────────────────────────────────────
    vacancy_pct = (total_sf - occupied_sf) / total_sf if total_sf > 0 else 0
    egi = gross_revenue  # NNN: expenses pass through to tenants
    noi = egi - operating_expenses
    if is_por_mode:
        asking_price = noi / float(cap_rate_override) if cap_rate_override else 0
        t12_cap_rate = float(cap_rate_override)
    else:
        t12_cap_rate = noi / asking_price if asking_price > 0 else 0
    price_per_sf = asking_price / total_sf if total_sf > 0 else 0
    walt = (weighted_months / occupied_sf / 12) if occupied_sf > 0 else 0
    avg_rent_psf = gross_revenue / occupied_sf if occupied_sf > 0 else 0

    # ── Financing & returns (same formulas as MF Layer 6-7) ─────────────
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

    # ── N-year projections + IRR ─────────────────────────────────────────
    hold_period = int(inputs.get("hold_period", defaults["hold_period"]))
    rent_growth = float(inputs.get("rent_growth_assumption", defaults["rent_growth_assumption"]))
    exit_cap_spread = float(inputs.get("exit_cap_spread", defaults["exit_cap_spread"]))
    exit_cap = t12_cap_rate + exit_cap_spread

    # Pro forma NOI = same as T-12 for commercial (manual entry)
    pf_noi = noi
    proforma_cap_rate = pf_noi / asking_price if asking_price > 0 else 0

    yr_cashflows = {}
    yr_nois = {}
    for yr in range(1, hold_period + 1):
        yr_noi = pf_noi * (1 + rent_growth) ** (yr - 1)
        yr_nois[yr] = yr_noi
        yr_cashflows[yr] = yr_noi - annual_debt_svc

    exit_yr_noi = yr_nois.get(hold_period, pf_noi)
    selling_cost = asking_price * 0.02
    reversion = (exit_yr_noi / exit_cap - selling_cost) if exit_cap > 0 else 0

    cash_flows_irr = [-equity]
    for yr in range(1, hold_period + 1):
        cf = yr_cashflows[yr]
        if yr == hold_period:
            cf += reversion
        cash_flows_irr.append(cf)

    irr = solve_irr(cash_flows_irr)

    # Equity multiple
    total_cf = sum(yr_cashflows[yr] for yr in range(1, hold_period + 1))
    equity_multiple = (total_cf + reversion) / equity if equity > 0 else 0

    # Cashflow years list — one dict per year, 1 through hold_period
    cashflow_years = []
    for yr in range(1, hold_period + 1):
        cashflow_years.append({
            "year": yr,
            "egi": fmt_dollar(yr_nois.get(yr, pf_noi)),  # commercial EGI = gross rev
            "noi": fmt_dollar(yr_nois.get(yr, pf_noi)),
            "debt_svc": fmt_dollar(annual_debt_svc),
            "cashflow": fmt_dollar(yr_cashflows.get(yr, yr1_cashflow)),
            "is_exit_year": yr == hold_period,
        })

    # Financing scenarios
    financing_scenarios = build_financing_scenarios(
        asking_price, noi, pf_noi, hold_period, t12_cap_rate,
        default_rent_growth=rent_growth,
    )

    # POR-mode display tokens. Hidden flags (None) signal templates to
    # skip the corresponding rows; Wave 2 C4 wires the {% if %} guards.
    if is_por_mode:
        asking_price_display = "Price on request"
        price_per_sf_display = None
        price_per_unit_display = None
        proforma_cap_rate_display = None
    else:
        asking_price_display = fmt_dollar(asking_price)
        price_per_sf_display = fmt_dollar(price_per_sf)
        # Commercial doesn't have units, so price_per_unit_display is
        # always hidden — emit None for parity with the MF context.
        price_per_unit_display = None
        proforma_cap_rate_display = fmt_pct(proforma_cap_rate)

    # ── Output dict ─────────────────────────────────────────────────────
    # ``total_rentable_sf`` matches the cover-template variable name (see
    # cover.html); the prior ``total_sf_display`` key was unreachable from
    # the cover. Renamed in Wave 2 C3.
    ctx = {
        "property_type": property_type,
        "is_por_mode": is_por_mode,
        "rent_roll": rent_roll,
        "total_rentable_sf": f"{total_sf:,}",
        "occupied_sf_display": f"{int(occupied_sf):,}",
        "vacancy_pct_display": fmt_pct(vacancy_pct),
        "gross_revenue_display": fmt_dollar(gross_revenue),
        "noi_display": fmt_dollar(noi),
        "t12_cap_rate": fmt_pct(t12_cap_rate),
        "proforma_cap_rate": proforma_cap_rate_display,
        "price_per_sf_display": price_per_sf_display,
        "price_per_unit_display": price_per_unit_display,
        "walt_display": f"{walt:.1f} years",
        "avg_rent_psf_display": f"${avg_rent_psf:.2f} / SF",
        "asking_price_display": asking_price_display,
        "asking_price_full": asking_price_display,
        "asking_price_short": (asking_price_display
                               if is_por_mode else fmt_dollar_medium(asking_price)),
        "cash_on_cash": fmt_pct(cash_on_cash),
        "irr": fmt_pct(irr) if irr is not None else "N/A",
        "hold_period": str(hold_period),
        "equity_multiple": fmt_ratio(equity_multiple),
        "equity_multiple_raw": round(equity_multiple, 2),
        "dscr": fmt_ratio(dscr),
        "cashflow_years": cashflow_years,
        "financing_scenarios": financing_scenarios,
        "financing": {
            "ltv": fmt_pct(ltv),
            "interest_rate": fmt_pct(rate),
            "amortization": str(amort),
            "dscr": fmt_ratio(dscr),
        },
    }

    return ctx
