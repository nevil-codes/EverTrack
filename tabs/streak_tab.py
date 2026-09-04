# tabs/streak_tab.py
import tkinter as tk

from core import stats
from core.streak import current_streak, longest_streak, streak_is_at_risk

WEEKS = 8
DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
INTENSITY = ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]


class StreakTab:
    """Visual streak calendar tab"""

    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()

    def create_ui(self):
        theme = self.app.theme_manager.get_theme()

        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = tk.Frame(container, bg="#e74c3c", height=70)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🔥 Your Habit Streak Calendar",
            font=("Arial", 22, "bold"),
            bg="#e74c3c",
            fg="white"
        ).pack(pady=20)

        self.calendar_frame = tk.Frame(container, bg=theme["panel_bg"], relief="solid", borderwidth=1)
        self.calendar_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.draw_calendar()

    def draw_calendar(self):
        """Draw the streak calendar heatmap.

        Columns are weeks, rows are weekdays. The window is aligned to Monday so
        the row labels are true, and it ends with the current week, so today is
        always on the grid.
        """
        theme = self.app.theme_manager.get_theme()

        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        logs = self.app.data_manager.log_models()
        dates, counts = stats.calendar_window(logs, weeks=WEEKS)
        busiest = max(counts.values()) if counts else 0

        tk.Label(
            self.calendar_frame,
            text=f"Last {WEEKS} Weeks Activity",
            font=("Arial", 16, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).grid(row=0, column=0, columnspan=WEEKS + 1, pady=15)

        for row, label in enumerate(DAY_LABELS):
            tk.Label(
                self.calendar_frame,
                text=label,
                font=("Arial", 10, "bold"),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                width=8
            ).grid(row=row + 1, column=0, padx=5, pady=2)

        for index, day in enumerate(dates):
            week, weekday = divmod(index, 7)
            count = counts.get(day, 0)

            cell = tk.Label(
                self.calendar_frame,
                text=str(day.day) if day.day == 1 else "",
                font=("Arial", 9),
                bg=self._intensity(count, busiest),
                fg="#7f8c8d" if count == 0 else "black",
                width=5,
                height=2,
                relief="solid",
                borderwidth=1
            )
            cell.grid(row=weekday + 1, column=week + 1, padx=2, pady=2)

            plural = "activity" if count == 1 else "activities"
            self.create_tooltip(cell, f"{day:%a %d %b %Y}\n{count} {plural}")

        self._draw_legend(theme)
        self._draw_stats(theme, [log.log_date for log in logs])

    @staticmethod
    def _intensity(count, busiest):
        if count == 0 or busiest == 0:
            return INTENSITY[0]
        step = min(int(count / busiest * (len(INTENSITY) - 1) + 0.999), len(INTENSITY) - 1)
        return INTENSITY[step]

    def _draw_legend(self, theme):
        legend = tk.Frame(self.calendar_frame, bg=theme["panel_bg"])
        legend.grid(row=9, column=0, columnspan=WEEKS + 1, pady=20)

        tk.Label(legend, text="Less", bg=theme["panel_bg"], fg=theme["fg"],
                 font=("Arial", 9)).pack(side="left", padx=5)
        for color in INTENSITY:
            tk.Label(legend, bg=color, width=4, height=1,
                     relief="solid", borderwidth=1).pack(side="left", padx=2)
        tk.Label(legend, text="More", bg=theme["panel_bg"], fg=theme["fg"],
                 font=("Arial", 9)).pack(side="left", padx=5)

    def _draw_stats(self, theme, dates):
        panel = tk.Frame(self.calendar_frame, bg=theme["panel_bg"])
        panel.grid(row=10, column=0, columnspan=WEEKS + 1, pady=20)

        current = current_streak(dates)
        longest = longest_streak(dates)

        tk.Label(panel, text=f"🔥 Current Streak: {current} days", font=("Arial", 18, "bold"),
                 bg=theme["panel_bg"], fg="#e74c3c").pack(pady=5)
        tk.Label(panel, text=f"🏆 Longest Streak: {longest} days", font=("Arial", 16),
                 bg=theme["panel_bg"], fg="#f39c12").pack(pady=5)

        if current and streak_is_at_risk(dates):
            message = "⏳ Nothing logged today yet — log something to keep the streak alive!"
        elif current >= 7:
            message = "🌟 Amazing! Keep the momentum going!"
        elif current >= 3:
            message = "💪 Great start! You're building consistency!"
        elif current > 0:
            message = "🌱 Good! Every day counts!"
        else:
            message = "🚀 Start your streak today!"

        tk.Label(panel, text=message, font=("Arial", 12),
                 bg=theme["panel_bg"], fg=theme["fg"]).pack(pady=10)

    def create_tooltip(self, widget, text):
        """Show a small tooltip while the pointer rests on a cell."""
        def show(event):
            hide(event)
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
            tk.Label(
                tooltip, text=text, bg="#2c3e50", fg="white", relief="solid",
                borderwidth=1, font=("Arial", 9), padx=6, pady=3, justify="left"
            ).pack()
            widget.tooltip = tooltip

        def hide(_event):
            tooltip = getattr(widget, "tooltip", None)
            if tooltip is not None:
                tooltip.destroy()
                widget.tooltip = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)
        widget.bind("<Destroy>", hide)

    # Kept so other tabs and tests can ask this tab for the same numbers.
    def calculate_current_streak(self):
        return current_streak([log.log_date for log in self.app.data_manager.log_models()])

    def calculate_longest_streak(self):
        return longest_streak([log.log_date for log in self.app.data_manager.log_models()])

    def refresh(self):
        self.draw_calendar()
