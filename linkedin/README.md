# LinkedIn Message Extraction

Extract recruiter / job-opportunity **LinkedIn message conversations** from a LinkedIn data export.

## Quick start

Run from the repo root first (see root [README.md](../README.md) → Requirements) to build the pinned `.venv/`:

```bash
pyenv install -s "$(cat .python-version)"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp config/participant.example.yaml config/participant.yaml
# edit: participant.*, linkedin.display_name
```

Then, using that same venv:

```bash
cd linkedin
../.venv/bin/python3 run_linkedin_pipeline.py
```

## Classification backend

`agent` (default, in this session, no API key) or `openrouter` (opt-in, automated, needs `OPENROUTER_API_KEY`) — see root [README.md](../README.md) → Classification of conversations, or pass `--backend openrouter` / set `classification.backend` in `participant.yaml`.

## Full workflow

[docs/LINKEDIN_EXTRACTION_WORKFLOW.md](docs/LINKEDIN_EXTRACTION_WORKFLOW.md)

Guided path: skill **`job-search-extraction`**.

- Shared criteria: [../docs/CLASSIFICATION_CRITERIA.md](../docs/CLASSIFICATION_CRITERIA.md)
- LinkedIn notes: [docs/classification_criteria.md](docs/classification_criteria.md)

## Data layout

```
config/participant.yaml
linkedin/
  data/Complete_LinkedInDataExport_*/messages.csv   # gitignored
  analysis/   # dumps + decisions.jsonl (gitignored)
  output/     # latest/ + runs/<timestamp>/ deliverables (gitignored)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `run_linkedin_pipeline.py` | stats → dump → classify → apply |
| `scripts/stats.py` | Keyword pre-screen (sanity only) |
| `scripts/dump_threads.py` | Thread dump |
| `scripts/classify_threads.py` | Prints agent instructions, or classifies via `--backend openrouter` |
| `scripts/apply_decisions.py` | Decisions → output CSVs/md |
