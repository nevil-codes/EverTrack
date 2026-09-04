"""Batch export: EverTrack's operational store to a partitioned Parquet dataset.

extract -> transform -> validate -> load, with the validation step able to stop
the run. Reads through core.repository, so it works against JSON, SQLite or
PostgreSQL without knowing which.
"""
