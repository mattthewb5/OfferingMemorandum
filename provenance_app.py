"""
Provenance — OM Generator Wizard

Standalone Streamlit app that collects broker inputs, assembles the full
context dict, and invokes the OM generation pipeline.

Run:  python -m streamlit run provenance_app.py
"""

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

# ── Path setup (match existing repo pattern) ─────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent
_OM_DIR = _REPO_ROOT / "om_generator"
sys.path.insert(0, str(_OM_DIR))
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from om_generator.storage import (
    write_json, read_json, file_exists, ensure_dir, write_file, read_file,
    read_text,
)
from generate_om import geocode_address, run_om_generation
from utils.county_detector import detect_county


# ── Supported counties ───────────────────────────────────────────────
_SUPPORTED_COUNTIES = {"fairfax", "loudoun"}


# ── Slug helper ──────────────────────────────────────────────────────
# Single source of truth lives in om_generator/address_slug.py so the
# audit-trail filenames stay byte-identical with the wizard's writes.
from address_slug import make_address_slug as make_slug  # noqa: E402


# ── Data directory scaffolding ───────────────────────────────────────
_DATA_DIRS = [
    _OM_DIR / "data" / "drafts",
    _OM_DIR / "data" / "property_photos",
    _OM_DIR / "data" / "comps",
    _OM_DIR / "data" / "rent_rolls",
    _OM_DIR / "data" / "t12",
    _OM_DIR / "data" / "property_inputs",
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


# ══════════════════════════════════════════════════════════════════════
# STEP 4 — Files & Photos
# ══════════════════════════════════════════════════════════════════════

_COMPS_TEMPLATE_CSV = (
    "name,units,sale_price,price_per_unit,cap_rate,sale_date,source\n"
)


def _step_4():
    _show_progress()

    slug = make_slug(st.session_state.address)

    st.caption(
        "*All uploads are optional. The OM will generate using available "
        "public data where files are not provided. Uploading your own data "
        "always produces a stronger document.*"
    )

    # ── Section A — Property Photos ─────────────────────────────────
    st.markdown("#### Property Photos")
    st.caption("JPG, JPEG, or PNG  |  Up to 10 files  |  Max 10 MB each")
    photos = st.file_uploader(
        "Property Photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="s4_photos",
        label_visibility="collapsed",
    )
    if photos:
        saved_paths = []
        photo_dir = str(_OM_DIR / "data" / "property_photos" / slug)
        ensure_dir(photo_dir)
        cols = st.columns(min(len(photos), 5))
        for i, photo in enumerate(photos[:10]):
            if photo.size > 10 * 1024 * 1024:
                st.error(f"{photo.name} exceeds 10 MB limit — skipped.")
                continue
            ext = Path(photo.name).suffix.lower() or ".jpg"
            save_path = str(
                Path(photo_dir) / f"{i:02d}{ext}"
            )
            write_file(save_path, photo.getvalue())
            saved_paths.append(save_path)
            with cols[i % len(cols)]:
                st.image(photo, width=120)
        st.session_state.uploaded_photos = saved_paths
        if len(photos) > 10:
            st.warning("Only the first 10 photos were saved.")
    st.caption("*Photos appear in the hero strip. First photo is the hero image.*")

    # ── Section B — Comparable Sales ────────────────────────────────
    st.markdown("---")
    st.markdown("#### Comparable Sales CSV")
    st.caption("Optional — overrides automated deed record comps")

    st.download_button(
        "Download template",
        data=_COMPS_TEMPLATE_CSV,
        file_name="comps_template.csv",
        mime="text/csv",
        key="s4_comps_template",
    )

    comps_file = st.file_uploader(
        "Comparable Sales CSV",
        type=["csv"],
        key="s4_comps",
        label_visibility="collapsed",
    )
    if comps_file is not None:
        try:
            comps_df = pd.read_csv(comps_file)
            required_cols = {
                "name", "units", "sale_price", "price_per_unit",
                "cap_rate", "sale_date", "source",
            }
            actual_cols = {c.strip().lower() for c in comps_df.columns}
            missing = required_cols - actual_cols
            if missing:
                st.error(
                    f"Missing required columns: {', '.join(sorted(missing))}. "
                    f"Required: {', '.join(sorted(required_cols))}"
                )
            else:
                save_path = str(_OM_DIR / "data" / "comps" / f"{slug}.csv")
                write_file(save_path, comps_file.getvalue())
                st.session_state.uploaded_comps = save_path
                st.success(f"{len(comps_df)} comparable sales loaded.")
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")

    # ── Section C — Rent Roll ───────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Rent Roll")
    st.caption("CSV or Excel export from your property management system")

    rr_file = st.file_uploader(
        "Rent Roll",
        type=["csv", "xlsx", "xls"],
        key="s4_rent_roll",
        label_visibility="collapsed",
    )
    if rr_file is not None:
        ext = Path(rr_file.name).suffix.lower()
        rr_dir = str(_OM_DIR / "data" / "rent_rolls" / slug)
        ensure_dir(rr_dir)
        rr_path = str(Path(rr_dir) / f"rent_roll{ext}")
        write_file(rr_path, rr_file.getvalue())
        st.session_state.uploaded_rent_roll = rr_path
        # Count rows for confirmation
        try:
            if ext in (".xlsx", ".xls"):
                row_count = len(pd.read_excel(rr_path))
            else:
                row_count = len(pd.read_csv(rr_path))
            st.success(f"rent_roll{ext} uploaded ({row_count} rows detected).")
        except Exception:
            st.success(f"rent_roll{ext} uploaded.")
        st.warning(
            "Rent roll uploaded — you'll review the parsed data in "
            "Step 5 before generating."
        )
    elif st.session_state.uploaded_rent_roll:
        st.info(
            f"Rent roll already uploaded: "
            f"{Path(st.session_state.uploaded_rent_roll).name}"
        )
    else:
        st.caption(
            "*No rent roll uploaded. The Financial Analysis section will "
            "show market-rate estimates. Upload a rent roll for actual "
            "in-place rent data.*"
        )

    # ── Section D — T-12 Operating Statement ────────────────────────
    st.markdown("---")
    st.markdown("#### T-12 Operating Statement")
    st.caption("CSV or Excel  |  Line-item format preferred")

    t12_file = st.file_uploader(
        "T-12 Operating Statement",
        type=["csv", "xlsx", "xls"],
        key="s4_t12",
        label_visibility="collapsed",
    )
    if t12_file is not None:
        ext = Path(t12_file.name).suffix.lower()
        t12_dir = str(_OM_DIR / "data" / "t12" / slug)
        ensure_dir(t12_dir)
        t12_path = str(Path(t12_dir) / f"t12{ext}")
        write_file(t12_path, t12_file.getvalue())
        st.session_state.uploaded_t12 = t12_path
        st.success(f"t12{ext} uploaded.")
    elif st.session_state.uploaded_t12:
        st.info(
            f"T-12 already uploaded: "
            f"{Path(st.session_state.uploaded_t12).name}"
        )
    else:
        st.caption(
            "*No T-12 uploaded. You'll enter operating figures manually "
            "in Step 5.*"
        )

    # ── Navigation ──────────────────────────────────────────────────
    st.markdown("---")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.wizard_step = 3
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            _auto_save()
            st.session_state.wizard_step = 5
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
# STEP 5 — Financials
# ══════════════════════════════════════════════════════════════════════

_RENT_ROLL_PARSE_PROMPT = """
You are parsing a property rent roll export. Extract each unit's data and return ONLY valid JSON, no other text.

Required JSON structure:
{
  "units": [
    {
      "unit_number": "string or null",
      "bedrooms": number or null,
      "bathrooms": number or null,
      "sq_ft": number or null,
      "monthly_rent": number or null,
      "lease_start": "YYYY-MM-DD or null",
      "lease_end": "YYYY-MM-DD or null",
      "status": "occupied | vacant | unknown"
    }
  ],
  "summary": {
    "total_units": number,
    "occupied_units": number,
    "vacant_units": number,
    "avg_monthly_rent": number,
    "parse_notes": "any ambiguities or flags"
  }
}

If a field is absent or unclear, use null. Do not invent data.
"""


def _parse_rent_roll_with_claude(file_path: str) -> dict | None:
    """Send rent roll file contents to Claude API for structured extraction.

    Returns parsed dict on success, None on failure.
    """
    try:
        from core.api_config import get_api_key
        import anthropic

        api_key = get_api_key("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        # Read file content — handle CSV and Excel
        ext = Path(file_path).suffix.lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path)
            file_text = df.to_csv(index=False)
        else:
            file_text = read_text(file_path)

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": (
                    f"{_RENT_ROLL_PARSE_PROMPT}\n\n"
                    f"--- RENT ROLL DATA ---\n{file_text}"
                ),
            }],
        )

        raw = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)

    except Exception as e:
        print(f"  Rent roll parse error: {e}")
        return None


