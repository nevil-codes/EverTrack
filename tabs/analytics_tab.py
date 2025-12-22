# tabs/analytics_tab.py
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AnalyticsTab:
    """Analytics and visualization tab"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()
    
    def create_ui(self):
        """Create the analytics UI"""
        theme = self.app.theme_manager.get_theme()
        
        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Chart buttons
        btn_frame = tk.Frame(container, bg=theme["bg"])
        btn_frame.pack(fill="x", pady=(0, 10))
        
        buttons = [
            ("📊 Bar Chart - Total Time", lambda: self.show_chart("bar"), "#3498db"),
            ("📈 Line Chart - Progress", lambda: self.show_chart("line"), "#9b59b6"),
            ("🥧 Pie Chart - Distribution", lambda: self.show_chart("pie"), "#e67e22"),
            ("✅ Completion Rate", lambda: self.show_chart("completion"), "#27ae60"),
            ("📅 Weekly Comparison", lambda: self.show_chart("weekly"), "#e74c3c"),
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
        
        # Chart display area
        self.chart_frame = tk.Frame(container, bg=theme["panel_bg"], relief="solid", borderwidth=1)
        self.chart_frame.pack(fill="both", expand=True)
        
        # Welcome message
        welcome_label = tk.Label(
            self.chart_frame,
            text="📊\n\nSelect a chart type above\nto visualize your habits!",
            font=("Arial", 16),
            bg=theme["panel_bg"],
            fg="#7f8c8d"
        )
        welcome_label.pack(expand=True)
    
    def show_chart(self, chart_type):
        """Display selected chart"""
        if not self.app.data_manager.habits_data:
            messagebox.showinfo("No Data", "No activities to display. Log some activities first!")
            return
        
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(7, 5), facecolor='white')
        
        if chart_type == "bar":
            self.app.analytics.create_bar_chart(ax)
        elif chart_type == "line":
            self.app.analytics.create_line_chart(ax)
        elif chart_type == "pie":
            self.app.analytics.create_pie_chart(ax)
        elif chart_type == "completion":
            self.app.analytics.create_completion_chart(ax)
        elif chart_type == "weekly":
            self.app.analytics.create_weekly_comparison(ax)
        
        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    
    def refresh(self):
        """Refresh analytics"""
        pass