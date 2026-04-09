"""
Investment Highlights builder for the OM executive summary.

Produces six pre-formatted HTML bullet strings for the
"Investment Highlights" section of executive_summary.html. Each bullet
draws from the live ctx populated by upstream builders (property,
zoning, development, schools, healthcare, demographics, employers) so
that every property gets county-correct, property-specific copy
instead of the prior Fairfax-only boilerplate.

Usage:
    from investment_highlights_context import build_investment_highlights_context
    ctx.update(build_investment_highlights_context(county, ctx))
    # → ctx['investment_highlights'] = [str, str, str, str, str, str]

The builder is called *after* every other builder has finished and
mutated ctx, so all upstream keys are available. The template
(executive_summary.html) iterates the returned list with
``{% for hl in investment_highlights %}`` and renders each entry as
raw HTML, so the strings here include ``<strong>...</strong>`` markup.
"""

import logging
import re

logger = logging.getLogger(__name__)


# ── Static lookup tables ──────────────────────────────────────────────

# Per-university enrollment and employee counts. Public deed and Census
# data don't carry these, but they're stable values that rarely change
# year-to-year for major institutions. Match against
# ctx['university_name_short'] using a case-insensitive substring scan.
_UNIVERSITY_DATA = {
    "George Mason":                {"enrollment": "39,000+", "employees": "7,500+",  "type": "research"},
    "Northern Virginia Community": {"enrollment": "52,000+", "employees": "3,000+",  "type": "community"},
    "Virginia Tech":               {"enrollment": "37,000+", "employees": "8,000+",  "type": "research"},
    "University of Virginia":      {"enrollment": "25,000+", "employees": "14,000+", "type": "research"},
    "James Madison":               {"enrollment": "22,000+", "employees": "4,000+",  "type": "research"},
    "Marymount":                   {"enrollment": "3,500+",  "employees": "500+",    "type": "research"},
    "Shenandoah":                  {"enrollment": "4,000+",  "employees": "700+",    "type": "research"},
}

# Per-county employment / school district descriptors. Used for the
# "diversified employment" bullet which name-checks the local school
# district and the dominant economic corridor.
_COUNTY_EMPLOYMENT = {
    "fairfax": {
        "school_district": "FCPS",
        "tech_corridor":   "Tysons/Merrifield technology corridor",
        "fed_employment":  "Federal government and defense contracting",
    },
    "loudoun": {
        "school_district": "LCPS",
        "tech_corridor":   "Ashburn/One Loudoun technology corridor",
        "fed_employment":  "Federal government and intelligence community",
    },
}


# ── Helpers ───────────────────────────────────────────────────────────

def _parse_distance_miles(distance_str: str) -> float | None:
    """Extract a float from a distance string like '0.4 mi' or '7.1 mi'."""
    if not distance_str:
        return None
    match = re.search(r"([\d.]+)", str(distance_str))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _parse_score_value(score_str: str) -> int | None:
    """Extract the leading integer from a score like '100/100 Top Tier'."""
    if not score_str:
        return None
    match = re.search(r"(\d+)", str(score_str))
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _parse_delta_int(delta_str: str) -> int | None:
    """Extract the integer from a delta string like '+15%' or '-4%'."""
    if not delta_str or delta_str == "N/A":
        return None
    match = re.search(r"(-?\d+)", str(delta_str))
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _lookup_university(name: str) -> dict | None:
    """Case-insensitive substring lookup against _UNIVERSITY_DATA."""
    if not name:
        return None
    name_lower = name.lower()
    for key, data in _UNIVERSITY_DATA.items():
        if key.lower() in name_lower:
            return data
    return None


def _school_by_level(schools: list[dict], level: str) -> dict | None:
    """Find a school dict by its 'level' field. Returns None if missing."""
    if not schools:
        return None
    for s in schools:
        if (s.get("level") or "").lower() == level.lower():
            return s
    return None


# ── Bullet builders ───────────────────────────────────────────────────

def _bullet_transit(ctx: dict) -> str:
    """Bullet 0 — Metro / transit access."""
    station = ctx.get("metro_station_name") or "See broker for transit details"
    distance = ctx.get("metro_distance") or "\u2014"
    corridor = ctx.get("transit_corridor") or "Regional transit"
    return (
        f"<strong>{station} Metro \u2014 Institutional Rent Premium:</strong> "
        f"{station} station {distance} from property. {corridor} provides "
        f"access to Washington DC metro area employment centers. NoVA "
        f"research consistently documents 10\u201320% rent premium for "
        f"walkable Metro proximity, directly supporting above-market rent "
        f"capture on unit turnover."
    )


