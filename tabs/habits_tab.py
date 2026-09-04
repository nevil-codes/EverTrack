# tabs/habits_tab.py
import tkinter as tk
from tkinter import messagebox, ttk

from core.dates import InvalidDate, parse_iso, to_iso, today
from core.models import ValidationError


class HabitsTab:
    """Habits management tab"""

    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()

    def create_ui(self):
        """Create the habits tab UI"""
        theme = self.app.theme_manager.get_theme()

        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Left side - Create habit
        left_frame = self.app.ui.create_label_frame(container, "Create New Habit")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # AI Quick Setup
        ai_frame = tk.Frame(left_frame, bg="#e8f4f8", relief="solid", borderwidth=1)
        ai_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15), padx=5)

        tk.Label(
            ai_frame,
            text="⚡ Quick Setup",
            font=("Arial", 10, "bold"),
            bg="#e8f4f8",
            fg="#2c3e50"
        ).pack(pady=(10, 5))

        tk.Label(
            ai_frame,
            text="Describe your goal (e.g., 'I want to read more'):",
            font=("Arial", 9),
            bg="#e8f4f8",
            fg="#34495e"
        ).pack()

        self.ai_goal_entry = tk.Entry(ai_frame, font=("Arial", 10), width=40)
        self.ai_goal_entry.pack(pady=5, padx=10)

        tk.Button(
            ai_frame,
            text="⚡ Suggest a habit",
            command=self.ai_suggest_habit,
            bg="#3498db",
            fg="black",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(pady=(5, 10))

        # Habit Name
        tk.Label(left_frame, text="Habit Name:", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=1, column=0, sticky="w", pady=10)
        self.habit_entry = self.app.ui.create_entry(left_frame)
        self.habit_entry.grid(row=1, column=1, pady=10, padx=10)

        # Start Date
        tk.Label(left_frame, text="Start Date:", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=2, column=0, sticky="w", pady=10)
        start_date_label = tk.Label(
            left_frame,
            text=to_iso(today()),
            font=("Arial", 11, "bold"),
            bg=theme["panel_bg"],
            fg="#27ae60"
        )
        start_date_label.grid(row=2, column=1, pady=10, padx=10, sticky="w")

        # End Date
        tk.Label(left_frame, text="End Date (Optional):", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=3, column=0, sticky="w", pady=10)

        end_frame = tk.Frame(left_frame, bg=theme["panel_bg"])
        end_frame.grid(row=3, column=1, pady=10, padx=10, sticky="w")

        self.no_limit_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            end_frame,
            text="No End Date",
            variable=self.no_limit_var,
            font=("Arial", 9),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).pack(side="left")

        self.end_date_entry = tk.Entry(end_frame, font=("Arial", 10), width=15, state="disabled")
        self.end_date_entry.pack(side="left", padx=(10, 0))

        # Daily Target
        tk.Label(left_frame, text="Daily Target (min):", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=4, column=0, sticky="w", pady=10)
        self.target_entry = self.app.ui.create_entry(left_frame)
        self.target_entry.grid(row=4, column=1, pady=10, padx=10)
        self.target_entry.insert(0, "30")

        # Reminder
        tk.Label(left_frame, text="Reminder Time (HH:MM):", font=("Arial", 10),
                bg=theme["panel_bg"], fg=theme["fg"]).grid(row=5, column=0, sticky="w", pady=10)
        self.reminder_entry = self.app.ui.create_entry(left_frame)
        self.reminder_entry.grid(row=5, column=1, pady=10, padx=10)
        self.reminder_entry.insert(0, "09:00")

        # Create button
        create_btn = self.app.ui.create_button(
            left_frame,
            "Create Habit",
            self.create_habit,
            theme["success"]
        )
        create_btn.grid(row=6, column=0, columnspan=2, pady=20)

        # Right side - Habits list
        right_frame = self.app.ui.create_label_frame(container, "Your Habits")
        right_frame.pack(side="right", fill="both", expand=True)

        scroll_y = tk.Scrollbar(right_frame)
        scroll_y.pack(side="right", fill="y")

        self.habits_table = ttk.Treeview(
            right_frame,
            columns=("Habit", "Start", "End", "Target", "Status"),
            show="headings",
            yscrollcommand=scroll_y.set,
            height=15
        )
        scroll_y.config(command=self.habits_table.yview)

        for col in ["Habit", "Start", "End", "Target", "Status"]:
            self.habits_table.heading(col, text=col)

        self.habits_table.column("Habit", width=180)
        self.habits_table.column("Start", width=100)
        self.habits_table.column("End", width=100)
        self.habits_table.column("Target", width=100)
        self.habits_table.column("Status", width=100)

        self.habits_table.pack(fill="both", expand=True, pady=(0, 10))

        delete_btn = self.app.ui.create_button(
            right_frame,
            "Delete Selected",
            self.delete_habit,
            theme["danger"]
        )
        delete_btn.pack(pady=5)

    def ai_suggest_habit(self):
        """Fill the form from a keyword-matched habit suggestion"""
        goal = self.ai_goal_entry.get().strip()
        if not goal:
            messagebox.showwarning("Input Required", "Please describe your goal!")
            return

        suggestion = self.app.ai_coach.suggest_habit(goal)

        self.habit_entry.delete(0, tk.END)
        self.habit_entry.insert(0, suggestion['name'])
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, str(suggestion['target']))

        messagebox.showinfo(
            "Suggested Habit",
            f"✨ Based on your goal:\n\n"
            f"Habit: {suggestion['name']}\n"
            f"Target: {suggestion['target']} min\n"
            f"Tip: {suggestion['tip']}"
        )

    def create_habit(self):
        """Create a new habit from the form."""
        habit_name = self.habit_entry.get().strip()
        if not habit_name:
            messagebox.showwarning("Error", "Please enter a habit name!")
            return

        try:
            target = int(self.target_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Daily target must be a whole number of minutes!")
            return

        end_date = "No Limit"
        if not self.no_limit_var.get():
            end_date = self.end_date_entry.get().strip()
            if not end_date:
                messagebox.showwarning("Error", "Enter an end date, or tick 'No End Date'!")
                return
            try:
                parse_iso(end_date)
            except InvalidDate:
                messagebox.showerror("Error", "End date must be in YYYY-MM-DD format!")
                return

        reminder_time = self.reminder_entry.get().strip()

        try:
            self.app.data_manager.add_habit({
                "name": habit_name,
                "start_date": to_iso(today()),
                "end_date": end_date,
                "daily_target": target,
                "status": "Active",
            })
            if reminder_time:
                self.app.data_manager.set_reminder(habit_name, reminder_time)
        except ValidationError as exc:
            messagebox.showerror("Could not create habit", str(exc))
            return

        self.app.check_achievements()
        self.refresh()
        self.app.log_tab.refresh()

        messagebox.showinfo("Success", f"Habit '{habit_name}' created!")

        self.habit_entry.delete(0, tk.END)
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, "30")
        self.reminder_entry.delete(0, tk.END)
        self.reminder_entry.insert(0, "09:00")

    def delete_habit(self):
        """Delete selected habit"""
        selected = self.habits_table.selection()
        if not selected:
            messagebox.showwarning("Error", "Please select a habit!")
            return

        if messagebox.askyesno("Confirm", "Delete this habit and all its logs?"):
            item = self.habits_table.item(selected[0])
            habit_name = item["values"][0]

            self.app.data_manager.delete_habit(habit_name)
            self.refresh()
            self.app.log_tab.refresh()

            messagebox.showinfo("Success", "Habit deleted!")

    def refresh(self):
        """Refresh the habits table"""
        self.habits_table.delete(*self.habits_table.get_children())

        for habit in self.app.data_manager.habits_list:
            self.habits_table.insert("", "end", values=(
                habit.get("name", "—"),
                habit.get("start_date", "—"),
                habit.get("end_date", "No Limit"),
                f"{habit.get('daily_target', '—')} min",
                habit.get("status", "Active")
            ))
