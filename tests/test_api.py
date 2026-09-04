"""API tests. Each test gets its own database through a dependency override."""
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from api.deps import get_repository
from api.main import create_app
from core.sqlite_repository import SqliteRepository

TODAY = date.today()


@pytest.fixture
def client(tmp_path):
    app = create_app()
    database = tmp_path / "api.db"

    def repository_for_this_test():
        repository = SqliteRepository(database)
        try:
            yield repository
        finally:
            repository.close()

    app.dependency_overrides[get_repository] = repository_for_this_test
    with TestClient(app) as test_client:
        yield test_client


def make_habit(client, name="Reading", target=20):
    return client.post("/habits", json={"name": name, "daily_target_min": target})


def make_log(client, habit="Reading", duration=25.0, offset=0, completed=True):
    return client.post("/logs", json={
        "habit": habit,
        "duration_min": duration,
        "log_date": str(TODAY - timedelta(days=offset)),
        "completed": completed,
    })


# ------------------------------------------------------------------- meta

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_document_is_generated(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "EverTrack API"
    assert "/habits" in schema["paths"]


# ----------------------------------------------------------------- habits

def test_create_and_list_habits(client):
    created = make_habit(client)
    assert created.status_code == 201

    body = created.json()
    assert body["name"] == "Reading"
    assert body["id"] is not None
    assert body["start_date"] == str(TODAY)   # defaults to today
    assert body["end_date"] is None

    assert [h["name"] for h in client.get("/habits").json()] == ["Reading"]


def test_duplicate_habit_is_a_conflict(client):
    make_habit(client)
    duplicate = make_habit(client, name="reading")
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "daily_target_min": 20},
        {"name": "X", "daily_target_min": 0},
        {"name": "X", "daily_target_min": -5},
        {"name": "X"},
        {"name": "X", "daily_target_min": 20, "start_date": "01-09-2026"},
        {"name": "X", "daily_target_min": 20, "status": "sleeping"},
    ],
)
def test_invalid_habit_payloads_are_rejected(client, payload):
    assert client.post("/habits", json=payload).status_code == 422


def test_end_date_before_start_date_is_rejected(client):
    response = client.post("/habits", json={
        "name": "X", "daily_target_min": 20,
        "start_date": "2026-09-01", "end_date": "2026-08-01",
    })
    assert response.status_code == 422


def test_get_habit_is_case_insensitive(client):
    make_habit(client)
    assert client.get("/habits/reading").json()["name"] == "Reading"


def test_get_unknown_habit_is_404(client):
    assert client.get("/habits/ghost").status_code == 404


def test_active_only_filter(client):
    make_habit(client)
    client.post("/habits", json={"name": "Old", "daily_target_min": 10, "status": "Archived"})

    assert len(client.get("/habits").json()) == 2
    assert [h["name"] for h in client.get("/habits", params={"active_only": True}).json()] == ["Reading"]


def test_deleting_a_habit_removes_its_logs(client):
    make_habit(client)
    make_log(client)

    assert client.delete("/habits/Reading").status_code == 204
    assert client.get("/logs").json() == []
    assert client.delete("/habits/Reading").status_code == 404


# ------------------------------------------------------------------- logs

def test_create_and_list_logs(client):
    make_habit(client)
    created = make_log(client, duration=22.5)

    assert created.status_code == 201
    assert created.json()["duration_min"] == 22.5
    assert created.json()["id"] is not None
    assert len(client.get("/logs").json()) == 1


def test_log_for_an_unknown_habit_is_404(client):
    response = make_log(client, habit="Ghost")
    assert response.status_code == 404
    assert "no habit named" in response.json()["detail"]


@pytest.mark.parametrize("duration", [0, -1, 1441])
def test_invalid_durations_are_rejected(client, duration):
    make_habit(client)
    assert make_log(client, duration=duration).status_code == 422


def test_future_dates_are_rejected(client):
    make_habit(client)
    response = client.post("/logs", json={
        "habit": "Reading", "duration_min": 10, "log_date": str(TODAY + timedelta(days=1)),
    })
    assert response.status_code == 422


def test_log_filters(client):
    make_habit(client)
    make_habit(client, name="Yoga", target=30)
    make_log(client, offset=0)
    make_log(client, offset=5)
    make_log(client, habit="Yoga", offset=1)

    assert len(client.get("/logs", params={"habit": "yoga"}).json()) == 1
    recent = client.get("/logs", params={"from": str(TODAY - timedelta(days=2))}).json()
    assert len(recent) == 2
    assert len(client.get("/logs", params={"to": str(TODAY - timedelta(days=3))}).json()) == 1


