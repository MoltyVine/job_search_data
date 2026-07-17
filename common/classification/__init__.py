"""Shared classification package for Gmail and LinkedIn."""

from .backend import make_ollama_client, resolve_backend
from .classify import classify_threads_ollama
from .client import OllamaClient, ensure_ollama_running, ollama_reachable
from .schema import RECRUITER_TYPES, ThreadDecision
from .store import DecisionStore

__all__ = [
    "DecisionStore",
    "OllamaClient",
    "RECRUITER_TYPES",
    "ThreadDecision",
    "classify_threads_ollama",
    "ensure_ollama_running",
    "make_ollama_client",
    "ollama_reachable",
    "resolve_backend",
]
