# Provenance — Front-End Spec
**Date:** April 2026  
**Repo:** OfferingMemorandum  
**For:** Claude Code Implementation  
**Status:** Approved for build

---

## Standing Guardrails

- Athens protection absolute — zero modifications to Athens files ever
- `fairfax_report.py` is legacy — never touch
- No pull requests — push branch, report name for Matt to merge
- No parallel agents — sequential execution only
- All secrets via `get_secret()` — never `os.getenv()` directly
- All business logic in modules — never in `provenance_app.py`
- Investigation before implementation if anything is ambiguous

---

## Overview

Build `provenance_app.py` — a standalone Streamlit wizard application in the OfferingMemorandum repo that collects broker inputs, assembles the full context dict, and invokes the OM generation pipeline. The output is a fully-rendered HTML Offering Memorandum that opens in a new browser tab with a download button.

This is a net-new file. Do not modify any existing app (`streamlit_app.py`, `unified_app.py`, `loudoun_streamlit_app.py`). Do not touch any Athens files.

---

## Prerequisites — Complete Before Building the Wizard

Two prerequisite tasks must be completed before the wizard itself is built. Complete them in order, verify each, then proceed.

### Prerequisite 1 — Refactor `generate_om.py` to expose a callable function

**Current state:** `generate_om.py` has a `main()` function that reads from `argparse`. It cannot be called programmatically.

**Required change:** Extract the core generation logic into a callable function. The CLI wrapper calls this function unchanged.

```python
def run_om_generation(address: str, output_path: str, financial_inputs_path: str = None) -> dict:
    """
    Core OM generation logic. Called by both the CLI and the Streamlit wizard.
    Returns a result dict: {"success": bool, "output_path": str, "error": str | None}
    """
    # Move all current main() logic here.
    # Use financial_inputs_path to locate the broker sidecar if provided.
    # Return result dict — do not sys.exit() from this function.
    ...

def main():
    """Thin CLI wrapper. Parses argparse, calls run_om_generation()."""
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    result = run_om_generation(args.address, args.output, args.financial_inputs)
    if not result["success"]:
        print(f"Error: {result['error']}")
        sys.exit(1)
    print(f"OM generated: {result['output_path']}")

if __name__ == "__main__":
    main()
```

**Verify:** CLI still works identically after refactor — `python generate_om.py "9333 Clocktower Place, Fairfax VA 22031"` should produce the same output as before. Run this test before proceeding.

---

### Prerequisite 2 — Create `storage.py`

Create `om_generator/storage.py`. This is a thin local-only abstraction. The interface is designed for future S3 swap via config — boto3 is NOT added in this build.

```python
"""
storage.py — File I/O abstraction layer for Provenance.

Currently implements local disk only. All reads and writes go through
this module so that swapping to S3 later is a config change, not a rewrite.

Future: set STORAGE_BACKEND=s3 in environment to route through boto3.
"""

import os
import json
from pathlib import Path

STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")


def read_file(path: str) -> bytes:
    """Read a file. Returns raw bytes."""
    return Path(path).read_bytes()


def read_text(path: str, encoding: str = "utf-8") -> str:
    """Read a text file. Returns string."""
    return Path(path).read_text(encoding=encoding)


def read_json(path: str) -> dict:
    """Read and parse a JSON file."""
    return json.loads(read_text(path))


def write_file(path: str, data: bytes) -> None:
    """Write bytes to a file. Creates parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


def write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    """Write a string to a file. Creates parent directories if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding=encoding)


def write_json(path: str, data: dict, indent: int = 2) -> None:
    """Serialize and write a dict as JSON."""
    write_text(path, json.dumps(data, indent=indent))


def file_exists(path: str) -> bool:
    """Check if a file exists."""
    return Path(path).exists()


def ensure_dir(path: str) -> None:
    """Ensure a directory exists, creating it if needed."""
    Path(path).mkdir(parents=True, exist_ok=True)
```

**Verify:** Import cleanly — `from om_generator.storage import write_json, read_json, file_exists` — no errors.

---

## Application Entry Point

**File:** `provenance_app.py` (repo root, alongside `generate_om.py`)

**Run command:** `python -m streamlit run provenance_app.py`

**Imports pattern:** Use `sys.path.insert` + `from om_generator.xxx import` — never package-prefix imports. Match existing repo pattern exactly.

