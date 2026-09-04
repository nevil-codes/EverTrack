"""Build a repository from a URL or a path.

    evertrack.db                                 -> SQLite file
    sqlite:///evertrack.db                       -> SQLite file
    postgresql://user:pass@host:5432/evertrack   -> PostgreSQL
"""
from __future__ import annotations

from core.repository import Repository

POSTGRES_PREFIXES = ("postgres://", "postgresql://")
SQLITE_PREFIX = "sqlite:///"


def repository_from_url(url: str) -> Repository:
    if url.startswith(POSTGRES_PREFIXES):
        from core.postgres_repository import PostgresRepository

        return PostgresRepository(url)

    from core.sqlite_repository import SqliteRepository

    if url.startswith(SQLITE_PREFIX):
        url = url[len(SQLITE_PREFIX):]
    return SqliteRepository(url)


def describe(url: str) -> str:
    """A URL safe to print: no password."""
    if url.startswith(POSTGRES_PREFIXES) and "@" in url:
        scheme, _, rest = url.partition("://")
        credentials, _, location = rest.rpartition("@")
        user, separator, _password = credentials.partition(":")
        masked = f"{user}:***" if separator else user
        return f"{scheme}://{masked}@{location}"
    return url
