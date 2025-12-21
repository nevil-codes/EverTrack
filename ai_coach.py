# ai_coach.py - AI features and NLP
import re
from collections import defaultdict

class AICoach:
    """AI Coach for habit suggestions and natural language processing"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def suggest_habit(self, goal):
        """Suggest habit based on goal"""
        goal_lower = goal.lower()
        
        suggestions = {
            'read': {'name': 'Reading', 'target': 30, 'tip': 'Start with 30 minutes daily'},
            'exercise': {'name': 'Exercise', 'target': 45, 'tip': 'Consistency beats intensity'},
            'meditate': {'name': 'Meditation', 'target': 15, 'tip': 'Even 10-15 minutes helps'},
            'code': {'name': 'Coding Practice', 'target': 60, 'tip': 'Daily practice builds skills'},
            'write': {'name': 'Writing', 'target': 20, 'tip': 'Write freely without judgment'},
            'learn': {'name': 'Learning', 'target': 45, 'tip': 'Focus on understanding'},
        }
        
        for keyword, suggestion in suggestions.items():
            if keyword in goal_lower:
                return suggestion
        
        return {'name': goal.title(), 'target': 30, 'tip': 'Start small and be consistent'}
    
    def parse_natural_language(self, text):
        """Parse natural language input"""
        text_lower = text.lower()
        
        # Extract duration
        duration = None
        minutes_pattern = re.search(r'(\d+)\s*(minute|minutes|min|mins)', text_lower)
        if minutes_pattern:
            duration = int(minutes_pattern.group(1))
        
        hour_pattern = re.search(r'(\d+|an|one)\s*hour', text_lower)
        if hour_pattern and not duration:
            hour_text = hour_pattern.group(1)
            duration = 60 if hour_text in ['an', 'one'] else int(hour_text) * 60
        
        if not duration:
            return None
        
        # Extract habit
        habits = {
            'meditate': 'Meditation', 'meditation': 'Meditation',
            'exercise': 'Exercise', 'workout': 'Exercise',
            'read': 'Reading', 'reading': 'Reading',
            'code': 'Coding', 'coding': 'Coding',
            'write': 'Writing', 'writing': 'Writing',
            'study': 'Studying', 'yoga': 'Yoga',
            'run': 'Running', 'walk': 'Walking',
        }
        
        for keyword, habit in habits.items():
            if keyword in text_lower:
                return {'habit': habit, 'duration': duration}
        
        return None
    
    def analyze_progress(self):
        """Generate progress analysis"""
        data = self.data_manager.habits_data
        
        if not data:
            return "No data to analyze yet!"
        
        total_logs = len(data)
        total_time = sum(log['duration'] for log in data)
        completed = sum(1 for log in data if log.get('completed', True))
        completion_rate = (completed / total_logs * 100) if total_logs > 0 else 0
        
        analysis = f"""📊 Progress Analysis

Total Activities: {total_logs}
Total Time: {total_time:.0f} minutes ({total_time/60:.1f} hours)
Completion Rate: {completion_rate:.1f}%

"""
        
        if completion_rate >= 80:
            analysis += "✨ Excellent! You're crushing it!"
        elif completion_rate >= 60:
            analysis += "👍 Good progress!"
        else:
            analysis += "💪 Keep pushing!"
        
        return analysis