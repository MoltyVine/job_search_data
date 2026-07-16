---
name: job-search-extraction
description: >-
  End-to-end job-search conversation extraction from Gmail and/or LinkedIn:
  interview for dates and identity, write participant.yaml, guide exports,
  run pipelines, and point to summary outputs. Use when onboarding, getting
  started, extracting recruiter/job emails or LinkedIn messages, or running
  the Gmail/LinkedIn workflows without requiring repo knowledge.
---

# Job-search extraction (end-to-end)

Guide the user from zero to finished deliverables. They should **not** need to
understand the repo. You place files, write config, run commands, and wait at
human gates (Gmail labeling, Takeout, LinkedIn archive email).

**Criteria:** [docs/CLASSIFICATION_CRITERIA.md](../../../docs/CLASSIFICATION_CRITERIA.md)  
**Gmail search detail:** [gmail-search-reference.md](gmail-search-reference.md)  
**Troubleshooting:** [troubleshooting.md](troubleshooting.md)

## Progress checklist

Copy and update as you go:

```
- [ ] Interview + confirm summary
- [ ] Write config/participant.yaml
- [ ] Gmail: label → search → Takeout → place export (if selected)
- [ ] LinkedIn: request export → place messages.csv (if selected)
- [ ] Run pipeline(s)
- [ ] Point user to summary outputs
```

---

## Agent rules

1. **Interview first** — ask before writing files or running pipelines.
2. **Plain language** — say “your summary spreadsheet,” not jargon, except when a path is required.
3. **Wait** at human gates; do not invent exports or skip labeling.
4. **Privacy** — never commit `config/participant.yaml`, takeouts, `.mbox`, LinkedIn `data/`, or `analysis/` / `output/` contents (gitignored).
5. **Gmail labeling** — prefer over-including; the classifier drops noise later.
6. **Classify handoff** — when unsure, **exclude** (see shared criteria).
7. Do **not** tell the user to open other skills; this skill covers the full path.

---

## Phase 0 — Interview (one batch)

Ask only what the chosen sources need:

1. **Sources:** Gmail / LinkedIn / both
2. **Search window:** start + end dates (defaults `2025-01-01` → `2026-01-01` inclusive). Brief: only conversations overlapping this window are kept.
3. **Identity:**
   - Full name (and first/last if easy)
   - **Gmail:** every send-from address they use
   - **LinkedIn:** display name exactly as it appears in `FROM` when *they* send a message
4. **Gmail keywords** (if Gmail): offer default, let them accept or edit:
   - Core: `(job OR role OR position OR recruit*)`
   - Optional noise: `-digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com`
5. **Classification:** default `auto` (local Ollama if available, else agent handoff). Only ask if they care about the model/backend.

### Confirm summary (required before writes)

Show something like:

```
Sources: … 
Window: YYYY-MM-DD → YYYY-MM-DD
Name: …
Gmail addresses: … (if any)
LinkedIn display name: … (if any)
Gmail search query: … (if Gmail)
Outputs:
  - Gmail summary: gmail/output/latest/recruiter_conversations_summary.csv
  - LinkedIn summary: linkedin/output/latest/recruiter_conversations_summary.csv
```
On confirmation → Phase 1.

---

## Phase 1 — Write config

From repo root:

```bash
test -f config/participant.yaml || cp config/participant.example.yaml config/participant.yaml
```

Write `config/participant.yaml` from answers. Shape:

```yaml
participant:
  name: "…"
  first_name: "…"
  last_name: "…"
  search_window:
    start: "YYYY-MM-DD"
    end: "YYYY-MM-DD"

gmail:
  my_emails:
    - user@example.com

linkedin:
  display_name: "…"

classification:
  backend: auto
  ollama:
    base_url: "http://127.0.0.1:11434"
    model: "qwen2.5:14b"
```

Omit or leave placeholder blocks only if a source was not selected — still fine to include both with the gathered fields. Keep `classification.backend: auto` unless the user chose otherwise.

---

## Phase 2a — Gmail (if selected)

### 1. Label

Ask them to create a Gmail label (e.g. `job_opportunities`).

### 2. Ready-to-paste search

Build the query from their window + keywords.

**Date math:** Gmail `before:` is **exclusive** — use the day *after* the inclusive end.

