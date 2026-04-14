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
# STEP 2 — Property Details
# ══════════════════════════════════════════════════════════════════════
def _step_2():
    _show_progress()

    ptype = st.session_state.property_type  # "multifamily" | "office" | etc.
    is_mf = ptype == "multifamily"
    is_commercial = ptype in ("office", "retail", "industrial")
    is_land = ptype == "land"

    # Backing store
    pd = st.session_state.property_details

    # ── Property Name ────────────────────────────────────────────────
    pd["property_name"] = st.text_input(
        "Property Name *",
        value=pd.get("property_name", ""),
        placeholder='e.g. "Regent\'s Park"',
        key="pd_property_name",
    )

    # ── Year Built ───────────────────────────────────────────────────
    pd["year_built"] = st.number_input(
        "Year Built *",
        min_value=1800, max_value=2030,
        value=pd.get("year_built", None),
        step=1,
        format="%d",
        key="pd_year_built",
        placeholder="e.g. 1997",
    )

    # ── Stories ───────────────────────────────────────────────────────
    pd["stories"] = st.number_input(
        "Stories",
        min_value=1, max_value=100,
        value=pd.get("stories", None),
        step=1,
        format="%d",
        key="pd_stories",
        placeholder="e.g. 4",
    )

    # ── Total Units (MF only) ────────────────────────────────────────
    if is_mf:
        pd["total_units"] = st.number_input(
            "Total Units *",
            min_value=1, max_value=10000,
            value=pd.get("total_units", None),
            step=1,
            format="%d",
            key="pd_total_units",
            placeholder="e.g. 552",
        )

    # ── Total Rentable SF (commercial only) ──────────────────────────
    if is_commercial:
        pd["total_rentable_sf"] = st.number_input(
            "Total Rentable SF *",
            min_value=1,
            value=pd.get("total_rentable_sf", None),
            step=1,
            format="%d",
            key="pd_total_rentable_sf",
            placeholder="e.g. 85000",
        )

    # ── MF-specific optional fields ──────────────────────────────────
    if is_mf:
        pd["floor_plan_count"] = st.number_input(
            "Floor Plan Count",
            min_value=1,
            value=pd.get("floor_plan_count", None),
            step=1,
            format="%d",
            key="pd_floor_plan_count",
        )
        pd["avg_unit_sf"] = st.number_input(
            "Avg Unit SF",
            min_value=1,
            value=pd.get("avg_unit_sf", None),
            step=1,
            format="%d",
            key="pd_avg_unit_sf",
        )
        col_min, col_max = st.columns(2)
        with col_min:
            pd["min_unit_sf"] = st.number_input(
                "Min Unit SF",
                min_value=1,
                value=pd.get("min_unit_sf", None),
                step=1,
                format="%d",
                key="pd_min_unit_sf",
            )
        with col_max:
            pd["max_unit_sf"] = st.number_input(
                "Max Unit SF",
                min_value=1,
                value=pd.get("max_unit_sf", None),
                step=1,
                format="%d",
                key="pd_max_unit_sf",
            )

    # ── Common optional fields ───────────────────────────────────────
    if not is_land:
        pd["management_company"] = st.text_input(
            "Management Company",
            value=pd.get("management_company", ""),
            placeholder='e.g. "Bozzuto"',
            key="pd_management_company",
        )
    pd["submarket_label"] = st.text_input(
        "Submarket Label",
        value=pd.get("submarket_label", ""),
        placeholder='e.g. "Vienna/Merrifield"',
        key="pd_submarket_label",
    )
    if not is_land:
        pd["utility_structure"] = st.text_input(
            "Utility Structure",
            value=pd.get("utility_structure", ""),
            placeholder="e.g. Tenant: Elec+Gas | LL: Water",
            key="pd_utility_structure",
        )
    pd["zoning_code"] = st.text_input(
        "Zoning Code",
        value=pd.get("zoning_code", ""),
        placeholder='e.g. "PDH \u00b7 PRC"',
        key="pd_zoning_code",
    )
    pd["transit_proximity_notes"] = st.text_area(
        "Transit / Proximity Notes",
        value=pd.get("transit_proximity_notes", ""),
        placeholder="e.g. Vienna Metro 1.3 mi \u00b7 George Mason 0.9 mi",
        key="pd_transit_proximity_notes",
    )

    # ── Asking Price ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Asking Price")
    pricing_mode = st.radio(
        "Pricing",
        ["Enter asking price", "Price Upon Request"],
        index=0 if pd.get("price_upon_request") is not True else 1,
        key="pd_pricing_mode",
        horizontal=True,
    )
    pd["price_upon_request"] = (pricing_mode == "Price Upon Request")

    if not pd["price_upon_request"]:
        pd["asking_price"] = st.number_input(
            "Asking Price ($)",
            min_value=0,
            value=pd.get("asking_price", None),
            step=100000,
            format="%d",
            key="pd_asking_price",
        )
        # Derived price-per-unit / price-per-sf
        asking = pd.get("asking_price")
        if asking and asking > 0:
            if is_mf and pd.get("total_units") and pd["total_units"] > 0:
                ppu = asking / pd["total_units"]
                st.markdown(f"**Price per Unit:** ${ppu:,.0f}")
            elif is_commercial and pd.get("total_rentable_sf") and pd["total_rentable_sf"] > 0:
                ppsf = asking / pd["total_rentable_sf"]
                st.markdown(f"**Price per SF:** ${ppsf:,.2f}")

    # ── Cap Rate ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Cap Rate")
    cap_mode = st.radio(
        "Cap Rate",
        ["Enter cap rate", "Leave blank (auto-generates disclosure language)"],
        index=0 if pd.get("cap_rate_omitted") is not True else 1,
        key="pd_cap_mode",
        horizontal=True,
    )
    pd["cap_rate_omitted"] = (cap_mode != "Enter cap rate")

    if not pd["cap_rate_omitted"]:
        pd["cap_rate"] = st.number_input(
            "Cap Rate (%)",
            min_value=0.0, max_value=30.0,
            value=pd.get("cap_rate", None),
            step=0.01,
            format="%.2f",
            key="pd_cap_rate",
        )
    else:
        st.info(
            "Cap rate not provided. The offering document will include "
            "standard disclosure language: *\"Capitalization rate has not "
            "been provided by the seller. Prospective purchasers are advised "
            "to conduct independent analysis.\"*"
        )

    # ── Validation + navigation ──────────────────────────────────────
    st.markdown("---")
    errors = []

    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.property_details = pd
            st.session_state.wizard_step = 1
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            # Validate required fields
            if not pd.get("property_name", "").strip():
                errors.append(("Property Name", "Property Name is required."))
            if pd.get("year_built") is None:
                errors.append(("Year Built", "Year Built is required."))
            if is_mf and not pd.get("total_units"):
                errors.append(("Total Units", "Total Units is required for multifamily."))
            if is_commercial and not pd.get("total_rentable_sf"):
                errors.append(("Total Rentable SF", "Total Rentable SF is required for commercial."))

            if errors:
                for field, msg in errors:
                    st.error(msg)
            else:
                st.session_state.property_details = pd
                _auto_save()
                st.session_state.wizard_step = 3
                st.rerun()


