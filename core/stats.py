"""Aggregations over log entries. No charting, no widgets — just numbers."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

from core.models import LogEntry


@dataclass(frozen=True)
class Totals:
    activities: int
    total_minutes: float
    completed: int
    active_days: int

    @property
    def completion_rate(self) -> float:
        """Percentage of logged activities marked completed (0.0 when empty)."""
        if not self.activities:
            return 0.0
        return self.completed / self.activities * 100

    @property
    def total_hours(self) -> float:
        return self.total_minutes / 60


def totals(logs: Sequence[LogEntry]) -> Totals:
    return Totals(
        activities=len(logs),
        total_minutes=sum(log.duration_min for log in logs),
        completed=sum(1 for log in logs if log.completed),
        active_days=len({log.log_date for log in logs}),
    )


def minutes_per_habit(logs: Iterable[LogEntry]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for log in logs:
        out[log.habit] += log.duration_min
    return dict(out)


def count_per_habit(logs: Iterable[LogEntry]) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for log in logs:
        out[log.habit] += 1
    return dict(out)


def minutes_per_day(logs: Iterable[LogEntry]) -> dict[date, float]:
    out: dict[date, float] = defaultdict(float)
    for log in logs:
        out[log.log_date] += log.duration_min
    return dict(sorted(out.items()))


def activities_per_day(logs: Iterable[LogEntry]) -> dict[date, int]:
    out: dict[date, int] = defaultdict(int)
    for log in logs:
        out[log.log_date] += 1
    return dict(sorted(out.items()))


def completion_rate_per_habit(logs: Iterable[LogEntry]) -> dict[str, float]:
    stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [total, completed]
    for log in logs:
        stats[log.habit][0] += 1
        stats[log.habit][1] += int(log.completed)
    return {habit: completed / total * 100 for habit, (total, completed) in stats.items()}


def most_practiced(logs: Sequence[LogEntry]) -> tuple[str, int] | None:
    counts = count_per_habit(logs)
    if not counts:
        return None
    return max(counts.items(), key=lambda item: item[1])


def weekly_buckets(
    logs: Iterable[LogEntry], today: date | None = None, weeks: int = 4
) -> list[tuple[str, float]]:
    """Minutes per week for the last `weeks` complete 7-day windows.

    Returns oldest-first, always exactly `weeks` buckets (zero-filled), so the
    x-axis is ordered and labelled consistently. Future-dated logs are ignored.
    """
    today = today or date.today()
    buckets = [0.0] * weeks
    for log in logs:
        days_ago = (today - log.log_date).days
        if days_ago < 0 or days_ago >= weeks * 7:
            continue
        buckets[weeks - 1 - days_ago // 7] += log.duration_min

    labels = []
    for index in range(weeks):
        offset = weeks - 1 - index
        end = today - timedelta(days=offset * 7)
        start = end - timedelta(days=6)
        labels.append(f"{start:%d %b}–{end:%d %b}")
    return list(zip(labels, buckets, strict=False))


def calendar_window(
    logs: Iterable[LogEntry], today: date | None = None, weeks: int = 8
) -> tuple[list[date], dict[date, int]]:
    """Dates for a heatmap ending *today*, aligned so each row is one weekday.

    Returns (dates, counts). The window starts on the Monday of the week that
    is `weeks - 1` weeks before this one, so column 0 is always a Monday and
    the final column contains today.
    """
    today = today or date.today()
    end_of_week = today + timedelta(days=6 - today.weekday())  # Sunday of this week
    start = end_of_week - timedelta(days=weeks * 7 - 1)  # a Monday
    dates = [start + timedelta(days=offset) for offset in range(weeks * 7)]

    counts = activities_per_day(logs)
    return dates, {day: counts.get(day, 0) for day in dates}
