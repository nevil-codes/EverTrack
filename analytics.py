# analytics.py - Charts and data visualization
"""Chart rendering only. All aggregation lives in core.stats."""
from core import stats


class Analytics:
    """Draws the app's charts onto a matplotlib Axes."""

    def __init__(self, data_manager, theme_manager):
        self.data_manager = data_manager
        self.theme_manager = theme_manager

    def _logs(self):
        return self.data_manager.log_models()

    @staticmethod
    def _empty(ax, message="No data available"):
        ax.text(0.5, 0.5, message, ha="center", va="center")
        return True

    def create_bar_chart(self, ax):
        totals = stats.minutes_per_habit(self._logs())
        if not totals:
            return self._empty(ax)

        habits = list(totals)
        ax.bar(habits, [totals[h] for h in habits], edgecolor="black", linewidth=1.2)
        ax.set_xlabel("Habits", fontsize=10, fontweight="bold")
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight="bold")
        ax.set_title("Total Time Spent Per Habit", fontsize=12, fontweight="bold")
        ax.tick_params(axis="x", labelrotation=45)

    def create_line_chart(self, ax):
        daily = stats.minutes_per_day(self._logs())
        if not daily:
            return self._empty(ax)

        ax.plot(list(daily), list(daily.values()), marker="o", linewidth=2, markersize=6, color="#3498db")
        ax.set_xlabel("Date", fontsize=10, fontweight="bold")
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight="bold")
        ax.set_title("Daily Habit Progress", fontsize=12, fontweight="bold")
        ax.tick_params(axis="x", labelrotation=45)

    def create_pie_chart(self, ax):
        totals = stats.minutes_per_habit(self._logs())
        if not totals:
            return self._empty(ax)

        ax.pie(list(totals.values()), labels=list(totals), autopct="%1.1f%%", startangle=90)
        ax.set_title("Time Distribution Across Habits", fontsize=12, fontweight="bold")

    def create_completion_chart(self, ax):
        rates = stats.completion_rate_per_habit(self._logs())
        if not rates:
            return self._empty(ax)

        habits = list(rates)
        values = [rates[h] for h in habits]
        colors = ["#27ae60" if v >= 80 else "#f39c12" if v >= 50 else "#e74c3c" for v in values]

        ax.barh(habits, values, color=colors, edgecolor="black", linewidth=1.2)
        ax.set_xlabel("Completion Rate (%)", fontsize=10, fontweight="bold")
        ax.set_ylabel("Habits", fontsize=10, fontweight="bold")
        ax.set_title("Habit Completion Rate", fontsize=12, fontweight="bold")
        ax.set_xlim(0, 100)

    def create_weekly_comparison(self, ax):
        buckets = stats.weekly_buckets(self._logs())
        if not any(minutes for _, minutes in buckets):
            return self._empty(ax)

        labels = [label for label, _ in buckets]
        ax.bar(labels, [minutes for _, minutes in buckets], color="#3498db",
               edgecolor="black", linewidth=1.2)
        ax.set_xlabel("Week", fontsize=10, fontweight="bold")
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight="bold")
        ax.set_title("Last 4 Weeks Comparison", fontsize=12, fontweight="bold")
        ax.tick_params(axis="x", labelrotation=20)