| Inclusive end | `before:` |
|---------------|-----------|
| 2026-01-01 | `before:2026/1/2` |
| 2026-06-30 | `before:2026/7/1` |

Example (defaults + core + optional noise):

```
after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Give them the **exact** string for their dates. More operators: [gmail-search-reference.md](gmail-search-reference.md).

### 3. Manual labeling

Coach:

1. Paste search in Gmail (web).
2. Review **each page** (often 50 conversations/page).
3. Label job/recruiting/interview/application threads.
4. Skip digests, newsletters, housing, shopping, non-job personal mail.
5. When unsure, **label it**.
6. Verify: `label:<their_label> after:… before:…`

### 4. Google Takeout

1. [takeout.google.com](https://takeout.google.com)
2. Deselect all → enable **Mail** only
3. All Mail data → deselect all labels → select **only** their label
4. Export → download → unzip
5. Place the unzipped `takeout-…` folder under `gmail/takeout_extracts/`

Wait until the export is on disk before running the pipeline.

### 5. Run Gmail pipeline

```bash
cd gmail
pip install -r requirements.txt
python3 run_gmail_pipeline.py
# --backend ollama|cursor   if needed
# --all-dates               if Takeout dates fall outside search_window
```

With one folder in `takeout_extracts/`, no path argument is needed.

---

## Phase 2b — LinkedIn (if selected)

LinkedIn has no in-product search step — export all messages; the pipeline filters by window.

### 1. Request archive

1. Me → **Settings & Privacy**
2. **Data Privacy** → **Get a copy of your data**
3. Larger archive **or** check **Messages**
4. Request archive → wait for email (up to ~24h) → download zip

Use root **`messages.csv`** only (not `guide_messages.csv` / learning coach files).

### 2. Place data

Unzip so this exists:

```
linkedin/data/Complete_LinkedInDataExport_MM-DD-YYYY/messages.csv
```

Sanity check:

```bash
wc -l linkedin/data/Complete_LinkedInDataExport_*/messages.csv
head -1 linkedin/data/Complete_LinkedInDataExport_*/messages.csv
```

### 3. Run LinkedIn pipeline

```bash
cd linkedin
pip install -r requirements.txt
python3 run_linkedin_pipeline.py
# --backend ollama|cursor   if needed
```

---

## Phase 3 — Classification backends

Pipelines use **Ollama** when reachable (`classification.backend: auto`).

If the run prints a **agent handoff** instead of writing decisions:

1. Read every `===== THREAD #… =====` or `===== CONV #… =====` block in:
   - Gmail: `gmail/analysis/threads_dump.txt`
   - LinkedIn: `linkedin/analysis/threads_dump.txt`
2. Apply [docs/CLASSIFICATION_CRITERIA.md](../../../docs/CLASSIFICATION_CRITERIA.md) (real person + specific role; unsure → **exclude**).
3. Write one JSON object per thread to `analysis/decisions.jsonl` (`source`: `"gmail"` or `"linkedin"`).
4. Apply:

```bash
# Gmail (adjust --emails-dir if needed)
cd gmail && python3 scripts/apply_decisions.py

# LinkedIn
cd linkedin && python3 scripts/apply_decisions.py
```

Optional local LLM setup (user-facing): install from https://ollama.com, then `ollama serve` and `ollama pull qwen2.5:14b`.

---

## Phase 4 — Deliverables (tell the user)

| Source | Open this first | Also available |
|--------|-----------------|----------------|
| Gmail | `gmail/output/latest/recruiter_conversations_summary.csv` | Full mail: `recruiter_conversations.mbox`; audit: `recruiter_conversations_report.csv` (same `latest/` folder). Prior runs under `gmail/output/runs/`. |
| LinkedIn | `linkedin/output/latest/recruiter_conversations_summary.csv` | Messages: `recruiter_position_conversations_filtered.csv`; readable: `recruiter_conversations_summary.md`. Prior runs under `linkedin/output/runs/`. |

Spot-check 10–15 summary rows against the thread dump if they want confidence. Compare company overlap across sources when both ran.

---

## Coaching prompts (Gmail labeling)

- "Does this discuss a **specific role or company**, or is it a bulk listing?"
- "Is the sender a **recruiter / hiring manager**, or a newsletter?"
- "Would you want this in a **job-search conversation archive**?"
