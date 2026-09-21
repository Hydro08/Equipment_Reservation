import tkinter as tk

class AdminDashboard:

    app_name = "Equipment Reservation"

    window_width = 1500
    window_height = 800

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    w_dashboard_title = "Dashboard"

    def __init__(self, admin: dict):
        self.user = admin
        self.admin_window = tk.Tk()
        self.admin_window.title(f"{self.w_dashboard_title} - {self.app_name}")
        self.admin_window.state("zoomed")
        self.admin_window.config(bg=self.primary_bg)

        self._center_window()
        self.admin_window.mainloop()

    def _center_window(self):
        screen_width = self.admin_window.winfo_screenwidth()
        screen_height = self.admin_window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.admin_window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _build_ui(self):
        pass