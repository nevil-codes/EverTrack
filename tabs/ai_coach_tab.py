# tabs/ai_coach_tab.py
import tkinter as tk
from tkinter import scrolledtext

from core import stats


class AICoachTab:
    """Rule-based coach tab: rolled-up stats and static habit guidance"""

    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()

    def create_ui(self):
        """Create the AI coach UI"""
        theme = self.app.theme_manager.get_theme()

        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg="#8e44ad", height=70)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🧭 Your Habit Coach",
            font=("Arial", 20, "bold"),
            bg="#8e44ad",
            fg="black"
        ).pack(pady=18)

        # Action buttons
        btn_frame = tk.Frame(container, bg=theme["bg"])
        btn_frame.pack(fill="x", pady=(0, 10))

        buttons = [
            ("📊 Analyze Progress", self.analyze_progress, "#3498db"),
            ("💡 Get Recommendations", self.get_recommendations, "#27ae60"),
            ("🎯 Optimize Targets", self.optimize_targets, "#e67e22"),
            ("💪 Get Motivation", self.get_motivation, "#e74c3c"),
        ]

        for text, command, color in buttons:
            tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=color,
                fg="black",
                font=("Arial", 10, "bold"),
                cursor="hand2",
                padx=15,
                pady=8
            ).pack(side="left", padx=5)

        # AI Response area
        response_frame = tk.LabelFrame(
            container,
            text="Insights",
            font=("Arial", 12, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            padx=15,
            pady=15
        )
        response_frame.pack(fill="both", expand=True)

        self.ai_response = scrolledtext.ScrolledText(
            response_frame,
            font=("Arial", 11),
            bg="#f9f9f9",
            fg="#2c3e50",
            wrap="word",
            relief="flat"
        )
        self.ai_response.pack(fill="both", expand=True)

        # Welcome message
        self.show_welcome_message()

        # Custom query
        query_frame = tk.Frame(container, bg=theme["bg"])
        query_frame.pack(fill="x", pady=(10, 0))

        tk.Label(
            query_frame,
            text="Ask me anything:",
            font=("Arial", 10, "bold"),
            bg=theme["bg"],
            fg=theme["fg"]
        ).pack(side="left", padx=(0, 10))

        self.query_entry = tk.Entry(query_frame, font=("Arial", 10), width=60)
        self.query_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.query_entry.bind('<Return>', lambda e: self.custom_query())

        tk.Button(
            query_frame,
            text="Ask",
            command=self.custom_query,
            bg="#9b59b6",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=5
        ).pack(side="left", padx=5)

    def show_welcome_message(self):
        """Show welcome message"""
        welcome = """👋 Welcome to Your Habit Coach!

I'm here to help you build better habits and reach your goals. Here's what I can do:

📊 Analyze My Progress
   • Get detailed insights into your habit patterns
   • Understand your strengths and areas for improvement
   • See personalized statistics and trends

💡 Get Recommendations
   • Discover new habits that complement your current routine
   • Get suggestions based on your goals and patterns
   • Find the optimal time to practice your habits

🎯 Optimize My Targets
   • Adjust your daily targets based on your performance
   • Get realistic and achievable goal suggestions
   • Balance your habit routine for sustainable growth

💪 Get Motivation
   • Receive personalized encouragement
   • Celebrate your achievements
   • Get tips to overcome challenges

Click any button above to get started! I'll analyze your data and provide personalized insights.
"""
        self.update_response(welcome)

    def analyze_progress(self):
        """Show rolled-up statistics for everything logged so far."""
        logs = self.app.data_manager.log_models()

        if not logs:
            self.update_response(
                "📊 No data to analyze yet!\n\nStart logging your habits and I'll summarise them here."
            )
            return

        summary = stats.totals(logs)
        top = stats.most_practiced(logs)

        analysis = f"""📊 Your Habit Analysis Report
{"=" * 60}

📈 Overall Statistics:
   • Total Activities Logged: {summary.activities}
   • Total Time Invested: {summary.total_minutes:.0f} minutes ({summary.total_hours:.1f} hours)
   • Active Days: {summary.active_days}
   • Completion Rate: {summary.completion_rate:.1f}%

🏆 Top Habit:
   • {top[0]} ({top[1]} times)

💡 Insights:
"""

        if summary.completion_rate >= 80:
            analysis += f"   ✨ Excellent! You're crushing it with {summary.completion_rate:.0f}% completion!\n"
        elif summary.completion_rate >= 60:
            analysis += "   👍 Good progress! You're completing most of your habits.\n"
        else:
            analysis += "   💪 Keep pushing! Try to be more consistent.\n"

        if summary.active_days >= 7:
            analysis += f"   🔥 You've been active on {summary.active_days} different days!\n"
        else:
            analysis += "   📅 Try to track daily for better results.\n"

        if summary.total_minutes >= 1000:
            analysis += f"   ⏰ Over {summary.total_hours:.1f} hours invested in self-improvement!\n"

        analysis += "\n🎯 Recommendations:\n"
        if summary.completion_rate < 70:
            analysis += "   • Focus on consistency over perfection\n"
            analysis += "   • Start with just 1-2 core habits\n"
        if summary.active_days < 7:
            analysis += "   • Try to log something every day\n"
            analysis += "   • Even 5 minutes counts!\n"
        analysis += "   • Review your progress weekly\n"
        analysis += "   • Celebrate small wins!\n"

        self.update_response(analysis)

    def get_recommendations(self):
        """Get habit recommendations"""
        recommendations = """💡 Personalized Habit Recommendations
============================================================

Based on proven habit-building research:

🌅 Morning Habits (High Impact):
   • Meditation (10-15 min) - Improves focus and reduces stress
   • Exercise (20-30 min) - Boosts energy and mood all day
   • Reading (15-20 min) - Expands knowledge and vocabulary
   • Journaling (10 min) - Increases self-awareness

🎯 Skill Building:
   • Coding Practice (30-60 min) - Daily practice builds expertise
   • Language Learning (20-30 min) - Consistent exposure is key
   • Drawing/Art (30 min) - Develops creative thinking
   • Writing (20-30 min) - Improves communication skills

💪 Health & Wellness:
   • Yoga (20-30 min) - Flexibility and mindfulness combined
   • Walking (30 min) - Low impact, high benefit
   • Stretching (10-15 min) - Prevents injury and stiffness
   • Healthy Cooking (30 min) - Better nutrition control

🧠 Evening Habits:
   • Gratitude Practice (5 min) - Improves mental health
   • Planning Tomorrow (10 min) - Reduces morning stress
   • Light Reading (20 min) - Better than screen time
   • Reflection (10 min) - Track what went well

💡 Pro Tips:
   ✓ Stack habits: Attach new habits to existing routines
   ✓ Start small: 5 minutes is better than 0 minutes
   ✓ Track consistently: What gets measured gets improved
   ✓ Be patient: It takes 21-66 days to form a habit
   ✓ Focus on systems, not goals

🎯 Suggested Combinations:
   Morning: Meditation → Exercise → Reading
   Evening: Journaling → Gratitude → Planning

Which habits interest you most? I can help you set them up!
"""
        self.update_response(recommendations)

    def optimize_targets(self):
        """Optimize habit targets"""
        logs = self.app.data_manager.log_models()
        habits = self.app.data_manager.habit_models()

        if not logs:
            self.update_response("🎯 No data available yet!\n\nLog some activities first, and I'll summarise your performance.")
            return

        from collections import defaultdict

        habit_performance = defaultdict(list)
        for log in logs:
            habit_performance[log.habit].append(log.duration_min)

        optimization = """🎯 Target Optimization Report
============================================================

Based on your actual performance, here are optimized targets:

"""

        for habit_name, durations in habit_performance.items():
            avg = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            current_target = 30
            for habit in habits:
                if habit.name == habit_name:
                    current_target = habit.daily_target_min
                    break

            optimal = int(avg * 1.2)

            optimization += f"\n📌 {habit_name}:\n"
            optimization += f"   Current Target: {current_target} min\n"
            optimization += f"   Your Average: {avg:.0f} min\n"
            optimization += f"   Range: {min_duration:.0f} - {max_duration:.0f} min\n"
            optimization += f"   🎯 Suggested Target: {optimal} min\n"

            if avg > current_target:
                optimization += "   ✨ You're exceeding your target! Consider increasing it.\n"
            elif avg < current_target * 0.8:
                optimization += "   💡 Target might be too high. Lower it for better consistency.\n"
            else:
                optimization += "   ✓ Your target is well-calibrated!\n"

        optimization += "\n💡 General Advice:\n"
        optimization += "   • Targets should be challenging but achievable\n"
        optimization += "   • It's better to hit 80% consistently than 100% occasionally\n"
        optimization += "   • Adjust targets monthly based on progress\n"
        optimization += "   • Life changes - your targets should too!\n"

        self.update_response(optimization)

    def get_motivation(self):
        """Get motivational message"""
        logs = self.app.data_manager.log_models()

        if not logs:
            motivation = """💪 Welcome to Your Habit Journey!

Every expert was once a beginner. You're taking the first step today, and that's what matters most!

Remember:
✓ Small daily improvements lead to stunning results
✓ You don't have to be great to start, but you have to start to be great
✓ The best time to start was yesterday. The second best time is now.

🚀 Ready to build amazing habits? Let's do this!
"""
        else:
            summary = stats.totals(logs)
            total_logs = summary.activities
            total_time = summary.total_minutes
            dates = {log.log_date for log in logs}

            motivation = f"""💪 You're Making Amazing Progress!

🏆 Your Achievements:
   • {total_logs} activities logged
   • {total_time/60:.1f} hours invested in yourself
   • {len(dates)} days of tracking

✨ Keep Going! Here's Why:

"""

            if len(dates) >= 7:
                motivation += "🔥 Seven or more days tracked! The habit is forming!\n\n"

            if total_time >= 1000:
                motivation += "⭐ Over 1000 minutes invested! You're in the top 10%!\n\n"

            motivation += """💡 Remember:
   • Every day you show up, you're rewiring your brain
   • Consistency beats intensity every time
   • You're not just building habits, you're building your future self

🎯 Today's Challenge:
   Pick ONE habit and do it for just 5 minutes right now!

🌟 You've got this! I believe in you!
"""

        self.update_response(motivation)

    def custom_query(self):
        """Handle custom AI queries"""
        query = self.query_entry.get().strip()
        if not query:
            return

        query_lower = query.lower()

        if 'streak' in query_lower or 'consistent' in query_lower:
            response = """🔥 Building Consistency & Streaks:

1. Start Micro: Do just 1 minute if you must - consistency matters more
2. Never Miss Twice: Missing one day is okay, missing two is a pattern
3. Track Visually: Use the calendar and mark completed days
4. Prepare the Night Before: Set up everything you need
5. Habit Stack: Attach to existing routine (e.g., "After coffee, I meditate")

Your streak builds momentum - protect it!
"""
        elif 'motivat' in query_lower or 'stuck' in query_lower:
            response = """💪 Staying Motivated:

When motivation fades, rely on systems:

1. Make it Easy: Remove friction (e.g., gym clothes ready)
2. Make it Obvious: Visual cues everywhere
3. Make it Attractive: Pair with something you enjoy
4. Make it Satisfying: Track and celebrate small wins

Remember: You don't need motivation, you need discipline and systems!
"""
        elif 'time' in query_lower or 'when' in query_lower:
            response = """⏰ Best Times for Habits:

🌅 Morning (6-9 AM):
   • Meditation, Exercise, Reading
   • Your willpower is highest!

🌞 Midday (12-2 PM):
   • Learning, Skill practice
   • Light activities work best

🌙 Evening (6-9 PM):
   • Creative work, Journaling
   • Wind-down activities

🎯 The BEST time is: When you'll actually do it consistently!
"""
        elif 'many' in query_lower or 'how much' in query_lower:
            response = """📊 How Many Habits?

Recommended: 1-3 core habits at a time

Why?
- Focus beats spreading thin
- Better to master one than fail at ten
- Each habit takes mental energy

Strategy:
1. Start with 1 keystone habit (e.g., exercise)
2. After 21-30 days, add another
3. Build slowly and sustainably

Quality > Quantity!
"""
        else:
            response = f"""I'd love to help with: "{query}"

For the best experience, try asking about:
- Consistency and streaks
- Staying motivated
- Best times for habits
- How many habits to track
- Specific habit advice

Or use the buttons above for detailed insights!
"""

        self.update_response(response)
        self.query_entry.delete(0, tk.END)

    def update_response(self, text):
        """Update AI response text"""
        self.ai_response.config(state="normal")
        self.ai_response.delete(1.0, tk.END)
        self.ai_response.insert(1.0, text)
        self.ai_response.config(state="disabled")

    def refresh(self):
        """Refresh the AI coach tab"""
        pass
