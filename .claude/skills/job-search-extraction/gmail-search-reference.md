# Gmail Search Reference

## Standard query

Build from the participant’s **inclusive** search window. Gmail `before:` is **exclusive** → use the day after the inclusive end.

`is:read` assumes job-search threads of interest were opened (drop it if unread recruiter mail may matter). Noise exclusions are part of the **standard** query (smaller Takeout; classifier still filters leftovers):

```
is:read after:YYYY/M/D before:YYYY/M/D (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Example (inclusive window 2025-01-01 → 2026-01-01 → `before:2026/1/2`):

```
is:read after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

`recruit*` is a Gmail suffix wildcard (recruiter, recruiting, recruitment, …).

Avoid `-unsubscribe` (many real recruiter/ATS threads include it). Use `-category:promotions` sparingly — some recruiter mail lands there.

Add more `-from:` domains if the user knows specific alert senders. To cast a wider net, remove some `-…` terms or expand keywords (below).

## Date operators

| Operator | Meaning |
|----------|---------|
| `after:2025/1/1` | On or after Jan 1, 2025 |
| `before:2026/1/2` | Before Jan 2, 2026 (i.e. through Jan 1 inclusive) |
| `older_than:1y` | Avoid for this workflow — use explicit dates |

## Keyword operators

| Pattern | Matches |
|---------|---------|
| `job OR role OR position OR recruit*` | Core terms (+ recruit* wildcard) |
| `"phone screen"` | Exact phrase |
| `-digest -newsletter` | Standard bulk-noise exclusions |
| `from:recruiter@company.com` | Specific sender (supplemental) |
| `-label:spam` | Exclude spam label |

## Label operators

| Pattern | Use |
|---------|-----|
| `label:job_opportunities` | All labeled mail |
| `label:job_opportunities after:YYYY/M/D before:YYYY/M/D` | Verification pass |

## Expanded search (if recall too low)

Keep standard exclusions unless the user wants them removed:

```
is:read after:YYYY/M/D before:YYYY/M/D (job OR role OR position OR recruit* OR interview OR application OR "phone screen" OR offer) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Larger result set is fine: still **select all** per page; the classifier filters later.

## Gmail UI labeling (per search page)

1. Checkbox at top of the list → **select all** on this page (~50 conversations).
2. **Label** → your label (e.g. `job_opportunities`).
3. Next page → repeat until done.

Do not triage individual threads against classification criteria at this step.

## Takeout path after export

Typical unzip structure:

```
takeout-20260308T120000Z/
└── Takeout/
    └── Mail/
        └── job_opportunities.mbox
```

Place that folder under `gmail/takeout_extracts/`.

Label name in Takeout may differ slightly from Gmail UI (spaces → underscores).