# ══════════════════════════════════════════════════════════════════════
# STEP 3 — Branding & Contact
# ══════════════════════════════════════════════════════════════════════
def _step_3():
    _show_progress()

    br = st.session_state.branding

    br["broker_firm"] = st.text_input(
        "Broker Firm Name *",
        value=br.get("broker_firm", ""),
        key="br_broker_firm",
    )
    st.caption(
        f"*{_BRAND_NAME} branding appears on the cover page and final "  # PLACEHOLDER — replace when platform name confirmed
        "attribution page automatically. No upload needed.*"
    )

    br["broker_name"] = st.text_input(
        "Broker Name *",
        value=br.get("broker_name", ""),
        key="br_broker_name",
    )
    br["broker_title"] = st.text_input(
        "Broker Title",
        value=br.get("broker_title", ""),
        key="br_broker_title",
    )
    br["phone"] = st.text_input(
        "Phone *",
        value=br.get("phone", ""),
        key="br_phone",
    )
    br["email"] = st.text_input(
        "Email *",
        value=br.get("email", ""),
        key="br_email",
    )
    br["offer_due_date"] = st.date_input(
        "Offer Due Date",
        value=br.get("offer_due_date", None),
        key="br_offer_due_date",
    )

    # ── Broker logo upload ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Broker Logo Upload")
    st.caption("Accepted formats: PNG, JPG  |  Max size: 5 MB")
    logo_file = st.file_uploader(
        "Broker Logo",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="br_logo_upload",
        label_visibility="collapsed",
    )
    if logo_file is not None:
        if logo_file.size > 5 * 1024 * 1024:
            st.error("Logo file exceeds 5 MB limit.")
        else:
            st.image(logo_file, width=200)
            # Save on Continue (not on every rerun)
            br["_logo_file_name"] = logo_file.name

    # ── Validation + navigation ──────────────────────────────────────
    st.markdown("---")
    errors = []

    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.branding = br
            st.session_state.wizard_step = 2
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            if not br.get("broker_firm", "").strip():
                errors.append("Broker Firm Name is required.")
            if not br.get("broker_name", "").strip():
                errors.append("Broker Name is required.")
            if not br.get("phone", "").strip():
                errors.append("Phone is required.")
            email = br.get("email", "").strip()
            if not email:
                errors.append("Email is required.")
            elif "@" not in email:
                errors.append("Email must contain @.")

            if errors:
                for msg in errors:
                    st.error(msg)
            else:
                # Save logo to disk if uploaded
                if logo_file is not None and logo_file.size <= 5 * 1024 * 1024:
                    slug = make_slug(st.session_state.address)
                    ext = Path(logo_file.name).suffix.lower()
                    logo_path = str(
                        _OM_DIR / "data" / "broker_assets" / slug
                        / f"logo{ext}"
                    )
                    write_file(logo_path, logo_file.getvalue())
                    br["logo_path"] = logo_path

                # Serialize date for auto-save
                if br.get("offer_due_date") is not None:
                    import datetime
                    if isinstance(br["offer_due_date"], datetime.date):
                        br["offer_due_date"] = br["offer_due_date"].isoformat()

                st.session_state.branding = br
                _auto_save()
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
