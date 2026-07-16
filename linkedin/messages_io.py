"""Shared helpers for reading LinkedIn messages.csv exports."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

csv.field_size_limit(10_000_000)

COLUMNS = [
    "CONVERSATION ID",
    "CONVERSATION TITLE",
    "FROM",
    "SENDER PROFILE URL",
    "TO",
    "RECIPIENT PROFILE URLS",
    "DATE",
    "SUBJECT",
    "CONTENT",
    "FOLDER",
    "ATTACHMENTS",
]


def parse_date(date_str: str) -> datetime | None:
    date_str = (date_str or "").strip()
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def load_messages(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            dt = parse_date(row.get("DATE", ""))
            if dt is None:
                continue
            row["_dt"] = dt
            rows.append(row)
    return rows


def group_conversations(rows: list[dict]) -> dict[str, list[dict]]:
    convs: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        convs[row["CONVERSATION ID"]].append(row)
    for cid in convs:
        convs[cid].sort(key=lambda r: r["_dt"])
    return convs


def other_party(msgs: list[dict], participant_name: str) -> str:
    others: set[str] = set()
    for m in msgs:
        frm = m.get("FROM", "")
        to = m.get("TO", "")
        if participant_name in frm:
            if to:
                others.add(to)
        else:
            if frm:
                others.add(frm)
    return " / ".join(sorted(others))


def in_window(msgs: list[dict], start: datetime, end: datetime) -> bool:
    return any(start <= m["_dt"] <= end for m in msgs)


def window_messages(msgs: list[dict], start: datetime, end: datetime) -> list[dict]:
    return [m for m in msgs if start <= m["_dt"] <= end]


def find_messages_csv(data_dir: Path) -> Path:
    candidates = sorted(data_dir.glob("**/messages.csv"))
    if not candidates:
        raise FileNotFoundError(f"No messages.csv found under {data_dir}")
    if len(candidates) > 1:
        # prefer Complete_LinkedInDataExport_* if multiple
        export = [p for p in candidates if "Complete_LinkedInDataExport" in str(p)]
        if export:
            return export[0]
    return candidates[0]
