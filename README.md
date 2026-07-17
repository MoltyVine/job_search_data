# Job Search Evidence Extraction

Extract **recruiter / job-opportunity conversations** from Gmail and LinkedIn.

## Set up - Guided with Cursor Skill (recommended)

1. Clone this repo and open it in **Cursor**.
2. Ask the agent to use the **`job-search-extraction`** skill  
   (e.g. “Use job-search-extraction to walk me through setup”).

The skill asks a few setup questions, writes `config/participant.yaml`, then walks **one source at a time** (extraction → processing for Gmail, then the same for LinkedIn if selected), and points you at each source’s outputs as you finish.

---

## What you get

After a successful run, open the **`latest/`** folder for each source you ran. Every pipeline run is also saved under `runs/<timestamp>/` so earlier results are never overwritten.

### Start with these (one row per conversation)

| Source | Open this file | What’s in it |
|--------|----------------|--------------|
| **Gmail** | [`gmail/output/latest/recruiter_conversations_summary.csv`](gmail/output/README.md) | Company, role, recruiter/contact, type, message count, reason |
| **LinkedIn** | [`linkedin/output/latest/recruiter_conversations_summary.csv`](linkedin/output/README.md) | Same idea, plus date span and from/to counts |

That’s the main deliverable — a spreadsheet of kept recruiter / job threads.

### Full conversation text (when you need it)

| Source | File | What’s in it |
|--------|------|--------------|
| Gmail | `gmail/output/latest/recruiter_conversations.mbox` | Full email bodies for kept threads (open in a mail client) |
| LinkedIn | `linkedin/output/latest/recruiter_position_conversations_filtered.csv` | Message-level InMail text for kept conversations |
| LinkedIn | `linkedin/output/latest/recruiter_conversations_summary.md` | Same summary as the CSV, readable as markdown |

### For debugging / audit

| Source | File | What’s in it |
|--------|------|--------------|
| Gmail | `gmail/output/latest/recruiter_conversations_report.csv` | Per-message keep/drop audit + classification fields |
| Both | `…/latest/decisions.jsonl` | Snapshot of include/exclude decisions for that run |

More detail: [gmail/output/README.md](gmail/output/README.md), [linkedin/output/README.md](linkedin/output/README.md).

---

## How it works

```
config/participant.yaml          ← skill writes this (or you edit once)
        │
        ├─► gmail/     Takeout .mbox  → dump → classify → output/latest/
        ├─► linkedin/  messages.csv   → dump → classify → output/latest/
        └─► (future)   other sources add a block to the same config file
```

| Source | Guide |
|--------|-------|
| [Gmail](gmail/) | [Workflow](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) |
| [LinkedIn](linkedin/) | [Workflow](linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md) |

Shared rules: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md). Project rule: [`.cursor/rules/job-search-extraction.mdc`](.cursor/rules/job-search-extraction.mdc).

---

## Manual setup (optional)

Use this if you prefer not to use the skill.

```bash
cp config/participant.example.yaml config/participant.yaml
```

| Section | Purpose |
|---------|---------|
| `participant:` | Name + **search window** (inclusive start/end — required; skill asks for yours) |
| `gmail:` | Your email addresses (`my_emails`) |
| `linkedin:` | Display name in `messages.csv` `FROM` (omit if same as `participant.name`) |
| `classification:` | Backend `auto` / `ollama` / `cursor` + Ollama model |

Gmail tip: `before:` is exclusive — for inclusive end `YYYY-MM-DD`, use `before:` of the next day (e.g. end `2026-01-01` → `before:2026/1/2`).

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


### LLM guided classification of conversations

Each conversation is included when it was with a **real person** about **one or more job opportunities**.

| Option | What you need | What happens |
|--------|----------------|--------------|
| **Local (default when available)** | [Ollama](https://ollama.com) running on your machine | Pipeline calls Ollama automatically (`classification.backend: auto`) |
| **In Cursor (no API key)** | This repo open in Cursor | If Ollama isn’t running, the skill / agent reads the thread dump and writes decisions — **no separate API key** |

The repo **does not** install a model for you. It checks whether Ollama is reachable, and if the `ollama` binary is installed but the server is down, it tries `ollama serve` automatically. For local runs:

```bash
ollama serve
ollama pull qwen2.5:14b   # model name in config; change if you prefer another
```

If Ollama isn’t installed, you can still finish entirely in Cursor via the skill — no cloud API key is required by this project.

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
│   └── output/latest/        # Gmail deliverables
├── linkedin/
│   └── output/latest/        # LinkedIn deliverables
└── .cursor/skills/job-search-extraction/
```
