---
name: job-search-extraction
description: >-
  End-to-end job-search conversation extraction from Gmail and/or LinkedIn:
  interview for dates and identity, write participant.yaml, guide exports,
  run pipelines, and point to summary outputs. Handles multiple Gmail
  accounts and high-volume mailboxes (optional automated classification).
  Use when onboarding, getting started, extracting recruiter/job emails or
  LinkedIn messages, or running the Gmail/LinkedIn workflows without
  requiring repo knowledge.
---

# Job-search extraction (end-to-end)

Guide the user from zero to finished deliverables. They should **not** need to
understand the repo. You place files, write config, run commands, classify
conversations yourself, and wait at human gates (Gmail labeling, Takeout,
LinkedIn archive email).

**Criteria:** [docs/CLASSIFICATION_CRITERIA.md](../../../docs/CLASSIFICATION_CRITERIA.md)
**Gmail search detail:** [gmail-search-reference.md](gmail-search-reference.md)
**Troubleshooting:** [troubleshooting.md](troubleshooting.md)

## Progress checklist

Copy and update as you go. Check off **one source fully** before starting the next:

```
- [ ] Interview + confirm summary
- [ ] Write config/participant.yaml
- [ ] Gmail account 1: extraction (label → Takeout → place export)   # if selected
- [ ] Gmail account 1: processing (pipeline → classify → summary)    # if selected
- [ ] Gmail account N: repeat extraction + processing                # only if several accounts
- [ ] Gmail: merge_account_summaries.py                              # only if several accounts
- [ ] LinkedIn extraction (request → place messages.csv)  # if selected
- [ ] LinkedIn processing (pipeline → classify → summary) # if selected
- [ ] Final wrap-up (paths + optional cross-source check)
```

---

## Agent rules

1. **Interview first** — adaptive, multi-turn OK. Ask **sources first** and wait; then ask only questions that apply. Do not dump Gmail and LinkedIn prompts together “just in case.”
2. **One source at a time** — never give Gmail and LinkedIn extraction (or processing) instructions in the same turn. Finish **extraction → processing** for the current source, then move to the next. Same pattern for any future source.
3. **Default order** when both selected: **Gmail, then LinkedIn**. (Only LinkedIn → skip Gmail blocks.)
4. **Plain language** — say “your summary spreadsheet,” not jargon, except when a path is required. Paths are from the **repo root** (`job_search_data/`) unless you `cd` into `gmail/` or `linkedin/`.
5. **Pace human gates** — one gate per turn when possible. Example Gmail extraction: (a) create label + paste search + select-all label → wait; (b) Takeout steps → wait until zip is unzipped under `gmail/takeout_extracts/`. Do not invent exports or skip labeling.
6. **Privacy** — never commit `config/participant.yaml`, takeouts, `.mbox`, LinkedIn `data/`, or `analysis/` / `output/` contents (gitignored). Message content stays local to this session unless the user opts into the `openrouter` classification backend (see rule 13) — never enable it without asking first.
7. **Gmail labeling** — after the search filter is in place, **select all on each results page** and apply the label. Do **not** ask them to judge relevance per thread; you classify that later.
8. **Classify handoff** — when unsure, **exclude** (see shared criteria). Applies during that source’s **processing** turn, not Gmail labeling.
9. Do **not** tell the user to open other skills; this skill covers the full path.
10. **You run processing** — after data is on disk, you run the pipeline via the pinned `.venv/bin/python3`, then classify and run `apply_decisions.py`. Don’t ask the user to figure out commands.
11. **Search window** — always ask for inclusive start/end dates. Do **not** suggest, mention, or offer a default range.
12. **Before any pipeline** — tell the user the dump + classify step may take a **few minutes** for a large mailbox (you’re reading every thread yourself). Run with `PYTHONUNBUFFERED=1` so any progress output streams. Prefer keeping the command in the foreground so they can see status.
13. **Classification backend** — default is `agent` (you, working through the thread dump; no API key, nothing to install). After `dump_threads.py` prints the in-window thread count, if it's large (rule of thumb: **50+** threads) mention that the optional `openrouter` backend can classify automatically instead — trades privacy (thread text goes to OpenRouter) for speed, needs `OPENROUTER_API_KEY`. Only switch if the user opts in; never enable it unprompted.
14. **Multiple Gmail accounts** — ask during Gmail's interview step (Step 3 below). Each account gets its own full Turn A + Turn B pass, tagged with `--account <label>`. Don't move to LinkedIn (or wrap up) until every Gmail account has a summary CSV.

