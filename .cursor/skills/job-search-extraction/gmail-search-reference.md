# Gmail Search Reference

## Core query (default window)

Inclusive window: **2025-01-01** – **2026-01-01**. Gmail `before:` is exclusive → use `before:2026/1/2`.

```
after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*)
```

`recruit*` is a Gmail suffix wildcard (recruiter, recruiting, recruitment, …).

Adjust `before:` for participants with later end dates (e.g. through Jun 30 2026 → `before:2026/7/1`).

## Optional noise exclusions

Subtract common alert/newsletter noise (add more `-from:` domains as needed):

```
after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit*) -digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com
```

Avoid `-unsubscribe` (many real recruiter/ATS threads include it). Use `-category:promotions` sparingly — some recruiter mail lands there.

Prefer over-including in Gmail; the pipeline classifier drops digests and newsletters later.

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
| `-digest -newsletter` | Exclude common bulk noise |
| `from:recruiter@company.com` | Specific sender (supplemental) |
| `-label:spam` | Exclude spam label |

## Label operators

| Pattern | Use |
|---------|-----|
| `label:job_opportunities` | All labeled mail |
| `label:job_opportunities after:2025/1/1 before:2026/1/2` | Verification pass |

## Optional expanded search (if recall too low)

```
after:2025/1/1 before:2026/1/2 (job OR role OR position OR recruit* OR interview OR application OR "phone screen" OR offer)
```

Warn participants this increases noise and labeling work.

## Gmail UI labeling shortcuts

- **x** — select conversation
- **l** — apply label
- **Shift + l** — apply last-used label (fast for batch work)

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
