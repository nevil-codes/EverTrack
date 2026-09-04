
import matplotlib

matplotlib.use('TkAgg')

import argparse
import sys
import tkinter as tk
from tkinter import messagebox, ttk

# Import custom modules
try:
    from achievements import AchievementSystem
    from ai_coach import AICoach
    from analytics import Analytics
    from data_manager import DataManager
    from notifications import NotificationManager
    from themes import ThemeManager
    from ui_components import UIComponents
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are in the same directory!")
    sys.exit(1)


class EverTrackPro:
    """Main application class for EverTrack Pro"""

    def __init__(self, root, data_manager=None):
        self.root = root
        self.root.title("EverTrack Pro - Smart Habit Tracking")
        self.root.geometry("1300x800")

        # Initialize managers
        self.data_manager = data_manager or DataManager()
        self.theme_manager = ThemeManager(self.root, self.data_manager)
        self.ui = UIComponents(self.root, self.theme_manager)
        self.ai_coach = AICoach(self.data_manager)
        self.analytics = Analytics(self.data_manager, self.theme_manager)
        self.achievement_system = AchievementSystem(self.data_manager)
        self.notification_manager = NotificationManager(self.root, self.data_manager)

        # Apply initial theme
        self.theme_manager.apply_theme()

        # Surface anything wrong with the stored data instead of starting empty
        self.report_data_problems()

        # Check for new achievements
        self.check_achievements()

        # Setup reminders
        self.setup_reminders()

        # Create UI
        self.create_main_ui()

        # Refresh tables
        self.refresh_all()

        print("✓ EverTrack Pro initialized successfully!")

    def create_main_ui(self):
        """Create the main user interface"""
        # Title bar
        self.create_title_bar()

        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # Create all tabs
        self.create_habits_tab()
        self.create_log_tab()
        self.create_streak_calendar_tab()
        self.create_achievements_tab()
        self.create_ai_coach_tab()
        self.create_analytics_tab()
        self.create_settings_tab()

    def create_title_bar(self):
        """Create the title bar with branding and controls"""
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        # App title
        title_label = tk.Label(
            title_frame,
            text="EverTrack Pro ✨",
            font=("Arial", 28, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side="left", padx=20, pady=20)

        # Points display
        points = self.achievement_system.get_total_points()
        self.points_label = tk.Label(
            title_frame,
            text=f"🏆 {points} Points",
            font=("Arial", 14, "bold"),
            bg="#2c3e50",
            fg="#f39c12"
        )
        self.points_label.pack(side="right", padx=20)

        # Theme toggle button
        theme_btn = tk.Button(
            title_frame,
            text="🌓 Toggle Theme",
            command=self.toggle_theme,
            bg="#34495e",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        )
        theme_btn.pack(side="right", padx=10)

    def create_habits_tab(self):
        """Create the habits management tab"""
        from tabs.habits_tab import HabitsTab
        habits_tab = HabitsTab(self.notebook, self)
        self.notebook.add(habits_tab.frame, text="📋 Manage Habits")
        self.habits_tab = habits_tab

    def create_log_tab(self):
        """Create the daily log tab"""
        from tabs.log_tab import LogTab
        log_tab = LogTab(self.notebook, self)
        self.notebook.add(log_tab.frame, text="✓ Daily Log")
        self.log_tab = log_tab

    def create_streak_calendar_tab(self):
        """Create the streak calendar tab"""
        from tabs.streak_tab import StreakTab
        streak_tab = StreakTab(self.notebook, self)
        self.notebook.add(streak_tab.frame, text="🔥 Streak Calendar")
        self.streak_tab = streak_tab

    def create_achievements_tab(self):
        """Create the achievements tab"""
        from tabs.achievements_tab import AchievementsTab
        achievements_tab = AchievementsTab(self.notebook, self)
        self.notebook.add(achievements_tab.frame, text="🏆 Achievements")
        self.achievements_tab = achievements_tab

    def create_ai_coach_tab(self):
        """Create the AI coach tab"""
        from tabs.ai_coach_tab import AICoachTab
        ai_coach_tab = AICoachTab(self.notebook, self)
        self.notebook.add(ai_coach_tab.frame, text="🧭 Coach")
        self.ai_coach_tab = ai_coach_tab

    def create_analytics_tab(self):
        """Create the analytics tab"""
        from tabs.analytics_tab import AnalyticsTab
        analytics_tab = AnalyticsTab(self.notebook, self)
        self.notebook.add(analytics_tab.frame, text="📊 Analytics")
        self.analytics_tab = analytics_tab

    def create_settings_tab(self):
        """Create the settings tab"""
        from tabs.settings_tab import SettingsTab
        settings_tab = SettingsTab(self.notebook, self)
        self.notebook.add(settings_tab.frame, text="⚙️ Settings")
        self.settings_tab = settings_tab

    def report_data_problems(self):
        """Tell the user when stored data could not be read or had bad records."""
        problems = getattr(self.data_manager, "problems", [])
        if not problems:
            return
        for problem in problems:
            print(f"! {problem}")
        messagebox.showwarning(
            "Data problems",
            "EverTrack had trouble with your saved data:\n\n• "
            + "\n• ".join(problems[:5])
            + ("\n\n(and more — see the console)" if len(problems) > 5 else "")
        )

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.theme_manager.toggle_theme()
        self.refresh_all()
        messagebox.showinfo("Theme Changed", f"Theme switched to {self.theme_manager.get_current_theme().title()} Mode!")

    def check_achievements(self):
        """Check for new unlocked achievements"""
        new_achievements = self.achievement_system.check_all_achievements()
        if new_achievements:
            for achievement in new_achievements:
                self.notification_manager.show_achievement_notification(achievement)

    def setup_reminders(self):
        """Check reminders once a minute, forever.

        The timer is always rescheduled: it used to stop the first time
        notifications were switched off, and never restarted.
        """
        if self.data_manager.settings.get("notifications", True):
            self.notification_manager.setup_reminders()
        self.root.after(60000, self.setup_reminders)

    def refresh_all(self):
        """Refresh every tab that shows stored data."""
        for name in ("habits_tab", "log_tab", "streak_tab", "achievements_tab", "settings_tab"):
            tab = getattr(self, name, None)
            if tab is None:
                continue
            try:
                tab.refresh()
            except Exception as exc:  # one broken tab must not blank the others
                print(f"Error refreshing {name}: {exc}")

        points = self.achievement_system.get_total_points()
        self.points_label.config(text=f"🏆 {points} Points")


def build_data_manager(argv=None):
    """Choose a storage backend from the command line."""
    parser = argparse.ArgumentParser(description="EverTrack Pro")
    parser.add_argument(
        "--storage", choices=("json", "sqlite"), default="json",
        help="where to keep data: the original JSON files (default) or a SQLite database"
    )
    parser.add_argument(
        "--database", default="evertrack.db",
        help="SQLite database path, used with --storage sqlite (default: evertrack.db)"
    )
    args = parser.parse_args(argv)

    if args.storage == "sqlite":
        print(f"storage: SQLite ({args.database})")
        return DataManager.sqlite(args.database)

    print("storage: JSON files in the current directory")
    return DataManager()


def main(argv=None):
    """Main entry point for the application"""
    print("=" * 50)
    print("EverTrack Pro - Habit Tracker")
    print("Version 2.0 (core refactor)")
    print("=" * 50)
    print("\nInitializing application...")

    data_manager = build_data_manager(argv)
    root = tk.Tk()
    EverTrackPro(root, data_manager)
    print("\n✓ Application started successfully!")
    print("=" * 50)

    try:
        root.mainloop()
    finally:
        data_manager.close()


if __name__ == "__main__":
    main()
