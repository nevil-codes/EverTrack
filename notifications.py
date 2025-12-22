# notifications.py - Desktop notifications and reminders
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta

class NotificationManager:
    """Manages desktop notifications and reminders"""
    
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager
        self.shown_reminders = set()
    
    def show_notification(self, title, message, icon="ℹ️"):
        """Show a desktop notification"""
        if not self.data_manager.settings.get("notifications", True):
            return
        
        notification = tk.Toplevel(self.root)
        notification.title(title)
        notification.geometry("350x120")
        notification.configure(bg="#2c3e50")
        
        # Position at top right
        screen_width = self.root.winfo_screenwidth()
        notification.geometry(f"+{screen_width-370}+20")
        
        # Icon and title
        header = tk.Frame(notification, bg="#2c3e50")
        header.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            header,
            text=f"{icon} {title}",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="black"
        ).pack(anchor="w")
        
        # Message
        tk.Label(
            notification,
            text=message,
            font=("Arial", 10),
            bg="#2c3e50",
            fg="black",
            wraplength=300,
            justify="left"
        ).pack(padx=10, pady=5)
        
        # Auto close after 5 seconds
        notification.after(5000, notification.destroy)
    
    def show_achievement_notification(self, achievement):
        """Show achievement unlocked notification"""
        title = "🏆 Achievement Unlocked!"
        message = f"{achievement['icon']} {achievement['name']}\n+{achievement['points']} points"
        self.show_notification(title, message, "🏆")
    
    def show_reminder(self, habit_name):
        """Show habit reminder"""
        title = "⏰ Reminder"
        message = f"Time to practice: {habit_name}"
        self.show_notification(title, message, "⏰")
    
    def setup_reminders(self):
        """Check and show reminders for habits"""
        if not self.data_manager.settings.get("notifications", True):
            return
        
        current_time = datetime.now().strftime("%H:%M")
        reminder_times = self.data_manager.settings.get("reminder_times", {})
        
        for habit_name, reminder_time in reminder_times.items():
            reminder_key = f"{habit_name}_{datetime.now().strftime('%Y-%m-%d')}"
            
            if reminder_time == current_time and reminder_key not in self.shown_reminders:
                self.show_reminder(habit_name)
                self.shown_reminders.add(reminder_key)
        
        # Clean up old reminders
        today = datetime.now().strftime('%Y-%m-%d')
        self.shown_reminders = {r for r in self.shown_reminders if today in r}
    
    def show_streak_notification(self, streak_days):
        """Show streak milestone notification"""
        if streak_days in [7, 10, 30, 50, 100]:
            title = "🔥 Streak Milestone!"
            message = f"Amazing! {streak_days}-day streak achieved!"
            self.show_notification(title, message, "🔥")
    
    def show_motivational_notification(self):
        """Show random motivational notification"""
        import random
        messages = [
            "Keep going! You're building amazing habits!",
            "Consistency is key! You're doing great!",
            "Small steps lead to big changes!",
            "You're stronger than you think!",
            "Progress, not perfection!",
        ]
        message = random.choice(messages)
        self.show_notification("💪 Motivation", message, "💪")