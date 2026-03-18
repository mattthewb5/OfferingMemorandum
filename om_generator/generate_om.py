#!/usr/bin/env python3
"""
NewCo OM Generator — Jinja2 Template Renderer

Assembles a context dictionary, renders the Jinja2 template, and outputs
a static HTML file visually identical to the v3 prototype.

Usage:
    python generate_om.py                    # outputs om_output.html
    python generate_om.py --output my.html   # custom output path
"""
import argparse
import os
import re
import sys

from jinja2 import Environment, FileSystemLoader

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, 'templates')
V3_PATH = os.path.join(SCRIPT_DIR, '..', 'investigation', 'newco_om_v3_regents_park.html')
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, 'om_output.html')


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
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT, help='Output HTML path')
    args = parser.parse_args()

    # Load context
    from context_sample import get_sample_context
    ctx = get_sample_context()

    # Inject logo base64
    ctx['wo_logo_base64'] = extract_logo_base64(V3_PATH)

    # ── Live crime data ──────────────────────────────────────────────
    # Subject property: 9333 Clocktower Place, Fairfax VA 22031
    # Geocoded via US Census Bureau geocoder (geocoding.geo.census.gov)
    SUBJECT_LAT = 38.8731
    SUBJECT_LON = -77.2689

    from crime_context import build_crime_context
    live_crime = build_crime_context(SUBJECT_LAT, SUBJECT_LON)
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
    live_schools = build_schools_context(SUBJECT_LAT, SUBJECT_LON)
    ctx['schools'] = live_schools['schools']
    ctx['school_footnote'] = live_schools['school_footnote']

    for s in live_schools['schools']:
        print(f"  School wired: {s['name']} — SOL {s['sol_pass']}, "
              f"State Avg {s['state_avg']}, Delta {s['delta']}")

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
