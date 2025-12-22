import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import re

class EverTrack:
    def __init__(self, root):
        self.root = root
        self.root.title("EverTrack - AI-Powered Smart Habit Tracking")
        self.root.geometry("1200x750")
        self.root.configure(bg="#f0f0f0")
        
        # Data files
        self.data_file = "habits_data.json"
        self.habits_file = "habits_list.json"
        self.habits_data = self.load_data()
        self.habits_list = self.load_habits()
        
        # Create main container with notebook
        self.create_ui()
        self.refresh_log_table()
        self.refresh_habits_table()
        
    def load_data(self):
        """Load habit log data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def load_habits(self):
        """Load habits list from JSON file"""
        if os.path.exists(self.habits_file):
            try:
                with open(self.habits_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_data(self):
        """Save habit log data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.habits_data, f, indent=4)
    
    def save_habits(self):
        """Save habits list to JSON file"""
        with open(self.habits_file, 'w') as f:
            json.dump(self.habits_list, f, indent=4)
    
    def create_ui(self):
        """Create the main user interface"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="EverTrack 🤖 AI-Powered", 
            font=("Arial", 28, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create tabs
        self.create_habits_tab()
        self.create_log_tab()
        self.create_ai_coach_tab()
        self.create_analytics_tab()
    
    def create_habits_tab(self):
        """Create the habits management tab"""
        habits_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(habits_tab, text="📋 Manage Habits")
        
        # Main container
        container = tk.Frame(habits_tab, bg="#f0f0f0")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left side - Add habit with AI assistant
        left_frame = tk.LabelFrame(
            container,
            text="Create New Habit (AI-Assisted)",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # AI Quick Setup
        ai_frame = tk.Frame(left_frame, bg="#e8f4f8", relief="solid", borderwidth=1)
        ai_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)
        
        tk.Label(
            ai_frame,
            text="🤖 AI Quick Setup",
            font=("Arial", 10, "bold"),
            bg="#e8f4f8",
            fg="#2c3e50"
        ).pack(pady=(10, 5))
        
        tk.Label(
            ai_frame,
            text="Tell AI your goal (e.g., 'I want to read more books'):",
            font=("Arial", 9),
            bg="#e8f4f8",
            fg="#34495e"
        ).pack()
        
        self.ai_goal_entry = tk.Entry(ai_frame, font=("Arial", 10), width=40)
        self.ai_goal_entry.pack(pady=5, padx=10)
        
        tk.Button(
            ai_frame,
            text="🤖 Get AI Suggestions",
            command=self.ai_suggest_habit,
            bg="#3498db",
            fg="black",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(pady=(5, 10))
        
        # Habit Name
        tk.Label(left_frame, text="Habit Name:", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=10)
        self.new_habit_entry = tk.Entry(left_frame, font=("Arial", 11), width=30)
        self.new_habit_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Start Date (auto-filled with current date)
        tk.Label(left_frame, text="Start Date:", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=10)
        self.start_date_label = tk.Label(
            left_frame,
            text=datetime.now().strftime("%Y-%m-%d"),
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#27ae60"
        )
        self.start_date_label.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        
        # End Date (optional)
        tk.Label(left_frame, text="End Date (Optional):", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=3, column=0, sticky="w", pady=10)
        
        end_date_frame = tk.Frame(left_frame, bg="white")
        end_date_frame.grid(row=3, column=1, pady=10, padx=10, sticky="w")
        
        self.no_limit_var = tk.BooleanVar(value=True)
        self.no_limit_check = tk.Checkbutton(
            end_date_frame,
            text="No End Date",
            variable=self.no_limit_var,
            command=self.toggle_end_date,
            font=("Arial", 9),
            bg="white"
        )
        self.no_limit_check.pack(side="left")
        
        self.end_date_entry = tk.Entry(end_date_frame, font=("Arial", 10), width=15, state="disabled")
        self.end_date_entry.pack(side="left", padx=(10, 0))
        tk.Label(end_date_frame, text="(YYYY-MM-DD)", font=("Arial", 8), bg="white", fg="#7f8c8d").pack(side="left", padx=5)
        
        # Target per day (optional)
        tk.Label(left_frame, text="Daily Target (min):", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=4, column=0, sticky="w", pady=10)
        self.target_entry = tk.Entry(left_frame, font=("Arial", 11), width=30)
        self.target_entry.grid(row=4, column=1, pady=10, padx=10)
        self.target_entry.insert(0, "30")
        
        # Add Button
        add_btn = tk.Button(
            left_frame,
            text="Create Habit",
            command=self.create_habit,
            bg="#27ae60",
            fg="black",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            padx=30,
            pady=10
        )
        add_btn.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Right side - Habits list
        right_frame = tk.LabelFrame(
            container,
            text="Your Habits",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        right_frame.pack(side="right", fill="both", expand=True)
        
        # Scrollbar
        scroll_y = tk.Scrollbar(right_frame)
        scroll_y.pack(side="right", fill="y")
        
        # Habits Table
        self.habits_table = ttk.Treeview(
            right_frame,
            columns=("Habit", "Start", "End", "Target", "Status"),
            show="headings",
            yscrollcommand=scroll_y.set,
            height=15
        )
        scroll_y.config(command=self.habits_table.yview)
        
        self.habits_table.heading("Habit", text="Habit Name")
        self.habits_table.heading("Start", text="Start Date")
        self.habits_table.heading("End", text="End Date")
        self.habits_table.heading("Target", text="Daily Target")
        self.habits_table.heading("Status", text="Status")
        
        self.habits_table.column("Habit", width=180, anchor="w")
        self.habits_table.column("Start", width=100, anchor="center")
        self.habits_table.column("End", width=100, anchor="center")
        self.habits_table.column("Target", width=100, anchor="center")
        self.habits_table.column("Status", width=100, anchor="center")
        
        self.habits_table.pack(fill="both", expand=True, pady=(0, 10))
        
        # Delete Button
        delete_habit_btn = tk.Button(
            right_frame,
            text="Delete Selected Habit",
            command=self.delete_habit,
            bg="#e74c3c",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        )
        delete_habit_btn.pack(pady=5)
    
    def create_log_tab(self):
        """Create the daily log tab with AI natural language input"""
        log_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(log_tab, text="✓ Daily Log")
        
        # Main container
        container = tk.Frame(log_tab, bg="#f0f0f0")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Input
        left_panel = tk.Frame(container, bg="#f0f0f0")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # AI Natural Language Input Section
        ai_input_frame = tk.LabelFrame(
            left_panel,
            text="🤖 AI Natural Language Input",
            font=("Arial", 12, "bold"),
            bg="#e8f4f8",
            padx=20,
            pady=15
        )
        ai_input_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            ai_input_frame,
            text="Just type naturally! Examples:",
            font=("Arial", 9, "bold"),
            bg="#e8f4f8",
            fg="#2c3e50"
        ).pack(anchor="w")
        
        tk.Label(
            ai_input_frame,
            text="• 'I meditated for 30 minutes'\n• 'Did 45 mins of exercise today'\n• 'Read for an hour'",
            font=("Arial", 8),
            bg="#e8f4f8",
            fg="#34495e",
            justify="left"
        ).pack(anchor="w", pady=(2, 10))
        
        self.nl_input_entry = tk.Entry(ai_input_frame, font=("Arial", 11), width=45)
        self.nl_input_entry.pack(fill="x", pady=5)
        self.nl_input_entry.bind('<Return>', lambda e: self.ai_parse_input())
        
        tk.Button(
            ai_input_frame,
            text="🤖 Parse & Log",
            command=self.ai_parse_input,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(pady=5)
        
        # Traditional Input Section
        input_frame = tk.LabelFrame(
            left_panel, 
            text="Traditional Log Entry", 
            font=("Arial", 12, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        input_frame.pack(fill="x", pady=(0, 20))
        
        # Habit Selection (Dropdown)
        tk.Label(input_frame, text="Select Habit:", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=0, column=0, sticky="w", pady=10)
        self.habit_combo = ttk.Combobox(input_frame, font=("Arial", 10), width=28, state="readonly")
        self.habit_combo.grid(row=0, column=1, pady=10, padx=10)
        self.update_habit_combo()
        
        # Duration
        tk.Label(input_frame, text="Duration (minutes):", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=1, column=0, sticky="w", pady=10)
        self.duration_entry = tk.Entry(input_frame, font=("Arial", 10), width=30)
        self.duration_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Completion status
        tk.Label(input_frame, text="Completed Today:", font=("Arial", 10), bg="white", fg="#2c3e50").grid(row=2, column=0, sticky="w", pady=10)
        self.completed_var = tk.BooleanVar(value=True)
        completion_check = tk.Checkbutton(
            input_frame,
            text="Yes, I completed this habit today",
            variable=self.completed_var,
            font=("Arial", 10),
            bg="white"
        )
        completion_check.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        
        # Add Button
        log_btn = tk.Button(
            input_frame,
            text="Log Activity",
            command=self.add_log,
            bg="#3498db",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        )
        log_btn.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Table Section
        table_frame = tk.LabelFrame(
            left_panel,
            text="Activity History",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        table_frame.pack(fill="both", expand=True)
        
        # Scrollbar
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side="right", fill="y")
        
        # Treeview (Table)
        self.log_table = ttk.Treeview(
            table_frame,
            columns=("Date", "Habit", "Duration", "Completed"),
            show="headings",
            yscrollcommand=scroll_y.set,
            height=10
        )
        scroll_y.config(command=self.log_table.yview)
        
        self.log_table.heading("Date", text="Date")
        self.log_table.heading("Habit", text="Habit Name")
        self.log_table.heading("Duration", text="Duration (min)")
        self.log_table.heading("Completed", text="Completed")
        
        self.log_table.column("Date", width=120, anchor="center")
        self.log_table.column("Habit", width=180, anchor="w")
        self.log_table.column("Duration", width=100, anchor="center")
        self.log_table.column("Completed", width=100, anchor="center")
        
        self.log_table.pack(fill="both", expand=True)
        
        # Delete Button
        delete_log_btn = tk.Button(
            left_panel,
            text="Delete Selected Log",
            command=self.delete_log,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        )
        delete_log_btn.pack(pady=10)
        
        # Right panel - Today's summary
        right_panel = tk.LabelFrame(
            container,
            text="Today's Summary",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.summary_text = tk.Text(
            right_panel,
            font=("Arial", 11),
            bg="#f9f9f9",
            fg="#2c3e50",
            relief="flat",
            wrap="word",
            height=20
        )
        self.summary_text.pack(fill="both", expand=True)
        self.update_daily_summary()
    
    def create_ai_coach_tab(self):
        """Create the AI Coach tab"""
        ai_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(ai_tab, text="🤖 AI Coach")
        
        container = tk.Frame(ai_tab, bg="#f0f0f0")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(container, bg="#8e44ad", height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🤖 Your Personal AI Habit Coach",
            font=("Arial", 18, "bold"),
            bg="#8e44ad",
            fg="white"
        ).pack(pady=15)
        
        # Action buttons
        btn_frame = tk.Frame(container, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(
            btn_frame,
            text="📊 Analyze My Progress",
            command=self.ai_analyze_progress,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="💡 Get Recommendations",
            command=self.ai_get_recommendations,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="🎯 Optimize My Targets",
            command=self.ai_optimize_targets,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="💪 Get Motivation",
            command=self.ai_get_motivation,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        # AI Response area
        response_frame = tk.LabelFrame(
            container,
            text="AI Insights",
            font=("Arial", 12, "bold"),
            bg="white",
            padx=15,
            pady=15
        )
        response_frame.pack(fill="both", expand=True)
        
        # Scrolled text for AI response
        self.ai_response_text = scrolledtext.ScrolledText(
            response_frame,
            font=("Arial", 11),
            bg="#f9f9f9",
            fg="#2c3e50",
            wrap="word",
            relief="flat"
        )
        self.ai_response_text.pack(fill="both", expand=True)
        
        # Welcome message
        welcome_msg = """👋 Welcome to Your AI Habit Coach!

