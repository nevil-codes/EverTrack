"""Date parsing and helpers.

All dates in stored data are ISO ``YYYY-MM-DD`` strings in local time.
"""
from __future__ import annotations

from datetime import date, datetime

ISO_FORMAT = "%Y-%m-%d"


class InvalidDate(ValueError):
    """Raised when a stored date string cannot be parsed."""


def parse_iso(value: str) -> date:
    """Parse ``YYYY-MM-DD`` into a ``date``.

    Raises InvalidDate (a ValueError) with the offending value, rather than
    letting a bare strptime failure escape from deep inside a UI callback.
    """
    if not isinstance(value, str):
        raise InvalidDate(f"expected a date string, got {type(value).__name__}: {value!r}")
    try:
        return datetime.strptime(value, ISO_FORMAT).date()
    except ValueError as exc:
        raise InvalidDate(f"not an ISO date (YYYY-MM-DD): {value!r}") from exc


def to_iso(value: date) -> str:
    return value.strftime(ISO_FORMAT)


def today() -> date:
    return date.today()


def parse_iso_lenient(value: str) -> date | None:
    """Parse, returning None instead of raising.

    Used when reading a whole file of records where one bad row should not
    take down the aggregate.
    """
    try:
        return parse_iso(value)
    except InvalidDate:
        return None
