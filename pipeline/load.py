"""Write the Parquet dataset, and a manifest describing the run.

fact_habit_log is partitioned by year and month, so a reader scanning one month
touches one directory. dim_habit is small and written whole.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

COMPRESSION = "zstd"


@dataclass
class DatasetResult:
    name: str
    rows: int
    files: list[str] = field(default_factory=list)
    partitions: list[str] = field(default_factory=list)


def write_dataset(
    table: pa.Table,
    root: Path,
    name: str,
    partition_columns: list[str] | None = None,
) -> DatasetResult:
    """Write one table. Re-running replaces the partitions it touches."""
    target = root / name
    target.mkdir(parents=True, exist_ok=True)

    pq.write_to_dataset(
        table,
        root_path=str(target),
        partitioning=(
            ds.partitioning(
                pa.schema([table.schema.field(column) for column in partition_columns]),
                flavor="hive",
            ) if partition_columns else None
        ),
        existing_data_behavior="delete_matching",
        compression=COMPRESSION,
        basename_template="part-{i}.parquet",
    )

    files = sorted(str(path.relative_to(root)) for path in target.rglob("*.parquet"))
    partitions = sorted({str(Path(f).parent.relative_to(name)) for f in files} - {"."})
    return DatasetResult(name=name, rows=table.num_rows, files=files, partitions=partitions)


def write_manifest(
    root: Path,
    *,
    run_id: str,
    source: str,
    datasets: list[DatasetResult],
    quality: list[dict[str, Any]],
    started_at: datetime,
) -> Path:
    """A manifest makes a run auditable: what ran, over what, with what result."""
    manifest = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(UTC).isoformat(),
        "source": source,
        "compression": COMPRESSION,
        "pyarrow_version": pa.__version__,
        "datasets": [asdict(dataset) for dataset in datasets],
        "quality": quality,
    }
    path = root / "_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
