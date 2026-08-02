#!/usr/bin/env python3
"""Classify Gmail threads: agent instructions (default) or the openrouter backend."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GMAIL_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = GMAIL_ROOT.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(GMAIL_ROOT))

from common.classification.backend import make_openrouter_client, resolve_backend  # noqa: E402
from common.classification.classify import classify_threads_openrouter  # noqa: E402
from common.classification.dump_format import DumpMessage, DumpThread  # noqa: E402
from common.participant_config import (  # noqa: E402
    classification_settings,
    load_participant_config,
)

_BLOCK = re.compile(
    r"===== THREAD #(\d+) \| id=(.+?) =====\n"
    r"OTHER PARTY: (.*)\n"
    r"SPAN: (\S+) to (\S+) \| (\d+) msgs\n"
    r"([\s\S]*?)(?=\n===== |\Z)"
)


def load_threads_from_dump(dump_path: Path, meta_path: Path) -> list[DumpThread]:
    meta = {m["thread_id"]: m for m in json.loads(meta_path.read_text(encoding="utf-8"))}
    text = dump_path.read_text(encoding="utf-8")
    threads: list[DumpThread] = []
    for match in _BLOCK.finditer(text):
        idx = int(match.group(1))
        tid = match.group(2).strip()
        other = match.group(3).strip()
        start = match.group(4)
        end = match.group(5)
        count = int(match.group(6))
        body = match.group(7)
        messages: list[DumpMessage] = []
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("["):
                continue
            # [YYYY-MM-DD] WHO: ...
            try:
                date_part, rest = line[1:].split("]", 1)
                who, content = rest.split(":", 1)
            except ValueError:
                continue
            subject = ""
            content = content.strip()
            if content.startswith("(subj:"):
                subj_end = content.find(")")
                if subj_end != -1:
                    subject = content[len("(subj:") : subj_end].strip()
                    content = content[subj_end + 1 :].strip()
            messages.append(
                DumpMessage(when=date_part.strip(), who=who.strip(), text=content, subject=subject)
            )
        info = meta.get(tid, {})
        threads.append(
            DumpThread(
                index=idx,
                thread_id=tid,
                other_party=other or info.get("other_party", ""),
                start=start,
                end=end,
                message_count=count,
                messages=messages,
                label="THREAD",
            )
        )
    threads.sort(key=lambda t: t.index)
    return threads


def print_agent_instructions(analysis_dir: Path, output_dir: Path) -> None:
    print(
        "\n=== Classification needed (Gmail) ===\n"
        "Read every '===== THREAD #... =====' block in:\n"
        f"  {analysis_dir / 'threads_dump.txt'}\n"
        "Apply docs/CLASSIFICATION_CRITERIA.md (real person + one or more job "
        "opportunities; unsure -> exclude).\n"
        "Write one JSON object per thread to:\n"
        f"  {analysis_dir / 'decisions.jsonl'}\n"
        "Keys: thread_id, include, reason, company, position_title, "
        'recruiter_type, other_party, source="gmail".\n'
        "Then run (use the --emails-dir path the pipeline printed):\n"
        f"  cd gmail && {sys.executable} scripts/apply_decisions.py --emails-dir <path> "
        f"--analysis-dir {analysis_dir} --output-dir {output_dir}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--analysis-dir", type=Path, default=GMAIL_ROOT / "analysis")
    parser.add_argument(
        "--account",
        default=None,
        help="Account label, for the printed apply_decisions.py hint only (see --account on run_gmail_pipeline.py)",
    )
    parser.add_argument(
        "--backend",
        choices=["agent", "openrouter"],
        default=None,
        help="Override classification.backend from participant.yaml",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Parallel OpenRouter requests (openrouter backend only)",
    )
    args = parser.parse_args()

    analysis_dir = args.analysis_dir
    dump_path = analysis_dir / "threads_dump.txt"
    meta_path = analysis_dir / "threads.json"
    if not dump_path.exists() or not meta_path.exists():
        raise SystemExit(f"Missing dump files in {analysis_dir}. Run dump_threads.py first.")

    cfg = load_participant_config(args.config)
    backend = resolve_backend(args.backend, cfg)
    if backend == "agent":
        output_dir = (GMAIL_ROOT / "output" / args.account) if args.account else (GMAIL_ROOT / "output")
        print_agent_instructions(analysis_dir, output_dir)
        return

    settings = classification_settings(cfg)
    max_chars = int(settings.get("max_chars_per_thread_msg") or 1200)
    threads = load_threads_from_dump(dump_path, meta_path)
    client = make_openrouter_client(cfg)
    classify_threads_openrouter(
        threads,
        source="gmail",
        store_path=analysis_dir / "decisions.jsonl",
        client=client,
        max_chars_per_msg=max_chars,
        concurrency=args.concurrency,
    )


if __name__ == "__main__":
    main()
