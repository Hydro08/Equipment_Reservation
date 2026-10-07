import tkinter as tk
import threading

from tkinter import messagebox

from Admin.pages.manage_inventory import ManageInventoryPage
from Admin.pages.manage_reservation import ManageReservationPage
from Admin.pages.manage_user import ManageUsersPage
from Admin.pages.report import ReportsPage

from Database.session_manager import clear_session
from Authentication.auth_service import get_admin_dashboard_summary

from Config.colors import PRIMARY_BG, SECONDARY_BG, WHITE_BG, PRIMARY_FG, MUTED_FG
from Config.settings import NAV_LABELS, APP_NAME, W_DASHBOARD_TITLE, W_MANAGE_USERS_TITLE, W_MANAGE_INVENTORY_TITLE, W_MANAGE_RESERVATION_TITLE, W_REPORTS_TITLE
from Config.layout import DASHBOARD_WINDOW_WIDTH, DASHBOARD_WINDOW_HEIGHT, BTN_WIDTH, BTN_FONT, BTN_CURSOR

class AdminDashboard:
    def __init__(self, admin: dict):
        self.user = admin
        self.admin_window = tk.Tk()
        self.admin_window.title(f"{W_DASHBOARD_TITLE} - {APP_NAME}")
        self.admin_window.config(bg=PRIMARY_BG)
        self.admin_window.state("zoomed")

        self._center_window()

        self.is_left_panel_minimized = False
        self.active_btn = None

        self.colors = self.fg_bg()
        self.btn_config = self._button_style()
        self._build_ui()

        self.admin_window.mainloop()

    @staticmethod
    def fg_bg():
        return {"bg": PRIMARY_BG, "fg": PRIMARY_FG}

    def _center_window(self):
        screen_width = self.admin_window.winfo_screenwidth()
        screen_height = self.admin_window.winfo_screenheight()
        x = (screen_width - DASHBOARD_WINDOW_WIDTH) // 2
        y = (screen_height - DASHBOARD_WINDOW_HEIGHT) // 2
        self.admin_window.geometry(f"{DASHBOARD_WINDOW_WIDTH}x{DASHBOARD_WINDOW_HEIGHT}+{x}+{y}")

    def _build_ui(self):
        self._top_navigation()

        self.top_navigation_bottom_border = tk.Frame(self.admin_window, bg=WHITE_BG, width=2)
        self.top_navigation_bottom_border.pack(fill="x")

        self._parent_frame()

        self.active_btn = self.dashboard_btn
        self._highlight_active_button()

    def _top_navigation(self):
        self.top_panel = tk.Frame(self.admin_window, bg=PRIMARY_BG, height=85)
        self.top_panel.pack(fill="x")
        self.top_panel.propagate(False)

        self.dashboard_app_name = tk.Label(self.top_panel, text=f"{APP_NAME}", font=("Arial", 24), bg=PRIMARY_BG, fg=PRIMARY_FG)
        self.dashboard_app_name.pack(pady=(20, 0))

    def _parent_frame(self):
        self.main_panel = tk.Frame(self.admin_window, bg=PRIMARY_BG)
        self.main_panel.pack(fill="both", expand=True)

        self._left_frame()
        self._left_panel_border()
        self._right_frame()

    def _left_frame(self):
        self.left_panel = tk.Frame(self.main_panel, bg=PRIMARY_BG, width=300)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.minimize_panel_btn = tk.Button(self.left_panel, text="<", font=("Arial", 12), width=3, cursor="hand2", bg=PRIMARY_BG, fg=PRIMARY_FG)
        self.minimize_panel_btn.pack(anchor="e", padx=(0, 20), pady=(20, 0))
        self.dashboard_btn = tk.Button(self.left_panel, text=NAV_LABELS["dashboard_btn"][0], **self.btn_config)
        self.dashboard_btn.pack(pady=(50, 0), padx=(80, 0))
        self.manage_reservation_btn = tk.Button(self.left_panel, text=NAV_LABELS["manage_reservation_btn"][0], **self.btn_config)
        self.manage_reservation_btn.pack(pady=(50, 0))
        self.manage_inventory_btn = tk.Button(self.left_panel, text=NAV_LABELS["manage_inventory_btn"][0], **self.btn_config)
        self.manage_inventory_btn.pack(pady=(50, 0))
        self.manage_users_btn = tk.Button(self.left_panel, text=NAV_LABELS["manage_users_btn"][0], **self.btn_config)
        self.manage_users_btn.pack(pady=(50, 0))
        self.reports_btn = tk.Button(self.left_panel, text=NAV_LABELS["reports_btn"][0], **self.btn_config)
        self.reports_btn.pack(pady=(50, 0))
        self.logout_btn = tk.Button(self.left_panel, text=NAV_LABELS["logout_btn"][0], **self.btn_config, command=self.logout)
        self.logout_btn.pack(pady=(50, 0))

        self.minimize_panel_btn.bind("<Button-1>", lambda e: self.toggle_sidebar())
        self.dashboard_btn.bind("<Button-1>", self._on_nav_click)
        self.manage_reservation_btn.bind("<Button-1>", self._on_nav_click)
        self.manage_inventory_btn.bind("<Button-1>", self._on_nav_click)
        self.manage_users_btn.bind("<Button-1>", self._on_nav_click)
        self.reports_btn.bind("<Button-1>", self._on_nav_click)

    def _left_panel_border(self):
        self.left_panel_right_border = tk.Frame(self.main_panel, bg=PRIMARY_BG, width=1)
        self.left_panel_right_border.pack(side="left", fill="y")

    @staticmethod
    def _button_style():
        return {"font": BTN_FONT, "width": BTN_WIDTH, "cursor": BTN_CURSOR, "bg": PRIMARY_BG, "fg": PRIMARY_FG,  "activebackground": PRIMARY_BG, "activeforeground": PRIMARY_FG,}

    def _right_frame(self):
        self.right_panel = tk.Frame(self.main_panel, bg=PRIMARY_BG)
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._show_dashboard()

    def _show_dashboard(self):
        self._clear_right_panel()

        self.admin_window.title(f"{W_DASHBOARD_TITLE} - {APP_NAME}")
        self.dashboard_title = tk.Label(self.right_panel, text="Dashboard", font=("Arial", 24, "bold"), **self.colors)
        self.dashboard_title.pack(pady=(20, 10))

        self.loading_database = tk.Label(self.right_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_database.pack()

        threading.Thread(target=self._fetch_dashboard_data, daemon=True).start()

    def _fetch_dashboard_data(self):
        summary = get_admin_dashboard_summary()

        self.admin_window.after(0, self._render_dashboard_cards, summary)

    def _render_dashboard_cards(self, summary):
        if not self.loading_database.winfo_exists():
            return

        self.loading_database.destroy()
        self._summary_cards(summary)

    def _summary_cards(self, summary):
        self.cards_frame = tk.Frame(self.right_panel, bg=PRIMARY_BG)
        self.cards_frame.pack(fill="both", expand=True, padx=40, pady=10)

        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_rowconfigure(0, weight=1)
        self.cards_frame.grid_rowconfigure(1, weight=1)
        self.cards_frame.grid_rowconfigure(2, weight=1)
        self.cards_frame.grid_rowconfigure(2, weight=1)

        self._create_card(self.cards_frame, "Total Equipment", str(summary["total_equipment"]), row=0, column=0, on_click=lambda: self._navigate_to(self.manage_inventory_btn))

        self._create_card(self.cards_frame, "Total Users", str(summary["total_users"]), row=0, column=1, on_click=lambda: self._navigate_to(self.manage_users_btn))

        self._create_card(self.cards_frame, "Pending", str(summary["pending"]), row=1, column=0, on_click=lambda: self._navigate_to(self.manage_reservation_btn, tab="request"))

        self._create_card(self.cards_frame, "Borrowed Equipment", str(summary["borrowed"]), row=1, column=1, on_click=lambda: self._navigate_to(self.manage_reservation_btn, tab="borrowed"))

        self._create_card(self.cards_frame, "Available Equipment", str(summary["available"]), row=2, column=0, on_click=lambda: self._navigate_to(self.manage_reservation_btn, tab="available"))

        self._create_card(self.cards_frame, "Pending Returns", str(summary["returning"]), row=2, column=1, on_click=lambda: self._navigate_to(self.manage_reservation_btn, tab="return"))

    @staticmethod
    def _create_card(parent, title, value, row, column, on_click=None):
        card = tk.Frame(parent, bg=SECONDARY_BG, cursor="hand2", height=180)
        card.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")
        card.grid_propagate(False)

        value_label = tk.Label(card, text=value, font=("Arial", 20, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG)
        value_label.pack(pady=(60, 20))
        title_label = tk.Label(card, text=title, font=("Arial", 24), bg=SECONDARY_BG, fg=MUTED_FG)
        title_label.pack(pady=(30, 10))

        if on_click:
            for widget in (card, value_label, title_label):
                widget.config(cursor="hand2")
                widget.bind("<Button-1>", lambda e: on_click())

    def toggle_sidebar(self):
        if self.is_left_panel_minimized:
            self._restore_left_frame()
            self.minimize_panel_btn.config(text="<")
            self._update_nav_labels(False)
        else:
            self._minimized_left_frame()
            self.minimize_panel_btn.config(text=">")
            self._update_nav_labels(True)

        self._highlight_active_button()

    def _minimized_left_frame(self):
        self.is_left_panel_minimized = True
        self.left_panel.config(width=100)

        for btn in (self.dashboard_btn, self.manage_reservation_btn, self.manage_inventory_btn, self.manage_users_btn, self.reports_btn, self.logout_btn):
            btn.config(width=4)
            btn.pack_configure(padx=(0, 0))

    def _restore_left_frame(self):
        self.is_left_panel_minimized = False
        self.left_panel.config(width=300)

        for btn in (self.dashboard_btn, self.manage_reservation_btn, self.manage_inventory_btn, self.manage_users_btn, self.reports_btn, self.logout_btn):
            btn.config(width=BTN_WIDTH, bg=PRIMARY_BG)

    def _update_nav_labels(self, minimized):
        index = 1 if minimized else 0
        for attr_name, labels in NAV_LABELS.items():
            btn = getattr(self, attr_name)
            btn.config(text=labels[index])

    def _on_nav_click(self, event):
        self._navigate_to(event.widget)

    def _navigate_to(self, target_btn, tab=None):
        self.active_btn = target_btn

        self._highlight_active_button()

        if self.is_left_panel_minimized:
            target_btn.pack_configure(padx=(0, 0))

        if not self.is_left_panel_minimized:
            target_btn.pack_configure(padx=(80, 0))
        else:
            for btn in (self.dashboard_btn, self.manage_reservation_btn, self.manage_inventory_btn,
                        self.manage_users_btn, self.reports_btn):
                btn.config(bg=PRIMARY_BG)
            target_btn.config(bg=SECONDARY_BG)

        if target_btn == self.dashboard_btn:
            self._show_dashboard()
        elif target_btn == self.manage_reservation_btn:
            self._show_manage_reservation_page(tab)
        elif target_btn == self.manage_inventory_btn:
            self._show_manage_inventory_page()
        elif target_btn == self.manage_users_btn:
            self._show_manage_users_page()
        elif target_btn == self.reports_btn:
            self._show_reports_page()

    def _highlight_active_button(self):
        self._loops_btn()
        for btn in (self.dashboard_btn, self.manage_reservation_btn, self.manage_inventory_btn, self.manage_users_btn,
                    self.reports_btn):
            btn.config(bg=PRIMARY_BG)

        if self.active_btn is None:
            return

        if self.is_left_panel_minimized:
            self.active_btn.config(bg=SECONDARY_BG)
        else:
            self.active_btn.pack_configure(padx=(80, 0))

    def _loops_btn(self):
        for btn in (self.dashboard_btn, self.manage_reservation_btn, self.manage_inventory_btn, self.manage_users_btn, self.reports_btn):
            btn.pack_configure(padx=(0, 0))

    def _show_manage_reservation_page(self, tab=None):
        self.admin_window.title(f"{W_MANAGE_RESERVATION_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        ManageReservationPage(self.right_panel, self.colors, initial_tab=tab or "request")

    def _show_manage_inventory_page(self):
        self.admin_window.title(f"{W_MANAGE_INVENTORY_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        ManageInventoryPage(self.right_panel, self.colors)

    def _show_manage_users_page(self):
        self.admin_window.title(f"{W_MANAGE_USERS_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        ManageUsersPage(self.right_panel, self.colors)

    def _show_reports_page(self):
        self.admin_window.title(f"{W_REPORTS_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        ReportsPage(self.right_panel, self.colors)

    def _clear_right_panel(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

    def logout(self):
        logout_question = messagebox.askyesno("Confirm Logout", "Are you sure to logout?")

        if logout_question:
            clear_session()

            self.admin_window.destroy()

            from Authentication.login import LoginWindow
            LoginWindow()