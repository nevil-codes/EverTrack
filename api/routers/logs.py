"""Activity log endpoints, including the plain-English parser."""
from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from api.deps import get_repository
from api.schemas import LogIn, LogOut, ParsedOut, ParseIn
from core.models import ValidationError
from core.parser import parse
from core.repository import Repository

router = APIRouter(prefix="/logs", tags=["logs"])

Repo = Annotated[Repository, Depends(get_repository)]


@router.get("", summary="List log entries")
def list_logs(
    repo: Repo,
    habit: str | None = Query(default=None, description="filter by habit name"),
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[LogOut]:
    entries = repo.list_logs()
    if habit:
        entries = [entry for entry in entries if entry.habit.lower() == habit.lower()]
    if date_from:
        entries = [entry for entry in entries if entry.log_date >= date_from]
    if date_to:
        entries = [entry for entry in entries if entry.log_date <= date_to]
    return [LogOut.from_domain(entry) for entry in entries[-limit:]]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Log an activity",
             responses={404: {"description": "the habit does not exist"}})
def create_log(payload: LogIn, repo: Repo) -> LogOut:
    try:
        return LogOut.from_domain(repo.add_log(payload.to_domain()))
    except ValidationError as exc:
        if "no habit named" in str(exc):
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.post("/parse", summary="Parse plain English into an activity",
             responses={422: {"description": "the text could not be parsed"}})
def parse_log(payload: ParseIn, repo: Repo) -> ParsedOut:
    result = parse(payload.text)
    if not result.ok:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, result.problem)

    activity = result.activity
    parsed = ParsedOut(
        habit=activity.habit,
        duration_min=activity.duration_min,
        log_date=activity.log_date,
    )
    if not payload.commit:
        return parsed

    entry = LogIn(habit=activity.habit, duration_min=activity.duration_min,
                  log_date=activity.log_date)
    parsed.stored = create_log(entry, repo)
    return parsed


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete one entry")
def delete_log(log_id: int, repo: Repo) -> Response:
    if not repo.delete_log(log_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no log entry with id {log_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
