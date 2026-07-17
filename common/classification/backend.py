"""Resolve classification backend: auto | ollama | cursor."""

from __future__ import annotations

import sys
from typing import Literal

from common.participant_config import classification_settings

from .client import OllamaClient, ensure_ollama_running

BackendName = Literal["ollama", "cursor"]


def resolve_backend(
    explicit: str | None = None,
    config: dict | None = None,
    *,
    interactive: bool = True,
) -> BackendName:
    """Pick backend.

    Order: CLI ``explicit`` → config ``classification.backend`` → probe Ollama
    (auto-start ``ollama serve`` if the binary is installed) → interactive prompt
    (if allowed) → error.
    """
    settings = classification_settings(config)
    choice = (explicit or settings.get("backend") or "auto").strip().lower()

    ollama_cfg = settings.get("ollama") or {}
    base_url = ollama_cfg.get("base_url") or "http://127.0.0.1:11434"

    if choice in {"ollama", "local", "llm"}:
        if not ensure_ollama_running(base_url):
            raise SystemExit(
                f"Backend 'ollama' requested but Ollama is not reachable at {base_url}.\n"
                "Install Ollama, or start it with: ollama serve\n"
                "Or pass --backend cursor"
            )
        return "ollama"

    if choice in {"cursor", "agent"}:
        return "cursor"

    if choice != "auto":
        raise SystemExit(
            f"Unknown classification backend '{choice}'. Use auto, ollama, or cursor."
        )

    if ensure_ollama_running(base_url):
        print(f"Using local LLM via Ollama at {base_url}")
        return "ollama"

    if not interactive or not sys.stdin.isatty():
        raise SystemExit(
            "Ollama not found and no interactive terminal for Cursor fallback.\n"
            "Install/start Ollama (ollama serve && ollama pull <model>), or pass:\n"
            "  --backend cursor\n"
            "  --backend ollama"
        )

    print(
        f"Ollama not reachable at {base_url}.\n"
        "You can classify with a Cursor agent instead (dump threads, then invoke the skill).\n"
    )
    answer = input("Use Cursor agent backend? [y/N]: ").strip().lower()
    if answer in {"y", "yes"}:
        return "cursor"

    raise SystemExit(
        "Aborted. Start Ollama or re-run with --backend cursor / --backend ollama."
    )


def make_ollama_client(config: dict | None = None) -> OllamaClient:
    settings = classification_settings(config)
    ollama_cfg = settings.get("ollama") or {}
    return OllamaClient(
        base_url=ollama_cfg.get("base_url") or "http://127.0.0.1:11434",
        model=ollama_cfg.get("model") or "llama3.1:8b",
        temperature=float(ollama_cfg.get("temperature", 0.1)),
        timeout_s=float(ollama_cfg.get("timeout_s", 180)),
    )
