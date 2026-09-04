"""Read-only rollups. Every number comes from core.stats or core.streak."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.deps import get_repository
from api.schemas import DailyPoint, HabitTotal, StreakOut, SummaryOut, WeeklyBucket
from core import stats
from core.repository import Repository
from core.streak import current_streak, longest_streak, streak_is_at_risk

router = APIRouter(prefix="/stats", tags=["stats"])

Repo = Annotated[Repository, Depends(get_repository)]


@router.get("/summary", summary="Totals across everything logged")
def summary(repo: Repo) -> SummaryOut:
    totals = stats.totals(repo.list_logs())
    return SummaryOut(
        activities=totals.activities,
        total_minutes=totals.total_minutes,
        total_hours=round(totals.total_hours, 2),
        completed=totals.completed,
        completion_rate=round(totals.completion_rate, 2),
        active_days=totals.active_days,
    )


@router.get("/streak", summary="Current and longest streak")
def streak(repo: Repo) -> StreakOut:
    dates = [entry.log_date for entry in repo.list_logs()]
    return StreakOut(
        current=current_streak(dates),
        longest=longest_streak(dates),
        at_risk=streak_is_at_risk(dates),
    )


@router.get("/daily", summary="Activities and minutes per day, oldest first")
def daily(repo: Repo) -> list[DailyPoint]:
    entries = repo.list_logs()
    minutes = stats.minutes_per_day(entries)
    counts = stats.activities_per_day(entries)
    return [
        DailyPoint(log_date=day, activities=counts[day], total_minutes=total)
        for day, total in minutes.items()
    ]


@router.get("/habits", summary="Per-habit totals and completion rate")
def per_habit(repo: Repo) -> list[HabitTotal]:
    entries = repo.list_logs()
    minutes = stats.minutes_per_habit(entries)
    counts = stats.count_per_habit(entries)
    rates = stats.completion_rate_per_habit(entries)
    return [
        HabitTotal(
            habit=habit,
            activities=counts[habit],
            total_minutes=total,
            completion_rate=round(rates[habit], 2),
        )
        for habit, total in sorted(minutes.items(), key=lambda item: -item[1])
    ]


@router.get("/weekly", summary="Minutes per week, oldest first")
def weekly(repo: Repo, weeks: int = Query(default=4, ge=1, le=52)) -> list[WeeklyBucket]:
    return [
        WeeklyBucket(label=label, total_minutes=total)
        for label, total in stats.weekly_buckets(repo.list_logs(), weeks=weeks)
    ]
