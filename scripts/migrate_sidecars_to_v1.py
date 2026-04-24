#!/usr/bin/env python3
"""Migrate legacy financial-inputs sidecars to v1.0 property-inputs schema.

For each file under:
    om_generator/test_inputs/financial_inputs_*.json
    om_generator/data/financial_inputs/*.json

write a v1.0 wrapper at:
    om_generator/data/property_inputs/property_<slug>.json

Identity block is intentionally empty: legacy sidecars never carried
identity values — those bled through from context_sample.py. Future
wizard runs populate the property block; this script only preserves
financial inputs.

After all writes, every output file is reloaded via
``load_property_inputs(path=...)`` to confirm the schema parses cleanly.
If any file fails to load the script aborts BEFORE any deletion.

Usage:
    python scripts/migrate_sidecars_to_v1.py
"""

from __future__ import annotations

import json
import shutil
import sys
import warnings
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OM_DIR = REPO_ROOT / "om_generator"
LEGACY_TEST_DIR = OM_DIR / "test_inputs"
LEGACY_DATA_DIR = OM_DIR / "data" / "financial_inputs"
TARGET_DIR = OM_DIR / "data" / "property_inputs"

sys.path.insert(0, str(OM_DIR))


def _slug_from_legacy(path: Path) -> str:
    """Extract the slug from a legacy filename.

    Both legacy directories use different prefixes:
        test_inputs/financial_inputs_<slug>.json
        data/financial_inputs/<slug>.json
    """
    stem = path.stem
    if stem.startswith("financial_inputs_"):
        return stem[len("financial_inputs_"):]
    return stem


def _wrap_legacy(legacy: dict, slug: str) -> dict:
    """Wrap a flat-financial dict into the v1.0 sidecar shape."""
    return {
        "schema_version": "1.0",
        "slug": slug,
        "address": legacy.get("address", ""),
        "county": legacy.get("county", ""),
        "property": {},  # legacy never carried identity
        **{k: v for k, v in legacy.items() if k not in {"address", "county"}},
    }


def _inventory():
    pairs = []
    for path in sorted(LEGACY_TEST_DIR.glob("financial_inputs_*.json")):
        pairs.append(path)
    if LEGACY_DATA_DIR.exists():
        for path in sorted(LEGACY_DATA_DIR.glob("*.json")):
            pairs.append(path)
    return pairs


def _verify_one(path: Path) -> None:
    """Reload via the production loader to confirm parse cleanliness."""
    from financial_defaults import load_property_inputs

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = load_property_inputs(
            address="", county="", path=str(path),
        )
    if result.schema_version != "1.0":
        raise RuntimeError(
            f"{path.name}: schema_version={result.schema_version!r} after migration"
        )


def main() -> int:
    legacy_files = _inventory()
    print(f"Inventoried {len(legacy_files)} legacy sidecar(s):")
    for p in legacy_files:
        print(f"  - {p.relative_to(REPO_ROOT)}")
    if not legacy_files:
        print("Nothing to migrate.")
        return 0

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    skipped: list[tuple[Path, str]] = []

    for src in legacy_files:
        slug = _slug_from_legacy(src)
        dst = TARGET_DIR / f"property_{slug}.json"
        if dst.exists():
            skipped.append((src, f"target exists: {dst.name}"))
            print(f"SKIP {src.name} -> {dst.name} (already exists)")
            continue
        try:
            with open(src, "r", encoding="utf-8") as f:
                legacy = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            skipped.append((src, f"parse error: {exc}"))
            print(f"SKIP {src.name}: parse error: {exc}")
            continue

        wrapped = _wrap_legacy(legacy, slug)
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(wrapped, f, indent=2)
            f.write("\n")
        written.append(dst)
        print(f"WROTE {src.name} -> {dst.relative_to(REPO_ROOT)}")

    # ── In-script verification BEFORE deletion ──────────────────────
    print(f"\nVerifying {len(written)} written file(s)…")
    for path in written:
        try:
            _verify_one(path)
        except Exception as exc:
            print(f"FAIL  {path.name}: {exc}", file=sys.stderr)
            print("Aborting before deletion. Delete nothing.", file=sys.stderr)
            return 1
        print(f"OK    {path.name}")

    # ── Deletion of legacy paths ───────────────────────────────────
    deleted_files: list[Path] = []
    for src in legacy_files:
        try:
            src.unlink()
            deleted_files.append(src)
        except OSError as exc:
            print(f"WARN: could not delete {src}: {exc}", file=sys.stderr)

    if LEGACY_DATA_DIR.exists():
        try:
            shutil.rmtree(LEGACY_DATA_DIR)
            print(f"Removed directory {LEGACY_DATA_DIR.relative_to(REPO_ROOT)}")
        except OSError as exc:
            print(f"WARN: could not remove {LEGACY_DATA_DIR}: {exc}", file=sys.stderr)

    if LEGACY_TEST_DIR.exists() and not any(LEGACY_TEST_DIR.iterdir()):
        try:
            LEGACY_TEST_DIR.rmdir()
            print(f"Removed empty directory {LEGACY_TEST_DIR.relative_to(REPO_ROOT)}")
        except OSError as exc:
            print(f"WARN: could not remove {LEGACY_TEST_DIR}: {exc}", file=sys.stderr)

    print("\n=== Migration complete ===")
    print(f"  Files migrated: {len(written)}")
    print(f"  Files skipped:  {len(skipped)}")
    print(f"  Files deleted:  {len(deleted_files)}")
    print(f"  Output dir:     {TARGET_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
