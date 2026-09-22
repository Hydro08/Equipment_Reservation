import tkinter as tk

from tkinter import messagebox

from Database.session_manager import clear_session

class AdminDashboard:

    app_name = "Equipment Reservation"

    window_width = 1500
    window_height = 800

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    btn_font = ("Arial", 18)
    btn_width = 12
    btn_cursor = "hand2"

    w_dashboard_title = "Dashboard"

    nav_labels = {
        "dashboard_btn": ("Dashboard", "🏠"),
        "manage_reservation_btn": ("Manage\nReservation", "📋"),
        "manage_equipment_btn": ("Manage\nEquipment", "📦"),
        "manage_users_btn": ("Manage Users", "👥"),
        "reports_btn": ("Reports", "📊"),
        "logout_btn": ("Log out", "🚪"),
    }

    def __init__(self, admin: dict):
        self.user = admin
        self.admin_window = tk.Tk()
        self.admin_window.title(f"{self.w_dashboard_title} - {self.app_name}")
        self.admin_window.state("zoomed")
        self.admin_window.config(bg=self.primary_bg)

        self._center_window()

        self.btn_config = self._button_style()

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

        self._left_frame()
        self._left_panel_border()

    def _left_frame(self):
        self.left_panel = tk.Frame(self.main_panel, bg="#1E293B", width=300)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.minimize_panel = tk.Button(self.left_panel, text="<", font=("Arial", 12), width=3, cursor="hand2", bg="#1E293B", fg="#FFFFFF")
        self.minimize_panel.pack(anchor="e", padx=(0, 20), pady=(20, 0))

        self.dashboard_btn = tk.Button(self.left_panel, text=self.nav_labels["dashboard_btn"][0], **self.btn_config)
        self.dashboard_btn.pack(pady=(50, 0))
        self.manage_reservation_btn = tk.Button(self.left_panel, text=self.nav_labels["manage_reservation_btn"][0], **self.btn_config)
        self.manage_reservation_btn.pack(pady=(50, 0))
        self.manage_equipment_btn = tk.Button(self.left_panel, text=self.nav_labels["manage_equipment_btn"][0], **self.btn_config)
        self.manage_equipment_btn.pack(pady=(50, 0))
        self.manage_users_btn = tk.Button(self.left_panel, text=self.nav_labels["manage_users_btn"][0], **self.btn_config)
        self.manage_users_btn.pack(pady=(50, 0))
        self.reports_btn = tk.Button(self.left_panel, text=self.nav_labels["reports_btn"][0], **self.btn_config)
        self.reports_btn.pack(pady=(50, 0))
        self.logout_btn = tk.Button(self.left_panel, text=self.nav_labels["logout_btn"][0], **self.btn_config, command=self.logout)
        self.logout_btn.pack(pady=(50, 0))

    def _left_panel_border(self):
        self.left_panel_right_border = tk.Frame(self.main_panel, bg="#FFFFFF", width=1)
        self.left_panel_right_border.pack(side="left", fill="y")

    def _button_style(self):
        return {"font": self.btn_font, "width": self.btn_width, "cursor": self.btn_cursor, "bg": "#1E293B", "fg": self.primary_fg,  "activebackground": "#1E293B", "activeforeground": "#FFFFFF",}

    def logout(self):
        logout_question = messagebox.askyesno("Confirm Logout", "Are you sure to logout?")

        if logout_question:
            clear_session()

            self.admin_window.destroy()

            from Authentication.login import LoginWindow
            LoginWindow()