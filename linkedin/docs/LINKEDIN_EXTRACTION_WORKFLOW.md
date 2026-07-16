# LinkedIn Job-Search Extraction Workflow

End-to-end process to extract **recruiter / job-opportunity LinkedIn message conversations** from a LinkedIn data export.

**Scope of this guide:** LinkedIn only. Gmail extraction is a separate workflow in `gmail/` (see `gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md`).

---

## Overview

| Phase | Who | What |
|-------|-----|------|
| **1. Prepare** | Participant | Note date window; confirm LinkedIn display name |
| **2. LinkedIn export** | Participant | Request "Download your data" archive with Messages |
| **3. Place data** | Participant | Unzip export into `linkedin/data/` |
| **4. Configure** | Participant or helper | Fill in repo-root `config/participant.yaml` (shared with Gmail) |
| **5. Prep & classify** | Cursor / command line | Run pipeline prep → read threads → build filtered outputs |
| **6. Review** | Participant | Spot-check summary CSV; compare with Gmail counts |

---

## Phase 1 — Prepare

**Before Phase 1:** set shared settings in the [repo README](../../README.md) / `config/participant.yaml`.

### 1.1 Record your date window

Use `participant.search_window` in repo-root `config/participant.yaml` (shared with all sources). Defaults are fine for most people.

- `search_window` — conversations with **any message** in this range are candidates.
- Optional `linkedin.summary_window` — narrower range for the human-readable summary doc only.

### 1.2 Find your LinkedIn display name

Open any sent LinkedIn message you've written. In `messages.csv`, your outbound rows use your name in the **FROM** column (usually `First Last`). Set this as `linkedin.display_name` in config.

**Example:** if `FROM` shows `Jane Doe` when you send, set `display_name: "Jane Doe"` under `linkedin:`.

### 1.3 Directory layout

```
config/participant.yaml                # shared (repo root, not committed)
linkedin/
  data/Complete_LinkedInDataExport_*/messages.csv
  analysis/                            # generated dumps (gitignored)
  output/                              # final deliverables (gitignored)
```

---

## Phase 2 — Request your LinkedIn data export

LinkedIn does **not** offer keyword search or labeling like Gmail. You download **all** messages, then filter locally.

### Step-by-step (LinkedIn UI)

1. Click your **Me** icon at the top of your LinkedIn Homepage.
2. Select **Settings & Privacy** from the dropdown menu.
3. Click on the **Data Privacy** tab on the left rail.
4. Scroll to the **How LinkedIn uses your data** section and click **Get a copy of your data**.
5. Select the **Download larger data archive** radio button (which includes messages) **or** check the **Messages** box directly under "Want something in particular?".
6. Click **Request archive**. You will be prompted to enter your account password.
7. LinkedIn will send a download link to your **primary email address**. (Larger data archives typically take up to 24 hours to prepare).
8. Open the email and click the link to download your data folder. Inside the `.zip` file, you will find a **`messages.csv`** file.

### Tips

- **Messages-only** export is faster if you only need this workflow.
- **Larger archive** includes messages plus profile, connections, etc. — still works; the pipeline finds `messages.csv` automatically.
- Export is a point-in-time snapshot. Re-export before filing if you want messages through a later date.
- LinkedIn may also include `guide_messages.csv`, `learning_coach_messages.csv`, etc. — **ignore** those; use root **`messages.csv`**.

---

## Phase 3 — Place the export

1. Download and unzip the LinkedIn archive.
2. Confirm `messages.csv` exists (usually inside `Complete_LinkedInDataExport_MM-DD-YYYY/`).
3. Copy the unzipped folder into this project:

   ```
   linkedin/data/Complete_LinkedInDataExport_07-06-2026/
     messages.csv
     Profile.csv
     …
   ```

4. Quick sanity check:

   ```bash
   wc -l linkedin/data/Complete_LinkedInDataExport_*/messages.csv
   head -1 linkedin/data/Complete_LinkedInDataExport_*/messages.csv
   ```

   Expected header includes: `CONVERSATION ID`, `FROM`, `TO`, `DATE`, `CONTENT`.

**Privacy:** The export contains full message content and PII. Store locally; **do not commit** to git (`linkedin/data/` is gitignored).

---

## Phase 4 — Configure participant

Shared config lives at the **repo root** (not under `linkedin/`):

```bash
# from repo root
cp config/participant.example.yaml config/participant.yaml
```

Edit `config/participant.yaml`:

