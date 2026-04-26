"""
Financial defaults — county-keyed Tier 2 assumptions for the financial engine.

All default assumptions live here. When a county-specific key is missing,
fall back to "default". Broker inputs from the sidecar JSON always override
these values.
"""

import json
import re
import warnings
from pathlib import Path

from property_identity import (
    AUTO_SOURCE_PREFIX,
    IDENTITY_FIELDS,
    KNOWN_SOURCES,
    PROPERTY_TYPE_MISSING_MSG,
    VALID_PROPERTY_TYPES,
    IdentityValue,
    PropertyInputs,
    SCHEMA_VERSION,
    SchemaVersionError,
)


# ============================================================================
# DEFAULTS — keyed by county (lowercase)
# ============================================================================

_FAIRFAX_DEFAULTS = {
    "vacancy_pct": 0.045,
    "credit_loss_pct": 0.005,
    "mgmt_pct": 0.05,
    "real_estate_tax_rate": 0.01040,        # per $1 of assessed value
    "insurance_per_unit": 625,
    "repairs_per_unit": 1050,
    "utility_per_unit": 879,
    "utility_benchmark_low": 820,
    "utility_benchmark_high": 960,
    "admin_pct_of_egi": 0.016,
    "reserves_per_unit": 250,
    "rent_growth_assumption": 0.035,
    "financing_ltv": 0.65,
    "financing_interest_rate": 0.0625,
    "financing_amortization": 30,
    "exit_cap_spread": 0.0025,              # exit cap = going-in cap + this spread
    "hold_period": 5,
    "below_market_threshold_pct": 0.97,     # unit is "below market" if in_place < market × this
}

DEFAULTS = {
    "fairfax": dict(_FAIRFAX_DEFAULTS),
    "loudoun": {
        **_FAIRFAX_DEFAULTS,
        "real_estate_tax_rate": 0.00875,    # Loudoun County rate
    },
    "default": dict(_FAIRFAX_DEFAULTS),
}


def get_defaults(county: str) -> dict:
    """Return merged defaults: county-specific over default."""
    base = DEFAULTS.get("default", {}).copy()
    base.update(DEFAULTS.get(county.lower(), {}))
    return base


# ============================================================================
# SIDECAR LOADER
# ============================================================================

_SCRIPT_DIR = Path(__file__).resolve().parent
_TEST_INPUTS_DIR = _SCRIPT_DIR / "test_inputs"
_PROPERTY_INPUTS_DIR = _SCRIPT_DIR / "data" / "property_inputs"


def _slugify(address: str) -> str:
    """Convert address to filename slug.

    e.g. "9333 Clocktower Place, Fairfax VA 22031"
         → "9333_clocktower_place_fairfax_va_22031"
    """
    slug = address.lower().strip()
    slug = re.sub(r'[^a-z0-9\s]', '', slug)
    slug = re.sub(r'\s+', '_', slug)
    return slug


def _validate_identity_entry(field_name: str, entry) -> IdentityValue:
    """Validate a single ``property.<field>`` entry and return an IdentityValue."""
    if not isinstance(entry, dict):
        raise SchemaVersionError(
            f"property.{field_name} must be a dict; got {type(entry).__name__}"
        )
    if "value" not in entry:
        raise SchemaVersionError(
            f"property.{field_name} is missing required 'value' key"
        )
    source = entry.get("source", "broker")
    if source not in KNOWN_SOURCES and not source.startswith(AUTO_SOURCE_PREFIX):
        raise SchemaVersionError(
            f"property.{field_name}.source={source!r} is not a known source"
        )
    return IdentityValue(
        value=entry["value"],
        source=source,
        confirmed_by_broker=bool(entry.get("confirmed_by_broker", False)),
    )


def _validate_property_type(value) -> str:
    """Enforce the schema-level requirement that ``property_type`` is set
    to one of :data:`VALID_PROPERTY_TYPES`. Raises :class:`SchemaVersionError`
    with the documented missing-field message when the value is absent;
    raises with a value-list message when the value is present but invalid.
    """
    if value is None:
        raise SchemaVersionError(PROPERTY_TYPE_MISSING_MSG)
    if value not in VALID_PROPERTY_TYPES:
        raise SchemaVersionError(
            f"property_type={value!r} is not one of: "
            f"{', '.join(VALID_PROPERTY_TYPES)}"
        )
    return value


