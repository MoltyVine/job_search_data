# Job Search Evidence Extraction

Extract **recruiter / job-opportunity conversations** from Gmail and LinkedIn.

## Start here (recommended)

1. Clone this repo and open it in Cursor.
2. Invoke the **`job-search-extraction`** skill (e.g. “Use job-search-extraction to walk me through setup”).

The skill interviews you for dates and identity, writes `config/participant.yaml`, guides Gmail labeling / Takeout and LinkedIn export, runs the pipelines, and points you at the summary outputs. You do not need to learn the repo layout first.

Optional: install [Ollama](https://ollama.com), run `ollama serve`, and `ollama pull qwen2.5:14b` so classification can use a local LLM (`classification.backend: auto`).

**Privacy:** Do not commit `config/participant.yaml`, takeouts, LinkedIn archives, or `analysis/` / `output/` contents (gitignored). Classification sends conversation text to the configured LLM backend — keep `classification.ollama.base_url` on loopback unless you trust a remote host.

---

## How it works

```
config/participant.yaml          ← skill writes this (or you edit once)
        │
        ├─► gmail/     Takeout .mbox  → dump → classify → mbox + CSV
        ├─► linkedin/  messages.csv   → dump → classify → CSV + summary
        └─► (future)   other sources add a block to the same config file
```

| Source | Guide | Deliverable |
|--------|-------|-------------|
| [Gmail](gmail/) | [Workflow](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) | `gmail/output/latest/` (mbox + audit/summary CSV; prior runs under `runs/`) |
| [LinkedIn](linkedin/) | [Workflow](linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md) | `linkedin/output/latest/` (filtered CSVs + summary; prior runs under `runs/`) |

Shared rules: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md). Project rule: [`.cursor/rules/job-search-extraction.mdc`](.cursor/rules/job-search-extraction.mdc).

---

## Manual setup (optional)

Use this if you prefer not to use the skill.

```bash
cp config/participant.example.yaml config/participant.yaml
```

| Section | Purpose |
|---------|---------|
| `participant:` | Name + **search window** (shared by every source) |
| `gmail:` | Your email addresses (`my_emails`) |
| `linkedin:` | Display name as it appears in `messages.csv` `FROM` |
| `classification:` | Backend `auto` / `ollama` / `cursor` + Ollama model |

**Default search window** (used if omitted): `2025-01-01` → `2026-01-01`. Gmail tip: `before:` is exclusive — for end `2026-01-01`, use `before:2026/1/2`.

### Gmail

1. Follow [gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) (label → Takeout).
2. Place unzipped Takeout under `gmail/takeout_extracts/`, then:

```bash
cd gmail
pip install -r requirements.txt
python3 run_gmail_pipeline.py
# optional: --backend ollama|cursor   --all-dates
```

### LinkedIn

1. Follow [linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md](linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md) (export → place `messages.csv`).
2. Process:

```bash
cd linkedin
pip install -r requirements.txt
python3 run_linkedin_pipeline.py
# optional: --backend ollama|cursor
```

---

## What to include

**Include** conversations with a **real person** about a **specific job or position**.

**Exclude** personal chat, generic connect spam, coaching sales, training marketing, events, product promos, job-alert digests.

Details: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md).

---

## Repo layout

```
job_search_data/
├── README.md
├── docs/CLASSIFICATION_CRITERIA.md
├── config/
├── common/                   # shared config + classification
├── gmail/
├── linkedin/
└── .cursor/skills/job-search-extraction/
```
