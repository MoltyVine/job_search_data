# LinkedIn Message Extraction

Extract recruiter / job-opportunity **LinkedIn message conversations** from a LinkedIn data export.

## Quick start

```bash
cp config/participant.example.yaml config/participant.yaml
# edit: participant.*, linkedin.display_name, classification.*

cd linkedin
pip install -r requirements.txt
python3 run_linkedin_pipeline.py
# --backend ollama|cursor
```

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
| `scripts/classify_threads.py` | Ollama or Cursor handoff |
| `scripts/apply_decisions.py` | Decisions → output CSVs/md |
