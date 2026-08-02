#!/usr/bin/env bash
# Nightly step sync: pull Apple Health CSV -> SQLite -> steps.json -> git push.
# Runs from cron; safe to re-run (idempotent upserts, no-op push when unchanged).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PY="python3"

echo "[$(date '+%F %T')] step-heatmap nightly sync"

# 1. Ingest any new rows from the iPhone Shortcut CSV (no-op if missing).
"$PY" ingest/pull_steps.py || echo "WARN: pull_steps failed (CSV may be missing)"

# 2. Regenerate the JSON the web app fetches.
"$PY" ingest/export_json.py

# 3. Commit + push if anything changed.
if git diff --quiet app/public/steps.json; then
  echo "No data change — nothing to push."
else
  git add app/public/steps.json
  git commit -m "nightly: update step data [$(date '+%F %T')]"
  git push origin main
  echo "Pushed updated step data."
fi
