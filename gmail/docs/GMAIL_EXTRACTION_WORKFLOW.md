# Gmail Job-Search Extraction Workflow

End-to-end process to extract **recruiter / job-opportunity email conversations** from Gmail.

---

## Overview


| Phase                       | Who                   | What                                                               |
| --------------------------- | --------------------- | ------------------------------------------------------------------ |
| **1. Prepare**              | Participant           | Create Gmail label; confirm repo-root config (see README)          |
| **2. Gmail search & label** | Participant           | Search, then select-all + label each results page                  |
| **3. Google Takeout**       | Participant           | Export labeled mail as `.mbox`                                     |
| **4. Process**              | Claude Code / command line | Run Python pipeline, then classify each thread → filtered mbox + audit CSV |
| **5. Review**               | Participant           | Spot-check `recruiter_conversations_report.csv`                    |

---



## Phase 1 — Prepare

### 1.1 Create a Gmail label

1. Open Gmail → **Settings** (gear) → **See all settings** → **Labels** → **Create new label**.
2. Use a clear name, e.g. `job_opportunities` or `recruiter_mail`. Remember it for Takeout (export only this label).

### 1.2 Confirm shared config

If you have not already, follow **Configure (once)** in the [repo README](../../README.md) (`config/participant.yaml`).

For Gmail, `gmail.my_emails` must list every address you send from (used to detect your replies). Set `participant.search_window` to your inclusive date range (used for Phase 2 search dates and pipeline filtering).



## Phase 2 — Gmail search & manual labeling

This phase will use a manual keyword step to cast a wide net for mail

### 2.1 Build the Gmail search query

Copy-paste into the Gmail search box (web). Replace the dates for **your** inclusive window (`before:` = day after inclusive end). Standard query includes noise exclusions:

```
is:read after:YYYY/M/D before:YYYY/M/D (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Example (inclusive 2025-01-01 → 2026-01-01):

```
is:read after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

`is:read` assumes relevant conversations were opened; drop it if unread recruiter mail may matter.

### 2.2 Review and label — page by page

1. Run the search in Gmail.
2. Gmail shows **50 conversations per page** (default).
3. For each page:
  - Select all emails → **Label** → your label (e.g. `job_opportunities`).
4. Go to the next page. Repeat until no results remain.

**Tips:**

- When unsure, **include** — later filtering can remove noise; missing a real recruiter thread is worse.
- Keep a rough count: pages × ~50 gives order-of-magnitude for how much you labeled.



## Phase 3 — Google Takeout export