def _validate_cap_rate_override(financial: dict) -> None:
    """Enforce 0.01 <= cap_rate_override <= 0.20 when the field is set."""
    value = financial.get("cap_rate_override")
    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise SchemaVersionError(
            f"cap_rate_override must be numeric; got {type(value).__name__}"
        )
    if not (0.01 <= float(value) <= 0.20):
        raise SchemaVersionError(
            f"cap_rate_override={value!r} out of range [0.01, 0.20]"
        )


def _parse_canonical(raw: dict, fallback_address: str,
                     fallback_county: str) -> PropertyInputs:
    """Parse a v1.0 sidecar dict into a PropertyInputs instance."""
    schema_version = raw.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Expected schema_version={SCHEMA_VERSION!r}, got {schema_version!r}"
        )

    property_type = _validate_property_type(raw.get("property_type"))

    identity_raw = raw.get("property", {})
    if not isinstance(identity_raw, dict):
        raise SchemaVersionError(
            f"'property' block must be a dict; got {type(identity_raw).__name__}"
        )

    identity = {
        name: _validate_identity_entry(name, entry)
        for name, entry in identity_raw.items()
    }

    branding_raw = raw.get("branding", {}) or {}
    if not isinstance(branding_raw, dict):
        raise SchemaVersionError(
            f"'branding' block must be a dict; got {type(branding_raw).__name__}"
        )
    branding = dict(branding_raw)

    # Anything outside the structural keys is treated as a flat financial
    # field. ``property_type`` is intentionally NOT in this set: the engine
    # dispatcher in build_financial_context still reads it from the
    # ``.financial`` dict via the deprecated alias until Wave 2 Commit 3
    # rewires the dispatcher to consume it from the dataclass directly.
    structural_keys = {
        "schema_version", "slug", "address", "county", "property", "branding",
    }
    financial = {k: v for k, v in raw.items() if k not in structural_keys}

    _validate_cap_rate_override(financial)

    return PropertyInputs(
        schema_version=schema_version,
        slug=raw.get("slug", _slugify(fallback_address)),
        address=raw.get("address", fallback_address),
        county=raw.get("county", fallback_county),
        property_type=property_type,
        identity=identity,
        financial=financial,
        branding=branding,
    )


def _wrap_legacy(raw: dict, address: str, county: str) -> PropertyInputs:
    """Wrap a legacy flat-financial dict into a PropertyInputs with empty identity.

    Legacy sidecars must still declare ``property_type`` — the
    'no code path defaults to multifamily' rule applies here too.
    """
    property_type = _validate_property_type(raw.get("property_type"))
    financial = dict(raw)
    _validate_cap_rate_override(financial)
    return PropertyInputs(
        schema_version=SCHEMA_VERSION,
        slug=_slugify(address),
        address=address,
        county=county,
        property_type=property_type,
        identity={},
        financial=financial,
        branding={},
    )


