"""One suite, run against every backend.

If SQLite and JSON ever disagree about what storage means, these fail.
"""
from datetime import date

import pytest

from core.json_repository import JsonRepository
from core.models import Habit, LogEntry, ValidationError
from core.sqlite_repository import SqliteRepository

TODAY = date(2026, 9, 4)


@pytest.fixture(params=["json", "sqlite"])
def repo(request, tmp_path):
    if request.param == "json":
        backend = JsonRepository(tmp_path)
    else:
        backend = SqliteRepository(tmp_path / "evertrack.db")
    yield backend
    backend.close()


def habit(name="Meditation", target=30, status="Active", end=None):
    return Habit(name=name, start_date=date(2026, 9, 1), daily_target_min=target,
                 end_date=end, status=status)


def entry(habit_name="Meditation", offset_days=0, duration=30.0, completed=True, notes=""):
    return LogEntry(log_date=date(2026, 9, 4 - offset_days), habit=habit_name,
                    duration_min=duration, completed=completed, notes=notes)


def test_starts_empty(repo):
    assert repo.list_habits() == []
    assert repo.list_logs() == []
    assert repo.get_unlocked() == []


def test_add_and_list_habits(repo):
    stored = repo.add_habit(habit())
    assert stored.id is not None

    listed = repo.list_habits()
    assert [h.name for h in listed] == ["Meditation"]
    assert listed[0].daily_target_min == 30
    assert listed[0].end_date is None


def test_habit_end_date_round_trips(repo):
    repo.add_habit(habit(end=date(2026, 12, 31)))
    assert repo.list_habits()[0].end_date == date(2026, 12, 31)


def test_duplicate_habit_names_are_refused_case_insensitively(repo):
    repo.add_habit(habit("Reading"))
    with pytest.raises(ValidationError):
        repo.add_habit(habit("reading"))


def test_add_and_list_logs_preserves_order_and_fractions(repo):
    repo.add_habit(habit())
    repo.add_log(entry(duration=23.4))
    repo.add_log(entry(offset_days=1, duration=30))

    logs = repo.list_logs()
    assert [log.duration_min for log in logs] == [23.4, 30.0]
    assert all(log.id is not None for log in logs)


def test_delete_log_removes_exactly_one_of_two_identical_entries(repo):
    repo.add_habit(habit())
    first = repo.add_log(entry())
    repo.add_log(entry())

    assert repo.delete_log(first.id) is True
    assert len(repo.list_logs()) == 1


def test_delete_log_with_an_unknown_id(repo):
    assert repo.delete_log(999) is False


def test_deleting_a_habit_takes_its_logs_and_reminder(repo):
    repo.add_habit(habit("Reading"))
    repo.add_habit(habit("Meditation"))
    repo.add_log(entry("Reading"))
    repo.add_log(entry("Meditation"))
    repo.save_settings({"theme": "light", "notifications": True,
                        "reminder_times": {"Reading": "09:00"}})

    assert repo.delete_habit("Reading") is True

    assert [h.name for h in repo.list_habits()] == ["Meditation"]
    assert [log.habit for log in repo.list_logs()] == ["Meditation"]
    assert repo.get_settings()["reminder_times"] == {}


def test_deleting_an_unknown_habit(repo):
    assert repo.delete_habit("Nope") is False


def test_settings_round_trip_with_defaults(repo):
    defaults = repo.get_settings()
    assert defaults["theme"] == "light"
    assert defaults["notifications"] is True
    assert defaults["reminder_times"] == {}

    repo.add_habit(habit())
    repo.save_settings({"theme": "dark", "notifications": False,
                        "reminder_times": {"Meditation": "07:30"}})

    stored = repo.get_settings()
    assert stored["theme"] == "dark"
    assert stored["notifications"] is False
    assert stored["reminder_times"] == {"Meditation": "07:30"}


def test_unlocked_achievements_round_trip(repo):
    repo.set_unlocked(["first_log", "perfect_day"])
    assert sorted(repo.get_unlocked()) == ["first_log", "perfect_day"]

    repo.set_unlocked(["first_log"])
    assert repo.get_unlocked() == ["first_log"]


def test_clear_all(repo):
    repo.add_habit(habit())
    repo.add_log(entry())
    repo.set_unlocked(["first_log"])

    repo.clear_all()

    assert repo.list_habits() == []
    assert repo.list_logs() == []
    assert repo.get_unlocked() == []


def test_a_log_needs_an_existing_habit(repo):
    # regression: logs could reference a habit that was never created, and the
    # JSON backend silently accepted them
    with pytest.raises(ValidationError):
        repo.add_log(entry("Ghost"))


def test_habit_names_are_matched_case_insensitively_when_logging(repo):
    repo.add_habit(habit("Reading"))
    stored = repo.add_log(entry("reading"))
    assert stored.id is not None
