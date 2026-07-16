#!/usr/bin/env python3
"""Quick statistics on LinkedIn messages.csv for a date window."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from messages_io import find_messages_csv, group_conversations, in_window, load_messages, window_messages
from participant_config import load_participant_config, participant_display_name, search_window

RECRUITER_KEYWORDS = [
    "recruit", "hiring", "opportunity", "role at", "position at", "job opening",
    "talent", "staffing", "headhunt", "calendly", "interview", "resume",
    "ats", "candidate", "open role", "open position", "job search",
    "talent acquisition", "talent partner", "recruiting", "placement",
    "career opportunit", "job description", "i am a recruiter", "i'm a recruiter",
    "recruiter for", "recruiter with", "recruiter at", "hiring for",
    "looking for someone", "exciting opportunity", "reach out about",
]


def keyword_score(msgs: list[dict]) -> int:
    score = 0
    for m in msgs:
        text = ((m.get("CONTENT") or "") + " " + (m.get("SUBJECT") or "")).lower()
        for kw in RECRUITER_KEYWORDS:
            if kw in text:
                score += 1
    return score


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn messages window stats")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args()

    cfg = load_participant_config(args.config)
    name = participant_display_name(cfg)
    start_s, end_s = search_window(cfg)
    start = datetime.strptime(start_s, "%Y-%m-%d")
    end = datetime.strptime(end_s, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    path = find_messages_csv(args.data_dir)
    rows = load_messages(path)
    convs = group_conversations(rows)

    in_win = {cid: msgs for cid, msgs in convs.items() if in_window(msgs, start, end)}
    win_msgs = []
    for cid, msgs in in_win.items():
        win_msgs.extend(window_messages(msgs, start, end))

    monthly = Counter(m["_dt"].strftime("%Y-%m") for m in win_msgs)
    likely = sum(1 for msgs in in_win.values() if keyword_score(msgs) >= 2)
    from_participant = sum(1 for m in win_msgs if name in (m.get("FROM") or ""))

    print(f"Source: {path}")
    print(f"Window: {start_s} – {end_s}")
    print(f"Participant display name: {name}")
    print()
    print(f"Total messages in file: {len(rows)}")
    if rows:
        print(f"File date range: {min(r['_dt'] for r in rows).date()} – {max(r['_dt'] for r in rows).date()}")
    print(f"Conversations with activity in window: {len(in_win)}")
    print(f"Messages in window: {len(win_msgs)}")
    print(f"  outbound from participant: {from_participant}")
    print(f"  inbound to participant: {len(win_msgs) - from_participant}")
    print(f"Conversations with keyword score >= 2 (rough pre-screen): {likely}")
    print()
    print("Messages by month (in window):")
    for month in sorted(monthly):
        print(f"  {month}: {monthly[month]}")


if __name__ == "__main__":
    main()
