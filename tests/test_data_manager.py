"""DataManager is GUI-free, so it can be tested directly against a temp directory."""
import json

import pytest

from core.models import ValidationError
from data_manager import DataManager


@pytest.fixture
def manager(tmp_path):
    return DataManager(directory=str(tmp_path))


def log(date="2026-09-04", habit="Meditation", duration=30, completed=True, notes=""):
    return {"date": date, "habit": habit, "duration": duration, "completed": completed, "notes": notes}


def habit_record(name="Meditation", target=30):
    return {"name": name, "start_date": "2026-09-01", "end_date": "No Limit",
            "daily_target": target, "status": "Active"}


def test_starts_empty(manager):
    assert manager.habits_data == [] and manager.habits_list == []
    assert manager.problems == []


def test_add_log_persists(manager, tmp_path):
    manager.add_habit(habit_record())
    manager.add_log(log())
    on_disk = json.loads((tmp_path / "habits_data.json").read_text())
    assert on_disk == [log()]


def test_add_log_rejects_invalid_records(manager):
    manager.add_habit(habit_record())
    with pytest.raises(ValidationError):
        manager.add_log(log(duration=0))
    with pytest.raises(ValidationError):
        manager.add_log(log(date="04/09/2026"))
    assert manager.habits_data == []


def test_duplicate_habit_names_are_refused(manager):
    manager.add_habit(habit_record("Reading"))
    with pytest.raises(ValidationError, match="already exists"):
        manager.add_habit(habit_record("reading"))


def test_delete_log_at_removes_exactly_one_duplicate(manager):
    # regression: value-matching deleted every identical row at once
    manager.add_habit(habit_record())
    manager.add_habit(habit_record("Reading"))
    manager.add_log(log())
    manager.add_log(log())
    manager.add_log(log(habit="Reading"))

    assert manager.delete_log_at(0) is True

    assert len(manager.habits_data) == 2
    assert [entry["habit"] for entry in manager.habits_data] == ["Meditation", "Reading"]


def test_delete_log_at_rejects_a_bad_index(manager):
    manager.add_habit(habit_record())
    manager.add_log(log())
    assert manager.delete_log_at(5) is False
    assert len(manager.habits_data) == 1


def test_fractional_durations_survive_a_round_trip(manager):
    # regression: the table rounded durations for display and deletion matched
    # on the rounded value, so a 23.4-minute log could never be deleted
    manager.add_habit(habit_record())
    manager.add_log(log(duration=23.4))
    assert manager.habits_data[0]["duration"] == 23.4
    assert manager.delete_log_at(0) is True


def test_deleting_a_habit_removes_its_logs_and_its_reminder(manager):
    manager.add_habit(habit_record("Reading"))
    manager.add_habit(habit_record("Meditation"))
    manager.set_reminder("Reading", "09:00")
    manager.add_log(log(habit="Reading"))
    manager.add_log(log(habit="Meditation"))

    manager.delete_habit("Reading")

    assert [h["name"] for h in manager.habits_list] == ["Meditation"]
    assert [entry["habit"] for entry in manager.habits_data] == ["Meditation"]
    # regression: the reminder used to outlive the habit
    assert manager.settings["reminder_times"] == {}


@pytest.mark.parametrize("value", ["9:00", "0900", "25:00", "09:70", "soon", ""])
def test_bad_reminder_times_are_refused(manager, value):
    with pytest.raises(ValidationError):
        manager.set_reminder("Reading", value)


def test_active_habits_ignore_case_in_status(manager):
    manager.add_habit(habit_record("A"))
    manager.add_habit({**habit_record("B"), "status": "active"})
    manager.add_habit({**habit_record("C"), "status": "Archived"})
    assert [h["name"] for h in manager.get_active_habits()] == ["A", "B"]


def test_typed_views_skip_and_report_unusable_rows(tmp_path):
    (tmp_path / "habits_data.json").write_text(json.dumps([log(), {"habit": "broken"}]))
    manager = DataManager(directory=str(tmp_path))

    assert len(manager.log_models()) == 1
    assert any("skipped a record" in problem for problem in manager.problems)


def test_corrupt_data_file_is_reported_at_startup(tmp_path):
    (tmp_path / "habits_data.json").write_text("{not json")
    manager = DataManager(directory=str(tmp_path))

    assert manager.habits_data == []
    assert any("not valid JSON" in problem for problem in manager.problems)


def test_export_to_csv_writes_a_header_and_every_row(manager, tmp_path):
    manager.add_habit(habit_record())
    manager.add_habit(habit_record("Reading"))
    manager.add_log(log())
    manager.add_log(log(habit="Reading", completed=False))

    target = tmp_path / "out.csv"
    assert manager.export_to_csv(str(target)) is True

    lines = target.read_text().strip().splitlines()
    assert lines[0] == "Date,Habit,Duration (min),Completed,Notes"
    assert len(lines) == 3
    assert lines[2].endswith("No,")
