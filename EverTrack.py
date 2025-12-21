import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

class EverTrack:
    def __init__(self, root):
        self.root = root
        self.root.title("EverTrack - Smart Habit Tracking")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # Data file path
        self.data_file = "habits_data.json"
        self.habits_data = self.load_data()
        
        # Create main container
        self.create_ui()
        self.refresh_table()
        
    def load_data(self):
        """Load habit data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_data(self):
        """Save habit data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.habits_data, f, indent=4)
    
    def create_ui(self):
        """Create the main user interface"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="EverTrack", 
            font=("Arial", 28, "bold"),
            bg="#2c3e50",
            fg="black"
        )
        title_label.pack(pady=20)
        
        # Main content area
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Input and Table
        left_panel = tk.Frame(content_frame, bg="#f0f0f0")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Input Section
        input_frame = tk.LabelFrame(
            left_panel, 
            text="Add New Habit", 
            font=("Arial", 12, "bold"),
            bg="white",
            padx=20,
            pady=20
        )
        input_frame.pack(fill="x", pady=(0, 20))
        
        # Habit Name
        tk.Label(input_frame, text="Habit Name:", font=("Arial", 10), bg="white", fg="black").grid(row=0, column=0, sticky="w", pady=5)
        self.habit_entry = tk.Entry(input_frame, font=("Arial", 10), width=30)
        self.habit_entry.grid(row=0, column=1, pady=5, padx=10)
        
        # Duration
        tk.Label(input_frame, text="Duration (minutes):", font=("Arial", 10), bg="white", fg="black").grid(row=1, column=0, sticky="w", pady=5)
        self.duration_entry = tk.Entry(input_frame, font=("Arial", 10), width=30)
        self.duration_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Add Button
        add_btn = tk.Button(
            input_frame,
            text="Add Habit",
            command=self.add_habit,
            bg="#27ae60",
            fg="black",
            font=("Arial", 11, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        )
        add_btn.grid(row=2, column=0, columnspan=2, pady=15)
        
        # Table Section
        table_frame = tk.LabelFrame(
            left_panel,
            text="Habit History",
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
        self.table = ttk.Treeview(
            table_frame,
            columns=("Date", "Habit", "Duration"),
            show="headings",
            yscrollcommand=scroll_y.set,
            height=15
        )
        scroll_y.config(command=self.table.yview)
        
        # Define columns
        self.table.heading("Date", text="Date")
        self.table.heading("Habit", text="Habit Name")
        self.table.heading("Duration", text="Duration (min)")
        
        self.table.column("Date", width=120, anchor="center")
        self.table.column("Habit", width=200, anchor="w")
        self.table.column("Duration", width=120, anchor="center")
        
        self.table.pack(fill="both", expand=True)
        
        # Delete Button
        delete_btn = tk.Button(
            left_panel,
            text="Delete Selected",
            command=self.delete_habit,
            bg="#e74c3c",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=5
        )
        delete_btn.pack(pady=10)
        
        # Right panel - Charts
        right_panel = tk.Frame(content_frame, bg="#f0f0f0", width=400)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Chart buttons
        btn_frame = tk.Frame(right_panel, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(0, 10))
        
        tk.Button(
            btn_frame,
            text="Bar Chart",
            command=lambda: self.show_chart("bar"),
            bg="#3498db",
            fg="black",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Line Chart",
            command=lambda: self.show_chart("line"),
            bg="#9b59b6",
            fg="black",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Pie Chart",
            command=lambda: self.show_chart("pie"),
            bg="#e67e22",
            fg="black",
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(side="left", padx=5)
        
        # Chart display area
        self.chart_frame = tk.Frame(right_panel, bg="white", relief="solid", borderwidth=1)
        self.chart_frame.pack(fill="both", expand=True)
        
        # Welcome message
        welcome_label = tk.Label(
            self.chart_frame,
            text="📊\n\nSelect a chart type above\nto visualize your habits!",
            font=("Arial", 14),
            bg="white",
            fg="black"
        )
        welcome_label.pack(expand=True)
    
    def add_habit(self):
        """Add a new habit entry"""
        habit_name = self.habit_entry.get().strip()
        duration = self.duration_entry.get().strip()
        
        if not habit_name or not duration:
            messagebox.showwarning("Input Error", "Please fill in all fields!")
            return
        
        try:
            duration = float(duration)
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Duration must be a positive number!")
            return
        
        # Create habit record
        habit_record = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "habit": habit_name,
            "duration": duration
        }
        
        self.habits_data.append(habit_record)
        self.save_data()
        self.refresh_table()
        
        # Clear inputs
        self.habit_entry.delete(0, tk.END)
        self.duration_entry.delete(0, tk.END)
        
        messagebox.showinfo("Success", f"Habit '{habit_name}' added successfully!")
    
    def refresh_table(self):
        """Refresh the table with current data"""
        # Clear existing rows
        for item in self.table.get_children():
            self.table.delete(item)
        
        # Add data
        for record in reversed(self.habits_data):
            self.table.insert("", "end", values=(
                record["date"],
                record["habit"],
                f"{record['duration']:.0f}"
            ))
    
    def delete_habit(self):
        """Delete selected habit entry"""
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a habit to delete!")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this habit?"):
            item = self.table.item(selected[0])
            values = item["values"]
            
            # Find and remove from data
            for i, record in enumerate(self.habits_data):
                if (record["date"] == values[0] and 
                    record["habit"] == values[1] and 
                    record["duration"] == float(values[2])):
                    del self.habits_data[i]
                    break
            
            self.save_data()
            self.refresh_table()
            messagebox.showinfo("Deleted", "Habit deleted successfully!")
    
    def show_chart(self, chart_type):
        """Display the selected chart type"""
        if not self.habits_data:
            messagebox.showinfo("No Data", "No habits to display. Add some habits first!")
            return
        
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(5, 4), facecolor='white')
        
        if chart_type == "bar":
            self.create_bar_chart(ax)
        elif chart_type == "line":
            self.create_line_chart(ax)
        elif chart_type == "pie":
            self.create_pie_chart(ax)
        
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

def main():
    root = tk.Tk()
    app = EverTrack(root)
    root.mainloop()

if __name__ == "__main__":
    main()