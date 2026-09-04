-- 001 initial schema (PostgreSQL)
--
-- The SQLite equivalent lives in core/schema.sql. Differences are dialect only:
-- identity columns, DATE/BOOLEAN/JSONB types, a functional unique index for
-- case-insensitive habit names, and a regex CHECK for reminder times.

CREATE TABLE habit (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT    NOT NULL CHECK (length(btrim(name)) > 0),
    start_date       DATE    NOT NULL,
    end_date         DATE,
    daily_target_min INTEGER NOT NULL CHECK (daily_target_min > 0),
    status           TEXT    NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'paused', 'archived')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT habit_end_after_start CHECK (end_date IS NULL OR end_date >= start_date)
);

-- Names are unique regardless of case: "Reading" and "reading" are one habit.
CREATE UNIQUE INDEX habit_name_uq ON habit (lower(name));

CREATE TABLE habit_log (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    habit_id     BIGINT  NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    log_date     DATE    NOT NULL,
    duration_min DOUBLE PRECISION NOT NULL
                 CHECK (duration_min > 0 AND duration_min <= 1440),
    completed    BOOLEAN NOT NULL DEFAULT TRUE,
    notes        TEXT    NOT NULL DEFAULT '',
    logged_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX habit_log_date_idx       ON habit_log (log_date);
CREATE INDEX habit_log_habit_date_idx ON habit_log (habit_id, log_date);

CREATE TABLE reminder (
    habit_id  BIGINT PRIMARY KEY REFERENCES habit(id) ON DELETE CASCADE,
    time_hhmm TEXT    NOT NULL CHECK (time_hhmm ~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'),
    enabled   BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE achievement_unlock (
    code        TEXT PRIMARY KEY,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE setting (
    key   TEXT  PRIMARY KEY,
    value JSONB NOT NULL
);

CREATE VIEW v_daily AS
SELECT log_date,
       COUNT(*)                                AS activities,
       SUM(duration_min)                       AS total_min,
       COUNT(*) FILTER (WHERE completed)       AS completed_count
FROM habit_log
GROUP BY log_date;

CREATE VIEW v_habit_totals AS
SELECT h.name,
       COUNT(l.id)                             AS activities,
       COALESCE(SUM(l.duration_min), 0)        AS total_min,
       COALESCE(AVG(l.duration_min), 0)        AS avg_min,
       COUNT(l.id) FILTER (WHERE l.completed)  AS completed_count
FROM habit h
LEFT JOIN habit_log l ON l.habit_id = h.id
GROUP BY h.id, h.name;
