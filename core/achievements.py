"""Achievement catalogue and unlock rules. Pure functions over domain records."""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date

from core.models import Habit, LogEntry
from core.streak import current_streak, longest_streak


@dataclass(frozen=True)
class Achievement:
    code: str
    name: str
    description: str
    icon: str
    points: int


# Note: the original catalogue contained "Early Bird — log 10 activities before
# 9 AM". Log entries record a date but no time of day, so that badge could never
# unlock. It is removed rather than left permanently unreachable; it returns when
# the data model carries a timestamp.
CATALOGUE: tuple[Achievement, ...] = (
    Achievement("first_log", "Getting Started", "Log your first habit", "🌱", 10),
    Achievement("week_streak", "Week Warrior", "Maintain a 7-day streak", "🔥", 50),
    Achievement("ten_streak", "Streak Master", "Achieve a 10-day streak", "🔥", 75),
    Achievement("month_streak", "Monthly Master", "Maintain a 30-day streak", "💎", 200),
    Achievement("hundred_activities", "Century Club", "Log 100 activities", "💯", 100),
    Achievement("thousand_minutes", "Time Investor", "Accumulate 1000 minutes", "⏰", 150),
    Achievement("perfect_day", "Perfect Day", "Complete every active habit in one day", "⭐", 30),
    Achievement("five_habits", "Habit Collector", "Create 5 different habits", "📚", 50),
    Achievement("consistency_king", "Consistency King", "80%+ completion rate with 50+ logs", "👑", 250),
    Achievement("three_month", "Quarter Champion", "Log on 90 different days", "🏆", 300),
    Achievement("meditation_guru", "Meditation Guru", "Log 30 meditation sessions", "🧘", 100),
    Achievement("reading_enthusiast", "Reading Enthusiast", "Log 30 reading sessions", "📖", 100),
    Achievement("fitness_pro", "Fitness Pro", "Log 30 exercise sessions", "💪", 100),
    Achievement("weekend_warrior", "Weekend Warrior", "Log on 10 weekend days", "🎯", 80),
)

BY_CODE: dict[str, Achievement] = {a.code: a for a in CATALOGUE}


def _habit_matches(logs: Sequence[LogEntry], *words: str) -> int:
    return sum(1 for log in logs if any(word in log.habit.lower() for word in words))


def _rules(today: date | None) -> dict[str, Callable[[Sequence[LogEntry], Sequence[Habit]], bool]]:
    dates = lambda logs: [log.log_date for log in logs]  # noqa: E731

    def perfect_day(logs: Sequence[LogEntry], habits: Sequence[Habit]) -> bool:
        active = {h.name for h in habits if h.is_active}
        if not active:
            return False
        per_day: dict[date, set[str]] = {}
        for log in logs:
            if log.completed:
                per_day.setdefault(log.log_date, set()).add(log.habit)
        return any(active <= done for done in per_day.values())

    def consistency(logs: Sequence[LogEntry], _: Sequence[Habit]) -> bool:
        if len(logs) < 50:
            return False
        return sum(1 for log in logs if log.completed) / len(logs) >= 0.8

    return {
        "first_log": lambda logs, _: len(logs) >= 1,
        "week_streak": lambda logs, _: current_streak(dates(logs), today) >= 7
        or longest_streak(dates(logs), today) >= 7,
        "ten_streak": lambda logs, _: longest_streak(dates(logs), today) >= 10,
        "month_streak": lambda logs, _: longest_streak(dates(logs), today) >= 30,
        "hundred_activities": lambda logs, _: len(logs) >= 100,
        "thousand_minutes": lambda logs, _: sum(log.duration_min for log in logs) >= 1000,
        "perfect_day": perfect_day,
        "five_habits": lambda _, habits: len(habits) >= 5,
        "consistency_king": consistency,
        "three_month": lambda logs, _: len(set(dates(logs))) >= 90,
        "meditation_guru": lambda logs, _: _habit_matches(logs, "meditat") >= 30,
        "reading_enthusiast": lambda logs, _: _habit_matches(logs, "read") >= 30,
        "fitness_pro": lambda logs, _: _habit_matches(logs, "exercise", "workout", "gym", "fitness") >= 30,
        "weekend_warrior": lambda logs, _: len({d for d in dates(logs) if d.weekday() >= 5}) >= 10,
    }


def is_unlocked(
    code: str, logs: Sequence[LogEntry], habits: Sequence[Habit], today: date | None = None
) -> bool:
    rule = _rules(today).get(code)
    return bool(rule and rule(logs, habits))


def newly_unlocked(
    logs: Sequence[LogEntry],
    habits: Sequence[Habit],
    already: Sequence[str],
    today: date | None = None,
) -> list[str]:
    """Codes earned now that were not already held. Order follows the catalogue."""
    held = set(already)
    rules = _rules(today)
    return [a.code for a in CATALOGUE if a.code not in held and rules[a.code](logs, habits)]


def total_points(unlocked: Sequence[str]) -> int:
    """Points are derived from what is unlocked — never stored and incremented."""
    return sum(BY_CODE[code].points for code in set(unlocked) if code in BY_CODE)
