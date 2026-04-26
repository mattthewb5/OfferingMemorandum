"""Identity-context builder.

Reads the v1.0 sidecar's ``.identity`` and ``.branding`` blocks and returns a
flat dict of broker-confirmed identity values keyed for the OM templates.

Designed to run AFTER ``property_context.build_property_context`` so that
broker-confirmed identity values overwrite any address-derived fallbacks
(notably ``submarket_name``).

Best-effort by design: any failure (missing file, parse error, schema
mismatch) yields an empty dict so upstream context defaults stand.
"""

from typing import Optional

from financial_defaults import load_property_inputs


_IDENTITY_KEYS = (
    "property_name",
    "year_built",
    "stories",
    "floor_plan_count",
    "management_company",
    "management_company_short",
    "submarket_name",
    "utility_structure_short",
    "hero_image_label",
)

_BRANDING_KEYS = (
    "broker_firm",
    "broker_name",
    "broker_title",
    "broker_phone",
    "broker_email",
    "offer_due_date",
)


def build_identity_context(financial_inputs_path: Optional[str]) -> dict:
    """Return a dict of identity + branding context overrides.

    Args:
        financial_inputs_path: Explicit path to the v1.0 sidecar JSON.

    Returns:
        Dict of context keys whose value is non-None. Returns ``{}`` on any
        failure or when no sidecar path is supplied.
    """
    if not financial_inputs_path:
        return {}

    try:
        inputs = load_property_inputs(
            address="", county="", path=financial_inputs_path
        )
    except Exception:
        return {}

    ctx: dict = {}

    try:
        identity = getattr(inputs, "identity", {}) or {}
        for key in _IDENTITY_KEYS:
            entry = identity.get(key)
            if entry is None:
                continue
            value = getattr(entry, "value", None)
            if value is None:
                continue
            ctx[key] = value

        branding = getattr(inputs, "branding", None) or {}
        for key in _BRANDING_KEYS:
            value = branding.get(key)
            if value is None:
                continue
            ctx[key] = value
    except Exception:
        return {}

    return ctx
