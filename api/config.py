"""Runtime configuration, read from the environment."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database: str = "evertrack.db"
    title: str = "EverTrack API"
    version: str = "0.1.0"


def load_settings() -> Settings:
    return Settings(database=os.environ.get("EVERTRACK_DB", "evertrack.db"))
