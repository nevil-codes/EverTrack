# achievements.py - Achievement and badge system (thin adapter over core.achievements)
from core import achievements as core_achievements
from core.streak import current_streak, longest_streak


class AchievementSystem:
    """Manages achievements and badges for the desktop app."""

    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.all_achievements = {
            a.code: {"name": a.name, "description": a.description, "icon": a.icon, "points": a.points}
            for a in core_achievements.CATALOGUE
        }

    # ------------------------------------------------------------- checks

    def check_all_achievements(self):
        """Unlock everything newly earned; return the achievements unlocked now."""
        unlocked = self.data_manager.get_unlocked()

        earned = core_achievements.newly_unlocked(
            self.data_manager.log_models(), self.data_manager.habit_models(), unlocked
        )
        if earned:
            # Points are derived from this list, never incremented, so they
            # cannot drift from the badges actually held.
            self.data_manager.set_unlocked(unlocked + earned)

        return [self.all_achievements[code] for code in earned]

    def check_achievement(self, achievement_id):
        return core_achievements.is_unlocked(
            achievement_id, self.data_manager.log_models(), self.data_manager.habit_models()
        )

    # -------------------------------------------------------------- stats

    def calculate_current_streak(self):
        return current_streak([log.log_date for log in self.data_manager.log_models()])

    def calculate_longest_streak(self):
        return longest_streak([log.log_date for log in self.data_manager.log_models()])

    def get_total_points(self):
        return core_achievements.total_points(self.data_manager.get_unlocked())

    def get_unlocked_achievements(self):
        codes = self.data_manager.get_unlocked()
        return [self.all_achievements[code] for code in codes if code in self.all_achievements]

    def get_locked_achievements(self):
        codes = set(self.data_manager.get_unlocked())
        return [info for code, info in self.all_achievements.items() if code not in codes]
