# EverTrack

A desktop habit tracker written in Python. Log daily activities, watch your streaks,
and see where your time actually goes.

<!-- Add a screenshot here: docs/screenshot.png, then ![EverTrack](docs/screenshot.png) -->

## Features

- **Habits** — create habits with a daily target (minutes) and an optional end date
- **Daily log** — log activities from a form, or type them in plain English ("read for 30 minutes")
- **Streak calendar** — an 8-week activity heatmap with current and longest streak
- **Achievements** — 15 badges with points, unlocked from your logged activity
- **Coach** — rolled-up statistics, target suggestions, and habit-building guidance
- **Analytics** — bar, line, pie, completion-rate and weekly-comparison charts (matplotlib)
- **Themes** — light and dark
- **Reminders** — per-habit reminder times, shown as in-app notifications
- **Export** — CSV export, PDF report, and a full backup of your data
- **HTTP API** — the same data over FastAPI, with OpenAPI docs

Everything runs offline. Data lives in JSON files next to the application, in
SQLite, or in PostgreSQL — the same code takes any of the three.

## A note on the "Coach"

The Coach tab and the plain-English log entry are **rule-based, not machine learning**:
a regular expression pulls a duration out of the text, a keyword table maps words to
habit names, and the coach's advice is selected from written templates. There is no
model and no API call. It is deterministic, offline, and honest about what it is —
and the parser is the first thing scheduled to get a real test suite (see Roadmap).

## Requirements

- Python 3.12 (3.10+ should work)
- Tkinter — standard library, but needs a system Tk:
  - macOS: bundled with python.org builds, or `brew install python-tk`
  - Debian/Ubuntu: `sudo apt install python3-tk`

## Installation

```bash
git clone https://github.com/nevil-codes/evertrack.git
cd evertrack
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Run it from the repository root — with the default JSON backend the app reads and
writes its data files relative to the current working directory, and creates them
on first run.

### Running on SQLite

```bash
python scripts/migrate_json_to_sqlite.py --dry-run   # report what would move
python scripts/migrate_json_to_sqlite.py             # writes evertrack.db
python main.py --storage sqlite
```

Both backends implement the same `core.repository.Repository` interface and are
covered by the same contract test suite, so the app behaves identically on either.

## HTTP API

The desktop app is one client of the domain layer, not the only one. The same
`core/` package and the same database are served over HTTP by FastAPI:

```bash
pip install -r requirements-api.txt
python scripts/seed_demo_data.py --database demo.db    # optional sample data
EVERTRACK_DB=demo.db uvicorn api.main:app --reload
```

Interactive docs at <http://localhost:8000/docs>, schema at `/openapi.json`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | liveness, version, database in use |
| `GET` `POST` | `/habits` | list (optionally `?active_only=true`), create |
| `GET` `DELETE` | `/habits/{name}` | fetch or delete one (deleting cascades to its logs and reminder) |
| `GET` `POST` | `/logs` | list (`?habit=`, `?from=`, `?to=`, `?limit=`), create |
| `POST` | `/logs/parse` | parse plain English; `"commit": true` also stores it |
| `DELETE` | `/logs/{id}` | delete one entry by id |
| `GET` | `/stats/summary` | activities, minutes, completion rate, active days |
| `GET` | `/stats/streak` | current, longest, and whether today is still empty |
| `GET` | `/stats/daily` | per-day rollup, oldest first |
| `GET` | `/stats/habits` | per-habit totals and completion rate |
| `GET` | `/stats/weekly` | minutes per week (`?weeks=`) |
| `GET` `POST` | `/achievements`, `/achievements/refresh` | badges held; re-evaluate the rules |

Validation is Pydantic at the edge and `core.models` underneath, so the API
refuses what the desktop app refuses: durations outside 0–1440 minutes, future
log dates, end dates before start dates, duplicate habit names (`409`), and logs
naming a habit that does not exist (`404`).

## Docker and PostgreSQL

```bash
docker compose up --build
curl localhost:8000/health
```

Three services: `db` (PostgreSQL 17), `migrate` (applies the SQL migrations and
exits), and `api` (waits for the migration to succeed, then serves on `:8000`).
The image is multi-stage — wheels are built in one stage, and the runtime stage
ships only the domain layer, the API, the migrations and a non-root user.

### Storage selection

| Environment | Backend |
|---|---|
| `EVERTRACK_DATABASE_URL=postgresql://user:pass@host:5432/evertrack` | PostgreSQL |
| `EVERTRACK_DB=evertrack.db` (or nothing) | SQLite |

`core.factory.repository_from_url` resolves either, so the API, the desktop app
and the scripts all take the same input.

### Migrations

Plain `.sql` files in `migrations/`, applied in filename order, each in its own
transaction and recorded in `schema_migrations` with a checksum. Editing a file
that has already been applied is refused — migrations are immutable, and the
fix is a new file.

```bash
python scripts/migrate_postgres.py --status
python scripts/migrate_postgres.py --dry-run
python scripts/migrate_postgres.py
```

The PostgreSQL schema (`migrations/001_initial_schema.sql`) is the SQLite one
with the dialect it deserves: identity columns, real `DATE`, `BOOLEAN` and
`JSONB` types, a functional unique index on `lower(name)` for case-insensitive
habit names, a regex `CHECK` on reminder times, and `COUNT(*) FILTER (WHERE …)`
in the rollup views.

### Moving data between backends

Both sides are only a `Repository`, so copying is generic:

```bash
python scripts/copy_store.py --from evertrack.db \
    --to postgresql://evertrack:evertrack@localhost:5432/evertrack --wipe
```

## Project layout

