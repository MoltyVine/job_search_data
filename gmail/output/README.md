# Gmail extraction deliverables

Written by `scripts/apply_decisions.py` from `analysis/decisions.jsonl`. Not committed — personal email content.

## Layout

```
gmail/output/
  README.md
  latest -> runs/<YYYYMMDD-HHMMSS>/
  runs/
    <YYYYMMDD-HHMMSS>/
      recruiter_conversations_summary.csv
      recruiter_conversations.mbox
      recruiter_conversations_report.csv
      decisions.jsonl
```

Each apply creates a new `runs/<timestamp>/` folder and updates the `latest` symlink. Previous runs are kept for comparison. Use `--in-place` to write flat into the output root (debug only).

## Files (under `latest/` or a run folder)

| File | Purpose |
|------|---------|
| `recruiter_conversations_summary.csv` | **Primary index** — one row per kept thread: company, position, recruiter/contact, type, message count, thread ID, reason. Best starting point for review. |
| `recruiter_conversations.mbox` | Full email bodies for every kept thread (open in a mail client or process with mailbox tools). |
| `recruiter_conversations_report.csv` | Per-message audit of the labeled Takeout set: which messages/threads were kept, plus classification fields for debugging false positives/negatives. |
| `decisions.jsonl` | Snapshot of classification decisions used for this run. |

Day-to-day: open `gmail/output/latest/recruiter_conversations_summary.csv`.

Classification rules: [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md).