---

## Branding — `[PLACEHOLDER]`

The platform name is not yet confirmed. Use West Oxford Advisors branding throughout the Streamlit app UI as a placeholder. Mark every branding element with a `# PLACEHOLDER — replace when platform name confirmed` comment so they are easy to find and swap.

- **App title (browser tab):** `West Oxford Advisors — OM Generator` `# PLACEHOLDER`
- **Header:** West Oxford Advisors wordmark or text, navy background (`#1B2A4A`), gold accent (`#C9A84C`)
- **Accent color throughout:** `#C9A84C` (gold)
- **Primary text:** `#1B2A4A` (navy)
- **Logo:** Use `provenance_logo.svg` if accessible from the app root; fall back to text header if not. `# PLACEHOLDER`
- **Tagline shown in header:** `built on the record` (lowercase, italic, gold) `# PLACEHOLDER`

Apply branding via Streamlit's `st.markdown` custom CSS injection at app startup. Keep all CSS in a single `_apply_styles()` helper function at the top of the file.

---

## Wizard Structure — 6 Steps

The app is a 6-step wizard. Step progression is controlled by `st.session_state.wizard_step` (integer 1–6). Navigation: "Continue" button advances, "Back" button retreats. The user cannot jump steps.

Display a progress bar and step label at the top of every step:
```
Step 2 of 6 — Property Details
[████████░░░░░░░░░░░░░░░░] 33%
```

### Session State Keys

Initialize all keys at app startup if not already present:

```python
DEFAULTS = {
    "wizard_step": 1,
    "address": "",
    "county": None,           # "fairfax" | "loudoun"
    "property_type": None,    # "multifamily" | "office" | "retail" | "industrial" | "land"
    "geocode_result": None,   # full geocode dict
    "property_details": {},
    "branding": {},
    "uploaded_photos": [],    # list of saved file paths
    "uploaded_comps": None,   # saved file path or None
    "uploaded_rent_roll": None,
    "uploaded_t12": None,
    "financials": {},
    "rent_roll_parsed": None, # confirmed parse result from Claude API
    "section_overrides": {},  # broker-adjusted section toggles
    "generation_result": None,
    "auto_save_path": None,
}

for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default
```

### Auto-Save

After every field change that updates session state, write a draft JSON to disk:

```
om_generator/data/drafts/{slug}.json
```

Where `slug` is the hyphenated address slug: `re.sub(r"[^a-z0-9]+", "-", address.lower()).strip("-")`

Draft JSON contains the full session state dict (excluding binary file data). On app load, if a draft exists for the entered address, offer to restore it:

> *"A saved draft was found for this address. Restore it?"* — [Restore] [Start Fresh]

Use `storage.write_json()` and `storage.read_json()` — never direct file I/O in `provenance_app.py`.

---

## Step 1 — Address, County & Property Type

### Purpose
Establish the property address, auto-detect the county, and collect the property type. Both county detection and property type selection must succeed before the wizard advances.

### Layout

**Address input**
- `st.text_input("Property Address", placeholder="e.g. 9333 Clocktower Place, Fairfax VA 22031")`
- "Look Up Address" button triggers geocoding (do not geocode on keystroke)
- While geocoding: `st.spinner("Looking up address...")`

**Geocoding logic**
- Use the existing geocoding cascade in `property_context.py` (Census geocoder → Google Maps fallback)
- On success: display a confirmation card (see below)
- On failure / unsupported county: display correctable hard error (see below)

**County confirmation card** (shown after successful geocode):
```
✓  9333 Clocktower Place, Fairfax, VA 22031
   Fairfax County — supported ✓
```
Display as a light green info box. Include a small "Not right? Edit address" link that clears the geocode result and returns focus to the address field without losing the typed address.

**Property type selector** (shown after successful county confirmation):
```
Select Property Type
○ Multifamily
○ Office
○ Retail  
○ Industrial
○ Land
```
Use `st.radio()`. Required — wizard does not advance until one is selected.

**Hard error states:**

*Address not found:*
> ⚠️ Address not found. Please check the address and try again.
> [address field remains editable, no other state lost]

*County not supported:*
> ⚠️ This address is outside the supported counties (Fairfax and Loudoun, VA).
> [address field remains editable, no other state lost]