def _build_unit_mix_from_parse(parsed: dict) -> list[dict]:
    """Convert rent_roll_parsed units into unit mix rows grouped by bedroom count."""
    from collections import defaultdict
    groups = defaultdict(lambda: {"count": 0, "total_sf": 0, "total_rent": 0})
    for u in parsed.get("units", []):
        br = u.get("bedrooms")
        if br is None:
            br = -1
        g = groups[br]
        g["count"] += 1
        g["total_sf"] += (u.get("sq_ft") or 0)
        g["total_rent"] += (u.get("monthly_rent") or 0)

    rows = []
    for br in sorted(groups.keys()):
        g = groups[br]
        if g["count"] == 0:
            continue
        if br == 0:
            label = "Studio"
        elif br == -1:
            label = "Unknown"
        else:
            label = f"{br} BR"
        rows.append({
            "Unit Type": label,
            "Count": g["count"],
            "Avg SF": int(g["total_sf"] / g["count"]) if g["count"] else 0,
            "In-Place Rent ($/mo)": int(g["total_rent"] / g["count"]) if g["count"] else 0,
        })
    return rows if rows else [{"Unit Type": "", "Count": 0, "Avg SF": 0, "In-Place Rent ($/mo)": 0}]


def _step_5():
    _show_progress()

    ptype = st.session_state.property_type
    is_mf = ptype == "multifamily"
    is_commercial = ptype in ("office", "retail", "industrial")
    is_land = ptype == "land"

    fin = st.session_state.financials

    # ── Step 5A — Rent Roll Parse & Confirmation ────────────────────
    if st.session_state.uploaded_rent_roll and is_mf:
        if st.session_state.rent_roll_parsed is None:
            if "rent_roll_parse_failed" not in st.session_state:
                st.session_state.rent_roll_parse_failed = False

            if not st.session_state.rent_roll_parse_failed:
                with st.spinner("Parsing rent roll with AI — this takes a few seconds..."):
                    parsed = _parse_rent_roll_with_claude(
                        st.session_state.uploaded_rent_roll
                    )

                if parsed and "units" in parsed:
                    st.session_state.rent_roll_parsed = parsed
                    st.rerun()
                else:
                    st.session_state.rent_roll_parse_failed = True
                    st.rerun()

            if st.session_state.rent_roll_parse_failed:
                st.warning(
                    "Couldn't parse rent roll automatically. "
                    "You can enter figures manually below."
                )
                if st.button("Enter Manually", key="rr_enter_manual"):
                    st.session_state.rent_roll_parse_failed = False
                    st.session_state.uploaded_rent_roll = None

        elif st.session_state.rent_roll_parsed is not None:
            parsed = st.session_state.rent_roll_parsed
            summary = parsed.get("summary", {})
            total_u = summary.get("total_units", len(parsed.get("units", [])))
            occ = summary.get("occupied_units", 0)
            vac = summary.get("vacant_units", 0)
            avg_rent = summary.get("avg_monthly_rent", 0)
            occ_pct = (occ / total_u * 100) if total_u > 0 else 0
            notes = summary.get("parse_notes", "")

            st.markdown(
                f"""<div class="success-card">
<b>Rent Roll Parsed</b> <span class="check">&#10003;</span><br>
<code style="font-size:0.9rem;">
Total units:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{total_u}<br>
Occupied:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{occ}&nbsp;&nbsp;&nbsp;({occ_pct:.1f}%)<br>
Vacant:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{vac}<br>
Avg monthly rent:&nbsp;${avg_rent:,.0f}
</code><br>
{f'<em>Parse notes: {notes}</em><br>' if notes else ''}
<em>Does this look right?</em>
</div>""",
                unsafe_allow_html=True,
            )
            col_ok, col_rej, _ = st.columns([1, 1, 3])
            with col_ok:
                if st.button("Looks right — continue", key="rr_confirm"):
                    pass  # parsed data stays; flows into unit mix below
            with col_rej:
                if st.button("Enter manually instead", key="rr_reject"):
                    st.session_state.rent_roll_parsed = None
                    st.rerun()

    # ── Step 5B — Financial Input Forms (property-type-aware) ───────
    if is_mf:
        _step_5b_multifamily(fin)
    elif is_commercial:
        _step_5b_commercial(fin, ptype)
    elif is_land:
        st.info(
            "No financial inputs required for Land listings. "
            "Pro forma assumptions below are optional."
        )

    # ── Step 5C — Pro Forma & Financing Assumptions ─────────────────
    _step_5c_proforma(fin, is_land)

    # ── Missing-field warnings ──────────────────────────────────────
    _step_5_missing_field_warnings(fin, is_mf, is_commercial, is_land)

    # ── Navigation ──────────────────────────────────────────────────
    st.markdown("---")
    col_b, col_c, _ = st.columns([1, 1, 3])
    with col_b:
        if st.button("Back"):
            st.session_state.financials = fin
            st.session_state.wizard_step = 4
            st.rerun()
    with col_c:
        if st.button("Continue", type="primary"):
            st.session_state.financials = fin
            _assemble_property_json(fin)
            _auto_save()
            st.session_state.wizard_step = 6
            st.rerun()


