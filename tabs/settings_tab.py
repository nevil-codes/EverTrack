# tabs/settings_tab.py
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox


class SettingsTab:
    """Settings and export tab"""

    def __init__(self, notebook, app):
        self.app = app
        self.frame = tk.Frame(notebook, bg=app.theme_manager.get_theme()["bg"])
        self.create_ui()

    def create_ui(self):
        """Create the settings UI"""
        theme = self.app.theme_manager.get_theme()

        container = tk.Frame(self.frame, bg=theme["bg"])
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = tk.Frame(container, bg="#34495e", height=70)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙️ Settings & Data Management",
            font=("Arial", 20, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(pady=18)

        # Appearance settings
        appearance_frame = self.app.ui.create_label_frame(container, "🎨 Appearance")
        appearance_frame.pack(fill="x", pady=10)

        tk.Label(
            appearance_frame,
            text="Theme:",
            font=("Arial", 11),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).grid(row=0, column=0, sticky="w", pady=10)

        current_theme = self.app.theme_manager.get_current_theme()
        theme_text = f"Current: {current_theme.title()} Mode"

        tk.Label(
            appearance_frame,
            text=theme_text,
            font=("Arial", 11, "bold"),
            bg=theme["panel_bg"],
            fg=theme["accent"]
        ).grid(row=0, column=1, sticky="w", padx=20, pady=10)

        tk.Button(
            appearance_frame,
            text="Toggle Theme",
            command=self.app.toggle_theme,
            bg=theme["accent"],
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=5
        ).grid(row=0, column=2, pady=10)

        # Notification settings
        notif_frame = self.app.ui.create_label_frame(container, "🔔 Notifications")
        notif_frame.pack(fill="x", pady=10)

        self.notif_var = tk.BooleanVar(value=self.app.data_manager.settings.get("notifications", True))

        tk.Checkbutton(
            notif_frame,
            text="Enable desktop notifications and reminders",
            variable=self.notif_var,
            command=self.toggle_notifications,
            font=("Arial", 11),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).pack(anchor="w", pady=10)

        tk.Label(
            notif_frame,
            text="Get reminders for your habits and achievement notifications",
            font=("Arial", 9),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).pack(anchor="w", padx=25)

        # Data export
        export_frame = self.app.ui.create_label_frame(container, "📤 Export Data")
        export_frame.pack(fill="x", pady=10)

        tk.Label(
            export_frame,
            text="Export your habit data for backup or external analysis",
            font=("Arial", 10),
            bg=theme["panel_bg"],
            fg=theme["fg"]
        ).pack(anchor="w", pady=10)

        export_btn_frame = tk.Frame(export_frame, bg=theme["panel_bg"])
        export_btn_frame.pack(fill="x", pady=10)

        tk.Button(
            export_btn_frame,
            text="📊 Export to CSV",
            command=self.export_csv,
            bg="#27ae60",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

        tk.Button(
            export_btn_frame,
            text="📄 Generate PDF Report",
            command=self.generate_pdf,
            bg="#3498db",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

        tk.Button(
            export_btn_frame,
            text="💾 Backup All Data",
            command=self.backup_data,
            bg="#9b59b6",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

        # Statistics
        stats_frame = self.app.ui.create_label_frame(container, "📊 Statistics")
        stats_frame.pack(fill="x", pady=10)

        self.update_statistics(stats_frame, theme)

        # Danger zone
        danger_frame = tk.LabelFrame(
            container,
            text="⚠️ Danger Zone",
            font=("Arial", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            padx=20,
            pady=20
        )
        danger_frame.pack(fill="x", pady=10)

        tk.Label(
            danger_frame,
            text="⚠️ Warning: These actions cannot be undone!",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white"
        ).pack(anchor="w", pady=5)

        tk.Button(
            danger_frame,
            text="🗑️ Clear All Data",
            command=self.clear_all_data,
            bg="#c0392b",
            fg="black",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(anchor="w", pady=10)

    def toggle_notifications(self):
        """Toggle notifications on/off"""
        self.app.data_manager.settings["notifications"] = self.notif_var.get()
        self.app.data_manager.save_json(
            self.app.data_manager.settings_file,
            self.app.data_manager.settings
        )

        status = "enabled" if self.notif_var.get() else "disabled"
        messagebox.showinfo("Notifications", f"Notifications {status}!")

    def export_csv(self):
        """Export data to CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"evertrack_data_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if filename:
            if self.app.data_manager.export_to_csv(filename):
                messagebox.showinfo("Success", f"Data exported to:\n{filename}")
            else:
                messagebox.showerror("Error", "Failed to export data!")

    def generate_pdf(self):
        """Generate PDF report"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch
            from reportlab.pdfgen import canvas

            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"evertrack_report_{datetime.now().strftime('%Y%m%d')}.pdf"
            )

            if not filename:
                return

            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter

            # Title
            c.setFont("Helvetica-Bold", 24)
            c.drawString(1*inch, height - 1*inch, "EverTrack Pro - Habit Report")

            # Date
            c.setFont("Helvetica", 12)
            c.drawString(1*inch, height - 1.5*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # Statistics
            logs = self.app.data_manager.log_models()
            habits = self.app.data_manager.habit_models()

            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*inch, height - 2.2*inch, "Summary Statistics")

            c.setFont("Helvetica", 12)
            y_pos = height - 2.7*inch

            stats = [
                f"Total Habits Created: {len(habits)}",
                f"Total Activities Logged: {len(logs)}",
                f"Total Time Invested: {sum(log.duration_min for log in logs):.0f} minutes",
                f"Active Days: {len({log.log_date for log in logs})}",
                f"Current Streak: {self.app.achievement_system.calculate_current_streak()} days",
                f"Achievement Points: {self.app.achievement_system.get_total_points()}",
            ]

            for stat in stats:
                c.drawString(1.2*inch, y_pos, f"• {stat}")
                y_pos -= 0.3*inch

            # Habits list
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*inch, y_pos - 0.5*inch, "Your Habits")

            y_pos -= 1*inch
            c.setFont("Helvetica", 11)

            for habit in habits:
                if y_pos < 1*inch:
                    c.showPage()
                    y_pos = height - 1*inch

                c.drawString(1.2*inch, y_pos, f"• {habit.name} - Target: {habit.daily_target_min} min/day")
                y_pos -= 0.3*inch

            c.save()
            messagebox.showinfo("Success", f"PDF report generated:\n{filename}")

        except ImportError:
            messagebox.showwarning(
                "Missing Library",
                "PDF generation requires 'reportlab' library.\n\n"
                "Install it with: pip install reportlab"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF:\n{str(e)}")

    def backup_data(self):
        """Backup all data to a folder"""
        import shutil

        folder = filedialog.askdirectory(title="Select Backup Location")

        if folder:
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"evertrack_backup_{timestamp}"
                backup_path = f"{folder}/{backup_name}"

                import os
                os.makedirs(backup_path, exist_ok=True)

                # Copy all JSON files
                files = [
                    self.app.data_manager.data_file,
                    self.app.data_manager.habits_file,
                    self.app.data_manager.settings_file,
                    self.app.data_manager.achievements_file
                ]

                for file in files:
                    if os.path.exists(file):
                        shutil.copy(file, backup_path)

                messagebox.showinfo("Success", f"Data backed up to:\n{backup_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed:\n{str(e)}")

    def clear_all_data(self):
        """Clear all data (dangerous operation)"""
        confirm = messagebox.askyesno(
            "⚠️ WARNING",
            "This will DELETE ALL your data:\n"
            "• All habits\n"
            "• All activity logs\n"
            "• All achievements\n"
            "• All settings\n\n"
            "This action CANNOT be undone!\n\n"
            "Are you absolutely sure?"
        )

        if confirm:
            double_confirm = messagebox.askyesno(
                "⚠️ FINAL WARNING",
                "Last chance to cancel!\n\n"
                "Delete everything?"
            )

            if double_confirm:
                data_manager = self.app.data_manager
                data_manager.habits_data = []
                data_manager.habits_list = []
                data_manager.achievements = {"unlocked": [], "total_points": 0}
                # The dialog promises settings are cleared too: keep the current
                # theme (the window is already drawn in it) and reset the rest,
                # including reminders for habits that no longer exist.
                data_manager.settings = {
                    "theme": self.app.theme_manager.get_current_theme(),
                    "notifications": True,
                    "reminder_times": {},
                }
                data_manager.save_all()

                self.app.refresh_all()

                messagebox.showinfo("Cleared", "All data has been deleted.")

    def update_statistics(self, parent, theme):
        """Update statistics display"""
        logs = self.app.data_manager.log_models()
        habits = self.app.data_manager.habit_models()

        stats = [
            ("Total Habits:", len(habits)),
            ("Total Logs:", len(logs)),
            ("Total Time:", f"{sum(log.duration_min for log in logs):.0f} min"),
            ("Achievement Points:", self.app.achievement_system.get_total_points()),
            ("Current Streak:", f"{self.app.achievement_system.calculate_current_streak()} days"),
        ]

        for label, value in stats:
            row_frame = tk.Frame(parent, bg=theme["panel_bg"])
            row_frame.pack(fill="x", pady=5)

            tk.Label(
                row_frame,
                text=label,
                font=("Arial", 11),
                bg=theme["panel_bg"],
                fg=theme["fg"],
                width=20,
                anchor="w"
            ).pack(side="left", padx=10)

            tk.Label(
                row_frame,
                text=str(value),
                font=("Arial", 11, "bold"),
                bg=theme["panel_bg"],
                fg=theme["accent"]
            ).pack(side="left")

    def refresh(self):
        """Refresh settings tab"""
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.create_ui()
