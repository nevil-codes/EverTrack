# analytics.py - Charts and data visualization
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
from datetime import datetime

class Analytics:
    """Handles all analytics and data visualization"""
    
    def __init__(self, data_manager, theme_manager):
        self.data_manager = data_manager
        self.theme_manager = theme_manager
    
    def create_bar_chart(self, ax):
        """Create bar chart showing total time per habit"""
        habit_totals = defaultdict(float)
        for record in self.data_manager.habits_data:
            habit_totals[record["habit"]] += record["duration"]
        
        if not habit_totals:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        habits = list(habit_totals.keys())
        durations = list(habit_totals.values())
        
        colors = plt.cm.Set3(range(len(habits)))
        ax.bar(habits, durations, color=colors, edgecolor='black', linewidth=1.2)
        ax.set_xlabel("Habits", fontsize=10, fontweight='bold')
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight='bold')
        ax.set_title("Total Time Spent Per Habit", fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    
    def create_line_chart(self, ax):
        """Create line chart showing daily progress"""
        daily_totals = defaultdict(float)
        for record in self.data_manager.habits_data:
            daily_totals[record["date"]] += record["duration"]
        
        if not daily_totals:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        dates = sorted(daily_totals.keys())
        durations = [daily_totals[date] for date in dates]
        
        ax.plot(dates, durations, marker='o', linewidth=2, markersize=6, color='#3498db')
        ax.set_xlabel("Date", fontsize=10, fontweight='bold')
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight='bold')
        ax.set_title("Daily Habit Progress", fontsize=12, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    
    def create_pie_chart(self, ax):
        """Create pie chart showing time distribution"""
        habit_totals = defaultdict(float)
        for record in self.data_manager.habits_data:
            habit_totals[record["habit"]] += record["duration"]
        
        if not habit_totals:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        habits = list(habit_totals.keys())
        durations = list(habit_totals.values())
        
        colors = plt.cm.Pastel1(range(len(habits)))
        ax.pie(durations, labels=habits, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title("Time Distribution Across Habits", fontsize=12, fontweight='bold')
        plt.tight_layout()
    
    def create_completion_chart(self, ax):
        """Create completion rate chart"""
        habit_stats = defaultdict(lambda: {"total": 0, "completed": 0})
        
        for record in self.data_manager.habits_data:
            habit_stats[record["habit"]]["total"] += 1
            if record.get("completed", True):
                habit_stats[record["habit"]]["completed"] += 1
        
        if not habit_stats:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        habits = list(habit_stats.keys())
        completion_rates = [
            (habit_stats[h]["completed"] / habit_stats[h]["total"] * 100)
            for h in habits
        ]
        
        colors = ['#27ae60' if rate >= 80 else '#f39c12' if rate >= 50 else '#e74c3c' 
                  for rate in completion_rates]
        
        ax.barh(habits, completion_rates, color=colors, edgecolor='black', linewidth=1.2)
        ax.set_xlabel("Completion Rate (%)", fontsize=10, fontweight='bold')
        ax.set_ylabel("Habits", fontsize=10, fontweight='bold')
        ax.set_title("Habit Completion Rate", fontsize=12, fontweight='bold')
        ax.set_xlim(0, 100)
        plt.tight_layout()
    
    def create_weekly_comparison(self, ax):
        """Create weekly comparison chart"""
        from datetime import timedelta
        
        # Get last 4 weeks
        today = datetime.now()
        weekly_data = defaultdict(float)
        
        for log in self.data_manager.habits_data:
            log_date = datetime.strptime(log['date'], "%Y-%m-%d")
            days_ago = (today - log_date).days
            
            if days_ago <= 28:
                week = f"Week {4 - (days_ago // 7)}"
                weekly_data[week] += log['duration']
        
        if not weekly_data:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return
        
        weeks = list(weekly_data.keys())
        durations = list(weekly_data.values())
        
        ax.bar(weeks, durations, color='#3498db', edgecolor='black', linewidth=1.2)
        ax.set_xlabel("Week", fontsize=10, fontweight='bold')
        ax.set_ylabel("Total Time (minutes)", fontsize=10, fontweight='bold')
        ax.set_title("Last 4 Weeks Comparison", fontsize=12, fontweight='bold')
        plt.tight_layout()