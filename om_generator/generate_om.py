#!/usr/bin/env python3
"""
NewCo OM Generator — Jinja2 Template Renderer

Assembles a context dictionary, renders the Jinja2 template, and outputs
a static HTML file visually identical to the v3 prototype.

Usage:
    python generate_om.py                                          # default test address
    python generate_om.py "9333 Clocktower Place, Fairfax VA 22031"
    python generate_om.py "43422 Cloister Pl, Leesburg, VA 20176" --output my.html
"""
import argparse
import os
import re
import sys

import requests
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, 'templates')
V3_PATH = os.path.join(SCRIPT_DIR, '..', 'investigation', 'newco_om_v3_regents_park.html')
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, 'om_output.html')

# Add multi-county research package to path (for county_detector)
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

DEFAULT_ADDRESS = "9333 Clocktower Place, Fairfax VA 22031"


def geocode_address(address: str):
    """
    Geocode an address to (lat, lon) using Google Maps, with Census fallback.

    Returns:
        Tuple of (lat, lon) or None on failure.
    """
    # Try Google Geocoding API first
    try:
        from core.api_config import get_api_key
        api_key = get_api_key('GOOGLE_MAPS_API_KEY')
        if api_key:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            resp = requests.get(url, params={"address": address, "key": api_key}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("results"):
                loc = data["results"][0]["geometry"]["location"]
                return (loc["lat"], loc["lng"])
    except Exception as e:
        print(f"  Google geocoding failed ({e}), trying Census fallback...", file=sys.stderr)

    # Census Bureau geocoder fallback
    try:
        url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        resp = requests.get(url, params={
            "address": address, "benchmark": "Public_AR_Current", "format": "json"
        }, timeout=15)
        resp.raise_for_status()
        matches = resp.json().get("result", {}).get("addressMatches", [])
        if matches:
            coords = matches[0]["coordinates"]
            return (coords["y"], coords["x"])
    except Exception as e:
        print(f"  Census geocoding failed: {e}", file=sys.stderr)

    return None


def extract_logo_base64(v3_path):
    """Extract the West Oxford logo base64 string from the v3 prototype."""
    with open(v3_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'(data:image/png;base64,[A-Za-z0-9+/=]+)', content)
    if not match:
        print("WARNING: Could not extract logo from v3 prototype", file=sys.stderr)
        return ""
    return match.group(1)


# Unicode -> HTML entity map for characters used in v3
_ENTITY_MAP = {
    '\u2019': '&#8217;',   # right single quote
    '\u2018': '&#8216;',   # left single quote
    '\u2014': '&#8212;',   # em dash
    '\u2013': '&#8211;',   # en dash
    '\u00d7': '&times;',   # multiplication sign
    '\u00b7': '&middot;',  # middle dot
    '\u2605': '&#9733;',   # star
    '\u2713': '&#10003;',  # check mark
    '\u2299': '&#8857;',   # circled dot
}


def _encode_entities(val):
    """Convert non-ASCII unicode chars to HTML entities in a string."""
    if isinstance(val, str):
        for char, entity in _ENTITY_MAP.items():
            val = val.replace(char, entity)
        return val
    elif isinstance(val, dict):
        return {k: _encode_entities(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_encode_entities(item) for item in val]
    return val


def main():
    parser = argparse.ArgumentParser(description='Generate OM HTML from Jinja2 templates')
    parser.add_argument('address', nargs='?', default=DEFAULT_ADDRESS,
                        help='Property address to generate OM for')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT, help='Output HTML path')
    args = parser.parse_args()

    address = args.address
    print(f"Generating OM for: {address}")

    # ── Geocode address ───────────────────────────────────────────────
    coords = geocode_address(address)
    if coords is None:
        print(f"ERROR: Could not geocode address: {address}", file=sys.stderr)
        print("Please verify the address and try again.", file=sys.stderr)
        sys.exit(1)

    lat, lon = coords
    print(f"  Geocoded: {lat:.4f}, {lon:.4f}")

    # ── Detect county ─────────────────────────────────────────────────
    from utils.county_detector import detect_county
    county = detect_county(lat, lon)
    if county == 'unknown':
        print(f"  Warning: Could not detect county for {lat}, {lon}. Defaulting to fairfax.")
        county = 'fairfax'
    print(f"  County: {county}")

    # Load context
    from context_sample import get_sample_context
    ctx = get_sample_context()

    # Inject logo base64
    ctx['wo_logo_base64'] = extract_logo_base64(V3_PATH)

    # ── Live crime data ──────────────────────────────────────────────
    from crime_context import build_crime_context
    live_crime = build_crime_context(lat, lon, county)
    ctx['crime'] = live_crime

    # Update the stoplight Crime Safety row to match live score
    score = int(live_crime['safety_score'])
    if score >= 80:
        rating, dot, badge = 'Very Safe', 'sl-green', 'badge-green'
    elif score >= 60:
        rating, dot, badge = 'Safe', 'sl-green', 'badge-green'
    elif score >= 40:
        rating, dot, badge = 'Moderate', 'sl-amber', 'badge-amber'
    elif score >= 20:
        rating, dot, badge = 'Caution Advised', 'sl-red', 'badge-red'
    else:
        rating, dot, badge = 'High Crime Area', 'sl-red', 'badge-red'

    for sl in ctx['stoplight_scores']:
        if sl['label'] == 'Crime Safety':
            sl['badge_text'] = rating
            sl['label_detail'] = rating
            sl['bar_width'] = f"{score}%"
            sl['bar_color'] = 'var(--green)' if score >= 60 else 'var(--amber)' if score >= 40 else 'var(--red)'
            sl['dot_class'] = dot
            sl['badge_class'] = badge
            break

    print(f"  Crime data wired: score={live_crime['safety_score']}, "
          f"violent={live_crime['violent_count']}, "
          f"property={live_crime['property_count']}, "
          f"total={live_crime['total_incidents']}")

    # ── Live schools data ─────────────────────────────────────────────
    from schools_context import build_schools_context
    live_schools = build_schools_context(lat, lon, county)
    ctx['schools'] = live_schools['schools']
    ctx['school_footnote'] = live_schools['school_footnote']

    for s in live_schools['schools']:
        print(f"  School wired: {s['name']} — SOL {s['sol_pass']}, "
              f"State Avg {s['state_avg']}, Delta {s['delta']}")

    # ── Live healthcare data ──────────────────────────────────────────
    from healthcare_context import build_healthcare_context
    live_healthcare = build_healthcare_context(lat, lon, county)
    ctx['healthcare'] = live_healthcare['healthcare']
    print(f"  Healthcare wired: {live_healthcare['healthcare']['name']} — "
          f"{live_healthcare['healthcare']['distance']}, "
          f"score={live_healthcare['healthcare']['score']}")

    # ── Live demographics data ────────────────────────────────────────
    from demographics_context import build_demographics_context
    demo_ctx = build_demographics_context(lat, lon, county)
    ctx['demo'] = demo_ctx['demo']
    print(f"  Demographics wired: income={demo_ctx['demo']['median_income']}, "
          f"pop={demo_ctx['demo']['population']}")

    # ── Live employers data ────────────────────────────────────────────
    from employers_context import build_employers_context
    emp_ctx = build_employers_context(lat, lon, county)
    ctx.update(emp_ctx)
    print(f"  Employers wired: {len(emp_ctx['employers'])} employers, "
          f"year={emp_ctx['employers_data_year']}")

    # ── Employer map (geocoded markers + logo domains) ────────────────
    from employer_map_context import build_employer_map_context
    map_ctx = build_employer_map_context(lat, lon, ctx["employers"], county)
    ctx.update(map_ctx)
    from core.api_config import get_api_key
    ctx["google_maps_api_key"] = get_api_key('GOOGLE_MAPS_API_KEY') or ""
    print(f"  Employer map wired: {len(map_ctx['employer_map_markers'])} markers geocoded")

    # ── Live development intelligence ──────────────────────────────────
    from development_context import build_development_context
    dev_ctx = build_development_context(lat, lon, county)
    ctx.update(dev_ctx)
    print(f"  Development wired: score={dev_ctx['dev_pressure_score']}, "
          f"permits_2mi={dev_ctx['permits_2mi_count']}, "
          f"new_mf={dev_ctx['new_mf_permits_count']}")

    # Convert unicode characters to HTML entities to match v3 output
    ctx = _encode_entities(ctx)

    # Render template
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        keep_trailing_newline=True,
    )
    template = env.get_template('base.html')
    html = template.render(**ctx)

    # Write output
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"OM generated: {args.output} ({len(html):,} chars)")

    # Quick sanity check: ensure no unresolved {{ }} remain
    unresolved = re.findall(r'\{\{.*?\}\}', html)
    if unresolved:
        print(f"WARNING: {len(unresolved)} unresolved template variables found:")
        for var in unresolved[:10]:
            print(f"  {var}")
    else:
        print("All template variables resolved successfully.")


if __name__ == '__main__':
    main()
