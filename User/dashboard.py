import tkinter as tk
import threading

from tkinter import messagebox

from User.pages.browse_equipment import BrowseEquipmentPage
from User.pages.reservation import ReservationPage
from User.pages.notification import NotificationPage
from User.pages.profile import ProfilePage

from Authentication.auth_service import get_dashboard_summary
from Database.session_manager import clear_session

class UserDashboard:

    app_name = "Equipment Reservation"
    window_width = 1500
    window_height = 800

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    btn_font = ("Arial", 18)
    btn_width = 12
    btn_cursor = "hand2"

    w_dashboard_title = "Dashboard"
    w_browser_equip_title = "Browser Equipment"
    w_reservation_title = "Reservation"
    w_notification_title = "Notification"
    w_profile_title = "Profile"

    nav_labels = {
        "dashboard_btn": ("Dashboard", "🏠"),
        "browse_equipment_btn": ("Browse\n Equipment", "🔍"),
        "reservation_btn": ("My Reservation", "📋"),
        "notification_btn": ("Notification", "🔔"),
        "profile_btn": ("Profile", "👤"),
        "logout_btn": ("Log out", "🚪"),
    }

    def __init__(self, user: dict):
        self.user = user
        self.user_window = tk.Tk()
        self.user_window.title(f"{self.w_dashboard_title} - {self.app_name}")
        self.user_window.minsize(self.window_width, self.window_height)
        self.user_window.config(bg=self.primary_bg)
        self.user_window.state("zoomed")

        self._center_window()

        self.is_left_panel_minimize = False
        self.active_btn = None

        self.colors = self.fg_bg()
        self.btn_config = self._button_style()
        self._build_ui()

        self.user_window.mainloop()

    def fg_bg(self):
        return {"bg": self.primary_bg, "fg": self.primary_fg}

    def _center_window(self):
        screen_width = self.user_window.winfo_screenwidth()
        screen_height = self.user_window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.user_window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _build_ui(self):
        self._top_navigation()

        self.top_navigation_bottom_border = tk.Frame(self.user_window, bg="#FFFFFF", width=2)
        self.top_navigation_bottom_border.pack(fill="x")

        self._parent_frame()

        self.active_btn = self.dashboard_btn
        self._highlight_active_button()

    def _top_navigation(self):
        self.top_panel = tk.Frame(self.user_window, bg=self.primary_bg, height=85)
        self.top_panel.pack(fill="x")
        self.top_panel.propagate(False)

        self.dashboard_app_name = tk.Label(self.top_panel, text=f"{self.app_name}", font=("Arial", 24), bg=self.primary_bg, fg=self.primary_fg)
        self.dashboard_app_name.pack(side="left", padx=(20,0))
        self.user_username = tk.Label(self.top_panel, text=f"{self.user['username']}", font=("Arial", 16, "underline"), bg=self.primary_bg, fg=self.primary_fg, cursor="hand2")
        self.user_username.pack(side="right", padx=(0,20))

    def _parent_frame(self):
        self.main_panel = tk.Frame(self.user_window, bg=self.primary_bg)
        self.main_panel.pack(fill="both", expand=True)

        self._left_frame()
        self._left_panel_border()
        self._right_frame()

    def _left_frame(self):
        self.left_panel = tk.Frame(self.main_panel, bg=self.primary_bg, width=300)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.minimize_panel = tk.Button(self.left_panel, text="<", font=("Arial", 12), width=3, cursor="hand2",  bg=self.primary_bg, fg="#FFFFFF")
        self.minimize_panel.pack(anchor="e", padx=(0, 20), pady=(20, 0))
        self.dashboard_btn = tk.Button(self.left_panel, text=self.nav_labels["dashboard_btn"][0], **self.btn_config)
        self.dashboard_btn.pack(pady=(50, 0), padx=(80, 0))
        self.browse_equipment_btn = tk.Button(self.left_panel,text=self.nav_labels["browse_equipment_btn"][0], **self.btn_config)
        self.browse_equipment_btn.pack(pady=(50, 0))
        self.reservation_btn = tk.Button(self.left_panel, text=self.nav_labels["reservation_btn"][0],**self.btn_config)
        self.reservation_btn.pack(pady=(50, 0))
        self.notification_btn = tk.Button(self.left_panel, text=self.nav_labels["notification_btn"][0],**self.btn_config)
        self.notification_btn.pack(pady=(50, 0))
        self.profile_btn = tk.Button(self.left_panel, text=self.nav_labels["profile_btn"][0],**self.btn_config)
        self.profile_btn.pack(pady=(50, 0))
        self.logout_btn = tk.Button(self.left_panel,
        text=self.nav_labels["logout_btn"][0], **self.btn_config, command = self.logout)
        self.logout_btn.pack(pady=(50, 0))

        self.minimize_panel.bind("<Button-1>", lambda e: self.toggle_sidebar())
        self.dashboard_btn.bind("<Button-1>", self._on_nav_click)
        self.browse_equipment_btn.bind("<Button-1>", self._on_nav_click)
        self.reservation_btn.bind("<Button-1>", self._on_nav_click)
        self.notification_btn.bind("<Button-1>", self._on_nav_click)
        self.profile_btn.bind("<Button-1>", self._on_nav_click)
        self.user_username.bind("<Button-1>", lambda e: self._show_profile_page())

    def _button_style(self):
        return {"font": self.btn_font, "width": self.btn_width, "cursor": self.btn_cursor, "bg": self.primary_bg, "fg": self.primary_fg,  "activebackground": self.primary_bg, "activeforeground": "#FFFFFF",}

    def _on_nav_click(self, event):
        clicked_button = event.widget
        self.active_btn = clicked_button

        self._highlight_active_button()

        if self.is_left_panel_minimize:
            clicked_button.pack_configure(padx=(0, 0))

        if not self.is_left_panel_minimize:
            clicked_button.pack_configure(padx=(80, 0))
        else:
            for btn in (self.dashboard_btn, self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn):
                btn.config(bg=self.primary_bg)
            clicked_button.config(bg="#334155")

        if clicked_button == self.dashboard_btn:
            self._show_dashboard()
        elif clicked_button == self.browse_equipment_btn:
            self._show_equipment_page()
        elif clicked_button == self.reservation_btn:
            self._show_reservation_page()
        elif clicked_button == self.notification_btn:
            self._show_notification_page()
        elif clicked_button == self.profile_btn:
            self._show_profile_page()

    def _highlight_active_button(self):
        self._loops_btn()
        for btn in (self.dashboard_btn, self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn):
            btn.config(bg=self.primary_bg)

        if self.active_btn is None:
            return

        if self.is_left_panel_minimize:
            self.active_btn.config(bg="#334155")
        else:
            self.active_btn.pack_configure(padx=(80, 0))

    def _loops_btn(self):
        for btn in (self.dashboard_btn,self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn):
            btn.pack_configure(padx=(0, 0))

    def _right_frame(self):
        self.right_panel = tk.Frame(self.main_panel, bg=self.primary_bg)
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._show_dashboard()

    def _show_dashboard(self):
        self._clear_right_panel()

        self.user_window.title(f"{self.w_dashboard_title} - {self.app_name}")
        self.dashboard_title = tk.Label(self.right_panel, text="Dashboard", font=("Arial", 24, "bold"), **self.colors)
        self.dashboard_title.pack(pady=(20, 10))

        self.loading_database = tk.Label(self.right_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_database.pack()

        threading.Thread(target=self._fetch_dashboard_data, daemon=True).start()

    def _fetch_dashboard_data(self):
        summary = get_dashboard_summary(self.user["id"])

        self.user_window.after(0, self._render_dashboard_cards, summary)

    def _render_dashboard_cards(self, summary):
        if not self.loading_database.winfo_exists():
            return

        self.loading_database.destroy()
        self._summary_cards(summary)

    def _summary_cards(self, summary):
        self.cards_frame = tk.Frame(self.right_panel, bg=self.primary_bg)
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_rowconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(1, weight=1)
        self.cards_frame.grid_rowconfigure(2, weight=1)

        self._create_card(self.cards_frame, "Available Equipment", str(summary["available"]), row=0, column=0)
        self._create_card(self.cards_frame, "Pending Reservation", str(summary["pending"]), row=0, column=1)
        self._create_card(self.cards_frame, "Borrowed Items", str(summary["borrowed"]), row=1, column=0)
        self._create_card(self.cards_frame, "Total Equipment", str(summary["total"]), row=1, column=1)
        self._create_card(self.cards_frame, "Due Soon", str(summary["due_soon"]), row=2, column=0)

    def _create_card(self, parent, title, value, row, column):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")
        card.grid_propagate(False)

        value_label = tk.Label(card, text=value, font=("Arial", 20, "bold"), bg="#334155", fg=self.primary_fg)
        value_label.pack(pady=(70, 10))
        title_label = tk.Label(card, text=title, font=("Arial", 24), bg="#334155", fg="#94A3B8")
        title_label.pack(pady=(30, 10))

    def _show_equipment_page(self):
        self.user_window.title(f"{self.w_browser_equip_title} - {self.app_name}")
        self._clear_right_panel()
        BrowseEquipmentPage(self.right_panel, self.colors)

    def _show_reservation_page(self):
        self.user_window.title(f"{self.w_reservation_title} - {self.app_name}")
        self._clear_right_panel()
        ReservationPage(self.right_panel, self.colors)

    def _show_notification_page(self):
        self.user_window.title(f"{self.w_notification_title} - {self.app_name}")
        self._clear_right_panel()
        NotificationPage(self.right_panel, self.colors)

    def _show_profile_page(self):
        self.user_window.title(f"{self.w_profile_title} - {self.app_name}")
        self._clear_right_panel()
        self.active_btn = self.profile_btn
        self._highlight_active_button()

        if not self.is_left_panel_minimize:
            self._loops_btn()
            self.profile_btn.pack(padx=(80, 0))

        ProfilePage(self.right_panel, self.colors)

    def _update_nav_labels(self, minimized):
        index = 1 if minimized else 0
        for attr_name, labels in self.nav_labels.items():
            btn = getattr(self, attr_name)
            btn.config(text=labels[index])

    def toggle_sidebar(self):
        if self.is_left_panel_minimize:
            self._restore_left_frame()
            self.minimize_panel.config(text="<")
            self._update_nav_labels(False)
        else:
            self._minimized_left_frame()
            self.minimize_panel.config(text=">")
            self._update_nav_labels(True)

        self._highlight_active_button()

    def _minimized_left_frame(self):
        self.is_left_panel_minimize = True
        self.left_panel.config(width=100)

        for btn in (self.dashboard_btn, self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn, self.logout_btn):
            btn.config(width=4)
            btn.pack_configure(padx=(0, 0))

    def _restore_left_frame(self):
        self.is_left_panel_minimize = False
        self.left_panel.config(width=300)

        for btn in (
        self.dashboard_btn, self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn):
            btn.config(width=self.btn_width, bg=self.primary_bg)

    def _left_panel_border(self):
        self.left_panel_right_border = tk.Frame(self.main_panel, bg="#FFFFFF", width=1)
        self.left_panel_right_border.pack(side="left", fill="y")

    def _clear_right_panel(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

    def logout(self):
        logout_question = messagebox.askyesno("Confirm Logout", "Are you sure to logout?")

        if logout_question:
            clear_session()

            self.user_window.destroy()

            from Authentication.login import LoginWindow
            LoginWindow()