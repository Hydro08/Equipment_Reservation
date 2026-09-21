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

        self._build_ui()

        self.admin_window.mainloop()

    def _center_window(self):
        screen_width = self.admin_window.winfo_screenwidth()
        screen_height = self.admin_window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.admin_window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _build_ui(self):
        self._top_navigation()

        self.top_navigation_bottom_border = tk.Frame(self.admin_window, bg="#FFFFFF", width=2)
        self.top_navigation_bottom_border.pack(fill="x")

        self._parent_frame()

    def _top_navigation(self):
        self.top_panel = tk.Frame(self.admin_window, bg="#1E293B", height=85)
        self.top_panel.pack(fill="x")
        self.top_panel.propagate(False)

        self.dashboard_app_name = tk.Label(self.top_panel, text=f"{self.app_name}", font=("Arial", 24), bg="#1E293B", fg=self.primary_fg)
        self.dashboard_app_name.pack(pady=(20, 0))

    def _parent_frame(self):
        self.main_panel = tk.Frame(self.admin_window, bg="#1E293B")
        self.main_panel.pack(fill="both", expand=True)

    def _left_frame(self):
        self.left_panel = tk.Frame(self.main_panel, bg="#1E293B", width=300)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self._left_panel_border()

    def _left_panel_border(self):
        self.left_panel_right_border = tk.Frame(self.main_panel, bg="#FFFFFF", width=1)
        self.left_panel_right_border.pack(side="left", fill="y")