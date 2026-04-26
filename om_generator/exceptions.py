"""Exceptions raised by the OM generator.

``OMFinancialEngineInputError`` is intentionally rooted at ``Exception``
(not ``ValueError``) so that ``build_financial_context`` can let it
propagate while continuing to swallow unrelated errors. ``SchemaVersionError``
(a ``ValueError`` subclass) covers the separate concern of sidecar-format
violations at load time; the two error classes deliberately do not share
a base.
"""


class OMFinancialEngineInputError(Exception):
    """Raised when the financial engine cannot proceed because its
    sidecar inputs are missing or inconsistent (e.g. POR mode with no
    cap_rate_override; multifamily engine with no unit_mix). Distinct
    from ``SchemaVersionError`` so callers can tell engine-input
    failures apart from sidecar-format violations.
    """
