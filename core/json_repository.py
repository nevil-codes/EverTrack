"""The original four-JSON-files backend, behind the Repository interface.

Kept so the app still runs on existing data, and so the SQLite backend has
something to be tested against for equivalence.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

from core import storage
from core.models import Habit, LogEntry, ValidationError, load_habits, load_logs
from core.repository import Repository, default_settings


class JsonRepository(Repository):
    """Ids are positions in the file: stable for as long as a snapshot lives,
    reassigned on every reload. Good enough for a single-process desktop app,
    and one of the reasons to move to SQLite."""

    def __init__(self, directory: str | Path = "."):
        directory = Path(directory)
        self.logs_file = directory / "habits_data.json"
        self.habits_file = directory / "habits_list.json"
        self.settings_file = directory / "settings.json"
        self.achievements_file = directory / "achievements.json"
        self._problems: list[str] = []

    # ---------------------------------------------------------------- helpers

    def _read(self, path: Path, default):
        result = storage.read_json(path, default)
        if result.problem and result.problem not in self._problems:
            self._problems.append(result.problem)
        return result.data

    def _note(self, report, path: Path):
        for _, reason in report.rejected:
            message = f"skipped a record in {path.name}: {reason}"
            if message not in self._problems:
                self._problems.append(message)

    def problems(self) -> list[str]:
        return list(self._problems)

    # ----------------------------------------------------------------- habits

    def list_habits(self) -> list[Habit]:
        report = load_habits(self._read(self.habits_file, []))
        self._note(report, self.habits_file)
        return [dataclasses.replace(h, id=index + 1) for index, h in enumerate(report.records)]

    def add_habit(self, habit: Habit) -> Habit:
        raw = self._read(self.habits_file, [])
        if any(str(r.get("name", "")).lower() == habit.name.lower() for r in raw):
            raise ValidationError(f"a habit named {habit.name!r} already exists")
        raw.append(habit.to_dict())
        storage.write_json(self.habits_file, raw)
        return dataclasses.replace(habit, id=len(raw))

    def delete_habit(self, name: str) -> bool:
        raw = self._read(self.habits_file, [])
        remaining = [r for r in raw if r.get("name") != name]
        if len(remaining) == len(raw):
            return False
        storage.write_json(self.habits_file, remaining)

        logs = self._read(self.logs_file, [])
        storage.write_json(self.logs_file, [log for log in logs if log.get("habit") != name])

        settings = self.get_settings()
        if settings.get("reminder_times", {}).pop(name, None) is not None:
            self.save_settings(settings)
        return True

    # ------------------------------------------------------------------- logs

    def list_logs(self) -> list[LogEntry]:
        report = load_logs(self._read(self.logs_file, []))
        self._note(report, self.logs_file)
        return [dataclasses.replace(e, id=index + 1) for index, e in enumerate(report.records)]

    def add_log(self, entry: LogEntry) -> LogEntry:
        # Referential integrity by hand: SQLite gets this from a foreign key,
        # and both backends must behave the same way.
        known = {str(r.get("name", "")).lower() for r in self._read(self.habits_file, [])}
        if entry.habit.lower() not in known:
            raise ValidationError(f"no habit named {entry.habit!r} — create it first")

        raw = self._read(self.logs_file, [])
        raw.append(entry.to_dict())
        storage.write_json(self.logs_file, raw)
        return dataclasses.replace(entry, id=len(raw))

    def delete_log(self, log_id: int) -> bool:
        raw = self._read(self.logs_file, [])
        index = log_id - 1
        if not 0 <= index < len(raw):
            return False
        del raw[index]
        storage.write_json(self.logs_file, raw)
        return True

    # --------------------------------------------------------------- settings

    def get_settings(self) -> dict:
        settings = default_settings()
        settings.update(self._read(self.settings_file, {}) or {})
        settings.setdefault("reminder_times", {})
        return settings

    def save_settings(self, settings: dict) -> None:
        storage.write_json(self.settings_file, settings)

    # ----------------------------------------------------------- achievements

    def get_unlocked(self) -> list[str]:
        stored = self._read(self.achievements_file, {}) or {}
        return list(stored.get("unlocked", []))

    def set_unlocked(self, codes: list[str]) -> None:
        from core.achievements import total_points

        storage.write_json(
            self.achievements_file,
            {"unlocked": list(codes), "total_points": total_points(codes)},
        )

    # -------------------------------------------------------------- lifecycle

    def clear_all(self) -> None:
        storage.write_json(self.logs_file, [])
        storage.write_json(self.habits_file, [])
        self.set_unlocked([])
