# data_manager.py - Handles all data operations
"""Storage facade for the desktop app.

Records stay dicts in memory because the tabs read them directly; every write
goes through core.storage (atomic) and every incoming record is validated by
core.models before it reaches disk.
"""
from core import storage
from core.models import Habit, LogEntry, ValidationError, load_habits, load_logs


class DataManager:
    """Manages all data operations for EverTrack"""

    def __init__(self, directory="."):
        self.data_file = f"{directory}/habits_data.json"
        self.habits_file = f"{directory}/habits_list.json"
        self.settings_file = f"{directory}/settings.json"
        self.achievements_file = f"{directory}/achievements.json"

        self.problems = []  # human-readable messages worth surfacing at startup

        self.habits_data = self._read(self.data_file, [])
        self.habits_list = self._read(self.habits_file, [])
        self.settings = self._read(self.settings_file, {
            "theme": "light",
            "notifications": True,
            "reminder_times": {}
        })
        self.achievements = self._read(self.achievements_file, {
            "unlocked": [],
            "total_points": 0
        })
        self.achievements.setdefault("unlocked", [])
        self.achievements.setdefault("total_points", 0)

    # ------------------------------------------------------------------ io

    def _read(self, filename, default):
        result = storage.read_json(filename, default)
        if result.problem:
            self.problems.append(result.problem)
        return result.data

    def load_json(self, filename, default):
        """Kept for callers outside this class; prefer the typed accessors."""
        return self._read(filename, default)

    def save_json(self, filename, data):
        try:
            storage.write_json(filename, data)
            return True
        except OSError as exc:
            print(f"Error saving {filename}: {exc}")
            return False

    def save_all(self):
        self.save_json(self.data_file, self.habits_data)
        self.save_json(self.habits_file, self.habits_list)
        self.save_json(self.settings_file, self.settings)
        self.save_json(self.achievements_file, self.achievements)

    # -------------------------------------------------------- typed views

    def habit_models(self):
        """Valid Habit records. Unusable rows are reported, not crashed on."""
        report = load_habits(self.habits_list)
        self._note_rejects(report, self.habits_file)
        return report.records

    def log_models(self):
        """Valid LogEntry records. Unusable rows are reported, not crashed on."""
        report = load_logs(self.habits_data)
        self._note_rejects(report, self.data_file)
        return report.records

    def _note_rejects(self, report, filename):
        for _, reason in report.rejected:
            message = f"skipped a record in {filename}: {reason}"
            if message not in self.problems:
                self.problems.append(message)

    # ----------------------------------------------------------- habits

    def add_habit(self, habit_data):
        """Validate and append a habit. Raises ValidationError if unusable."""
        habit = Habit.from_dict(habit_data)
        if any(existing.get("name", "").lower() == habit.name.lower() for existing in self.habits_list):
            raise ValidationError(f"a habit named {habit.name!r} already exists")
        self.habits_list.append(habit.to_dict())
        self.save_json(self.habits_file, self.habits_list)
        return habit

    def delete_habit(self, habit_name):
        """Delete a habit, its logs, and its reminder."""
        self.habits_list = [h for h in self.habits_list if h.get("name") != habit_name]
        self.habits_data = [log for log in self.habits_data if log.get("habit") != habit_name]
        self.settings.get("reminder_times", {}).pop(habit_name, None)
        self.save_all()

    def set_reminder(self, habit_name, time_hhmm):
        """Store a HH:MM reminder. Raises ValidationError on a bad time."""
        if not _is_hhmm(time_hhmm):
            raise ValidationError(f"reminder time must look like 09:00, got {time_hhmm!r}")
        self.settings.setdefault("reminder_times", {})[habit_name] = time_hhmm
        self.save_json(self.settings_file, self.settings)

    # -------------------------------------------------------------- logs

    def add_log(self, log_data):
        """Validate and append a log entry. Raises ValidationError if unusable."""
        entry = LogEntry.from_dict(log_data)
        self.habits_data.append(entry.to_dict())
        self.save_json(self.data_file, self.habits_data)
        return entry

    def delete_log_at(self, index):
        """Delete exactly one log entry, addressed by position.

        Position, not value: matching on (date, habit, duration) deleted every
        duplicate at once, and could not address a row at all once the display
        had rounded its duration.
        """
        if not 0 <= index < len(self.habits_data):
            return False
        del self.habits_data[index]
        self.save_json(self.data_file, self.habits_data)
        return True

    def delete_log(self, date, habit, duration):
        """Deprecated: deletes the first matching entry only. Prefer delete_log_at."""
        for index, log in enumerate(self.habits_data):
            if (log.get("date") == date and log.get("habit") == habit
                    and float(log.get("duration", 0)) == float(duration)):
                return self.delete_log_at(index)
        return False

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
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Habit', 'Duration (min)', 'Completed', 'Notes'])
                for log in self.habits_data:
                    writer.writerow([
                        log.get('date', ''),
                        log.get('habit', ''),
                        log.get('duration', ''),
                        'Yes' if log.get('completed', True) else 'No',
                        log.get('notes', '')
                    ])
            return True
        except OSError as exc:
            print(f"Error exporting to CSV: {exc}")
            return False


def _is_hhmm(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return False
    hours, _, minutes = value.partition(":")
    return (
        hours.isdigit() and minutes.isdigit()
        and 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59
    )