```yaml
participant:
  name: "Jane Doe"
  first_name: "Jane"
  last_name: "Doe"
  search_window:
    start: "2025-01-01"   # default
    end: "2026-01-01"     # default; later if needed, e.g. 2026-06-30

gmail:
  my_emails:
    - jane.doe@gmail.com

linkedin:
  display_name: "Jane Doe"   # must match FROM column when you send
```

Omit `search_window` to use code defaults. Fill both `gmail` and `linkedin` sections in this file as needed.

---

## Phase 5 — Prep & classify

Classification is **conversation-based**: dump threads, then classify with **Ollama** (default when available) or **Cursor agent**. Rules: [classification_criteria.md](classification_criteria.md) → [docs/CLASSIFICATION_CRITERIA.md](../../docs/CLASSIFICATION_CRITERIA.md).

### 5.1 Install dependencies

```bash
cd linkedin
python3 -m pip install -r requirements.txt
```

### 5.2 Run the pipeline

```bash
python3 run_linkedin_pipeline.py
# optional: --backend ollama|cursor
```

```
data/…/messages.csv
        │
        ▼  scripts/stats.py
        ▼  scripts/dump_threads.py   → analysis/threads_dump.txt
        ▼  scripts/classify_threads.py → analysis/decisions.jsonl  (or Cursor handoff)
        ▼  scripts/apply_decisions.py  → output/latest/ → runs/<timestamp>/
```

### 5.3 Cursor backend only

If Ollama is unavailable and you choose Cursor: follow the agent handoff from `classify_threads.py` (or the **`job-search-extraction`** skill), write `analysis/decisions.jsonl`, then `python3 scripts/apply_decisions.py`.

### 5.4 Classification types

See shared criteria. Types include `agency_recruiter`, `inhouse_recruiter`, `hiring_manager`, `referral_network`, `outbound_application`, `company_rep`, `ats_system`.

---

## Phase 6 — Review & cross-check

1. Open `output/latest/recruiter_conversations_summary.csv`.
2. Sort by `Start Date` — confirm spike around layoff period if applicable.
3. Spot-check 10–15 rows: company and position match the thread content.
4. Compare with Gmail:

   | Channel | File | Metric |
   |---------|------|--------|
   | LinkedIn | `output/latest/recruiter_conversations_summary.csv` | row count |
   | Gmail | `gmail/output/latest/recruiter_conversations_report.csv` | distinct `thread_id` where kept |

5. Note overlaps (same company on both channels) if useful.

Re-run prep after config changes:

```bash
python3 run_linkedin_pipeline.py --skip-stats   # or full re-run
```

---

## Guided path

Invoke the **`job-search-extraction`** skill for interview → config → LinkedIn export → pipeline → outputs.

> Use job-search-extraction to walk me through LinkedIn message extraction.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No messages.csv found` | Unzip export under `linkedin/data/`; check folder name |
| `Missing participant.yaml` | From repo root: `cp config/participant.example.yaml config/participant.yaml` |
| Outbound count is 0 | Fix `linkedin.display_name` — must match `FROM` when you send |
| Keyword pre-screen much lower than expected | Normal if window is narrow or job-search was mostly email |
| Multiline message parsing errors | Use provided scripts (they use Python `csv` module) |
| `ModuleNotFoundError: yaml` | `pip install -r requirements.txt` |
| threads_dump.txt huge | Expected — classification is per-conversation, not per-message |

---

## Checklist (printable)

```
Phase 1 — Prepare
[ ] Date window documented (match Gmail if applicable)
[ ] LinkedIn display name confirmed from messages.csv

Phase 2 — LinkedIn export
[ ] Requested archive with Messages
[ ] Download link received (may take up to 24h)
[ ] messages.csv located in zip

Phase 3 — Place data
[ ] Unzipped to linkedin/data/Complete_LinkedInDataExport_*/
[ ] wc -l messages.csv looks reasonable

Phase 4 — Configure
[ ] config/participant.yaml filled in (repo root)
[ ] linkedin.display_name verified

Phase 5 — Prep & classify
[ ] pip install -r requirements.txt
[ ] run_linkedin_pipeline.py completed
[ ] threads_dump.txt reviewed / classified via Cursor
[ ] output/latest/recruiter_conversations_summary.md produced

Phase 6 — Review
[ ] Spot-checked output/latest/recruiter_conversations_summary.csv
[ ] Compared counts with Gmail export
[ ] Deliverables saved / shared as needed
```

---

## Related work

- **Gmail emails:** `gmail/docs/GMAIL_EXTRACTION_WORKFLOW.md`
- **Classification rules:** [classification_criteria.md](classification_criteria.md)
