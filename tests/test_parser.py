"""The parser writes straight to permanent storage, so it gets the most tests."""
from datetime import date, timedelta

import pytest

from core.parser import extract_duration, extract_habit, parse, suggest_habit

TODAY = date(2026, 9, 4)  # a Friday


@pytest.mark.parametrize(
    "text, minutes",
    [
        ("30 minutes", 30),
        ("45 mins", 45),
        ("20 min", 20),
        ("an hour", 60),
        ("one hour", 60),
        ("2 hours", 120),
        ("half an hour", 30),
        ("1 hour 30 minutes", 90),
        ("1 hour and 15 mins", 75),
        ("1.5 hours", 90),          # regression: used to read the "5" and return 300
        ("1,5 hours", 90),
    ],
)
def test_extract_duration(text, minutes):
    assert extract_duration(text) == minutes


def test_only_the_first_duration_is_used():
    # regression: durations from two separate activities used to be summed
    assert extract_duration("coded for 90 minutes and read for 20 minutes") == 90


def test_duration_absent():
    assert extract_duration("i meditated") is None


@pytest.mark.parametrize(
    "text, habit",
    [
        ("i meditated", "Meditation"),
        ("meditation session", "Meditation"),
        ("did a workout", "Exercise"),
        ("went to the gym", "Exercise"),
        ("i read", "Reading"),
        ("some reading", "Reading"),
        ("i coded", "Coding"),
        ("i wrote", "Writing"),
        ("i studied", "Studying"),      # regression: "study" is not in "studied"
        ("studying tonight", "Studying"),
        ("i ran", "Running"),
        ("went jogging", "Running"),
        ("walked the dog", "Walking"),
        ("yoga class", "Yoga"),
    ],
)
def test_extract_habit(text, habit):
    assert extract_habit(text) == habit


def test_habit_matching_respects_word_boundaries():
    # regression: "spread" contains "read" and used to be logged as Reading
    assert extract_habit("i spread butter") is None


def test_earliest_habit_wins():
    assert extract_habit("i coded for a while then read") == "Coding"


def test_parse_happy_path():
    result = parse("I meditated for 30 minutes", TODAY)
    assert result.ok
    assert result.activity.habit == "Meditation"
    assert result.activity.duration_min == 30
    assert result.activity.log_date == TODAY


def test_parse_yesterday():
    # regression: relative days were ignored and the entry was stamped today
    result = parse("I meditated yesterday for 30 minutes", TODAY)
    assert result.activity.log_date == TODAY - timedelta(days=1)


def test_parse_days_ago():
    result = parse("ran 3 days ago for 25 min", TODAY)
    assert result.activity.log_date == TODAY - timedelta(days=3)


def test_parse_pairs_the_first_habit_with_the_first_duration():
    result = parse("I coded for 90 minutes and read for 20 minutes", TODAY)
    assert (result.activity.habit, result.activity.duration_min) == ("Coding", 90)


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("", "Nothing to parse"),
        ("I meditated", "duration"),
        ("exercise for 0 minutes", "greater than zero"),
        ("yoga for 999999 minutes", "more than a day"),
        ("I spread butter for 10 minutes", "did not recognise"),
    ],
)
def test_parse_failures_explain_themselves(text, fragment):
    result = parse(text, TODAY)
    assert not result.ok
    assert fragment.lower() in result.problem.lower()


def test_suggest_habit_matches_keyword():
    assert suggest_habit("I want to read more")["name"] == "Reading"


def test_suggest_habit_falls_back_to_the_goal_text():
    assert suggest_habit("play piano")["name"] == "Play Piano"
