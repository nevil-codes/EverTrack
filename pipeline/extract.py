"""Read the operational store. The only step that knows where data comes from."""
from __future__ import annotations

from dataclasses import dataclass

from core.factory import repository_from_url
from core.models import Habit, LogEntry


@dataclass(frozen=True)
class Extracted:
    habits: list[Habit]
    logs: list[LogEntry]
    source: str


def extract(source_url: str) -> Extracted:
    repository = repository_from_url(source_url)
    try:
        return Extracted(
            habits=repository.list_habits(),
            logs=repository.list_logs(),
            source=source_url,
        )
    finally:
        repository.close()
