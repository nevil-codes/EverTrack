# tabs/log_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class LogTab:
    """Daily log tab with plain-English quick entry"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()
    
    def create_ui(self):
        """Create the log tab UI"""
        theme = self.app.theme_manager.get_theme()
        
        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel
        left_panel = tk.Frame(container, bg=theme["bg"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # AI Natural Language Input
        ai_frame = tk.LabelFrame(
            left_panel,
            text="⌨️ Quick Entry (plain English)",
            font=("Arial", 12, "bold"),
            bg="#e8f4f8",
            padx=20,
            pady=15
        )
        ai_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(
            ai_frame,
            text="Just type naturally! Examples:",
            font=("Arial", 9, "bold"),
            bg="#e8f4f8",
            fg="#2c3e50"
        ).pack(anchor="w")
        
        tk.Label(
            ai_frame,
            text="• 'I meditated for 30 minutes'\n• 'Did 45 mins of exercise today'\n• 'Read for an hour'",
            font=("Arial", 8),
            bg="#e8f4f8",
            fg="#34495e",
            justify="left"
        ).pack(anchor="w", pady=(2, 10))
        
        self.nl_entry = tk.Entry(ai_frame, font=("Arial", 11), width=50)
        self.nl_entry.pack(fill="x", pady=5)
        self.nl_entry.bind('<Return>', lambda e: self.parse_and_log())
        
        tk.Button(
            ai_frame,
            text="⌨️ Parse & Log",
            command=self.parse_and_log,
            bg="#9b59b6",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(pady=5)
        
        # Traditional Input
        input_frame = self.app.ui.create_label_frame(left_panel, "Traditional Log Entry")
        input_frame.pack(fill="x", pady=(0, 20))
        
        # Habit selection
        tk.Label(input_frame, text="Select Habit:", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=0, column=0, sticky="w", pady=10)
        self.habit_combo = ttk.Combobox(input_frame, font=("Arial", 10), width=28, state="readonly")
        self.habit_combo.grid(row=0, column=1, pady=10, padx=10)
        self.update_habit_combo()
        
        # Duration
        tk.Label(input_frame, text="Duration (minutes):", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="w", pady=10)
        self.duration_entry = self.app.ui.create_entry(input_frame)
        self.duration_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Notes
        tk.Label(input_frame, text="Notes (Optional):", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=2, column=0, sticky="w", pady=10)
        self.notes_entry = self.app.ui.create_entry(input_frame)
        self.notes_entry.grid(row=2, column=1, pady=10, padx=10)
        
        # Completed checkbox
        tk.Label(input_frame, text="Completed Today:", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=3, column=0, sticky="w", pady=10)
        self.completed_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            input_frame,
            text="Yes, I completed this habit today",
            variable=self.completed_var,
            font=("Arial", 10),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).grid(row=3, column=1, pady=10, padx=10, sticky="w")
        
        # Log button
        log_btn = self.app.ui.create_button(
            input_frame,
            "Log Activity",
            self.add_log,
            theme["accent"]
        )
        log_btn.grid(row=4, column=0, columnspan=2, pady=15)
        
        # Activity history table
        table_frame = self.app.ui.create_label_frame(left_panel, "Activity History")
        table_frame.pack(fill="both", expand=True)
        
        scroll_y = tk.Scrollbar(table_frame)
        scroll_y.pack(side="right", fill="y")
        
        self.log_table = ttk.Treeview(
            table_frame,
            columns=("Date", "Habit", "Duration", "Completed"),
            show="headings",
            yscrollcommand=scroll_y.set,
            height=10
        )
        scroll_y.config(command=self.log_table.yview)
        
        for col in ["Date", "Habit", "Duration", "Completed"]:
            self.log_table.heading(col, text=col)
        
        self.log_table.column("Date", width=120, anchor="center")
        self.log_table.column("Habit", width=180, anchor="w")
        self.log_table.column("Duration", width=100, anchor="center")
        self.log_table.column("Completed", width=100, anchor="center")
        
        self.log_table.pack(fill="both", expand=True)
        
        # Delete button
        delete_btn = self.app.ui.create_button(
            left_panel,
            "Delete Selected Log",
            self.delete_log,
            theme["danger"]
        )
        delete_btn.pack(pady=10)
        
        # Right panel - Today's summary
        right_panel = self.app.ui.create_label_frame(container, "Today's Summary")
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.summary_text = tk.Text(
            right_panel,
            font=("Arial", 11),
            bg="#f9f9f9",
            fg="#2c3e50",
            relief="flat",
            wrap="word",
            height=25
        )
        self.summary_text.pack(fill="both", expand=True)
        self.update_summary()
    
    def parse_and_log(self):
        """Parse natural language and log activity"""
        text = self.nl_entry.get().strip()
        if not text:
            messagebox.showwarning("Error", "Please type your activity!")
            return
        
        parsed = self.app.ai_coach.parse_natural_language(text)
        
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
        habit_exists = any(h['name'].lower() == parsed['habit'].lower() 
                          for h in self.app.data_manager.habits_list)
        
        if not habit_exists:
            create = messagebox.askyesno(
                "Create Habit?",
                f"The habit '{parsed['habit']}' doesn't exist.\n\n"
                f"Would you like to create it now?"
            )
            if create:
                habit_data = {
                    "name": parsed['habit'],
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": "No Limit",
                    "daily_target": 30,
                    "status": "Active"
                }
                self.app.data_manager.add_habit(habit_data)
                self.update_habit_combo()
                self.app.habits_tab.refresh()
            else:
                return
        
        # Log the activity
        log_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "habit": parsed['habit'],
            "duration": parsed['duration'],
            "completed": True,
            "notes": ""
        }
        
        self.app.data_manager.add_log(log_data)
        self.app.check_achievements()
        self.refresh()
        
        self.nl_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"✓ Logged: {parsed['habit']} - {parsed['duration']} minutes!")
    
    def add_log(self):
        """Add a log entry manually"""
        if not self.app.data_manager.habits_list:
            messagebox.showwarning("Error", "Please create a habit first!")
            return
        
        habit = self.habit_combo.get()
        duration = self.duration_entry.get().strip()
        notes = self.notes_entry.get().strip()
        completed = self.completed_var.get()
        
        if not habit:
            messagebox.showwarning("Error", "Please select a habit!")
            return
        
        if not duration:
            messagebox.showwarning("Error", "Please enter duration!")
            return
        
        try:
            duration = float(duration)
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Duration must be a positive number!")
            return
        
        log_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "habit": habit,
            "duration": duration,
            "completed": completed,
            "notes": notes
        }
        
        self.app.data_manager.add_log(log_data)
        self.app.check_achievements()
        self.refresh()
        
        # Clear inputs
        self.duration_entry.delete(0, tk.END)
        self.notes_entry.delete(0, tk.END)
        self.completed_var.set(True)
        
        messagebox.showinfo("Success", f"Activity logged for '{habit}'!")
    
    def delete_log(self):
        """Delete selected log"""
        selected = self.log_table.selection()
        if not selected:
            messagebox.showwarning("Error", "Please select a log!")
            return
        
        if messagebox.askyesno("Confirm", "Delete this log?"):
            item = self.log_table.item(selected[0])
            values = item["values"]
            
            self.app.data_manager.delete_log(
                values[0],  # date
                values[1],  # habit
                float(values[2])  # duration
            )
            self.refresh()
            messagebox.showinfo("Success", "Log deleted!")
    
    def update_habit_combo(self):
        """Update habit dropdown"""
        habits = [h['name'] for h in self.app.data_manager.get_active_habits()]
        self.habit_combo['values'] = habits
        if habits:
            self.habit_combo.current(0)
    
    def update_summary(self):
        """Update today's summary"""
        self.summary_text.delete(1.0, tk.END)
        today = datetime.now().strftime("%Y-%m-%d")
        
        today_logs = self.app.data_manager.get_logs_by_date(today)
        
        if not today_logs:
            self.summary_text.insert(1.0, f"📅 {today}\n\nNo activities logged today.\nStart tracking your habits!")
            return
        
        summary = f"📅 {today}\n\n"
        summary += f"Total Activities: {len(today_logs)}\n\n"
        
        total_time = sum(log["duration"] for log in today_logs)
        summary += f"⏱️ Total Time: {total_time:.0f} minutes ({total_time/60:.1f} hours)\n\n"
        
        completed_count = sum(1 for log in today_logs if log.get("completed", True))
        summary += f"✓ Completed: {completed_count}/{len(today_logs)}\n\n"
        
        summary += "━━━━━━━━━━━━━━━━━━━\n\n"
        summary += "📋 Today's Habits:\n\n"
        
        for log in today_logs:
            status = "✓" if log.get("completed", True) else "✗"
            summary += f"{status} {log['habit']}: {log['duration']:.0f} min"
            if log.get('notes'):
                summary += f"\n   📝 {log['notes']}"
            summary += "\n"
        
        self.summary_text.insert(1.0, summary)
    
    def refresh(self):
        """Refresh the log table and summary"""
        self.log_table.delete(*self.log_table.get_children())
        
        for log in reversed(self.app.data_manager.habits_data):
            completed_text = "✓ Yes" if log.get("completed", True) else "✗ No"
            self.log_table.insert("", "end", values=(
                log["date"],
                log["habit"],
                f"{log['duration']:.0f}",
                completed_text
            ))
        
        self.update_summary()