---

## Phase 0 — Interview (adaptive)

Do **not** ask everything in one message. Multiple turns are expected.

### Step 1 — Sources only

Ask: **Gmail**, **LinkedIn**, or **both**? Wait for the answer before anything else.

### Step 2 — Shared (after sources are known)

Ask:

1. **Search window:** inclusive start and end dates (YYYY-MM-DD). Say only that conversations overlapping this window are kept. **Never** propose or mention a default range.
2. **Full name** — if they don’t split it, derive `first_name` / `last_name` (last token = last name).

### Step 3 — Source-specific (only what they selected)

**If Gmail:**

- Every address they send from, across **every** Gmail account they'll search (one shared list — used only to detect "is this me?" in any thread).
- **How many Gmail accounts** need searching? Most people: just one. If more than one, get a short label for each (e.g. "personal", "old work") — each account repeats the full Gmail loop (Turn A + Turn B) on its own, tagged with `--account <label>`.
- Gmail search: build the **standard** query from their window (see below). Confirm it; they may edit. Do **not** frame noise exclusions as optional extras — they are part of the standard query. Same query applies to every account (each has its own label and Takeout export).

Standard query shape:

```
is:read after:YYYY/M/D before:YYYY/M/D (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Notes for you (not a quiz for the user): `before:` is exclusive (day after inclusive end); `is:read` assumes they’ve opened job-search mail — drop it if they may have unread recruiter threads. Operators: [gmail-search-reference.md](gmail-search-reference.md).

**If LinkedIn:**

- LinkedIn name **only if different** from full name (must match `FROM` when *they* send). If same, skip — config falls back to full name.

### Confirm summary (required before writes)

Show only fields that apply, e.g.:

```
Sources: …
Window: YYYY-MM-DD → YYYY-MM-DD
Name: …
Gmail addresses: …          # Gmail only
Gmail accounts: …           # Gmail only; omit if just one
Gmail search query: …       # Gmail only
LinkedIn name: …            # LinkedIn only; or “same as Name”
Next up: … extraction
```

Ask them to confirm (or note corrections). On yes: write config, then **start guiding them through** the first source’s extraction (e.g. “I’ll start guiding you through Gmail extraction”). Do **not** say you’ll “start labeling” as if you’re doing it for them.

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
  display_name: "…"   # same as participant.name unless they gave a different LinkedIn name
```

Omit or leave placeholder blocks only if a source was not selected — still fine to include both with the gathered fields.

Then, once (skip if `.venv/` already exists), build the pinned virtualenv from repo root:

```bash
pyenv install -s "$(cat .python-version)"
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Every pipeline command in this skill uses `.venv/bin/python3` (never a bare `python3`) so both sources run on the same pinned interpreter and dependency set.

Then start the **first selected source** (Gmail if selected, else LinkedIn).

---

## Per-source loop

For **each** selected source, run two stages in order. Do not start the next source until the current source’s processing has finished (summary CSV exists). Gmail with multiple accounts nests one more level — repeat the Gmail loop per account before moving on:

```
Source N (e.g. Gmail):
  Account 1 (only relevant for Gmail — LinkedIn has exactly one):
    Turn A — Extraction   (human gates; wait)
    Turn B — Processing   (pipeline --account <label> → you classify → summary)
  Account 2, 3, … : repeat
  [if 2+ Gmail accounts] merge_account_summaries.py → combined summary
Source N+1 (e.g. LinkedIn):
  Turn A — Extraction   (human gates; wait)
  Turn B — Processing   (pipeline → you classify → summary)
```

---

## Gmail — Turn A: Extraction (if selected)

Stay on Gmail only until Turn B is done — and if several accounts were selected, until **all** of them are done. Prefer **two waits** per account: labeling done, then Takeout on disk. If this is account 2+, repeat A1–A2 for that account's own label and Takeout export; nothing here changes per account except which Gmail account the user is working in.

### A1. Label + search (wait for “labeling done”)

1. Ask them to create a Gmail label (e.g. `job_opportunities`).
2. Give a **ready-to-paste** search for their window.

**Date math:** Gmail `before:` is **exclusive** — use the day *after* the inclusive end.

| Inclusive end | `before:` |
|---------------|-----------|
| 2026-01-01 | `before:2026/1/2` |
| 2026-06-30 | `before:2026/7/1` |

Paste the query from the interview (standard shape includes noise exclusions). Example for an inclusive end of 2026-01-01:

```
is:read after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Operators: [gmail-search-reference.md](gmail-search-reference.md).

