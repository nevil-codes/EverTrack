from datetime import date

import pytest

from core.models import Habit, LogEntry, ValidationError, load_logs

RAW_HABIT = {
    "name": "Meditation",
    "start_date": "2025-12-21",
    "end_date": "No Limit",
    "daily_target": 30,
    "status": "Active",
}


def test_habit_round_trips_the_on_disk_shape():
    assert Habit.from_dict(RAW_HABIT).to_dict() == RAW_HABIT


def test_no_limit_sentinel_becomes_none():
    assert Habit.from_dict(RAW_HABIT).end_date is None


def test_real_end_date_is_parsed():
    habit = Habit.from_dict({**RAW_HABIT, "end_date": "2026-01-31"})
    assert habit.end_date == date(2026, 1, 31)


@pytest.mark.parametrize(
    "override",
    [
        {"end_date": "asdf"},              # regression: unvalidated in the live path
        {"daily_target": 0},
        {"daily_target": "thirty"},
        {"name": "   "},
        {"start_date": "21-12-2025"},
        {"end_date": "2025-01-01"},        # before start_date
    ],
)
def test_bad_habit_records_are_rejected(override):
    with pytest.raises(ValidationError):
        Habit.from_dict({**RAW_HABIT, **override})


def test_missing_field_names_itself():
    raw = dict(RAW_HABIT)
    del raw["daily_target"]
    with pytest.raises(ValidationError, match="daily_target"):
        Habit.from_dict(raw)


def test_status_is_compared_case_insensitively():
    assert Habit.from_dict({**RAW_HABIT, "status": "active"}).is_active


def test_log_entry_defaults_notes_when_absent():
    entry = LogEntry.from_dict({"date": "2025-12-21", "habit": "Meditation", "duration": 30})
    assert entry.notes == ""
    assert entry.completed is True
    assert entry.to_dict()["notes"] == ""


def test_log_entry_accepts_int_and_float_durations():
    assert LogEntry.from_dict({"date": "2025-12-21", "habit": "h", "duration": 23.0}).duration_min == 23.0
    assert LogEntry.from_dict({"date": "2025-12-21", "habit": "h", "duration": 30}).duration_min == 30.0


@pytest.mark.parametrize("duration", [0, -5, 24 * 60 + 1])
def test_bad_durations_are_rejected(duration):
    with pytest.raises(ValidationError):
        LogEntry(log_date=date(2025, 12, 21), habit="h", duration_min=duration)


def test_load_logs_keeps_good_rows_and_reports_bad_ones():
    report = load_logs([
        {"date": "2025-12-21", "habit": "Meditation", "duration": 30},
        {"date": "not-a-date", "habit": "Meditation", "duration": 30},
        {"habit": "Meditation", "duration": 30},
    ])
    assert len(report.records) == 1
    assert len(report.rejected) == 2
    assert report.ok is False