I'm here to help you build better habits and reach your goals. Here's what I can do for you:

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
        self.ai_response_text.insert(1.0, welcome_msg)
        self.ai_response_text.config(state="disabled")
        
        # Custom query section
        query_frame = tk.Frame(container, bg="#f0f0f0")
        query_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(
            query_frame,
            text="Ask me anything:",
            font=("Arial", 10, "bold"),
            bg="#f0f0f0",
            fg="#2c3e50"
        ).pack(side="left", padx=(0, 10))
        
        self.ai_query_entry = tk.Entry(query_frame, font=("Arial", 10), width=60)
        self.ai_query_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.ai_query_entry.bind('<Return>', lambda e: self.ai_custom_query())
        
        tk.Button(
            query_frame,
            text="Ask AI",
            command=self.ai_custom_query,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=5
        ).pack(side="left", padx=5)
    
    def create_analytics_tab(self):
        """Create the analytics tab"""
        analytics_tab = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(analytics_tab, text="📊 Analytics")
        
        container = tk.Frame(analytics_tab, bg="#f0f0f0")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Chart buttons
        btn_frame = tk.Frame(container, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(
            btn_frame,
            text="Bar Chart - Total Time",
            command=lambda: self.show_chart("bar"),
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Line Chart - Progress",
            command=lambda: self.show_chart("line"),
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Pie Chart - Distribution",
            command=lambda: self.show_chart("pie"),
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Completion Rate",
            command=lambda: self.show_chart("completion"),
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side="left", padx=5)
        
        # Chart display area
        self.chart_frame = tk.Frame(container, bg="white", relief="solid", borderwidth=1)
        self.chart_frame.pack(fill="both", expand=True)
        
        # Welcome message
        welcome_label = tk.Label(
            self.chart_frame,
            text="📊\n\nSelect a chart type above\nto visualize your habits!",
            font=("Arial", 14),
            bg="white",
            fg="#7f8c8d"
        )
        welcome_label.pack(expand=True)
    
    # AI Functions
    def ai_suggest_habit(self):
        """AI suggests habit setup based on user goal"""
        goal = self.ai_goal_entry.get().strip()
        if not goal:
            messagebox.showwarning("Input Required", "Please describe your goal!")
            return
        
        # Simulate AI processing
        self.show_ai_processing("Analyzing your goal...")
        
        # Simple rule-based AI (you can replace with actual Claude API)
        suggestions = self.generate_habit_suggestions(goal)
        
        if suggestions:
            self.new_habit_entry.delete(0, tk.END)
            self.new_habit_entry.insert(0, suggestions['name'])
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, str(suggestions['target']))
            
            messagebox.showinfo(
                "AI Suggestion",
                f"✨ Based on your goal, I suggest:\n\n"
                f"Habit: {suggestions['name']}\n"
                f"Daily Target: {suggestions['target']} minutes\n"
                f"Tip: {suggestions['tip']}"
            )
    
    def generate_habit_suggestions(self, goal):
        """Generate habit suggestions based on goal keywords"""
        goal_lower = goal.lower()
        
        # Keyword-based suggestions
        if any(word in goal_lower for word in ['read', 'book', 'reading']):
            return {'name': 'Reading', 'target': 30, 'tip': 'Start with 30 minutes daily and gradually increase'}
        elif any(word in goal_lower for word in ['exercise', 'workout', 'fitness', 'gym']):
            return {'name': 'Exercise', 'target': 45, 'tip': 'Consistency beats intensity - start moderate'}
        elif any(word in goal_lower for word in ['meditate', 'meditation', 'mindful']):
            return {'name': 'Meditation', 'target': 15, 'tip': 'Even 10-15 minutes daily makes a huge difference'}
        elif any(word in goal_lower for word in ['code', 'coding', 'program']):
            return {'name': 'Coding Practice', 'target': 60, 'tip': 'Daily practice builds strong programming skills'}
        elif any(word in goal_lower for word in ['write', 'writing', 'journal']):
            return {'name': 'Writing', 'target': 20, 'tip': 'Write freely without judgment to build the habit'}
        elif any(word in goal_lower for word in ['learn', 'study', 'course']):
            return {'name': 'Learning', 'target': 45, 'tip': 'Focus on understanding, not just completion'}
        else:
            return {'name': goal.title(), 'target': 30, 'tip': 'Start small and be consistent'}
    
    def ai_parse_input(self):
        """AI parses natural language input and logs habit"""
        nl_text = self.nl_input_entry.get().strip()
        if not nl_text:
            messagebox.showwarning("Input Required", "Please type your activity!")
            return
        
        # Parse the input
        parsed = self.parse_natural_language(nl_text)
        
        if not parsed:
            messagebox.showerror(
                "Parsing Failed",
                "I couldn't understand that. Try:\n"
                "• 'I meditated for 30 minutes'\n"
                "• 'Did 45 mins of exercise'\n"
                "• 'Read for an hour'"
            )
            return
        
        # Check if habit exists
        habit_exists = any(h['name'].lower() == parsed['habit'].lower() for h in self.habits_list)
        
        if not habit_exists:
            # Ask to create habit
            create = messagebox.askyesno(
                "Create New Habit?",
                f"The habit '{parsed['habit']}' doesn't exist yet.\n\n"
                f"Would you like to create it now?"
            )
            if create:
                # Create habit automatically
                habit_record = {
                    "name": parsed['habit'],
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": "No Limit",
                    "daily_target": 30,
                    "status": "Active"
                }
                self.habits_list.append(habit_record)
                self.save_habits()
                self.refresh_habits_table()
                self.update_habit_combo()
            else:
                return
        
        # Log the activity
        log_record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "habit": parsed['habit'],
            "duration": parsed['duration'],
            "completed": True
        }
        
        self.habits_data.append(log_record)
        self.save_data()
        self.refresh_log_table()
        self.update_daily_summary()
        
        self.nl_input_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"✓ Logged: {parsed['habit']} - {parsed['duration']} minutes!")
    
    def parse_natural_language(self, text):
        """Parse natural language input to extract habit and duration"""
        text_lower = text.lower()
        
        # Extract duration
        duration = None
        
        # Look for patterns like "30 minutes", "30 mins", "30min"
        minutes_pattern = re.search(r'(\d+)\s*(minute|minutes|min|mins)', text_lower)
        if minutes_pattern:
            duration = int(minutes_pattern.group(1))
        
        # Look for "an hour", "1 hour", "2 hours"
        hour_pattern = re.search(r'(\d+|an|one)\s*hour', text_lower)
        if hour_pattern and not duration:
            hour_text = hour_pattern.group(1)
            if hour_text in ['an', 'one']:
                duration = 60
            else:
                duration = int(hour_text) * 60
        
        if not duration:
            return None
        
        # Extract habit name (common activities)
        habits = {
            'meditate': 'Meditation',
            'meditation': 'Meditation',
            'exercise': 'Exercise',
            'workout': 'Exercise',
            'read': 'Reading',
            'reading': 'Reading',
            'code': 'Coding',
            'coding': 'Coding',
            'write': 'Writing',
            'writing': 'Writing',
            'study': 'Studying',
            'studying': 'Studying',
            'practice': 'Practice',
            'learn': 'Learning',
            'yoga': 'Yoga',
            'run': 'Running',
            'running': 'Running',
            'walk': 'Walking',
            'walking': 'Walking',
        }
        
        habit_name = None
        for keyword, habit in habits.items():
            if keyword in text_lower:
                habit_name = habit
                break
        
        if not habit_name:
            # Try to extract from common patterns
            for word in text_lower.split():
                if word.endswith('ing'):
                    habit_name = word.capitalize()
                    break
        
        if habit_name and duration:
            return {'habit': habit_name, 'duration': duration}
        
        return None
    
    def ai_analyze_progress(self):
        """AI analyzes user's progress"""
        if not self.habits_data:
            self.update_ai_response("📊 No data to analyze yet!\n\nStart logging your habits and I'll provide detailed insights about your progress.")
            return
        
        self.update_ai_response("🤖 Analyzing your habit data...\n\n")
        
        # Calculate statistics
        total_logs = len(self.habits_data)
        total_time = sum(log['duration'] for log in self.habits_data)
        completed_count = sum(1 for log in self.habits_data if log.get('completed', True))
        completion_rate = (completed_count / total_logs * 100) if total_logs > 0 else 0
        
        # Get date range
        dates = [log['date'] for log in self.habits_data]
        unique_dates = len(set(dates))
        
        # Most practiced habit
        habit_counts = defaultdict(int)
        for log in self.habits_data:
            habit_counts[log['habit']] += 1
        most_practiced = max(habit_counts.items(), key=lambda x: x[1]) if habit_counts else ("None", 0)
        
        # Generate analysis
        analysis = f"""📊 Your Habit Analysis Report
{'='*50}

📈 Overall Statistics:
   • Total Activities Logged: {total_logs}
   • Total Time Invested: {total_time:.0f} minutes ({total_time/60:.1f} hours)
   • Active Days: {unique_dates}
   • Completion Rate: {completion_rate:.1f}%

🏆 Top Habit:
   • {most_practiced[0]} ({most_practiced[1]} times)

💡 Insights:
"""
        
        if completion_rate >= 80:
            analysis += "   ✨ Excellent! You're crushing it with {:.0f}% completion!\n".format(completion_rate)
        elif completion_rate >= 60:
            analysis += "   👍 Good progress! You're completing most of your habits.\n"
        else:
            analysis += "   💪 Keep pushing! Try to be more consistent.\n"
        
        if unique_dates >= 7:
            analysis += "   🔥 Great streak! You've been active for {} days!\n".format(unique_dates)
        else:
            analysis += "   📅 Try to track daily for better results.\n"
        
        if total_time >= 1000:
            analysis += "   ⏰ Wow! Over {:.1f} hours invested in self-improvement!\n".format(total_time/60)
        
        analysis += "\n🎯 Recommendations:\n"
        
        if completion_rate < 70:
            analysis += "   • Focus on consistency over perfection\n"
            analysis += "   • Start with just 1-2 core habits\n"
        
        if unique_dates < 7:
            analysis += "   • Try to log something every day\n"
            analysis += "   • Even 5 minutes counts!\n"
        
        analysis += "   • Review your progress weekly\n"
        analysis += "   • Celebrate small wins!\n"
        
        self.update_ai_response(analysis)
    
    def ai_get_recommendations(self):
        """AI provides habit recommendations"""
        recommendations = """💡 Personalized Habit Recommendations
{'='*50}

Based on proven habit-building research:

🌅 Morning Habits (High Impact):
   • Meditation (10-15 min) - Improves focus and reduces stress
   • Exercise (20-30 min) - Boosts energy and mood
   • Reading (15-20 min) - Expands knowledge and vocabulary
   • Journaling (10 min) - Increases self-awareness

🎯 Skill Building:
   • Coding Practice (30-60 min) - Daily practice builds expertise
   • Language Learning (20-30 min) - Consistent exposure is key
   • Drawing/Art (30 min) - Develops creative thinking
   • Writing (20-30 min) - Improves communication skills

💪 Health & Wellness:
   • Yoga (20-30 min) - Flexibility and mindfulness
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
        self.update_ai_response(recommendations)
    
    def ai_optimize_targets(self):
        """AI suggests optimal targets based on performance"""
        if not self.habits_data:
            self.update_ai_response("🎯 No data available yet!\n\nLog some activities first, and I'll analyze your performance to suggest optimal targets.")
            return
        
        # Calculate average performance per habit
        habit_performance = defaultdict(list)
        for log in self.habits_data:
            habit_performance[log['habit']].append(log['duration'])
        
        optimization = """🎯 Target Optimization Report
{'='*50}

