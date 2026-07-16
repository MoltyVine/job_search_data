#!/usr/bin/env python3
"""Validate takeout mbox and pipeline output."""

import csv
import mailbox
import sys
from collections import defaultdict
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 4:
        print("Usage: validate_takeout.py <source.mbox> <filtered.mbox> <report.csv>")
        sys.exit(1)

    source = Path(sys.argv[1])
    filtered = Path(sys.argv[2])
    report = Path(sys.argv[3])

    src = mailbox.mbox(str(source))
    filt = mailbox.mbox(str(filtered))
    rows = list(csv.DictReader(report.open(encoding="utf-8")))

    src_threads = {m.get("X-GM-THRID") for m in src}
    filt_threads = {m.get("X-GM-THRID") for m in filt}
    kept_threads = {r["thread_id"] for r in rows if r.get("thread_kept") == "True"}

    by_thread = defaultdict(int)
    for r in rows:
        if r.get("kept") == "True":
            by_thread[r["thread_id"]] += 1

    conv = sum(1 for n in by_thread.values() if n >= 2)

    print("=== Validation ===")
    print(f"Source messages:     {len(src)}")
    print(f"Source threads:      {len(src_threads)}")
    print(f"Filtered messages:   {len(filt)}")
    print(f"Filtered threads:    {len(filt_threads)}")
    print(f"Report kept threads: {len(kept_threads)}")
    print(f"Multi-msg threads:   {conv}")

    ok = (
        len(filt) == sum(1 for r in rows if r.get("kept") == "True")
        and len(filt_threads) == len(kept_threads)
    )
    if not ok:
        print("\nWARNING: mbox counts do not match report.csv")
        sys.exit(2)

    print("\nOK: output is consistent with report.")


if __name__ == "__main__":
    main()
