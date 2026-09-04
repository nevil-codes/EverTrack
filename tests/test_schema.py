"""The schema is meant to enforce integrity itself, not merely document it."""
import sqlite3

import pytest

from core.sqlite_repository import SqliteRepository


@pytest.fixture
def db(tmp_path):
    repo = SqliteRepository(tmp_path / "t.db")
    repo.connection.execute(
        "INSERT INTO habit (name, start_date, daily_target_min) VALUES ('Reading', '2026-09-01', 20)")
    repo.connection.commit()
    yield repo.connection
    repo.close()


def habit_id(db):
    return db.execute("SELECT id FROM habit WHERE name = 'Reading'").fetchone()["id"]


@pytest.mark.parametrize(
    "sql, params",
    [
        # duplicate name, case-insensitively
        ("INSERT INTO habit (name, start_date, daily_target_min) VALUES ('reading', '2026-09-01', 20)", ()),
        # non-positive target
        ("INSERT INTO habit (name, start_date, daily_target_min) VALUES ('X', '2026-09-01', 0)", ()),
        # malformed date
        ("INSERT INTO habit (name, start_date, daily_target_min) VALUES ('X', '01-09-2026', 20)", ()),
        # end before start
        ("INSERT INTO habit (name, start_date, end_date, daily_target_min) "
         "VALUES ('X', '2026-09-01', '2026-08-01', 20)", ()),
        # unknown status
        ("INSERT INTO habit (name, start_date, daily_target_min, status) "
         "VALUES ('X', '2026-09-01', 20, 'sleeping')", ()),
    ],
)
def test_habit_constraints(db, sql, params):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(sql, params)


def test_log_requires_an_existing_habit(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO habit_log (habit_id, log_date, duration_min) VALUES (999, '2026-09-04', 10)")


@pytest.mark.parametrize("duration", [0, -1, 1441])
def test_log_duration_bounds(db, duration):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO habit_log (habit_id, log_date, duration_min) VALUES (?, '2026-09-04', ?)",
                   (habit_id(db), duration))


def test_deleting_a_habit_cascades_to_logs_and_reminders(db):
    hid = habit_id(db)
    db.execute("INSERT INTO habit_log (habit_id, log_date, duration_min) VALUES (?, '2026-09-04', 20)", (hid,))
    db.execute("INSERT INTO reminder (habit_id, time_hhmm) VALUES (?, '09:00')", (hid,))
    db.commit()

    db.execute("DELETE FROM habit WHERE id = ?", (hid,))
    db.commit()

    assert db.execute("SELECT COUNT(*) c FROM habit_log").fetchone()["c"] == 0
    assert db.execute("SELECT COUNT(*) c FROM reminder").fetchone()["c"] == 0


def test_reminder_time_format_is_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO reminder (habit_id, time_hhmm) VALUES (?, '9:00')", (habit_id(db),))


def test_v_daily_rolls_up_per_day(db):
    hid = habit_id(db)
    db.executemany(
        "INSERT INTO habit_log (habit_id, log_date, duration_min, completed) VALUES (?, ?, ?, ?)",
        [(hid, "2026-09-04", 20, 1), (hid, "2026-09-04", 10, 0), (hid, "2026-09-03", 15, 1)],
    )
    db.commit()

    rows = {r["log_date"]: dict(r) for r in db.execute("SELECT * FROM v_daily")}
    assert rows["2026-09-04"]["activities"] == 2
    assert rows["2026-09-04"]["total_min"] == 30
    assert rows["2026-09-04"]["completed_count"] == 1
    assert rows["2026-09-03"]["total_min"] == 15


def test_v_habit_totals_includes_habits_with_no_logs(db):
    row = db.execute("SELECT * FROM v_habit_totals WHERE name = 'Reading'").fetchone()
    assert row["activities"] == 0
    assert row["total_min"] == 0
