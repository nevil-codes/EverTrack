from datetime import date, timedelta

from pytest import approx

from core import stats
from core.models import LogEntry

TODAY = date(2026, 9, 4)  # Friday


def entry(offset=0, habit="Meditation", duration=30, completed=True):
    return LogEntry(TODAY - timedelta(days=offset), habit, duration, completed)


def test_totals_on_empty_input():
    summary = stats.totals([])
    assert (summary.activities, summary.total_minutes, summary.active_days) == (0, 0, 0)
    assert summary.completion_rate == 0.0


def test_totals():
    summary = stats.totals([entry(0), entry(0, duration=60), entry(1, completed=False)])
    assert summary.activities == 3
    assert summary.total_minutes == 120
    assert summary.active_days == 2
    assert summary.completion_rate == approx(66.67, abs=0.01)


def test_minutes_per_habit():
    logs = [entry(habit="Reading", duration=10), entry(habit="Reading", duration=5), entry(duration=30)]
    assert stats.minutes_per_habit(logs) == {"Reading": 15, "Meditation": 30}


def test_minutes_per_day_is_ordered():
    logs = [entry(2), entry(0), entry(1)]
    assert list(stats.minutes_per_day(logs)) == sorted(log.log_date for log in logs)


def test_completion_rate_per_habit():
    logs = [entry(habit="Reading"), entry(habit="Reading", completed=False), entry()]
    rates = stats.completion_rate_per_habit(logs)
    assert rates == {"Reading": 50.0, "Meditation": 100.0}


def test_most_practiced():
    logs = [entry(habit="Reading"), entry(habit="Reading"), entry()]
    assert stats.most_practiced(logs) == ("Reading", 2)
    assert stats.most_practiced([]) is None


def test_weekly_buckets_are_ordered_and_zero_filled():
    buckets = stats.weekly_buckets([entry(0, duration=10), entry(20, duration=5)], TODAY)
    assert len(buckets) == 4                      # regression: 28 days ago produced a 5th bucket
    assert [minutes for _, minutes in buckets] == [0.0, 5.0, 0.0, 10.0]


def test_weekly_buckets_ignore_out_of_range_and_future_logs():
    future = LogEntry(TODAY + timedelta(days=3), "Meditation", 99)
    old = entry(60, duration=99)
    assert all(minutes == 0 for _, minutes in stats.weekly_buckets([future, old], TODAY))


def test_calendar_window_starts_on_a_monday_and_includes_today():
    dates, counts = stats.calendar_window([entry(0)], TODAY, weeks=8)

    assert len(dates) == 56
    assert dates[0].weekday() == 0            # regression: rows were mislabelled
    assert TODAY in dates                     # regression: today fell outside the window
    assert counts[TODAY] == 1


def test_calendar_window_counts_activities_per_day():
    _, counts = stats.calendar_window([entry(0), entry(0), entry(1)], TODAY)
    assert counts[TODAY] == 2
    assert counts[TODAY - timedelta(days=1)] == 1
