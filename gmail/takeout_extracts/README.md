# Google Takeout extracts (local only)

Place each unzipped Takeout folder here, e.g.:

```
gmail/takeout_extracts/
  takeout-20260308T120000Z-3-001/
    Takeout/Mail/<label>.mbox
```

Then from `gmail/`:

```bash
python3 run_gmail_pipeline.py
```

- **One** folder with an `.mbox` → used automatically
- **Several** → pass the path: `python3 run_gmail_pipeline.py takeout_extracts/<folder>/`
- Contents of this directory are gitignored (not committed)
