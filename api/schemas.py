"""Request and response models. Validation happens here and in core.models."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.dates import today
from core.models import MAX_DURATION_MIN, Habit, LogEntry

Status = Literal["Active", "Paused", "Archived"]


class HabitIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100, examples=["Reading"])
    daily_target_min: int = Field(gt=0, le=MAX_DURATION_MIN, examples=[30])
    start_date: date | None = Field(default=None, description="defaults to today")
    end_date: date | None = Field(default=None, description="null means no end date")
    status: Status = "Active"

    def to_domain(self) -> Habit:
        return Habit(
            name=self.name,
            start_date=self.start_date or today(),
            daily_target_min=self.daily_target_min,
            end_date=self.end_date,
            status=self.status,
        )


class HabitOut(BaseModel):
    id: int | None
    name: str
    start_date: date
    end_date: date | None
    daily_target_min: int
    status: str

    @classmethod
    def from_domain(cls, habit: Habit) -> HabitOut:
        return cls(
            id=habit.id,
            name=habit.name,
            start_date=habit.start_date,
            end_date=habit.end_date,
            daily_target_min=habit.daily_target_min,
            status=habit.status,
        )


class LogIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    habit: str = Field(min_length=1, examples=["Reading"])
    duration_min: float = Field(gt=0, le=MAX_DURATION_MIN, examples=[30])
    log_date: date | None = Field(default=None, description="defaults to today")
    completed: bool = True
    notes: str = ""

    @field_validator("log_date")
    @classmethod
    def not_in_the_future(cls, value: date | None) -> date | None:
        if value and value > today():
            raise ValueError("log_date cannot be in the future")
        return value

    def to_domain(self) -> LogEntry:
        return LogEntry(
            log_date=self.log_date or today(),
            habit=self.habit,
            duration_min=self.duration_min,
            completed=self.completed,
            notes=self.notes,
        )


class LogOut(BaseModel):
    id: int | None
    habit: str
    log_date: date
    duration_min: float
    completed: bool
    notes: str

    @classmethod
    def from_domain(cls, entry: LogEntry) -> LogOut:
        return cls(
            id=entry.id,
            habit=entry.habit,
            log_date=entry.log_date,
            duration_min=entry.duration_min,
            completed=entry.completed,
            notes=entry.notes,
        )


class ParseIn(BaseModel):
    text: str = Field(min_length=1, examples=["read for an hour and 15 mins"])
    commit: bool = Field(default=False, description="also store the parsed activity")


class ParsedOut(BaseModel):
    habit: str
    duration_min: float
    log_date: date
    stored: LogOut | None = None


class SummaryOut(BaseModel):
    activities: int
    total_minutes: float
    total_hours: float
    completed: int
    completion_rate: float
    active_days: int


class StreakOut(BaseModel):
    current: int
    longest: int
    at_risk: bool = Field(description="a live streak with nothing logged today yet")


class DailyPoint(BaseModel):
    log_date: date
    activities: int
    total_minutes: float


class HabitTotal(BaseModel):
    habit: str
    activities: int
    total_minutes: float
    completion_rate: float


class WeeklyBucket(BaseModel):
    label: str
    total_minutes: float


class AchievementOut(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    points: int
    unlocked: bool


class AchievementsOut(BaseModel):
    total_points: int
    unlocked: list[AchievementOut]
    locked: list[AchievementOut]


class Problem(BaseModel):
    detail: str
