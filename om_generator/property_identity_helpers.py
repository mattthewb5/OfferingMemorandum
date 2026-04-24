"""Reuse-only auto-derivation helpers for the v1.0 property sidecar.

Each helper either returns an :class:`IdentityValue` (when an existing
pipeline cleanly exposes the answer for the given inputs) or ``None``.
Helpers do not build new fetch logic — they wire existing modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from property_identity import IdentityValue

logger = logging.getLogger(__name__)


# ── sys.path bootstrapping (matches generate_om.py convention) ──────
_OM_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _OM_DIR.parent
_MC_RESEARCH = _REPO_ROOT / "multi-county-real-estate-research"

for _candidate in (str(_OM_DIR), str(_MC_RESEARCH)):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)


# ── Submarket via zoning growth-center pipeline ────────────────────

# Treat the property as belonging to a growth-center submarket only when
# it sits inside (or essentially at) the growth-center boundary.
_INSIDE_THRESHOLD_MILES = 0.5

_SUPPORTED_COUNTIES = {"fairfax", "loudoun"}


def _build_zoning_context_or_none(lat, lon, county):
    """Wrapper that imports + calls zoning_context.build_zoning_context.

    Isolated for ease of monkeypatching in tests. Returns ``None`` when the
    module isn't importable or the call raises.
    """
    try:
        from zoning_context import build_zoning_context  # type: ignore
    except ImportError:
        logger.debug("zoning_context not importable; submarket auto-derive skipped")
        return None
    try:
        return build_zoning_context(lat, lon, county)
    except Exception as exc:  # pragma: no cover — pipeline is best-effort
        logger.debug("build_zoning_context raised %s; submarket auto-derive skipped", exc)
        return None


def derive_submarket_name(
    county: str,
    address: str,
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[IdentityValue]:
    """Return the nearest growth-center name, when the property is inside one.

    Reuses ``zoning_context.build_zoning_context`` which already exposes
    ``growth_center_name`` and ``growth_center_distance_raw`` for both
    Fairfax and Loudoun. Returns ``None`` when the inputs are incomplete,
    the pipeline raises, or the property is outside any growth center.
    """
    county_key = (county or "").strip().lower()
    if county_key not in _SUPPORTED_COUNTIES or lat is None or lon is None:
        return None

    ctx = _build_zoning_context_or_none(lat, lon, county_key)
    if ctx is None:
        return None

    if not isinstance(ctx, dict):
        return None

    name = ctx.get("growth_center_name") or ""
    raw = ctx.get("growth_center_distance_raw")

    if not name or name == "N/A":
        return None
    if raw is None or raw > _INSIDE_THRESHOLD_MILES:
        return None

    return IdentityValue(
        value=name,
        source=f"auto:{county_key}_zoning_growth_center",
        confirmed_by_broker=False,
    )


# ── Management company via Loudoun community lookup ────────────────


def derive_management_company(
    county: str,
    subdivision_name: Optional[str],
) -> Optional[IdentityValue]:
    """Loudoun-only: read management_company from the curated communities JSON."""
    county_key = (county or "").strip().lower()
    if county_key != "loudoun":
        return None
    name = (subdivision_name or "").strip()
    if not name:
        return None

    try:
        from core.loudoun_community_lookup import CommunityLookup  # type: ignore
    except (ImportError, FileNotFoundError):
        return None

    try:
        lookup = CommunityLookup()
    except (FileNotFoundError, OSError):
        return None
    except Exception as exc:  # pragma: no cover
        logger.debug("CommunityLookup init failed: %s", exc)
        return None

    try:
        community = lookup.get_community_for_subdivision(name)
    except Exception as exc:  # pragma: no cover
        logger.debug("get_community_for_subdivision raised %s", exc)
        return None

    if not community:
        return None

    mgmt = community.get("management_company")
    if not mgmt:
        return None

    return IdentityValue(
        value=mgmt,
        source="auto:loudoun_community_lookup",
        confirmed_by_broker=False,
    )
