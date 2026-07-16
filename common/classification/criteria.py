"""Load shared classification criteria markdown."""

from __future__ import annotations

from pathlib import Path

from common.participant_config import REPO_ROOT

CRITERIA_PATH = REPO_ROOT / "docs" / "CLASSIFICATION_CRITERIA.md"


def load_criteria(path: Path | None = None) -> str:
    criteria_path = path or CRITERIA_PATH
    if not criteria_path.exists():
        raise FileNotFoundError(f"Missing classification criteria: {criteria_path}")
    return criteria_path.read_text(encoding="utf-8")