Based on your actual performance, here are optimized targets:

"""
        
        for habit, durations in habit_performance.items():
            avg = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Find current target
            current_target = 30
            for h in self.habits_list:
                if h['name'] == habit:
                    current_target = h['daily_target']
                    break
            
            # Suggest optimal target (slightly above average)
            optimal = int(avg * 1.2)
            
            optimization += f"\n📌 {habit}:\n"
            optimization += f"   Current Target: {current_target} min\n"
            optimization += f"   Your Average: {avg:.0f} min\n"
            optimization += f"   Range: {min_duration:.0f} - {max_duration:.0f} min\n"
            optimization += f"   🎯 Suggested Target: {optimal} min\n"
            
            if avg > current_target:
                optimization += f"   ✨ You're exceeding your target! Consider increasing it.\n"
            elif avg < current_target * 0.8:
                optimization += f"   💡 Target might be too high. Lower it for better consistency.\n"
            else:
                optimization += f"   ✓ Your target is well-calibrated!\n"
        
        optimization += "\n💡 General Advice:\n"
        optimization += "   • Targets should be challenging but achievable\n"
        optimization += "   • It's better to hit 80% consistently than 100% occasionally\n"
        optimization += "   • Adjust targets monthly based on progress\n"
        optimization += "   • Life changes - your targets should too!\n"
        
        self.update_ai_response(optimization)
    
    def ai_get_motivation(self):
        """AI provides motivational message"""
        if not self.habits_data:
            motivation = """💪 Welcome to Your Habit Journey!

