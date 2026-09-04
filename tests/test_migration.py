"""The migration is the piece that touches real user data, so it is tested on
the exact shapes the committed JSON files actually contained."""
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from migrate_json_to_sqlite import migrate  # noqa: E402

# The three log shapes that were all present in the original habits_data.json:
# float duration without notes, int duration, float duration with notes.
LOGS = [
    {"date": "2025-12-21", "habit": "maths", "duration": 23.0, "completed": True},
    {"date": "2025-12-21", "habit": "Meditation", "duration": 30, "completed": True},
    {"date": "2025-12-21", "habit": "Meditation", "duration": 25.0, "completed": True, "notes": ""},
]
HABITS = [
    {"name": "maths", "start_date": "2025-12-21", "end_date": "No Limit",
     "daily_target": 30, "status": "Active"},
    {"name": "Meditation", "start_date": "2025-12-21", "end_date": "No Limit",
     "daily_target": 30, "status": "Active"},
]
SETTINGS = {"theme": "dark", "notifications": True,
            "reminder_times": {"new habit": "17:46"}}  # orphan, as committed
ACHIEVEMENTS = {"unlocked": ["first_log", "perfect_day"], "total_points": 40}


@pytest.fixture
def source(tmp_path):
    (tmp_path / "habits_data.json").write_text(json.dumps(LOGS))
    (tmp_path / "habits_list.json").write_text(json.dumps(HABITS))
    (tmp_path / "settings.json").write_text(json.dumps(SETTINGS))
    (tmp_path / "achievements.json").write_text(json.dumps(ACHIEVEMENTS))
    return tmp_path


def run(source, tmp_path, **kwargs):
    database = tmp_path / "evertrack.db"
    options = {"replace": False, "create_missing_habits": False, "dry_run": False}
    options.update(kwargs)
    return migrate(source, database, **options), database


def rows(database, sql):
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(sql)]
    finally:
        connection.close()


def test_migrates_every_record(source, tmp_path):
    report, database = run(source, tmp_path)

    assert (report.habits, report.logs) == (2, 3)
    assert len(rows(database, "SELECT * FROM habit")) == 2
    assert len(rows(database, "SELECT * FROM habit_log")) == 3


def test_no_limit_becomes_null(source, tmp_path):
    _, database = run(source, tmp_path)
    assert all(row["end_date"] is None for row in rows(database, "SELECT end_date FROM habit"))


def test_int_and_float_durations_both_land_as_real(source, tmp_path):
    _, database = run(source, tmp_path)
    durations = sorted(row["duration_min"] for row in rows(database, "SELECT duration_min FROM habit_log"))
    assert durations == [23.0, 25.0, 30.0]
    assert all(isinstance(d, float) for d in durations)


def test_missing_notes_become_empty_strings(source, tmp_path):
    _, database = run(source, tmp_path)
    assert all(row["notes"] == "" for row in rows(database, "SELECT notes FROM habit_log"))


def test_logs_are_linked_to_their_habit_by_id(source, tmp_path):
    _, database = run(source, tmp_path)
    linked = rows(database, """SELECT h.name, COUNT(*) AS n FROM habit_log l
                               JOIN habit h ON h.id = l.habit_id GROUP BY h.name ORDER BY h.name""")
    # habit.name is COLLATE NOCASE, so "maths" sorts before "Meditation"
    assert linked == [{"name": "maths", "n": 1}, {"name": "Meditation", "n": 2}]


def test_orphan_reminder_is_reported_and_dropped(source, tmp_path):
    report, database = run(source, tmp_path)

    assert report.dropped_reminders == ["new habit at 17:46"]
    assert rows(database, "SELECT * FROM reminder") == []


def test_derived_points_are_not_migrated(source, tmp_path):
    report, database = run(source, tmp_path)

    assert report.achievements == 2
    assert {row["code"] for row in rows(database, "SELECT code FROM achievement_unlock")} == {
        "first_log", "perfect_day"}
    # total_points was stored data that could drift; it is derived now
    assert "total_points" not in {row["key"] for row in rows(database, "SELECT key FROM setting")}


def test_orphan_logs_are_reported_and_skipped(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps(HABITS))
    (source / "habits_data.json").write_text(json.dumps(
        LOGS + [{"date": "2025-12-22", "habit": "ghost", "duration": 10, "completed": True}]))

    report, database = run(source, tmp_path)

    assert report.logs == 3
    assert len(report.orphan_logs) == 1
    assert "ghost" in report.orphan_logs[0]


def test_orphan_logs_can_be_adopted(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps(HABITS))
    (source / "habits_data.json").write_text(json.dumps(
        LOGS + [{"date": "2025-12-22", "habit": "ghost", "duration": 10, "completed": True}]))

    report, database = run(source, tmp_path, create_missing_habits=True)

    assert report.logs == 4
    assert report.habits == 3
    assert report.orphan_logs == []


def test_unusable_rows_are_reported_not_written(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps(HABITS))
    (source / "habits_data.json").write_text(json.dumps(
        LOGS + [{"date": "21-12-2025", "habit": "maths", "duration": 10}]))

    report, database = run(source, tmp_path)

    assert report.logs == 3
    assert any("not an ISO date" in problem for problem in report.rejected)


def test_refuses_to_overwrite_an_existing_database(source, tmp_path):
    run(source, tmp_path)
    with pytest.raises(SystemExit, match="already exists"):
        run(source, tmp_path)


def test_replace_rebuilds_and_stays_idempotent(source, tmp_path):
    first, database = run(source, tmp_path)
    second, _ = run(source, tmp_path, replace=True)

    assert (first.habits, first.logs) == (second.habits, second.logs)
    assert len(rows(database, "SELECT * FROM habit_log")) == 3


def test_dry_run_writes_nothing(source, tmp_path):
    report, database = run(source, tmp_path, dry_run=True)

    assert report.logs == 3
    assert not database.exists()
