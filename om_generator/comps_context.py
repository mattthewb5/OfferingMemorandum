"""
Comparable sales context builder for the OM Jinja2 template.

Three-tier comp sourcing for the financials.html "Comparable Sales" table:
  Tier 1 — Broker-provided CSV at data/comps/<slug>.csv (authoritative)
  Tier 2 — County proximity sales (Fairfax/Loudoun deed records via
           the existing *_sales_analysis modules, commercial mode)
  Tier 3 — Graceful empty (returns comps=[] + a "data pending" note)

The builder never raises. Any analyzer exception falls through to Tier 3.
"""

import csv
import logging
import re
import sys
from pathlib import Path

# Add multi-county research package to path (same pattern as every other
# om_generator builder — the package name has hyphens so a direct import
# isn't possible; sys.path + `from core.*` is the house convention).
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

logger = logging.getLogger(__name__)

# Broker CSV drop directory (mirrors the property_photos pattern).
_COMPS_ROOT = Path(__file__).resolve().parent / "data" / "comps"

# Columns the broker CSV is expected to provide — must match the template
# keys in financials.html:171-172.
_BROKER_COLUMNS = (
    "name",
    "units",
    "sale_price",
    "price_per_unit",
    "cap_rate",
    "sale_date",
    "source",
)

# Per-county copy for Tier 2. Keyed by lowercase county name.
_COUNTY_METHODOLOGY = {
    "fairfax": (
        "Multifamily building sales comparables sourced from Fairfax County "
        "deed transfer records via county GIS parcel cross-reference. Unit "
        "counts and cap rates reflect broker-provided data where available; "
        "county land records sourcing shows price and date only."
    ),
    "loudoun": (
        "Multifamily building sales comparables sourced from Loudoun County "
        "deed transfer records via county GIS parcel cross-reference. Unit "
        "counts and cap rates reflect broker-provided data where available; "
        "county land records sourcing shows price and date only."
    ),
}

_COUNTY_DEED_SOURCE = {
    "fairfax": "Virginia RETR / Fairfax County Land Records GIS",
    "loudoun": "Virginia RETR / Loudoun County Land Records",
}

_COUNTY_SOURCE_LABEL = {
    "fairfax": "Fairfax County Land Records",
    "loudoun": "Loudoun County Land Records",
}

_EMPTY_METHODOLOGY = (
    "Comparable sales data pending. Contact broker for transaction comps."
)

_BROKER_METHODOLOGY = (
    "Comparable sales provided by listing broker. Cap rates and unit counts "
    "reflect verified transaction data."
)

_BROKER_DEED_SOURCE = "Broker-Provided / CREXi / CoStar"


def _slugify(address: str) -> str:
    """Match the photo strip slugifier so broker drops line up with photos."""
    slug = re.sub(r"[^a-z0-9]+", "-", address.lower())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _format_dollars(amount) -> str:
    """Render a numeric sale price as a display string: '$NNN,NNN,NNN'."""
    try:
        return f"${int(round(float(amount))):,}"
    except (TypeError, ValueError):
        return "\u2014"


# Months used when formatting "YYYY-MM-DD" → "Mon YYYY".
_MONTH_ABBR = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def _format_sale_date(date_str) -> str:
    """Render an ISO 'YYYY-MM-DD' date as 'Mon YYYY' (e.g. 'Mar 2024')."""
    if not date_str:
        return "\u2014"
    try:
        parts = str(date_str).split("-")
        year = int(parts[0])
        month = int(parts[1])
        if 1 <= month <= 12:
            return f"{_MONTH_ABBR[month - 1]} {year}"
    except (ValueError, IndexError):
        pass
    return str(date_str)


def _load_broker_csv(address: str) -> list[dict] | None:
    """Tier 1: return broker-provided comp rows, or None if no file exists."""
    slug = _slugify(address)
    csv_path = _COMPS_ROOT / f"{slug}.csv"
    if not csv_path.is_file():
        logger.info("Broker comps file not found at %s", csv_path)
        return None

    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = []
            for raw in reader:
                row = {col: (raw.get(col, "") or "").strip() for col in _BROKER_COLUMNS}
                # Fallback to em-dash for any missing field so the template
                # never prints an empty cell.
                for col in _BROKER_COLUMNS:
                    if not row[col]:
                        row[col] = "\u2014"
                rows.append(row)
        logger.info("Broker comps loaded: %d rows from %s", len(rows), csv_path)
        return rows
    except Exception as exc:
        logger.warning("Failed to read broker comps CSV %s: %s", csv_path, exc)
        return None


