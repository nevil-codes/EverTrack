"""Request-scoped dependencies."""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from api.config import Settings, load_settings
from core.factory import repository_from_url
from core.repository import Repository


@lru_cache
def settings() -> Settings:
    return load_settings()


def get_repository() -> Iterator[Repository]:
    """One connection per request.

    Both drivers tie a connection to the thread that opened it, and FastAPI runs
    sync endpoints in a worker thread pool — so the repository is built and
    closed per request rather than shared. A pool belongs here when load
    justifies it; correctness comes first.
    """
    repository = repository_from_url(settings().database_url)
    try:
        yield repository
    finally:
        repository.close()
