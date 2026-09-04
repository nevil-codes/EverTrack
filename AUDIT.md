# EverTrack — Repository Audit

**Audited commit:** `40401f5` ("final commit", 2025-12-22) on `main`
**Scope:** full read-only pass over all tracked Python, JSON, Markdown and git metadata.
**Audience note:** recommendations are weighted toward MLOps / data-engineering signal (SQL, Docker, FastAPI), not toward more features.

---

## 0. Snapshot

| Metric | Value |
|---|---|
| Tracked files | 4,627 |
| Of those, virtualenv files | 4,589 (99.2%) |
| Hand-written Python | ~2,959 lines across 16 files |
| Dead Python (never imported/run) | 1,491 lines (`EverTrack.py`) — 50% of the code |
| Packed repo size | 41.3 MiB |
| Tests | 0 |
| `.gitignore` / `requirements.txt` / `LICENSE` / CI | none of them |
| Commits | 8, all from one day-ish burst, messages like "final commit", "ui updation" |

---

## 1. ARCHITECTURE

### 1.1 Real module dependency graph

```
main.py                        <-- LIVE ENTRY POINT (python main.py)
├── data_manager.DataManager        (json, os) — no GUI imports
├── themes.ThemeManager             (pure python, but holds a Tk `root` and calls root.configure)
├── ui_components.UIComponents      (tkinter)
├── ai_coach.AICoach                (re) — no GUI imports
├── analytics.Analytics             (matplotlib + backend_tkagg)
├── achievements.AchievementSystem  (datetime, collections) — no GUI imports
├── notifications.NotificationManager (tkinter)
└── tabs/                       (imported lazily inside main.create_*_tab methods)
    ├── habits_tab.HabitsTab        -> app.ui, app.ai_coach, app.data_manager, app.log_tab
    ├── log_tab.LogTab              -> app.ui, app.ai_coach, app.data_manager, app.habits_tab
    ├── streak_tab.StreakTab        -> app.data_manager   (+ its own streak math)
    ├── achievements_tab.Achievements-> app.achievement_system
    ├── ai_coach_tab.AICoachTab     -> app.data_manager   (does NOT use ai_coach.py!)
    ├── analytics_tab.AnalyticsTab  -> app.analytics, matplotlib
    └── settings_tab.SettingsTab    -> app.data_manager, app.achievement_system, app.toggle_theme

EverTrack.py                   <-- DEAD. Imports nothing local, nothing imports it.
tabs/__init__.py               <-- declares __all__ of module names but imports nothing (no-op).
```

Key structural facts:

- **Every tab receives the whole `app` object** (`tabs/habits_tab.py:9`, and identically in all seven tabs). There are no interfaces; a tab can reach `app.data_manager.habits_data` and mutate it. This is a god-object pattern — the reason nothing here is unit-testable without a display.
- **Tabs reach sideways into each other**: `habits_tab.create_habit` calls `self.app.log_tab.refresh()` (`tabs/habits_tab.py:217`), `log_tab.parse_and_log` calls `self.app.habits_tab.refresh()` (`tabs/log_tab.py:204`). Circular runtime coupling, ordered only by tab-creation order in `main.create_main_ui`.
- **`ai_coach_tab.py` does not use `ai_coach.py`.** All 450 lines of "AI Coach" are `if/elif` on keyword substrings plus static text blocks written inline in the tab. The one genuinely reusable function in `ai_coach.py` — `analyze_progress()` — is never called by anything; `ai_coach_tab.analyze_progress()` re-implements it (`tabs/ai_coach_tab.py:140-206` vs `ai_coach.py:65-92`).
- **Streak math exists twice**, character-for-character: `achievements.calculate_current_streak` (`achievements.py:196`) and `StreakTab.calculate_current_streak` (`tabs/streak_tab.py:195`). Both carry the same bug (§3.1).

### 1.2 Business logic entangled with tkinter

These functions contain real domain logic but cannot run without a display. Ranked by how much they *should* move to a GUI-free `core/`:

| Function | File | What's actually domain logic |
|---|---|---|
| `StreakTab.calculate_current_streak` | `tabs/streak_tab.py:195` | streak from a set of dates |
| `StreakTab.calculate_longest_streak` | `tabs/streak_tab.py:217` | longest run of consecutive dates |
| `StreakTab.draw_calendar` (lines 47-58, 82-103) | `tabs/streak_tab.py:40` | 8-week bucketing + intensity binning, welded to `tk.Label` creation |
| `AICoachTab.analyze_progress` | `tabs/ai_coach_tab.py:140` | totals, completion rate, active days, top habit — then string-formats and pushes to a widget |
| `AICoachTab.optimize_targets` | `tabs/ai_coach_tab.py:254` | per-habit avg/min/max and target recommendation (`int(avg*1.2)`) |
| `AICoachTab.custom_query` | `tabs/ai_coach_tab.py:361` | intent routing on keywords |
| `LogTab.add_log` | `tabs/log_tab.py:224` | duration validation + record construction |
| `LogTab.parse_and_log` | `tabs/log_tab.py:165` | habit auto-creation policy |
| `LogTab.update_summary` | `tabs/log_tab.py:296` | daily aggregation |
| `HabitsTab.create_habit` | `tabs/habits_tab.py:178` | duplicate check, target parsing, habit record construction, reminder registration |
| `SettingsTab.update_statistics` | `tabs/settings_tab.py:345` | the whole stats block |
| `SettingsTab.generate_pdf` | `tabs/settings_tab.py:207` | report content assembly |
| `Analytics.create_*_chart` (5 fns) | `analytics.py:14-129` | aggregation (`defaultdict` rollups) is domain; only the `ax.bar/plot/pie` calls are presentation |
| `ThemeManager.toggle_theme` | `themes.py:44` | persists a setting; only `apply_theme` needs Tk |