1. Go to [https://takeout.google.com](https://takeout.google.com).
2. **Deselect all** products.
3. Find and select **Mail** only
4. Press **All Mail data included** button → **Deselect all** → check **only your label** (e.g. `job_opportunities`).
5. 'OK' -> then click Next Step.
5. Export size: one delivery, `.zip` if possible.
6. Download and unzip
7. Copy the unzipped takeout folder into `gmail/takeout_extracts/` (e.g. `gmail/takeout_extracts/takeout-20260703T001747Z-3-001/`).

**Privacy:** Takeout contains full email content. Store locally; do not commit to git. The repo `.gitignore` excludes takeout data.

---

## Phase 4 — Run the processing pipeline

### 4.1 Install dependencies

From the repo root, build the pinned venv once (see root [README.md](../../README.md) → Requirements):

```bash
pyenv install -s "$(cat .python-version)"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Then run the pipeline with that same interpreter:

```bash
cd gmail
../.venv/bin/python3 run_gmail_pipeline.py
# optional: --all-dates
```

With one folder under `takeout_extracts/`, no path argument is needed. If several exist:

```bash
../.venv/bin/python3 run_gmail_pipeline.py takeout_extracts/takeout-YYYYMMDD/
```

**Several Gmail accounts to review?** Google Takeout only exports one account at a time, so repeat **all** of Phase 1–4 once per account (its own label, its own search, its own Takeout export), and tag each pipeline run with `--account <label>`:

```bash
../.venv/bin/python3 run_gmail_pipeline.py takeout_extracts/takeout-personal/ --account personal
../.venv/bin/python3 run_gmail_pipeline.py takeout_extracts/takeout-oldwork/ --account oldwork
```

This keeps `analysis/<label>/` and `output/<label>/` separate per account so the second run doesn't overwrite the first. `gmail.my_emails` in `participant.yaml` stays one shared list across every account — it's just used to detect "is this me?" in any thread. Once every account has a run:

```bash
../.venv/bin/python3 scripts/merge_account_summaries.py
```

writes `gmail/output/all_accounts_summary.csv` — every account's summary rows combined, tagged with an `Account` column.

### 4.2 What the pipeline does

```
takeout …/label.mbox
        │
        ▼  split_mbox.py
        …/label_emails/*.eml
        │
        ▼  scripts/dump_threads.py
        analysis/threads_dump.txt + threads.json
        │
        ▼  scripts/classify_threads.py
        prints instructions → you classify → analysis/decisions.jsonl
        │
        ▼  scripts/apply_decisions.py
        output/latest/ → runs/<timestamp>/
          recruiter_conversations.mbox
          recruiter_conversations_report.csv
          recruiter_conversations_summary.csv
```

**Classification:** include if a **real person** discusses **one or more job opportunities**. Shared rules: [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md). By default (`agent` backend) the pipeline stops after the dump and prints instructions; the Claude Code agent reads `analysis/threads_dump.txt` and writes `analysis/decisions.jsonl` directly — no local model or API key involved. For a large mailbox, pass `--backend openrouter` (or set `classification.backend: openrouter` in `participant.yaml`) to classify automatically instead — needs `OPENROUTER_API_KEY`, and sends thread text to OpenRouter.

### 4.3 Outputs

| File | Purpose |
|------|---------|
| `gmail/output/latest/recruiter_conversations.mbox` | Kept threads |
| `gmail/output/latest/recruiter_conversations_report.csv` | Per-message audit + LLM fields |
| `gmail/output/latest/recruiter_conversations_summary.csv` | One row per kept thread |
| `gmail/output/runs/<timestamp>/` | Immutable copy of each apply (includes `decisions.jsonl` snapshot) |
| `gmail/analysis/decisions.jsonl` | Working decisions (resume-friendly) |

---

## Phase 5 — Review & tune

1. Open `gmail/output/latest/recruiter_conversations_summary.csv` and spot-check against `analysis/threads_dump.txt`.
2. Fix bad calls by editing `analysis/decisions.jsonl` (or re-classify), then:

```bash
cd gmail
../.venv/bin/python3 scripts/apply_decisions.py --emails-dir takeout_extracts/.../label_emails/
```

---

## Guided path

Invoke the **`job-search-extraction`** skill for interview → config → labeling → Takeout → pipeline → outputs.

> Use job-search-extraction to walk me through Gmail job-search extraction.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No takeout folders` / multiple | Put one unzip under `takeout_extracts/`, or pass the folder path |
| Empty dump (0 threads) | Window may not match Takeout dates — use `--all-dates` or fix `search_window` |
| `Missing participant.yaml` | `cp config/participant.example.yaml config/participant.yaml` |
| `ModuleNotFoundError: yaml` | Not using the pinned venv — run `.venv/bin/pip install -r requirements.txt` from the repo root, then invoke scripts via `.venv/bin/python3` |
| Second Gmail account's run overwrote the first | Re-run both with `--account <label>` (see §4.1) — without it, every account shares the same `analysis/`/`output/` |
| `Backend 'openrouter' requested but OPENROUTER_API_KEY is not set` | Export the key, or drop `--backend openrouter` / `classification.backend` to use the default `agent` backend instead |

---

## Checklist (printable)

```
Phase 1 — Prepare
[ ] Gmail label created: _______________
[ ] Shared config done per README (gmail.my_emails set)
[ ] Search window set (or defaults)

Phase 2 — Search & label
[ ] Gmail search run with after/before + core terms + standard noise exclusions
[ ] All result pages: select all → apply label
[ ] Label covers full search result set

Phase 3 — Takeout
[ ] takeout.google.com — Mail only, single label
[ ] Unzipped folder under gmail/takeout_extracts/

Phase 4 — Process
[ ] .venv/bin/pip install -r requirements.txt (from repo root)
[ ] run_gmail_pipeline.py completed and decisions applied

Phase 5 — Review
[ ] Spot-checked gmail/output/latest/recruiter_conversations_summary.csv
```

---

## Related work (not in this guide)

- **LinkedIn messages:** [linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md](../../linkedin/docs/LINKEDIN_EXTRACTION_WORKFLOW.md)
- **Shared criteria:** [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md)

