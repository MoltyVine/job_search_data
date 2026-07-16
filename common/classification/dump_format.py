"""Shared human-readable thread dump formatting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable


@dataclass
class DumpMessage:
    when: datetime | date | str
    who: str
    text: str
    subject: str = ""


@dataclass
class DumpThread:
    index: int
    thread_id: str
    other_party: str
    start: str
    end: str
    message_count: int
    messages: list[DumpMessage]
    label: str = "CONV"  # CONV (linkedin) or THREAD (gmail)


def format_thread_block(thread: DumpThread, *, max_chars_per_msg: int = 800) -> str:
    lines = [
        f"\n===== {thread.label} #{thread.index} | id={thread.thread_id} =====",
        f"OTHER PARTY: {thread.other_party}",
        f"SPAN: {thread.start} to {thread.end} | {thread.message_count} msgs",
    ]
    for m in thread.messages:
        if isinstance(m.when, datetime):
            when_s = m.when.strftime("%Y-%m-%d")
        elif isinstance(m.when, date):
            when_s = m.when.isoformat()
        else:
            when_s = str(m.when)
        content = (m.text or "").replace("\r", " ").replace("\n", " ").strip()
        if max_chars_per_msg and len(content) > max_chars_per_msg:
            content = content[:max_chars_per_msg]
        line = f"  [{when_s}] {m.who}: "
        if m.subject:
            line += f"(subj: {m.subject}) "
        line += content
        lines.append(line)
    return "\n".join(lines) + "\n"


def write_dump(
    path,
    threads: Iterable[DumpThread],
    *,
    max_chars_per_msg: int = 800,
) -> None:
    with path.open("w", encoding="utf-8") as f:
        for thread in threads:
            f.write(format_thread_block(thread, max_chars_per_msg=max_chars_per_msg))


def thread_text_for_llm(
    thread: DumpThread,
    *,
    max_chars_per_msg: int = 600,
    max_messages: int = 12,
    max_total_chars: int = 9000,
) -> str:
    """Compact text for the model.

    Long threads are head+tail sampled so interview loops still fit context
    and small models are less likely to return empty/truncated JSON.
    """
    msgs = list(thread.messages)
    if len(msgs) > max_messages:
        keep_head = max_messages // 2
        keep_tail = max_messages - keep_head
        omitted = len(msgs) - max_messages
        sampled = (
            msgs[:keep_head]
            + [
                DumpMessage(
                    when="",
                    who="…",
                    text=f"[{omitted} earlier/middle messages omitted for length]",
                    subject="",
                )
            ]
            + msgs[-keep_tail:]
        )
        slim = DumpThread(
            index=thread.index,
            thread_id=thread.thread_id,
            other_party=thread.other_party,
            start=thread.start,
            end=thread.end,
            message_count=thread.message_count,
            messages=sampled,
            label=thread.label,
        )
    else:
        slim = thread

    text = format_thread_block(slim, max_chars_per_msg=max_chars_per_msg)
    if len(text) > max_total_chars:
        text = text[: max_total_chars - 80] + "\n…[truncated for model context]\n"
    return text