Every expert was once a beginner. You're taking the first step today, and that's what matters most!

Remember:
✓ Small daily improvements lead to stunning results
✓ You don't have to be great to start, but you have to start to be great
✓ The best time to start was yesterday. The second best time is now.

🚀 Ready to build amazing habits? Let's do this!
"""
        else:
            total_logs = len(self.habits_data)
            total_time = sum(log['duration'] for log in self.habits_data)
            dates = set(log['date'] for log in self.habits_data)
            
            motivation = f"""💪 You're Making Amazing Progress!

🏆 Your Achievements:
   • {total_logs} activities logged
   • {total_time/60:.1f} hours invested in yourself
   • {len(dates)} days of tracking

✨ Keep Going! Here's Why:

"""
            
            if len(dates) >= 7:
                motivation += "🔥 You've built a 7-day streak! The habit is forming!\n\n"
            
            if total_time >= 1000:
                motivation += "⭐ Over 1000 minutes invested! You're in the top 10% of habit trackers!\n\n"
            
            motivation += """💡 Remember:
   • Every day you show up, you're rewiring your brain
   • Consistency beats intensity every time
   • You're not just building habits, you're building your future self

🎯 Today's Challenge:
   Pick ONE habit and do it for just 5 minutes right now!
   
🌟 You've got this! I believe in you!
"""
        
        self.update_ai_response(motivation)
    
    def ai_custom_query(self):
        """Handle custom AI queries"""
        query = self.ai_query_entry.get().strip()
        if not query:
            return
        
        self.update_ai_response(f"❓ Your Question: {query}\n\n🤖 Processing...\n\n")
        
        # Simple keyword-based responses
        query_lower = query.lower()
        
        if 'streak' in query_lower or 'consistent' in query_lower:
            response = """🔥 Building Consistency & Streaks:

