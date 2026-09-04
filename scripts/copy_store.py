#!/usr/bin/env python3
"""Copy everything from one backend to another.

Possible because both sides are just a core.repository.Repository:

    python scripts/copy_store.py --from evertrack.db \
        --to postgresql://evertrack:evertrack@localhost:5432/evertrack

The target must already have its schema (run scripts/migrate_postgres.py first)
and is expected to be empty; pass --wipe to clear it before copying.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.factory import describe, repository_from_url  # noqa: E402
from core.models import ValidationError  # noqa: E402


def copy(source_url: str, target_url: str, *, wipe: bool = False) -> dict:
    source = repository_from_url(source_url)
    target = repository_from_url(target_url)
    report = {"habits": 0, "logs": 0, "achievements": 0, "skipped": []}

    try:
        if wipe:
            target.clear_all()

        for habit in source.list_habits():
            try:
                target.add_habit(habit)
                report["habits"] += 1
            except ValidationError as exc:
                report["skipped"].append(f"habit {habit.name!r}: {exc}")

        for entry in source.list_logs():
            try:
                target.add_log(entry)
                report["logs"] += 1
            except ValidationError as exc:
                report["skipped"].append(f"log {entry.log_date} {entry.habit}: {exc}")

        target.save_settings(source.get_settings())

        unlocked = source.get_unlocked()
        target.set_unlocked(unlocked)
        report["achievements"] = len(unlocked)
    finally:
        source.close()
        target.close()

    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="source", required=True)
    parser.add_argument("--to", dest="target", required=True)
    parser.add_argument("--wipe", action="store_true", help="clear the target first")
    args = parser.parse_args(argv)

    report = copy(args.source, args.target, wipe=args.wipe)
    print(f"{describe(args.source)} -> {describe(args.target)}")
    print(f"copied {report['habits']} habits, {report['logs']} logs, "
          f"{report['achievements']} unlocked achievements")
    for problem in report["skipped"]:
        print(f"  skipped {problem}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
