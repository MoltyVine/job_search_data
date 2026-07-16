# Gmail Job-Search Extraction

Extract recruiter / job-opportunity **email conversations** from a Google Takeout Mail export.

## Quick start

```bash
cp config/participant.example.yaml config/participant.yaml
# edit: participant.*, gmail.my_emails, classification.*

cd gmail
pip install -r requirements.txt
# put unzipped takeout under takeout_extracts/, then:
python3 run_gmail_pipeline.py
# --backend ollama|cursor  --all-dates
```

**Outputs** under `gmail/output/latest/` (each run also kept in `gmail/output/runs/<timestamp>/`):

- `recruiter_conversations.mbox`
- `recruiter_conversations_report.csv`
- `recruiter_conversations_summary.csv`

## Full workflow

[docs/GMAIL_EXTRACTION_WORKFLOW.md](docs/GMAIL_EXTRACTION_WORKFLOW.md)

Guided path: skill **`job-search-extraction`**. Shared criteria: [../docs/CLASSIFICATION_CRITERIA.md](../docs/CLASSIFICATION_CRITERIA.md).

## Scripts

| Script | Purpose |
|--------|---------|
| `run_gmail_pipeline.py` | Orchestrator: split → dump → classify → apply |
| `split_mbox.py` | `.mbox` → one `.eml` per message |
| `scripts/dump_threads.py` | Thread dump for classification |
| `scripts/classify_threads.py` | Ollama or Cursor handoff |
| `scripts/apply_decisions.py` | Decisions → mbox + CSVs |
| `scripts/validate_takeout.py` | Output consistency check |

## Data

Place Takeout folders in [`takeout_extracts/`](takeout_extracts/README.md). Analysis/output are gitignored.