# ── Step 5B — Multifamily ───────────────────────────────────────────
def _step_5b_multifamily(fin: dict):
    """Render MF-specific financial input forms: unit mix + T-12 + live NOI."""

    st.markdown("#### Unit Mix")

    # Pre-populate from rent roll parse if available, else from saved state
    if "unit_mix_df" not in st.session_state:
        parsed = st.session_state.rent_roll_parsed
        if parsed:
            rows = _build_unit_mix_from_parse(parsed)
        elif fin.get("unit_mix_rows"):
            rows = fin["unit_mix_rows"]
        else:
            rows = [{"Unit Type": "", "Count": 0, "Avg SF": 0, "In-Place Rent ($/mo)": 0}]
        st.session_state.unit_mix_df = pd.DataFrame(rows)

    edited_mix = st.data_editor(
        st.session_state.unit_mix_df,
        num_rows="dynamic",
        use_container_width=True,
        key="unit_mix_editor",
        column_config={
            "Unit Type": st.column_config.TextColumn("Unit Type", width="medium"),
            "Count": st.column_config.NumberColumn("Count", min_value=0, step=1),
            "Avg SF": st.column_config.NumberColumn("Avg SF", min_value=0, step=1),
            "In-Place Rent ($/mo)": st.column_config.NumberColumn(
                "In-Place Rent ($/mo)", min_value=0, step=50, format="$%d",
            ),
        },
    )

    # Persist edits back so they survive reruns
    st.session_state.unit_mix_df = edited_mix
    fin["unit_mix_rows"] = edited_mix.to_dict(orient="records")

    # ── T-12 Income & Expenses ──────────────────────────────────────
    st.markdown("---")
    st.markdown("#### T-12 Income & Expenses")

    t12 = fin.get("t12", {})

    # --- Income ---
    st.markdown("**Income**")
    t12["gpr"] = st.number_input(
        "Gross Potential Rent ($/yr)",
        min_value=0,
        value=t12.get("gpr", None),
        step=10000,
        format="%d",
        key="t12_gpr",
        placeholder="e.g. 16428000",
    )
    t12["vacancy_pct"] = st.number_input(
        "Vacancy Rate (%)",
        min_value=0.0, max_value=100.0,
        value=t12.get("vacancy_pct", None),
        step=0.1,
        format="%.1f",
        key="t12_vacancy_pct",
        placeholder="e.g. 4.5",
    )
    t12["credit_loss_pct"] = st.number_input(
        "Credit / Bad Debt Rate (%)",
        min_value=0.0, max_value=100.0,
        value=t12.get("credit_loss_pct", None),
        step=0.1,
        format="%.1f",
        key="t12_credit_loss_pct",
        placeholder="e.g. 0.5",
    )

    # --- Expenses ---
    st.markdown("**Expenses (annual $)**")
    t12["real_estate_taxes"] = st.number_input(
        "Real Estate Taxes",
        min_value=0,
        value=t12.get("real_estate_taxes", None),
        step=10000,
        format="%d",
        key="t12_re_taxes",
        placeholder="e.g. 1385000",
    )
    t12["insurance"] = st.number_input(
        "Insurance",
        min_value=0,
        value=t12.get("insurance", None),
        step=5000,
        format="%d",
        key="t12_insurance",
        placeholder="e.g. 345000",
    )
    t12["repairs"] = st.number_input(
        "Repairs & Maintenance",
        min_value=0,
        value=t12.get("repairs", None),
        step=5000,
        format="%d",
        key="t12_repairs",
        placeholder="e.g. 580000",
    )
    t12["mgmt_pct"] = st.number_input(
        "Property Management (% of EGI)",
        min_value=0.0, max_value=100.0,
        value=t12.get("mgmt_pct", None),
        step=0.5,
        format="%.1f",
        key="t12_mgmt_pct",
        placeholder="e.g. 5.0",
    )
    t12["utilities"] = st.number_input(
        "Utilities (Landlord-Paid)",
        min_value=0,
        value=t12.get("utilities", None),
        step=5000,
        format="%d",
        key="t12_utilities",
        placeholder="e.g. 485000",
    )
    t12["admin"] = st.number_input(
        "Administrative",
        min_value=0,
        value=t12.get("admin", None),
        step=5000,
        format="%d",
        key="t12_admin",
        placeholder="e.g. 245000",
    )
    t12["reserves"] = st.number_input(
        "Replacement Reserves",
        min_value=0,
        value=t12.get("reserves", None),
        step=1000,
        format="%d",
        key="t12_reserves",
    )

    fin["t12"] = t12

    # ── Live NOI Summary ────────────────────────────────────────────
    gpr = t12.get("gpr") or 0
    vac_pct = (t12.get("vacancy_pct") or 0) / 100.0
    credit_pct = (t12.get("credit_loss_pct") or 0) / 100.0
    vacancy_loss = gpr * vac_pct
    credit_loss = gpr * credit_pct
    egi = gpr - vacancy_loss - credit_loss

    mgmt_pct_val = (t12.get("mgmt_pct") or 0) / 100.0
    management = egi * mgmt_pct_val

    re_taxes = t12.get("real_estate_taxes") or 0
    insurance = t12.get("insurance") or 0
    repairs = t12.get("repairs") or 0
    utilities = t12.get("utilities") or 0
    admin = t12.get("admin") or 0
    reserves = t12.get("reserves") or 0

    total_opex = re_taxes + insurance + repairs + management + utilities + admin + reserves
    noi = egi - total_opex
    opex_ratio = (total_opex / egi * 100) if egi > 0 else 0

    if gpr > 0:
        st.markdown("---")
        st.markdown("**Live NOI Summary**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Effective Gross Income", f"${egi:,.0f}")
        with c2:
            st.metric("Total Operating Expenses", f"(${total_opex:,.0f})",
                       delta=f"OpEx Ratio: {opex_ratio:.1f}%", delta_color="off")
        with c3:
            st.metric("Net Operating Income", f"${noi:,.0f}")