1. Start Micro: Do just 1 minute if you must - consistency matters more than duration
2. Never Miss Twice: Missing one day is okay, missing two is a pattern
3. Track Visually: Use a calendar and mark completed days with ✓
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
   • Post-lunch energy dip - light activities

🌙 Evening (6-9 PM):
   • Creative work, Journaling
   • Wind-down activities

🎯 The BEST time is: When you'll actually do it consistently!
"""
        elif 'many' in query_lower or 'how much' in query_lower:
            response = """📊 How Many Habits?

Recommended: 1-3 core habits at a time

Why?
• Focus beats spreading thin
• Better to master one than fail at ten
• Each habit takes mental energy

Strategy:
1. Start with 1 keystone habit (e.g., exercise)
2. After 21-30 days, add another
3. Build slowly and sustainably

Quality > Quantity!
"""
        else:
            response = f"""I'd love to help with: "{query}"

For the best experience, try asking about:
• Consistency and streaks
• Staying motivated
• Best times for habits
• How many habits to track
• Specific habit advice

Or use the buttons above for detailed insights!
"""
        
        self.update_ai_response(response)
        self.ai_query_entry.delete(0, tk.END)
    
    def update_ai_response(self, text):
        """Update AI response text area"""
        self.ai_response_text.config(state="normal")
        self.ai_response_text.delete(1.0, tk.END)
        self.ai_response_text.insert(1.0, text)
        self.ai_response_text.config(state="disabled")
    
    def show_ai_processing(self, message):
        """Show AI processing message"""
        processing_window = tk.Toplevel(self.root)
        processing_window.title("AI Processing")
        processing_window.geometry("300x100")
        processing_window.configure(bg="white")
        
        tk.Label(
            processing_window,
            text=message,
            font=("Arial", 11),
            bg="white",
            fg="#2c3e50"
        ).pack(expand=True)
        
        processing_window.after(1000, processing_window.destroy)
    
    # Original functions
    def toggle_end_date(self):
        """Toggle end date entry based on checkbox"""
        if self.no_limit_var.get():
            self.end_date_entry.config(state="disabled")
        else:
            self.end_date_entry.config(state="normal")
    
    def update_habit_combo(self):
        """Update the habit dropdown in log tab"""
        habit_names = [h["name"] for h in self.habits_list if h["status"] == "Active"]
        self.habit_combo['values'] = habit_names
        if habit_names:
            self.habit_combo.current(0)
    
    def create_habit(self):
        """Create a new habit"""
        habit_name = self.new_habit_entry.get().strip()
        
        if not habit_name:
            messagebox.showwarning("Input Error", "Please enter a habit name!")
            return
        
        # Check if habit already exists
        if any(h["name"].lower() == habit_name.lower() for h in self.habits_list):
            messagebox.showerror("Duplicate Habit", "This habit already exists!")
            return
        
        start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Handle end date
        if self.no_limit_var.get():
            end_date = "No Limit"
        else:
            end_date = self.end_date_entry.get().strip()
            if end_date:
                try:
                    datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Invalid Date", "End date must be in YYYY-MM-DD format!")
                    return
            else:
                messagebox.showwarning("Input Error", "Please enter an end date or check 'No End Date'!")
                return
        
        # Handle target
        target = self.target_entry.get().strip()
        try:
            target_val = int(target) if target else 0
        except ValueError:
            messagebox.showerror("Invalid Target", "Daily target must be a number!")
            return
        
        # Create habit record
        habit_record = {
            "name": habit_name,
            "start_date": start_date,
            "end_date": end_date,
            "daily_target": target_val,
            "status": "Active"
        }
        
        self.habits_list.append(habit_record)
        self.save_habits()
        self.refresh_habits_table()
        self.update_habit_combo()
        
        # Clear inputs
        self.new_habit_entry.delete(0, tk.END)
        self.end_date_entry.delete(0, tk.END)
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, "30")
        self.no_limit_var.set(True)
        self.toggle_end_date()
        
        messagebox.showinfo("Success", f"Habit '{habit_name}' created successfully!")
    
    def delete_habit(self):
        """Delete selected habit"""
        selected = self.habits_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a habit to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this habit?\n\nThis will also delete all associated logs!"):
            item = self.habits_table.item(selected[0])
            habit_name = item["values"][0]
            
            # Remove from habits list
            self.habits_list = [h for h in self.habits_list if h["name"] != habit_name]
            
            # Remove associated logs
            self.habits_data = [log for log in self.habits_data if log["habit"] != habit_name]
            
            self.save_habits()
            self.save_data()
            self.refresh_habits_table()
            self.refresh_log_table()
            self.update_habit_combo()
            self.update_daily_summary()
            
            messagebox.showinfo("Deleted", f"Habit '{habit_name}' and all its logs have been deleted!")
    
    def add_log(self):
        """Add a new activity log"""
        if not self.habits_list:
            messagebox.showwarning("No Habits", "Please create a habit first in the 'Manage Habits' tab!")
            return
        
        habit_name = self.habit_combo.get()
        duration = self.duration_entry.get().strip()
        completed = self.completed_var.get()
        
        if not habit_name:
            messagebox.showwarning("Input Error", "Please select a habit!")
            return
        
        if not duration:
            messagebox.showwarning("Input Error", "Please enter duration!")
            return
        
        try:
            duration = float(duration)
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Duration must be a positive number!")
            return
        
        # Create log record
        log_record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "habit": habit_name,
            "duration": duration,
            "completed": completed
        }
        
        self.habits_data.append(log_record)
        self.save_data()
        self.refresh_log_table()
        self.update_daily_summary()
        
        # Clear inputs
        self.duration_entry.delete(0, tk.END)
        self.completed_var.set(True)
        
        messagebox.showinfo("Success", f"Activity logged for '{habit_name}'!")
    
    def delete_log(self):
        """Delete selected log entry"""
        selected = self.log_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a log to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this log?"):
            item = self.log_table.item(selected[0])
            values = item["values"]
            
            # Find and remove from data
            for i, record in enumerate(self.habits_data):
                if (record["date"] == values[0] and 
                    record["habit"] == values[1] and 
                    record["duration"] == float(values[2])):
                    del self.habits_data[i]
                    break
            
            self.save_data()
            self.refresh_log_table()
            self.update_daily_summary()
            messagebox.showinfo("Deleted", "Log deleted successfully!")
    
    def refresh_habits_table(self):
        """Refresh the habits table"""
        for item in self.habits_table.get_children():
            self.habits_table.delete(item)
        
        for habit in self.habits_list:
            self.habits_table.insert("", "end", values=(
                habit["name"],
                habit["start_date"],
                habit["end_date"],
                f"{habit['daily_target']} min",
                habit["status"]
            ))
    
    def refresh_log_table(self):
        """Refresh the log table"""
        for item in self.log_table.get_children():
            self.log_table.delete(item)
        
        for record in reversed(self.habits_data):
            completed_text = "✓ Yes" if record.get("completed", True) else "✗ No"
            self.log_table.insert("", "end", values=(
                record["date"],
                record["habit"],
                f"{record['duration']:.0f}",
                completed_text
            ))
    
    def update_daily_summary(self):
        """Update today's summary"""
        self.summary_text.delete(1.0, tk.END)
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_logs = [log for log in self.habits_data if log["date"] == today]
        
        if not today_logs:
            self.summary_text.insert(1.0, f"📅 {today}\n\n" + "No activities logged today.\nStart tracking your habits!")
            return
        
        summary = f"📅 {today}\n\n"
        summary += f"Total Activities: {len(today_logs)}\n\n"
        
        total_time = sum(log["duration"] for log in today_logs)
        summary += f"⏱️ Total Time: {total_time:.0f} minutes\n\n"
        
        completed_count = sum(1 for log in today_logs if log.get("completed", True))
        summary += f"✓ Completed: {completed_count}/{len(today_logs)}\n\n"
        
        summary += "━━━━━━━━━━━━━━━━━━━\n\n"
        summary += "📋 Today's Habits:\n\n"
        
        for log in today_logs:
            status = "✓" if log.get("completed", True) else "✗"
            summary += f"{status} {log['habit']}: {log['duration']:.0f} min\n"
        
        self.summary_text.insert(1.0, summary)
    
    def show_chart(self, chart_type):
        """Display the selected chart type"""
        if not self.habits_data:
            messagebox.showinfo("No Data", "No activities to display. Log some activities first!")
            return
        
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4.5), facecolor='white')
        
        if chart_type == "bar":
            self.create_bar_chart(ax)
        elif chart_type == "line":
            self.create_line_chart(ax)
        elif chart_type == "pie":
            self.create_pie_chart(ax)
        elif chart_type == "completion":
            self.create_completion_chart(ax)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_bar_chart(self, ax):
        """Create bar chart showing total time per habit"""
        habit_totals = defaultdict(float)
        for record in self.habits_data:
            habit_totals[record["habit"]] += record["duration"]
        
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
        for record in self.habits_data:
            daily_totals[record["date"]] += record["duration"]
        
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
        for record in self.habits_data:
            habit_totals[record["habit"]] += record["duration"]
        
        habits = list(habit_totals.keys())
        durations = list(habit_totals.values())
        
        colors = plt.cm.Pastel1(range(len(habits)))
        ax.pie(durations, labels=habits, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.set_title("Time Distribution Across Habits", fontsize=12, fontweight='bold')
        plt.tight_layout()
    
    def create_completion_chart(self, ax):
        """Create completion rate chart"""
        habit_stats = defaultdict(lambda: {"total": 0, "completed": 0})
        
        for record in self.habits_data:
            habit_stats[record["habit"]]["total"] += 1
            if record.get("completed", True):
                habit_stats[record["habit"]]["completed"] += 1
        
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

def main():
    root = tk.Tk()
    app = EverTrack(root)
    root.mainloop()

if __name__ == "__main__":
    main()