3. Labeling is mechanical — **do not** triage relevance:

   - Paste the search in Gmail (web).
   - ~50 conversations per page.
   - For **each page**: select **all** → **Label** → their label.
   - Next page → repeat until no results remain.
   - Optional verify: `label:<their_label> after:… before:…`

Over-including is fine; classification drops digests later. **Wait** until they say labeling is done.

### A2. Google Takeout (wait for folder on disk)

Takeout can take **minutes to hours** (email when ready).

1. [takeout.google.com](https://takeout.google.com)
2. Deselect all → enable **Mail** only
3. All Mail data → deselect all labels → select **only** their label
4. Next step → export → download → unzip
5. Place the unzipped `takeout-…` folder under `gmail/takeout_extracts/`

Typical contents: `Takeout/Mail/<label>.mbox`. **Wait** until that folder exists → **Gmail Turn B**.

---

## Gmail — Turn B: Processing (if selected)

Tell the user this may take a **few minutes** (dump, then you read and classify each thread). Then you run (unbuffered so any progress output streams; add `--account <label>` whenever more than one Gmail account was selected — omit it entirely for a single account):

```bash
cd gmail
PYTHONUNBUFFERED=1 ../.venv/bin/python3 run_gmail_pipeline.py
# --account personal            if multiple Gmail accounts (repeat per account, own label each time)
# --all-dates                   if Takeout dates fall outside search_window
```

With **one** folder in `takeout_extracts/`, no path argument is needed. If several, pass the folder path.

The dump step prints the in-window thread count — if it's large (50+), mention the optional `openrouter` backend now (rule 13) before you start classifying by hand; proceed with the default `agent` backend unless the user opts in.

The run stops after printing **classification instructions** — classify **this account only** (see [Classification](#classification)), then apply using the **exact command the pipeline printed** (it already includes the right `--emails-dir`, and `--analysis-dir`/`--output-dir` when `--account` is in play — don't drop those flags or output lands in the wrong account's folder):

```bash
cd gmail && ../.venv/bin/python3 scripts/apply_decisions.py --emails-dir takeout_extracts/<takeout>/…/<label>_emails
# with --account set, the pipeline's printout adds --analysis-dir/--output-dir here too — keep them
```

**If more Gmail accounts remain, go back to Gmail Turn A for the next one** — don't point to outputs or move to LinkedIn yet.

**Once every Gmail account is done**, if there was more than one, merge them:

```bash
cd gmail && ../.venv/bin/python3 scripts/merge_account_summaries.py
```

**Point them to Gmail outputs now** (don’t wait for LinkedIn):

| Open first | What’s in it |
|------------|--------------|
| `gmail/output/latest/recruiter_conversations_summary.csv` | Single account: **main deliverable** — one row per kept conversation (company, role, contact, type, reason) |
| `gmail/output/all_accounts_summary.csv` | Multiple accounts: same, combined across accounts with an `Account` column |

Also available: per account, full mail (`recruiter_conversations.mbox`), per-message audit (`recruiter_conversations_report.csv`), prior runs under `gmail/output/<label>/runs/` (or `gmail/output/runs/` for a single account).

Then, if LinkedIn was selected → tell them you’re moving to LinkedIn next → **LinkedIn Turn A**. Else → [Final wrap-up](#final-wrap-up).

---

## LinkedIn — Turn A: Extraction (if selected)

Do not mix in Gmail steps. LinkedIn has no in-product search — export **all** messages; the pipeline filters by window.

Warn up front: LinkedIn’s email link can take **up to ~24 hours**.

### A1. Request archive (wait for download email)

1. Me → **Settings & Privacy**
2. **Data Privacy** → **Download my data**
3. Choose **Download larger data archive** (includes messages)
4. **Request archive** → wait for email (up to ~24h) → download zip

Use root **`messages.csv`** only (not `guide_messages.csv` / learning coach files).

### A2. Place data (wait until path exists)

Unzip so this exists:

```
linkedin/data/Complete_LinkedInDataExport_MM-DD-YYYY/messages.csv
```

Sanity check (you can run):

```bash
wc -l linkedin/data/Complete_LinkedInDataExport_*/messages.csv
head -1 linkedin/data/Complete_LinkedInDataExport_*/messages.csv
```

Expected header includes `CONVERSATION ID`, `FROM`, `TO`, `DATE`, `CONTENT`. → **LinkedIn Turn B**.

---

## LinkedIn — Turn B: Processing (if selected)

Tell the user this may take a **few minutes**. Then you run:

```bash
cd linkedin
PYTHONUNBUFFERED=1 ../.venv/bin/python3 run_linkedin_pipeline.py
```

The dump step prints the in-window conversation count — if it's large (50+), mention the optional `openrouter` backend now (rule 13) before you start classifying by hand; proceed with the default `agent` backend unless the user opts in.

The run stops after printing **classification instructions** — classify **this source only** (see [Classification](#classification)), then:

```bash
cd linkedin && ../.venv/bin/python3 scripts/apply_decisions.py
```

**Point them to LinkedIn outputs now:**

| Open first | What’s in it |
|------------|--------------|
| `linkedin/output/latest/recruiter_conversations_summary.csv` | **Main deliverable** — one row per kept conversation |

Also available: readable markdown (`recruiter_conversations_summary.md`), message-level text (`recruiter_position_conversations_filtered.csv`), prior runs under `linkedin/output/runs/`.

Then → [Final wrap-up](#final-wrap-up).

---

## Classification

Two backends (rule 13). **`agent` (default) — you classify inline:**

1. Read every `===== THREAD #… =====` or `===== CONV #… =====` block in that source's dump:
   - Gmail: `gmail/analysis/threads_dump.txt` (or `gmail/analysis/<label>/threads_dump.txt` when `--account` is in play)
   - LinkedIn: `linkedin/analysis/threads_dump.txt`
2. Apply [docs/CLASSIFICATION_CRITERIA.md](../../../docs/CLASSIFICATION_CRITERIA.md) (real person + one or more job opportunities; unsure → **exclude**).
3. Write one JSON object per thread to that dump's `decisions.jsonl` (`source`: `"gmail"` or `"linkedin"`).
4. Run that source's `apply_decisions.py` (always via `.venv/bin/python3`), using the **exact command the pipeline printed** — it already has the right `--emails-dir`/`--analysis-dir`/`--output-dir` for this account:
   - **Gmail:** must pass `--emails-dir` (plus `--analysis-dir`/`--output-dir` when using `--account`).
   - **LinkedIn:** `cd linkedin && ../.venv/bin/python3 scripts/apply_decisions.py` is enough.

**`openrouter` (opt-in) — automated, for high-volume mailboxes:** only after the user agrees (rule 13). Set `classification.backend: openrouter` in `config/participant.yaml` (and optionally `classification.openrouter.model` — check [openrouter.ai/models](https://openrouter.ai/models) for current slugs) or pass `--backend openrouter` on the pipeline command. Confirm `OPENROUTER_API_KEY` is set in the environment before running — if it's missing, the pipeline explains how to export it and stops; do not put the key in `participant.yaml`. With this backend the pipeline classifies every thread itself and writes `decisions.jsonl` directly — skip straight to `apply_decisions.py` once it finishes.

### Classification prompts

- Real person about **one or more job opportunities**? If unsure → **exclude**.
- Recruiter / hiring manager / referrer, or automated digest / careers marketing?
- Multi-role recruiter threads still **include**.

---

## Final wrap-up

After all selected sources have a summary CSV, give a short **outputs summary** (not just paths):

**What you have**

- Each kept conversation is a real-person thread about one or more job opportunities (see classification criteria).
- Open the **summary CSV** first — one row per conversation (company, role, contact, type).

**Where to look**

| Source | Start here | Also useful |
|--------|------------|-------------|
| Gmail (one account) | `gmail/output/latest/recruiter_conversations_summary.csv` | `.mbox` = full emails; `…_report.csv` = keep/drop audit |
| Gmail (multiple accounts) | `gmail/output/all_accounts_summary.csv` | Per-account `.mbox`/`…_report.csv` under `gmail/output/<label>/latest/` |
| LinkedIn | `linkedin/output/latest/recruiter_conversations_summary.csv` | `.md` = readable table; `…_filtered.csv` = full message text |

Prior runs stay under each source’s `output/runs/<timestamp>/` (per-account: `output/<label>/runs/<timestamp>/`); `latest` points at the newest.

**Optional next steps**

- Spot-check 10–15 summary rows against that source’s `analysis/threads_dump.txt`.
- If **both** ran: compare company overlap across the two summary CSVs.

---

## Future sources

When a new source is added: same loop — **Turn A extraction (wait) → Turn B processing → next source**. Do not parallelize instructions across sources in one turn.