The domain logic lives in `core/`, which imports neither tkinter nor matplotlib:
it can be imported, tested and reused without a display. Everything else is the
desktop client on top of it.

```
api/                  FastAPI service over the same core
  main.py             App factory, OpenAPI metadata, domain error handling
  config.py           Settings from the environment (EVERTRACK_DB)
  deps.py             Request-scoped repository
  schemas.py          Pydantic request/response models
  routers/            habits, logs, stats, achievements

migrations/           Plain SQL migrations for PostgreSQL
Dockerfile            Multi-stage build for the API, non-root runtime
docker-compose.yml    db + migrate + api

core/                 GUI-free domain layer — the tested part
  models.py           Habit and LogEntry records, validation, JSON round-trip
  dates.py            ISO date parsing with useful errors
  streak.py           Current and longest streak
  stats.py            Totals, per-habit and per-day rollups, calendar window
  parser.py           Plain-English activity parser
  achievements.py     Badge catalogue and unlock rules
  repository.py       The storage contract every backend implements
  json_repository.py  Backend: the original four JSON files
  sqlite_repository.py Backend: SQLite
  postgres_repository.py Backend: PostgreSQL on psycopg 3
  factory.py          Resolves a URL or path to a backend
  schema.sql          SQLite tables, constraints, indexes and rollup views
  storage.py          Atomic JSON writes, corrupt files quarantined

scripts/
  migrate_json_to_sqlite.py   JSON -> SQLite migration, with a report
  migrate_postgres.py         Applies migrations/*.sql, tracks them, refuses edits
  copy_store.py               Copies any backend into any other
  seed_demo_data.py           Sample data for demos and CI

main.py               Application entry point and window shell
data_manager.py       Storage facade the UI talks to; delegates to a Repository
ai_coach.py           Adapter: parser and coaching text for the UI
achievements.py       Adapter: badge state for the UI
analytics.py          Chart builders (matplotlib)
notifications.py      In-app notification windows and reminder scheduling
themes.py             Light/dark palettes
ui_components.py      Shared styled widgets
tabs/                 One module per tab in the notebook
  habits_tab.py       Create and delete habits
  log_tab.py          Log activities, today's summary
  streak_tab.py       Streak heatmap
  achievements_tab.py Badge gallery
  ai_coach_tab.py     Coach: statistics and guidance
  analytics_tab.py    Chart display
  settings_tab.py     Theme, notifications, export, backup, reset

tests/                pytest suite over core/ and data_manager
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

228 tests, no display required. They cover the parser, streak maths, achievement
rules, record validation, atomic and corrupt-file storage behaviour, the schema's
own constraints, both migrations, every API endpoint including its error cases,
and a contract suite run against **all three** storage backends so they cannot
drift apart.

The PostgreSQL tests are skipped unless a scratch database is available:

```bash
EVERTRACK_TEST_DATABASE_URL=postgresql://evertrack:evertrack@localhost:5432/evertrack_test pytest
```

CI runs them with a PostgreSQL service container, and builds and exercises the
Docker stack in a separate job.

## Data

### JSON backend (default)

Created in the working directory on first run, and **not** version controlled:

| File | Contents |
|---|---|
| `habits_list.json` | habit definitions (name, start/end date, daily target, status) |
| `habits_data.json` | activity log entries (date, habit, duration, completed, notes) |
| `settings.json` | theme, notification toggle, per-habit reminder times |
| `achievements.json` | unlocked achievement ids and total points |

Writes are atomic, and a file that cannot be parsed is renamed to
`<name>.corrupt-<timestamp>` and reported — never silently replaced with an
empty one.

### SQLite backend

`core/schema.sql`: `habit`, `habit_log`, `reminder`, `achievement_unlock` and
`setting`, plus the `v_daily` and `v_habit_totals` rollup views. Integrity is
enforced by the database — unique habit names (case-insensitive), foreign keys
with `ON DELETE CASCADE`, and CHECK constraints on date format, target, duration
and reminder time.

The migration reports rather than coerces. It maps the `"No Limit"` sentinel to
`NULL`, normalizes int and float durations to `REAL`, fills in absent `notes`,
links each log to its habit by id, and lists anything it could not migrate:
unusable records, logs naming a habit that never existed, and reminders left
behind by deleted habits. `total_points` is not migrated — it is derived from
the unlocked badges instead of stored and incremented.

## Project status

This is a learning project, and it is mid-refactor. [`AUDIT.md`](AUDIT.md) is a full
technical audit of the codebase — architecture, data model, known bugs, and what
needs to change. It is deliberately unflattering and kept in the repository on purpose.

Fixed in the refactor so far: the streak no longer resets before the day's first log
or collapses because of one future-dated entry; the parser reads decimal hours,
understands "yesterday", and refuses input it cannot parse rather than guessing;
deleting one of two identical logs deletes one; a corrupt data file is quarantined
instead of being silently replaced with an empty one; and writes are atomic.

## Roadmap

1. **Hygiene** — .gitignore, dependency pinning, license, dead code removed *(done)*
2. **`core/` package + pytest + CI** — domain logic separated from Tkinter *(done)*
3. **SQLite** — normalized schema behind a repository interface, plus a JSON migration *(done)*
4. **HTTP API** — FastAPI over the same core *(done)*
5. **Docker** — containerized API with PostgreSQL via docker compose *(done)*
6. **Next** — a scheduled export to Parquet with data-quality checks, or
   observability (structured logs, Prometheus metrics). One, finished.

## License

MIT — see [LICENSE](LICENSE).

## Author

Nevil Amraniya — [github.com/nevil-codes](https://github.com/nevil-codes)
