# Step Heatmap

A mobile-friendly heatmap of daily step counts, sourced from Apple Health.
Green = 10K+ steps, yellow = >5K, light red = <5K.

Live at: **https://gudguliai.github.io/step-heatmap/**

## How it works

```
iPhone (Shortcut automation, nightly)
    │  appends "YYYY-MM-DD,steps" to steps.csv in iCloud Drive
    ▼
Mac cron (nightly.sh, nightly)
    │  pull_steps.py  → SQLite (ingest/steps.db)
    │  export_json.py → app/public/steps.json
    ▼
git push to main
    ▼
GitHub Actions builds the React app and deploys to GitHub Pages
```

- **Storage:** SQLite on the Mac is the source of truth. GitHub Pages is
  static, so the JSON export is what the app actually fetches — committed to
  the repo and redeployed on each push.
- **Idempotent:** upserts by date; a nightly run with no new data makes no
  commit and no push.

## Setting up the iPhone → Mac data flow

macOS can't query HealthKit from a script (the data lives on the iPhone), so
the phone pushes it to iCloud Drive and the Mac ingests the file.

1. On the iPhone, create a **Shortcut** named e.g. `Log Steps`:
   - Add action **Find Health Samples** → *Step Count* → filter to *Today*
     (Start Date = Start of Today, End Date = End of Today)
   - Add action **Get Numbers from Input** (input: the health samples)
   - Add action **Calculate Statistics** → **Sum** (this is today's total)
   - Add action **Text** → insert the **Sum** magic variable (just the number —
     the Mac stamps the date, so no fragile date formatting needed)
   - Add action **Append to File** → iCloud Drive → folder `Steps` → file
     `steps.csv` → toggle **New Line Each Run: ON**
2. In **Automation** (Personal), add a time-based automation (e.g. 10 PM
   daily, or when charging) that runs that Shortcut.
3. First manual run: the Mac should then see the file at:
   `~/Library/Mobile Documents/com~apple~CloudDocs/Steps/steps.csv`
4. Test the pull: `python3 ingest/pull_steps.py`

The CSV rows can be either `YYYY-MM-DD,steps` or a bare `steps` number —
a bare number is stamped with today's date on the Mac.

### Health Auto Export alternative

If you prefer a dedicated app, [Health Auto Export](https://apps.apple.com/us/app/health-auto-export/id1115567069)
can write the same CSV to iCloud Drive on a schedule — point `pull_steps.py`
at that file instead (`--csv`).

## Local development

```bash
cd app
npm install
npm run dev        # http://localhost:5173/step-heatmap/
npm run build      # production build to app/dist/
```

Seed demo data (365 days of realistic steps) so the UI renders before real
data flows:

```bash
python3 ingest/seed_demo.py
python3 ingest/export_json.py
```

## Manual nightly run

```bash
./nightly.sh
```

## Colors / thresholds

| Range | Color |
|---|---|
| ≥ 10,000 steps | 🟩 green |
| 5,001 – 9,999 | 🟨 yellow |
| < 5,000 | 🟥 light red |
| no data | gray (dimmed) |
