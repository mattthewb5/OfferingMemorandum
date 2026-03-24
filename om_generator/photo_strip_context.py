"""
Photo Strip Context Builder for OM Generator

Builds Street View Static API URLs for the cover page photo strip.
Uses the metadata endpoint to verify coverage before generating image URLs.

Usage:
    from photo_strip_context import build_photo_strip_context
    ctx = build_photo_strip_context(lat, lon)
"""

import sys
from pathlib import Path

import requests

# Add the multi-county research package to the path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "multi-county-real-estate-research"))

from core.api_config import get_api_key

_METADATA_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"
_IMAGE_URL = "https://maps.googleapis.com/maps/api/streetview"

_HEADINGS = [0, 90, 180, 270]
_LABELS = [
    "Street View \u2014 Front",
    "Street View \u2014 Right",
    "Street View \u2014 Rear",
    "Street View \u2014 Left",
]
_FALLBACK_LABELS = ["Aerial View", "Clubhouse", "Pool Deck", "Unit Interior"]


def _check_coverage(lat: float, lon: float, heading: int, api_key: str) -> bool:
    """Return True if Street View imagery exists at the given heading."""
    try:
        resp = requests.get(
            _METADATA_URL,
            params={
                "location": f"{lat},{lon}",
                "heading": heading,
                "key": api_key,
            },
            timeout=5,
        )
        if resp.status_code == 200:
            return resp.json().get("status") == "OK"
    except Exception:
        pass
    return False


def _build_image_url(lat: float, lon: float, heading: int, api_key: str) -> str:
    """Build a Street View Static API image URL."""
    return (
        f"{_IMAGE_URL}"
        f"?size=400x200"
        f"&location={lat},{lon}"
        f"&heading={heading}"
        f"&pitch=0"
        f"&fov=90"
        f"&key={api_key}"
    )


def _graceful_default() -> dict:
    return {
        "photo_urls": [None, None, None, None],
        "photo_labels": _FALLBACK_LABELS[:],
    }


def build_photo_strip_context(lat: float, lon: float) -> dict:
    """Build Street View photo strip URLs for the cover page.

    Returns dict with:
        photo_urls:   list of 4 URL strings (or None where unavailable)
        photo_labels: list of 4 label strings
    """
    try:
        api_key = get_api_key("GOOGLE_MAPS_API_KEY")
        if not api_key:
            print("  WARNING: GOOGLE_MAPS_API_KEY not available for photo strip",
                  file=sys.stderr)
            return _graceful_default()

        urls = []
        labels = []
        any_ok = False

        for i, heading in enumerate(_HEADINGS):
            if _check_coverage(lat, lon, heading, api_key):
                urls.append(_build_image_url(lat, lon, heading, api_key))
                labels.append(_LABELS[i])
                any_ok = True
            else:
                urls.append(None)
                labels.append(_LABELS[i])

        if not any_ok:
            return _graceful_default()

        return {
            "photo_urls": urls,
            "photo_labels": labels,
        }

    except Exception as exc:
        print(f"  WARNING: Photo strip context failed: {exc}", file=sys.stderr)
        return _graceful_default()
