# tabs/streak_tab.py
import tkinter as tk
from datetime import datetime, timedelta
from collections import defaultdict

class StreakTab:
    """Visual streak calendar tab"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()
    
    def create_ui(self):
        """Create the streak calendar UI"""
        theme = self.app.theme_manager.get_theme()
        
        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Frame(container, bg="#e74c3c", height=70)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🔥 Your Habit Streak Calendar",
            font=("Arial", 22, "bold"),
            bg="#e74c3c",
            fg="black"
        ).pack(pady=20)
        
        # Calendar frame
        self.calendar_frame = tk.Frame(container, bg=theme["panel_bg"], relief="solid", borderwidth=1)
        self.calendar_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.draw_calendar()
    
    def draw_calendar(self):
        """Draw the streak calendar heatmap"""
        theme = self.app.theme_manager.get_theme()
        
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Get last 8 weeks
        today = datetime.now()
        start_date = today - timedelta(days=56)
        
        # Count activities per day
        daily_counts = defaultdict(int)
        for log in self.app.data_manager.habits_data:
            log_date = datetime.strptime(log['date'], "%Y-%m-%d")
            if log_date >= start_date:
                daily_counts[log['date']] += 1
        
        max_count = max(daily_counts.values()) if daily_counts else 1
        
        # Title
        tk.Label(
            self.calendar_frame,
            text="Last 8 Weeks Activity",
            font=("Arial", 16, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).grid(row=0, column=0, columnspan=9, pady=15)
        
        # Day labels
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            tk.Label(
                self.calendar_frame,
                text=day,
                font=("Arial", 10, "bold"),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                width=8
            ).grid(row=i+1, column=0, padx=5, pady=2)
        
        # Draw calendar cells
        for week in range(8):
            for day in range(7):
                date = start_date + timedelta(days=week*7 + day)
                date_str = date.strftime("%Y-%m-%d")
                count = daily_counts.get(date_str, 0)
                
                # Color based on activity count
                if count == 0:
                    color = "#ebedf0"
                    text_color = "#7f8c8d"
                elif count <= max_count * 0.25:
                    color = "#c6e48b"
                    text_color = "black"
                elif count <= max_count * 0.5:
                    color = "#7bc96f"
                    text_color = "black"
                elif count <= max_count * 0.75:
                    color = "#239a3b"
                    text_color = "black"
                else:
                    color = "#196127"
                    text_color = "black"
                
                cell = tk.Label(
                    self.calendar_frame,
                    text=str(date.day) if date.day <= 7 or date.day % 7 == 0 else "",
                    font=("Arial", 9),
                    bg=color,
                    fg=text_color,
                    width=5,
                    height=2,
                    relief="solid",
                    borderwidth=1
                )
                cell.grid(row=day+1, column=week+1, padx=2, pady=2)
                
                # Tooltip
                self.create_tooltip(cell, f"{date_str}\n{count} activities")
        
        # Legend
        legend_frame = tk.Frame(self.calendar_frame, bg=theme["panel_bg"])
        legend_frame.grid(row=9, column=0, columnspan=9, pady=20)
        
        tk.Label(legend_frame, text="Less", bg=theme["panel_bg"], fg=theme["fg"], 
                font=("Arial", 9)).pack(side="left", padx=5)
        
        colors = ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"]
        for color in colors:
            tk.Label(legend_frame, bg=color, width=4, height=1, 
                    relief="solid", borderwidth=1).pack(side="left", padx=2)
        
        tk.Label(legend_frame, text="More", bg=theme["panel_bg"], fg=theme["fg"], 
                font=("Arial", 9)).pack(side="left", padx=5)
        
        # Streak stats
        stats_frame = tk.Frame(self.calendar_frame, bg=theme["panel_bg"])
        stats_frame.grid(row=10, column=0, columnspan=9, pady=20)
        
        current_streak = self.calculate_current_streak()
        longest_streak = self.calculate_longest_streak()
        
        tk.Label(
            stats_frame,
            text=f"🔥 Current Streak: {current_streak} days",
            font=("Arial", 18, "bold"),
            bg=theme["panel_bg"],
            fg="#e74c3c"
        ).pack(pady=5)
        
        tk.Label(
            stats_frame,
            text=f"🏆 Longest Streak: {longest_streak} days",
            font=("Arial", 16),
            bg=theme["panel_bg"],
            fg="#f39c12"
        ).pack(pady=5)
        
        # Motivational message
        if current_streak >= 7:
            msg = "🌟 Amazing! Keep the momentum going!"
        elif current_streak >= 3:
            msg = "💪 Great start! You're building consistency!"
        elif current_streak > 0:
            msg = "🌱 Good! Every day counts!"
        else:
            msg = "🚀 Start your streak today!"
        
        tk.Label(
            stats_frame,
            text=msg,
            font=("Arial", 12),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).pack(pady=10)
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, bg="black", fg="black", 
                           relief="solid", borderwidth=1, font=("Arial", 9), padx=5, pady=3)
            label.pack()
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def calculate_current_streak(self):
        """Calculate current streak"""
        if not self.app.data_manager.habits_data:
            return 0
        
        dates = sorted(set(log['date'] for log in self.app.data_manager.habits_data), reverse=True)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not dates or dates[0] != today:
            return 0
        
        streak = 1
        for i in range(len(dates) - 1):
            date1 = datetime.strptime(dates[i], "%Y-%m-%d")
            date2 = datetime.strptime(dates[i+1], "%Y-%m-%d")
            if (date1 - date2).days == 1:
                streak += 1
            else:
                break
        
        return streak
    
    def calculate_longest_streak(self):
        """Calculate longest streak ever"""
        if not self.app.data_manager.habits_data:
            return 0
        
        dates = sorted(set(log['date'] for log in self.app.data_manager.habits_data))
        if not dates:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(len(dates) - 1):
            date1 = datetime.strptime(dates[i], "%Y-%m-%d")
            date2 = datetime.strptime(dates[i+1], "%Y-%m-%d")
            if (date2 - date1).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    def refresh(self):
        """Refresh the calendar"""
        self.draw_calendar()