# SalesRadar

Sales twin of JobRadar: same nightly scrape, same `latest.json` schema, but only the daily
dashboard of **sales / commercial vacancies**. No CV database, no matching, no Hookly,
no assistant, no pipeline, no contracts.

Lives in its own repo so it gets its own URL: `https://jobbybranch.github.io/salesradar/`

## What is in this folder

| file | what |
|---|---|
| `index.html` | the dashboard (static, no backend calls). Tabs: Dashboard, Bronnen. Blacklist is kept in the browser. |
| `.github/workflows/scrape.yml` | weekday 08:00 scan, commits `output/latest.json` — identical to JobRadar's except the name and `RADAR_PROFILE=sales` |
| `sales_profile.py` | the sales keyword pre-filter + Claude classification prompt that replaces the IT filter |
| `output/latest.json` | starts empty (`[]`); filled by the first scan |
| `state/` | scraper dedup state |

## What to copy from the JobRadar repo

These files are not included here — copy them from `JobbyBranch/Jobby` as-is:

- `scraper.py`
- `requirements.txt`
- `sources.yaml` (the career pages to scan — same list works, sales jobs are on the same pages)

Not needed: `harvest.py`, `discover.py`, `merge_sources.py`, `linkedin_signals.py` and the
`pipeline` / `harvest` / `discover` workflows. Copy those too only if you want SalesRadar to
grow its own source list from KBO every night.

## scraper.py — the one change

Where scraper.py decides whether a title is an IT job (keyword check + Claude prompt),
switch on `RADAR_PROFILE`:

```python
import os
if os.environ.get("RADAR_PROFILE") == "sales":
    from sales_profile import looks_like_sales as looks_relevant, CLASSIFY_PROMPT
else:
    # existing IT logic
```

- keyword pre-filter → `looks_like_sales(title)`
- classification prompt → `CLASSIFY_PROMPT` (returns `is_sales`, `role_type`, `tags`, `experience`, `in_belgium` as JSON)
- put `tags` in the `stack` field of each job — the dashboard shows that field as chips
- skip the candidate matching block entirely (`CANDIDATES_CSV_URL` is not set)
- use `state/seen_sales.json` for dedup so the two radars never share state

Upload `scraper.py` and I'll make this edit for you.

## Go live

1. GitHub → New repository → `salesradar` under **JobbyBranch**, public, empty.
2. Push this folder plus the three copied files to `main`.
3. Settings → Secrets and variables → Actions: add `ANTHROPIC_API_KEY` and (optional) `SLACK_WEBHOOK_URL`.
4. Settings → Pages → Source: *Deploy from a branch* → `main` / `/ (root)` → Save.
   After a minute the dashboard is at `https://jobbybranch.github.io/salesradar/`.
5. Actions → *SalesRadar daily scan* → **Run workflow** for the first scan. Every weekday
   morning after that runs by itself.
6. Hard-refresh the dashboard (Ctrl+Shift+R) once `output/latest.json` has been committed.

If you named the repo or org differently, change `LIVE_DATA_URL` at the top of `index.html`.

## Custom domain (optional)

Settings → Pages → Custom domain → e.g. `sales.jouwdomein.be`, then add a CNAME record at your
DNS provider pointing to `jobbybranch.github.io`.
