from datetime import date

import pyarrow as pa

from core.models import Habit, LogEntry
from pipeline.transform import (
    DIM_HABIT_SCHEMA,
    FACT_SCHEMA,
    build_dim_habit,
    build_fact_habit_log,
    habit_key,
    to_table,
)

MONDAY = date(2026, 9, 7)
SATURDAY = date(2026, 9, 5)


def habit(name="Reading", target=20, start=date(2026, 8, 1), status="Active", end=None):
    return Habit(name=name, start_date=start, daily_target_min=target, end_date=end, status=status)


def entry(name="Reading", day=MONDAY, duration=30.0, completed=True, notes=""):
    return LogEntry(log_date=day, habit=name, duration_min=duration, completed=completed, notes=notes)


def test_habit_key_folds_case_and_whitespace():
    assert habit_key("  Reading ") == habit_key("READING") == "reading"


def test_dim_habit_columns():
    row = build_dim_habit([habit()])[0]
    assert row["habit_key"] == "reading"
    assert row["habit_name"] == "Reading"
    assert row["is_active"] is True


def test_dim_habit_marks_archived_habits_inactive():
    assert build_dim_habit([habit(status="Archived")])[0]["is_active"] is False


def test_fact_derives_date_parts():
    row = build_fact_habit_log([entry(day=SATURDAY)], [habit()])[0]
    assert (row["year"], row["month"]) == (2026, 9)
    assert row["iso_week"] == SATURDAY.isocalendar().week
    assert row["weekday"] == 5
    assert row["is_weekend"] is True


def test_weekday_is_not_a_weekend():
    assert build_fact_habit_log([entry(day=MONDAY)], [habit()])[0]["is_weekend"] is False


def test_met_target():
    habits = [habit(target=30)]
    assert build_fact_habit_log([entry(duration=30.0)], habits)[0]["met_target"] is True
    assert build_fact_habit_log([entry(duration=29.5)], habits)[0]["met_target"] is False


def test_days_since_habit_start():
    row = build_fact_habit_log([entry(day=date(2026, 8, 11))], [habit(start=date(2026, 8, 1))])[0]
    assert row["days_since_habit_start"] == 10


def test_a_log_before_its_habit_started_is_negative_not_dropped():
    row = build_fact_habit_log([entry(day=date(2026, 7, 1))], [habit(start=date(2026, 8, 1))])[0]
    assert row["days_since_habit_start"] < 0


def test_fact_joins_case_insensitively():
    row = build_fact_habit_log([entry(name="reading")], [habit("Reading")])[0]
    assert row["habit_name"] == "Reading"
    assert row["daily_target_min"] == 20


def test_an_orphan_log_survives_transform_for_quality_to_catch():
    row = build_fact_habit_log([entry(name="Ghost")], [habit()])[0]
    assert row["habit_key"] == "ghost"
    assert row["daily_target_min"] is None
    assert row["met_target"] is None


def test_has_notes():
    assert build_fact_habit_log([entry(notes="  ")], [habit()])[0]["has_notes"] is False
    assert build_fact_habit_log([entry(notes="felt good")], [habit()])[0]["has_notes"] is True


def test_tables_use_the_declared_schema():
    fact = to_table(build_fact_habit_log([entry()], [habit()]), FACT_SCHEMA)
    dim = to_table(build_dim_habit([habit()]), DIM_HABIT_SCHEMA)

    assert fact.schema == FACT_SCHEMA
    assert dim.schema == DIM_HABIT_SCHEMA
    assert fact.column("log_date").type == pa.date32()
    assert fact.column("duration_min").type == pa.float64()


def test_an_empty_run_still_has_the_right_columns():
    empty = to_table([], FACT_SCHEMA)
    assert empty.num_rows == 0
    assert empty.schema == FACT_SCHEMA
