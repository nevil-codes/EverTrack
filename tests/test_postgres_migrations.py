"""Migration runner. Skipped unless EVERTRACK_TEST_DATABASE_URL points at a
scratch PostgreSQL database (CI sets it)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

URL = os.environ.get("EVERTRACK_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="EVERTRACK_TEST_DATABASE_URL is not set")

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


@pytest.fixture
def fresh_database():
    import psycopg

    with psycopg.connect(URL, autocommit=True) as connection:
        connection.execute("DROP SCHEMA public CASCADE")
        connection.execute("CREATE SCHEMA public")
    yield URL


def test_migrations_apply_then_report_up_to_date(fresh_database):
    from migrate_postgres import migrate

    applied = migrate(fresh_database)
    assert applied == ["001_initial_schema"]
    assert migrate(fresh_database) == []


def test_status_reflects_what_has_run(fresh_database):
    from migrate_postgres import migrate, status

    assert status(fresh_database) == [("001_initial_schema", False)]
    migrate(fresh_database)
    assert status(fresh_database) == [("001_initial_schema", True)]


def test_dry_run_changes_nothing(fresh_database):
    from migrate_postgres import migrate, status

    assert migrate(fresh_database, dry_run=True) == ["001_initial_schema"]
    assert status(fresh_database) == [("001_initial_schema", False)]


def test_an_edited_migration_is_refused(fresh_database, tmp_path):
    """Applied migrations are immutable; editing one must not pass silently."""
    from migrate_postgres import migrate

    directory = tmp_path / "migrations"
    directory.mkdir()
    target = directory / "001_initial_schema.sql"
    target.write_text((MIGRATIONS / "001_initial_schema.sql").read_text())

    migrate(fresh_database, directory=directory)
    target.write_text(target.read_text() + "\n-- edited after the fact\n")

    with pytest.raises(SystemExit, match="has changed"):
        migrate(fresh_database, directory=directory)


def test_schema_objects_exist_after_migrating(fresh_database):
    import psycopg
    from migrate_postgres import migrate

    migrate(fresh_database)

    with psycopg.connect(fresh_database) as connection:
        tables = {row[0] for row in connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ).fetchall()}

    assert {"habit", "habit_log", "reminder", "achievement_unlock", "setting",
            "schema_migrations", "v_daily", "v_habit_totals"} <= tables
