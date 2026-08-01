#!/usr/bin/env python3
"""Ingest step data pasted directly into chat (stdin).

Accepts one of:
  - a bare number per line:       9876        -> stamped with today's date
  - a date,count line:            2026-08-01,9876
  - 'date count' or 'date: count' -> same as comma form

Usage:
    python3 ingest_dump.py [--db PATH]
    then: python3 ingest/export_json.py   (regenerates steps.json)
"""
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "steps.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS steps (
    date TEXT PRIMARY KEY,
    count INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    updated_at TEXT NOT NULL
);
"""

LINE_RE = re.compile(
    r"^\s*(?:(\d{4}-\d{2}-\d{2})\s*[,:=\s]\s*)?(\d+)\s*$"
)


def parse_line(line: str):
    """Return (date_str, count) or None."""
    m = LINE_RE.match(line)
    if not m:
        return None
    d, c = m.group(1), int(m.group(2))
    if d is None:
        d = date.today().isoformat()
    else:
        # validate the date parses
        try:
            date.fromisoformat(d)
        except ValueError:
            return None
    return d, c


def main() -> int:
    ap = __import__("argparse").ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    rows = []
    skipped = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parsed = parse_line(line)
        if parsed:
            rows.append(parsed)
        else:
            skipped.append(line)

    if not rows:
        print("No valid step entries found.")
        if skipped:
            print("Unparsed:", skipped)
        return 1

    conn = sqlite3.connect(args.db)
    conn.execute(SCHEMA)
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO steps (date, count, source, updated_at)
           VALUES (?, ?, 'manual', ?)
           ON CONFLICT(date) DO UPDATE SET
               count = excluded.count,
               source = 'manual',
               updated_at = excluded.updated_at""",
        [(d, c, now) for d, c in rows],
    )
    conn.commit()
    conn.close()

    days = sorted({d for d, _ in rows})
    print(f"Added {len(rows)} day(s) ({days[0]} .. {days[-1]}).")
    if skipped:
        print("Unparsed:", skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
