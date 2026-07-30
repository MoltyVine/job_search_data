# Job Search Evidence Extraction

Extract **recruiter / job-opportunity conversations** from Gmail and LinkedIn.

## Requirements

- [pyenv](https://github.com/pyenv/pyenv) — this repo pins its Python version in [`.python-version`](.python-version)
- A virtualenv built from that pinned interpreter (`.venv/`, gitignored)

One-time setup, from the repo root:

```bash
pyenv install -s "$(cat .python-version)"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Every command below (`run_gmail_pipeline.py`, `run_linkedin_pipeline.py`, and everything under `gmail/scripts/` or `linkedin/scripts/`) should be run with `.venv/bin/python3` rather than a bare `python3` — this keeps every script (Gmail and LinkedIn alike) on the same pinned interpreter and dependency set instead of whatever `python3` happens to resolve to on your `PATH`.

## Set up - Guided with Claude Code Skill (recommended)

1. Clone this repo and open it with **Claude Code**.
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

Shared rules: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md). Project rules: [`CLAUDE.md`](CLAUDE.md).

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

Gmail tip: `before:` is exclusive — for inclusive end `YYYY-MM-DD`, use `before:` of the next day (e.g. end `2026-01-01` → `before:2026/1/2`).

### Gmail

1. Follow [gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md](gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md) (label → Takeout).
2. Place unzipped Takeout under `gmail/takeout_extracts/`, then (from the repo root, using the venv from [Requirements](#requirements)):

```bash
cd gmail
../.venv/bin/python3 run_gmail_pipeline.py
# optional: --all-dates
```

**Several Gmail accounts to review?** Each Google Takeout export is per-account, so run the pipeline once per account with `--account <label>` (e.g. `--account personal`, `--account oldwork`) — this keeps each account’s `analysis/` and `output/` separate instead of overwriting the previous account’s run. `gmail.my_emails` in `participant.yaml` stays one shared list across every account. Once every account has a run, combine them:

```bash
../.venv/bin/python3 scripts/merge_account_summaries.py
```

writes `gmail/output/all_accounts_summary.csv` — every account’s summary rows in one file, tagged with an `Account` column.

### LinkedIn

1. Follow [linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md](linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md) (export → place `messages.csv`).
2. Process:

```bash
cd linkedin
../.venv/bin/python3 run_linkedin_pipeline.py
```


### Classification of conversations

Each conversation is included when it was with a **real person** about **one or more job opportunities**. Two backends, set via `classification.backend` in `participant.yaml` or `--backend` on either pipeline:

| Backend | What happens | Needs |
|---------|--------------|-------|
| `agent` (default) | Each pipeline dumps threads to `analysis/threads_dump.txt`, then stops and prints instructions — the Claude Code agent running the pipeline reads that dump, applies the criteria, and writes `analysis/decisions.jsonl` itself. | Nothing — no network call, no API key |
| `openrouter` (opt-in) | The pipeline classifies every thread automatically via [OpenRouter](https://openrouter.ai). Faster for a large mailbox, but thread text leaves this session. | `OPENROUTER_API_KEY` in your environment (never in `participant.yaml`) |

`agent` is private and free but classifies one thread at a time in conversation, so it doesn’t scale well past a few hundred threads — switch to `openrouter` for bigger mailboxes.

Details: [docs/CLASSIFICATION_CRITERIA.md](docs/CLASSIFICATION_CRITERIA.md).

---

## Repo layout

```
job_search_data/
├── README.md
├── .python-version            # pyenv pin — see Requirements above
├── docs/CLASSIFICATION_CRITERIA.md
├── config/
├── common/                   # shared config + classification
├── gmail/
│   └── output/latest/        # Gmail deliverables
├── linkedin/
│   └── output/latest/        # LinkedIn deliverables
└── .claude/skills/job-search-extraction/
```
