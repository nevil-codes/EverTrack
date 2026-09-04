"""PostgreSQL backend, on psycopg 3 and hand-written SQL.

Same interface, same behaviour as the SQLite backend — the contract test suite
runs against both. The schema is created by the migrations in migrations/, not
by this module: a service should not be silently reshaping its own database at
start-up.
"""
from __future__ import annotations

import json

import psycopg
from psycopg.rows import dict_row

from core.models import Habit, LogEntry, ValidationError
from core.repository import Repository, default_settings

VALID_STATUS = ("active", "paused", "archived")


class PostgresRepository(Repository):
    def __init__(self, url: str):
        self.url = url
        # autocommit + explicit transaction() blocks. Without autocommit, the
        # first read opens an implicit transaction, every later transaction()
        # block becomes a nested savepoint, and nothing is committed until the
        # connection is closed — which silently discarded writes.
        self.connection = psycopg.connect(url, row_factory=dict_row, autocommit=True)

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _habit_from_row(row) -> Habit:
        return Habit(
            id=row["id"],
            name=row["name"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            daily_target_min=row["daily_target_min"],
            status=str(row["status"]).title(),
        )

    @staticmethod
    def _log_from_row(row) -> LogEntry:
        return LogEntry(
            id=row["id"],
            log_date=row["log_date"],
            habit=row["habit"],
            duration_min=float(row["duration_min"]),
            completed=row["completed"],
            notes=row["notes"],
        )

    def _habit_id(self, name: str) -> int | None:
        row = self.connection.execute(
            "SELECT id FROM habit WHERE lower(name) = lower(%s)", (name,)
        ).fetchone()
        return row["id"] if row else None

    # ----------------------------------------------------------------- habits

    def list_habits(self) -> list[Habit]:
        rows = self.connection.execute("SELECT * FROM habit ORDER BY id").fetchall()
        return [self._habit_from_row(row) for row in rows]

    def add_habit(self, habit: Habit) -> Habit:
        status = habit.status.strip().lower()
        if status not in VALID_STATUS:
            raise ValidationError(f"status must be one of {VALID_STATUS}, got {habit.status!r}")
        try:
            with self.connection.transaction():
                row = self.connection.execute(
                    """INSERT INTO habit (name, start_date, end_date, daily_target_min, status)
                       VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                    (habit.name, habit.start_date, habit.end_date, habit.daily_target_min, status),
                ).fetchone()
        except psycopg.errors.UniqueViolation as exc:
            raise ValidationError(f"a habit named {habit.name!r} already exists") from exc
        except psycopg.errors.CheckViolation as exc:
            raise ValidationError(f"habit rejected by the database: {exc}") from exc
        return self._habit_from_row(row)

    def delete_habit(self, name: str) -> bool:
        with self.connection.transaction():
            cursor = self.connection.execute(
                "DELETE FROM habit WHERE lower(name) = lower(%s)", (name,)
            )
        return cursor.rowcount > 0

    # ------------------------------------------------------------------- logs

    def list_logs(self) -> list[LogEntry]:
        rows = self.connection.execute(
            """SELECT l.id, l.log_date, h.name AS habit, l.duration_min, l.completed, l.notes
               FROM habit_log l JOIN habit h ON h.id = l.habit_id
               ORDER BY l.id"""
        ).fetchall()
        return [self._log_from_row(row) for row in rows]

    def add_log(self, entry: LogEntry) -> LogEntry:
        habit_id = self._habit_id(entry.habit)
        if habit_id is None:
            raise ValidationError(f"no habit named {entry.habit!r} — create it first")
        try:
            with self.connection.transaction():
                row = self.connection.execute(
                    """INSERT INTO habit_log (habit_id, log_date, duration_min, completed, notes)
                       VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                    (habit_id, entry.log_date, float(entry.duration_min),
                     entry.completed, entry.notes or ""),
                ).fetchone()
        except psycopg.errors.CheckViolation as exc:
            raise ValidationError(f"log entry rejected by the database: {exc}") from exc
        return LogEntry(
            id=row["id"],
            log_date=entry.log_date,
            habit=entry.habit,
            duration_min=float(entry.duration_min),
            completed=entry.completed,
            notes=entry.notes or "",
        )

    def delete_log(self, log_id: int) -> bool:
        with self.connection.transaction():
            cursor = self.connection.execute("DELETE FROM habit_log WHERE id = %s", (log_id,))
        return cursor.rowcount > 0

    # --------------------------------------------------------------- settings

    def get_settings(self) -> dict:
        settings = default_settings()
        for row in self.connection.execute("SELECT key, value FROM setting").fetchall():
            settings[row["key"]] = row["value"]

        settings["reminder_times"] = {
            row["name"]: row["time_hhmm"]
            for row in self.connection.execute(
                """SELECT h.name, r.time_hhmm FROM reminder r
                   JOIN habit h ON h.id = r.habit_id
                   WHERE r.enabled"""
            ).fetchall()
        }
        return settings

    def save_settings(self, settings: dict) -> None:
        reminders = settings.get("reminder_times", {}) or {}
        with self.connection.transaction():
            for key, value in settings.items():
                if key == "reminder_times":
                    continue
                self.connection.execute(
                    """INSERT INTO setting (key, value) VALUES (%s, %s)
                       ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value""",
                    (key, json.dumps(value)),
                )

            self.connection.execute("DELETE FROM reminder")
            for habit_name, time_hhmm in reminders.items():
                habit_id = self._habit_id(habit_name)
                if habit_id is None:
                    continue  # the foreign key is the point; orphans are dropped
                self.connection.execute(
                    "INSERT INTO reminder (habit_id, time_hhmm) VALUES (%s, %s)",
                    (habit_id, time_hhmm),
                )

    # ----------------------------------------------------------- achievements

    def get_unlocked(self) -> list[str]:
        rows = self.connection.execute(
            "SELECT code FROM achievement_unlock ORDER BY unlocked_at, code"
        ).fetchall()
        return [row["code"] for row in rows]

    def set_unlocked(self, codes: list[str]) -> None:
        with self.connection.transaction():
            for code in codes:
                self.connection.execute(
                    "INSERT INTO achievement_unlock (code) VALUES (%s) ON CONFLICT DO NOTHING",
                    (code,),
                )
            self.connection.execute(
                "DELETE FROM achievement_unlock WHERE NOT (code = ANY(%s))", (list(codes),)
            )

    # -------------------------------------------------------------- lifecycle

    def clear_all(self) -> None:
        with self.connection.transaction():
            self.connection.execute("TRUNCATE habit_log, reminder, habit RESTART IDENTITY CASCADE")
            self.connection.execute("DELETE FROM achievement_unlock")

    def close(self) -> None:
        if not self.connection.closed:
            self.connection.close()
