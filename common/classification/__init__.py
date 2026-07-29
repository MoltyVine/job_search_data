"""Shared classification package for Gmail and LinkedIn.

Classification itself has no library code: the Claude Code agent running the
pipeline reads each source's ``analysis/threads_dump.txt``, applies
``docs/CLASSIFICATION_CRITERIA.md``, and writes ``analysis/decisions.jsonl``
directly. This package only holds the shared decision schema/store and the
dump text formatting used to build that file.
"""

from .schema import RECRUITER_TYPES, ThreadDecision
from .store import DecisionStore

__all__ = [
    "DecisionStore",
    "RECRUITER_TYPES",
    "ThreadDecision",
]