def test_delete_one_log_leaves_its_duplicate(client):
    make_habit(client)
    first = make_log(client).json()
    make_log(client)

    assert client.delete(f"/logs/{first['id']}").status_code == 204
    assert len(client.get("/logs").json()) == 1
    assert client.delete(f"/logs/{first['id']}").status_code == 404


# ----------------------------------------------------------------- parser

def test_parse_without_committing(client):
    make_habit(client)
    response = client.post("/logs/parse", json={"text": "read for an hour and 15 mins"})

    assert response.status_code == 200
    body = response.json()
    assert (body["habit"], body["duration_min"]) == ("Reading", 75)
    assert body["stored"] is None
    assert client.get("/logs").json() == []


def test_parse_and_commit(client):
    make_habit(client)
    body = client.post("/logs/parse", json={"text": "read for 30 minutes yesterday",
                                            "commit": True}).json()

    assert body["log_date"] == str(TODAY - timedelta(days=1))
    assert body["stored"]["id"] is not None
    assert len(client.get("/logs").json()) == 1


def test_parse_failure_explains_itself(client):
    response = client.post("/logs/parse", json={"text": "i spread butter for 10 minutes"})
    assert response.status_code == 422
    assert "did not recognise" in response.json()["detail"]


def test_parse_commit_for_an_unknown_habit_is_404(client):
    response = client.post("/logs/parse", json={"text": "yoga for 20 minutes", "commit": True})
    assert response.status_code == 404


# ------------------------------------------------------------------ stats

def test_summary(client):
    make_habit(client)
    make_log(client, duration=30, offset=0)
    make_log(client, duration=10, offset=1, completed=False)

    body = client.get("/stats/summary").json()
    assert body["activities"] == 2
    assert body["total_minutes"] == 40
    assert body["active_days"] == 2
    assert body["completion_rate"] == 50.0


def test_streak(client):
    make_habit(client)
    for offset in range(3):
        make_log(client, offset=offset)

    body = client.get("/stats/streak").json()
    assert body == {"current": 3, "longest": 3, "at_risk": False}


def test_daily_is_ordered_oldest_first(client):
    make_habit(client)
    make_log(client, offset=0)
    make_log(client, offset=2)

    days = client.get("/stats/daily").json()
    assert [row["log_date"] for row in days] == [
        str(TODAY - timedelta(days=2)), str(TODAY)]


def test_per_habit_totals_are_sorted_by_time(client):
    make_habit(client)
    make_habit(client, name="Yoga", target=30)
    make_log(client, duration=10)
    make_log(client, habit="Yoga", duration=60)

    rows = client.get("/stats/habits").json()
    assert [row["habit"] for row in rows] == ["Yoga", "Reading"]


def test_weekly_buckets(client):
    make_habit(client)
    make_log(client, duration=45)

    buckets = client.get("/stats/weekly", params={"weeks": 4}).json()
    assert len(buckets) == 4
    assert buckets[-1]["total_minutes"] == 45


def test_stats_on_an_empty_database(client):
    assert client.get("/stats/summary").json()["activities"] == 0
    assert client.get("/stats/streak").json()["current"] == 0
    assert client.get("/stats/daily").json() == []
    assert client.get("/stats/habits").json() == []


# ----------------------------------------------------------- achievements

def test_achievements_start_locked(client):
    body = client.get("/achievements").json()
    assert body["total_points"] == 0
    assert body["unlocked"] == []
    assert len(body["locked"]) == 14


def test_refresh_unlocks_what_was_earned(client):
    make_habit(client)
    make_log(client)

    body = client.post("/achievements/refresh").json()
    codes = {row["code"] for row in body["unlocked"]}

    assert "first_log" in codes
    assert body["total_points"] > 0
    # and it is idempotent
    assert client.post("/achievements/refresh").json()["total_points"] == body["total_points"]


def test_api_and_desktop_share_the_same_database(client, tmp_path):
    """The point of the repository interface: one store, two front ends."""
    from data_manager import DataManager

    make_habit(client)
    make_log(client, duration=42)

    desktop = DataManager.sqlite(tmp_path / "api.db")
    try:
        assert [h["name"] for h in desktop.habits_list] == ["Reading"]
        assert [entry.duration_min for entry in desktop.log_models()] == [42.0]
    finally:
        desktop.close()
