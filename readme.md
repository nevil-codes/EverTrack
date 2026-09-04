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

```
main.py               Application entry point and window shell
data_manager.py       Loads/saves the four JSON files, CRUD over habits and logs
ai_coach.py           Plain-English parser and habit suggestions (rule-based)
achievements.py       Achievement definitions, unlock checks, streak calculation
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
```

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

Known issues worth stating up front: the streak resets to zero before the day's first
log, the plain-English parser misreads decimal hours, and there are no tests yet.
All three are tracked in the audit and fixed in the roadmap below.

## Roadmap

1. **Hygiene** — .gitignore, dependency pinning, license, dead code removed *(done)*
2. **`core/` package + pytest + CI** — domain logic separated from Tkinter, tests first
3. **SQLite** — normalized schema behind a repository interface, plus a JSON migration
4. **HTTP API** — FastAPI over the same core, so the desktop app is one client of many
5. **Docker** — containerized API with Postgres via docker compose

## License

MIT — see [LICENSE](LICENSE).

## Author

Nevil Amraniya — [github.com/nevil-codes](https://github.com/nevil-codes)