**Continue button:** Enabled only when geocode succeeded AND property type selected.

**On advance:** Store `county`, `property_type`, `geocode_result`, `address` to session state. Trigger auto-save.

---

## Step 2 — Property Details

### Purpose
Collect broker-input property specifications. Clean blank form — no pre-population from assessor data. Broker fills in everything.

### Fields

All fields use `st.session_state.property_details` as backing store.

| Field | Widget | Required | Notes |
|---|---|---|---|
| Property Name | `st.text_input` | Required | Marketing name, e.g. "Regent's Park" |
| Year Built | `st.number_input` (int, 1800–2030) | Required | |
| Stories | `st.number_input` (int, 1–100) | Optional | |
| Total Units | `st.number_input` (int, 1–10000) | Required if MF | Hidden for Land |
| Total Rentable SF | `st.number_input` (int) | Required if Office/Retail/Industrial | Hidden for MF and Land |
| Floor Plan Count | `st.number_input` (int) | Optional, MF only | |
| Avg Unit SF | `st.number_input` (int) | Optional, MF only | |
| Min / Max Unit SF | Two `st.number_input` side by side | Optional, MF only | |
| Management Company | `st.text_input` | Optional | |
| Submarket Label | `st.text_input` | Optional | e.g. "Vienna/Merrifield" |
| Utility Structure | `st.text_input` | Optional | e.g. "Tenant: Elec+Gas \| LL: Water" |
| Zoning Code | `st.text_input` | Optional | e.g. "PDH · PRC" |
| Transit / Proximity Notes | `st.text_area` | Optional | e.g. "Vienna Metro 1.3 mi · George Mason 0.9 mi" |

**Asking Price (always shown):**
- Toggle: `st.radio("Pricing", ["Enter asking price", "Price Upon Request"])`
- If "Enter asking price": `st.number_input("Asking Price ($)", min_value=0)`
- Compute and display `price_per_unit` (MF) or `price_per_sf` (commercial) dynamically as broker types — show as non-editable derived field below the input
- If "Price Upon Request": store flag, display "Price Upon Request" on cover

**Cap Rate:**
- `st.radio("Cap Rate", ["Enter cap rate", "Leave blank (auto-generates disclosure language)"])`
- If "Enter cap rate": `st.number_input("Cap Rate (%)", min_value=0.0, max_value=30.0, step=0.01, format="%.2f")`
- If "Leave blank": show disclosure preview text in a muted info box:
  > *"Cap rate not provided. The offering document will include standard disclosure language: 'Capitalization rate has not been provided by the seller. Prospective purchasers are advised to conduct independent analysis.'"*

**Validation on Continue:**
- Property name: required, error if blank
- Year built: required, error if blank
- Total units: required if MF, error if blank
- Total rentable SF: required if Office/Retail/Industrial, error if blank
- All other fields: optional, no blocking

Show all validation errors inline (next to the field) — not as a summary block at the top.

**On advance:** Store all fields to `st.session_state.property_details`. Trigger auto-save.

---

## Step 3 — Branding & Contact

### Purpose
Collect broker identity information for the cover page, confidentiality page, and contact section of the OM.

### Fields

All fields stored in `st.session_state.branding`.

| Field | Widget | Required | Notes |
|---|---|---|---|
| Broker Firm Name | `st.text_input` | Required | Appears on cover ("Exclusively Offered By"), confidentiality page |
| Broker Name | `st.text_input` | Required | |
| Broker Title | `st.text_input` | Optional | |
| Phone | `st.text_input` | Required | |
| Email | `st.text_input` | Required | Basic format validation (must contain @) |
| Offer Due Date | `st.date_input` | Optional | |

**Broker Logo Upload:**
```
Upload Broker Logo
Accepted formats: PNG, JPG  |  Max size: 5 MB
[Browse files]
```
- `st.file_uploader("Broker Logo", type=["png", "jpg", "jpeg"], accept_multiple_files=False)`
- On upload: save to `om_generator/data/broker_assets/{slug}/logo.{ext}` via `storage.write_file()`
- Show preview: `st.image(uploaded_file, width=200)`
- Optional — generation proceeds without it

**Note shown below firm name field:**
> *West Oxford Advisors branding appears on the cover page and final attribution page automatically. No upload needed.*

