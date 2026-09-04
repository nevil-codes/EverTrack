from datetime import date, timedelta

from pipeline.quality import (
    DIM_EXPECTATIONS,
    FACT_EXPECTATIONS,
    Context,
    Severity,
    validate,
)

TODAY = date(2026, 9, 7)


def fact(habit="reading", day=TODAY, duration=30.0, completed=True, since_start=5):
    return {
        "habit_key": habit, "habit_name": habit.title() if habit else None, "log_date": day,
        "duration_min": duration, "completed": completed,
        "days_since_habit_start": since_start,
    }


def check(rows, name, dim=(("reading",),), as_of=TODAY):
    context = Context(dim_habit=[{"habit_key": key[0]} for key in dim], as_of=as_of)
    report = validate("fact_habit_log", rows, FACT_EXPECTATIONS, context)
    return next(result for result in report.results if result.expectation.name == name)


def test_clean_data_passes_everything():
    report = validate("fact_habit_log", [fact()], FACT_EXPECTATIONS,
                      Context(dim_habit=[{"habit_key": "reading"}], as_of=TODAY))
    assert report.ok
    assert report.failed == []


def test_null_habit_key_is_blocking():
    result = check([fact(habit=None)], "habit_key_not_null")
    assert result.failed == 1
    assert result.blocking


def test_null_duration_is_blocking():
    result = check([{**fact(), "duration_min": None}], "duration_not_null")
    assert result.blocking


def test_a_null_never_crashes_the_other_checks():
    """A null must be reported once, by its own expectation, not blow up the run."""
    rows = [{"habit_key": None, "habit_name": None, "log_date": None,
             "duration_min": None, "completed": True, "days_since_habit_start": None}]
    report = validate("fact_habit_log", rows, FACT_EXPECTATIONS,
                      Context(dim_habit=[], as_of=TODAY))

    failed = {result.expectation.name for result in report.failed}
    assert failed == {"habit_key_not_null", "log_date_not_null", "duration_not_null"}


def test_duration_bounds():
    assert check([fact(duration=0)], "duration_within_bounds").failed == 1
    assert check([fact(duration=-5)], "duration_within_bounds").failed == 1
    assert check([fact(duration=1441)], "duration_within_bounds").failed == 1
    assert check([fact(duration=1440)], "duration_within_bounds").failed == 0


def test_future_dates_are_blocking():
    result = check([fact(day=TODAY + timedelta(days=1))], "log_date_not_in_the_future")
    assert result.failed == 1 and result.blocking


def test_an_orphan_habit_is_blocking():
    result = check([fact(habit="ghost")], "habit_key_resolves")
    assert result.failed == 1 and result.blocking
    assert "Ghost" in result.sample[0]


def test_a_log_before_the_habit_started_warns():
    result = check([fact(since_start=-3)], "log_not_before_habit_start")
    assert result.failed == 1
    assert result.expectation.severity is Severity.WARN
    assert not result.blocking


def test_duplicate_entries_warn():
    result = check([fact(), fact(), fact(duration=31.0)], "no_duplicate_entries")
    assert result.failed == 1


def test_more_than_a_day_logged_for_one_habit_warns():
    rows = [fact(duration=800.0), fact(duration=700.0)]
    assert check(rows, "daily_total_within_a_day").failed == 2


def test_stale_data_warns():
    result = check([fact(day=TODAY - timedelta(days=30))], "dataset_is_fresh")
    assert result.failed == 1
    assert not result.blocking


def test_freshness_passes_on_an_empty_dataset():
    assert check([], "dataset_is_fresh").failed == 0


def test_report_separates_blocking_from_warnings():
    rows = [fact(habit="ghost"), fact(), fact()]
    report = validate("fact_habit_log", rows, FACT_EXPECTATIONS,
                      Context(dim_habit=[{"habit_key": "reading"}], as_of=TODAY))

    assert not report.ok
    assert {result.expectation.name for result in report.blocking} == {"habit_key_resolves"}
    assert {result.expectation.name for result in report.failed} >= {"no_duplicate_entries"}


def test_report_serializes_for_the_manifest():
    report = validate("fact_habit_log", [fact()], FACT_EXPECTATIONS,
                      Context(dim_habit=[{"habit_key": "reading"}], as_of=TODAY))
    payload = report.to_dict()

    assert payload["dataset"] == "fact_habit_log"
    assert payload["checks"] == len(FACT_EXPECTATIONS)
    assert payload["failed"] == 0
    assert {"name", "severity", "checked", "failed", "sample"} == set(payload["results"][0])


def test_report_renders_a_readable_summary():
    rendered = validate("fact_habit_log", [fact(habit="ghost")], FACT_EXPECTATIONS,
                        Context(dim_habit=[], as_of=TODAY)).render()
    assert "[FAIL] habit_key_resolves" in rendered


def test_dim_expectations():
    duplicate = [{"habit_key": "reading", "daily_target_min": 20,
                  "start_date": date(2026, 1, 1), "end_date": None}] * 2
    report = validate("dim_habit", duplicate, DIM_EXPECTATIONS)
    assert not report.ok

    bad_target = [{"habit_key": "a", "daily_target_min": 0,
                   "start_date": date(2026, 1, 1), "end_date": None}]
    assert not validate("dim_habit", bad_target, DIM_EXPECTATIONS).ok

    bad_dates = [{"habit_key": "a", "daily_target_min": 10,
                  "start_date": date(2026, 5, 1), "end_date": date(2026, 1, 1)}]
    assert not validate("dim_habit", bad_dates, DIM_EXPECTATIONS).ok
