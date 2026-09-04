#!/usr/bin/env python3
"""Fill a database with a few weeks of plausible activity.

For demos, screenshots and CI smoke tests — never for real data.

    python scripts/seed_demo_data.py --database demo.db
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.models import Habit, LogEntry, ValidationError  # noqa: E402
from core.sqlite_repository import SqliteRepository  # noqa: E402

HABITS = [("Reading", 30), ("Meditation", 15), ("Exercise", 45), ("Coding", 60)]


def seed(database: Path, days: int = 45, seed_value: int = 7) -> tuple[int, int]:
    random.seed(seed_value)
    repository = SqliteRepository(database)
    today = date.today()
    habits = logs = 0

    for name, target in HABITS:
        try:
            repository.add_habit(
                Habit(name=name, start_date=today - timedelta(days=days), daily_target_min=target)
            )
            habits += 1
        except ValidationError:
            pass  # already seeded

    for offset in range(days, -1, -1):
        day = today - timedelta(days=offset)
        for name, target in HABITS:
            if random.random() < 0.55:
                continue
            duration = max(5, round(random.gauss(target, target * 0.3)))
            repository.add_log(LogEntry(
                log_date=day, habit=name, duration_min=float(min(duration, 1440)),
                completed=random.random() > 0.15,
            ))
            logs += 1

    repository.close()
    return habits, logs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database", type=Path, default=Path("demo.db"))
    parser.add_argument("--days", type=int, default=45)
    args = parser.parse_args(argv)

    habits, logs = seed(args.database, args.days)
    print(f"seeded {habits} habits and {logs} log entries into {args.database}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
