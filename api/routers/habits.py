"""Habit endpoints."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.deps import get_repository
from api.schemas import HabitIn, HabitOut
from core.models import ValidationError
from core.repository import Repository

router = APIRouter(prefix="/habits", tags=["habits"])

Repo = Annotated[Repository, Depends(get_repository)]


@router.get("", summary="List habits")
def list_habits(repo: Repo, active_only: bool = False) -> list[HabitOut]:
    habits = repo.list_habits()
    if active_only:
        habits = [habit for habit in habits if habit.is_active]
    return [HabitOut.from_domain(habit) for habit in habits]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a habit",
             responses={409: {"description": "a habit with that name already exists"}})
def create_habit(payload: HabitIn, repo: Repo) -> HabitOut:
    try:
        return HabitOut.from_domain(repo.add_habit(payload.to_domain()))
    except ValidationError as exc:
        if "already exists" in str(exc):
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.get("/{name}", summary="Fetch one habit")
def get_habit(name: str, repo: Repo) -> HabitOut:
    for habit in repo.list_habits():
        if habit.name.lower() == name.lower():
            return HabitOut.from_domain(habit)
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"no habit named {name!r}")


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a habit, its logs and its reminder")
def delete_habit(name: str, repo: Repo) -> Response:
    if not repo.delete_habit(name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no habit named {name!r}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