**Validation on Continue:**
- Broker firm name, broker name, phone, email: required
- Email: must contain `@`
- All errors shown inline

**On advance:** Store to `st.session_state.branding`. Trigger auto-save.

---

## Step 4 — Files & Photos

### Purpose
Accept optional broker-provided files that supplement or override automated pipeline data.

### Layout

Four upload sections, each clearly separated. All are optional. Generation proceeds without any of them — show a clear note at the top:

> *All uploads are optional. The OM will generate using available public data where files are not provided. Uploading your own data always produces a stronger document.*

---

**Section A — Property Photos**
```
Property Photos
JPG, JPEG, or PNG  |  Up to 10 files  |  Max 10 MB each
[Browse files]
```
- `st.file_uploader(..., accept_multiple_files=True, type=["jpg","jpeg","png"])`
- On upload: save each to `om_generator/data/property_photos/{slug}/{n:02d}.jpg` via `storage.write_file()`
- Show thumbnail grid after upload (use `st.columns`)
- Note: *"Photos appear in the hero strip. First photo is the hero image."*

---

**Section B — Comparable Sales (Override)**
```
Comparable Sales CSV
Optional — overrides automated deed record comps
[Download template ↓]   [Browse files]
```
- Template download: provide a `st.download_button` for a pre-built CSV template with headers: `name, units, sale_price, price_per_unit, cap_rate, sale_date, source`
- `st.file_uploader(..., type=["csv"])`
- On upload: save to `om_generator/data/comps/{slug}.csv` via `storage.write_file()`
- On upload: parse with pandas, validate required columns present, show row count confirmation: *"3 comparable sales loaded."*
- On column mismatch: show error with required column names, do not save file

---

**Section C — Rent Roll**
```
Rent Roll
CSV or Excel export from your property management system
[Browse files]
```
- `st.file_uploader(..., type=["csv","xlsx","xls"])`
- On upload: save to `om_generator/data/rent_rolls/{slug}/rent_roll.{ext}` via `storage.write_file()`
- Store path to `st.session_state.uploaded_rent_roll`
- Show file name confirmation: *"rent_roll.csv uploaded (248 rows detected)."*
- Show warning note:
  > ⚠️ *Rent roll uploaded — you'll review the parsed data in Step 5 before generating.*

**Missing file note** (shown if no upload):
> *No rent roll uploaded. The Financial Analysis section will show market-rate estimates. Upload a rent roll for actual in-place rent data.*

---

**Section D — T-12 Operating Statement**
```
T-12 Operating Statement
CSV or Excel  |  Line-item format preferred
[Browse files]
```
- `st.file_uploader(..., type=["csv","xlsx","xls"])`
- On upload: save to `om_generator/data/t12/{slug}/t12.{ext}` via `storage.write_file()`
- Store path to `st.session_state.uploaded_t12`
- Show file name confirmation

**Missing file note** (shown if no upload):
> *No T-12 uploaded. You'll enter operating figures manually in Step 5.*

---

**Continue button:** Always enabled — all uploads optional.

**On advance:** Confirm all saved paths in session state. Trigger auto-save.

---

## Step 5 — Financials

### Purpose
Collect the financial inputs that drive the pro forma model. This step is property-type-aware — the form rendered depends on the property type selected in Step 1.

### Step 5A — Rent Roll Parse & Confirmation (conditional)

**Show this sub-section only if a rent roll file was uploaded in Step 4.**

On entering Step 5, if `st.session_state.uploaded_rent_roll` is set and `st.session_state.rent_roll_parsed` is None:

1. Show: *"Parsing rent roll with AI — this takes a few seconds..."*
2. Call the Claude API (using `anthropic` client, key via `get_secret("ANTHROPIC_API_KEY")`):

```python
RENT_ROLL_PARSE_PROMPT = """
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
```

3. Parse the returned JSON. On success: store to `st.session_state.rent_roll_parsed`. On failure: show a warning and allow the broker to skip:
   > *"Couldn't parse rent roll automatically. You can enter figures manually below."* — [Enter Manually]

4. Show confirmation card:
```
Rent Roll Parsed ✓
──────────────────────────────
Total units:      248
Occupied:         236   (95.2%)
Vacant:           12
Avg monthly rent: $2,180

Parse notes: [any flags from AI]
──────────────────────────────
Does this look right?
[✓ Looks right — continue]   [✗ Enter manually instead]
```

