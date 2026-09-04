"""Build a repository from a URL or a path.

    evertrack.db                                 -> SQLite file
    sqlite:///evertrack.db                       -> SQLite file
    postgresql://user:pass@host:5432/evertrack   -> PostgreSQL
    json:///path/to/dir  or  a directory path    -> the four JSON files
"""
from __future__ import annotations

from pathlib import Path

from core.repository import Repository

POSTGRES_PREFIXES = ("postgres://", "postgresql://")
SQLITE_PREFIX = "sqlite:///"
JSON_PREFIX = "json://"


def repository_from_url(url: str) -> Repository:
    if url.startswith(POSTGRES_PREFIXES):
        from core.postgres_repository import PostgresRepository

        return PostgresRepository(url)

    if url.startswith(JSON_PREFIX):
        from core.json_repository import JsonRepository

        return JsonRepository(url[len(JSON_PREFIX):].lstrip("/") or ".")

    if url.startswith(SQLITE_PREFIX):
        url = url[len(SQLITE_PREFIX):]

    # A directory holds the JSON files; a file (or a path that does not exist
    # yet) is a SQLite database.
    if Path(url).is_dir():
        from core.json_repository import JsonRepository

        return JsonRepository(url)

    from core.sqlite_repository import SqliteRepository

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
