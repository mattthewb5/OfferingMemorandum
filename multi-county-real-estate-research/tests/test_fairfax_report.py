"""Tests for Fairfax report alignment with Loudoun pattern.

Validates syntax, required functions, no Loudoun text leaks,
and Athens file protection.
"""
import pytest
import ast
import subprocess


def test_syntax():
    """Verify fairfax_report_new.py parses without syntax errors."""
    with open('reports/fairfax_report_new.py') as f:
        ast.parse(f.read())


def test_required_functions_exist():
    """Verify all spec-required display functions are defined."""
    with open('reports/fairfax_report_new.py') as f:
        source = f.read()

    tree = ast.parse(source)
    function_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    required = [
        'display_location_quality_section',
        'display_schools_section',
        'display_cell_towers_section',
        'display_neighborhood_section',
        'display_community_amenities_section',
        'display_demographics_section_fairfax',
        'display_economic_indicators_section',
        'display_medical_access_section',
        'display_development_section',
        'display_zoning_section',
        'display_comparable_sales_section',
        'display_ai_analysis_section',
        'display_footer',
        'render_report',
    ]
    for fn in required:
        assert fn in function_names, f"Missing required function: {fn}"


def test_no_loudoun_references():
    """Ensure no forbidden Loudoun text leaked into Fairfax report."""
    with open('reports/fairfax_report_new.py') as f:
        content = f.read()

    forbidden = [
        'Loudoun County Public Schools',
        'LCPS Boundaries',
        'Loudoun County ACFR',
        'from reports.loudoun_report import',
        'import loudoun_report',
    ]
    for term in forbidden:
        assert term not in content, f"Forbidden Loudoun reference found: {term}"


def test_dead_code_removed():
    """Verify dead standalone sections were removed."""
    with open('reports/fairfax_report_new.py') as f:
        source = f.read()

    tree = ast.parse(source)
    function_names = {
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    removed = [
        'display_traffic_section',
        'display_emergency_services_section',
        'display_subdivisions_section',
    ]
    for fn in removed:
        assert fn not in function_names, f"Dead code not removed: {fn}"


def test_section_order_in_render_report():
    """Verify render_report calls sections in spec order."""
    with open('reports/fairfax_report_new.py') as f:
        content = f.read()

    # Extract the render_report function body
    start = content.index('def render_report(')
    # Find the section calls
    section_calls = [
        'display_schools_section',
        'display_location_quality_section',
        'display_cell_towers_section',
        'display_neighborhood_section',
        'display_community_amenities_section',
        'display_demographics_section_fairfax',
        'display_economic_indicators_section',
        'display_medical_access_section',
        'display_development_section',
        'display_zoning_section',
        'display_comparable_sales_section',
        'display_ai_analysis_section',
        'display_footer',
    ]

    render_body = content[start:]
    positions = []
    for call in section_calls:
        pos = render_body.find(call + '(')
        assert pos != -1, f"Section call not found in render_report: {call}"
        positions.append(pos)

    # Verify order is correct (each position > previous)
    for i in range(1, len(positions)):
        assert positions[i] > positions[i-1], (
            f"Section order wrong: {section_calls[i]} appears before {section_calls[i-1]}"
        )


def test_data_sources_table_has_fairfax_entries():
    """Verify data sources footer uses Fairfax-specific sources."""
    with open('reports/fairfax_report_new.py') as f:
        content = f.read()

    fairfax_sources = [
        'Fairfax County ACFR',
        'Fairfax County Public Schools (FCPS) Boundaries',
        'Fairfax County Open Data',
        'VDOT Bidirectional Traffic Volume Database',
        'WMATA Station Data / Fairfax County GIS',
        'Fairfax County GIS Parks',
        'Fairfax Street Centerline GIS',
        'Fairfax County Noise Overlay Districts',
        'FairfaxSubdivisionsAnalysis',
    ]
    for source in fairfax_sources:
        assert source in content, f"Missing Fairfax data source: {source}"


def test_athens_not_modified():
    """Verify Athens files were not modified."""
    result = subprocess.run(
        ['git', 'diff', 'main', '--name-only'],
        capture_output=True, text=True
    )
    modified = result.stdout.strip().split('\n') if result.stdout.strip() else []
    athens_files = [f for f in modified if 'streamlit_app.py' in f or '/athens/' in f]
    assert len(athens_files) == 0, f"Athens files modified: {athens_files}"
