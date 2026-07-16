#!/usr/bin/env python3
"""Split an mbox file into one .eml file per message."""

import argparse
import mailbox
import re
from email.utils import parsedate_to_datetime
from pathlib import Path


def slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_-]+", "-", text.strip())
    return (text[:max_len].rstrip("-") or "no-subject").lower()


def decode_subject(msg) -> str:
    from email.header import decode_header

    raw = msg.get("Subject", "") or ""
    parts = []
    for fragment, charset in decode_header(raw):
        if isinstance(fragment, bytes):
            parts.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(fragment)
    return "".join(parts) or "no-subject"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mbox_path", type=Path)
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for individual .eml files (default: <mbox_stem>_emails/)",
    )
    args = parser.parse_args()

    mbox_path = args.mbox_path.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else mbox_path.parent / f"{mbox_path.stem}_emails"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    mbox = mailbox.mbox(mbox_path)
    total = len(mbox)
    print(f"Splitting {total} messages from {mbox_path.name} -> {output_dir}")

    for i, msg in enumerate(mbox):
        subject = decode_subject(msg)
        slug = slugify(subject)
        date = msg.get("Date")
        try:
            dt = parsedate_to_datetime(date) if date else None
            date_prefix = dt.strftime("%Y%m%d") if dt else "nodate"
        except (TypeError, ValueError, OverflowError):
            date_prefix = "nodate"

        filename = f"{i:04d}_{date_prefix}_{slug}.eml"
        out_path = output_dir / filename
        with out_path.open("wb") as f:
            f.write(msg.as_bytes())

    print(f"Wrote {total} files to {output_dir}")


if __name__ == "__main__":
    main()