def _read_json(path: Path):
    """Read JSON, returning the parsed object or raising on parse error."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_property_inputs(address: str, county: str,
                         path: str = None) -> PropertyInputs:
    """
    Load broker property inputs for this property.

    Search order:
    0. ``path`` (explicit path — from wizard or CLI). If the file contains
       ``schema_version`` it's parsed as v1.0; otherwise it's treated as a
       legacy flat-financial sidecar with a one-shot DeprecationWarning.
    1. ``om_generator/data/property_inputs/property_<slug>.json`` — the
       canonical v1.0 runtime location written by the wizard. This
       directory is gitignored; static test fixtures live separately
       under ``om_generator/data/test_fixtures/wizard/``.
    2. ``test_inputs/financial_inputs_<slug>.json`` (LEGACY — emits
       DeprecationWarning once per load)
    3. ``test_inputs/financial_inputs_<county>.json`` (county fallback,
       legacy flat format — unchanged behavior)
    4. Defaults only (returns a PropertyInputs whose ``financial`` is the
       merged county defaults and ``identity`` is empty).

    The returned ``financial`` dict is merged over defaults: broker values
    win over defaults at the top level (nested dicts replace wholesale,
    matching the prior behavior).
    """
    defaults = get_defaults(county)

    # Tier 0: explicit path
    if path:
        explicit_path = Path(path)
        if explicit_path.exists():
            try:
                raw = _read_json(explicit_path)
            except (json.JSONDecodeError, IOError) as e:
                print(f"  Warning: Could not parse {explicit_path}: {e}")
            else:
                if isinstance(raw, dict) and "schema_version" in raw:
                    inputs = _parse_canonical(raw, address, county)
                    print(f"  Property inputs loaded (explicit, v1.0): {explicit_path}")
                else:
                    warnings.warn(
                        "Loaded a legacy flat-financial sidecar via "
                        "load_property_inputs(path=...); migrate to v1.0.",
                        DeprecationWarning,
                        stacklevel=2,
                    )
                    inputs = _wrap_legacy(raw, address, county)
                    print(f"  Property inputs loaded (explicit, legacy): {explicit_path}")
                merged = dict(defaults)
                merged.update(inputs.financial)
                inputs.financial = merged
                return inputs

    slug = _slugify(address)

    # Tier 1: canonical address-level
    canonical_file = _PROPERTY_INPUTS_DIR / f"property_{slug}.json"
    if canonical_file.exists():
        try:
            raw = _read_json(canonical_file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {canonical_file.name}: {e}")
        else:
            inputs = _parse_canonical(raw, address, county)
            merged = dict(defaults)
            merged.update(inputs.financial)
            inputs.financial = merged
            print(f"  Property inputs loaded: {canonical_file.name}")
            return inputs

    # Tier 1b: legacy address-level
    legacy_address_file = _TEST_INPUTS_DIR / f"financial_inputs_{slug}.json"
    if legacy_address_file.exists():
        try:
            raw = _read_json(legacy_address_file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {legacy_address_file.name}: {e}")
        else:
            warnings.warn(
                f"Loaded legacy sidecar {legacy_address_file.name}; "
                "migrate to om_generator/data/property_inputs/"
                "property_<slug>.json (v1.0 runtime location, gitignored).",
                DeprecationWarning,
                stacklevel=2,
            )
            inputs = _wrap_legacy(raw, address, county)
            merged = dict(defaults)
            merged.update(inputs.financial)
            inputs.financial = merged
            print(f"  Property inputs loaded (legacy): {legacy_address_file.name}")
            return inputs

    # Tier 2: county-level legacy fallback (unchanged)
    legacy_county_file = _TEST_INPUTS_DIR / f"financial_inputs_{county.lower()}.json"
    if legacy_county_file.exists():
        try:
            raw = _read_json(legacy_county_file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: Could not parse {legacy_county_file.name}: {e}")
        else:
            inputs = _wrap_legacy(raw, address, county)
            merged = dict(defaults)
            merged.update(inputs.financial)
            inputs.financial = merged
            print(
                f"  Property inputs loaded (county fallback): "
                f"{legacy_county_file.name}"
            )
            return inputs

    # Tier 3: no sidecar found. The 'no code path defaults to multifamily'
    # rule (Wave 2) means we cannot synthesise a PropertyInputs without a
    # property_type — raise so the caller knows the wizard must supply one.
    raise SchemaVersionError(
        f"No property-inputs sidecar found for '{address}'. "
        + PROPERTY_TYPE_MISSING_MSG
    )


def load_financial_inputs(address: str, county: str,
                          financial_inputs_path: str = None) -> dict:
    """Deprecated. Returns the flat ``financial`` dict from the sidecar.

    Use :func:`load_property_inputs` for new code — it returns the full
    PropertyInputs object including the identity block.
    """
    warnings.warn(
        "load_financial_inputs is deprecated; use load_property_inputs",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_property_inputs(address, county, path=financial_inputs_path).financial
