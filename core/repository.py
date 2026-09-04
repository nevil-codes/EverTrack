"""The storage contract.

Every backend implements this, and nothing above it knows which one is in use.
Habits are addressed by name (unique, case-insensitive); log entries are
addressed by the id the repository assigns them.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import Habit, LogEntry


def default_settings() -> dict:
    """A fresh settings mapping.

    A module-level dict would be shared: a shallow copy hands every caller the
    same reminder_times object, and one reminder leaks into every backend.
    """
    return {"theme": "light", "notifications": True, "reminder_times": {}}


class Repository(ABC):
    # ---------------------------------------------------------------- habits

    @abstractmethod
    def list_habits(self) -> list[Habit]:
        """All habits, in creation order."""

    @abstractmethod
    def add_habit(self, habit: Habit) -> Habit:
        """Store a habit and return it with its id. Raises ValidationError on a
        duplicate name (compared case-insensitively)."""

    @abstractmethod
    def delete_habit(self, name: str) -> bool:
        """Delete a habit, its logs and its reminder. False when it did not exist."""

    # ------------------------------------------------------------------ logs

    @abstractmethod
    def list_logs(self) -> list[LogEntry]:
        """All log entries, oldest first, each carrying its id."""

    @abstractmethod
    def add_log(self, entry: LogEntry) -> LogEntry:
        """Store an entry and return it with its id."""

    @abstractmethod
    def delete_log(self, log_id: int) -> bool:
        """Delete exactly one entry. False when that id does not exist."""

    # -------------------------------------------------------------- settings

    @abstractmethod
    def get_settings(self) -> dict:
        """Settings mapping, defaults filled in."""

    @abstractmethod
    def save_settings(self, settings: dict) -> None:
        ...

    # ---------------------------------------------------------- achievements

    @abstractmethod
    def get_unlocked(self) -> list[str]:
        """Achievement codes unlocked so far."""

    @abstractmethod
    def set_unlocked(self, codes: list[str]) -> None:
        ...

    # ------------------------------------------------------------ lifecycle

    @abstractmethod
    def clear_all(self) -> None:
        """Delete habits, logs and achievements. Settings are reset by the caller."""

    def problems(self) -> list[str]:
        """Human-readable trouble found while reading storage (may be empty)."""
        return []

    def close(self) -> None:  # noqa: B027 - optional hook, not every backend holds resources
        """Release any resources. Safe to call more than once."""
        return None
