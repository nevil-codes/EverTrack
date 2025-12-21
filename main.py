# main.py - Main entry point for EverTrack Pro
"""
EverTrack Pro - AI-Powered Smart Habit Tracking Application

Main Features:
- AI-powered habit creation and natural language input
- Visual streak calendar with heatmap
- Achievements and badges system
- Desktop notifications and reminders
- Dark/Light theme toggle
- Export to CSV/PDF
- Advanced analytics dashboard
- Notes and reflections
- Multi-tab interface

File Structure:
- main.py (this file) - Main application entry point
- data_manager.py - Handles all data operations
- ui_components.py - Reusable UI components
- ai_coach.py - AI features and natural language processing
- analytics.py - Charts and data visualization
- achievements.py - Badge system and achievement tracking
- notifications.py - Desktop notifications and reminders
- themes.py - Theme management

Author: EverTrack Development Team
Version: 2.0 Pro
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sys
import os

# Import custom modules
try:
    from data_manager import DataManager
    from ui_components import UIComponents
    from ai_coach import AICoach
    from analytics import Analytics
    from achievements import AchievementSystem
    from notifications import NotificationManager
    from themes import ThemeManager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure all required files are in the same directory!")
    sys.exit(1)


class EverTrackPro:
    """Main application class for EverTrack Pro"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EverTrack Pro - AI-Powered Smart Habit Tracking")
        self.root.geometry("1300x800")
        
        # Initialize managers
        self.data_manager = DataManager()
        self.theme_manager = ThemeManager(self.root, self.data_manager)
        self.ui = UIComponents(self.root, self.theme_manager)
        self.ai_coach = AICoach(self.data_manager)
        self.analytics = Analytics(self.data_manager, self.theme_manager)
        self.achievement_system = AchievementSystem(self.data_manager)
        self.notification_manager = NotificationManager(self.root, self.data_manager)
        
        # Apply initial theme
        self.theme_manager.apply_theme()
        
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
            text="EverTrack Pro 🤖✨",
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
        self.notebook.add(ai_coach_tab.frame, text="🤖 AI Coach")
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
        """Setup habit reminders"""
        if self.data_manager.settings.get("notifications", True):
            self.notification_manager.setup_reminders()
            self.root.after(60000, self.setup_reminders)  # Check every minute
    
    def refresh_all(self):
        """Refresh all UI components"""
        try:
            if hasattr(self, 'habits_tab'):
                self.habits_tab.refresh()
            if hasattr(self, 'log_tab'):
                self.log_tab.refresh()
            if hasattr(self, 'streak_tab'):
                self.streak_tab.refresh()
            if hasattr(self, 'achievements_tab'):
                self.achievements_tab.refresh()
            
            # Update points display
            points = self.achievement_system.get_total_points()
            self.points_label.config(text=f"🏆 {points} Points")
        except Exception as e:
            print(f"Error refreshing UI: {e}")


def main():
    """Main entry point for the application"""
    print("=" * 50)
    print("EverTrack Pro - AI-Powered Habit Tracker")
    print("Version 2.0")
    print("=" * 50)
    print("\nInitializing application...")
    
    root = tk.Tk()
    app = EverTrackPro(root)
    
    print("\n✓ Application started successfully!")
    print("=" * 50)
    
    root.mainloop()


if __name__ == "__main__":
    main()