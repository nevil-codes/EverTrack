import json

from core.storage import read_json, write_json


def test_missing_file_returns_the_default(tmp_path):
    result = read_json(tmp_path / "absent.json", [])
    assert result.ok and result.data == []


def test_round_trip(tmp_path):
    path = tmp_path / "data.json"
    write_json(path, [{"a": 1}])
    assert read_json(path, []).data == [{"a": 1}]


def test_corrupt_file_is_quarantined_not_silently_dropped(tmp_path):
    # regression: a truncated file was swallowed, the app started empty, and the
    # next save overwrote the only copy of the user's history
    path = tmp_path / "habits_data.json"
    path.write_text('[{"date": "2025-12-21",')

    result = read_json(path, [])

    assert result.data == []
    assert result.problem is not None
    assert result.quarantined_to.exists()
    assert result.quarantined_to.read_text().startswith('[{"date"')
    assert not path.exists()


def test_write_is_atomic_and_leaves_no_temp_files(tmp_path):
    path = tmp_path / "data.json"
    write_json(path, {"a": 1})
    write_json(path, {"a": 2})

    assert json.loads(path.read_text()) == {"a": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_failed_write_leaves_the_previous_file_intact(tmp_path):
    path = tmp_path / "data.json"
    write_json(path, {"good": True})

    class Unserializable:
        pass

    try:
        write_json(path, {"bad": Unserializable()})
    except TypeError:
        pass

    assert json.loads(path.read_text()) == {"good": True}
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]
