# Gmail Job-Search Extraction

Extract recruiter / job-opportunity **email conversations** from a Google Takeout Mail export.

## Quick start

Run from the repo root first (see root [README.md](../README.md) → Requirements) to build the pinned `.venv/`:

```bash
pyenv install -s "$(cat .python-version)"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp config/participant.example.yaml config/participant.yaml
# edit: participant.*, gmail.my_emails
```

Then, using that same venv:

```bash
cd gmail
# put unzipped takeout under takeout_extracts/, then:
../.venv/bin/python3 run_gmail_pipeline.py
# --all-dates
```

**Outputs** under `gmail/output/latest/` (each run also kept in `gmail/output/runs/<timestamp>/`):

- `recruiter_conversations.mbox`
- `recruiter_conversations_report.csv`
- `recruiter_conversations_summary.csv`

## Multiple accounts

Google Takeout exports one account at a time, so process each Gmail account as its own run, tagged with `--account <label>`:

```bash
../.venv/bin/python3 run_gmail_pipeline.py takeout_extracts/takeout-personal/ --account personal
../.venv/bin/python3 run_gmail_pipeline.py takeout_extracts/takeout-oldwork/ --account oldwork
```

This keeps `analysis/<label>/` and `output/<label>/` separate per account instead of the second run overwriting the first. `gmail.my_emails` in `participant.yaml` is one shared list across every account. Once every account has a run:

```bash
../.venv/bin/python3 scripts/merge_account_summaries.py
```

writes `gmail/output/all_accounts_summary.csv` combining every account's summary rows, tagged with an `Account` column.

## Classification backend

`agent` (default, in this session, no API key) or `openrouter` (opt-in, automated, needs `OPENROUTER_API_KEY`) — see root [README.md](../README.md) → Classification of conversations, or pass `--backend openrouter` / set `classification.backend` in `participant.yaml`.

## Full workflow

[docs/GMAIL_EXTRACTION_WORKFLOW.md](docs/GMAIL_EXTRACTION_WORKFLOW.md)

Guided path: skill **`job-search-extraction`**. Shared criteria: [../docs/CLASSIFICATION_CRITERIA.md](../docs/CLASSIFICATION_CRITERIA.md).

## Scripts

| Script | Purpose |
|--------|---------|
| `run_gmail_pipeline.py` | Orchestrator: split → dump → classify → apply |
| `split_mbox.py` | `.mbox` → one `.eml` per message |
| `scripts/dump_threads.py` | Thread dump for classification |
| `scripts/classify_threads.py` | Prints agent instructions, or classifies via `--backend openrouter` |
| `scripts/apply_decisions.py` | Decisions → mbox + CSVs |
| `scripts/validate_takeout.py` | Output consistency check |
| `scripts/merge_account_summaries.py` | Combine multiple accounts' summary CSVs |

## Data

Place Takeout folders in [`takeout_extracts/`](takeout_extracts/README.md). Analysis/output are gitignored.
