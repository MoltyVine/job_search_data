"""Persist classification decisions as JSONL (resume-friendly)."""

from __future__ import annotations

import json
from pathlib import Path

from .schema import ThreadDecision


class DecisionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, ThreadDecision]:
        if not self.path.exists():
            return {}
        out: dict[str, ThreadDecision] = {}
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                decision = ThreadDecision.from_dict(data)
                out[decision.thread_id] = decision
        return out

    def append(self, decision: ThreadDecision) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + "\n")

    def write_all(self, decisions: dict[str, ThreadDecision]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for decision in decisions.values():
                f.write(json.dumps(decision.to_dict(), ensure_ascii=False) + "\n")
