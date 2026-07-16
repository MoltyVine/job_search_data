#!/usr/bin/env python3
"""Apply LinkedIn classification decisions → filtered CSV + summary docs."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

LINKEDIN_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LINKEDIN_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(LINKEDIN_ROOT))

from common.classification.store import DecisionStore  # noqa: E402
from common.csv_safe import csv_safe_rows  # noqa: E402
from common.run_output import resolve_write_dir, snapshot_decisions  # noqa: E402
from messages_io import (  # noqa: E402
    COLUMNS,
    find_messages_csv,
    group_conversations,
    load_messages,
    window_messages,
)
from participant_config import (  # noqa: E402
    load_participant_config,
    participant_display_name,
    search_window,
    summary_window,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=LINKEDIN_ROOT / "data")
    parser.add_argument("--analysis-dir", type=Path, default=LINKEDIN_ROOT / "analysis")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=LINKEDIN_ROOT / "output",
        help="Output root (writes to runs/<timestamp>/ unless --in-place)",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write flat into --output-dir (skip runs/ + latest symlink)",
    )
    args = parser.parse_args()

    cfg = load_participant_config(args.config)
    name = participant_display_name(cfg)
    start_s, end_s = search_window(cfg)
    sum_start_s, sum_end_s = summary_window(cfg)
    start = datetime.strptime(start_s, "%Y-%m-%d")
    end = datetime.strptime(end_s, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    sum_start = datetime.strptime(sum_start_s, "%Y-%m-%d")
    sum_end = datetime.strptime(sum_end_s, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59
    )

    decisions_path = args.analysis_dir / "decisions.jsonl"
    store = DecisionStore(decisions_path)
    decisions = store.load()
    if not decisions:
        raise SystemExit(f"No decisions in {store.path}. Run classify_threads.py first.")

    messages_path = find_messages_csv(args.data_dir)
    rows = load_messages(messages_path)
    convs = group_conversations(rows)

    write_dir = resolve_write_dir(args.output_dir, in_place=args.in_place)
    snapshot_decisions(decisions_path, write_dir)

    filtered_path = write_dir / "recruiter_position_conversations_filtered.csv"
    summary_csv_path = write_dir / "recruiter_conversations_summary.csv"
    summary_md_path = write_dir / "recruiter_conversations_summary.md"

    filtered_fields = COLUMNS + ["COMPANY", "POSITION_TITLE", "RECRUITER_TYPE", "OTHER_PARTY"]
    filtered_rows: list[dict] = []
    summary_rows: list[dict] = []
    type_counts: Counter[str] = Counter()
    monthly: Counter[str] = Counter()

    for tid, decision in decisions.items():
        if not decision.include:
            continue
        msgs = convs.get(tid)
        if not msgs:
            # try prefix match if dump truncated ids historically
            matches = [c for c in convs if c.startswith(tid) or tid.startswith(c[:24])]
            msgs = convs[matches[0]] if len(matches) == 1 else None
        if not msgs:
            continue

        win_msgs = window_messages(msgs, start, end)
        if not win_msgs:
            continue

        from_part = sum(1 for m in win_msgs if name in (m.get("FROM") or ""))
        to_part = len(win_msgs) - from_part
        party = decision.other_party or ""
        company = decision.company or "Unspecified"
        position = decision.position_title or "Unspecified"
        rtype = decision.recruiter_type or "unknown"

        type_counts[rtype] += 1
        month_key = win_msgs[0]["_dt"].strftime("%Y-%m")
        monthly[month_key] += 1

        in_summary_window = any(sum_start <= m["_dt"] <= sum_end for m in win_msgs)
        if in_summary_window:
            summary_rows.append(
                {
                    "Company": company,
                    "Position Title": position,
                    "Recruiter/Contact": party,
                    "Type": rtype,
                    "Start Date": win_msgs[0]["_dt"].strftime("%Y-%m-%d"),
                    "End Date": win_msgs[-1]["_dt"].strftime("%Y-%m-%d"),
                    "# Msgs": len(win_msgs),
                    "From Participant": from_part,
                    "To Participant": to_part,
                    "Conversation ID": tid,
                }
            )

        for m in win_msgs:
            row = {col: m.get(col, "") for col in COLUMNS}
            row["COMPANY"] = company
            row["POSITION_TITLE"] = position
            row["RECRUITER_TYPE"] = rtype
            row["OTHER_PARTY"] = party
            filtered_rows.append(row)

    with filtered_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=filtered_fields)
        writer.writeheader()
        writer.writerows(csv_safe_rows(filtered_rows))

    summary_fields = [
        "Company",
        "Position Title",
        "Recruiter/Contact",
        "Type",
        "Start Date",
        "End Date",
        "# Msgs",
        "From Participant",
        "To Participant",
        "Conversation ID",
    ]
    with summary_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(csv_safe_rows(summary_rows))

    notable = [r for r in summary_rows if int(r["# Msgs"]) >= 6]
    lines = [
        "# Recruiter conversations summary (LinkedIn)",
        "",
        "Built from local LLM or Cursor decisions applied by `scripts/apply_decisions.py`.",
        "Criteria: [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md).",
        "",
        f"- Search window: {start_s} → {end_s}",
        f"- Summary window: {sum_start_s} → {sum_end_s}",
        f"- Included conversations (in summary window): {len(summary_rows)}",
        f"- Filtered in-window messages: {len(filtered_rows)}",
        "",
        "## Counts by recruiter type",
        "",
    ]
    for t, n in sorted(type_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{t}`: {n}")
    lines += ["", "## New conversations by month", ""]
    for month, n in sorted(monthly.items()):
        lines.append(f"- {month}: {n}")
    lines += ["", "## Conversations", "", "| Company | Position | Contact | Type | Start | Msgs |", "|---|---|---|---|---|---|"]
    for r in summary_rows:
        lines.append(
            f"| {r['Company']} | {r['Position Title']} | {r['Recruiter/Contact']} | "
            f"{r['Type']} | {r['Start Date']} | {r['# Msgs']} |"
        )
    if notable:
        lines += ["", "## Notable multi-message pipelines (≥6 msgs)", ""]
        for r in notable:
            lines.append(
                f"- {r['Company']} / {r['Position Title']} ({r['# Msgs']} msgs) — {r['Recruiter/Contact']}"
            )
    summary_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    latest = args.output_dir / "latest"
    print(f"Included decisions: {sum(1 for d in decisions.values() if d.include)}")
    print(f"Summary rows:       {len(summary_rows)}")
    print(f"Filtered messages:  {len(filtered_rows)}")
    print(f"Run dir:            {write_dir}")
    if not args.in_place and latest.exists():
        print(f"Latest:             {latest}")
    print(f"Wrote {filtered_path}")
    print(f"Wrote {summary_csv_path}")
    print(f"Wrote {summary_md_path}")


if __name__ == "__main__":
    main()