If broker confirms: rent roll data flows into financial engine.
If broker rejects: `st.session_state.rent_roll_parsed = None`, proceed to manual entry forms.

---

### Step 5B — Financial Input Forms

Forms rendered depend on `st.session_state.property_type`. All values stored in `st.session_state.financials`.

#### Multifamily Forms

**Unit Mix Table**

Show an editable table built from `st.data_editor`. Pre-populated from rent roll parse if available; otherwise blank with one row. Broker can add/remove rows.

| Unit Type | Count | Avg SF | In-Place Rent ($/mo) |
|---|---|---|---|
| 1 BR / 1 BA | — | — | — |

Minimum 1 row. Validate: count and in-place rent must be > 0 if row is present.

**T-12 Income & Expenses** (manual entry; pre-populated from uploaded T-12 if available — otherwise blank):

*Income:*
| Field | Widget | Required |
|---|---|---|
| Gross Potential Rent ($/yr) | `st.number_input` | Strongly encouraged |
| Vacancy Rate (%) | `st.number_input` (0–100, step 0.1) | Strongly encouraged |
| Credit / Bad Debt Rate (%) | `st.number_input` (0–100, step 0.1) | Optional |

*Expenses (annual $):*
| Field | Widget | Required |
|---|---|---|
| Real Estate Taxes | `st.number_input` | Strongly encouraged |
| Insurance | `st.number_input` | Strongly encouraged |
| Repairs & Maintenance | `st.number_input` | Strongly encouraged |
| Property Management (%) | `st.number_input` (% of EGI) | Strongly encouraged |
| Utilities (Landlord-Paid) | `st.number_input` | Optional |
| Administrative | `st.number_input` | Optional |
| Replacement Reserves | `st.number_input` | Optional |

Show live-computed summary below the expense form (updates on every field change):
```
Effective Gross Income:    $15,607,000
Total Operating Expenses:  ($3,958,000)   OpEx Ratio: 25.4%
Net Operating Income:      $11,649,000
```
Use `st.metric()` or styled `st.markdown` for this display.

---

#### Office / Retail / Industrial Forms

**Rent Roll (Tenant Schedule)**

Two options — radio toggle at top of section:

`○ Upload tenant CSV   ○ Enter manually`

*Upload path:*
- If tenant CSV already uploaded in Step 4, show confirmation and skip upload widget
- If not: `st.file_uploader(..., type=["csv"])` with template download
- Template columns: `tenant_name, sq_ft, annual_rent_psf, lease_start, lease_end, lease_type` (NNN/Gross/Modified Gross)
- On upload: parse, validate columns, show row count

*Manual entry path:*
- `st.data_editor` table with columns: Tenant Name, SF, Annual Rent PSF ($), Lease Start, Lease End, Lease Type
- One blank row by default, broker adds rows

**T-12 Expenses** (same structure as MF but income side differs):

*Income:*
| Field | Widget | Required |
|---|---|---|
| Total Gross Revenue ($/yr) | `st.number_input` | Strongly encouraged |
| Vacancy Rate (%) | `st.number_input` | Strongly encouraged |
| Total SF | `st.number_input` | Required (if not already in Step 2) |

*Expenses (annual $):*
Same fields as MF expense table. All strongly encouraged.

Show same live NOI summary.

---

#### Land Form

Land has no financial form beyond asking price (already collected in Step 2). Show a note:

> *No financial inputs required for Land listings. Pro forma assumptions below are optional.*

---

### Step 5C — Pro Forma & Financing Assumptions

Shown for all property types except Land (where it is still shown but fully optional). Use `st.expander` to collapse by default — label: *"Pro Forma & Financing Assumptions (optional — market defaults applied if left blank)"*.

**Pro Forma:**
| Field | Widget | Default |
|---|---|---|
| Rent Growth Assumption (%/yr) | `st.number_input` | 3.5% |
| Expense Growth Assumption (%/yr) | `st.number_input` | 2.5% |
| Hold Period (years) | `st.number_input` int 1–20 | 5 |
| Exit Cap Rate Spread (bps over going-in) | `st.number_input` | 25 bps |

**Financing:**
| Field | Widget | Default |
|---|---|---|
| LTV (%) | `st.number_input` | 65% |
| Interest Rate (%/yr) | `st.number_input` | 6.25% |
| Amortization (years) | `st.number_input` | 30 |

