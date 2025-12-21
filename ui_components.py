# ui_components.py - Reusable UI components
import tkinter as tk
from tkinter import ttk

class UIComponents:
    """Reusable UI components"""
    
    def __init__(self, root, theme_manager):
        self.root = root
        self.theme_manager = theme_manager
    
    def create_button(self, parent, text, command, bg_color, **kwargs):
        """Create a styled button"""
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=8,
            **kwargs
        )
    
    def create_label_frame(self, parent, title):
        """Create a styled label frame"""
        theme = self.theme_manager.get_theme()
        return tk.LabelFrame(
            parent,
            text=title,
            font=("Arial", 12, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            padx=20,
            pady=20
        )
    
    def create_entry(self, parent, width=30):
        """Create a styled entry"""
        return tk.Entry(
            parent,
            font=("Arial", 11),
            width=width
        )