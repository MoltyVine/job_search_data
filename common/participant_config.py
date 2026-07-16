"""Shared participant configuration for all data-source pipelines.

Single file: config/participant.yaml (see participant.example.yaml).

Shared fields live under ``participant:``. Source-specific fields live under
top-level keys named for the source (``gmail:``, ``linkedin:``, …).
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "participant.yaml"
EXAMPLE_PATH = REPO_ROOT / "config" / "participant.example.yaml"

# Defaults match repo README — change end date in participant.yaml if needed.
DEFAULT_SEARCH_WINDOW = {
    "start": "2025-01-01",  # inclusive
    "end": "2026-01-01",  # inclusive
}


def load_participant_config(path: Path | None = None) -> dict:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing {config_path}. Copy {EXAMPLE_PATH.name} to participant.yaml "
            f"and edit:\n  cp {EXAMPLE_PATH} {CONFIG_PATH}"
        )
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "participant" not in data:
        raise ValueError(f"{config_path} must contain a top-level 'participant' key")
    return data


def source_config(name: str, config: dict | None = None) -> dict:
    """Return the source block (e.g. 'gmail', 'linkedin'), or {} if missing."""
    cfg = config or load_participant_config()
    block = cfg.get(name)
    return block if isinstance(block, dict) else {}


def participant_block(config: dict | None = None) -> dict:
    cfg = config or load_participant_config()
    return cfg["participant"]


def search_window(config: dict | None = None) -> tuple[str, str]:
    """Return (start, end) ISO dates; falls back to DEFAULT_SEARCH_WINDOW."""
    p = participant_block(config)
    w = p.get("search_window") or DEFAULT_SEARCH_WINDOW
    return (
        w.get("start") or DEFAULT_SEARCH_WINDOW["start"],
        w.get("end") or DEFAULT_SEARCH_WINDOW["end"],
    )


def summary_window(config: dict | None = None) -> tuple[str, str]:
    """Optional narrower window under linkedin.summary_window; else search_window."""
    linkedin = source_config("linkedin", config)
    w = linkedin.get("summary_window")
    if w:
        start, end = search_window(config)
        return w.get("start") or start, w.get("end") or end
    return search_window(config)


def participant_name(config: dict | None = None) -> str:
    return participant_block(config)["name"]


def first_name(config: dict | None = None) -> str:
    return participant_block(config)["first_name"]


def last_name(config: dict | None = None) -> str:
    return participant_block(config)["last_name"]


def my_emails(config: dict | None = None) -> set[str]:
    emails = source_config("gmail", config).get("my_emails") or []
    return {e.lower() for e in emails}


def linkedin_display_name(config: dict | None = None) -> str:
    linkedin = source_config("linkedin", config)
    name = linkedin.get("display_name")
    if name:
        return name
    # Fallback: full participant name
    return participant_name(config)


def participant_name_patterns(config: dict | None = None) -> str:
    """Regex fragment matching intro-style subjects for this participant."""
    import re

    p = participant_block(config)
    parts = [re.escape(p["first_name"]), re.escape(p["last_name"])]
    return "|".join(parts)


DEFAULT_CLASSIFICATION = {
    "backend": "auto",
    "ollama": {
        "base_url": "http://127.0.0.1:11434",
        "model": "qwen2.5:14b",
        "temperature": 0.1,
        "timeout_s": 180,
    },
    "max_chars_per_thread_msg": 1200,
}


def classification_settings(config: dict | None = None) -> dict:
    """Return classification block merged over defaults."""
    cfg = config or load_participant_config()
    block = cfg.get("classification")
    if not isinstance(block, dict):
        block = {}
    out = {
        "backend": block.get("backend") or DEFAULT_CLASSIFICATION["backend"],
        "max_chars_per_thread_msg": block.get("max_chars_per_thread_msg")
        or DEFAULT_CLASSIFICATION["max_chars_per_thread_msg"],
        "ollama": {
            **DEFAULT_CLASSIFICATION["ollama"],
            **(block.get("ollama") or {}),
        },
    }
    return out
