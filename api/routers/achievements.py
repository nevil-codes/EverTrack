"""Badge state, and the endpoint that re-evaluates it."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.deps import get_repository
from api.schemas import AchievementOut, AchievementsOut
from core import achievements as core_achievements
from core.repository import Repository

router = APIRouter(prefix="/achievements", tags=["achievements"])

Repo = Annotated[Repository, Depends(get_repository)]


def _render(unlocked: list[str]) -> AchievementsOut:
    held = set(unlocked)
    rows = [
        AchievementOut(
            code=item.code, name=item.name, description=item.description,
            icon=item.icon, points=item.points, unlocked=item.code in held,
        )
        for item in core_achievements.CATALOGUE
    ]
    return AchievementsOut(
        total_points=core_achievements.total_points(unlocked),
        unlocked=[row for row in rows if row.unlocked],
        locked=[row for row in rows if not row.unlocked],
    )


@router.get("", summary="Badges held and still to earn")
def list_achievements(repo: Repo) -> AchievementsOut:
    return _render(repo.get_unlocked())


@router.post("/refresh", summary="Re-evaluate the rules and unlock anything earned")
def refresh(repo: Repo) -> AchievementsOut:
    unlocked = repo.get_unlocked()
    earned = core_achievements.newly_unlocked(repo.list_logs(), repo.list_habits(), unlocked)
    if earned:
        unlocked = unlocked + earned
        repo.set_unlocked(unlocked)
    return _render(unlocked)
