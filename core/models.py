"""Domain records, with validation, that round-trip the existing JSON shape."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from core.dates import InvalidDate, parse_iso, to_iso

NO_END_DATE = "No Limit"
MAX_DURATION_MIN = 24 * 60


class ValidationError(ValueError):
    """Raised when a record is not usable."""


@dataclass(frozen=True)
class Habit:
    name: str
    start_date: date
    daily_target_min: int
    end_date: date | None = None
    status: str = "Active"
    id: int | None = None  # assigned by the repository; never written to JSON

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("habit name must not be empty")
        if self.daily_target_min <= 0:
            raise ValidationError(f"daily target must be positive, got {self.daily_target_min}")
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValidationError(f"end date {self.end_date} precedes start date {self.start_date}")

    @property
    def is_active(self) -> bool:
        return self.status.strip().lower() == "active"

    @classmethod
    def from_dict(cls, raw: dict) -> Habit:
        try:
            name = raw["name"]
            start = parse_iso(raw["start_date"])
            target = int(raw["daily_target"])
        except KeyError as exc:
            raise ValidationError(f"habit record missing field {exc.args[0]!r}: {raw!r}") from exc
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"habit record has a bad field: {raw!r} ({exc})") from exc

        raw_end = raw.get("end_date", NO_END_DATE)
        if raw_end in (None, "", NO_END_DATE):
            end = None
        else:
            try:
                end = parse_iso(raw_end)
            except InvalidDate as exc:
                raise ValidationError(f"habit {name!r} has an unusable end date: {exc}") from exc

        return cls(
            name=name,
            start_date=start,
            daily_target_min=target,
            end_date=end,
            status=raw.get("status", "Active"),
        )

    def to_dict(self) -> dict:
        """Emit the on-disk shape the existing JSON files use."""
        return {
            "name": self.name,
            "start_date": to_iso(self.start_date),
            "end_date": NO_END_DATE if self.end_date is None else to_iso(self.end_date),
            "daily_target": self.daily_target_min,
            "status": self.status,
        }


@dataclass(frozen=True)
class LogEntry:
    log_date: date
    habit: str
    duration_min: float
    completed: bool = True
    notes: str = ""
    id: int | None = None  # assigned by the repository; never written to JSON

    def __post_init__(self) -> None:
        if not self.habit or not self.habit.strip():
            raise ValidationError("log entry must name a habit")
        if self.duration_min <= 0:
            raise ValidationError(f"duration must be positive, got {self.duration_min}")
        if self.duration_min > MAX_DURATION_MIN:
            raise ValidationError(
                f"duration {self.duration_min} exceeds {MAX_DURATION_MIN} minutes (one day)"
            )

    @classmethod
    def from_dict(cls, raw: dict) -> LogEntry:
        try:
            log_date = parse_iso(raw["date"])
            habit = raw["habit"]
            duration = float(raw["duration"])
        except KeyError as exc:
            raise ValidationError(f"log record missing field {exc.args[0]!r}: {raw!r}") from exc
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"log record has a bad field: {raw!r} ({exc})") from exc

        return cls(
            log_date=log_date,
            habit=habit,
            duration_min=duration,
            completed=bool(raw.get("completed", True)),
            notes=raw.get("notes", "") or "",
        )

    def to_dict(self) -> dict:
        return {
            "date": to_iso(self.log_date),
            "habit": self.habit,
            "duration": self.duration_min,
            "completed": self.completed,
            "notes": self.notes,
        }


@dataclass
class LoadReport:
    """What happened when a file of records was read."""

    records: list = field(default_factory=list)
    rejected: list = field(default_factory=list)  # (raw_record, reason)

    @property
    def ok(self) -> bool:
        return not self.rejected


def load_habits(raws: list) -> LoadReport:
    return _load(raws, Habit.from_dict)


def load_logs(raws: list) -> LoadReport:
    return _load(raws, LogEntry.from_dict)


def _load(raws: list, build) -> LoadReport:
    report = LoadReport()
    for raw in raws or []:
        try:
            report.records.append(build(raw))
        except ValidationError as exc:
            report.rejected.append((raw, str(exc)))
    return report
