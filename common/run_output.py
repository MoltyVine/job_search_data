"""Timestamped output run directories + latest symlink."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


def timestamp_label(now: datetime | None = None) -> str:
    """Local wall-clock stamp YYYYMMDD-HHMMSS."""
    return (now or datetime.now()).strftime("%Y%m%d-%H%M%S")


def new_run_dir(output_root: Path, *, now: datetime | None = None) -> Path:
    """Create output_root/runs/<YYYYMMDD-HHMMSS>/ (append -2, -3, … on collision)."""
    root = Path(output_root)
    runs = root / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    base = timestamp_label(now)
    label = base
    n = 2
    while (runs / label).exists():
        label = f"{base}-{n}"
        n += 1
    run_dir = runs / label
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def update_latest_symlink(output_root: Path, run_dir: Path) -> Path:
    """Point output_root/latest → relative runs/<ts>. Returns the symlink path."""
    root = Path(output_root).resolve()
    run = Path(run_dir).resolve()
    if not run.is_relative_to(root):
        raise ValueError(f"run_dir {run} is not under output_root {root}")
    rel = run.relative_to(root)
    latest = root / "latest"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(rel)
    return latest


def resolve_write_dir(output_root: Path, *, in_place: bool) -> Path:
    """Return directory to write deliverables into; update latest unless in_place."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    if in_place:
        return root
    run_dir = new_run_dir(root)
    update_latest_symlink(root, run_dir)
    return run_dir


def snapshot_decisions(decisions_path: Path, dest_dir: Path) -> Path | None:
    """Copy decisions.jsonl into dest_dir if it exists. Returns dest path or None."""
    src = Path(decisions_path)
    if not src.is_file():
        return None
    dest = Path(dest_dir) / "decisions.jsonl"
    shutil.copy2(src, dest)
    return dest
