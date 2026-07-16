# Classification criteria — LinkedIn notes

Shared rules live in **[docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md)**.

## LinkedIn-specific notes

- Unit ID: `CONVERSATION ID` from `messages.csv`
- Dump includes **full thread history** for context; filtered deliverables keep **in-window** messages only
- Mechanical prep: `python3 run_linkedin_pipeline.py`
- Classification: local Ollama (default when available) or Cursor agent handoff via skill `job-search-extraction`
- Decisions file: `linkedin/analysis/decisions.jsonl`
- Outputs: `linkedin/output/` via `scripts/apply_decisions.py`
