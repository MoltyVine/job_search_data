#!/usr/bin/env python3
"""Build an mbox of recruiter job-opportunity conversations."""

import argparse
import csv
import mailbox
from collections import defaultdict
from email import message_from_bytes
from pathlib import Path

from filters import (
    ATS_DOMAIN,
    decode_header_value,
    include_in_recruiter_thread,
    parse_from,
    seeds_recruiter_thread,
)


def thread_has_ats(items: list[dict]) -> bool:
    return any(ATS_DOMAIN.search(item["addr"]) for item in items)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory of .eml files from split_mbox.py",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output mbox (default: recruiter_conversations.mbox next to input)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional CSV report of inclusion decisions",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_path = (
        args.output.resolve()
        if args.output
        else input_dir.parent / "recruiter_conversations.mbox"
    )
    report_path = (
        args.report.resolve()
        if args.report
        else input_dir.parent / "recruiter_conversations_report.csv"
    )

    threads: dict[str, list[dict]] = defaultdict(list)
    for eml in sorted(input_dir.glob("*.eml")):
        msg = message_from_bytes(eml.read_bytes())
        display, addr = parse_from(msg)
        subject = decode_header_value(msg.get("Subject", ""))
        thread_id = msg.get("X-GM-THRID") or eml.name
        threads[thread_id].append(
            {
                "eml": eml,
                "msg": msg,
                "display": display,
                "addr": addr,
                "subject": subject,
            }
        )

    seeded_threads = {
        thread_id
        for thread_id, items in threads.items()
        if any(
            seeds_recruiter_thread(item["display"], item["addr"], item["msg"], item["subject"])
            for item in items
        )
    }

    included = []
    rows = []
    thread_kept_items: dict[str, list[dict]] = defaultdict(list)

    for thread_id, items in threads.items():
        in_thread = thread_id in seeded_threads
        for item in items:
            msg_keep = in_thread and include_in_recruiter_thread(
                item["display"], item["addr"], item["msg"], item["subject"]
            )
            if msg_keep:
                thread_kept_items[thread_id].append(item)

    for thread_id, items in threads.items():
        in_thread = thread_id in seeded_threads
        kept_items = thread_kept_items.get(thread_id, [])
        keep_thread = bool(kept_items) and (
            len(kept_items) >= 2 or thread_has_ats(kept_items)
        )
        kept_files = {item["eml"].name for item in kept_items} if keep_thread else set()

        for item in items:
            keep = item["eml"].name in kept_files
            rows.append(
                {
                    "file": item["eml"].name,
                    "thread_id": thread_id,
                    "thread_seeded": in_thread,
                    "thread_kept": keep_thread,
                    "kept": keep,
                    "from_display": item["display"],
                    "from_addr": item["addr"],
                    "subject": item["subject"],
                }
            )
            if keep:
                included.append(item)

    if output_path.exists():
        output_path.unlink()

    out = mailbox.mbox(str(output_path))
    out.lock()
    try:
        for item in sorted(included, key=lambda x: x["eml"].name):
            out.add(item["msg"])
    finally:
        out.flush()
        out.unlock()
        out.close()

    with report_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    kept_threads = len({r["thread_id"] for r in rows if r["thread_kept"]})

    print(f"Threads:        {len(threads)}")
    print(f"Seeded threads: {len(seeded_threads)}")
    print(f"Kept threads:   {kept_threads}")
    print(f"Messages kept:  {len(included)} / {len(rows)}")
    print(f"Output:         {output_path}")
    print(f"Report:         {report_path}")


if __name__ == "__main__":
    main()
