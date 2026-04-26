"""Identity-context builder.

Reads the v1.0 sidecar's ``.identity`` and ``.branding`` blocks and returns a
flat dict of broker-confirmed identity values keyed for the OM templates.

Designed to run AFTER ``property_context.build_property_context`` so that
broker-confirmed identity values overwrite any address-derived fallbacks
(notably ``submarket_name``).

Best-effort by design: any failure (missing file, parse error, schema
mismatch) yields an empty dict so upstream context defaults stand.
"""

from datetime import date, datetime
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


def _format_offer_due(value) -> Optional[str]:
    """Convert an ISO date (or date object) to 'April 30, 2026'.

    Returns the original string unchanged if it isn't ISO-parseable.
    Returns None if the input is empty.
    """
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, date):
        d = value
    else:
        try:
            d = date.fromisoformat(str(value))
        except (TypeError, ValueError):
            return str(value)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


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

        # Companion display field: human-readable offer due date so
        # templates can render "April 30, 2026" without a strftime filter.
        if "offer_due_date" in ctx:
            display = _format_offer_due(ctx["offer_due_date"])
            if display:
                ctx["offer_due_date_display"] = display
    except Exception:
        return {}

    return ctx
