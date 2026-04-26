"""Schema definitions for the v1.0 property-inputs sidecar.

The sidecar JSON has shape:

    {
      "schema_version": "1.0",
      "slug": "...",
      "address": "...",
      "county": "...",
      "property": {
        "<identity_field>": {"value": ..., "source": ..., "confirmed_by_broker": bool},
        ...
      },
      "<flat financial fields>": ...
    }

Identity fields are wrapped in :class:`IdentityValue` so callers can tell
broker-confirmed values apart from auto-derived or default fallbacks.
Financial fields stay flat — they live alongside ``property`` at the top
level and are consumed by the existing ``mf_financials`` /
``commercial_financials`` engines unchanged.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


SCHEMA_VERSION = "1.0"

# Identity fields that may appear inside the ``property`` block.
IDENTITY_FIELDS = [
    "property_name",
    "submarket_name",
    "year_built",
    "stories",
    "floor_plan_count",
    "management_company",
    "management_company_short",
    "utility_structure_short",
    "hero_image_label",
]

# Recognised provenance labels for an :class:`IdentityValue`. Any string
# beginning with :data:`AUTO_SOURCE_PREFIX` is also accepted (e.g.
# ``"auto:loudoun_community_lookup"``).
KNOWN_SOURCES = {"broker", "derived", "default"}
AUTO_SOURCE_PREFIX = "auto:"


class SchemaVersionError(ValueError):
    """Raised when a sidecar file fails schema-version validation."""


@dataclass
class IdentityValue:
    """A single property-identity datum with its provenance."""

    value: Any
    source: str
    confirmed_by_broker: bool


@dataclass
class PropertyInputs:
    """Loaded sidecar — both identity block and flat financial inputs."""

    schema_version: str
    slug: str
    address: str
    county: str
    identity: Dict[str, IdentityValue] = field(default_factory=dict)
    financial: Dict[str, Any] = field(default_factory=dict)
