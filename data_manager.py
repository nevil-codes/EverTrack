# data_manager.py - Storage facade used by the desktop UI
"""Sits between the tkinter layer and a core.repository.Repository.

The UI still reads plain dicts (`habits_list`, `habits_data`), but every write
goes through the repository, so the same app runs on JSON files or on SQLite
depending only on which backend is constructed here.
"""
from pathlib import Path

from core.achievements import total_points
from core.json_repository import JsonRepository
from core.models import Habit, LogEntry, ValidationError
from core.repository import Repository


class DataManager:
    """Manages all data operations for EverTrack"""

    def __init__(self, directory=".", repository: Repository | None = None):
        self.repository = repository or JsonRepository(directory)
        self.problems: list[str] = []
        self.reload()

    # ----------------------------------------------------------- backends

    @classmethod
    def sqlite(cls, database="evertrack.db"):
        from core.sqlite_repository import SqliteRepository

        return cls(repository=SqliteRepository(database))

    def backup_paths(self) -> list[Path]:
        """Files worth copying when the user asks for a backup."""
        repo = self.repository
        if isinstance(repo, JsonRepository):
            return [repo.logs_file, repo.habits_file, repo.settings_file, repo.achievements_file]
        return [getattr(repo, "path", None)] if getattr(repo, "path", None) else []

    # -------------------------------------------------------------- state

    def reload(self):
        """Re-read everything from the repository into the dicts the UI reads."""
        self._habits = self.repository.list_habits()
        self._logs = self.repository.list_logs()

        self.habits_list = [dict(habit.to_dict(), id=habit.id) for habit in self._habits]
        self.habits_data = [dict(entry.to_dict(), id=entry.id) for entry in self._logs]
        self.settings = self.repository.get_settings()

        unlocked = self.repository.get_unlocked()
        self.achievements = {"unlocked": unlocked, "total_points": total_points(unlocked)}

        for problem in self.repository.problems():
            if problem not in self.problems:
                self.problems.append(problem)

    def habit_models(self) -> list[Habit]:
        return list(self._habits)

    def log_models(self) -> list[LogEntry]:
        return list(self._logs)

    # ------------------------------------------------------------- habits

    def add_habit(self, habit_data):
        """Validate and store a habit. Raises ValidationError if unusable."""
        habit = self.repository.add_habit(Habit.from_dict(habit_data))
        self.reload()
        return habit

    def delete_habit(self, habit_name):
        """Delete a habit, its logs and its reminder."""
        deleted = self.repository.delete_habit(habit_name)
        self.reload()
        return deleted

    def set_reminder(self, habit_name, time_hhmm):
        """Store a HH:MM reminder. Raises ValidationError on a bad time."""
        if not _is_hhmm(time_hhmm):
            raise ValidationError(f"reminder time must look like 09:00, got {time_hhmm!r}")
        settings = dict(self.settings)
        settings.setdefault("reminder_times", {})[habit_name] = time_hhmm
        self.save_settings(settings)

    # --------------------------------------------------------------- logs

    def add_log(self, log_data):
        """Validate and store a log entry. Raises ValidationError if unusable."""
        entry = self.repository.add_log(LogEntry.from_dict(log_data))
        self.reload()
        return entry

    def delete_log_at(self, index):
        """Delete exactly one log entry, addressed by its position in habits_data."""
        if not 0 <= index < len(self.habits_data):
            return False
        deleted = self.repository.delete_log(self.habits_data[index]["id"])
        self.reload()
        return deleted

    def delete_log(self, date, habit, duration):
        """Deprecated: deletes the first matching entry only. Prefer delete_log_at."""
        for index, log in enumerate(self.habits_data):
            if (log.get("date") == date and log.get("habit") == habit
                    and float(log.get("duration", 0)) == float(duration)):
                return self.delete_log_at(index)
        return False

    # ----------------------------------------------------------- settings

    def save_settings(self, settings=None):
        self.repository.save_settings(settings or self.settings)
        self.reload()

    def set_setting(self, key, value):
        settings = dict(self.settings)
        settings[key] = value
        self.save_settings(settings)

    # ------------------------------------------------------- achievements

    def get_unlocked(self):
        return list(self.achievements.get("unlocked", []))

    def set_unlocked(self, codes):
        self.repository.set_unlocked(list(codes))
        self.reload()

    # -------------------------------------------------------------- reset

    def clear_all(self, keep_theme=None):
        """Delete habits, logs, achievements and reminders."""
        self.repository.clear_all()
        self.repository.save_settings({
            "theme": keep_theme or self.settings.get("theme", "light"),
            "notifications": True,
            "reminder_times": {},
        })
        self.reload()

    # ------------------------------------------------------------ queries

    def get_active_habits(self):
        return [h for h in self.habits_list if str(h.get("status", "")).strip().lower() == "active"]

    def get_logs_by_date(self, date):
        return [log for log in self.habits_data if log.get("date") == date]

    def get_logs_by_habit(self, habit_name):
        return [log for log in self.habits_data if log.get("habit") == habit_name]

    # ------------------------------------------------------------- export

    def export_to_csv(self, filename):
        import csv
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as handle:
                writer = csv.writer(handle)
                writer.writerow(['Date', 'Habit', 'Duration (min)', 'Completed', 'Notes'])
                for entry in self._logs:
                    writer.writerow([
                        entry.log_date.isoformat(),
                        entry.habit,
                        entry.duration_min,
                        'Yes' if entry.completed else 'No',
                        entry.notes,
                    ])
            return True
        except OSError as exc:
            print(f"Error exporting to CSV: {exc}")
            return False

    def close(self):
        self.repository.close()


def _is_hhmm(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False
    hours, _, minutes = value.partition(":")
    return (
        hours.isdigit() and minutes.isdigit()
        and 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59
    )
