"""Streak calculation.

Semantics (deliberately chosen, and tested):

* A streak is a run of consecutive calendar days on which *something* was
  logged. It is not per-habit and does not consider daily targets.
* The current streak is counted back from the most recent logged day. That day
  may be today or yesterday: a streak is not broken until a whole day has
  passed without a log, so the number does not drop to zero every midnight
  before the user has had a chance to log anything.
* Dates in the future are ignored entirely. A single mistyped future date used
  to zero the streak permanently.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta

from core.dates import today as today_


def _clean(dates: Iterable[date], today: date) -> list[date]:
    return sorted({d for d in dates if d <= today}, reverse=True)


def current_streak(dates: Iterable[date], today: date | None = None) -> int:
    """Length of the run of consecutive days ending today or yesterday."""
    today = today or today_()
    ordered = _clean(dates, today)
    if not ordered:
        return 0

    most_recent = ordered[0]
    if (today - most_recent).days > 1:
        return 0

    streak = 1
    for earlier, later in zip(ordered[1:], ordered, strict=False):
        if (later - earlier).days == 1:
            streak += 1
        else:
            break
    return streak


def longest_streak(dates: Iterable[date], today: date | None = None) -> int:
    """Longest run of consecutive logged days ever recorded."""
    today = today or today_()
    ordered = sorted({d for d in dates if d <= today})
    if not ordered:
        return 0

    longest = run = 1
    for previous, current in zip(ordered, ordered[1:], strict=False):
        if (current - previous).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1
    return longest


def streak_is_at_risk(dates: Iterable[date], today: date | None = None) -> bool:
    """True when a live streak has nothing logged for today yet."""
    today = today or today_()
    ordered = _clean(dates, today)
    if not ordered:
        return False
    return ordered[0] == today - timedelta(days=1)
