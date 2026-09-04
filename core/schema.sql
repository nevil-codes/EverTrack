-- EverTrack schema. SQLite dialect; kept close to portable SQL so the same
-- shape moves to Postgres later with minimal change.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS habit (
    id               INTEGER PRIMARY KEY,
    name             TEXT    NOT NULL COLLATE NOCASE,
    start_date       TEXT    NOT NULL CHECK (start_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    end_date         TEXT             CHECK (end_date IS NULL OR
                                             end_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    daily_target_min INTEGER NOT NULL CHECK (daily_target_min > 0),
    status           TEXT    NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'paused', 'archived')),
    created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE UNIQUE INDEX IF NOT EXISTS habit_name_uq ON habit (name);

CREATE TABLE IF NOT EXISTS habit_log (
    id           INTEGER PRIMARY KEY,
    habit_id     INTEGER NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    log_date     TEXT    NOT NULL CHECK (log_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    duration_min REAL    NOT NULL CHECK (duration_min > 0 AND duration_min <= 1440),
    completed    INTEGER NOT NULL DEFAULT 1 CHECK (completed IN (0, 1)),
    notes        TEXT    NOT NULL DEFAULT '',
    logged_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS habit_log_date_idx       ON habit_log (log_date);
CREATE INDEX IF NOT EXISTS habit_log_habit_date_idx ON habit_log (habit_id, log_date);

CREATE TABLE IF NOT EXISTS reminder (
    habit_id  INTEGER PRIMARY KEY REFERENCES habit(id) ON DELETE CASCADE,
    time_hhmm TEXT NOT NULL CHECK (time_hhmm GLOB '[0-2][0-9]:[0-5][0-9]'),
    enabled   INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1))
);

CREATE TABLE IF NOT EXISTS achievement_unlock (
    code        TEXT PRIMARY KEY,
    unlocked_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS setting (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL          -- JSON-encoded scalar
);

-- Rollups the charts and the streak calculation both want. Defined once here
-- instead of being recomputed in Python for every redraw.
CREATE VIEW IF NOT EXISTS v_daily AS
SELECT log_date,
       COUNT(*)          AS activities,
       SUM(duration_min) AS total_min,
       SUM(completed)    AS completed_count
FROM habit_log
GROUP BY log_date;

CREATE VIEW IF NOT EXISTS v_habit_totals AS
SELECT h.name,
       COUNT(l.id)                     AS activities,
       COALESCE(SUM(l.duration_min), 0) AS total_min,
       COALESCE(AVG(l.duration_min), 0) AS avg_min,
       COALESCE(SUM(l.completed), 0)    AS completed_count
FROM habit h
LEFT JOIN habit_log l ON l.habit_id = h.id
GROUP BY h.id, h.name;
