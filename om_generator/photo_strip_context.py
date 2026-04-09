"""
Photo Strip Context Builder for OM Generator.

Three-tier photo sourcing for the cover page photo strip:
  Tier 1 — Broker-uploaded photos under data/property_photos/<slug>/
  Tier 2 — Google Street View Static API outdoor fallback (per slot)
  Tier 3 — None (cover.html renders a grey placeholder)

All resolved URLs are emitted as base64 data URIs so the rendered OM
is self-contained.

Usage:
    from photo_strip_context import build_photo_strip_context
    ctx = build_photo_strip_context(address, lat, lon)
"""

import base64
import logging
import re
import sys
from pathlib import Path

import requests

# Add the multi-county research package to the path (for api_config)
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

logger = logging.getLogger(__name__)

_METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
_IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"

# Slot → compass heading (degrees)
_HEADINGS = [0, 180, 90, 270]  # front, rear, right, left

# Broker photo directory
_PHOTOS_ROOT = Path(__file__).resolve().parent / "data" / "property_photos"

# Accepted broker photo extensions (lowercase, leading dot)
_BROKER_EXTS = (".jpg", ".jpeg", ".png", ".webp")

_EXT_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _slugify(address: str) -> str:
    """Lowercase, non-alphanumeric → hyphen, collapse, strip edges."""
    slug = re.sub(r"[^a-z0-9]+", "-", address.lower())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def _encode_file(path: Path) -> str | None:
    """Read *path*, base64-encode, wrap as a data URI. Returns None on error."""
    try:
        mime = _EXT_MIME[path.suffix.lower()]
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception as exc:
        logger.warning("Failed to encode broker photo %s: %s", path, exc)
        return None


def _find_broker_photo(slot_dir: Path, slot_num: int) -> Path | None:
    """Look for `0N.<ext>` in *slot_dir* for the given 1-based slot number."""
    stem = f"{slot_num:02d}"
    for ext in _BROKER_EXTS:
        candidate = slot_dir / f"{stem}{ext}"
        if candidate.is_file():
            return candidate
        # Case-insensitive fallback: same stem, any case extension
        candidate_upper = slot_dir / f"{stem}{ext.upper()}"
        if candidate_upper.is_file():
            return candidate_upper
    return None


def _load_broker_photos(address: str) -> list[str | None]:
    """Tier 1: return 4-element list of data-URI strings or None per slot."""
    slug = _slugify(address)
    slot_dir = _PHOTOS_ROOT / slug
    urls: list[str | None] = [None, None, None, None]

    if not slot_dir.is_dir():
        logger.info("Broker photos found: 0/4 (no directory at %s)", slot_dir)
        return urls

    found = 0
    for i in range(4):
        photo_path = _find_broker_photo(slot_dir, i + 1)
        if photo_path is None:
            continue
        data_uri = _encode_file(photo_path)
        if data_uri:
            urls[i] = data_uri
            found += 1

    logger.info("Broker photos found: %d/4 (dir=%s)", found, slot_dir)
    return urls


def _streetview_metadata(lat: float, lon: float, heading: int, api_key: str) -> bool:
    """Tier 2 Step A: check coverage via metadata endpoint.

    Returns True iff metadata says imagery exists. Logs WARNING on non-200
    with the status code and a response-body snippet (for diagnosing key
    restriction issues). Logs DEBUG when HTTP 200 but status != "OK".
    """
    try:
        resp = requests.get(
            _METADATA_URL,
            params={
                "location": f"{lat},{lon}",
                "heading": heading,
                "source": "outdoor",
                "key": api_key,
            },
            timeout=10,
        )
    except Exception as exc:
        logger.warning(
            "Street View metadata request failed (heading=%d): %s", heading, exc
        )
        return False

    if resp.status_code != 200:
        logger.warning(
            "Street View metadata non-200 (heading=%d): status=%d body=%r",
            heading,
            resp.status_code,
            resp.text[:200],
        )
        return False

    try:
        status = resp.json().get("status")
    except Exception as exc:
        logger.warning(
            "Street View metadata JSON parse failed (heading=%d): %s", heading, exc
        )
        return False

    if status != "OK":
        logger.debug(
            "Street View metadata heading=%d: status=%s (no coverage)",
            heading,
            status,
        )
        return False
    return True


def _streetview_image(lat: float, lon: float, heading: int, api_key: str) -> str | None:
    """Tier 2 Step B: fetch the image bytes, base64-encode, return data URI."""
    try:
        resp = requests.get(
            _IMAGE_URL,
            params={
                "size": "800x500",
                "location": f"{lat},{lon}",
                "heading": heading,
                "pitch": 5,
                "fov": 90,
                "source": "outdoor",
                "key": api_key,
            },
            timeout=15,
        )
    except Exception as exc:
        logger.warning(
            "Street View image fetch failed (heading=%d): %s", heading, exc
        )
        return None

    if resp.status_code != 200:
        logger.warning(
            "Street View image non-200 (heading=%d): status=%d body=%r",
            heading,
            resp.status_code,
            resp.text[:200],
        )
        return None

    b64 = base64.b64encode(resp.content).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _fill_with_streetview(
    urls: list[str | None], lat: float, lon: float
) -> list[str | None]:
    """Tier 2: fill empty slots in *urls* with Street View data URIs."""
    api_key = get_api_key("GOOGLE_MAPS_API_KEY")
    sv_count = 0
    for i, existing in enumerate(urls):
        if existing is not None:
            continue
        heading = _HEADINGS[i]
        if not _streetview_metadata(lat, lon, heading, api_key):
            continue
        data_uri = _streetview_image(lat, lon, heading, api_key)
        if data_uri is not None:
            urls[i] = data_uri
            sv_count += 1

    logger.info("Street View coverage: %d/4 headings", sv_count)
    return urls


def build_photo_strip_context(address: str, lat: float, lon: float) -> dict:
    """Build the photo strip context for the cover page.

    Tier 1 — Broker photos under data/property_photos/<slug>/
    Tier 2 — Street View outdoor fallback for any empty slot
    Tier 3 — None (template renders the grey placeholder)

    Parameters
    ----------
    address : str
        Full address string, used to locate the broker-photo directory.
    lat, lon : float
        Geocoded coordinates for the Street View fallback.

    Returns
    -------
    dict
        ``{"photo_urls": [url_or_none, url_or_none, url_or_none, url_or_none]}``
    """
    urls = _load_broker_photos(address)
    urls = _fill_with_streetview(urls, lat, lon)
    return {"photo_urls": urls}
