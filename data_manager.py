# data_manager.py - Handles all data operations
import json
import os
from datetime import datetime

class DataManager:
    """Manages all data operations for EverTrack Pro"""
    
    def __init__(self):
        self.data_file = "habits_data.json"
        self.habits_file = "habits_list.json"
        self.settings_file = "settings.json"
        self.achievements_file = "achievements.json"
        
        self.habits_data = self.load_json(self.data_file, [])
        self.habits_list = self.load_json(self.habits_file, [])
        self.settings = self.load_json(self.settings_file, {
            "theme": "light",
            "notifications": True,
            "reminder_times": {}
        })
        self.achievements = self.load_json(self.achievements_file, {
            "unlocked": [],
            "total_points": 0
        })
    
    def load_json(self, filename, default):
        """Load JSON file with error handling"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def save_json(self, filename, data):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving {filename}: {e}")
            return False
    
    def save_all(self):
        """Save all data"""
        self.save_json(self.data_file, self.habits_data)
        self.save_json(self.habits_file, self.habits_list)
        self.save_json(self.settings_file, self.settings)
        self.save_json(self.achievements_file, self.achievements)
    
    def add_habit(self, habit_data):
        """Add a new habit"""
        self.habits_list.append(habit_data)
        self.save_json(self.habits_file, self.habits_list)
    
    def delete_habit(self, habit_name):
        """Delete a habit and its logs"""
        self.habits_list = [h for h in self.habits_list if h['name'] != habit_name]
        self.habits_data = [log for log in self.habits_data if log['habit'] != habit_name]
        self.save_all()
    
    def add_log(self, log_data):
        """Add a new log entry"""
        self.habits_data.append(log_data)
        self.save_json(self.data_file, self.habits_data)
    
    def delete_log(self, date, habit, duration):
        """Delete a specific log"""
        self.habits_data = [
            log for log in self.habits_data
            if not (log['date'] == date and log['habit'] == habit and log['duration'] == duration)
        ]
        self.save_json(self.data_file, self.habits_data)
    
    def get_active_habits(self):
        """Get list of active habits"""
        return [h for h in self.habits_list if h.get('status') == 'Active']
    
    def get_logs_by_date(self, date):
        """Get all logs for a specific date"""
        return [log for log in self.habits_data if log['date'] == date]
    
    def get_logs_by_habit(self, habit_name):
        """Get all logs for a specific habit"""
        return [log for log in self.habits_data if log['habit'] == habit_name]
    
    def export_to_csv(self, filename):
        """Export data to CSV"""
        import csv
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Habit', 'Duration (min)', 'Completed', 'Notes'])
                for log in self.habits_data:
                    writer.writerow([
                        log['date'],
                        log['habit'],
                        log['duration'],
                        'Yes' if log.get('completed', True) else 'No',
                        log.get('notes', '')
                    ])
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False