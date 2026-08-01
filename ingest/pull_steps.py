#!/usr/bin/env python3
"""Pull step data from a CSV file (written by an iPhone Shortcut to iCloud Drive)
and upsert it into the local SQLite database.

CSV format: one `YYYY-MM-DD,steps` per line, optional header — OR a bare
`steps` number per line, in which case the Mac stamps today's date (this
avoids relying on iOS Shortcuts' buggy custom date formatting).
Default source: ~/Library/Mobile Documents/com~apple~CloudDocs/Steps/steps.csv
Override with --csv.

Usage:
    python3 pull_steps.py [--csv PATH] [--db PATH]
"""
import argparse
import csv
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_CSV = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Steps/steps.csv"
DEFAULT_DB = Path(__file__).parent / "steps.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS steps (
    date TEXT PRIMARY KEY,
    count INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'apple-health',
    updated_at TEXT NOT NULL
);
"""


def parse_row(raw_date: str, raw_count: str) -> Optional[Tuple[str, int]]:
    """Validate and normalize a (date, count) row. Returns None if invalid."""
    d = raw_date.strip()
    try:
        date.fromisoformat(d)
    except ValueError:
        return None
    try:
        c = int(float(raw_count.strip()))
    except ValueError:
        return None
    return d, max(c, 0)


def parse_line(line: str) -> Optional[Tuple[str, int]]:
    """Parse one CSV line. Accepts 'YYYY-MM-DD,steps' or a bare 'steps'
    (bare count gets today's date stamped by the Mac)."""
    parts = [p.strip() for p in line.split(",") if p.strip()]
    if not parts:
        return None
    if len(parts) == 1:
        try:
            c = int(float(parts[0]))
        except ValueError:
            return None
        return date.today().isoformat(), max(c, 0)
    return parse_row(parts[0], parts[1])


def upsert(conn: sqlite3.Connection, rows: list) -> int:
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO steps (date, count, source, updated_at)
           VALUES (?, ?, 'apple-health', ?)
           ON CONFLICT(date) DO UPDATE SET
               count = excluded.count,
               source = 'apple-health',
               updated_at = excluded.updated_at""",
        [(d, c, now) for d, c in rows],
    )
    conn.commit()
    return cur.rowcount


def read_csv(path: Path) -> list:
    if not path.exists():
        print(f"No CSV at {path} — nothing to pull (expected if Shortcut hasn't run yet).")
        return []
    rows: list = []
    with path.open(newline="") as f:
        for line in f:
            if not line.strip():
                continue
            parsed = parse_line(line)
            if parsed:
                rows.append(parsed)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV file to ingest")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    args = ap.parse_args()

    rows = read_csv(Path(args.csv))
    if not rows:
        return 0

    conn = sqlite3.connect(args.db)
    conn.execute(SCHEMA)
    upserted = upsert(conn, rows)
    conn.close()

    days = sorted({d for d, _ in rows})
    print(f"Ingested {len(rows)} rows from {args.csv} ({len(days)} unique days, "
          f"{upserted} upserted). Range: {days[0]} .. {days[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