def _bullet_university(ctx: dict) -> str:
    """Bullet 1 — University / education anchor.

    Three modes:
      research  — full demand-engine framing with enrollment + employees
      community — softer education-anchor framing for community colleges
      generic   — fallback when no match or distance > 8 mi
    """
    name = ctx.get("university_name_short") or ""
    distance_str = ctx.get("university_distance") or ""
    distance_val = _parse_distance_miles(distance_str)
    uni_data = _lookup_university(name)

    too_far = distance_val is not None and distance_val > 8.0

    if uni_data and not too_far and uni_data["type"] == "research":
        enrollment = uni_data["enrollment"]
        employees = uni_data["employees"]
        return (
            f"<strong>{name} University Demand Engine:</strong> {name} at "
            f"{distance_str} enrolls {enrollment} students with {employees} "
            f"employees. Graduate student and faculty housing demand provides "
            f"a recession-resistant occupancy floor. University enrollment "
            f"has grown consistently regardless of broader economic cycles."
        )
    if uni_data and not too_far and uni_data["type"] == "community":
        enrollment = uni_data["enrollment"]
        return (
            f"<strong>{name} College \u2014 Education Anchor:</strong> {name} "
            f"campus at {distance_str} serves {enrollment} students through "
            f"workforce training, transfer programs, and continuing education. "
            f"Community college proximity drives sustained workforce-housing "
            f"demand from faculty, staff, and adult learners across multiple "
            f"economic cycles."
        )

    return (
        "<strong>Northern Virginia Education Corridor:</strong> The property "
        "sits within the broader Northern Virginia education corridor, served "
        "by the region's deep network of public universities, community "
        "colleges, and federal research institutions. Sustained education-"
        "sector employment provides multifamily demand insulation independent "
        "of any single institution."
    )


def _supply_headline(permits: int) -> str:
    """Pipeline headline that scales with the live permit count.

    For permits > 15 the pipeline qualifier is dropped entirely and the
    bullet falls back to a bare "Supply-Constrained Location" headline
    (per the task spec — claiming any specific pipeline label would be
    inconsistent with a >15 permit count).
    """
    if permits == 0:
        return "Supply-Constrained Location \u2014 Zero Competing Pipeline"
    if permits <= 5:
        return "Supply-Constrained Location \u2014 Minimal Competing Pipeline"
    if permits <= 15:
        return "Supply-Constrained Location \u2014 Limited Competing Pipeline"
    return "Supply-Constrained Location"


def _bullet_supply(ctx: dict) -> str:
    """Bullet 2 — Development pressure / supply constraint."""
    score = ctx.get("dev_pressure_score", "0")
    label = ctx.get("dev_pressure_label", "Moderate Development Pressure")
    try:
        permits = int(ctx.get("new_mf_permits_count", 0) or 0)
    except (TypeError, ValueError):
        permits = 0
    zoning = ctx.get("zoning_code_slash") or ctx.get("zoning_display") or "current"
    county = ctx.get("property_county") or "the county"
    headline = _supply_headline(permits)

    return (
        f"<strong>{headline}:</strong> "
        f"Development Pressure Score of {score}/100 ({label}). {zoning} "
        f"zoning with Comprehensive Plan designation unchanged. {permits} "
        f"new multifamily permits within 2-mile radius in trailing 24 months. "
        f"{county}\u2019s development review process makes competitive supply "
        f"additions a 5\u20137 year horizon at minimum."
    )


def _sol_claim(deltas: list[int | None]) -> str:
    """Phrase the SOL state-average comparison based on actual deltas."""
    valid = [d for d in deltas if d is not None]
    above = sum(1 for d in valid if d > 0)
    if not valid:
        return "with reported SOL pass rates from the Virginia Department of Education"
    if above == len(valid):
        return "all above Virginia SOL state averages"
    if above >= 2:
        return "largely above Virginia SOL state averages"
    return "in line with Virginia SOL benchmarks"