# ── Step 5B — Commercial (Office / Retail / Industrial) ────────────
_TENANT_TEMPLATE_CSV = (
    "tenant_name,sq_ft,annual_rent_psf,lease_start,lease_end,lease_type\n"
)


def _step_5b_commercial(fin: dict, ptype: str):
    """Render commercial financial forms: tenant schedule + T-12 + live NOI."""

    st.markdown(f"#### Tenant Schedule ({ptype.title()})")

    # Radio toggle: upload vs manual
    entry_mode = st.radio(
        "Tenant data entry",
        ["Upload tenant CSV", "Enter manually"],
        horizontal=True,
        key="comm_entry_mode",
    )

    if entry_mode == "Upload tenant CSV":
        # If rent roll was already uploaded in Step 4, reuse it
        if st.session_state.uploaded_rent_roll:
            st.info(
                f"Tenant data file already uploaded: "
                f"{Path(st.session_state.uploaded_rent_roll).name}"
            )
        else:
            st.download_button(
                "Download template",
                data=_TENANT_TEMPLATE_CSV,
                file_name="tenant_schedule_template.csv",
                mime="text/csv",
                key="comm_tenant_template",
            )
            tenant_file = st.file_uploader(
                "Tenant Schedule CSV",
                type=["csv"],
                key="comm_tenant_csv",
                label_visibility="collapsed",
            )
            if tenant_file is not None:
                try:
                    tdf = pd.read_csv(tenant_file)
                    required = {
                        "tenant_name", "sq_ft", "annual_rent_psf",
                        "lease_start", "lease_end", "lease_type",
                    }
                    actual = {c.strip().lower() for c in tdf.columns}
                    missing = required - actual
                    if missing:
                        st.error(
                            f"Missing columns: {', '.join(sorted(missing))}. "
                            f"Required: {', '.join(sorted(required))}"
                        )
                    else:
                        fin["tenant_schedule"] = tdf.to_dict(orient="records")
                        st.success(f"{len(tdf)} tenants loaded.")
                except Exception as e:
                    st.error(f"Could not parse CSV: {e}")
    else:
        # Manual entry via data_editor
        if "comm_tenant_df" not in st.session_state:
            if fin.get("tenant_schedule"):
                rows = fin["tenant_schedule"]
            else:
                rows = [{
                    "Tenant Name": "", "SF": 0,
                    "Annual Rent PSF ($)": 0.0,
                    "Lease Start": "", "Lease End": "",
                    "Lease Type": "NNN",
                }]
            st.session_state.comm_tenant_df = pd.DataFrame(rows)

        edited_tenants = st.data_editor(
            st.session_state.comm_tenant_df,
            num_rows="dynamic",
            use_container_width=True,
            key="comm_tenant_editor",
            column_config={
                "Tenant Name": st.column_config.TextColumn("Tenant Name", width="medium"),
                "SF": st.column_config.NumberColumn("SF", min_value=0, step=100),
                "Annual Rent PSF ($)": st.column_config.NumberColumn(
                    "Annual Rent PSF ($)", min_value=0.0, step=0.5, format="$%.2f",
                ),
                "Lease Start": st.column_config.TextColumn("Lease Start"),
                "Lease End": st.column_config.TextColumn("Lease End"),
                "Lease Type": st.column_config.SelectboxColumn(
                    "Lease Type", options=["NNN", "Gross", "Modified Gross"],
                ),
            },
        )
        st.session_state.comm_tenant_df = edited_tenants
        fin["tenant_schedule"] = edited_tenants.to_dict(orient="records")

    # ── T-12 Income & Expenses ──────────────────────────────────────
    st.markdown("---")
    st.markdown("#### T-12 Income & Expenses")

    t12 = fin.get("t12", {})

    st.markdown("**Income**")
    t12["total_gross_revenue"] = st.number_input(
        "Total Gross Revenue ($/yr)",
        min_value=0,
        value=t12.get("total_gross_revenue", None),
        step=10000,
        format="%d",
        key="comm_t12_revenue",
        placeholder="e.g. 3200000",
    )
    t12["vacancy_pct"] = st.number_input(
        "Vacancy Rate (%)",
        min_value=0.0, max_value=100.0,
        value=t12.get("vacancy_pct", None),
        step=0.1,
        format="%.1f",
        key="comm_t12_vacancy",
        placeholder="e.g. 5.0",
    )
    # Total SF (if not already in Step 2)
    pd_sf = st.session_state.property_details.get("total_rentable_sf")
    if not pd_sf:
        t12["total_sf"] = st.number_input(
            "Total SF *",
            min_value=1,
            value=t12.get("total_sf", None),
            step=1000,
            format="%d",
            key="comm_t12_total_sf",
            placeholder="e.g. 85000",
        )

    st.markdown("**Expenses (annual $)**")
    t12["real_estate_taxes"] = st.number_input(
        "Real Estate Taxes",
        min_value=0,
        value=t12.get("real_estate_taxes", None),
        step=10000, format="%d",
        key="comm_t12_re_taxes",
        placeholder="e.g. 280000",
    )
    t12["insurance"] = st.number_input(
        "Insurance",
        min_value=0,
        value=t12.get("insurance", None),
        step=5000, format="%d",
        key="comm_t12_insurance",
    )
    t12["repairs"] = st.number_input(
        "Repairs & Maintenance",
        min_value=0,
        value=t12.get("repairs", None),
        step=5000, format="%d",
        key="comm_t12_repairs",
    )
    t12["mgmt_pct"] = st.number_input(
        "Property Management (% of EGI)",
        min_value=0.0, max_value=100.0,
        value=t12.get("mgmt_pct", None),
        step=0.5, format="%.1f",
        key="comm_t12_mgmt",
    )
    t12["utilities"] = st.number_input(
        "Utilities (Landlord-Paid)",
        min_value=0,
        value=t12.get("utilities", None),
        step=5000, format="%d",
        key="comm_t12_utilities",
    )
    t12["admin"] = st.number_input(
        "Administrative",
        min_value=0,
        value=t12.get("admin", None),
        step=5000, format="%d",
        key="comm_t12_admin",
    )
    t12["reserves"] = st.number_input(
        "Replacement Reserves",
        min_value=0,
        value=t12.get("reserves", None),
        step=1000, format="%d",
        key="comm_t12_reserves",
    )

    fin["t12"] = t12

    # ── Live NOI Summary ────────────────────────────────────────────
    gross_rev = t12.get("total_gross_revenue") or 0
    vac_pct = (t12.get("vacancy_pct") or 0) / 100.0
    egi = gross_rev * (1 - vac_pct)

    mgmt_pct_val = (t12.get("mgmt_pct") or 0) / 100.0
    management = egi * mgmt_pct_val

    re_taxes = t12.get("real_estate_taxes") or 0
    insurance = t12.get("insurance") or 0
    repairs = t12.get("repairs") or 0
    utilities = t12.get("utilities") or 0
    admin = t12.get("admin") or 0
    reserves = t12.get("reserves") or 0

    total_opex = re_taxes + insurance + repairs + management + utilities + admin + reserves
    noi = egi - total_opex
    opex_ratio = (total_opex / egi * 100) if egi > 0 else 0

    if gross_rev > 0:
        st.markdown("---")
        st.markdown("**Live NOI Summary**")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Effective Gross Income", f"${egi:,.0f}")
        with c2:
            st.metric("Total Operating Expenses", f"(${total_opex:,.0f})",
                       delta=f"OpEx Ratio: {opex_ratio:.1f}%", delta_color="off")
        with c3:
            st.metric("Net Operating Income", f"${noi:,.0f}")


