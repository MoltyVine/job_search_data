#!/usr/bin/env python3
"""Dump Gmail threads (from split .eml dir) for LLM / Cursor classification."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

GMAIL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = GMAIL_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(GMAIL_ROOT))

from common.classification.dump_format import DumpMessage, DumpThread, write_dump  # noqa: E402
from participant_config import load_participant_config, my_emails, search_window  # noqa: E402


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


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


def message_date(msg) -> datetime | None:
    raw = msg.get("Date")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except (TypeError, ValueError, IndexError):
        return None


def extract_body(msg) -> str:
    plain_parts: list[str] = []
    html_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            disp = str(part.get("Content-Disposition") or "").lower()
            if "attachment" in disp:
                continue
            try:
                payload = part.get_payload(decode=True)
            except Exception:  # noqa: BLE001
                continue
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            if ctype == "text/plain":
                plain_parts.append(text)
            elif ctype == "text/html":
                html_parts.append(text)
    else:
        try:
            payload = msg.get_payload(decode=True)
        except Exception:  # noqa: BLE001
            payload = None
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text = payload.decode(charset, errors="replace")
            ctype = (msg.get_content_type() or "").lower()
            if ctype == "text/html":
                html_parts.append(text)
            else:
                plain_parts.append(text)

    if plain_parts:
        return "\n".join(plain_parts)
    if html_parts:
        stripper = _HTMLStripper()
        stripper.feed("\n".join(html_parts))
        return stripper.get_text()
    return ""


def find_emails_dir(takeout_dir: Path) -> Path:
    """Prefer <label>_emails next to source mbox under takeout."""
    candidates = sorted(
        p for p in takeout_dir.rglob("*_emails") if p.is_dir() and not p.name.endswith("_filtered")
    )
    # Prefer dirs that look like split output (contain .eml)
    with_eml = [p for p in candidates if any(p.glob("*.eml"))]
    if len(with_eml) == 1:
        return with_eml[0]
    if len(with_eml) > 1:
        # Prefer non-output-ish names
        preferred = [p for p in with_eml if "recruiter" not in p.name.lower()]
        if len(preferred) == 1:
            return preferred[0]
        raise FileNotFoundError(
            "Multiple *_emails dirs found; pass --emails-dir:\n"
            + "\n".join(str(p) for p in with_eml)
        )
    raise FileNotFoundError(
        f"No *_emails directory with .eml under {takeout_dir}. Run split first."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "takeout_dir",
        type=Path,
        nargs="?",
        default=None,
        help="Takeout folder (used to locate *_emails). Optional if --emails-dir set.",
    )
    parser.add_argument("--emails-dir", type=Path, help="Directory of .eml files")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=GMAIL_ROOT / "analysis",
    )
    parser.add_argument(
        "--all-dates",
        action="store_true",
        help="Do not filter threads by search_window (dump everything in the eml dir)",
    )
    args = parser.parse_args()

    cfg = load_participant_config(args.config)
    mine = my_emails(cfg)
    start_s, end_s = search_window(cfg)
    start = datetime.strptime(start_s, "%Y-%m-%d")
    end = datetime.strptime(end_s, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    if args.emails_dir:
        emails_dir = args.emails_dir.resolve()
    elif args.takeout_dir:
        emails_dir = find_emails_dir(args.takeout_dir.resolve())
    else:
        raise SystemExit("Pass takeout_dir or --emails-dir")

    threads_raw: dict[str, list[dict]] = defaultdict(list)
    for eml in sorted(emails_dir.glob("*.eml")):
        msg = message_from_bytes(eml.read_bytes())
        display, addr = parse_from(msg)
        subject = decode_header_value(msg.get("Subject", ""))
        dt = message_date(msg)
        thread_id = msg.get("X-GM-THRID") or eml.stem
        body = extract_body(msg)
        threads_raw[thread_id].append(
            {
                "eml": eml,
                "msg": msg,
                "display": display,
                "addr": addr,
                "subject": subject,
                "dt": dt,
                "body": body,
                "is_mine": addr in mine,
            }
        )

    for items in threads_raw.values():
        items.sort(key=lambda x: x["dt"] or datetime.min)

    def in_window(items: list[dict]) -> bool:
        if args.all_dates:
            return True
        return any(it["dt"] and start <= it["dt"] <= end for it in items)

    ordered_ids = [
        tid
        for tid, items in sorted(
            threads_raw.items(),
            key=lambda kv: next((i["dt"] for i in kv[1] if i["dt"]), datetime.min),
        )
        if in_window(items)
    ]

    dump_threads: list[DumpThread] = []
    meta = []
    for idx, tid in enumerate(ordered_ids):
        items = threads_raw[tid]
        others = sorted(
            {
                (it["display"] or it["addr"] or "").strip()
                for it in items
                if not it["is_mine"] and (it["display"] or it["addr"])
            }
        )
        other_party = " / ".join(others) if others else ""
        dts = [it["dt"] for it in items if it["dt"]]
        start_d = dts[0].strftime("%Y-%m-%d") if dts else ""
        end_d = dts[-1].strftime("%Y-%m-%d") if dts else ""
        messages = []
        for it in items:
            who = "PARTICIPANT" if it["is_mine"] else (it["display"] or it["addr"] or "unknown")
            messages.append(
                DumpMessage(
                    when=it["dt"] or "",
                    who=who,
                    text=it["body"] or "",
                    subject=it["subject"] or "",
                )
            )
        dump_threads.append(
            DumpThread(
                index=idx,
                thread_id=tid,
                other_party=other_party,
                start=start_d,
                end=end_d,
                message_count=len(items),
                messages=messages,
                label="THREAD",
            )
        )
        meta.append(
            {
                "index": idx,
                "thread_id": tid,
                "other_party": other_party,
                "start": start_d,
                "end": end_d,
                "message_count": len(items),
                "eml_files": [it["eml"].name for it in items],
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    dump_path = args.out_dir / "threads_dump.txt"
    json_path = args.out_dir / "threads.json"
    write_dump(dump_path, dump_threads)
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Emails dir: {emails_dir}")
    print(f"Threads total: {len(threads_raw)}")
    if args.all_dates:
        print("Window filter: disabled (--all-dates)")
    else:
        print(f"Threads in window ({start_s} – {end_s}): {len(ordered_ids)}")
    print(f"Wrote {dump_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
