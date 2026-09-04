from datetime import date, timedelta

from core.streak import current_streak, longest_streak, streak_is_at_risk

TODAY = date(2026, 9, 4)


def days(*offsets):
    return [TODAY - timedelta(days=offset) for offset in offsets]


def test_no_data():
    assert current_streak([], TODAY) == 0
    assert longest_streak([], TODAY) == 0


def test_consecutive_days_ending_today():
    assert current_streak(days(0, 1, 2), TODAY) == 3


def test_streak_survives_until_a_whole_day_is_missed():
    # regression: a streak ending yesterday used to report 0
    assert current_streak(days(1, 2, 3), TODAY) == 3


def test_streak_broken_after_two_missed_days():
    assert current_streak(days(2, 3, 4), TODAY) == 0


def test_future_dates_are_ignored():
    # regression: one future-dated log used to zero the streak permanently
    dates = days(0, 1, 2) + [TODAY + timedelta(days=3)]
    assert current_streak(dates, TODAY) == 3


def test_duplicate_days_count_once():
    assert current_streak(days(0, 0, 1, 1), TODAY) == 2


def test_longest_streak_finds_the_best_run():
    dates = days(0, 1, 20, 21, 22, 23, 40)
    assert longest_streak(dates, TODAY) == 4


def test_longest_streak_with_a_single_day():
    assert longest_streak(days(5), TODAY) == 1


def test_at_risk_only_when_today_is_empty():
    assert streak_is_at_risk(days(1, 2), TODAY) is True
    assert streak_is_at_risk(days(0, 1), TODAY) is False
    assert streak_is_at_risk([], TODAY) is False
