"""JSON persistence: atomic writes, and corrupt files quarantined not overwritten.

The failure this module exists to prevent: a truncated file used to be swallowed
by a bare `except`, the app started with empty data, and the next save wrote that
empty data over the only copy of the user's history.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReadResult:
    data: Any
    problem: str | None = None
    quarantined_to: Path | None = None

    @property
    def ok(self) -> bool:
        return self.problem is None


def read_json(path: str | Path, default: Any) -> ReadResult:
    """Read JSON, quarantining an unreadable file instead of silently ignoring it."""
    path = Path(path)
    if not path.exists():
        return ReadResult(data=default)

    try:
        with path.open("r", encoding="utf-8") as handle:
            return ReadResult(data=json.load(handle))
    except json.JSONDecodeError as exc:
        backup = _quarantine(path)
        return ReadResult(
            data=default,
            problem=f"{path.name} is not valid JSON ({exc}); it has been moved to {backup.name} "
            f"and a fresh file will be created.",
            quarantined_to=backup,
        )
    except OSError as exc:
        return ReadResult(data=default, problem=f"could not read {path.name}: {exc}")


def _quarantine(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = path.with_suffix(path.suffix + f".corrupt-{stamp}")
    counter = 1
    while backup.exists():
        backup = path.with_suffix(path.suffix + f".corrupt-{stamp}-{counter}")
        counter += 1
    path.rename(backup)
    return backup


def write_json(path: str | Path, data: Any) -> None:
    """Write atomically: a crash mid-write leaves the previous file intact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            json.dump(data, handle, indent=4)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        Path(handle.name).unlink(missing_ok=True)
        raise
