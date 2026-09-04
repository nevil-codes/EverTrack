#!/usr/bin/env python3
"""Export EverTrack to a partitioned Parquet dataset, with quality gates.

    python -m pipeline.run --source evertrack.db --out warehouse
    python -m pipeline.run --source postgresql://evertrack@localhost/evertrack --out warehouse
    python -m pipeline.run --dry-run          # validate, write nothing
    python -m pipeline.run --fail-on warn     # treat warnings as failures

Exit codes: 0 published, 1 blocked by data quality, 2 bad arguments.
"""
from __future__ import annotations

import argparse
import sys
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.factory import describe  # noqa: E402
from pipeline import load, quality, transform  # noqa: E402
from pipeline.extract import extract  # noqa: E402

EXIT_OK = 0
EXIT_QUALITY = 1


class Outcome:
    def __init__(self, reports, datasets, manifest, published):
        self.reports = reports
        self.datasets = datasets
        self.manifest = manifest
        self.published = published


def run(source_url: str, out: Path, *, dry_run: bool = False,
        fail_on_warn: bool = False, as_of: date | None = None) -> Outcome:
    started_at = datetime.now(UTC)
    run_id = uuid.uuid4().hex[:12]
    as_of = as_of or date.today()

    extracted = extract(source_url)
    dim_rows = transform.build_dim_habit(extracted.habits)
    fact_rows = transform.build_fact_habit_log(extracted.logs, extracted.habits)

    context = quality.Context(dim_habit=dim_rows, as_of=as_of)
    reports = [
        quality.validate("dim_habit", dim_rows, quality.DIM_EXPECTATIONS, context),
        quality.validate("fact_habit_log", fact_rows, quality.FACT_EXPECTATIONS, context),
    ]

    blocked = any(not report.ok for report in reports)
    if fail_on_warn:
        blocked = blocked or any(report.failed for report in reports)

    if blocked or dry_run:
        return Outcome(reports, [], None, published=False)

    out.mkdir(parents=True, exist_ok=True)
    datasets = [
        load.write_dataset(
            transform.to_table(dim_rows, transform.DIM_HABIT_SCHEMA), out, "dim_habit"
        ),
        load.write_dataset(
            transform.to_table(fact_rows, transform.FACT_SCHEMA), out, "fact_habit_log",
            partition_columns=transform.PARTITION_COLUMNS,
        ),
    ]
    manifest = load.write_manifest(
        out,
        run_id=run_id,
        source=describe(source_url),
        datasets=datasets,
        quality=[report.to_dict() for report in reports],
        started_at=started_at,
    )
    return Outcome(reports, datasets, manifest, published=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default="evertrack.db",
                        help="path or URL of the operational store (default: evertrack.db)")
    parser.add_argument("--out", type=Path, default=Path("warehouse"),
                        help="directory to write the dataset into (default: warehouse)")
    parser.add_argument("--dry-run", action="store_true", help="validate only, write nothing")
    parser.add_argument("--fail-on", choices=("error", "warn"), default="error",
                        help="stop the run on errors only (default) or on warnings too")
    args = parser.parse_args(argv)

    outcome = run(args.source, args.out, dry_run=args.dry_run,
                  fail_on_warn=args.fail_on == "warn")

    for report in outcome.reports:
        print(report.render())

    if not outcome.published:
        if args.dry_run:
            print("\ndry run: nothing written")
            return EXIT_OK
        print("\nnot published: data quality gate failed")
        return EXIT_QUALITY

    print()
    for dataset in outcome.datasets:
        partitions = f", {len(dataset.partitions)} partitions" if dataset.partitions else ""
        print(f"wrote {dataset.name}: {dataset.rows} rows, {len(dataset.files)} file(s){partitions}")
    print(f"manifest: {outcome.manifest}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