Already GUI-free and directly liftable: all of `data_manager.py`, all of `ai_coach.py`, all of `achievements.py`.

A `core/` package would be roughly: `core/models.py` (Habit, LogEntry), `core/streak.py`, `core/stats.py`, `core/parser.py`, `core/achievements.py`, `core/storage.py`. That is ~600 lines of the current code, and it is the part worth showing anyone.

### 1.3 Dead and duplicated code

**`EverTrack.py` vs `main.py` — `main.py` is the live entry point.** Evidence:
- `main.py:206-222` defines `main()` and the `__main__` guard, and imports the seven modules that all `tabs/*` depend on.
- `EverTrack.py` imports nothing from this repo and nothing imports it; deleting it changes no behaviour.
- `EverTrack.py`'s class is `EverTrack` (1200x750, no achievements/streaks/notifications/themes/settings). `main.py`'s is `EverTrackPro` (1300x800, seven tabs). `EverTrack.py` is the pre-refactor monolith, kept and committed alongside its own replacement.
- `readme.md:44` tells the user to run `python evertrack.py` — a file that does not exist under that name (the file is `EverTrack.py`, and on Linux/macOS-case-sensitive volumes that command fails outright). So the README documents running the dead file, under the wrong name.

Duplication inventory:
- `parse_natural_language`: `ai_coach.py:30` and `EverTrack.py:766` (the dead one has an extra `-ing`-word fallback).
- Chart builders: `analytics.py:14-100` and `EverTrack.py:1414-1485`.
- CRUD + JSON I/O: `data_manager.py:27-75` and `EverTrack.py:29-57`.
- Streak: `achievements.py:196` and `tabs/streak_tab.py:195`.
- Progress analysis: `ai_coach.py:65` (unreachable) and `tabs/ai_coach_tab.py:140`.
- 7 stale `.pyc` files in `__pycache__/` and 7 in `tabs/__pycache__/`, all committed.
- Unused imports: `main.py:9` (`os`), `ai_coach.py:3` (`defaultdict`), `notifications.py:4` (`timedelta`), `analytics.py:3` (`FigureCanvasTkAgg`), `tabs/analytics_tab.py:4` (`plt` used, `FigureCanvasTkAgg` used — fine).

---

## 2. DATA LAYER

Four JSON files, all read/written from the process working directory (`data_manager.py:10-13`) — meaning the app only finds its data if launched from the repo root.

### 2.1 `habits_list.json` — array of habit objects

| Field | Type | Notes |
|---|---|---|
| `name` | string | **primary key by convention**; used as the join key everywhere |
| `start_date` | string `YYYY-MM-DD` | always "now" at creation; never editable |
| `end_date` | string | `"No Limit"` sentinel **or** a date string; unvalidated in the live path |
| `daily_target` | int (minutes) | |
| `status` | string | only ever `"Active"`; nothing ever writes another value |

```json
{"name": "Meditation", "start_date": "2025-12-21", "end_date": "No Limit", "daily_target": 30, "status": "Active"}
```

### 2.2 `habits_data.json` — array of log entries

| Field | Type | Notes |
|---|---|---|
| `date` | string `YYYY-MM-DD` | always today; no way to backfill |
| `habit` | string | free text, must match `habits_list.name`, **not enforced** |
| `duration` | int **or** float | int via the NL parser (`ai_coach.py:38`), float via the form (`tabs/log_tab.py:244`) — both shapes are in the committed file |
| `completed` | bool | |
| `notes` | string | **optional — absent in some committed records** |

Committed file, verbatim, shows all three shape variants:
```json
[
  {"date": "2025-12-21", "habit": "maths",      "duration": 23.0, "completed": true},
  {"date": "2025-12-21", "habit": "Meditation", "duration": 30,   "completed": true},
  {"date": "2025-12-21", "habit": "Meditation", "duration": 25.0, "completed": true, "notes": ""}
]
```
Note there is **no id and no timestamp** — two identical (date, habit, duration) rows are indistinguishable, which is the root of the delete bug in §3.4.

### 2.3 `settings.json` — object

| Field | Type | Notes |
|---|---|---|
| `theme` | `"light"` \| `"dark"` | |
| `notifications` | bool | |
| `reminder_times` | object `{habit_name: "HH:MM"}` | keyed by habit **name**; never cleaned up |

The committed file is itself the evidence of the orphan bug — it holds a reminder for a habit that does not exist:
```json
{"theme": "dark", "notifications": true, "reminder_times": {"new habit": "17:46"}}
```

### 2.4 `achievements.json` — object

| Field | Type | Notes |
|---|---|---|
| `unlocked` | array of achievement-id strings | ids defined only in Python (`achievements.py:12-103`) |
| `total_points` | int | **denormalized** — derivable from `unlocked`, and drifts if hand-edited |

```json
{"unlocked": ["first_log", "perfect_day"], "total_points": 40}
```

