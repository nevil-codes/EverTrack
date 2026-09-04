from datetime import date, timedelta

from core.achievements import BY_CODE, newly_unlocked, total_points
from core.models import Habit, LogEntry

TODAY = date(2026, 9, 4)


def habit(name="Meditation", status="Active"):
    return Habit(name=name, start_date=TODAY - timedelta(days=60), daily_target_min=30, status=status)


def logs_on(offsets, name="Meditation", duration=30, completed=True):
    return [LogEntry(TODAY - timedelta(days=o), name, duration, completed) for o in offsets]


def test_first_log():
    assert "first_log" in newly_unlocked(logs_on([0]), [habit()], [], TODAY)


def test_nothing_unlocks_without_data():
    assert newly_unlocked([], [], [], TODAY) == []


def test_already_held_badges_are_not_returned_again():
    earned = newly_unlocked(logs_on([0]), [habit()], ["first_log"], TODAY)
    assert "first_log" not in earned


def test_week_streak_needs_seven_consecutive_days():
    assert "week_streak" not in newly_unlocked(logs_on(range(6)), [habit()], [], TODAY)
    assert "week_streak" in newly_unlocked(logs_on(range(7)), [habit()], [], TODAY)


def test_perfect_day_ignores_archived_habits():
    habits = [habit("Meditation"), habit("Reading", status="Archived")]
    assert "perfect_day" in newly_unlocked(logs_on([0]), habits, [], TODAY)


def test_perfect_day_requires_every_active_habit():
    habits = [habit("Meditation"), habit("Reading")]
    assert "perfect_day" not in newly_unlocked(logs_on([0]), habits, [], TODAY)


def test_perfect_day_ignores_incomplete_logs():
    entries = logs_on([0], completed=False)
    assert "perfect_day" not in newly_unlocked(entries, [habit()], [], TODAY)


def test_thousand_minutes():
    entries = logs_on(range(10), duration=100)
    assert "thousand_minutes" in newly_unlocked(entries, [habit()], [], TODAY)


def test_consistency_king_needs_fifty_logs_and_eighty_percent():
    entries = logs_on(range(50)) + logs_on(range(50, 55), completed=False)
    assert "consistency_king" in newly_unlocked(entries, [habit()], [], TODAY)

    mostly_missed = logs_on(range(30)) + logs_on(range(30, 60), completed=False)
    assert "consistency_king" not in newly_unlocked(mostly_missed, [habit()], [], TODAY)


def test_weekend_warrior_counts_distinct_weekend_days():
    weekends = [d for d in (TODAY - timedelta(days=i) for i in range(60)) if d.weekday() >= 5][:10]
    entries = [LogEntry(d, "Meditation", 30) for d in weekends]
    assert "weekend_warrior" in newly_unlocked(entries, [habit()], [], TODAY)


def test_points_are_derived_from_the_unlocked_list():
    assert total_points([]) == 0
    assert total_points(["first_log"]) == BY_CODE["first_log"].points
    # regression: points were stored and incremented, so they could drift or
    # be double-counted; duplicates and unknown codes must not inflate them
    assert total_points(["first_log", "first_log", "nonsense"]) == BY_CODE["first_log"].points


def test_every_catalogue_entry_has_a_rule():
    earned = newly_unlocked([], [], [], TODAY)  # exercises every rule
    assert earned == []
