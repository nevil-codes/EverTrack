"""End-to-end: operational store in, validated Parquet dataset out."""
import json
from datetime import date, timedelta

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pytest

from core.models import Habit, LogEntry
from core.sqlite_repository import SqliteRepository
from pipeline.run import EXIT_OK, EXIT_QUALITY, main, run

TODAY = date.today()


@pytest.fixture
def store(tmp_path):
    """A small but real SQLite store spanning two months."""
    path = tmp_path / "evertrack.db"
    repository = SqliteRepository(path)
    repository.add_habit(Habit("Reading", TODAY - timedelta(days=90), 20))
    repository.add_habit(Habit("Yoga", TODAY - timedelta(days=90), 30))
    for offset in (0, 1, 2, 40, 41):
        repository.add_log(LogEntry(TODAY - timedelta(days=offset), "Reading", 25.0))
        repository.add_log(LogEntry(TODAY - timedelta(days=offset), "Yoga", 35.0, completed=False))
    repository.close()
    return path


def read(root, name):
    return ds.dataset(str(root / name), format="parquet", partitioning="hive").to_table()


def test_publishes_both_datasets(store, tmp_path):
    out = tmp_path / "warehouse"
    outcome = run(str(store), out)

    assert outcome.published
    assert {dataset.name for dataset in outcome.datasets} == {"dim_habit", "fact_habit_log"}
    assert read(out, "dim_habit").num_rows == 2
    assert read(out, "fact_habit_log").num_rows == 10


def test_fact_is_partitioned_by_year_and_month(store, tmp_path):
    out = tmp_path / "warehouse"
    run(str(store), out)

    directories = sorted(p.name for p in (out / "fact_habit_log").iterdir() if p.is_dir())
    assert all(name.startswith("year=") for name in directories)

    months = {p.name for p in (out / "fact_habit_log").rglob("month=*")}
    assert months, "expected month partitions below the year directories"


def test_partition_pruning_reads_one_fragment(store, tmp_path):
    out = tmp_path / "warehouse"
    run(str(store), out)

    dataset = ds.dataset(str(out / "fact_habit_log"), format="parquet", partitioning="hive")
    condition = (pc.field("year") == TODAY.year) & (pc.field("month") == TODAY.month)
    assert len(list(dataset.get_fragments(filter=condition))) == 1


def test_values_survive_the_round_trip(store, tmp_path):
    out = tmp_path / "warehouse"
    run(str(store), out)

    table = read(out, "fact_habit_log")
    rows = {row["habit_name"] for row in table.to_pylist()}
    assert rows == {"Reading", "Yoga"}

    yoga = [row for row in table.to_pylist() if row["habit_name"] == "Yoga"][0]
    assert yoga["duration_min"] == 35.0
    assert yoga["completed"] is False
    assert yoga["met_target"] is True     # 35 >= 30


def test_manifest_records_the_run(store, tmp_path):
    out = tmp_path / "warehouse"
    outcome = run(str(store), out)

    manifest = json.loads(outcome.manifest.read_text())
    assert len(manifest["run_id"]) == 12
    assert manifest["source"].endswith("evertrack.db")
    assert {d["name"]: d["rows"] for d in manifest["datasets"]} == \
        {"dim_habit": 2, "fact_habit_log": 10}
    assert [report["failed"] for report in manifest["quality"]] == [0, 0]
    assert manifest["finished_at"] >= manifest["started_at"]


def test_rerunning_replaces_rather_than_appends(store, tmp_path):
    out = tmp_path / "warehouse"
    run(str(store), out)
    run(str(store), out)

    assert read(out, "fact_habit_log").num_rows == 10
    assert read(out, "dim_habit").num_rows == 2


def test_dry_run_validates_without_writing(store, tmp_path):
    out = tmp_path / "warehouse"
    outcome = run(str(store), out, dry_run=True)

    assert not outcome.published
    assert all(report.ok for report in outcome.reports)
    assert not out.exists()


def test_a_blocking_violation_prevents_publication(tmp_path):
    """The JSON store has no constraints, so it is where bad data comes from."""
    source = tmp_path / "json"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps([{
        "name": "Reading", "start_date": str(TODAY - timedelta(days=5)),
        "end_date": "No Limit", "daily_target": 20, "status": "Active"}]))
    (source / "habits_data.json").write_text(json.dumps([
        {"date": str(TODAY), "habit": "Ghost", "duration": 10, "completed": True},
    ]))

    out = tmp_path / "warehouse"
    outcome = run(str(source), out)

    assert not outcome.published
    assert not out.exists()
    assert [result.expectation.name for result in outcome.reports[1].blocking] == \
        ["habit_key_resolves"]


def test_warnings_alone_still_publish(tmp_path):
    source = tmp_path / "json"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps([{
        "name": "Reading", "start_date": str(TODAY), "end_date": "No Limit",
        "daily_target": 20, "status": "Active"}]))
    (source / "habits_data.json").write_text(json.dumps([
        {"date": str(TODAY), "habit": "Reading", "duration": 10, "completed": True},
        {"date": str(TODAY), "habit": "Reading", "duration": 10, "completed": True},
    ]))

    out = tmp_path / "warehouse"
    outcome = run(str(source), out)

    assert outcome.published
    assert any(report.failed for report in outcome.reports)


def test_fail_on_warn_blocks_the_same_data(tmp_path):
    source = tmp_path / "json"
    source.mkdir()
    (source / "habits_list.json").write_text(json.dumps([{
        "name": "Reading", "start_date": str(TODAY), "end_date": "No Limit",
        "daily_target": 20, "status": "Active"}]))
    (source / "habits_data.json").write_text(json.dumps([
        {"date": str(TODAY), "habit": "Reading", "duration": 10, "completed": True},
        {"date": str(TODAY), "habit": "Reading", "duration": 10, "completed": True},
    ]))

    outcome = run(str(source), tmp_path / "warehouse", fail_on_warn=True)
    assert not outcome.published


def test_an_empty_store_publishes_empty_datasets(tmp_path):
    empty = tmp_path / "empty.db"
    SqliteRepository(empty).close()

    out = tmp_path / "warehouse"
    outcome = run(str(empty), out)

    assert outcome.published
    assert read(out, "dim_habit").num_rows == 0


def test_cli_exit_codes(store, tmp_path, capsys):
    assert main(["--source", str(store), "--out", str(tmp_path / "w")]) == EXIT_OK
    assert "wrote fact_habit_log" in capsys.readouterr().out

    assert main(["--source", str(store), "--out", str(tmp_path / "w2"), "--dry-run"]) == EXIT_OK
    assert "dry run" in capsys.readouterr().out


def test_cli_reports_a_quality_failure(tmp_path, capsys):
    source = tmp_path / "json"
    source.mkdir()
    (source / "habits_data.json").write_text(json.dumps([
        {"date": str(TODAY), "habit": "Ghost", "duration": 10, "completed": True}]))

    assert main(["--source", str(source), "--out", str(tmp_path / "w")]) == EXIT_QUALITY
    assert "data quality gate failed" in capsys.readouterr().out
