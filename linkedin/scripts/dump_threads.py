#!/usr/bin/env python3
"""Dump full LinkedIn conversation threads for LLM / Cursor classification."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

from common.classification.dump_format import DumpMessage, DumpThread, write_dump  # noqa: E402
from messages_io import (  # noqa: E402
    find_messages_csv,
    group_conversations,
    in_window,
    load_messages,
    other_party,
)
from participant_config import (  # noqa: E402
    load_participant_config,
    participant_display_name,
    search_window,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump LinkedIn threads for review")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "analysis",
    )
    args = parser.parse_args()

    cfg = load_participant_config(args.config)
    name = participant_display_name(cfg)
    start_s, end_s = search_window(cfg)
    start = datetime.strptime(start_s, "%Y-%m-%d")
    end = datetime.strptime(end_s, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    messages_path = find_messages_csv(args.data_dir)
    rows = load_messages(messages_path)
    convs = group_conversations(rows)

    in_win = {
        cid: msgs for cid, msgs in convs.items() if in_window(msgs, start, end)
    }
    ordered = sorted(in_win.items(), key=lambda kv: kv[1][0]["_dt"])

    dump_threads: list[DumpThread] = []
    meta = []
    for idx, (cid, msgs) in enumerate(ordered):
        party = other_party(msgs, name)
        messages = []
        for m in msgs:
            who = "PARTICIPANT" if name in (m.get("FROM") or "") else (m.get("FROM") or "")
            messages.append(
                DumpMessage(
                    when=m["_dt"],
                    who=who,
                    text=(m.get("CONTENT") or "").strip(),
                    subject=(m.get("SUBJECT") or "").strip(),
                )
            )
        dump_threads.append(
            DumpThread(
                index=idx,
                thread_id=cid,
                other_party=party,
                start=msgs[0]["_dt"].strftime("%Y-%m-%d"),
                end=msgs[-1]["_dt"].strftime("%Y-%m-%d"),
                message_count=len(msgs),
                messages=messages,
                label="CONV",
            )
        )
        meta.append(
            {
                "index": idx,
                "conversation_id": cid,
                "thread_id": cid,
                "other_party": party,
                "start": msgs[0]["_dt"].strftime("%Y-%m-%d"),
                "end": msgs[-1]["_dt"].strftime("%Y-%m-%d"),
                "message_count": len(msgs),
            }
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    dump_path = args.out_dir / "threads_dump.txt"
    json_path = args.out_dir / "threads.json"
    write_dump(dump_path, dump_threads)
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"messages.csv: {messages_path}")
    print(f"Total messages parsed: {len(rows)}")
    print(f"Conversations in window ({start_s} – {end_s}): {len(ordered)}")
    print(f"Wrote {dump_path}")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
