"""Data-quality expectations.

Deliberately small and explicit rather than a framework: each expectation is a
name, a severity and a function that returns the rows that violate it. A run
with an ERROR violation does not publish.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any

Row = dict[str, Any]
Rows = list[Row]

MAX_DURATION_MIN = 1440
FRESHNESS_DAYS = 7
SAMPLE_SIZE = 5


class Severity(str, Enum):
    ERROR = "error"    # the dataset is wrong; do not publish
    WARN = "warn"      # worth knowing, not worth stopping for


@dataclass(frozen=True)
class Expectation:
    name: str
    description: str
    severity: Severity
    check: Callable[[Rows, Context], Rows]  # returns the offending rows


@dataclass(frozen=True)
class Context:
    """Everything an expectation may need beyond the rows themselves."""
    dim_habit: Rows = field(default_factory=list)
    as_of: date = field(default_factory=date.today)


@dataclass(frozen=True)
class Result:
    expectation: Expectation
    failed: int
    checked: int
    sample: list[str]

    @property
    def passed(self) -> bool:
        return self.failed == 0

    @property
    def blocking(self) -> bool:
        return not self.passed and self.expectation.severity is Severity.ERROR


@dataclass(frozen=True)
class Report:
    dataset: str
    results: list[Result]

    @property
    def failed(self) -> list[Result]:
        return [result for result in self.results if not result.passed]

    @property
    def blocking(self) -> list[Result]:
        return [result for result in self.results if result.blocking]

    @property
    def ok(self) -> bool:
        return not self.blocking

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "checks": len(self.results),
            "failed": len(self.failed),
            "blocking": len(self.blocking),
            "results": [
                {
                    "name": result.expectation.name,
                    "severity": result.expectation.severity.value,
                    "checked": result.checked,
                    "failed": result.failed,
                    "sample": result.sample,
                }
                for result in self.results
            ],
        }

    def render(self) -> str:
        lines = [f"data quality — {self.dataset}"]
        for result in self.results:
            if result.passed:
                mark = "PASS"
            else:
                mark = "FAIL" if result.blocking else "WARN"
            lines.append(
                f"  [{mark}] {result.expectation.name}: "
                f"{result.failed}/{result.checked} rows"
            )
            for item in result.sample:
                lines.append(f"           {item}")
        return "\n".join(lines)


# --------------------------------------------------------------- expectations

def _identify(row: Row) -> str:
    return f"{row.get('log_date')} {row.get('habit_name')} {row.get('duration_min')}min"



def _complete(rows: Rows) -> Rows:
    """Rows with the fields these checks need.

    A null is reported once, by the not-null expectation that owns it; the
    checks that would otherwise crash on it skip it instead.
    """
    return [row for row in rows
            if row.get("habit_key") is not None
            and row.get("log_date") is not None
            and row.get("duration_min") is not None]


def _not_null(column: str) -> Callable[[Rows, Context], Rows]:
    def check(rows: Rows, _context: Context) -> Rows:
        return [row for row in rows if row.get(column) is None]
    return check


def _duration_in_range(rows: Rows, _context: Context) -> Rows:
    # Nulls belong to duration_not_null; checking them twice would double-report.
    return [row for row in rows
            if row.get("duration_min") is not None
            and not (0 < row["duration_min"] <= MAX_DURATION_MIN)]


def _not_in_the_future(rows: Rows, context: Context) -> Rows:
    return [row for row in rows
            if row.get("log_date") is not None and row["log_date"] > context.as_of]


def _habit_exists(rows: Rows, context: Context) -> Rows:
    known = {habit["habit_key"] for habit in context.dim_habit}
    return [row for row in rows
            if row.get("habit_key") is not None and row["habit_key"] not in known]


def _not_before_habit_started(rows: Rows, _context: Context) -> Rows:
    return [row for row in rows
            if row.get("days_since_habit_start") is not None
            and row["days_since_habit_start"] < 0]


def _no_duplicate_entries(rows: Rows, _context: Context) -> Rows:
    seen: set[tuple] = set()
    duplicates = []
    for row in _complete(rows):
        key = (row["habit_key"], row["log_date"], row["duration_min"], row["completed"])
        if key in seen:
            duplicates.append(row)
        else:
            seen.add(key)
    return duplicates


def _daily_total_within_a_day(rows: Rows, _context: Context) -> Rows:
    totals: dict[tuple, float] = {}
    for row in _complete(rows):
        key = (row["habit_key"], row["log_date"])
        totals[key] = totals.get(key, 0) + row["duration_min"]
    over = {key for key, total in totals.items() if total > MAX_DURATION_MIN}
    return [row for row in _complete(rows) if (row["habit_key"], row["log_date"]) in over]


def _is_fresh(rows: Rows, context: Context) -> Rows:
    """Not row-level: either the dataset is stale or it is not."""
    dated = [row for row in rows if row.get("log_date") is not None]
    if not dated:
        return []
    latest = max(row["log_date"] for row in dated)
    if latest >= context.as_of - timedelta(days=FRESHNESS_DAYS):
        return []
    return [{"log_date": latest, "habit_name": "(dataset)", "duration_min": 0}]


FACT_EXPECTATIONS: tuple[Expectation, ...] = (
    Expectation("habit_key_not_null", "every fact row names a habit",
                Severity.ERROR, _not_null("habit_key")),
    Expectation("log_date_not_null", "every fact row is dated",
                Severity.ERROR, _not_null("log_date")),
    Expectation("duration_not_null", "every fact row has a duration",
                Severity.ERROR, _not_null("duration_min")),
    Expectation("duration_within_bounds", f"0 < duration <= {MAX_DURATION_MIN} minutes",
                Severity.ERROR, _duration_in_range),
    Expectation("log_date_not_in_the_future", "nothing is logged after today",
                Severity.ERROR, _not_in_the_future),
    Expectation("habit_key_resolves", "every fact row joins to dim_habit",
                Severity.ERROR, _habit_exists),
    Expectation("log_not_before_habit_start", "activities fall on or after the habit's start date",
                Severity.WARN, _not_before_habit_started),
    Expectation("no_duplicate_entries", "no two identical entries for one habit and day",
                Severity.WARN, _no_duplicate_entries),
    Expectation("daily_total_within_a_day", "a habit's daily total fits in 24 hours",
                Severity.WARN, _daily_total_within_a_day),
    Expectation("dataset_is_fresh", f"something logged in the last {FRESHNESS_DAYS} days",
                Severity.WARN, _is_fresh),
)

DIM_EXPECTATIONS: tuple[Expectation, ...] = (
    Expectation("habit_key_unique", "one row per habit",
                Severity.ERROR,
                lambda rows, _context: _duplicate_keys(rows, "habit_key")),
    Expectation("target_is_positive", "every habit has a positive daily target",
                Severity.ERROR,
                lambda rows, _context: [r for r in rows if not (r["daily_target_min"] or 0) > 0]),
    Expectation("end_date_after_start", "an end date, if set, follows the start date",
                Severity.ERROR,
                lambda rows, _context: [r for r in rows
                                        if r["end_date"] and r["end_date"] < r["start_date"]]),
)


def _duplicate_keys(rows: Rows, column: str) -> Rows:
    seen: set = set()
    duplicates = []
    for row in rows:
        if row[column] in seen:
            duplicates.append(row)
        else:
            seen.add(row[column])
    return duplicates


def validate(dataset: str, rows: Rows, expectations, context: Context | None = None) -> Report:
    context = context or Context()
    results = []
    for expectation in expectations:
        offenders = expectation.check(rows, context)
        results.append(Result(
            expectation=expectation,
            failed=len(offenders),
            checked=len(rows),
            sample=[_identify(row) for row in offenders[:SAMPLE_SIZE]],
        ))
    return Report(dataset=dataset, results=results)