**Existing Debt** (optional, collapsible expander — label: *"Existing Debt (optional)"*):
| Field | Widget |
|---|---|
| Outstanding Balance ($) | `st.number_input` |
| Interest Rate (%) | `st.number_input` |
| Maturity Date | `st.date_input` |
| Lender Name | `st.text_input` |

**CapEx** (optional, collapsible expander — label: *"Capital Expenditures (optional)"*):
| Field | Widget |
|---|---|
| Recent CapEx Description | `st.text_area` |
| Recent CapEx Amount ($) | `st.number_input` |
| Planned CapEx Description | `st.text_area` |
| Planned CapEx Amount ($) | `st.number_input` |

---

### Warnings for Missing Strongly-Encouraged Fields

At the bottom of Step 5, before the Continue button, evaluate which strongly-encouraged fields are blank. If any are missing, show a yellow warning box — but do NOT block generation:

> ⚠️ *The following fields are missing and will result in placeholder data in the OM:*
> - Gross Potential Rent
> - Real Estate Taxes
>
> *You can continue, but the Financial Analysis section will be incomplete. Consider filling these in for a stronger document.*

**Continue button:** Always enabled (warnings are non-blocking).

**On advance:** Assemble `st.session_state.financials` into the sidecar JSON shape expected by `financial_context.py`. Write sidecar to `om_generator/data/property_inputs/property_{slug}.json` (v1.0 schema) via `storage.write_json()`. Trigger auto-save.

---

## Step 6 — Review & Generate

### Purpose
Give the broker a final review of all inputs before generation, allow section toggling, and trigger the pipeline.

### Layout

**Section A — Input Summary Card**

Display a read-only summary of all collected inputs. Organize into collapsible sections using `st.expander`:

- Property: address, county, type, name, year built, asking price
- Specifications: units (MF), SF, stories, management, submarket, utility structure
- Branding: firm name, broker name, email, phone
- Files: list each uploaded file or "Not provided"
- Financials: NOI (if computable), asking cap rate, key assumptions

Include an "Edit" link next to each section that sends `wizard_step` back to the relevant step. Provide a "Back" button at the bottom for standard back-navigation.

---

**Section B — Section Toggle Checklist**

Show a checklist of OM sections, pre-checked per property type defaults. Broker can uncheck any section to exclude it from the generated document.

Use this default toggle table:

| Section | MF | Office | Retail | Industrial | Land |
|---|---|---|---|---|---|
| Executive Summary | ✓ | ✓ | ✓ | ✓ | ✓ |
| Investment Highlights | ✓ | ✓ | ✓ | ✓ | ✓ |
| Financial Analysis | ✓ | ✓ | ✓ | ✓ | — |
| Unit Mix & Rent Roll | ✓ | — | — | — | — |
| Comparable Sales | ✓ | ✓ | ✓ | ✓ | ✓ |
| Location Analysis | ✓ | ✓ | ✓ | ✓ | ✓ |
| Demographics | ✓ | ✓ | ✓ | ✓ | — |
| Schools | ✓ | — | — | — | — |
| Crime & Safety | ✓ | ✓ | ✓ | ✓ | — |
| Traffic | ✓ | ✓ | ✓ | ✓ | ✓ |
| Amenities | ✓ | ✓ | ✓ | ✓ | ✓ |
| Healthcare | ✓ | ✓ | — | — | — |
| Top Employers | ✓ | ✓ | ✓ | — | — |
| Development Intelligence | ✓ | ✓ | ✓ | ✓ | ✓ |
| Zoning | ✓ | ✓ | ✓ | ✓ | ✓ |
| Market Overview | ✓ | ✓ | ✓ | ✓ | — |

Store broker overrides in `st.session_state.section_overrides`.

Label the section:
> *All sections are selected by default for your property type. Uncheck any section you want to exclude from this OM.*

---

**Section C — Generate**

Show a final summary line:
> *Ready to generate: 9333 Clocktower Place — Fairfax County — Multifamily*

Large primary button: **Generate Offering Memorandum**

---

### Generation Flow

On "Generate" button click:

1. Disable the Generate button immediately (prevent double-click)

2. Show progress container. Update it module-by-module as the pipeline runs:

