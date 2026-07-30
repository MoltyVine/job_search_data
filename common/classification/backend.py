"""Resolve classification backend: agent | openrouter."""

from __future__ import annotations

from typing import Literal

from common.participant_config import classification_settings

from .openrouter_client import API_KEY_ENV_VAR, OpenRouterClient

BackendName = Literal["agent", "openrouter"]


def resolve_backend(explicit: str | None = None, config: dict | None = None) -> BackendName:
    """Pick backend.

    Order: CLI ``explicit`` → config ``classification.backend`` → ``agent``.

    ``agent`` (default) means the Claude Code agent running the pipeline
    classifies inline — no network call, no API key. ``openrouter`` sends
    each thread to OpenRouter for automated classification; requires
    ``OPENROUTER_API_KEY`` to be set.
    """
    settings = classification_settings(config)
    choice = (explicit or settings.get("backend") or "agent").strip().lower()

    if choice not in ("agent", "openrouter"):
        raise SystemExit(f"Unknown classification backend '{choice}'. Use agent or openrouter.")
    return choice  # type: ignore[return-value]


def make_openrouter_client(config: dict | None = None) -> OpenRouterClient:
    settings = classification_settings(config)
    openrouter_cfg = settings.get("openrouter") or {}
    client = OpenRouterClient(
        model=openrouter_cfg.get("model") or "anthropic/claude-haiku-4.5",
        temperature=float(openrouter_cfg.get("temperature", 0.1)),
        timeout_s=float(openrouter_cfg.get("timeout_s", 180)),
    )
    if not client.api_key:
        raise SystemExit(
            f"Backend 'openrouter' requested but {API_KEY_ENV_VAR} is not set.\n"
            f"Export it (never put it in config/participant.yaml), e.g.:\n"
            f"  export {API_KEY_ENV_VAR}=sk-or-...\n"
            "Or pass --backend agent to classify in this session instead."
        )
    return client
