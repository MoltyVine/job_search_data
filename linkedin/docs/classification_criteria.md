# Classification criteria — LinkedIn notes

Shared rules live in **[docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md)**.

## LinkedIn-specific notes

- Unit ID: `CONVERSATION ID` from `messages.csv`
- Dump includes **full thread history** for context; filtered deliverables keep **in-window** messages only
- Mechanical prep: `../.venv/bin/python3 run_linkedin_pipeline.py`
- Classification: the Claude Code agent, working through the thread dump directly (via the `job-search-extraction` skill, or on request)
- Decisions file: `linkedin/analysis/decisions.jsonl`
- Outputs: `linkedin/output/` via `scripts/apply_decisions.py`
