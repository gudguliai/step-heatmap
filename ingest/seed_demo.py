#!/usr/bin/env python3
"""Seed the SQLite DB with realistic demo data so the app shows a full
heatmap before real Apple Health data flows in.

Usage:
    python3 seed_demo.py [--db PATH] [--days 365] [--seed 42]
"""
import argparse
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

DEFAULT_DB = Path(__file__).parent / "steps.db"


def gen_steps(rng: random.Random) -> int:
    """Realistic step count: weekday-active, occasional rest/very-high days."""
    roll = rng.random()
    if roll < 0.08:      # rest / sick day
        return rng.randint(0, 2500)
    if roll < 0.30:      # low activity
        return rng.randint(2501, 5000)
    if roll < 0.70:      # normal
        return rng.randint(5001, 9999)
    if roll < 0.92:      # solid 10K+
        return rng.randint(10000, 14999)
    return rng.randint(15000, 22000)  # big day


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    today = date.today()
    start = today - timedelta(days=args.days - 1)

    conn = sqlite3.connect(args.db)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS steps (
            date TEXT PRIMARY KEY,
            count INTEGER NOT NULL,
            source TEXT NOT NULL DEFAULT 'demo',
            updated_at TEXT NOT NULL
        )"""
    )
    now = date.today().isoformat()
    cur = conn.cursor()
    cur.executemany(
        """INSERT INTO steps (date, count, source, updated_at) VALUES (?, ?, 'demo', ?)
           ON CONFLICT(date) DO UPDATE SET
               count = excluded.count,
               source = 'demo',
               updated_at = excluded.updated_at""",
        [
            ((start + timedelta(days=i)).isoformat(), gen_steps(rng), now)
            for i in range(args.days)
        ],
    )
    conn.commit()
    conn.close()
    print(f"Seeded {args.days} demo days from {start} to {today} in {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