# ── Step 5C — Pro Forma & Financing Assumptions ────────────────────
def _step_5c_proforma(fin: dict, is_land: bool):
    """Render pro forma, financing, existing debt, and CapEx expanders."""

    with st.expander(
        "Pro Forma & Financing Assumptions "
        "(optional — market defaults applied if left blank)",
        expanded=False,
    ):
        pf = fin.get("pro_forma", {})

        st.markdown("**Pro Forma**")
        pf["rent_growth"] = st.number_input(
            "Rent Growth Assumption (%/yr)",
            min_value=0.0, max_value=20.0,
            value=pf.get("rent_growth", 3.5),
            step=0.1, format="%.1f",
            key="pf_rent_growth",
        )
        pf["expense_growth"] = st.number_input(
            "Expense Growth Assumption (%/yr)",
            min_value=0.0, max_value=20.0,
            value=pf.get("expense_growth", 2.5),
            step=0.1, format="%.1f",
            key="pf_expense_growth",
        )
        pf["hold_period"] = st.number_input(
            "Hold Period (years)",
            min_value=1, max_value=20,
            value=pf.get("hold_period", 5),
            step=1, format="%d",
            key="pf_hold_period",
        )
        pf["exit_cap_spread_bps"] = st.number_input(
            "Exit Cap Rate Spread (bps over going-in)",
            min_value=0, max_value=500,
            value=pf.get("exit_cap_spread_bps", 25),
            step=5, format="%d",
            key="pf_exit_cap_spread",
        )

        st.markdown("**Financing**")
        financing = fin.get("financing", {})
        financing["ltv"] = st.number_input(
            "LTV (%)",
            min_value=0.0, max_value=100.0,
            value=financing.get("ltv", 65.0),
            step=1.0, format="%.1f",
            key="pf_ltv",
        )
        financing["interest_rate"] = st.number_input(
            "Interest Rate (%/yr)",
            min_value=0.0, max_value=20.0,
            value=financing.get("interest_rate", 6.25),
            step=0.05, format="%.2f",
            key="pf_interest_rate",
        )
        financing["amortization"] = st.number_input(
            "Amortization (years)",
            min_value=1, max_value=40,
            value=financing.get("amortization", 30),
            step=1, format="%d",
            key="pf_amortization",
        )

        fin["pro_forma"] = pf
        fin["financing"] = financing

    # ── Existing Debt ───────────────────────────────────────────────
    with st.expander("Existing Debt (optional)", expanded=False):
        debt = fin.get("existing_debt", {})
        debt["outstanding_balance"] = st.number_input(
            "Outstanding Balance ($)",
            min_value=0,
            value=debt.get("outstanding_balance", None),
            step=100000, format="%d",
            key="pf_debt_balance",
        )
        debt["interest_rate"] = st.number_input(
            "Interest Rate (%)",
            min_value=0.0, max_value=20.0,
            value=debt.get("interest_rate", None),
            step=0.05, format="%.2f",
            key="pf_debt_rate",
        )
        debt["maturity_date"] = st.date_input(
            "Maturity Date",
            value=debt.get("maturity_date", None),
            key="pf_debt_maturity",
        )
        debt["lender_name"] = st.text_input(
            "Lender Name",
            value=debt.get("lender_name", ""),
            key="pf_debt_lender",
        )
        fin["existing_debt"] = debt

    # ── Capital Expenditures ────────────────────────────────────────
    with st.expander("Capital Expenditures (optional)", expanded=False):
        capex = fin.get("capex", {})
        capex["recent_description"] = st.text_area(
            "Recent CapEx Description",
            value=capex.get("recent_description", ""),
            key="pf_capex_recent_desc",
        )
        capex["recent_amount"] = st.number_input(
            "Recent CapEx Amount ($)",
            min_value=0,
            value=capex.get("recent_amount", None),
            step=10000, format="%d",
            key="pf_capex_recent_amt",
        )
        capex["planned_description"] = st.text_area(
            "Planned CapEx Description",
            value=capex.get("planned_description", ""),
            key="pf_capex_planned_desc",
        )
        capex["planned_amount"] = st.number_input(
            "Planned CapEx Amount ($)",
            min_value=0,
            value=capex.get("planned_amount", None),
            step=10000, format="%d",
            key="pf_capex_planned_amt",
        )
        fin["capex"] = capex


