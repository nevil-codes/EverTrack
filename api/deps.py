"""Request-scoped dependencies."""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from api.config import Settings, load_settings
from core.repository import Repository
from core.sqlite_repository import SqliteRepository


@lru_cache
def settings() -> Settings:
    return load_settings()


def get_repository() -> Iterator[Repository]:
    """One connection per request.

    sqlite3 connections belong to the thread that created them, and FastAPI runs
    sync endpoints in a worker thread pool — so the repository is built and
    closed per request rather than shared.
    """
    repository = SqliteRepository(settings().database)
    try:
        yield repository
    finally:
        repository.close()
