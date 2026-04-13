"""
Financial formatter — all numeric → display string formatting.

The engine always computes with Python float/int, then calls these functions
on output. No formatting logic lives anywhere else.
"""

import re


def fmt_dollar(n: float, decimals: int = 0) -> str:
    """Format as dollar amount with comma separator.

    Examples: 11649000 → "$11,649,000", 420289.86 → "$420,290"
    """
    rounded = round(n, decimals)
    if decimals == 0:
        return f"${int(rounded):,}"
    return f"${rounded:,.{decimals}f}"


def fmt_dollar_short(n: float) -> str:
    """Abbreviate to $X.XXM (always M for CRE context).

    Examples: 11649000 → "$11.65M", 5985000 → "$5.99M"
    """
    return f"${n / 1_000_000:.2f}M"


def fmt_dollar_medium(n: float) -> str:
    """Abbreviate with one decimal, no trailing zero.

    Examples: 232000000 → "$232M", 19600000 → "$19.6M"
    """
    m = n / 1_000_000
    if m == int(m):
        return f"${int(m)}M"
    formatted = f"${m:.1f}M"
    # Remove trailing zero after decimal if present
    formatted = formatted.replace('.0M', 'M')
    return formatted


def fmt_pct(n: float, decimals: int = 2) -> str:
    """Format as percentage. Multiplies by 100 if n < 1.

    Examples: 0.0502 → "5.02%", 0.035 → "3.50%", 0.091 → "9.10%"
    """
    if abs(n) < 1:
        pct = n * 100
    else:
        pct = n

    formatted = f"{pct:.{decimals}f}"
    return f"{formatted}%"


def fmt_int(n: float) -> str:
    """Integer with no formatting — for counts.

    Examples: 552 → "552", 331 → "331"
    """
    return str(int(n))


def fmt_ratio(n: float, decimals: int = 2) -> str:
    """Plain decimal ratio — for DSCR, multiples.

    Examples: 1.38 → "1.38", 0.0765 → "0.08"
    """
    return f"{n:.{decimals}f}"


def parse_dollar(s: str) -> float:
    """Inverse of fmt_dollar. Strips $, commas, M suffix.

    Examples: "$11,649,000" → 11649000.0, "$11.65M" → 11650000.0
    """
    if isinstance(s, (int, float)):
        return float(s)
    cleaned = s.strip().replace('$', '').replace(',', '')
    if cleaned.upper().endswith('M'):
        return float(cleaned[:-1]) * 1_000_000
    return float(cleaned)


def parse_pct(s: str) -> float:
    """Strips % suffix, divides by 100.

    Examples: "5.02%" → 0.0502, "65" → 0.65
    """
    if isinstance(s, (int, float)):
        return float(s) if float(s) < 1 else float(s) / 100
    cleaned = s.strip().replace('%', '')
    val = float(cleaned)
    if val >= 1:
        return val / 100
    return val
