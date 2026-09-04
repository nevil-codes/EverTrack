"""Plain-English activity parser.

Rule-based on purpose: a regex for the duration, a keyword table for the habit,
and a small vocabulary of relative day words. No model, no network.

Known limits, stated rather than hidden:
  * only the first activity in a sentence is returned
  * the habit vocabulary is fixed (see HABIT_PATTERNS)
  * anything it cannot parse is reported, never guessed
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

from core.models import MAX_DURATION_MIN

# Canonical habit -> the words that mean it. Matched on word boundaries, so
# "spread" no longer counts as "read".
HABIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "Meditation": ("meditate", "meditated", "meditating", "meditation"),
    "Exercise": ("exercise", "exercised", "exercising", "workout", "worked out", "gym"),
    "Reading": ("read", "reads", "reading"),
    "Coding": ("code", "coded", "coding", "program", "programmed", "programming"),
    "Writing": ("write", "writes", "writing", "wrote", "journal", "journaling"),
    "Studying": ("study", "studied", "studying", "revise", "revised", "revising"),
    "Learning": ("learn", "learned", "learnt", "learning"),
    "Yoga": ("yoga",),
    "Running": ("run", "ran", "running", "jog", "jogged", "jogging"),
    "Walking": ("walk", "walked", "walking"),
    "Stretching": ("stretch", "stretched", "stretching"),
}

_HABIT_REGEXES = {
    habit: re.compile(r"\b(?:{})\b".format("|".join(sorted(words, key=len, reverse=True))))
    for habit, words in HABIT_PATTERNS.items()
}

_NUMBER = r"\d+(?:[.,]\d+)?"
_HOURS = re.compile(rf"({_NUMBER}|half an|half a|an|one|a)\s*(?:hours?|hrs?|hr|h)\b")
_MINUTES = re.compile(rf"({_NUMBER})\s*(?:minutes?|mins?|min|m)\b")
_DAYS_AGO = re.compile(r"\b(\d+)\s+days?\s+ago\b")

_WORD_HOURS = {"an": 1.0, "a": 1.0, "one": 1.0, "half an": 0.5, "half a": 0.5}


@dataclass(frozen=True)
class ParsedActivity:
    habit: str
    duration_min: float
    log_date: date


@dataclass(frozen=True)
class ParseResult:
    activity: ParsedActivity | None = None
    problem: str | None = None

    @property
    def ok(self) -> bool:
        return self.activity is not None


def _to_number(token: str) -> float | None:
    token = token.strip()
    if token in _WORD_HOURS:
        return _WORD_HOURS[token]
    try:
        return float(token.replace(",", "."))
    except ValueError:
        return None


# Text allowed to sit between two parts of one duration ("1 hour and 30 minutes").
_JOINER = re.compile(r"^[\s,]*(?:and\s*)?$")


def _duration_matches(text: str) -> list[tuple[int, int, float]]:
    """All duration mentions as (start, end, minutes), in reading order."""
    found: list[tuple[int, int, float]] = []
    for match in _HOURS.finditer(text):
        hours = _to_number(match.group(1))
        if hours is not None:
            found.append((match.start(), match.end(), hours * 60))
    for match in _MINUTES.finditer(text):
        minutes = _to_number(match.group(1))
        if minutes is not None:
            found.append((match.start(), match.end(), minutes))
    return sorted(found)


def extract_duration(text: str) -> float | None:
    """Minutes for the *first* duration in the text.

    Adjacent parts are summed ("1 hour 30 minutes" -> 90), but a second,
    separate duration later in the sentence is ignored rather than folded in:
    "coded for 90 minutes and read for 20 minutes" is 90, not 110.
    """
    matches = _duration_matches(text)
    if not matches:
        return None

    total = matches[0][2]
    end = matches[0][1]
    for start, next_end, minutes in matches[1:]:
        if not _JOINER.match(text[end:start]):
            break
        total += minutes
        end = next_end
    return total


def extract_habit(text: str) -> str | None:
    """The habit whose keyword appears earliest; longest keyword breaks ties."""
    best: tuple[int, int, str] | None = None
    for habit, regex in _HABIT_REGEXES.items():
        match = regex.search(text)
        if match is None:
            continue
        candidate = (match.start(), -len(match.group(0)), habit)
        if best is None or candidate < best:
            best = candidate
    return best[2] if best else None


def extract_date(text: str, today: date) -> date:
    """Resolve relative day words. Defaults to today."""
    if re.search(r"\byesterday\b", text):
        return today - timedelta(days=1)
    days_ago = _DAYS_AGO.search(text)
    if days_ago:
        return today - timedelta(days=int(days_ago.group(1)))
    return today


def parse(text: str, today: date | None = None) -> ParseResult:
    """Parse free text into an activity, or explain why it could not."""
    today = today or date.today()
    if not text or not text.strip():
        return ParseResult(problem="Nothing to parse.")

    lowered = text.lower()

    duration = extract_duration(lowered)
    if duration is None:
        return ParseResult(
            problem="I could not find a duration. Try '30 minutes', '45 mins' or 'an hour'."
        )
    if duration <= 0:
        return ParseResult(problem="Duration must be greater than zero.")
    if duration > MAX_DURATION_MIN:
        return ParseResult(
            problem=f"{duration:.0f} minutes is more than a day — please check the number."
        )

    habit = extract_habit(lowered)
    if habit is None:
        known = ", ".join(sorted(HABIT_PATTERNS))
        return ParseResult(problem=f"I did not recognise the activity. I know about: {known}.")

    return ParseResult(
        activity=ParsedActivity(habit=habit, duration_min=duration, log_date=extract_date(lowered, today))
    )


def suggest_habit(goal: str) -> dict:
    """Suggest a starting habit from a free-text goal."""
    suggestions = {
        "read": {"name": "Reading", "target": 30, "tip": "Start with 30 minutes daily"},
        "exercise": {"name": "Exercise", "target": 45, "tip": "Consistency beats intensity"},
        "meditat": {"name": "Meditation", "target": 15, "tip": "Even 10-15 minutes helps"},
        "code": {"name": "Coding Practice", "target": 60, "tip": "Daily practice builds skills"},
        "writ": {"name": "Writing", "target": 20, "tip": "Write freely without judgment"},
        "learn": {"name": "Learning", "target": 45, "tip": "Focus on understanding"},
        "run": {"name": "Running", "target": 30, "tip": "Build distance slowly"},
    }
    lowered = (goal or "").lower()
    for keyword, suggestion in suggestions.items():
        if keyword in lowered:
            return suggestion
    return {"name": goal.strip().title() or "New Habit", "target": 30, "tip": "Start small and be consistent"}
