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

# Local om_generator/ module imports — sys.path bootstrap matches the
# convention used by every *_context.py file in this package.
sys.path.insert(0, SCRIPT_DIR)
from audit_trail import setup_audit, finalize_audit  # noqa: E402
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


def run_om_generation(address: str, output_path: str,
                      financial_inputs_path: str = None) -> dict:
    """
    Core OM generation logic. Called by both the CLI and the Streamlit wizard.

    Args:
        address: Property address string.
        output_path: Path to write the output HTML file.
        financial_inputs_path: Optional explicit path to a financial sidecar
            JSON file. If provided, this file is loaded instead of the default
            test_inputs/ search.

    Returns:
        {"success": bool, "output_path": str, "error": str | None}
    """
    audit_handle = setup_audit(address, financial_inputs_path)
    result = {"success": False, "output_path": output_path,
              "error": "Unknown failure"}
    try:
        result = _run_om_generation_inner(address, output_path,
                                          financial_inputs_path)
        return result
    finally:
        finalize_audit(audit_handle, result, output_path)


def _run_om_generation_inner(address: str, output_path: str,
                             financial_inputs_path: str = None) -> dict:
    """Existing OM-generation body. Returns the result dict."""
    import traceback

    try:
        print(f"Generating OM for: {address}")

        # ── Geocode address ───────────────────────────────────────────
        coords = geocode_address(address)
        if coords is None:
            return {"success": False, "output_path": output_path,
                    "error": f"Could not geocode address: {address}"}

        lat, lon = coords
        print(f"  Geocoded: {lat:.4f}, {lon:.4f}")

        # ── Detect county ─────────────────────────────────────────────
        from utils.county_detector import detect_county
        county = detect_county(lat, lon)
        if county == 'unknown':
            print(f"  Warning: Could not detect county for {lat}, {lon}. Defaulting to fairfax.")
            county = 'fairfax'
        print(f"  County: {county}")

        # Load context
        from context_sample import get_sample_context
        ctx = get_sample_context()

        # ── Static page chrome (footer section names + page numbers) ──
        from chrome_context import build_chrome_context
        ctx.update(build_chrome_context())

        # ── Property identity (must run first) ─────────────────────────
        from property_context import build_property_context
        prop_ctx = build_property_context(address, lat, lon, county)
        ctx.update(prop_ctx)
        print(f"  Property wired: {prop_ctx['property_address']}, "
              f"{prop_ctx['property_city']}, {prop_ctx['property_state_abbr']} "
              f"{prop_ctx['property_zip']} | county={prop_ctx['property_county']} | "
              f"metro={prop_ctx['metro_station_name']} ({prop_ctx['metro_distance']}) | "
              f"uni={prop_ctx['university_name_short']} ({prop_ctx['university_distance']})")

        # ── Broker-confirmed identity + branding overrides ────────────
        from identity_context import build_identity_context
        identity_ctx = build_identity_context(financial_inputs_path)
        ctx.update(identity_ctx)
        if identity_ctx:
            print(f"  Identity wired: {len(identity_ctx)} broker-confirmed "
                  f"keys ({', '.join(sorted(identity_ctx))})")

        # ── County-aware data sources sidebar ──────────────────────────
        from data_sources_context import build_data_sources_context
        data_sources_ctx = build_data_sources_context(county)
        ctx.update(data_sources_ctx)
        print(f"  Data sources wired: {len(data_sources_ctx['data_sources'])} entries "
              f"(county={county})")

        # Inject logo base64
        ctx['wo_logo_base64'] = extract_logo_base64(V3_PATH)

        # ── Photo strip (Street View) ────────────────────────────────
        from photo_strip_context import build_photo_strip_context
        photo_ctx = build_photo_strip_context(address, lat, lon)
        ctx.update(photo_ctx)
        has_photos = sum(1 for u in photo_ctx['photo_urls'] if u)
        print(f"  Photo strip wired: {has_photos}/4 headings with Street View coverage")

        # ── Live crime data ──────────────────────────────────────────
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

        # ── Live schools data ─────────────────────────────────────────
        from schools_context import build_schools_context
        live_schools = build_schools_context(lat, lon, county)
        ctx['schools'] = live_schools['schools']
        ctx['school_footnote'] = live_schools['school_footnote']

        for s in live_schools['schools']:
            print(f"  School wired: {s['name']} — SOL {s['sol_pass']}, "
                  f"State Avg {s['state_avg']}, Delta {s['delta']}")

        # ── Live healthcare data ──────────────────────────────────────
        from healthcare_context import build_healthcare_context
        live_healthcare = build_healthcare_context(lat, lon, county)
        ctx['healthcare'] = live_healthcare['healthcare']
        print(f"  Healthcare wired: {live_healthcare['healthcare']['name']} — "
              f"{live_healthcare['healthcare']['distance']}, "
              f"score={live_healthcare['healthcare']['score']}")

        # ── Live demographics data ────────────────────────────────────
        from demographics_context import build_demographics_context
        demo_ctx = build_demographics_context(lat, lon, county)
        ctx['demo'] = demo_ctx['demo']
        print(f"  Demographics wired: income={demo_ctx['demo']['median_income']}, "
              f"pop={demo_ctx['demo']['population']}")

        # ── Live employers data ───────────────────────────────────────
        from employers_context import build_employers_context
        emp_ctx = build_employers_context(lat, lon, county)
        ctx.update(emp_ctx)
        print(f"  Employers wired: {len(emp_ctx['employers'])} employers, "
              f"year={emp_ctx['employers_data_year']}")

        # ── Employer map ──────────────────────────────────────────────
        from employer_map_context import build_employer_map_context
        map_ctx = build_employer_map_context(lat, lon, ctx["employers"], county)
        ctx.update(map_ctx)
        has_map = "yes" if map_ctx.get("employer_map_static_url") else "no"
        print(f"  Employer map wired: {len(map_ctx['employer_map_markers'])} markers, "
              f"static_url={has_map}")

        # ── Live zoning data ──────────────────────────────────────────
        from zoning_context import build_zoning_context
        zoning_ctx = build_zoning_context(lat, lon, county)
        ctx.update(zoning_ctx)
        print(f"  Zoning wired: {zoning_ctx.get('zoning_code', 'N/A')} | "
              f"planning_pts={zoning_ctx.get('planning_pts', 0)} | "
              f"comp_plan={zoning_ctx.get('comp_plan_designation', 'N/A')}")

        # ── Comparable sales ─────────────────────────────────────────
        from comps_context import build_comps_context
        comps_ctx = build_comps_context(
            address=address,
            lat=lat,
            lon=lon,
            county=county,
            submarket_name=ctx.get("submarket_name", ""),
        )
        ctx.update(comps_ctx)
        print(f"  Comps wired: {len(comps_ctx['comps'])} comps, "
              f"tier={comps_ctx.get('_tier', 'empty')}")

        # ── Live development data ─────────────────────────────────────
        from development_context import build_development_context
        dev_ctx = build_development_context(lat, lon, county, zoning_ctx=zoning_ctx)
        ctx.update(dev_ctx)
        print(f"  Development wired: score={dev_ctx['dev_pressure_score']}, "
              f"permits_2mi={dev_ctx['permits_2mi_count']}, "
              f"new_mf={dev_ctx['new_mf_permits_count']}")

        # ── Development map ──────────────────────────────────────────
        from dev_map_context import build_dev_map_context
        dev_map_ctx = build_dev_map_context(lat, lon, county, ctx)
        ctx.update(dev_map_ctx)
        has_dev_map = "yes" if dev_map_ctx.get("dev_map_static_url") else "no"
        print(f"  Dev map static_url={has_dev_map}")

        # ── Live traffic data ─────────────────────────────────────────
        from traffic_context import build_traffic_context
        traffic_ctx = build_traffic_context(lat, lon, county)
        ctx.update(traffic_ctx)
        print(f"  Traffic wired: {traffic_ctx['traffic']['primary_road_name']} "
              f"({traffic_ctx['traffic']['primary_road_count']} ADT), "
              f"{traffic_ctx['traffic']['secondary_road_name']} "
              f"({traffic_ctx['traffic']['secondary_road_count']} ADT)")

        # ── Live amenities data ──────────────────────────────────────
        from amenities_context import build_amenities_context
        amenities_ctx = build_amenities_context(lat, lon, county)
        ctx.update(amenities_ctx)
        counts = [a['count'] for a in amenities_ctx['amenities']]
        print(f"  Amenities wired: {len(amenities_ctx['amenities'])} categories, "
              f"counts={counts}")

        # ── Location map ─────────────────────────────────────────────
        from location_map_context import build_location_map_context
        location_map_ctx = build_location_map_context(
            lat, lon, county, live_schools, live_healthcare, prop_ctx)
        ctx.update(location_map_ctx)
        has_loc_map = "yes" if location_map_ctx.get("location_map_static_url") else "no"
        print(f"  Location map static_url={has_loc_map}")

        # Update the stoplight Development Pressure row to match live score
        dev_score_int = int(ctx.get("dev_pressure_score", 0))
        if dev_score_int <= 25:
            dev_badge, dev_detail = 'Low \u2713', 'Low \u00b7 Supply Constrained'
            dev_dot, dev_badge_cls = 'sl-green', 'badge-green'
            dev_bar_color = 'var(--green)'
        elif dev_score_int <= 60:
            dev_badge, dev_detail = 'Moderate', 'Moderate'
            dev_dot, dev_badge_cls = 'sl-amber', 'badge-amber'
            dev_bar_color = 'var(--amber)'
        else:
            dev_badge, dev_detail = 'High \u26a0', 'High \u00b7 Active Pipeline'
            dev_dot, dev_badge_cls = 'sl-red', 'badge-red'
            dev_bar_color = 'var(--red)'

        for sl in ctx['stoplight_scores']:
            if sl['label'] == 'Development Pressure':
                sl['badge_text'] = dev_badge
                sl['label_detail'] = dev_detail
                sl['bar_width'] = f"{dev_score_int}%"
                sl['bar_color'] = dev_bar_color
                sl['dot_class'] = dev_dot
                sl['badge_class'] = dev_badge_cls
                break

        # ── Financial engine ──────────────────────────────────────────
        from financial_context import build_financial_context
        financial_ctx = build_financial_context(
            address, lat, lon, county, ctx,
            financial_inputs_path=financial_inputs_path)
        ctx.update(financial_ctx)
        if financial_ctx:
            print(f"  Financials wired: type={financial_ctx.get('property_type', 'N/A')}, "
                  f"cap={financial_ctx.get('t12_cap_rate', 'N/A')}, "
                  f"CoC={financial_ctx.get('cash_on_cash', 'N/A')}, "
                  f"IRR={financial_ctx.get('irr', 'N/A')}")
        else:
            print("  Financials: using seed defaults (engine returned empty)")

        # ── Investment highlights ─────────────────────────────────────
        # Must run last — reads from every other builder's output to assemble
        # county-aware, property-specific bullets for the executive summary.
        from investment_highlights_context import build_investment_highlights_context
        highlights_ctx = build_investment_highlights_context(county, ctx)
        ctx.update(highlights_ctx)
        print(f"  Highlights wired: {len(highlights_ctx['investment_highlights'])} bullets")

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
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"OM generated: {output_path} ({len(html):,} chars)")

        # Quick sanity check: ensure no unresolved {{ }} remain
        unresolved = re.findall(r'\{\{.*?\}\}', html)
        if unresolved:
            print(f"WARNING: {len(unresolved)} unresolved template variables found:")
            for var in unresolved[:10]:
                print(f"  {var}")
        else:
            print("All template variables resolved successfully.")

        return {"success": True, "output_path": output_path, "error": None}

    except Exception as e:
        traceback.print_exc()
        return {"success": False, "output_path": output_path, "error": str(e)}


def main():
    """Thin CLI wrapper. Parses argparse, calls run_om_generation()."""
    parser = argparse.ArgumentParser(description='Generate OM HTML from Jinja2 templates')
    parser.add_argument('address', nargs='?', default=DEFAULT_ADDRESS,
                        help='Property address to generate OM for')
    parser.add_argument('--output', '-o', default=DEFAULT_OUTPUT, help='Output HTML path')
    parser.add_argument('--financial-inputs', '-f', default=None,
                        help='Path to financial inputs JSON sidecar')
    args = parser.parse_args()

    result = run_om_generation(args.address, args.output, args.financial_inputs)
    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
    print(f"OM generated: {result['output_path']}")


if __name__ == '__main__':
    main()
