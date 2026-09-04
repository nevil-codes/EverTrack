"""Shape the operational records into an analytical model.

Two tables, both explicitly typed:

  dim_habit       one row per habit
  fact_habit_log  one row per logged activity, at log grain, denormalized with
                  the few habit attributes an analyst always wants and the date
                  parts that make partitioning and grouping cheap
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pyarrow as pa

from core.models import Habit, LogEntry

DIM_HABIT_SCHEMA = pa.schema([
    pa.field("habit_key", pa.string(), nullable=False),
    pa.field("habit_id", pa.int64()),
    pa.field("habit_name", pa.string(), nullable=False),
    pa.field("start_date", pa.date32(), nullable=False),
    pa.field("end_date", pa.date32()),
    pa.field("daily_target_min", pa.int32(), nullable=False),
    pa.field("status", pa.string(), nullable=False),
    pa.field("is_active", pa.bool_(), nullable=False),
])

FACT_SCHEMA = pa.schema([
    pa.field("log_id", pa.int64()),
    pa.field("habit_key", pa.string(), nullable=False),
    pa.field("habit_name", pa.string(), nullable=False),
    pa.field("log_date", pa.date32(), nullable=False),
    pa.field("year", pa.int32(), nullable=False),
    pa.field("month", pa.int32(), nullable=False),
    pa.field("iso_week", pa.int32(), nullable=False),
    pa.field("weekday", pa.int32(), nullable=False),
    pa.field("is_weekend", pa.bool_(), nullable=False),
    pa.field("duration_min", pa.float64(), nullable=False),
    pa.field("completed", pa.bool_(), nullable=False),
    pa.field("daily_target_min", pa.int32()),
    pa.field("met_target", pa.bool_()),
    pa.field("days_since_habit_start", pa.int32()),
    pa.field("has_notes", pa.bool_(), nullable=False),
])

PARTITION_COLUMNS = ["year", "month"]


def habit_key(name: str) -> str:
    """Stable join key. Habit names are unique case-insensitively, so the key is
    the folded name — it survives a rename of case and does not depend on an id
    that differs between backends."""
    return name.strip().lower()


def build_dim_habit(habits: list[Habit]) -> list[dict[str, Any]]:
    return [
        {
            "habit_key": habit_key(habit.name),
            "habit_id": habit.id,
            "habit_name": habit.name,
            "start_date": habit.start_date,
            "end_date": habit.end_date,
            "daily_target_min": habit.daily_target_min,
            "status": habit.status,
            "is_active": habit.is_active,
        }
        for habit in habits
    ]


def build_fact_habit_log(logs: list[LogEntry], habits: list[Habit]) -> list[dict[str, Any]]:
    by_key = {habit_key(habit.name): habit for habit in habits}
    rows = []

    for entry in logs:
        key = habit_key(entry.habit)
        habit = by_key.get(key)
        target = habit.daily_target_min if habit else None
        started = habit.start_date if habit else None

        rows.append({
            "log_id": entry.id,
            "habit_key": key,
            "habit_name": habit.name if habit else entry.habit,
            "log_date": entry.log_date,
            "year": entry.log_date.year,
            "month": entry.log_date.month,
            "iso_week": entry.log_date.isocalendar().week,
            "weekday": entry.log_date.weekday(),
            "is_weekend": entry.log_date.weekday() >= 5,
            "duration_min": float(entry.duration_min),
            "completed": bool(entry.completed),
            "daily_target_min": target,
            "met_target": None if target is None else entry.duration_min >= target,
            "days_since_habit_start": None if started is None else (entry.log_date - started).days,
            "has_notes": bool((entry.notes or "").strip()),
        })

    return rows


def to_table(rows: list[dict[str, Any]], schema: pa.Schema) -> pa.Table:
    """Rows to an Arrow table under a fixed schema.

    The schema is declared rather than inferred: an empty run still produces the
    right columns, and a type that drifts fails here instead of downstream.
    """
    columns = {
        field.name: pa.array([row.get(field.name) for row in rows], type=field.type)
        for field in schema
    }
    return pa.Table.from_pydict(columns, schema=schema)


def today() -> date:
    return date.today()
