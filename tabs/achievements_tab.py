# tabs/achievements_tab.py
import tkinter as tk
from tkinter import ttk


class AchievementsTab:
    """Achievements and badges tab"""

    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()

    def create_ui(self):
        """Create the achievements UI"""
        theme = self.app.theme_manager.get_theme()

        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg="#f39c12", height=80)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        points = self.app.achievement_system.get_total_points()

        tk.Label(
            header,
            text="🏆 Achievements & Badges",
            font=("Arial", 24, "bold"),
            bg="#f39c12",
            fg="black"
        ).pack(side="left", padx=30, pady=20)

        tk.Label(
            header,
            text=f"Total Points: {points}",
            font=("Arial", 18, "bold"),
            bg="#f39c12",
            fg="black"
        ).pack(side="right", padx=30)

        # Create scrollable canvas
        canvas = tk.Canvas(container, bg=theme["bg"])
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=theme["bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Unlocked achievements
        unlocked_frame = tk.LabelFrame(
            scrollable_frame,
            text="🎉 Unlocked Achievements",
            font=("Arial", 14, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            padx=20,
            pady=20
        )
        unlocked_frame.pack(fill="x", padx=10, pady=10)

        unlocked = self.app.achievement_system.get_unlocked_achievements()

        if unlocked:
            for i, achievement in enumerate(unlocked):
                self.create_achievement_card(unlocked_frame, achievement, True, i)
        else:
            tk.Label(
                unlocked_frame,
                text="No achievements unlocked yet. Start tracking habits to earn badges!",
                font=("Arial", 11),
                bg=theme["panel_bg"],
                fg=theme["fg"]
            ).pack(pady=20)

        # Locked achievements
        locked_frame = tk.LabelFrame(
            scrollable_frame,
            text="🔒 Locked Achievements",
            font=("Arial", 14, "bold"),
            bg=theme["panel_bg"],
            fg=theme["fg"],
            padx=20,
            pady=20
        )
        locked_frame.pack(fill="x", padx=10, pady=10)

        locked = self.app.achievement_system.get_locked_achievements()

        for i, achievement in enumerate(locked):
            self.create_achievement_card(locked_frame, achievement, False, i)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_achievement_card(self, parent, achievement, unlocked, index):
        """Create an achievement card"""
        card_bg = "#ecf0f1" if unlocked else "#bdc3c7"

        card = tk.Frame(parent, bg=card_bg, relief="raised", borderwidth=2)
        card.pack(fill="x", pady=5)

        # Icon
        tk.Label(
            card,
            text=achievement["icon"],
            font=("Arial", 36),
            bg=card_bg
        ).pack(side="left", padx=20, pady=10)

        # Info
        info_frame = tk.Frame(card, bg=card_bg)
        info_frame.pack(side="left", fill="both", expand=True, pady=10)

        tk.Label(
            info_frame,
            text=achievement["name"],
            font=("Arial", 14, "bold"),
            bg=card_bg,
            fg="#2c3e50"
        ).pack(anchor="w")

        tk.Label(
            info_frame,
            text=achievement["description"],
            font=("Arial", 10),
            bg=card_bg,
            fg="#34495e"
        ).pack(anchor="w", pady=2)

        # Points
        points_text = f"✓ {achievement['points']} pts" if unlocked else f"🔒 {achievement['points']} pts"
        tk.Label(
            card,
            text=points_text,
            font=("Arial", 12, "bold"),
            bg=card_bg,
            fg="#27ae60" if unlocked else "#7f8c8d"
        ).pack(side="right", padx=20)

    def refresh(self):
        """Refresh achievements display"""
        # Recreate UI to show new achievements
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.create_ui()
