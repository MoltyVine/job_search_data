"""Classify dump threads with Ollama (shared helper used by source scripts)."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from .backend import make_ollama_client
from .dump_format import DumpThread, thread_text_for_llm
from .prompt import parse_model_json, system_prompt, user_prompt
from .schema import ThreadDecision
from .store import DecisionStore


def _progress_bar(done: int, total: int, width: int = 28) -> str:
    if total <= 0:
        return "[" + ("-" * width) + "]"
    filled = int(width * done / total)
    return "[" + ("#" * filled) + ("-" * (width - filled)) + "]"


def _format_eta(seconds: float) -> str:
    if seconds < 0 or seconds != seconds:  # NaN
        return "--:--"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _print_progress(
    *,
    done: int,
    total: int,
    flag: str,
    label: str,
    started: float,
    pending_at_start: int,
    completed_this_run: int,
) -> None:
    pct = (100.0 * done / total) if total else 100.0
    bar = _progress_bar(done, total)
    elapsed = time.monotonic() - started
    rate = completed_this_run / elapsed if elapsed > 0 and completed_this_run else 0.0
    remaining = max(pending_at_start - completed_this_run, 0)
    eta = (remaining / rate) if rate > 0 else float("nan")
    line = (
        f"\r{bar} {done}/{total} ({pct:5.1f}%) "
        f"ETA {_format_eta(eta)} | {flag}: {label[:48]}"
    )
    # Pad to clear leftover chars from longer previous labels
    sys.stdout.write(line.ljust(120))
    sys.stdout.flush()


def classify_threads_ollama(
    threads: list[DumpThread],
    *,
    source: str,
    store_path: Path,
    config: dict | None = None,
    max_chars_per_msg: int = 1200,
) -> dict[str, ThreadDecision]:
    client = make_ollama_client(config)
    store = DecisionStore(store_path)
    existing = store.load()
    system = system_prompt()

    total = len(threads)
    already = sum(1 for t in threads if t.thread_id in existing)
    pending = [t for t in threads if t.thread_id not in existing]

    print(f"Ollama model: {client.model}", flush=True)
    print(
        f"Threads: {total} total | {already} already decided | {len(pending)} to classify",
        flush=True,
    )
    if not pending:
        included = sum(1 for d in existing.values() if d.include)
        print(f"Nothing new to do. Included {included} / {len(existing)}.", flush=True)
        return existing

    started = time.monotonic()
    completed_this_run = 0

    for thread in pending:
        text = thread_text_for_llm(thread, max_chars_per_msg=max_chars_per_msg)
        user = user_prompt(text, thread_id=thread.thread_id, source=source)
        try:
            raw = client.chat(system, user)
            decision = parse_model_json(raw, thread_id=thread.thread_id, source=source)
            if decision.reason.startswith("parse_error"):
                raw = client.chat(system, user + "\n\nReturn ONLY valid JSON with include true or false.")
                decision = parse_model_json(raw, thread_id=thread.thread_id, source=source)
            # Empty reason often means truncated JSON from oversized prompts —
            # retry once on a shorter head+tail sample.
            if not decision.reason.strip() and thread.message_count >= 8:
                short = thread_text_for_llm(
                    thread, max_chars_per_msg=400, max_messages=8, max_total_chars=5000
                )
                raw = client.chat(
                    system,
                    user_prompt(short, thread_id=thread.thread_id, source=source)
                    + "\n\nReturn ONLY valid JSON. include=true only for real-person recruiting.",
                )
                decision = parse_model_json(raw, thread_id=thread.thread_id, source=source)
            if decision.reason.startswith("parse_error"):
                # Minimal retry — force the boolean field
                raw = client.chat(
                    "Reply with ONLY JSON: "
                    '{"include":true|false,"reason":"...","company":"","position_title":"",'
                    '"recruiter_type":"unknown","other_party":""}',
                    user
                    + "\n\nIs this a real person recruiting the participant for a specific role? "
                    "include=true only if yes.",
                )
                decision = parse_model_json(raw, thread_id=thread.thread_id, source=source)
        except Exception as exc:  # noqa: BLE001 — keep pipeline moving
            decision = ThreadDecision.parse_error_exclude(
                thread.thread_id, source, str(exc)[:200]
            )

        if not decision.other_party and thread.other_party:
            decision.other_party = thread.other_party
        store.append(decision)
        existing[thread.thread_id] = decision
        completed_this_run += 1

        done = already + completed_this_run
        flag = "INCLUDE" if decision.include else "exclude"
        label = thread.other_party or thread.thread_id[:24]
        _print_progress(
            done=done,
            total=total,
            flag=flag,
            label=label,
            started=started,
            pending_at_start=len(pending),
            completed_this_run=completed_this_run,
        )

    # Finish the progress line, then summary
    sys.stdout.write("\n")
    sys.stdout.flush()
    elapsed = time.monotonic() - started
    included = sum(1 for d in existing.values() if d.include)
    print(
        f"Done in {_format_eta(elapsed)}. "
        f"Included {included} / {len(existing)} threads with decisions.",
        flush=True,
    )
    return existing
