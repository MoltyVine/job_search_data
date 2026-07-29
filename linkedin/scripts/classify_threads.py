#!/usr/bin/env python3
"""Confirm the LinkedIn conversation dump is ready, then print classification instructions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LINKEDIN_ROOT = Path(__file__).resolve().parent.parent


def print_classification_instructions(analysis_dir: Path) -> None:
    print(
        "\n=== Classification needed (LinkedIn) ===\n"
        "Read every '===== CONV #... =====' block in:\n"
        f"  {analysis_dir / 'threads_dump.txt'}\n"
        "Apply docs/CLASSIFICATION_CRITERIA.md (real person + one or more job "
        "opportunities; unsure -> exclude).\n"
        "Write one JSON object per conversation to:\n"
        f"  {analysis_dir / 'decisions.jsonl'}\n"
        "Keys: thread_id, include, reason, company, position_title, "
        'recruiter_type, other_party, source="linkedin".\n'
        "Then run:\n"
        f"  cd linkedin && {sys.executable} scripts/apply_decisions.py\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=LINKEDIN_ROOT / "analysis")
    args = parser.parse_args()

    analysis_dir = args.analysis_dir
    dump_path = analysis_dir / "threads_dump.txt"
    meta_path = analysis_dir / "threads.json"
    if not dump_path.exists() or not meta_path.exists():
        raise SystemExit(f"Missing dump files in {analysis_dir}. Run dump_threads.py first.")

    print_classification_instructions(analysis_dir)


if __name__ == "__main__":
    main()
