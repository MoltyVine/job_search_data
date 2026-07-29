#!/usr/bin/env python3
"""End-to-end Gmail takeout → dump → classify → recruiter conversations."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from participant_config import load_participant_config, search_window

GMAIL_DIR = Path(__file__).resolve().parent
TAKEOUT_EXTRACTS = GMAIL_DIR / "takeout_extracts"
SCRIPTS = GMAIL_DIR / "scripts"
ANALYSIS_BASE = GMAIL_DIR / "analysis"
OUTPUT_BASE = GMAIL_DIR / "output"


def list_takeout_dirs(extracts_dir: Path = TAKEOUT_EXTRACTS) -> list[Path]:
    if not extracts_dir.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(extracts_dir.iterdir()):
        if child.is_dir() and any(child.rglob("*.mbox")):
            found.append(child)
    return found


def resolve_takeout_dir(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.resolve()
    candidates = list_takeout_dirs()
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(
            f"No takeout folders with .mbox under {TAKEOUT_EXTRACTS}/\n"
            f"Unzip a Google Takeout export there, or pass the folder path."
        )
    listed = "\n".join(f"  {p.name}" for p in candidates)
    raise FileNotFoundError(
        f"Multiple takeout folders in {TAKEOUT_EXTRACTS}/:\n{listed}\n"
        f"Pass one explicitly."
    )


def find_mbox(takeout_dir: Path) -> Path:
    def is_source_mbox(path: Path) -> bool:
        name = path.name
        if name == "recruiter_conversations.mbox":
            return False
        if name.endswith("_filtered.mbox"):
            return False
        return True

    candidates = sorted(p for p in takeout_dir.rglob("*.mbox") if is_source_mbox(p))
    if not candidates:
        raise FileNotFoundError(f"No .mbox files under {takeout_dir}")
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(
        "Multiple mbox files found; pass --mbox explicitly:\n"
        + "\n".join(str(p) for p in candidates)
    )


def run_step(cmd: list[str]) -> None:
    print(f"\n>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=GMAIL_DIR, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("takeout_dir", type=Path, nargs="?", default=None)
    parser.add_argument("--mbox", type=Path, help="Explicit source .mbox")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--account",
        default=None,
        help=(
            "Label for this Gmail account (e.g. 'personal', 'oldwork'). Keeps "
            "analysis/ and output/ separate per account under analysis/<label>/ "
            "and output/<label>/. Omit for the single-account layout (analysis/, "
            "output/ directly)."
        ),
    )
    parser.add_argument(
        "--backend",
        choices=["agent", "openrouter"],
        default=None,
        help="Classification backend override",
    )
    parser.add_argument("--skip-split", action="store_true")
    parser.add_argument("--skip-dump", action="store_true")
    parser.add_argument("--skip-classify", action="store_true")
    parser.add_argument("--skip-apply", action="store_true")
    parser.add_argument(
        "--all-dates",
        action="store_true",
        help="Dump all threads (ignore search_window)",
    )
    args = parser.parse_args()

    analysis_dir = (ANALYSIS_BASE / args.account) if args.account else ANALYSIS_BASE
    output_dir = (OUTPUT_BASE / args.account) if args.account else OUTPUT_BASE

    if args.config:
        import participant_config as pc

        cfg = pc.load_participant_config(args.config)
    else:
        cfg = load_participant_config()

    participant = cfg["participant"]
    window_start, window_end = search_window(cfg)
    takeout_dir = resolve_takeout_dir(args.takeout_dir)
    mbox = args.mbox.resolve() if args.mbox else find_mbox(takeout_dir)
    mail_dir = mbox.parent
    emails_dir = mail_dir / f"{mbox.stem}_emails"

    print("Gmail recruiter extraction pipeline")
    print(f"  Participant: {participant['name']}")
    if args.account:
        print(f"  Account:     {args.account}")
    print(f"  Window:      {window_start} → {window_end}")
    print(f"  Takeout:     {takeout_dir}")
    print(f"  Input mbox:  {mbox}")
    print()

    py = sys.executable
    config_flag = ["--config", str(args.config)] if args.config else []

    if not args.skip_split:
        run_step([py, "split_mbox.py", str(mbox), "-o", str(emails_dir)])
    elif not emails_dir.is_dir():
        raise FileNotFoundError(f"--skip-split set but {emails_dir} does not exist")

    if not args.skip_dump:
        dump_cmd = [
            py,
            str(SCRIPTS / "dump_threads.py"),
            str(takeout_dir),
            "--emails-dir",
            str(emails_dir),
            "--out-dir",
            str(analysis_dir),
            *config_flag,
        ]
        if args.all_dates:
            dump_cmd.append("--all-dates")
        run_step(dump_cmd)

    if not args.skip_classify:
        classify_cmd = [
            py,
            str(SCRIPTS / "classify_threads.py"),
            "--analysis-dir",
            str(analysis_dir),
            *config_flag,
        ]
        if args.account:
            classify_cmd.extend(["--account", args.account])
        if args.backend:
            classify_cmd.extend(["--backend", args.backend])
        run_step(classify_cmd)

    # Agent backend stops after printing instructions — no decisions yet
    decisions = analysis_dir / "decisions.jsonl"
    if args.skip_apply:
        print("\nSkipped apply.")
    elif not decisions.exists() or decisions.stat().st_size == 0:
        print(
            "\nNo decisions.jsonl yet — classify the threads in this session "
            "(see docs/CLASSIFICATION_CRITERIA.md), then run:\n"
            f"  {py} scripts/apply_decisions.py --emails-dir {emails_dir} "
            f"--analysis-dir {analysis_dir} --output-dir {output_dir}"
        )
    else:
        run_step(
            [
                py,
                str(SCRIPTS / "apply_decisions.py"),
                "--emails-dir",
                str(emails_dir),
                "--analysis-dir",
                str(analysis_dir),
                "--output-dir",
                str(output_dir),
                *config_flag,
            ]
        )
        # Optional consistency check against source mbox when outputs exist
        latest = output_dir / "latest"
        out_mbox = latest / "recruiter_conversations.mbox"
        out_report = latest / "recruiter_conversations_report.csv"
        if out_mbox.exists() and out_report.exists():
            run_step(
                [
                    py,
                    str(SCRIPTS / "validate_takeout.py"),
                    str(mbox),
                    str(out_mbox),
                    str(out_report),
                ]
            )
        print(f"\nOutputs: {latest}/ (symlink to latest run)")

    print("\nDone.")


if __name__ == "__main__":
    main()
