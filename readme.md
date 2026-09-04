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
- **Export** — CSV export, PDF report, and a full backup of your data files

Everything runs offline. Data is stored in JSON files next to the application.

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

Run it from the repository root — the app reads and writes its JSON data files
relative to the current working directory. They are created on first run.

## Project layout

The domain logic lives in `core/`, which imports neither tkinter nor matplotlib:
it can be imported, tested and reused without a display. Everything else is the
desktop client on top of it.

```
core/                 GUI-free domain layer — the tested part
  models.py           Habit and LogEntry records, validation, JSON round-trip
  dates.py            ISO date parsing with useful errors
  streak.py           Current and longest streak
  stats.py            Totals, per-habit and per-day rollups, calendar window
  parser.py           Plain-English activity parser
  achievements.py     Badge catalogue and unlock rules
  storage.py          Atomic JSON writes, corrupt files quarantined

main.py               Application entry point and window shell
data_manager.py       Storage facade over core.storage, CRUD over habits and logs
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

111 tests, no display required. They cover the parser, streak maths, achievement
rules, record validation, atomic/corrupt-file storage behaviour and the storage
facade — the places where bugs silently corrupted data.

## Data files

Created in the working directory on first run, and **not** version controlled:

| File | Contents |
|---|---|
| `habits_list.json` | habit definitions (name, start/end date, daily target, status) |
| `habits_data.json` | activity log entries (date, habit, duration, completed, notes) |
| `settings.json` | theme, notification toggle, per-habit reminder times |
| `achievements.json` | unlocked achievement ids and total points |

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
3. **SQLite** — normalized schema behind a repository interface, plus a JSON migration
4. **HTTP API** — FastAPI over the same core, so the desktop app is one client of many
5. **Docker** — containerized API with Postgres via docker compose

## License

MIT — see [LICENSE](LICENSE).

## Author

Nevil Amraniya — [github.com/nevil-codes](https://github.com/nevil-codes)
