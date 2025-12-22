# themes.py - Theme management
class ThemeManager:
    """Manages application themes"""
    
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager
        self.current_theme = self.data_manager.settings.get("theme", "dark")
        
        self.themes = {
            "light": {
                "bg": "#f0f0f0",
                "fg": "#1e1e1e",
                "panel_bg": "white",
                "accent": "#3498db",
                "success": "#27ae60",
                "danger": "#e74c3c",
                "warning": "#f39c12"
            },
            "dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "panel_bg": "#2d2d2d",
                "accent": "#3498db",
                "success": "#27ae60",
                "danger": "#e74c3c",
                "warning": "#f39c12"
            }
        }
    
    def get_theme(self):
        """Get current theme colors"""
        return self.themes[self.current_theme]
    
    def get_current_theme(self):
        """Get current theme name"""
        return self.current_theme
    
    def apply_theme(self):
        """Apply current theme to root window"""
        theme = self.get_theme()
        self.root.configure(bg=theme["bg"])
    
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.data_manager.settings["theme"] = self.current_theme
        self.data_manager.save_json(self.data_manager.settings_file, self.data_manager.settings)
        self.apply_theme()