def _load_county_sales(county: str, lat: float, lon: float) -> list[dict]:
    """Tier 2: call the county-specific analyzer for nearby commercial sales.

    Dispatches on *county* (expected lowercase 'fairfax' or 'loudoun'). The
    analyzer modules expose module-level ``get_nearby_sales`` functions — no
    class wrapper exists, so we import and call directly.

    All exceptions are swallowed and logged; callers receive [] on failure.
    """
    try:
        if county == "fairfax":
            from core.fairfax_sales_analysis import get_nearby_sales
        elif county == "loudoun":
            from core.loudoun_sales_analysis import get_nearby_sales
        else:
            logger.info("No sales analyzer available for county=%r", county)
            return []

        return get_nearby_sales(
            lat=lat,
            lon=lon,
            radius_miles=1.0,
            limit=8,
            commercial_mode=True,
        )
    except Exception as exc:
        logger.warning("County sales lookup failed (county=%s): %s", county, exc)
        return []


def _build_county_rows(sales: list[dict], county: str) -> list[dict]:
    """Format county-sales dicts into template comp rows.

    `sales` has already been filtered through commercial_mode in the analyzer
    (min_price=$1M), but we re-check defensively. Unit count and cap rate stay
    as em-dashes — public deed records don't carry either. (These fields will
    populate when the ATTOM commercial endpoint is implemented, pending
    ATTOM_API_KEY configuration and a new client method.)
    """
    source_label = _COUNTY_SOURCE_LABEL.get(county, "County Land Records")
    rows = []
    for sale in sales:
        try:
            price_value = float(sale.get("sale_price", 0) or 0)
        except (TypeError, ValueError):
            continue
        if price_value < 1_000_000:
            continue
        name = str(sale.get("address") or "").strip() or "See broker"
        rows.append({
            "name": name,
            "units": "\u2014",
            "sale_price": _format_dollars(price_value),
            "price_per_unit": "\u2014",
            "cap_rate": "\u2014",
            "sale_date": _format_sale_date(sale.get("sale_date")),
            "source": source_label,
        })
        if len(rows) >= 5:
            break
    return rows


def build_comps_context(
    address: str,
    lat: float,
    lon: float,
    county: str,
    submarket_name: str,
) -> dict:
    """Return the comparable-sales context keys for the OM template.

    Keys populated:
        comps                     — list of row dicts (may be empty)
        comps_submarket_display   — string for the submarket sub-heading
        comps_methodology_text    — narrative paragraph describing sourcing
        deed_source               — label for the data-sources sidebar

    Parameters
    ----------
    address : str
        Full property address as provided on the CLI.
    lat, lon : float
        Geocoded subject property coordinates.
    county : str
        Lowercase county slug from detect_county() ('fairfax'/'loudoun').
    submarket_name : str
        Submarket label from property_context.py (for the sub-heading).
    """
    submarket_display = submarket_name or "See broker"

    # Tier 1 — broker-authoritative CSV drop.
    broker_rows = _load_broker_csv(address)
    if broker_rows:
        return {
            "comps": broker_rows,
            "comps_submarket_display": submarket_display,
            "comps_methodology_text": _BROKER_METHODOLOGY,
            "deed_source": _BROKER_DEED_SOURCE,
            "_tier": "broker",
        }

    # Tier 2 — county deed-record proximity sales.
    raw_sales = _load_county_sales(county, lat, lon)
    county_rows = _build_county_rows(raw_sales, county) if raw_sales else []

    if county_rows:
        county_key = county if county in _COUNTY_METHODOLOGY else None
        methodology = (
            _COUNTY_METHODOLOGY[county_key]
            if county_key
            else _EMPTY_METHODOLOGY
        )
        deed_source = (
            _COUNTY_DEED_SOURCE[county_key]
            if county_key
            else "County Land Records"
        )
        return {
            "comps": county_rows,
            "comps_submarket_display": submarket_display,
            "comps_methodology_text": methodology,
            "deed_source": deed_source,
            "_tier": "county",
        }

    # Tier 3 — graceful empty.
    return {
        "comps": [],
        "comps_submarket_display": submarket_display,
        "comps_methodology_text": _EMPTY_METHODOLOGY,
        "deed_source": "Broker Input Required",
        "_tier": "empty",
    }
