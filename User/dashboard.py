import tkinter as tk
import threading
import httpx

from tkinter import messagebox

from User.pages.browse_equipment import BrowseEquipmentPage
from User.pages.reservation import ReservationPage
from User.pages.notification import NotificationPage
from User.pages.profile import ProfilePage

from Authentication.auth_service import get_dashboard_summary, get_user_by_id
from Database.session_manager import clear_session
from Config.colors import PRIMARY_BG, SECONDARY_BG, WHITE_BG, PRIMARY_FG, GREEN_BG, DARK_BLUE_BG, MUTED_FG
from Config.settings import BAN_CHECK_MS, SCHOOL_NAME, APP_NAME, W_DASHBOARD_TITLE, W_BROWSE_EQUIP_TITLE, W_RESERVATION_TITLE, W_NOTIFICATION_TITLE, W_PROFILE_TITLE, NAV_LABELS
from Config.layout import DASHBOARD_WINDOW_WIDTH, DASHBOARD_WINDOW_HEIGHT, BTN_WIDTH, BTN_FONT, BTN_CURSOR

class UserDashboard:
    def __init__(self, user: dict):
        self.user = user
        self.user_window = tk.Tk()
        self.user_window.title(f"{W_DASHBOARD_TITLE} - {APP_NAME}")
        self.user_window.minsize(DASHBOARD_WINDOW_WIDTH, DASHBOARD_WINDOW_HEIGHT)
        self.user_window.config(bg=PRIMARY_BG)
        self.user_window.state("zoomed")

        self._center_window()

        self.is_left_panel_minimize = False
        self.active_btn = None

        self.colors = self.fg_bg()
        self.btn_config = self._button_style()
        self._build_ui()

        self._start_ban_check()

        self.user_window.mainloop()

    @staticmethod
    def fg_bg():
        return {"bg": PRIMARY_BG, "fg": PRIMARY_FG}

    def _center_window(self):
        screen_width = self.user_window.winfo_screenwidth()
        screen_height = self.user_window.winfo_screenheight()
        x = (screen_width - DASHBOARD_WINDOW_WIDTH) // 2
        y = (screen_height - DASHBOARD_WINDOW_HEIGHT) // 2
        self.user_window.geometry(f"{DASHBOARD_WINDOW_WIDTH}x{DASHBOARD_WINDOW_HEIGHT}+{x}+{y}")

    def _build_ui(self):
        self._top_navigation()

        self.top_navigation_bottom_border = tk.Frame(self.user_window, bg=WHITE_BG, width=2)
        self.top_navigation_bottom_border.pack(fill="x")

        self._parent_frame()

        self.active_btn = self.dashboard_btn
        self._highlight_active_button()

    def _top_navigation(self):
        self.top_panel = tk.Frame(self.user_window, bg=PRIMARY_BG, height=85)
        self.top_panel.pack(fill="x")
        self.top_panel.propagate(False)

        self.school_name = tk.Label(self.top_panel, text=SCHOOL_NAME, font=("Arial", 24), bg=PRIMARY_BG, fg=PRIMARY_FG)
        self.school_name.pack(side="left", padx=(20, 0))

        self.dashboard_app_name = tk.Label(self.top_panel, text=APP_NAME, font=("Arial", 24), bg=PRIMARY_BG, fg=PRIMARY_FG)
        self.dashboard_app_name.place(relx=0.5, rely=0.5, anchor="center")
        
        self.user_avatar = tk.Canvas(self.top_panel, width=44, height=44, bg=PRIMARY_BG, highlightthickness=0, cursor="hand2")
        self.user_avatar.pack(side="right", padx=(0, 20))

        self.user_username = tk.Label(self.top_panel, text=f"{self.user['username']}", font=("Arial", 16, "underline"), bg=PRIMARY_BG, fg=PRIMARY_FG, cursor="hand2")
        self.user_username.pack(side="right", padx=(0, 10))

        self._draw_avatar()

    def _draw_avatar(self):
        size = 44
        self.user_avatar.delete("all")
        self.user_avatar.create_oval(2, 2, size - 2, size - 2, fill=GREEN_BG, outline="")
        initial = (self.user.get("username") or "?").strip()[:2].upper() or "?"
        self.user_avatar.create_text(size // 2, size // 2, text=initial, font=("Arial", 18, "bold"), fill=DARK_BLUE_BG)

    def _parent_frame(self):
        self.main_panel = tk.Frame(self.user_window, bg=PRIMARY_BG)
        self.main_panel.pack(fill="both", expand=True)

        self._left_frame()
        self._left_panel_border()
        self._right_frame()

    def _left_frame(self):
        self.left_panel = tk.Frame(self.main_panel, bg=PRIMARY_BG, width=300)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.minimize_panel = tk.Button(self.left_panel, text="<", font=("Arial", 12), width=3, cursor="hand2",  bg=PRIMARY_BG, fg=PRIMARY_FG)
        self.minimize_panel.pack(anchor="e", padx=(0, 20), pady=(20, 0))
        self.dashboard_btn = tk.Button(self.left_panel, text=NAV_LABELS["dashboard_btn"][0], **self.btn_config)
        self.dashboard_btn.pack(pady=(50, 0), padx=(80, 0))
        self.browse_equipment_btn = tk.Button(self.left_panel,text=NAV_LABELS["browse_equipment_btn"][0], **self.btn_config)
        self.browse_equipment_btn.pack(pady=(50, 0))
        self.reservation_btn = tk.Button(self.left_panel, text=NAV_LABELS["reservation_btn"][0],**self.btn_config)
        self.reservation_btn.pack(pady=(50, 0))
        self.notification_btn = tk.Button(self.left_panel, text=NAV_LABELS["notification_btn"][0],**self.btn_config)
        self.notification_btn.pack(pady=(50, 0))
        self.profile_btn = tk.Button(self.left_panel, text=NAV_LABELS["profile_btn"][0],**self.btn_config)
        self.profile_btn.pack(pady=(50, 0))
        self.logout_btn = tk.Button(self.left_panel,
        text=NAV_LABELS["logout_btn"][0], **self.btn_config, command = self.logout)
        self.logout_btn.pack(pady=(50, 0))

        self.minimize_panel.bind("<Button-1>", lambda e: self.toggle_sidebar())
        self.dashboard_btn.bind("<Button-1>", self._on_nav_click)
        self.browse_equipment_btn.bind("<Button-1>", self._on_nav_click)
        self.reservation_btn.bind("<Button-1>", self._on_nav_click)
        self.notification_btn.bind("<Button-1>", self._on_nav_click)
        self.profile_btn.bind("<Button-1>", self._on_nav_click)
        self.user_avatar.bind("<Button-1>", lambda e: self._show_profile_page())
        self.user_username.bind("<Button-1>", lambda e: self._show_profile_page())

    @staticmethod
    def _button_style():
        return {"font": BTN_FONT, "width": BTN_WIDTH, "cursor": BTN_CURSOR, "bg": PRIMARY_BG, "fg": PRIMARY_FG,  "activebackground": PRIMARY_BG, "activeforeground": PRIMARY_FG,}

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
                btn.config(bg=PRIMARY_BG)
            clicked_button.config(bg=SECONDARY_BG)

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
            btn.config(bg=PRIMARY_BG)

        if self.active_btn is None:
            return

        if self.is_left_panel_minimize:
            self.active_btn.config(bg=SECONDARY_BG)
        else:
            self.active_btn.pack_configure(padx=(80, 0))

    def _loops_btn(self):
        for btn in (self.dashboard_btn,self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn):
            btn.pack_configure(padx=(0, 0))

    def _right_frame(self):
        self.right_panel = tk.Frame(self.main_panel, bg=PRIMARY_BG)
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._show_dashboard()

    def _show_dashboard(self):
        self._clear_right_panel()

        self.user_window.title(f"{W_DASHBOARD_TITLE} - {APP_NAME}")
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
        self.cards_frame = tk.Frame(self.right_panel, bg=PRIMARY_BG)
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
        self._create_card(self.cards_frame, "Due Soon / Overdue", str(summary["due_soon"]), row=2, column=0)

    @staticmethod
    def _create_card(parent, title, value, row, column):
        card = tk.Frame(parent, bg=SECONDARY_BG, cursor="no", height=180)
        card.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")
        card.grid_propagate(False)

        value_label = tk.Label(card, text=value, font=("Arial", 20, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG)
        value_label.pack(pady=(70, 10))
        title_label = tk.Label(card, text=title, font=("Arial", 24), bg=SECONDARY_BG, fg=MUTED_FG)
        title_label.pack(pady=(30, 10))

    def _show_equipment_page(self):
        self.user_window.title(f"{W_BROWSE_EQUIP_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        BrowseEquipmentPage(self.right_panel, self.colors, self.user["id"])

    def _show_reservation_page(self, tab=None):
        self.user_window.title(f"{W_RESERVATION_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        ReservationPage(self.right_panel, self.colors, self.user, initial_tab=tab or "pending")

    def _show_notification_page(self):
        self.user_window.title(f"{W_NOTIFICATION_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        NotificationPage(self.right_panel, self.colors, self.user)

    def _show_profile_page(self):
        self.user_window.title(f"{W_PROFILE_TITLE} - {APP_NAME}")
        self._clear_right_panel()
        self.active_btn = self.profile_btn
        self._highlight_active_button()

        if not self.is_left_panel_minimize:
            self._loops_btn()
            self.profile_btn.pack(padx=(80, 0))

        ProfilePage(self.right_panel, self.colors, self.user, self._on_username_updated, self._go_to_reservation)

    def _on_username_updated(self, new_username):
        self.user["username"] = new_username
        self.user_username.config(text=new_username)
        self._draw_avatar()

    def _update_nav_labels(self, minimized):
        index = 1 if minimized else 0
        for attr_name, labels in NAV_LABELS.items():
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
        self.dashboard_btn, self.browse_equipment_btn, self.reservation_btn, self.notification_btn, self.profile_btn, self.logout_btn):
            btn.config(width=BTN_WIDTH, bg=PRIMARY_BG)

    def _left_panel_border(self):
        self.left_panel_right_border = tk.Frame(self.main_panel, bg=WHITE_BG, width=1)
        self.left_panel_right_border.pack(side="left", fill="y")

    def _clear_right_panel(self):
        for widget in self.right_panel.winfo_children():
            widget.destroy()

    def logout(self):
        logout_question = messagebox.askyesno("Confirm Logout", "Are you sure to logout?")

        if logout_question:
            clear_session()
            self._cancel_ban_check()
            self.user_window.destroy()

            from Authentication.login import LoginWindow
            LoginWindow()

    def _start_ban_check(self):
        # noinspection PyTypeChecker
        self._ban_after_id = self.user_window.after(BAN_CHECK_MS, self._check_ban)

    def _check_ban(self):
        if not self.user_window.winfo_exists():
            return
        threading.Thread(target=self._ban_worker, daemon=True).start()

    def _ban_worker(self):
        try:
            user = get_user_by_id(self.user["id"])
        except (httpx.HTTPError, OSError):
            user = None
        try:
            # noinspection PyTypeChecker
            self.user_window.after(0, lambda: self._apply_ban_result(user))
        except (tk.TclError, RuntimeError):
            pass

    def _apply_ban_result(self, user):
        if not self.user_window.winfo_exists():
            return

        if user and user.get("is_banned"):
            self._force_logout()
            return

        # noinspection PyTypeChecker
        self._ban_after_id = self.user_window.after(BAN_CHECK_MS, self._check_ban)

    def _cancel_ban_check(self):
        after_id = getattr(self, "_ban_after_id", None)
        if after_id:
            try:
                self.user_window.after_cancel(after_id)
            except tk.TclError:
                pass
            self._ban_after_id = None

    def _force_logout(self):
        messagebox.showinfo("Account Banned", "Your account has been banned. You will be logged out.")
        clear_session()
        self._cancel_ban_check()
        self.user_window.destroy()

        from Authentication.login import LoginWindow
        LoginWindow()

    def _go_to_reservation(self, tab="pending"):
        self.active_btn = self.reservation_btn
        self._highlight_active_button()
        self._show_reservation_page(tab)