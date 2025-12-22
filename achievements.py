# achievements.py - Achievement and badge system
from datetime import datetime
from collections import defaultdict

class AchievementSystem:
    """Manages achievements and badges"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        
        # Define all available achievements
        self.all_achievements = {
            "first_log": {
                "name": "Getting Started",
                "description": "Log your first habit",
                "icon": "🌱",
                "points": 10
            },
            "week_streak": {
                "name": "Week Warrior",
                "description": "Maintain a 7-day streak",
                "icon": "🔥",
                "points": 50
            },
            "month_streak": {
                "name": "Monthly Master",
                "description": "Maintain a 30-day streak",
                "icon": "💎",
                "points": 200
            },
            "hundred_activities": {
                "name": "Century Club",
                "description": "Log 100 activities",
                "icon": "💯",
                "points": 100
            },
            "thousand_minutes": {
                "name": "Time Investor",
                "description": "Accumulate 1000 minutes",
                "icon": "⏰",
                "points": 150
            },
            "perfect_day": {
                "name": "Perfect Day",
                "description": "Complete all habits in one day",
                "icon": "⭐",
                "points": 30
            },
            "early_bird": {
                "name": "Early Bird",
                "description": "Log 10 activities before 9 AM",
                "icon": "🌅",
                "points": 75
            },
            "five_habits": {
                "name": "Habit Collector",
                "description": "Create 5 different habits",
                "icon": "📚",
                "points": 50
            },
            "consistency_king": {
                "name": "Consistency King",
                "description": "80%+ completion rate with 50+ logs",
                "icon": "👑",
                "points": 250
            },
            "three_month": {
                "name": "Quarter Champion",
                "description": "Track for 90 days",
                "icon": "🏆",
                "points": 300
            },
            "ten_streak": {
                "name": "Streak Master",
                "description": "Achieve a 10-day streak",
                "icon": "🔥",
                "points": 75
            },
            "meditation_guru": {
                "name": "Meditation Guru",
                "description": "Log 30 meditation sessions",
                "icon": "🧘",
                "points": 100
            },
            "reading_enthusiast": {
                "name": "Reading Enthusiast",
                "description": "Log 30 reading sessions",
                "icon": "📖",
                "points": 100
            },
            "fitness_pro": {
                "name": "Fitness Pro",
                "description": "Log 30 exercise sessions",
                "icon": "💪",
                "points": 100
            },
            "weekend_warrior": {
                "name": "Weekend Warrior",
                "description": "Log activities on 10 weekends",
                "icon": "🎯",
                "points": 80
            }
        }
    
    def check_all_achievements(self):
        """Check all achievements and return newly unlocked ones"""
        unlocked = self.data_manager.achievements.get("unlocked", [])
        new_achievements = []
        
        for achievement_id, achievement in self.all_achievements.items():
            if achievement_id not in unlocked:
                if self.check_achievement(achievement_id):
                    unlocked.append(achievement_id)
                    new_achievements.append(achievement)
                    self.data_manager.achievements["total_points"] += achievement["points"]
        
        self.data_manager.achievements["unlocked"] = unlocked
        self.data_manager.save_json(
            self.data_manager.achievements_file,
            self.data_manager.achievements
        )
        
        return new_achievements
    
    def check_achievement(self, achievement_id):
        """Check if specific achievement is unlocked"""
        data = self.data_manager.habits_data
        habits = self.data_manager.habits_list
        
        if achievement_id == "first_log":
            return len(data) >= 1
        
        elif achievement_id == "week_streak":
            return self.calculate_current_streak() >= 7
        
        elif achievement_id == "month_streak":
            return self.calculate_current_streak() >= 30
        
        elif achievement_id == "ten_streak":
            return self.calculate_current_streak() >= 10
        
        elif achievement_id == "hundred_activities":
            return len(data) >= 100
        
        elif achievement_id == "thousand_minutes":
            return sum(log['duration'] for log in data) >= 1000
        
        elif achievement_id == "perfect_day":
            # Check if any day has all habits completed
            daily_logs = defaultdict(list)
            for log in data:
                if log.get('completed', True):
                    daily_logs[log['date']].append(log['habit'])
            
            for date, logged_habits in daily_logs.items():
                if len(set(logged_habits)) == len(habits):
                    return True
            return False
        
        elif achievement_id == "five_habits":
            return len(habits) >= 5
        
        elif achievement_id == "consistency_king":
            if len(data) >= 50:
                completed = sum(1 for log in data if log.get('completed', True))
                return (completed / len(data)) >= 0.8
            return False
        
        elif achievement_id == "three_month":
            dates = set(log['date'] for log in data)
            return len(dates) >= 90
        
        elif achievement_id == "meditation_guru":
            meditation_logs = [log for log in data if 'meditation' in log['habit'].lower()]
            return len(meditation_logs) >= 30
        
        elif achievement_id == "reading_enthusiast":
            reading_logs = [log for log in data if 'read' in log['habit'].lower()]
            return len(reading_logs) >= 30
        
        elif achievement_id == "fitness_pro":
            fitness_logs = [log for log in data if any(word in log['habit'].lower() 
                           for word in ['exercise', 'workout', 'gym', 'fitness'])]
            return len(fitness_logs) >= 30
        
        elif achievement_id == "weekend_warrior":
            weekend_count = 0
            for log in data:
                log_date = datetime.strptime(log['date'], "%Y-%m-%d")
                if log_date.weekday() in [5, 6]:  # Saturday, Sunday
                    weekend_count += 1
            return weekend_count >= 10
        
        return False
    
    def calculate_current_streak(self):
        """Calculate current streak"""
        if not self.data_manager.habits_data:
            return 0
        
        dates = sorted(set(log['date'] for log in self.data_manager.habits_data), reverse=True)
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
    
    def get_total_points(self):
        """Get total achievement points"""
        return self.data_manager.achievements.get("total_points", 0)
    
    def get_unlocked_achievements(self):
        """Get list of unlocked achievements"""
        unlocked_ids = self.data_manager.achievements.get("unlocked", [])
        return [self.all_achievements[aid] for aid in unlocked_ids if aid in self.all_achievements]
    
    def get_locked_achievements(self):
        """Get list of locked achievements"""
        unlocked_ids = self.data_manager.achievements.get("unlocked", [])
        return [ach for aid, ach in self.all_achievements.items() if aid not in unlocked_ids]