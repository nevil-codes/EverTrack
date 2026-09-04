"""SQLite backend.

Constraints live in the schema (core/schema.sql), not only in Python: unique
habit names, foreign keys with ON DELETE CASCADE, and CHECKs on dates, targets
and durations. A bad row cannot reach the database even if a caller forgets to
validate it.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.dates import parse_iso, to_iso
from core.models import Habit, LogEntry, ValidationError
from core.repository import Repository, default_settings

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
VALID_STATUS = ("active", "paused", "archived")


class SqliteRepository(Repository):
    def __init__(self, database: str | Path = "evertrack.db"):
        self.path = Path(database)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.connection.commit()

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _habit_from_row(row: sqlite3.Row) -> Habit:
        return Habit(
            id=row["id"],
            name=row["name"],
            start_date=parse_iso(row["start_date"]),
            end_date=parse_iso(row["end_date"]) if row["end_date"] else None,
            daily_target_min=row["daily_target_min"],
            status=str(row["status"]).title(),
        )

    @staticmethod
    def _log_from_row(row: sqlite3.Row) -> LogEntry:
        return LogEntry(
            id=row["id"],
            log_date=parse_iso(row["log_date"]),
            habit=row["habit"],
            duration_min=row["duration_min"],
            completed=bool(row["completed"]),
            notes=row["notes"],
        )

    def _habit_id(self, name: str) -> int | None:
        row = self.connection.execute(
            "SELECT id FROM habit WHERE name = ? COLLATE NOCASE", (name,)
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
            cursor = self.connection.execute(
                """INSERT INTO habit (name, start_date, end_date, daily_target_min, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    habit.name,
                    to_iso(habit.start_date),
                    to_iso(habit.end_date) if habit.end_date else None,
                    habit.daily_target_min,
                    status,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if "habit_name_uq" in str(exc) or "UNIQUE" in str(exc).upper():
                raise ValidationError(f"a habit named {habit.name!r} already exists") from exc
            raise ValidationError(f"habit rejected by the database: {exc}") from exc
        self.connection.commit()
        return self._habit_from_row(
            self.connection.execute("SELECT * FROM habit WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )

    def delete_habit(self, name: str) -> bool:
        # habit_log and reminder rows go with it: ON DELETE CASCADE
        cursor = self.connection.execute(
            "DELETE FROM habit WHERE name = ? COLLATE NOCASE", (name,)
        )
        self.connection.commit()
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
            cursor = self.connection.execute(
                """INSERT INTO habit_log (habit_id, log_date, duration_min, completed, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (habit_id, to_iso(entry.log_date), float(entry.duration_min),
                 int(entry.completed), entry.notes or ""),
            )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"log entry rejected by the database: {exc}") from exc
        self.connection.commit()
        return LogEntry(
            id=cursor.lastrowid,
            log_date=entry.log_date,
            habit=entry.habit,
            duration_min=float(entry.duration_min),
            completed=entry.completed,
            notes=entry.notes or "",
        )

    def delete_log(self, log_id: int) -> bool:
        cursor = self.connection.execute("DELETE FROM habit_log WHERE id = ?", (log_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    # --------------------------------------------------------------- settings

    def get_settings(self) -> dict:
        settings = default_settings()
        for row in self.connection.execute("SELECT key, value FROM setting"):
            try:
                settings[row["key"]] = json.loads(row["value"])
            except json.JSONDecodeError:
                settings[row["key"]] = row["value"]

        settings["reminder_times"] = {
            row["name"]: row["time_hhmm"]
            for row in self.connection.execute(
                """SELECT h.name, r.time_hhmm FROM reminder r
                   JOIN habit h ON h.id = r.habit_id
                   WHERE r.enabled = 1"""
            )
        }
        return settings

    def save_settings(self, settings: dict) -> None:
        reminders = settings.get("reminder_times", {}) or {}
        with self.connection:
            for key, value in settings.items():
                if key == "reminder_times":
                    continue
                self.connection.execute(
                    "INSERT INTO setting (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, json.dumps(value)),
                )

            self.connection.execute("DELETE FROM reminder")
            for habit_name, time_hhmm in reminders.items():
                habit_id = self._habit_id(habit_name)
                if habit_id is None:
                    # a reminder for a habit that no longer exists cannot be stored:
                    # the foreign key is the point of the schema
                    continue
                self.connection.execute(
                    "INSERT INTO reminder (habit_id, time_hhmm) VALUES (?, ?)",
                    (habit_id, time_hhmm),
                )

    # ----------------------------------------------------------- achievements

    def get_unlocked(self) -> list[str]:
        return [
            row["code"]
            for row in self.connection.execute(
                "SELECT code FROM achievement_unlock ORDER BY unlocked_at, code"
            )
        ]

    def set_unlocked(self, codes: list[str]) -> None:
        with self.connection:
            self.connection.executemany(
                "INSERT INTO achievement_unlock (code) VALUES (?) ON CONFLICT(code) DO NOTHING",
                [(code,) for code in codes],
            )
            placeholders = ",".join("?" for _ in codes) or "''"
            self.connection.execute(
                f"DELETE FROM achievement_unlock WHERE code NOT IN ({placeholders})",
                list(codes),
            )

    # -------------------------------------------------------------- lifecycle

    def clear_all(self) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM habit_log")
            self.connection.execute("DELETE FROM reminder")
            self.connection.execute("DELETE FROM habit")
            self.connection.execute("DELETE FROM achievement_unlock")

    def close(self) -> None:
        try:
            self.connection.close()
        except sqlite3.ProgrammingError:
            pass
