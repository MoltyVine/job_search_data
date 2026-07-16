#!/usr/bin/env python3
"""Apply Gmail classification decisions → mbox + report under gmail/output/."""

from __future__ import annotations

import argparse
import csv
import mailbox
import sys
from collections import defaultdict
from email import message_from_bytes
from email.header import decode_header
from email.utils import getaddresses
from pathlib import Path

GMAIL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = GMAIL_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(GMAIL_ROOT))

from common.classification.store import DecisionStore  # noqa: E402
from common.csv_safe import csv_safe_rows  # noqa: E402
from common.run_output import resolve_write_dir, snapshot_decisions  # noqa: E402
from participant_config import load_participant_config  # noqa: E402


def decode_header_value(raw: str) -> str:
    parts = []
    for fragment, charset in decode_header(raw or ""):
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(fragment)
    return "".join(parts)


def parse_from(msg) -> tuple[str, str]:
    addrs = getaddresses([msg.get("From", "")])
    if not addrs:
        return "", ""
    display, addr = addrs[0]
    return decode_header_value(display), (addr or "").lower()


def find_emails_dir(takeout_dir: Path | None, explicit: Path | None) -> Path:
    if explicit:
        return explicit.resolve()
    if not takeout_dir:
        raise SystemExit("Pass --takeout-dir or --emails-dir")
    candidates = [
        p
        for p in takeout_dir.resolve().rglob("*_emails")
        if p.is_dir() and any(p.glob("*.eml")) and "recruiter" not in p.name.lower()
    ]
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise FileNotFoundError(f"No *_emails dir under {takeout_dir}")
    raise FileNotFoundError(
        "Multiple *_emails dirs; pass --emails-dir:\n" + "\n".join(str(p) for p in candidates)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--analysis-dir", type=Path, default=GMAIL_ROOT / "analysis")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=GMAIL_ROOT / "output",
        help="Output root (writes to runs/<timestamp>/ unless --in-place)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write flat into --output-dir (skip runs/ + latest symlink)",
    )
    parser.add_argument("--takeout-dir", type=Path, default=None)
    parser.add_argument("--emails-dir", type=Path, default=None)
    args = parser.parse_args()

    load_participant_config(args.config)  # validate config exists
    decisions_path = args.analysis_dir / "decisions.jsonl"
    store = DecisionStore(decisions_path)
    decisions = store.load()
    if not decisions:
        raise SystemExit(f"No decisions in {store.path}. Run classify_threads.py first.")

    emails_dir = find_emails_dir(args.takeout_dir, args.emails_dir)

    threads: dict[str, list[dict]] = defaultdict(list)
    for eml in sorted(emails_dir.glob("*.eml")):
        msg = message_from_bytes(eml.read_bytes())
        display, addr = parse_from(msg)
        subject = decode_header_value(msg.get("Subject", ""))
        thread_id = msg.get("X-GM-THRID") or eml.stem
        threads[thread_id].append(
            {
                "eml": eml,
                "msg": msg,
                "display": display,
                "addr": addr,
                "subject": subject,
            }
        )

    included_msgs: list[dict] = []
    rows: list[dict] = []
    for thread_id, items in threads.items():
        decision = decisions.get(thread_id)
        keep_thread = bool(decision and decision.include)
        for item in items:
            rows.append(
                {
                    "file": item["eml"].name,
                    "thread_id": thread_id,
                    "thread_kept": keep_thread,
                    "kept": keep_thread,
                    "from_display": item["display"],
                    "from_addr": item["addr"],
                    "subject": item["subject"],
                    "company": decision.company if decision else "",
                    "position_title": decision.position_title if decision else "",
                    "recruiter_type": decision.recruiter_type if decision else "",
                    "reason": decision.reason if decision else "no_decision",
                    "other_party": decision.other_party if decision else "",
                }
            )
            if keep_thread:
                included_msgs.append(item)

    write_dir = resolve_write_dir(args.output_dir, in_place=args.in_place)
    snapshot_decisions(decisions_path, write_dir)

    output_mbox = write_dir / "recruiter_conversations.mbox"
    report_csv = write_dir / "recruiter_conversations_report.csv"
    summary_csv = write_dir / "recruiter_conversations_summary.csv"

    if output_mbox.exists():
        output_mbox.unlink()
    out = mailbox.mbox(str(output_mbox))
    out.lock()
    try:
        for item in sorted(included_msgs, key=lambda x: x["eml"].name):
            out.add(item["msg"])
    finally:
        out.flush()
        out.unlock()
        out.close()

    with report_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "file", "thread_id", "thread_kept", "kept", "from_display", "from_addr",
            "subject", "company", "position_title", "recruiter_type", "reason", "other_party",
        ])
        writer.writeheader()
        writer.writerows(csv_safe_rows(rows))

    summary_rows = []
    for tid, decision in decisions.items():
        if not decision.include:
            continue
        items = threads.get(tid, [])
        summary_rows.append(
            {
                "Company": decision.company,
                "Position Title": decision.position_title,
                "Recruiter/Contact": decision.other_party,
                "Type": decision.recruiter_type,
                "# Msgs": len(items),
                "Thread ID": tid,
                "Reason": decision.reason,
            }
        )
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "Company",
            "Position Title",
            "Recruiter/Contact",
            "Type",
            "# Msgs",
            "Thread ID",
            "Reason",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(csv_safe_rows(summary_rows))

    kept_threads = sum(1 for d in decisions.values() if d.include)
    latest = args.output_dir / "latest"
    print(f"Decisions:     {len(decisions)}")
    print(f"Kept threads:  {kept_threads}")
    print(f"Messages kept: {len(included_msgs)}")
    print(f"Run dir:       {write_dir}")
    if not args.in_place and latest.exists():
        print(f"Latest:        {latest}")
    print(f"Mbox:          {output_mbox}")
    print(f"Report:        {report_csv}")
    print(f"Summary:       {summary_csv}")


if __name__ == "__main__":
    main()
