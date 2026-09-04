# ai_coach.py - Rule-based coaching helpers (thin adapter over core.parser / core.stats)
from core import parser, stats


class AICoach:
    """Keyword-driven habit suggestions and plain-English log parsing.

    Nothing here is machine learning: see core/parser.py for what it actually does.
    """

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def suggest_habit(self, goal):
        return parser.suggest_habit(goal)

    def parse(self, text):
        """Return a core.parser.ParseResult, which explains failures."""
        return parser.parse(text)

    def parse_natural_language(self, text):
        """Backwards-compatible shim: dict on success, None on failure."""
        result = parser.parse(text)
        if not result.ok:
            return None
        return {
            "habit": result.activity.habit,
            "duration": result.activity.duration_min,
            "date": result.activity.log_date,
        }

    def analyze_progress(self):
        logs = self.data_manager.log_models()
        if not logs:
            return "No data to analyze yet!"

        summary = stats.totals(logs)
        analysis = (
            "📊 Progress Analysis\n\n"
            f"Total Activities: {summary.activities}\n"
            f"Total Time: {summary.total_minutes:.0f} minutes ({summary.total_hours:.1f} hours)\n"
            f"Completion Rate: {summary.completion_rate:.1f}%\n\n"
        )

        if summary.completion_rate >= 80:
            return analysis + "✨ Excellent! You're crushing it!"
        if summary.completion_rate >= 60:
            return analysis + "👍 Good progress!"
        return analysis + "💪 Keep pushing!"
