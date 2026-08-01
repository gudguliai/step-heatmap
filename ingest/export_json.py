#!/usr/bin/env python3
"""Export the SQLite step database to the JSON file the web app fetches.

Writes app/public/steps.json as an array of {date, steps} objects, sorted
oldest-first. A "steps" of null means the day had no data (used for the
empty cell color instead of the <5K red).

Usage:
    python3 export_json.py [--db PATH] [--out PATH]
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "steps.db"
DEFAULT_OUT = Path(__file__).parent.parent / "app" / "public" / "steps.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path")
    args = ap.parse_args()

    out = Path(args.out)
    if not Path(args.db).exists():
        print(f"No DB at {args.db} — writing empty dataset.")
        payload = {"updated": None, "days": []}
    else:
        conn = sqlite3.connect(args.db)
        rows = conn.execute(
            "SELECT date, count FROM steps ORDER BY date"
        ).fetchall()
        updated = conn.execute(
            "SELECT MAX(updated_at) FROM steps"
        ).fetchone()[0]
        conn.close()
        payload = {
            "updated": updated,
            "days": [{"date": d, "steps": c} for d, c in rows],
        }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(f"Exported {len(payload['days'])} days to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
