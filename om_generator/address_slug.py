"""Shared address-slug helper.

Single source of truth for the wizard's slug function. Reused by the
wizard sidecar writer (provenance_app) and the audit-trail filename
builder (audit_trail) so audit artifacts always line up with what the
wizard wrote to disk.

Pattern: lowercase, collapse runs of non-alphanumerics into a single
hyphen, strip leading/trailing hyphens. The ZIP code is preserved as
its own segment when present in the input address.

Examples:
    "21001 Sycolin Rd, Ashburn VA 20147"
        → "21001-sycolin-rd-ashburn-va-20147"
    "9333 Clocktower Place, Fairfax VA 22031"
        → "9333-clocktower-place-fairfax-va-22031"
"""

import re


def make_address_slug(address: str) -> str:
    """Convert a property address into the wizard's filename slug."""
    return re.sub(r"[^a-z0-9]+", "-", address.lower()).strip("-")
