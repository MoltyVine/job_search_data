#!/usr/bin/env python3
"""Orchestrate LinkedIn extraction: stats → dump → classify → apply."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LINKEDIN_ROOT = Path(__file__).resolve().parent
SCRIPTS = LINKEDIN_ROOT / "scripts"
ANALYSIS = LINKEDIN_ROOT / "analysis"


def run(cmd: list[str]) -> None:
    print(f"\n$ {' '.join(cmd)}\n")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LinkedIn message extraction — dump, classify, write outputs"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=LINKEDIN_ROOT / "data",
        help="Directory with Complete_LinkedInDataExport_* folder",
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--skip-stats", action="store_true")
    parser.add_argument("--skip-dump", action="store_true")
    parser.add_argument("--skip-classify", action="store_true")
    parser.add_argument("--skip-apply", action="store_true")
    args = parser.parse_args()

    config_flag = ["--config", str(args.config)] if args.config else []
    data_flag = ["--data-dir", str(args.data_dir)]
    py = sys.executable

    if not args.skip_stats:
        run([py, str(SCRIPTS / "stats.py"), *data_flag, *config_flag])

    if not args.skip_dump:
        run([py, str(SCRIPTS / "dump_threads.py"), *data_flag, *config_flag])

    if not args.skip_classify:
        classify_cmd = [
            py,
            str(SCRIPTS / "classify_threads.py"),
            "--analysis-dir",
            str(ANALYSIS),
        ]
        run(classify_cmd)

    decisions = ANALYSIS / "decisions.jsonl"
    if args.skip_apply:
        print("\nSkipped apply.")
    elif not decisions.exists() or decisions.stat().st_size == 0:
        print(
            "\nNo decisions.jsonl yet — classify the conversations in this session "
            "(see docs/CLASSIFICATION_CRITERIA.md), then run:\n"
            f"  {py} scripts/apply_decisions.py"
        )
    else:
        run(
            [
                py,
                str(SCRIPTS / "apply_decisions.py"),
                *data_flag,
                "--analysis-dir",
                str(ANALYSIS),
                "--output-dir",
                str(LINKEDIN_ROOT / "output"),
                *config_flag,
            ]
        )
        print(f"\nOutputs: {LINKEDIN_ROOT / 'output' / 'latest'}/ (symlink to latest run)")

    print("\nDone.")


if __name__ == "__main__":
    main()
