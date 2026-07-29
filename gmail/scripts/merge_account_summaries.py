#!/usr/bin/env python3
"""Merge recruiter_conversations_summary.csv across multiple Gmail accounts.

Run run_gmail_pipeline.py once per account with --account <label> first (see
gmail/README.md -> Multiple accounts). This finds every
output/<label>/latest/recruiter_conversations_summary.csv and concatenates
them into one CSV tagged with an Account column.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

GMAIL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = GMAIL_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))

from common.csv_safe import csv_safe_rows  # noqa: E402


def find_account_summaries(output_base: Path) -> list[tuple[str, Path]]:
    """Return (account_label, summary_path) for each output/<label>/latest/summary.csv."""
    if not output_base.is_dir():
        return []
    found = []
    for child in sorted(output_base.iterdir()):
        if not child.is_dir():
            continue
        summary = child / "latest" / "recruiter_conversations_summary.csv"
        if summary.exists():
            found.append((child.name, summary))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-base", type=Path, default=GMAIL_ROOT / "output")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Merged CSV path (default: <output-base>/all_accounts_summary.csv)",
    )
    args = parser.parse_args()

    accounts = find_account_summaries(args.output_base)
    if not accounts:
        raise SystemExit(
            f"No {args.output_base}/<account>/latest/recruiter_conversations_summary.csv "
            "found.\nRun run_gmail_pipeline.py with --account <label> for each Gmail "
            "account first."
        )

    fields = ["Account"]
    all_rows: list[dict] = []
    for label, summary_path in accounts:
        with summary_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for name in reader.fieldnames or []:
                if name not in fields:
                    fields.append(name)
            for row in reader:
                row["Account"] = label
                all_rows.append(row)

    out_path = args.out or (args.output_base / "all_accounts_summary.csv")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_safe_rows(all_rows))

    print(f"Accounts merged: {', '.join(label for label, _ in accounts)}")
    print(f"Rows: {len(all_rows)}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
