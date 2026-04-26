"""Engine routing dispatcher.

A thin layer that consumes the v1.0 :class:`PropertyInputs` dataclass and
routes to the appropriate engine based on the *structural* ``property_type``
attribute — not the catch-all ``.financial`` dict copy. The engines
themselves still accept the flat financial dict as their primary input
since the broader Wave 2 scope leaves the deprecated
:func:`load_financial_inputs` alias untouched.
"""

from typing import Optional

from commercial_financials import compute_commercial_financials
from exceptions import OMFinancialEngineInputError
from mf_financials import compute_mf_financials
from property_identity import PropertyInputs


def route_financial_engine(
    inputs: PropertyInputs,
    defaults: dict,
    market_rents: Optional[dict] = None,
) -> dict:
    """Dispatch to the right engine based on ``inputs.property_type``.

    ``inputs`` is the PropertyInputs dataclass returned by
    :func:`load_property_inputs`. The dispatcher reads ``property_type``
    from the dataclass attribute (validated at sidecar load) and never
    consults the ``.financial`` dict for type information.

    Args:
        inputs: Loaded sidecar.
        defaults: County defaults from :func:`get_defaults`.
        market_rents: RentCast lookup result (MF only); ``None`` or ``{}``
            for the commercial path.

    Returns:
        Engine output dict ready for ``ctx.update()``.

    Raises:
        OMFinancialEngineInputError: When the engine's input prerequisites
            are missing or inconsistent (POR mode without override,
            missing unit_mix for MF, missing total_sf for commercial,
            etc.).
        NotImplementedError: When ``property_type == "land"`` — Wave 2
            stubs this path; full implementation is Wave 3+.
    """
    pt = inputs.property_type
    market_rents = market_rents or {}

    if pt == "multifamily":
        return compute_mf_financials(inputs.financial, defaults, market_rents)
    if pt in ("retail", "office", "industrial"):
        return compute_commercial_financials(inputs.financial, defaults, pt)
    if pt == "land":
        raise NotImplementedError(
            "Land property type stubbed in Wave 2; full path is Wave 3+."
        )

    # Unreachable when the schema validator does its job — but be loud
    # if we ever land here so the bug doesn't hide as silent fallback.
    raise OMFinancialEngineInputError(
        f"Engine dispatcher received unknown property_type={pt!r}. "
        f"Schema validation should have rejected this at sidecar load."
    )