# ── Missing-field warnings ─────────────────────────────────────────
def _step_5_missing_field_warnings(
    fin: dict, is_mf: bool, is_commercial: bool, is_land: bool,
):
    """Show non-blocking warnings for strongly-encouraged blank fields."""
    if is_land:
        return

    t12 = fin.get("t12", {})
    missing = []

    if is_mf:
        if not t12.get("gpr"):
            missing.append("Gross Potential Rent")
        if t12.get("vacancy_pct") is None:
            missing.append("Vacancy Rate")
    elif is_commercial:
        if not t12.get("total_gross_revenue"):
            missing.append("Total Gross Revenue")
        if t12.get("vacancy_pct") is None:
            missing.append("Vacancy Rate")

    if not t12.get("real_estate_taxes"):
        missing.append("Real Estate Taxes")
    if not t12.get("insurance"):
        missing.append("Insurance")
    if not t12.get("repairs"):
        missing.append("Repairs & Maintenance")
    if t12.get("mgmt_pct") is None:
        missing.append("Property Management (%)")

    if missing:
        bullets = "\n".join(f"- {f}" for f in missing)
        st.warning(
            f"The following fields are missing and will result in "
            f"placeholder data in the OM:\n\n{bullets}\n\n"
            f"You can continue, but the Financial Analysis section will be "
            f"incomplete. Consider filling these in for a stronger document."
        )


# ── Sidecar JSON assembly ──────────────────────────────────────────
# Wizard form keys (left) renamed to canonical sidecar keys (right) before
# being written into the v1.0 ``property`` block.
_WIZARD_TO_IDENTITY_KEYS = {
    "property_name": "property_name",
    "year_built": "year_built",
    "stories": "stories",
    "floor_plan_count": "floor_plan_count",
    "management_company": "management_company",
    "submarket_label": "submarket_name",
    "utility_structure": "utility_structure_short",
}


def _broker_identity(value):
    """Wrap a wizard-supplied value as a broker-confirmed identity entry."""
    return {"value": value, "source": "broker", "confirmed_by_broker": True}


