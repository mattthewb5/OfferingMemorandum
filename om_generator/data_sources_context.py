"""
County-aware data sources sidebar builder.

The "NewCo Data Intelligence — Sources" panel in market_overview.html lists
the data sources powering the OM. Most entries are state/federal/global and
apply everywhere; a handful are county-specific. This builder dispatches on
*county* and assembles the right list, replacing the static Fairfax-only
default that previously lived in context_sample.py.

Usage:
    from data_sources_context import build_data_sources_context
    ctx = build_data_sources_context("loudoun")
    # → {"data_sources": [...]}
"""

# Sources used in every county OM (state, federal, global APIs).
_NEUTRAL_SOURCES = [
    {"icon": "\u2713", "name": "Census ACS 5-Year API",           "color": "var(--slate-light)"},
    {"icon": "\u2713", "name": "VDOT Traffic Volume API",         "color": "var(--slate-light)"},
    {"icon": "\u2713", "name": "Virginia DOE SOL Data",           "color": "var(--slate-light)"},
    {"icon": "\u2713", "name": "CMS Hospital Ratings",            "color": "var(--slate-light)"},
    {"icon": "\u2713", "name": "Google Places API",               "color": "var(--slate-light)"},
    {"icon": "\u2713", "name": "EIA Forms 861 + 176 (Utilities)", "color": "var(--slate-light)"},
]

# Pending integrations — rendered with the dotted-circle icon and the
# wo-blue accent color to mark them as not-yet-active.
_PENDING_SOURCES = [
    {"icon": "\u2299", "name": "RentCast (mkt rents \u00b7 on activation)", "color": "var(--wo-blue)"},
    {"icon": "\u2299", "name": "Virginia RETR (CRE comps \u00b7 pending)",  "color": "var(--wo-blue)"},
]

# County-specific sources keyed by lowercase county slug.
_COUNTY_SOURCES = {
    "fairfax": [
        {"icon": "\u2713", "name": "Fairfax Co. Permit DB (41K+)", "color": "var(--slate-light)"},
        {"icon": "\u2713", "name": "Fairfax Co. GIS / Zoning",     "color": "var(--slate-light)"},
        {"icon": "\u2713", "name": "Fairfax Co. Crime Database",   "color": "var(--slate-light)"},
    ],
    "loudoun": [
        {"icon": "\u2713", "name": "Loudoun Co. Permit DB (~18K)",         "color": "var(--slate-light)"},
        {"icon": "\u2713", "name": "Loudoun Co. GIS / Zoning",             "color": "var(--slate-light)"},
        {"icon": "\u2713", "name": "Loudoun Co. Sheriff Crime Database",   "color": "var(--slate-light)"},
    ],
}


def build_data_sources_context(county: str) -> dict:
    """Return the data sources sidebar context keyed for the given county.

    Parameters
    ----------
    county : str
        County slug from detect_county() — expected lowercase 'fairfax' or
        'loudoun'. Falls back to neutral + pending only when unknown.

    Returns
    -------
    dict
        ``{"data_sources": [...]}`` — list of source row dicts with
        ``icon``, ``name``, and ``color`` keys consumed by the
        ``{% for source in data_sources %}`` loop in
        templates/sections/market_overview.html.
    """
    county_key = (county or "").strip().lower()
    sources = (
        _NEUTRAL_SOURCES
        + _COUNTY_SOURCES.get(county_key, [])
        + _PENDING_SOURCES
    )
    return {"data_sources": sources}
