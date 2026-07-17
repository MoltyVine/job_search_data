# Job-search extraction troubleshooting

## Gmail search returns too many results

- Standard query already includes: `-digest -newsletter -"new jobs for" -"jobs you may like" -from:quora.com`
- Add more `-from:` for known alert domains; avoid `-unsubscribe`
- Still select-all label each search page; noise is OK — the classifier filters later

## Gmail search returns too few results

- Widen: add `interview`, `application`, `offer`
- Check date range — `before:` is exclusive
- Search individual terms: `after:2025/1/1 before:2026/1/2 interview`

## Labeled count much higher than expected filtered output

Normal. Manual labeling casts a wide net; classification drops bulk digests and single-message blasts by design. Spot-check the Gmail report CSV if counts feel too low.

## Labeled count much lower than expected

- Re-run broader Gmail search without label filter
- Compare to LinkedIn conversation count if available
- Check if mail lives in a non-primary account

## Takeout missing messages

- Takeout only exports **labeled** threads
- Re-run verification: `label:<name> after:… before:…`
- Takeout can take hours; wait for completion email

## Pipeline: No / multiple takeout folders

```bash
cd gmail
# put unzipped export in takeout_extracts/, or:
python3 run_gmail_pipeline.py takeout_extracts/takeout-YYYYMMDD/
```

## Pipeline: Multiple mbox files found

```bash
cd gmail
python3 run_gmail_pipeline.py takeout_extracts/takeout-YYYYMMDD/ \
  --mbox takeout_extracts/takeout-YYYYMMDD/Takeout/Mail/job_opportunities.mbox
```

## Pipeline: Missing participant.yaml

Re-run the interview in **job-search-extraction**, or from repo root:

```bash
cp config/participant.example.yaml config/participant.yaml
```

## False positives in output

1. Open `gmail/output/latest/recruiter_conversations_report.csv` or LinkedIn `output/latest/` summary
2. Note noisy senders / threads
3. Fix bad LLM calls by editing `analysis/decisions.jsonl`, then re-run `scripts/apply_decisions.py` (Gmail needs `--emails-dir`)

## False negatives in output

1. Confirm the thread was labeled (Gmail) or falls in the search window (LinkedIn)
2. Check `analysis/threads_dump.txt` and `analysis/decisions.jsonl`
3. Re-classify or manually set `include: true` and re-apply

## LinkedIn export

| Problem | Fix |
|---------|-----|
| Export email not arrived | Wait up to 24h; check spam; re-request |
| No messages.csv in zip | Re-request with Messages checked |
| Wrong file | Use `messages.csv` at export root, not learning/guide files |

## Privacy

- Never commit takeouts, `.mbox`, LinkedIn `data/`, `analysis/` / `output/` contents, or `config/participant.yaml` with real PII
- `.gitignore` excludes these by default