def _derive_management_company_short(full_name: str) -> str:
    """Shorten a management company name for the cover-page badge.

    Strips trailing common qualifiers; falls back to the first whitespace token.
    """
    if not full_name:
        return ""
    cleaned = full_name.strip()
    for suffix in (" Residential", " Management Company", " Management"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()
            break
    return cleaned.split()[0] if " " in cleaned else cleaned


def _build_property_sidecar_dict(
    *,
    ptype: str,
    pd_details: dict,
    fin: dict,
    address: str,
    county: str,
    geocode: dict,
    slug: str,
    branding: dict | None = None,
) -> dict:
    """Pure builder — produces the v1.0 sidecar dict; no I/O, no globals."""
    import datetime as _dt
    sidecar = {
        "schema_version": "1.0",
        "slug": slug,
        "address": address,
        "county": county,
        "property": {},
        "property_type": ptype,
    }

    # ── Branding block — broker contact / offer metadata ───────────
    if branding:
        sidecar_branding: dict = {}
        for key in (
            "broker_firm", "broker_name", "broker_title",
            "broker_phone", "broker_email", "offer_due_date",
        ):
            v = branding.get(key)
            if v in (None, ""):
                continue
            if isinstance(v, _dt.date):
                v = v.isoformat()
            sidecar_branding[key] = v
        if sidecar_branding:
            sidecar["branding"] = sidecar_branding

    # ── Identity block — broker-supplied wizard fields ───────────────
    identity = sidecar["property"]
    for wizard_key, sidecar_key in _WIZARD_TO_IDENTITY_KEYS.items():
        v = pd_details.get(wizard_key)
        # Skip empty strings, None, and 0/None numeric placeholders for fields
        # that streamlit number_input returns as None when blank.
        if v in (None, ""):
            continue
        identity[sidecar_key] = _broker_identity(v)

    # ── Derived: management_company_short ───────────────────────────
    full_mgmt = pd_details.get("management_company")
    if full_mgmt:
        short = _derive_management_company_short(full_mgmt)
        if short:
            identity["management_company_short"] = {
                "value": short,
                "source": "derived",
                "confirmed_by_broker": False,
            }

    # ── Default: hero_image_label ───────────────────────────────────
    identity["hero_image_label"] = {
        "value": "Property Exterior",
        "source": "default",
        "confirmed_by_broker": False,
    }

    # ── Auto-derivation: only fills fields the wizard did NOT provide ─
    try:
        from property_identity_helpers import (
            derive_submarket_name,
            derive_management_company,
        )

        if "submarket_name" not in identity:
            auto = derive_submarket_name(
                county, address, geocode.get("lat"), geocode.get("lon")
            )
            if auto is not None:
                identity["submarket_name"] = {
                    "value": auto.value,
                    "source": auto.source,
                    "confirmed_by_broker": auto.confirmed_by_broker,
                }

        if "management_company" not in identity:
            subdivision = (
                pd_details.get("subdivision")
                or fin.get("subdivision")
                or ""
            )
            auto = derive_management_company(county, subdivision)
            if auto is not None:
                identity["management_company"] = {
                    "value": auto.value,
                    "source": auto.source,
                    "confirmed_by_broker": auto.confirmed_by_broker,
                }
                if "management_company_short" not in identity:
                    short = _derive_management_company_short(auto.value)
                    if short:
                        identity["management_company_short"] = {
                            "value": short,
                            "source": "derived",
                            "confirmed_by_broker": False,
                        }
    except ImportError:
        # Helpers not yet available; identity stays as-is.
        pass

    # ── Flat financial fields (unchanged shape) ──────────────────────

    # Asking price (from Step 2)
    if not pd_details.get("price_upon_request"):
        sidecar["asking_price"] = pd_details.get("asking_price", 0)

    # Pro forma / financing defaults
    pf = fin.get("pro_forma", {})
    sidecar["rent_growth_assumption"] = (pf.get("rent_growth", 3.5)) / 100.0
    sidecar["hold_period"] = pf.get("hold_period", 5)
    sidecar["exit_cap_spread"] = (pf.get("exit_cap_spread_bps", 25)) / 10000.0

    fdata = fin.get("financing", {})
    sidecar["financing"] = {
        "ltv": (fdata.get("ltv", 65.0)) / 100.0,
        "interest_rate": (fdata.get("interest_rate", 6.25)) / 100.0,
        "amortization": fdata.get("amortization", 30),
    }

    t12 = fin.get("t12", {})

    if ptype == "multifamily":
        sidecar["total_units"] = pd_details.get("total_units", 0)

        # Unit mix from data editor rows
        unit_mix = []
        for row in fin.get("unit_mix_rows", []):
            count = row.get("Count", 0)
            if not count:
                continue
            unit_mix.append({
                "type": row.get("Unit Type", ""),
                "count": int(count),
                "avg_sf": int(row.get("Avg SF", 0)),
                "in_place_rent": float(row.get("In-Place Rent ($/mo)", 0)),
            })
        sidecar["unit_mix"] = unit_mix

        # T-12
        sidecar_t12 = {}
        if t12.get("gpr"):
            sidecar_t12["gpr"] = t12["gpr"]
        if t12.get("vacancy_pct") is not None:
            sidecar_t12["vacancy_pct"] = t12["vacancy_pct"] / 100.0
        if t12.get("credit_loss_pct") is not None:
            sidecar_t12["credit_loss_pct"] = t12["credit_loss_pct"] / 100.0
        if t12.get("real_estate_taxes"):
            sidecar_t12["real_estate_taxes"] = t12["real_estate_taxes"]
        if t12.get("insurance"):
            sidecar_t12["insurance"] = t12["insurance"]
        if t12.get("repairs"):
            sidecar_t12["repairs"] = t12["repairs"]
        if t12.get("mgmt_pct") is not None:
            sidecar_t12["mgmt_pct"] = t12["mgmt_pct"] / 100.0
        if t12.get("utilities"):
            sidecar_t12["utilities"] = t12["utilities"]
        if t12.get("admin"):
            sidecar_t12["admin"] = t12["admin"]
        if sidecar_t12:
            sidecar["t12"] = sidecar_t12

    elif ptype in ("office", "retail", "industrial"):
        total_sf = (
            pd_details.get("total_rentable_sf")
            or t12.get("total_sf")
            or 0
        )
        sidecar["total_sf"] = total_sf

        # Tenant schedule → commercial rent_roll
        rent_roll = []
        for row in fin.get("tenant_schedule", []):
            sf = row.get("SF") or row.get("sq_ft") or 0
            psf = row.get("Annual Rent PSF ($)") or row.get("annual_rent_psf") or 0
            if not sf:
                continue
            rent_roll.append({
                "tenant": row.get("Tenant Name") or row.get("tenant_name", ""),
                "sf": float(sf),
                "annual_rent_psf": float(psf),
                "lease_expiry": row.get("Lease End") or row.get("lease_end", ""),
                "lease_type": row.get("Lease Type") or row.get("lease_type", "Gross"),
            })
        sidecar["rent_roll"] = rent_roll

        # Compute operating_expenses from T-12 fields
        opex = 0
        for k in ("real_estate_taxes", "insurance", "repairs", "utilities", "admin", "reserves"):
            opex += t12.get(k) or 0
        # Add management
        gross_rev = t12.get("total_gross_revenue") or 0
        vac_pct = (t12.get("vacancy_pct") or 0) / 100.0
        egi_val = gross_rev * (1 - vac_pct)
        mgmt = egi_val * ((t12.get("mgmt_pct") or 0) / 100.0)
        opex += mgmt
        sidecar["operating_expenses"] = opex

    # CapEx / existing debt as pass-through metadata
    if fin.get("capex"):
        capex = fin["capex"]
        sidecar_capex = {}
        for k in ("recent_description", "recent_amount", "planned_description", "planned_amount"):
            v = capex.get(k)
            if v:
                sidecar_capex[k] = v
        if sidecar_capex:
            sidecar["capex"] = sidecar_capex

    if fin.get("existing_debt"):
        debt = fin["existing_debt"]
        sidecar_debt = {}
        for k in ("outstanding_balance", "interest_rate", "lender_name"):
            v = debt.get(k)
            if v:
                sidecar_debt[k] = v
        mat = debt.get("maturity_date")
        if mat is not None:
            if isinstance(mat, _dt.date):
                sidecar_debt["maturity_date"] = mat.isoformat()
            elif mat:
                sidecar_debt["maturity_date"] = str(mat)
        if sidecar_debt:
            sidecar["existing_debt"] = sidecar_debt

    return sidecar


def _assemble_property_json(fin: dict):
    """Build the v1.0 sidecar JSON and write to the live runtime
    directory ``om_generator/data/property_inputs/`` (gitignored).
    Static test fixtures live separately under
    ``om_generator/data/test_fixtures/wizard/``.
    """
    address = st.session_state.address
    slug = make_slug(address)
    sidecar = _build_property_sidecar_dict(
        ptype=st.session_state.property_type,
        pd_details=st.session_state.property_details,
        fin=fin,
        address=address,
        county=(st.session_state.get("county") or "").lower(),
        geocode=st.session_state.get("geocode_result") or {},
        slug=slug,
        branding=st.session_state.get("branding") or {},
    )
    sidecar_path = str(
        _OM_DIR / "data" / "property_inputs" / f"property_{slug}.json"
    )
    write_json(sidecar_path, sidecar)
    fin["_sidecar_path"] = sidecar_path


# ══════════════════════════════════════════════════════════════════════
# STEP 6 — Review & Generate
# ══════════════════════════════════════════════════════════════════════

_SECTION_DEFAULTS = {
    #                                MF    Office Retail Indust Land
    "Executive Summary":            (True,  True,  True,  True,  True),
    "Investment Highlights":        (True,  True,  True,  True,  True),
    "Property Description":         (True,  True,  True,  True,  True),
    "Location & Demographics":      (True,  True,  True,  True,  True),
    "Financial Analysis":           (True,  True,  True,  True,  False),
    "Rent Roll / Lease Summary":    (True,  True,  True,  True,  False),
    "Sales Comparables":            (True,  True,  True,  True,  True),
    "Development Activity":         (True,  True,  True,  True,  True),
    "Zoning & Entitlements":        (False, False, False, False, True),
}
_PTYPE_INDEX = {
    "multifamily": 0, "office": 1, "retail": 2, "industrial": 3, "land": 4,
}


def _step_6():
    _show_progress()

    slug = make_slug(st.session_state.address)
    ptype = st.session_state.property_type
    pd_details = st.session_state.property_details
    br = st.session_state.branding

    # ── PART 1 — Input Summary Card ─────────────────────────────────
    st.subheader("Review Your Inputs")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(f"**Address:** {st.session_state.address}")
        st.markdown(f"**County:** {(st.session_state.county or '').title()}")
        st.markdown(f"**Property Type:** {(ptype or '').title()}")
        asking = pd_details.get("asking_price")
        if pd_details.get("price_upon_request"):
            st.markdown("**Asking Price:** Price Upon Request")
        elif asking:
            st.markdown(f"**Asking Price:** ${asking:,.0f}")
        else:
            st.markdown("**Asking Price:** —")
    with col_r:
        broker_name = br.get("broker_name", "—")
        broker_firm = br.get("broker_firm", "—")
        st.markdown(f"**Broker:** {broker_name}, {broker_firm}")
        photo_count = len(st.session_state.get("uploaded_photos", []))
        st.markdown(f"**Photos uploaded:** {photo_count}")
        comps_path = st.session_state.get("uploaded_comps")
        if comps_path and file_exists(comps_path):
            try:
                comps_count = len(pd.read_csv(comps_path))
                st.markdown(f"**Comps loaded:** {comps_count} rows")
            except Exception:
                st.markdown("**Comps loaded:** Yes")
        else:
            st.markdown("**Comps loaded:** None")
        rr_status = "Uploaded" if st.session_state.get("uploaded_rent_roll") else "Not uploaded"
        st.markdown(f"**Rent roll:** {rr_status}")
        t12_status = "Uploaded" if st.session_state.get("uploaded_t12") else "Not uploaded"
        st.markdown(f"**T-12:** {t12_status}")

    st.caption(
        "Need to change something? Use the Back button or jump to any "
        "step using the sidebar."
    )

    # ── PART 2 — Section Toggle Checklist ───────────────────────────
    st.divider()
    st.subheader("Select OM Sections")
    st.info(
        "Sections are pre-selected based on your property type. "
        "Uncheck any section to exclude it from the OM."
    )

    ptype_idx = _PTYPE_INDEX.get(ptype, 0)

    # Initialize defaults only on first entry
    if "selected_sections" not in st.session_state:
        st.session_state.selected_sections = {
            name: defaults[ptype_idx]
            for name, defaults in _SECTION_DEFAULTS.items()
        }

    selected = st.session_state.selected_sections
    for section_name in _SECTION_DEFAULTS:
        selected[section_name] = st.checkbox(
            section_name,
            value=selected.get(section_name, True),
            key=f"sec_toggle_{section_name}",
        )
    st.session_state.selected_sections = selected

    # ── PART 3 — Generate Button & Progress ─────────────────────────
    st.divider()
    st.subheader("Generate Offering Memorandum")

    output_path = str(_OM_DIR / "output" / f"{slug}_om.html")
    sidecar_path = str(
        _OM_DIR / "data" / "property_inputs" / f"property_{slug}.json"
    )
    fin_path = sidecar_path if file_exists(sidecar_path) else None

    # If already generated, jump to Part 4
    if st.session_state.get("om_output_path") and file_exists(
        st.session_state["om_output_path"]
    ):
        _step_6_success()
    else:
        if st.button("Generate OM", type="primary"):
            st.session_state.generating = True

            progress_steps = [
                "Gathering property data...",
                "Building financial analysis...",
                "Assembling comparable sales...",
                "Compiling demographics & market context...",
                "Rendering document...",
            ]

            try:
                with st.status("Generating your OM...", expanded=True) as status:
                    for step_msg in progress_steps:
                        time.sleep(0.4)
                        st.write(f"✓ {step_msg}")

                    result = run_om_generation(
                        address=st.session_state.address,
                        output_path=output_path,
                        financial_inputs_path=fin_path,
                    )

                    status.update(label="Generation complete!", state="complete")

                st.session_state.om_output_path = output_path
                st.session_state.generating = False
                st.rerun()

            except Exception as e:
                st.session_state.generating = False
                st.error("OM generation failed. See details below.")
                st.exception(e)

    # ── Navigation ──────────────────────────────────────────────────
    st.markdown("---")
    if st.button("Back"):
        st.session_state.wizard_step = 5
        st.rerun()


def _step_6_success():
    """Render the post-generation success state with download button."""
    slug = make_slug(st.session_state.address)
    output_path = st.session_state["om_output_path"]

    st.success("Your Offering Memorandum is ready.")

    html_bytes = read_file(output_path)
    st.download_button(
        label="Download OM (.html)",
        data=html_bytes,
        file_name=f"{slug}_om.html",
        mime="text/html",
        key="download_om",
    )

    st.caption(
        "Open in any browser for full formatting. "
        "Print to PDF from your browser for distribution."
    )

    if st.button("Generate New OM"):
        st.session_state.om_output_path = None
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