def _bullet_schools(ctx: dict) -> str:
    """Bullet 3 — Top-tier school district."""
    schools = ctx.get("schools") or []
    elementary = _school_by_level(schools, "Elementary")
    middle = _school_by_level(schools, "Middle School")
    high = _school_by_level(schools, "High School")
    county = ctx.get("property_county") or "the county"

    if not (elementary and middle and high):
        return (
            f"<strong>Local School District \u2014 Family Tenant Retention:"
            f"</strong> Served by the {county} public school system. School "
            f"quality is the #1 stated retention driver for family renters in "
            f"{county} surveys."
        )

    deltas = [
        _parse_delta_int(elementary.get("delta")),
        _parse_delta_int(middle.get("delta")),
        _parse_delta_int(high.get("delta")),
    ]
    sol_phrase = _sol_claim(deltas)

    return (
        f"<strong>Local School District \u2014 Family Tenant Retention:"
        f"</strong> Served by {high['name']} ({high['sol_pass']} SOL), "
        f"{middle['name']} ({middle['sol_pass']}), and {elementary['name']} "
        f"({elementary['sol_pass']}) \u2014 {sol_phrase}. School quality is "
        f"the #1 stated retention driver for family renters in {county} "
        f"surveys."
    )


def _hospital_descriptor(score_value: int | None) -> str:
    if score_value is None:
        return "A regional healthcare facility"
    if score_value >= 80:
        return "One of the region\u2019s premier healthcare facilities"
    if score_value >= 50:
        return "A major regional healthcare facility"
    return "A regional healthcare facility"


def _bullet_healthcare(ctx: dict) -> str:
    """Bullet 4 — Healthcare anchor."""
    hc = ctx.get("healthcare") or {}
    name = hc.get("name") or "Regional Healthcare Anchor"
    distance = hc.get("distance") or "\u2014"
    score_value = _parse_score_value(hc.get("score"))
    descriptor = _hospital_descriptor(score_value)

    return (
        f"<strong>{name} \u2014 Healthcare Anchor ({distance}):</strong> "
        f"{descriptor} drives consistent demand from medical professionals "
        f"and health system employees. Hospital proximity creates sustained "
        f"multifamily demand within the care radius."
    )


def _bullet_employment(ctx: dict, county: str) -> str:
    """Bullet 5 — Diversified employment / median income."""
    county_key = (county or "").strip().lower()
    emp_data = _COUNTY_EMPLOYMENT.get(county_key, {
        "school_district": "the local school district",
        "tech_corridor":   "the regional technology corridor",
        "fed_employment":  "Federal government employment",
    })
    school_district = emp_data["school_district"]
    tech_corridor = emp_data["tech_corridor"]
    fed_employment = emp_data["fed_employment"]
    university_name = ctx.get("university_name_short") or "regional universities"

    median_income = ctx.get("demo", {}).get("median_income", "N/A")
    income_multiplier = ctx.get("demo", {}).get("income_multiplier", "N/A")

    return (
        f"<strong>Deep, Diversified Employment \u2014 Recession-Resistant "
        f"Demand:</strong> 3-mile median household income of {median_income} "
        f"({income_multiplier}\u00d7 national median). {fed_employment}, "
        f"{school_district}, {university_name}, and the {tech_corridor} "
        f"provide multi-sector employment insulation unavailable in "
        f"single-industry markets."
    )


# ── Public API ────────────────────────────────────────────────────────

def build_investment_highlights_context(county: str, ctx: dict) -> dict:
    """Return the six investment-highlights bullets for the OM template.

    Parameters
    ----------
    county : str
        Lowercase county slug ('fairfax' or 'loudoun').
    ctx : dict
        Fully populated context dict — caller has already run every
        upstream builder. The investment highlights builder reads from
        the keys these builders set: metro_*, university_*,
        transit_corridor, dev_pressure_*, new_mf_permits_count,
        zoning_code_slash, property_county, schools, healthcare, demo,
        and the bullet builders also use the *county* parameter for
        the per-county static descriptors.

    Returns
    -------
    dict
        ``{"investment_highlights": [bullet0, bullet1, ..., bullet5]}``
        — a list of six pre-formatted HTML strings, one per bullet,
        consumed by the ``{% for hl in investment_highlights %}`` loop
        in templates/sections/executive_summary.html.
    """
    bullets = [
        _bullet_transit(ctx),
        _bullet_university(ctx),
        _bullet_supply(ctx),
        _bullet_schools(ctx),
        _bullet_healthcare(ctx),
        _bullet_employment(ctx, county),
    ]
    return {"investment_highlights": bullets}
