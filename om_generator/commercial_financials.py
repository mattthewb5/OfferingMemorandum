"""
Commercial Financial Engine — office, retail, and industrial.

Manual-entry engine for commercial property types. Broker provides
rent roll and key financials; engine formats and computes NOI, cap rate,
WALT. No automated data sourcing in Phase 1.
"""

from datetime import datetime
from financial_formatter import (
    fmt_dollar, fmt_dollar_short, fmt_dollar_medium,
    fmt_pct, fmt_int, fmt_ratio,
)
from mf_financials import _monthly_payment, solve_irr


def compute_commercial_financials(inputs: dict, defaults: dict,
                                   property_type: str) -> dict:
    """
    Commercial financial engine for office, retail, and industrial.

    property_type: "office" | "retail" | "industrial"
    inputs: broker-provided rent roll + financials
    Returns: dict of ctx keys for commercial template sections
    """

    asking_price = float(inputs.get("asking_price", 0))
    if asking_price <= 0:
        raise ValueError("asking_price is required and must be > 0")

    total_sf = int(inputs.get("total_sf", 0))
    if total_sf <= 0:
        raise ValueError("total_sf is required and must be > 0")

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

    # ── 5-year projections + IRR ────────────────────────────────────────
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

    yr5_noi = yr_nois.get(hold_period, pf_noi)
    selling_cost = asking_price * 0.02
    reversion = (yr5_noi / exit_cap - selling_cost) if exit_cap > 0 else 0

    cash_flows_irr = [-equity]
    for yr in range(1, hold_period + 1):
        cf = yr_cashflows[yr]
        if yr == hold_period:
            cf += reversion
        cash_flows_irr.append(cf)

    irr = solve_irr(cash_flows_irr)

    # ── Output dict ─────────────────────────────────────────────────────
    ctx = {
        "property_type": property_type,
        "rent_roll": rent_roll,
        "total_sf_display": f"{total_sf:,}",
        "occupied_sf_display": f"{int(occupied_sf):,}",
        "vacancy_pct_display": fmt_pct(vacancy_pct),
        "gross_revenue_display": fmt_dollar(gross_revenue),
        "noi_display": fmt_dollar(noi),
        "t12_cap_rate": fmt_pct(t12_cap_rate),
        "proforma_cap_rate": fmt_pct(proforma_cap_rate),
        "price_per_sf_display": fmt_dollar(price_per_sf),
        "walt_display": f"{walt:.1f} years",
        "avg_rent_psf_display": f"${avg_rent_psf:.2f} / SF",
        "asking_price_display": fmt_dollar(asking_price),
        "asking_price_full": fmt_dollar(asking_price),
        "asking_price_short": fmt_dollar_medium(asking_price),
        "cash_on_cash": fmt_pct(cash_on_cash),
        "irr": fmt_pct(irr) if irr is not None else "N/A",
        "hold_period": str(hold_period),
        "dscr": fmt_ratio(dscr),
        "financing": {
            "ltv": fmt_pct(ltv),
            "interest_rate": fmt_pct(rate),
            "amortization": str(amort),
            "dscr": fmt_ratio(dscr),
        },
    }

    return ctx