### 2.5 Proposed normalized SQLite schema

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE habit (
    id             INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL COLLATE NOCASE,
    start_date     TEXT    NOT NULL CHECK (start_date  GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    end_date       TEXT             CHECK (end_date IS NULL OR
                                           end_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    daily_target_min INTEGER NOT NULL CHECK (daily_target_min > 0),
    status         TEXT    NOT NULL DEFAULT 'active'
                           CHECK (status IN ('active', 'paused', 'archived')),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (end_date IS NULL OR end_date >= start_date)
);
CREATE UNIQUE INDEX habit_name_uq ON habit (name);

CREATE TABLE habit_log (
    id           INTEGER PRIMARY KEY,
    habit_id     INTEGER NOT NULL REFERENCES habit(id) ON DELETE CASCADE,
    log_date     TEXT    NOT NULL CHECK (log_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    duration_min REAL    NOT NULL CHECK (duration_min > 0 AND duration_min <= 1440),
    completed    INTEGER NOT NULL DEFAULT 1 CHECK (completed IN (0, 1)),
    notes        TEXT    NOT NULL DEFAULT '',
    source       TEXT    NOT NULL DEFAULT 'manual'
                         CHECK (source IN ('manual', 'nlp', 'import')),
    logged_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX habit_log_date_idx       ON habit_log (log_date);
CREATE INDEX habit_log_habit_date_idx ON habit_log (habit_id, log_date);

CREATE TABLE reminder (
    habit_id  INTEGER PRIMARY KEY REFERENCES habit(id) ON DELETE CASCADE,
    time_hhmm TEXT NOT NULL CHECK (time_hhmm GLOB '[0-2][0-9]:[0-5][0-9]'),
    enabled   INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1))
);

-- catalog: the 15 definitions currently hardcoded in achievements.py
CREATE TABLE achievement (
    code        TEXT PRIMARY KEY,
    name        TEXT    NOT NULL,
    description TEXT    NOT NULL,
    icon        TEXT    NOT NULL,
    points      INTEGER NOT NULL CHECK (points >= 0)
);

CREATE TABLE achievement_unlock (
    achievement_code TEXT PRIMARY KEY REFERENCES achievement(code),
    unlocked_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE setting (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL          -- JSON-encoded scalar
);

-- total_points stops being stored and becomes derived:
CREATE VIEW v_total_points AS
SELECT COALESCE(SUM(a.points), 0) AS total_points
FROM achievement_unlock u JOIN achievement a ON a.code = u.achievement_code;

-- daily rollup the charts and the streak calc both want:
CREATE VIEW v_daily AS
SELECT log_date,
       COUNT(*)             AS activities,
       SUM(duration_min)    AS total_min,
       SUM(completed)       AS completed_count
FROM habit_log
GROUP BY log_date;
```

**Things in the JSON that do not map cleanly — decide explicitly during migration:**

1. `end_date: "No Limit"` is a sentinel string in a date column → becomes `NULL`. Migration must translate it, and any other non-date junk (the live path never validates this field) has to be quarantined, not silently coerced.
2. `duration` is `int` in some rows and `float` in others → one `REAL` column. Cheap, but note every equality comparison in the current code (`data_manager.py:71`) breaks on floats already.
3. `notes` is absent in some records → `NOT NULL DEFAULT ''`.
4. **No log id and no time-of-day.** Two identical rows on one day are the same row as far as the current code can tell. SQLite gives you the surrogate key for free — but there is no way to reconstruct the original ordering when migrating, so accept arbitrary order for legacy rows.
5. **Habit identity is the name string.** Every log references a habit by name, case-sensitively (`data_manager.py:59-60`), while duplicate-detection is case-*in*sensitive (`tabs/habits_tab.py:187`). So `"Reading"` and `"reading"` cannot both be created, but a log written as `"reading"` would orphan. Migration must fold on `COLLATE NOCASE` and map names → ids; expect orphan logs (the sample data already has habit `"maths"` while `settings.reminder_times` references `"new habit"`, which has no habit row at all).
6. `settings.reminder_times` keyed by name → `reminder.habit_id`, and the orphan entries simply cannot be migrated. Log them, drop them.
7. `achievements.total_points` is derived state stored as fact → replaced by `v_total_points`. Any drift between the stored value and the sum is data you must choose to discard.
8. Achievement definitions (name/icon/points) live in Python, not in data → seed `achievement` from `achievements.py:12-103` in the migration, then treat the table as the source of truth.
9. The `status` field only ever holds `"Active"`, but `get_active_habits` filters on exact `'Active'` (`data_manager.py:77`) — pick lowercase in SQL and normalize on import.

### 2.6 Every place that touches the JSON files directly

Anything here has to change when storage moves behind a repository interface.

| Location | What it does |
|---|---|
| `data_manager.py:10-13` | hardcodes the four filenames (CWD-relative) |
| `data_manager.py:15-25` | loads all four at construction, into memory, forever |
| `data_manager.py:27-35` | `load_json` — bare `except:` |
| `data_manager.py:37-45` | `save_json` — full-file rewrite, non-atomic |
| `data_manager.py:47-51` | `save_all` |
| `data_manager.py:53-56` | `add_habit` → writes `habits_list.json` |
| `data_manager.py:57-62` | `delete_habit` → rewrites two files |
| `data_manager.py:64-67` | `add_log` → writes `habits_data.json` |
| `data_manager.py:69-75` | `delete_log` → writes `habits_data.json` |
| `data_manager.py:88-107` | `export_to_csv` — reads in-memory list, writes CSV |
| `themes.py:47-48` | mutates `settings` dict and calls `save_json` **directly**, bypassing DataManager's own API |
| `achievements.py:115-121` | mutates `achievements` dict and calls `save_json` directly |
| `tabs/habits_tab.py:208-212` | writes `settings.reminder_times` directly from the UI |
| `tabs/settings_tab.py:184-188` | writes `settings.notifications` directly from the UI |
| `tabs/settings_tab.py:300-309` | copies the four files on disk by path (backup) |
| `tabs/settings_tab.py:336-339` | resets in-memory state, then `save_all` |
| `EverTrack.py:29-57` | dead file's own four load/save methods |

That is **five modules** writing storage, three of them from inside UI callbacks. Four of the seventeen call sites bypass `DataManager`'s own methods entirely.

---

## 3. CORRECTNESS

Verified by reading, and where marked ✓ by actually executing the function.

### 3.1 Streak calculation

- **✓ A streak that ended yesterday reports 0, not "broken yesterday".** `achievements.py:204` / `tabs/streak_tab.py:203`: if the most recent log date isn't today, return 0. Ten consecutive days ending yesterday → `0`. Verified by running it. So the "Week Warrior" achievement can only ever fire on a day you have already logged, and the number the user sees before their first log of the day is a lie.
- **✓ A single future-dated log zeroes the streak permanently.** Same lines: `dates[0]` is the max date; if it's in the future it never equals today. Verified: 5 real consecutive days + one log dated +3 days → streak `0`. Nothing prevents a future date entering the file (hand edit, clock skew, or a timezone change on the machine).
- **The streak counts calendar days on which *anything* was logged**, not per-habit and not against `daily_target`. "Maintain a 7-day streak" (`achievements.py:22`) is really "opened the app on 7 consecutive days". Logging 1 minute of one habit sustains it.
- **`completed: false` still counts toward the streak** — `calculate_current_streak` never looks at the field.
- **Duplicated implementation** (`achievements.py:196` and `tabs/streak_tab.py:195`), so any fix must be applied twice or the two displays will disagree.
- `calculate_longest_streak` (`tabs/streak_tab.py:217`) returns `1` for a dataset with zero consecutive days — arguably right, but it also returns `1` when `dates` has exactly one entry and `0` only when data is empty; inconsistent with `calculate_current_streak`'s 0.

### 3.2 Date handling

- **The streak calendar's weekday labels are wrong.** `tabs/streak_tab.py:49` sets `start_date = today - 56 days`; 56 is exactly 8 weeks, so `start_date.weekday() == today.weekday()`. Row 0 is then labelled `Mon` (`tabs/streak_tab.py:70-79`) regardless. **The grid only aligns with reality if today happens to be a Monday.** Every other day of the week, every cell in the heatmap is under the wrong weekday label.
- **Today is not on the calendar.** The last cell drawn is `start_date + 55 days` = *yesterday* (`tabs/streak_tab.py:82-84`). The user's most recent activity — the one that drives the streak number displayed right below the grid — is never shown.
- **The cell date label logic is nonsense**: `str(date.day) if date.day <= 7 or date.day % 7 == 0 else ""` (`tabs/streak_tab.py:107`) shows the 1st–7th, 14th, 21st, 28th and blanks everything else. It reads as an attempt at month markers and isn't one.
- **`create_weekly_comparison` produces five buckets for "Last 4 Weeks"** (`analytics.py:114-116`): `days_ago == 28` yields `Week 0`, and any future-dated log yields `Week 5` or higher and still passes the `days_ago <= 28` filter (negative ≤ 28). Bars are also drawn in `defaultdict` insertion order (`analytics.py:122-125`), i.e. whatever order the logs happen to sit in the file — the x-axis is unordered.
- **Every log is stamped `datetime.now()`** (`tabs/log_tab.py:210, 252`). There is no way to record yesterday's run. Combined with the parser accepting "yesterday" (§3.3), the app confidently writes the wrong date.
- **All dates are naive local time with no timezone or DST handling.** Crossing midnight while the app is open leaves stale "today" strings in already-rendered widgets.
- **`datetime.strptime(log['date'], "%Y-%m-%d")` is called on unvalidated data in four places** — `analytics.py:111`, `achievements.py:189`, `tabs/streak_tab.py:54, 208/230`. One malformed date in `habits_data.json` raises `ValueError` and takes down the calendar tab, the weekly chart, and achievement checking (which runs in `EverTrackPro.__init__`, `main.py:47` — so a bad date means **the app will not start**).

### 3.3 Natural-language parser (`ai_coach.py:30-63`)

All verified by execution:

| Input | Result | Problem |
|---|---|---|
| `"I spread butter for 10 minutes"` | `{'habit': 'Reading', 'duration': 10}` | naive substring match — `"read"` is inside `"spread"` |
| `"I studied for 45 mins"` | `None` | `"study"` isn't a substring of `"studied"`; no stemming, and `"studying"` is missing from the map (the *dead* `EverTrack.py:790` has it) |
| `"yoga 1.5 hours"` | `duration: 300` | `\d+` grabs the `5` from `1.5` → 5 hours. **Silently 3.3× wrong.** |
| `"I meditated yesterday for 30 minutes"` | `{'Meditation', 30}` | "yesterday" ignored, entry written with today's date |
| `"I coded for 90 minutes and read for 20 minutes"` | `{'Reading', 90}` | wrong habit (dict order puts `read` before `code`) *and* the wrong pairing of habit to duration |
| `"yoga 90 minutes ago"` | `{'Yoga', 90}` | "ago" is not a duration |
| `"exercise for 0 minutes"` | `None` | `if not duration` treats 0 as parse failure (`ai_coach.py:45`) |
| `"yoga for 999999 minutes"` | accepted | no upper bound; 694 days in one entry |

Structurally: match order is dict-insertion order, so the earliest key wins rather than the longest or leftmost match; there is no confidence score, no confirmation step, and no unit test. **And the parsed result is written straight to disk** (`tabs/log_tab.py:209-217`) with no review dialog — every one of the wrong answers above becomes a permanent record.

### 3.4 Writes without validation / silent corruption

Ordered by severity.

1. **Bare `except:` on load + full-file overwrite on save = total history loss.** `data_manager.py:33` swallows *any* exception (including `json.JSONDecodeError` from a truncated file) and returns `[]`. The app then runs normally with an empty history, and the very next log write (`data_manager.py:66`) overwrites the damaged-but-recoverable file with a one-element list. **A single interrupted save destroys all data on the next launch, silently, with no error shown to the user.**
2. **Non-atomic writes.** `data_manager.py:39-41` opens the real file `'w'` (truncating it) and then serializes. A crash, a full disk, or a `KeyboardInterrupt` mid-`json.dump` leaves a truncated file — which feeds directly into bug #1. Fix is write-temp-then-`os.replace`.
3. **`delete_log` deletes *every* matching row, not one.** `data_manager.py:71-74` filters out all entries matching `(date, habit, duration)`. Logging "Meditation 30 min" twice today and deleting one deletes both. The dead `EverTrack.py:1318-1322` did this correctly (`break` after the first). This is a regression introduced by the refactor.
4. **`delete_log` frequently deletes nothing while reporting success.** The table renders duration as `f"{log['duration']:.0f}"` (`tabs/log_tab.py:336`) and the delete path parses that rounded string back with `float(values[2])` (`tabs/log_tab.py:284`). A 23.4-minute log displays as `23`, matches nothing, and the user still sees "Log deleted!" (`tabs/log_tab.py:287`).
5. **`KeyError: 'total_points'` at startup — app won't launch.** ✓ Verified: `achievements.py:115` does `self.data_manager.achievements["total_points"] += ...` with no `.get`. An `achievements.json` containing `{"unlocked": []}` (hand-edited, partially written, or from an older version) crashes inside `EverTrackPro.__init__` → `check_achievements` (`main.py:47`) before any window is drawn. Same class of bug: `habit['daily_target']` (`tabs/habits_tab.py:254`), `habit['end_date']`, `log['duration']` — any missing key in a hand-edited file is an unhandled crash.
6. **Achievement points can be double-counted and never revoked.** `unlocked` and `total_points` are independent fields; delete `unlocked` while keeping `total_points` and the next check re-awards everything. Clearing all data (`tabs/settings_tab.py:338`) *does* reset them together — but deleting individual logs does not, so points survive the data that earned them.
7. **`end_date` is never validated in the live path.** `tabs/habits_tab.py:200` takes the entry box verbatim when "No End Date" is unchecked — `"asdf"` is stored as a date. The dead `EverTrack.py:1194-1197` validated it with `strptime`. Second refactor regression.
8. **Reminder time is never validated.** `tabs/habits_tab.py:206-208` stores any string. `notifications.py:77` compares it to `"%H:%M"` — a bad value simply never fires, with no feedback.
9. **`delete_habit` orphans the reminder.** `data_manager.py:57-62` removes the habit and its logs but never touches `settings["reminder_times"]`. The committed `settings.json` already contains an orphan (`"new habit"`), so this has happened in real use.
10. **`clear_all_data` doesn't do what its dialog says.** The confirmation lists "All settings" (`tabs/settings_tab.py:322`) but the handler resets only logs, habits and achievements (`tabs/settings_tab.py:336-338`) — `settings`, including every orphaned `reminder_times` entry, survives.
11. **No referential integrity.** `add_log` never checks the habit exists (`data_manager.py:64`). `parse_and_log` can create a habit named from the parser's fixed vocabulary while the log is written with that same name — but a habit renamed by hand in the JSON orphans every log silently.
12. **`get_active_habits` filters `status == 'Active'` exactly** (`data_manager.py:77`), while nothing else in the codebase ever sets `status` to anything else. A `"active"` typo in the file makes a habit vanish from the log dropdown with no error.

### 3.5 Other real bugs

- **Literal `{'='*60}` printed to the user.** `tabs/ai_coach_tab.py:211` and `:270` are plain (non-f) triple-quoted strings, so the "AI report" header renders the source text `{'='*60}` verbatim on screen. The neighbouring reports at `:163` and `:164` *are* f-strings, so the inconsistency is visible in the same tab.
- **Creating a habit doesn't add it to the Daily Log dropdown.** `tabs/habits_tab.py:216-217` calls `refresh()` on itself and `log_tab.refresh()`, but the combobox is filled by `LogTab.update_habit_combo` (`tabs/log_tab.py:289`), which nobody calls here. New habit → restart required. The NL path (`tabs/log_tab.py:203`) gets it right, which makes the omission obvious.
- **Deleting a habit leaves it in the dropdown**, same cause (`tabs/habits_tab.py:239-241`).
- **The reminder loop dies permanently if notifications are ever off.** `main.py:183-185` only re-arms `root.after` when `notifications` is true. Disable → the chain stops; re-enable → nothing reschedules it until restart.
- **Reminders can miss their minute.** `setup_reminders` compares `"%H:%M"` string equality on a 60-second timer (`notifications.py:71-78`); drift means the matching minute can be skipped entirely.
- **Theme toggling barely works.** `toggle_theme` → `refresh_all` (`main.py:187-201`) refreshes four tabs, and only `achievements_tab.refresh` actually rebuilds widgets. `settings_tab` has a `refresh()` that rebuilds — and `refresh_all` never calls it. Habits/log/streak tabs keep their old colours. The user gets a "Theme switched!" dialog for a change that mostly didn't happen.
- **Default theme disagrees with itself**: `data_manager.py:18` defaults to `"light"`, `themes.py:8` defaults to `"dark"`.
- **Unreadable text, by construction.** Black-on-dark: `notifications.py:37, 47` (`fg="black"` on `bg="#2c3e50"`); `main.py:111`; the tooltip at `tabs/streak_tab.py:183` is `bg="black", fg="black"` — invisible. White-on-white: `tabs/settings_tab.py:90` hardcodes `fg="#ffffff"` on the light theme's white `panel_bg`. Roughly 30 widgets hardcode `fg="black"` while the theme system exists two files away.
- **Matplotlib figures are never closed.** `tabs/analytics_tab.py:72` calls `plt.subplots` on every chart click and destroys only the Tk widget; after 20 clicks matplotlib emits its `RuntimeWarning` and the figures leak for the session.
- **Analytics mixes the OO and pyplot APIs.** `analytics.py:32-33, 52-53, 71, 100, 129` call `plt.xticks(...)` / `plt.tight_layout()`, which act on the *current* global figure, not the `ax` that was passed in. It happens to work because only one figure is live at a time — it stops working the moment anything else creates a figure.
- **Tooltips leak Toplevels.** `tabs/streak_tab.py:177-193` creates a parentless `tk.Toplevel` per hover and destroys only the last one stored on the widget; fast mouse movement across 56 cells strands windows.
- **`export_to_csv` has no `return False` on the failure path** (`data_manager.py:105-107`) — returns `None`, which happens to be falsy, so the caller's error branch works by accident.
- **`perfect_day` compares against *all* habits, including archived ones** (`achievements.py:156` uses `habits_list`, not `get_active_habits()`), and `three_month` counts 90 *distinct logged dates* rather than a 90-day span (`achievements.py:169-171`) — so its description "Track for 90 days" is wrong.

---

## 4. TESTABILITY

Functions that could be unit tested **today**, with no refactor and no display. Ranked by value-per-test.

| # | Function | Location | Why it's worth testing |
|---|---|---|---|
| 1 | `AICoach.parse_natural_language` | `ai_coach.py:30` | Pure `str → dict|None`. Writes to permanent storage. Already provably wrong on 8 realistic inputs (§3.3). One parametrized test locks in every fix. **Highest value in the repo.** |
| 2 | `AchievementSystem.calculate_current_streak` | `achievements.py:196` | Pure over `data_manager.habits_data`; a stub object with one attribute is enough. Two confirmed bugs, and it gates achievements. |
| 3 | `AchievementSystem.check_achievement` | `achievements.py:125` | 15 branches, zero coverage, drives points. Needs a 2-attribute stub. Table-driven test, big surface per line of test code. |
| 4 | `DataManager.load_json` / `save_json` | `data_manager.py:27, 37` | Take a filename → `tmp_path` fixture. Tests would pin down the corruption behaviour of §3.4.1–2 and make the atomic-write fix safe. |
| 5 | `DataManager.delete_log` | `data_manager.py:69` | Pure list filtering after construction. A three-line test proves the delete-all-duplicates bug. |
| 6 | `AICoach.suggest_habit` | `ai_coach.py:11` | Trivial keyword map, trivially testable; low bug risk, so low value — but free. |
| 7 | `DataManager.get_active_habits` / `get_logs_by_date` / `get_logs_by_habit` | `data_manager.py:77-87` | One-line filters. Cheap; mostly valuable as regression guards once storage moves to SQL. |
| 8 | `AICoach.analyze_progress` | `ai_coach.py:65` | Pure, returns a string. But it's **dead code** — test it only if you wire it up (which you should; it deduplicates `tabs/ai_coach_tab.py:140`). |
| 9 | `DataManager.export_to_csv` | `data_manager.py:88` | Writes a file, readable back in the test. Medium value; will get rewritten in v2 anyway. |
| 10 | `ThemeManager.get_theme` / `toggle_theme` | `themes.py:31, 44` | `toggle_theme` needs a `root` for `apply_theme`, so it's not GUI-free — skip until `apply_theme` is split out. |

Requires refactor before it can be tested (and each is worth extracting for exactly that reason): both `calculate_longest_streak` and `StreakTab.calculate_current_streak` (constructor builds widgets), all five `Analytics.create_*` aggregations (entangled with `ax`), `AICoachTab.analyze_progress` / `optimize_targets` (entangled with the widget), `LogTab.update_summary`.

**A realistic first test suite is ~120 lines of pytest covering rows 1–5 and catches every bug in §3.1, §3.3, and §3.4.1–4.**

---

## 5. REPO HYGIENE

### 5.1 Committed and shouldn't be

| What | Size / count | Why it's bad |
|---|---|---|
| `evertrack_env312/` | **4,589 files, ~40 MiB** | A macOS/arm64 Python 3.12 virtualenv, including compiled `.dylib` binaries. Doesn't work on any other machine. `evertrack_env312/bin/activate:49` and `pyvenv.cfg` hardcode an absolute local path from the author's machine (`/Users/…/Downloads/EverTrackPro/…`), leaking the local username and directory layout. |
| `__pycache__/` + `tabs/__pycache__/` | 14 `.pyc` | Build artifacts; the committed ones are already stale relative to the sources. |
| `Project Title.docx` | 19 KB binary | A coursework write-up ("suitable for … academic submissions"). Binary in git, undiffable, and it frames the repo as a class assignment. |
| `habits_data.json`, `habits_list.json`, `settings.json`, `achievements.json` | 4 files | Personal usage data (a habit named "maths", a reminder at 17:46) committed as live app state, so every run dirties the working tree. Ship `*.example.json` instead, or seed on first run. |

### 5.2 Exact commands to untrack

Run from the repo root, on a clean tree, on a branch:

```bash
git rm -r --cached evertrack_env312 __pycache__ tabs/__pycache__
```

```bash
git rm --cached "Project Title.docx" habits_data.json habits_list.json settings.json achievements.json
```

Then create `.gitignore` before committing:

```bash
printf '%s\n' '__pycache__/' '*.py[cod]' '.venv/' 'venv/' 'evertrack_env312/' '*.egg-info/' '.pytest_cache/' '.DS_Store' '*.db' '*.sqlite3' 'habits_data.json' 'habits_list.json' 'settings.json' 'achievements.json' '*.docx' > .gitignore
```

```bash
git add .gitignore && git commit -m "Remove virtualenv, caches and local data from version control"
```

Note: this stops tracking them going forward but **the 40 MiB stays in history** (`git count-objects -vH` → 41.34 MiB pack). Clones stay slow and the leaked local path stays reachable. Two options:

```bash
# Option A — purge from history (rewrites all commits; force-push required)
pipx run git-filter-repo --path evertrack_env312 --path __pycache__ --path tabs/__pycache__ --invert-paths
```

```bash
# Option B — the honest one for a portfolio repo with 8 low-quality commit messages:
# start a clean repo with a real history and force-push it.
```

Given the commit log reads `init repo`, `initial commit`, `Initial commit`, `ui update`, `ui updation`, `further updation and artificial intelligence recommendation`, `final commit` — **Option B costs you nothing and buys you a history a reviewer can read.** The current history has no value to preserve.

### 5.3 Missing

| Missing | Impact |
|---|---|
| `.gitignore` | root cause of everything in §5.1 |
| `requirements.txt` / `pyproject.toml` | nobody can install this. Actual runtime deps, from the committed venv: `matplotlib==3.10.8`, `reportlab==4.4.7` (+ their transitive `numpy`, `pillow`, `contourpy`, `cycler`, `fonttools`, `kiwisolver`, `packaging`, `pyparsing`, `python-dateutil`, `six`). `tkinter` is stdlib but needs a system Tk. |
| `LICENSE` | no license = all rights reserved; nobody may legally reuse it |
| tests / `pytest.ini` | zero tests, and §4 shows five of them are nearly free |
| CI (`.github/workflows/`) | nothing verifies the code even imports |
| `Dockerfile` | none — and this is directly on your stated learning path |
| Python version pin / `README` run instructions that work | see below |
| a screenshot in the README | for a GUI app this is the single highest-signal missing artifact |

### 5.4 Where `readme.md` contradicts the code

| README says | Reality |
|---|---|
| `python evertrack.py` (`readme.md:44`) | No such file. The file is `EverTrack.py` (case-sensitive mismatch), **and it's the dead monolith**. The real command is `python main.py`. |
| `pip install matplotlib` (`readme.md:40`) | Also needs `reportlab`, or "Generate PDF Report" fails (`tabs/settings_tab.py:275`). |
| "Future Enhancements: Add notifications and reminders" (`readme.md:54`) | Already implemented — `notifications.py`, 102 lines, wired up in `main.py:41`. |
| "Future Enhancements: Add habit streaks and goal tracking" (`readme.md:56`) | Already implemented — `tabs/streak_tab.py`, plus `daily_target` on every habit. |
| Features list: habits, table, bar/line/pie charts (`readme.md:10-13`) | Undersells by half: omits the achievement system (15 badges), the streak calendar, the AI Coach tab, themes, CSV/PDF export, backup. The README describes `EverTrack.py`, not `main.py`. |
| "Technologies Used: Python 3, Tkinter, Matplotlib, JSON" (`readme.md:16-19`) | Omits ReportLab. |
| Author `@Nevil Amraniya` → `github.com/nicks1107` (`readme.md:60`) | Repo lives at `github.com/nevil-codes/evertrack`; the link 404s or points elsewhere. Commits are authored by `niks1107 <niksofficial14@gmail.com>`. Three identities for one person, in a repo meant to prove that person's work. |
| No mention of "AI" at all | The app's title bar says "AI-Powered Smart Habit Tracking" (`main.py:31`) and there is an "AI Coach" tab. See §6. |

---

## 6. VERDICT

### 6.1 The 90-second read

A hiring manager opens the repo and sees, in this order:

1. **A file tree dominated by `evertrack_env312/`.** Before reading one line of your code, the conclusion is formed: *this person committed their virtualenv*. That single fact says "has not worked on a team, does not know git." It is the most damaging thing in the repository and it takes ten minutes to fix.
2. **No `requirements.txt`, no `.gitignore`, no tests, no CI, no LICENSE, no Dockerfile.** Nothing that says "software", everything that says "coursework folder uploaded to GitHub".
3. **`Project Title.docx`** — confirms coursework.
4. **Commit log**: `init repo`, `initial commit`, `Initial commit`, `ui update`, `ui updation`, `final commit`. Eight commits, essentially one day of work. No branches, no PRs, no incremental story.
5. **Two entry points**, `EverTrack.py` (1,491 lines) and `main.py`, with the README pointing at neither correctly. The reviewer cannot tell what runs. Half your visible line count is dead code.
6. **"AI-Powered"** in the window title, an "AI Coach" tab — and the implementation is `if 'streak' in query_lower` returning a hardcoded paragraph. **This is the second-most damaging thing here.** A technical reviewer spots it in fifteen seconds, and it converts "junior, needs mentoring" into "overstates their work" — which is disqualifying in a way that being junior is not.

Verdict at 90 seconds: *first-year student project, GUI-focused, no engineering practice, and the marketing doesn't match the code.* They will not open `data_manager.py`.

**And that's genuinely unfair to what's underneath.** The `tabs/` refactor is a real decomposition; `data_manager.py` is a coherent (if flawed) storage boundary; `achievements.py` is clean, GUI-free, testable code. The problem is that none of that is visible past the venv, and none of it is on the path you're actually walking. **Nothing in this repo demonstrates SQL, Docker, FastAPI, or MLOps** — the four things you want it to say about you. A Tkinter app writing four JSON files is the *opposite* signal for a data-engineering role.

Blunt version: the repository currently costs you more than it earns. Sixty minutes of hygiene work turns it neutral. The v2 plan below turns it into the thing you actually want to point at.

### 6.2 Ordered v2 work plan

Every step ends with a runnable app. Each is a separate PR on a branch — the PR trail is itself the artifact.

---

**Step 0 — Hygiene. ~1 hour.**
`.gitignore`; untrack the venv, caches, `.docx` and personal JSON (§5.2); `requirements.txt` with pinned versions; MIT `LICENSE`; **delete `EverTrack.py`**; rewrite `readme.md` to describe `main.py` with correct install/run steps, a screenshot, and honest feature claims. Rename "AI Coach" → "Coach" or "Insights" and describe it as *rule-based* — keep the feature, drop the overclaim. Then rewrite the history (§5.2 Option B).
*Demonstrates:* basic professionalism. **Highest ROI in this document by an order of magnitude.** Do it today; do not let the rest of the plan block it.

**Step 1 — `core/` + first tests. ~4–6 hours.**
Create `core/` with `models.py` (dataclasses `Habit`, `LogEntry` with validation), `streak.py` (one implementation, replacing both copies), `stats.py`, `parser.py`. Move `achievements.py` in. Import from `core/` in the tabs; keep JSON storage. Add `tests/` with pytest covering §4 rows 1–5 and fix every bug those tests expose (§3.1, §3.3, §3.4.3–4). Add a GitHub Actions workflow running `pytest` + `ruff`.
*Demonstrates:* separating domain from presentation, testing, CI. **This is the step that makes every later step cheap.**

**Step 2 — SQLite behind a repository interface. ~5–7 hours.**
Define `core/storage.py` with an abstract `Repository`. Implement `SQLiteRepository` against the DDL in §2.5 (foreign keys on, CHECK constraints, indexes, the two views). Write `scripts/migrate_json_to_sqlite.py`: idempotent, transactional, reports orphans and unmappable rows (§2.5) rather than silently coercing them. Point the Tk app at the repository — the seventeen direct-JSON call sites (§2.6) collapse into one.
*Demonstrates:* **SQL** — schema design, constraints, foreign keys, indexes, views, a real migration with data-quality handling. This is your first genuine data-engineering artifact. Put the DDL and the migration report in the README.

**Step 3 — FastAPI service over the same core. ~5–7 hours.**
`api/` with FastAPI + Pydantic v2 models (Pydantic is where the §3.4 validation gaps actually get closed): `POST/GET/DELETE /habits`, `POST/GET/DELETE /logs`, `GET /stats/streak`, `GET /stats/daily`, `GET /achievements`. Same `Repository`, no duplicated logic. `pytest` + `httpx` tests against the endpoints. The Tk app keeps working, unchanged, against the same DB.
*Demonstrates:* **FastAPI**, API design, request validation, auto-generated OpenAPI. One service, two frontends, one core — the clearest possible statement that you understand layering.

**Step 4 — Docker + Postgres. ~4–5 hours.**
Multi-stage `Dockerfile` for the API (non-root user, pinned base). `docker-compose.yml` with `api` + `postgres` + a healthcheck. Add `PostgresRepository` (SQLAlchemy Core or asyncpg) and Alembic migrations; keep SQLite as the local/test backend so the test suite stays fast. Extend CI to build the image and run the suite against Postgres in a service container.
*Demonstrates:* **Docker**, compose, migrations, dev/prod parity, DB portability behind an interface. `docker compose up` → working API is the single best line in a README for the roles you're targeting.

**Step 5 — Pick exactly one, and do it properly. ~6–10 hours.**
- **(a) Data pipeline** — scheduled job exporting `habit_log` to partitioned Parquet, with data-quality assertions (row counts, null checks, date ranges) failing loudly; a small dbt project over Postgres with tests. *Strongest for a data-engineering role.*
- **(b) MLOps** — predict tomorrow's completion per habit from features you already have (day-of-week, recent streak, rolling mean duration); track experiments with MLflow; serve behind `POST /predict` in the same API; a scheduled retrain in CI. *Strongest for an MLOps role. Be scrupulously honest about a model trained on three months of one person's data — writing that limitation up yourself is itself a strong signal.*
- **(c) Observability** — structured logging, Prometheus metrics on the API, Grafana in compose.

**Do not do all three.** One finished, documented, tested vertical beats three half-built ones — and the current repo is already a lesson in what "more features, no foundation" looks like from the outside.

---

**Suggested ordering if time is short:** Step 0 today. Step 2's DDL + migration next (SQL is what you're learning right now, and it's the single most portable skill on the list). Then Step 3 and 4 together as one "containerized API" push. Step 1's tests can be folded into whichever step you're on, but every step gets slower and riskier without them.

**Rename the repo at the end.** `evertrack` as a Tkinter habit tracker is a student project. `evertrack` as *"habit-tracking data platform: FastAPI + Postgres + Docker, with a legacy Tk client"* is a portfolio piece — and it will be a truthful description of what you built.
