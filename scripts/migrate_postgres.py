#!/usr/bin/env python3
"""Apply the SQL migrations in migrations/ to a PostgreSQL database.

Plain .sql files, applied in filename order, each in its own transaction, each
recorded in schema_migrations so it is applied exactly once.

    python scripts/migrate_postgres.py --status
    python scripts/migrate_postgres.py --dry-run
    python scripts/migrate_postgres.py            # uses $EVERTRACK_DATABASE_URL
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"

TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    checksum    TEXT        NOT NULL,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def discover(directory: Path = MIGRATIONS_DIR) -> list[Path]:
    return sorted(directory.glob("*.sql"))


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def applied(connection) -> dict[str, str]:
    connection.execute(TRACKING_TABLE)
    connection.commit()
    return {
        row[0]: row[1]
        for row in connection.execute("SELECT version, checksum FROM schema_migrations").fetchall()
    }


def migrate(url: str, *, dry_run: bool = False, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Apply everything not yet applied. Returns the versions applied."""
    done: list[str] = []
    with psycopg.connect(url) as connection:
        already = applied(connection)

        for path in discover(directory):
            version = path.stem
            digest = checksum(path)

            if version in already:
                if already[version] != digest:
                    raise SystemExit(
                        f"{path.name} has changed since it was applied "
                        f"({already[version]} -> {digest}). Migrations are immutable: "
                        f"add a new file instead."
                    )
                continue

            if dry_run:
                done.append(version)
                continue

            with connection.transaction():
                connection.execute(path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                    (version, digest),
                )
            done.append(version)
    return done


def status(url: str, directory: Path = MIGRATIONS_DIR) -> list[tuple[str, bool]]:
    with psycopg.connect(url) as connection:
        already = applied(connection)
    return [(path.stem, path.stem in already) for path in discover(directory)]


def database_url(argument: str | None) -> str:
    url = argument or os.environ.get("EVERTRACK_DATABASE_URL")
    if not url:
        raise SystemExit(
            "no database URL: pass --database-url or set EVERTRACK_DATABASE_URL, e.g.\n"
            "  postgresql://evertrack:evertrack@localhost:5432/evertrack"
        )
    return url


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--status", action="store_true", help="list migrations and whether each is applied")
    parser.add_argument("--dry-run", action="store_true", help="report what would be applied")
    args = parser.parse_args(argv)

    url = database_url(args.database_url)

    if args.status:
        for version, is_applied in status(url):
            print(f"[{'x' if is_applied else ' '}] {version}")
        return 0

    versions = migrate(url, dry_run=args.dry_run)
    verb = "would apply" if args.dry_run else "applied"
    print(f"{verb} {len(versions)} migration(s)" + (": " + ", ".join(versions) if versions else ""))
    if not versions:
        print("database is up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
