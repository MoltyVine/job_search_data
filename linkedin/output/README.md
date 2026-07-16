# LinkedIn extraction deliverables

Written by `scripts/apply_decisions.py` from `analysis/decisions.jsonl`. Not committed — personal message content.

## Layout

```
linkedin/output/
  README.md
  latest -> runs/<YYYYMMDD-HHMMSS>/
  runs/
    <YYYYMMDD-HHMMSS>/
      recruiter_conversations_summary.csv
      recruiter_conversations_summary.md
      recruiter_position_conversations_filtered.csv
      decisions.jsonl
```

Each apply creates a new `runs/<timestamp>/` folder and updates the `latest` symlink. Previous runs are kept for comparison. Use `--in-place` to write flat into the output root (debug only).

## Files (under `latest/` or a run folder)

| File | Purpose |
|------|---------|
| `recruiter_conversations_summary.csv` | **Primary index** — one row per kept conversation: company, position, recruiter/contact, type, date span, message counts (from/to participant), conversation ID. Best starting point for review. |
| `recruiter_conversations_summary.md` | Same summary as the CSV, in readable markdown (tables + short notes). |
| `recruiter_position_conversations_filtered.csv` | Message-level export for kept conversations only (original LinkedIn columns plus company, position, recruiter type, other party). Use when you need full InMail text. |
| `decisions.jsonl` | Snapshot of classification decisions used for this run. |

Day-to-day: open `linkedin/output/latest/recruiter_conversations_summary.csv`.

Classification rules: [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md).