```python
progress_messages = [
    "Geocoding address...",
    "Loading property data...",
    "Pulling crime & safety data...",
    "Analyzing schools...",
    "Fetching healthcare data...",
    "Loading demographic data...",
    "Identifying top employers...",
    "Running comparable sales...",
    "Analyzing development pipeline...",
    "Pulling traffic counts...",
    "Loading amenities...",
    "Building location maps...",
    "Running financial model...",
    "Generating investment highlights...",
    "Rendering document...",
    "Almost done...",
]
```

Display as a `st.progress` bar with the current step message below it. Update on each step. Use a `st.empty()` container for the message so it updates in place.

**Implementation note:** `run_om_generation()` currently runs synchronously. For this build, simulate step-by-step progress by updating the progress bar at defined checkpoints within or around the `run_om_generation()` call. A full async/callback architecture is not required for this build.

3. Pass section overrides to `run_om_generation()` so excluded sections are skipped.

4. Pass the financial sidecar path from `st.session_state`.

5. On success:

```
✓  Offering Memorandum generated successfully

[Open in New Tab ↗]    [Download HTML ↓]
```

- "Open in New Tab": use `st.link_button()` pointing to the output HTML file served locally, or encode as a data URI link
- "Download HTML": `st.download_button()` with `data=open(output_path).read()`, `file_name=f"OM_{slug}.html"`, `mime="text/html"`

6. On failure:

```
✗  Generation failed

Error: [error message from result dict]

[Try Again]   [Back to Step 5]
```

Log the full traceback to console (not shown to broker).

---

## File Path Conventions

Use hyphenated slugs for all new wizard-written files. Slug function:

```python
def make_slug(address: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", address.lower()).strip("-")
```

| File Type | Path |
|---|---|
| Auto-save draft | `om_generator/data/drafts/{slug}.json` |
| Property photos | `om_generator/data/property_photos/{slug}/{n:02d}.jpg` |
| Comps CSV | `om_generator/data/comps/{slug}.csv` |
| Rent roll | `om_generator/data/rent_rolls/{slug}/rent_roll.{ext}` |
| T-12 | `om_generator/data/t12/{slug}/t12.{ext}` |
| Property sidecar (v1.0) | `om_generator/data/property_inputs/property_{slug}.json` |
| Broker assets | `om_generator/data/broker_assets/{slug}/logo.{ext}` |
| Generated OM output | `om_generator/output/{slug}_om.html` |

All writes via `storage.write_file()` or `storage.write_json()`. Never raw `open()` calls in `provenance_app.py`.

Ensure all data subdirectories are created with `storage.ensure_dir()` at app startup.

---

## `requirements.txt` — Root File

Create or replace the root `requirements.txt` with:

```
streamlit>=1.28.0
anthropic>=0.7.0
requests>=2.31.0
shapely>=2.0.0
geopy>=2.4.0
pandas>=2.0.0
openpyxl>=3.1.0
python-dotenv>=1.0.0
pytest>=7.4.0
```

Notes:
- `openpyxl` added for Excel rent roll / T-12 parsing
- `WeasyPrint` not added — deferred to PDF generation phase
- `boto3` not added — deferred to AWS architecture phase

---

## Key Patterns & Reminders

- All imports: `sys.path.insert` + `from om_generator.xxx import` — never package-prefix
- Context variable in `generate_om.py`: `ctx` — not `context`
- All secrets: `get_secret("KEY_NAME")` — never `os.getenv()` directly
- All file I/O: `storage.py` functions — never raw `open()` in `provenance_app.py`
- No business logic in `provenance_app.py` — UI only; logic in modules
- No parallel agents — sequential execution only
- Push branch, report name to Matt — no pull requests

---

## Test Properties

- Fairfax OM: 9333 Clocktower Place, Fairfax VA 22031
- Loudoun OM: 21001 Sycolin Rd, Ashburn VA 20147

After build: run both test properties through the wizard end-to-end. Confirm OM generates without errors for each.

---

## Deliverables

1. `om_generator/storage.py` — new file
2. `generate_om.py` — refactored with `run_om_generation()` callable + thin `main()` CLI wrapper
3. `provenance_app.py` — new file, repo root
4. `requirements.txt` — updated at repo root
5. All `om_generator/data/` subdirectories scaffolded with `.gitkeep`

