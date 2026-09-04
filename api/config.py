"""Runtime configuration, read from the environment."""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.factory import describe


@dataclass(frozen=True)
class Settings:
    database_url: str = "evertrack.db"
    title: str = "EverTrack API"
    version: str = "0.1.0"

    @property
    def safe_database_url(self) -> str:
        """The URL with any password removed, for logs and /health."""
        return describe(self.database_url)


def load_settings() -> Settings:
    """EVERTRACK_DATABASE_URL wins; EVERTRACK_DB stays as the SQLite shorthand."""
    url = os.environ.get("EVERTRACK_DATABASE_URL") or os.environ.get("EVERTRACK_DB", "evertrack.db")
    return Settings(database_url=url)
