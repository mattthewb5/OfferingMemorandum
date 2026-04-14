"""
Provenance — OM Generator Wizard

Standalone Streamlit app that collects broker inputs, assembles the full
context dict, and invokes the OM generation pipeline.

Run:  python -m streamlit run provenance_app.py
"""

import re
import sys
from pathlib import Path

import streamlit as st

# ── Path setup (match existing repo pattern) ─────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent
_OM_DIR = _REPO_ROOT / "om_generator"
sys.path.insert(0, str(_OM_DIR))
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from om_generator.storage import (
    write_json, read_json, file_exists, ensure_dir, write_file,
)
from generate_om import geocode_address
from utils.county_detector import detect_county


# ── Supported counties ───────────────────────────────────────────────
_SUPPORTED_COUNTIES = {"fairfax", "loudoun"}


# ── Slug helper ──────────────────────────────────────────────────────
def make_slug(address: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", address.lower()).strip("-")


# ── Data directory scaffolding ───────────────────────────────────────
_DATA_DIRS = [
    _OM_DIR / "data" / "drafts",
    _OM_DIR / "data" / "property_photos",
    _OM_DIR / "data" / "comps",
    _OM_DIR / "data" / "rent_rolls",
    _OM_DIR / "data" / "t12",
    _OM_DIR / "data" / "financial_inputs",
    _OM_DIR / "data" / "broker_assets",
    _OM_DIR / "output",
]

for _d in _DATA_DIRS:
    ensure_dir(str(_d))


# ── Branding ─────────────────────────────────────────────────────────
_APP_TITLE = "West Oxford Advisors — OM Generator"  # PLACEHOLDER — replace when platform name confirmed
_BRAND_NAME = "West Oxford Advisors"  # PLACEHOLDER — replace when platform name confirmed
_TAGLINE = "built on the record"  # PLACEHOLDER — replace when platform name confirmed
_NAVY = "#1B2A4A"
_GOLD = "#C9A84C"


def _apply_styles():
    """Inject custom CSS for branding. All CSS in one place."""
    st.markdown(f"""
    <style>
        /* Header bar */
        .wo-header {{
            background-color: {_NAVY};
            padding: 1.2rem 2rem;
            margin: -1rem -1rem 1.5rem -1rem;
            display: flex;
            align-items: baseline;
            gap: 1rem;
        }}
        .wo-header-title {{
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .wo-header-tagline {{
            color: {_GOLD};
            font-size: 0.95rem;
            font-style: italic;
        }}
        /* Progress bar accent */
        .stProgress > div > div > div > div {{
            background-color: {_GOLD};
        }}
        /* Step label */
        .step-label {{
            color: {_NAVY};
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        /* Success card */
        .success-card {{
            background-color: #f0faf0;
            border: 1px solid #b2dfb2;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin: 1rem 0;
        }}
        .success-card .check {{
            color: #2e7d32;
            font-weight: 700;
        }}
        /* Error card */
        .error-card {{
            background-color: #fff8e1;
            border: 1px solid #ffe082;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin: 1rem 0;
        }}
    </style>
    """, unsafe_allow_html=True)


# ── Session state defaults ───────────────────────────────────────────
DEFAULTS = {
    "wizard_step": 1,
    "address": "",
    "county": None,
    "property_type": None,
    "geocode_result": None,
    "property_details": {},
    "branding": {},
    "uploaded_photos": [],
    "uploaded_comps": None,
    "uploaded_rent_roll": None,
    "uploaded_t12": None,
    "financials": {},
    "rent_roll_parsed": None,
    "section_overrides": {},
    "generation_result": None,
    "auto_save_path": None,
}

for _key, _default in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _default


# ── Auto-save ────────────────────────────────────────────────────────
def _auto_save():
    """Write current session state as a draft JSON (excludes binary data)."""
    address = st.session_state.get("address", "")
    if not address:
        return
    slug = make_slug(address)
    draft_path = str(_OM_DIR / "data" / "drafts" / f"{slug}.json")
    # Serialize only JSON-safe state
    saveable = {}
    for k, v in DEFAULTS.items():
        val = st.session_state.get(k, v)
        # Skip non-serializable values
        if isinstance(val, (str, int, float, bool, list, dict, type(None))):
            saveable[k] = val
    write_json(draft_path, saveable)
    st.session_state["auto_save_path"] = draft_path


def _try_restore_draft(address: str) -> bool:
    """Check if a draft exists for this address. Returns True if found."""
    if not address:
        return False
    slug = make_slug(address)
    draft_path = str(_OM_DIR / "data" / "drafts" / f"{slug}.json")
    return file_exists(draft_path)


def _restore_draft(address: str):
    """Restore session state from a draft JSON."""
    slug = make_slug(address)
    draft_path = str(_OM_DIR / "data" / "drafts" / f"{slug}.json")
    draft = read_json(draft_path)
    for k, v in draft.items():
        if k in DEFAULTS:
            st.session_state[k] = v


# ── Progress display ─────────────────────────────────────────────────
_STEP_LABELS = {
    1: "Address & Property Type",
    2: "Property Details",
    3: "Branding & Contact",
    4: "Files & Photos",
    5: "Financials",
    6: "Review & Generate",
}


def _show_progress():
    """Display step progress bar and label."""
    step = st.session_state.wizard_step
    total = 6
    pct = (step - 1) / (total - 1)
    st.markdown(
        f'<div class="step-label">Step {step} of {total} — '
        f'{_STEP_LABELS[step]}</div>',
        unsafe_allow_html=True,
    )
    st.progress(pct)


# ══════════════════════════════════════════════════════════════════════
# STEP 1 — Address, County & Property Type
# ══════════════════════════════════════════════════════════════════════
def _step_1():
    _show_progress()

    # ── Address input ────────────────────────────────────────────────
    address = st.text_input(
        "Property Address",
        value=st.session_state.address,
        placeholder="e.g. 9333 Clocktower Place, Fairfax VA 22031",
        key="address_input",
    )

    # Sync typed address to session state (without clearing geocode on
    # every keystroke — only the button triggers geocoding)
    if address != st.session_state.address:
        st.session_state.address = address

    # ── Draft restore offer ──────────────────────────────────────────
    if (address
            and st.session_state.geocode_result is None
            and _try_restore_draft(address)):
        st.info("A saved draft was found for this address. Restore it?")
        col_r, col_f, _ = st.columns([1, 1, 3])
        with col_r:
            if st.button("Restore"):
                _restore_draft(address)
                st.rerun()
        with col_f:
            if st.button("Start Fresh"):
                pass  # Continue with blank state

    # ── Geocode button ───────────────────────────────────────────────
    geocode_result = st.session_state.geocode_result

    if geocode_result is None:
        if st.button("Look Up Address", disabled=not address):
            with st.spinner("Looking up address..."):
                coords = geocode_address(address)
            if coords is None:
                st.markdown(
                    '<div class="error-card">'
                    "&#9888;&#65039; Address not found. Please check the "
                    "address and try again.</div>",
                    unsafe_allow_html=True,
                )
                return
            lat, lon = coords
            county = detect_county(lat, lon)
            if county == "unknown" or county not in _SUPPORTED_COUNTIES:
                st.markdown(
                    '<div class="error-card">'
                    "&#9888;&#65039; This address is outside the supported "
                    "counties (Fairfax and Loudoun, VA).</div>",
                    unsafe_allow_html=True,
                )
                return
            # Store geocode result
            st.session_state.geocode_result = {
                "lat": lat, "lon": lon, "county": county,
            }
            st.session_state.county = county
            st.session_state.address = address
            st.rerun()
        return  # Don't render anything below until geocode succeeds

    # ── County confirmation card ─────────────────────────────────────
    gr = geocode_result
    county_display = gr["county"].title() + " County"
    # Parse city/state/zip from address for display
    st.markdown(
        f'<div class="success-card">'
        f'<span class="check">&#10003;</span>&nbsp; {address}<br>'
        f'&nbsp;&nbsp;&nbsp;{county_display} — supported &#10003;'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("Not right? Edit address", type="secondary"):
        st.session_state.geocode_result = None
        st.session_state.county = None
        st.session_state.property_type = None
        st.rerun()

    # ── Property type selector ───────────────────────────────────────
    st.markdown("#### Select Property Type")
    prop_types = ["Multifamily", "Office", "Retail", "Industrial", "Land"]
    current = st.session_state.property_type
    # Find current index for default
    default_idx = None
    if current:
        lower_map = {p.lower(): i for i, p in enumerate(prop_types)}
        default_idx = lower_map.get(current, None)

    selected = st.radio(
        "Property Type",
        prop_types,
        index=default_idx,
        label_visibility="collapsed",
        key="property_type_radio",
    )

    # ── Continue button ──────────────────────────────────────────────
    can_continue = geocode_result is not None and selected is not None
    if st.button("Continue", disabled=not can_continue, type="primary"):
        st.session_state.property_type = selected.lower()
        _auto_save()
        st.session_state.wizard_step = 2
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# STEP STUBS (to be built in subsequent phases)
# ══════════════════════════════════════════════════════════════════════
def _step_2():
    _show_progress()
    st.info("Step 2 — Property Details (coming next)")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.wizard_step = 1
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            st.session_state.wizard_step = 3
            st.rerun()


def _step_3():
    _show_progress()
    st.info("Step 3 — Branding & Contact (coming next)")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.wizard_step = 2
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            st.session_state.wizard_step = 4
            st.rerun()


def _step_4():
    _show_progress()
    st.info("Step 4 — Files & Photos (coming next)")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.wizard_step = 3
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            st.session_state.wizard_step = 5
            st.rerun()


def _step_5():
    _show_progress()
    st.info("Step 5 — Financials (coming next)")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.wizard_step = 4
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            st.session_state.wizard_step = 6
            st.rerun()


def _step_6():
    _show_progress()
    st.info("Step 6 — Review & Generate (coming next)")
    if st.button("Back"):
        st.session_state.wizard_step = 5
        st.rerun()


# ══════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════
def main():
    st.set_page_config(
        page_title=_APP_TITLE,  # PLACEHOLDER — replace when platform name confirmed
        layout="centered",
    )

    _apply_styles()

    # ── Header ───────────────────────────────────────────────────────
    st.markdown(
        f'<div class="wo-header">'
        f'<span class="wo-header-title">{_BRAND_NAME}</span>'  # PLACEHOLDER — replace when platform name confirmed
        f'<span class="wo-header-tagline">{_TAGLINE}</span>'  # PLACEHOLDER — replace when platform name confirmed
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Step router ──────────────────────────────────────────────────
    step = st.session_state.wizard_step
    {
        1: _step_1,
        2: _step_2,
        3: _step_3,
        4: _step_4,
        5: _step_5,
        6: _step_6,
    }[step]()


if __name__ == "__main__":
    main()
