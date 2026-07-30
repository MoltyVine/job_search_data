"""Shared classification package for Gmail and LinkedIn.

Two backends, selected per docs/CLASSIFICATION_CRITERIA.md and
``classification.backend`` in participant.yaml:

- ``agent`` (default) — the Claude Code agent running the pipeline reads
  each source's ``analysis/threads_dump.txt`` and writes
  ``analysis/decisions.jsonl`` directly. No network call, no API key.
- ``openrouter`` (opt-in) — for high-volume runs. Sends each thread to
  OpenRouter for automated classification; requires ``OPENROUTER_API_KEY``.
"""

from .backend import make_openrouter_client, resolve_backend
from .classify import classify_threads_openrouter
from .openrouter_client import OpenRouterClient
from .schema import RECRUITER_TYPES, ThreadDecision
from .store import DecisionStore

__all__ = [
    "DecisionStore",
    "OpenRouterClient",
    "RECRUITER_TYPES",
    "ThreadDecision",
    "classify_threads_openrouter",
    "make_openrouter_client",
    "resolve_backend",
]
