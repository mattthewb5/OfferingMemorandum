"""Audit trail for OM generation runs.

Every call to ``generate_om.run_om_generation`` writes three timestamped
files into ``om_generator/data/audit_trail/``:

    <YYYY-MM-DD_HH-MM-SS>_<slug>_wizard.json   — copy of the broker sidecar
    <YYYY-MM-DD_HH-MM-SS>_<slug>_om.html       — copy of the rendered OM
    <YYYY-MM-DD_HH-MM-SS>_<slug>_meta.json     — git/result metadata

The leading ISO timestamp keeps newest runs at the top when the
directory is sorted by Name (descending). Files older than
``AUDIT_RETENTION_DAYS`` are deleted on the next ``setup_audit`` call.

The audit layer is best-effort: every I/O call is wrapped, every
failure is logged but swallowed, and OM generation always proceeds
even if no audit can be written.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from address_slug import make_address_slug

logger = logging.getLogger(__name__)


AUDIT_RETENTION_DAYS = 30
AUDIT_DIR = Path(__file__).resolve().parent / "data" / "audit_trail"


@dataclass
class AuditHandle:
    """Per-run audit context shared between setup and finalize."""

    audit_dir: Path
    prefix: str
    address: str
    started_at_iso: str


def _cleanup_old_files(audit_dir: Path, retention_days: int) -> None:
    """Delete any file in *audit_dir* whose mtime is older than *retention_days*."""
    if not audit_dir.exists():
        return
    cutoff = time.time() - (retention_days * 86_400)
    for entry in audit_dir.iterdir():
        if not entry.is_file():
            continue
        try:
            if entry.stat().st_mtime < cutoff:
                entry.unlink()
        except OSError as exc:
            logger.warning("Audit cleanup could not remove %s: %s", entry, exc)


def setup_audit(
    address: str, financial_inputs_path: Optional[str]
) -> Optional[AuditHandle]:
    """Prepare the audit directory and copy the wizard sidecar in.

    Returns an ``AuditHandle`` on success or ``None`` if anything in the
    setup path fails. Never raises.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        slug = make_address_slug(address) if address else "unknown-address"
        prefix = f"{timestamp}_{slug}"

        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        _cleanup_old_files(AUDIT_DIR, AUDIT_RETENTION_DAYS)

        if financial_inputs_path:
            src = Path(financial_inputs_path)
            if src.exists() and src.is_file():
                try:
                    shutil.copy2(src, AUDIT_DIR / f"{prefix}_wizard.json")
                except OSError as exc:
                    logger.warning(
                        "Audit could not copy wizard sidecar %s: %s", src, exc
                    )

        return AuditHandle(
            audit_dir=AUDIT_DIR,
            prefix=prefix,
            address=address,
            started_at_iso=datetime.now().isoformat(timespec="seconds"),
        )
    except (OSError, IOError) as exc:
        logger.warning("setup_audit failed; skipping audit for this run: %s", exc)
        return None


def _git_field(args: list[str], cwd: Path) -> Optional[str]:
    """Run a short git query; return stripped stdout or ``None`` on any failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    out = (result.stdout or "").strip()
    return out or None


def finalize_audit(
    audit_handle: Optional[AuditHandle],
    result: dict,
    output_path: Optional[str],
) -> None:
    """Copy the rendered OM and write a meta JSON. Never raises."""
    if audit_handle is None:
        return

    audit_dir = audit_handle.audit_dir
    prefix = audit_handle.prefix

    # Copy the rendered OM if it exists
    if output_path:
        try:
            src = Path(output_path)
            if src.exists() and src.is_file():
                shutil.copy2(src, audit_dir / f"{prefix}_om.html")
        except OSError as exc:
            logger.warning("Audit could not copy OM output %s: %s", output_path, exc)

    # Build meta dict
    repo_root = Path(__file__).resolve().parent.parent
    meta = {
        "timestamp": audit_handle.started_at_iso,
        "address": audit_handle.address,
        "success": bool(result.get("success", False)) if isinstance(result, dict) else False,
        "error": (result.get("error") if isinstance(result, dict) else None),
        "git_branch": _git_field(["branch", "--show-current"], repo_root),
        "git_commit": _git_field(["rev-parse", "--short", "HEAD"], repo_root),
    }

    try:
        meta_path = audit_dir / f"{prefix}_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")
    except OSError as exc:
        logger.warning("Audit could not write meta JSON: %s", exc)
