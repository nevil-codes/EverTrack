#!/usr/bin/env python3
"""Migrate the JSON data files into a SQLite database.

Nothing is coerced silently. Rows that cannot be represented are reported and
skipped, and the script says exactly what it did:

    python scripts/migrate_json_to_sqlite.py --from . --to evertrack.db
    python scripts/migrate_json_to_sqlite.py --dry-run
    python scripts/migrate_json_to_sqlite.py --replace --create-missing-habits

Known shapes that need a decision, all handled here:
  * end_date "No Limit"      -> NULL
  * duration int or float    -> REAL
  * notes absent             -> ''
  * habit referenced by name -> foreign key to habit.id
  * logs naming a habit that was never created (orphans)
  * reminders for habits that no longer exist
  * achievements.total_points, which is derived and therefore dropped
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.json_repository import JsonRepository  # noqa: E402
from core.models import ValidationError  # noqa: E402
from core.sqlite_repository import SqliteRepository  # noqa: E402


@dataclass
class Report:
    habits: int = 0
    logs: int = 0
    reminders: int = 0
    achievements: int = 0
    settings: int = 0
    orphan_logs: list[str] = field(default_factory=list)
    dropped_reminders: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)

    def render(self, dry_run: bool) -> str:
        verb = "would migrate" if dry_run else "migrated"
        lines = [
            f"{verb} {self.habits} habits",
            f"{verb} {self.logs} log entries",
            f"{verb} {self.reminders} reminders",
            f"{verb} {self.achievements} unlocked achievements",
            f"{verb} {self.settings} settings",
        ]
        for label, items in (
            ("unusable records skipped", self.rejected),
            ("logs whose habit does not exist", self.orphan_logs),
            ("reminders for habits that do not exist", self.dropped_reminders),
        ):
            if items:
                lines.append(f"\n{len(items)} {label}:")
                lines.extend(f"  - {item}" for item in items[:20])
                if len(items) > 20:
                    lines.append(f"  ... and {len(items) - 20} more")
        return "\n".join(lines)


def migrate(source_dir: Path, database: Path, *, replace: bool,
            create_missing_habits: bool, dry_run: bool) -> Report:
    source = JsonRepository(source_dir)
    report = Report()

    if dry_run:
        target = SqliteRepository(":memory:")
    else:
        if database.exists() and not replace:
            raise SystemExit(
                f"{database} already exists. Re-run with --replace to rebuild it, "
                f"or choose another --to path."
            )
        if database.exists() and replace:
            database.unlink()
        target = SqliteRepository(database)

    habits = source.list_habits()
    logs = source.list_logs()
    report.rejected.extend(source.problems())

    known: set[str] = set()
    for habit in habits:
        try:
            target.add_habit(habit)
            known.add(habit.name.lower())
            report.habits += 1
        except ValidationError as exc:
            report.rejected.append(f"habit {habit.name!r}: {exc}")

    for entry in logs:
        if entry.habit.lower() not in known:
            if not create_missing_habits:
                report.orphan_logs.append(f"{entry.log_date} {entry.habit} ({entry.duration_min:g} min)")
                continue
            from core.models import Habit

            placeholder = Habit(name=entry.habit, start_date=entry.log_date, daily_target_min=30)
            try:
                target.add_habit(placeholder)
                known.add(entry.habit.lower())
                report.habits += 1
            except ValidationError as exc:
                report.rejected.append(f"could not create habit {entry.habit!r}: {exc}")
                continue
        try:
            target.add_log(entry)
            report.logs += 1
        except ValidationError as exc:
            report.rejected.append(f"log {entry.log_date} {entry.habit}: {exc}")

    settings = source.get_settings()
    reminders = settings.get("reminder_times", {}) or {}
    keep = {name: time for name, time in reminders.items() if name.lower() in known}
    report.dropped_reminders = [f"{name} at {time}" for name, time in reminders.items()
                                if name.lower() not in known]
    settings["reminder_times"] = keep
    target.save_settings(settings)
    report.reminders = len(keep)
    report.settings = len(settings) - 1  # reminder_times is stored separately

    unlocked = source.get_unlocked()
    target.set_unlocked(unlocked)
    report.achievements = len(unlocked)

    target.close()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="source", default=".", type=Path,
                        help="directory holding the JSON files (default: .)")
    parser.add_argument("--to", dest="database", default=Path("evertrack.db"), type=Path,
                        help="SQLite database to create (default: evertrack.db)")
    parser.add_argument("--replace", action="store_true",
                        help="delete an existing database and rebuild it")
    parser.add_argument("--create-missing-habits", action="store_true",
                        help="create a placeholder habit for logs that reference an unknown one")
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would happen, write nothing")
    args = parser.parse_args(argv)

    report = migrate(
        args.source, args.database,
        replace=args.replace,
        create_missing_habits=args.create_missing_habits,
        dry_run=args.dry_run,
    )
    print(report.render(args.dry_run))
    if not args.dry_run:
        print(f"\nwrote {args.database}")
        print("run the app against it with:  python main.py --storage sqlite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
