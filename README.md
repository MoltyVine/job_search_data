# Job Search Evidence Extraction

Extract **recruiter / job-opportunity conversations** from Gmail and LinkedIn (and other sources as you add them).

**One config. Multiple sources.** Set identity and date window once, then run each source workflow against the same settings.

---

## How it works

```
config/participant.yaml          ← you fill this once
        │
        ├─► gmail/     Takeout .mbox  → dump → classify → mbox + CSV
        ├─► linkedin/  messages.csv   → dump → classify → CSV + summary
        └─► (future)   other sources add a block to the same config file
```

Classification (both sources): **local LLM via Ollama** when available, or **Cursor agent** handoff. Shared rules: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md).

| Source | Guide | Deliverable |
|--------|-------|-------------|
| [Gmail](gmail/) | [Workflow](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) | `gmail/output/latest/` (mbox + audit/summary CSV; prior runs under `runs/`) |
| [LinkedIn](linkedin/) | [Workflow](linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md) | `linkedin/output/latest/` (filtered CSVs + summary; prior runs under `runs/`) |

---

## 1. Configure (once)

```bash
cp config/participant.example.yaml config/participant.yaml
```

Edit [`config/participant.yaml`](config/participant.example.yaml):

| Section | Purpose |
|---------|---------|
| `participant:` | Name + **search window** (shared by every source) |
| `gmail:` | Your email addresses (`my_emails`) |
| `linkedin:` | Display name as it appears in `messages.csv` `FROM` |
| `classification:` | Backend `auto` / `ollama` / `cursor` + Ollama model |
| *(future)* | New top-level key per source — pipelines ignore unknown keys |

**Default search window** (used if omitted):

| | Date |
|--|------|
| Start | `2025-01-01` |
| End | `2026-01-01` |

Gmail tip: `before:` is exclusive — for end `2026-01-01`, search with `before:2026/1/2`.

### Local LLM (recommended)

```bash
# install from https://ollama.com — then:
ollama serve
ollama pull llama3.1:8b
```

With `classification.backend: auto` (default), pipelines use Ollama when reachable; otherwise they prompt to use the Cursor agent backend (or pass `--backend cursor`).

**Privacy:** `config/participant.yaml` and raw exports are gitignored. Do not commit PII, takeout zips, `.mbox` files, LinkedIn archives, or `analysis/` / `output/` contents.

---

## 2. Run sources

Do either or both. Same config either way.

### Gmail

1. Follow [gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) (label → Takeout).
2. Process:

```bash
cd gmail
pip install -r requirements.txt
python3 run_gmail_pipeline.py
# optional: --backend ollama|cursor   --all-dates
```

Place unzipped Takeout folders in `gmail/takeout_extracts/`. With one folder, no path argument is needed.

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
├── common/                   # shared config + classification (Ollama client)
├── gmail/
├── linkedin/
└── .cursor/skills/
```

---

## Cursor skill

| Skill | Use for |
|-------|---------|
| `job-search-extraction` | End-to-end setup: interview → config → Gmail/LinkedIn export → pipelines → outputs |

Guided path: invoke **job-search-extraction** (writes `participant.yaml`, walks exports, runs pipelines). Detailed human guides remain under `gmail/docs/` and `linkedin/docs/`.

Project rule: [`.cursor/rules/job-search-extraction.mdc`](.cursor/rules/job-search-extraction.mdc)
