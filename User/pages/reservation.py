import tkinter as tk
import threading

from datetime import date
from tkinter import messagebox
from Authentication.auth_service import get_user_reservations, cancel_reservation, request_return
from Config.colors import PRIMARY_BG, SECONDARY_BG, RED_BG, PRIMARY_FG, MUTED_FG, STATUS_WARNING, ACTIVE_TAB_BG, ACTIVE_TAB_FG, INACTIVE_TAB_BG, INACTIVE_TAB_FG, DARK_FG, LIGHT_GREEN, STATUS_SUCCESS, STATUS_ERROR
from Config.layout import ITEMS_PER_PAGE
from Config.settings import DUE_SOON_DAYS

class ReservationPage:

    TABS = [
        ("pending", "Pending Request", "No pending reservation."),
        ("borrowed", "Borrowed Equipment", "No borrowed equipment.")
    ]

    TAB_STATUSES = {
        "pending": ("Pending",),
        "borrowed": ("Approved", "Return Pending"),
    }

    def __init__(self, parent, color, user, initial_tab="pending"):
        self.parent = parent
        self.colors = color
        self.user = user
        self.mode = initial_tab
        self.all_reservations = []
        self.current_data = []
        self.current_page = 0
        self.empty_texts = {mode: empty for mode, _, empty in self.TABS}

        self._build_ui()

    def _build_ui(self):
        self.reservation_panel = tk.Frame(self.parent, bg=PRIMARY_BG)
        self.reservation_panel.pack(fill="both", expand=True)

        self.reservation_title = tk.Label(self.reservation_panel, text="Reservation", font=("Arial", 24), **self.colors)
        self.reservation_title.pack(pady=(20, 0))

        self.tab_frame = tk.Frame(self.reservation_panel, bg=PRIMARY_BG)
        self.tab_frame.pack(pady=(15, 0))

        self.tab_buttons = {}
        for mode, label, _ in self.TABS:
            btn = tk.Button(self.tab_frame, text=label, font=("Arial", 12, "bold"), cursor="hand2", bd=0, padx=20, pady=8, command=lambda m=mode: self._switch_tab(m))
            btn.pack(side="left", padx=5)
            self.tab_buttons[mode] = btn

        self.body_frame = tk.Frame(self.reservation_panel, bg=PRIMARY_BG)
        self.body_frame.pack(fill="both", expand=True)

        self.content_frame = None
        self.loading_label = None

        self._switch_tab(self.mode)

    def _update_tab_styles(self):
        for mode, btn in self.tab_buttons.items():
            if mode == self.mode:
                btn.config(bg=ACTIVE_TAB_BG, fg=ACTIVE_TAB_FG)
            else:
                btn.config(bg=INACTIVE_TAB_BG, fg=INACTIVE_TAB_FG)

    def _switch_tab(self, mode):
        self.mode = mode
        self.current_page = 0
        self._update_tab_styles()
        self._show_loading_and_fetch()

    def _show_loading_and_fetch(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()
        self.content_frame = None

        self.loading_label = tk.Label(self.body_frame, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_data, args=(self.mode,), daemon=True).start()

    def _fetch_data(self, mode):
        data = get_user_reservations(self.user["id"])
        try:
            # noinspection PyTypeChecker
            self.reservation_panel.after(0, lambda: self._on_data_fetched(mode, data))
        except (tk.TclError, RuntimeError):
            pass

    def _filter_current_tab(self):
        statuses = self.TAB_STATUSES[self.mode]
        return [r for r in self.all_reservations if r.get("status") in statuses]

    def _on_data_fetched(self, mode, data):
        if mode != self.mode:
            return
        if not self.loading_label or not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_reservations = data
        self.current_data = self._filter_current_tab()

        self.content_frame = tk.Frame(self.body_frame, bg=PRIMARY_BG)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._render_page()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_page(self):
        self._clear_content()

        if not self.current_data:
            tk.Label(self.content_frame, text=self.empty_texts[self.mode], font=("Arial", 14), bg=PRIMARY_BG, fg=PRIMARY_FG, height=50).pack(pady=20)
            return

        start_index = self.current_page * ITEMS_PER_PAGE
        page_items = self.current_data[start_index:start_index + ITEMS_PER_PAGE]

        for reservation in page_items:
            self.create_reservation_row(reservation)

        self._pagination_controls()

    def create_reservation_row(self, reservation):
        row = tk.Frame(self.content_frame, bg=SECONDARY_BG)
        row.pack(fill="x", padx=10, pady=6)

        equipment_data = reservation.get("equipment") or {}
        equipment_name = equipment_data.get("name", "Unknown Equipment")
        category_name = (equipment_data.get("categories") or {}).get("name", "N/A")
        department_name = (equipment_data.get("departments") or {}).get("name", "N/A")
        status = reservation.get("status", "Pending")

        content = tk.Frame(row, bg=SECONDARY_BG)
        content.pack(fill="x", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, minsize=260)

        tk.Label(content, text=f"Department: {department_name}", font=("Arial", 11), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").grid(row=0, column=0, sticky="w")
        tk.Label(content, text=f"Category: {category_name}", font=("Arial", 11), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").grid(row=1, column=0, sticky="w")
        tk.Label(content, text=f"Equipment: {equipment_name}", font=("Arial", 14), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").grid(row=2, column=0, sticky="w")

        status_display = "Borrowed" if status == "Approved" else status
        status_color = {
            "Pending": STATUS_WARNING,
            "Borrowed": STATUS_SUCCESS,
            "Return Pending": STATUS_WARNING,
        }.get(status_display, MUTED_FG)

        if status == "Approved":
            tk.Label(content, text=status_display, font=("Arial", 12, "bold"), bg=SECONDARY_BG, fg=status_color, anchor="w").grid(row=0, column=1, sticky="w", padx=20)

            return_date_display = self._format_display_date(reservation.get("return_date"))
            tk.Label(content, text=f"Return Date: {return_date_display}", font=("Arial", 11), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").grid(row=1, column=1, sticky="w", padx=20)

            due_badge = self._get_due_badge(reservation.get("return_date"))
            if due_badge:
                badge_text, badge_color = due_badge
                tk.Label(content, text=badge_text, font=("Arial", 11, "bold"), bg=SECONDARY_BG, fg=badge_color, anchor="w").grid(row=2, column=1, sticky="w", padx=20)
        else:
            tk.Label(content, text=status_display, font=("Arial", 12, "bold"), bg=SECONDARY_BG, fg=status_color, anchor="w").grid(row=1, column=1, sticky="w", padx=20)

        if status == "Pending":
            tk.Button(content, text="Cancel", font=("Arial", 11, "bold"), bg=RED_BG, fg=DARK_FG, cursor="hand2", bd=0, padx=12, pady=4, command=lambda: self._handle_cancel(reservation)).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))
        elif status == "Approved":
            tk.Button(content, text="Return", font=("Arial", 11, "bold"), bg=LIGHT_GREEN, fg=DARK_FG, cursor="hand2", bd=0, padx=12, pady=4, command=lambda: self._handle_return(reservation)).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))
        elif status == "Return Pending":
            tk.Label(content, text="Awaiting confirmation", font=("Arial", 10, "italic"), bg=SECONDARY_BG, fg=MUTED_FG).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))

    @staticmethod
    def _format_display_date(return_date_str):
        if not return_date_str:
            return "N/A"
        try:
            parsed = date.fromisoformat(str(return_date_str)[:10])
            return parsed.strftime("%m/%d/%Y")
        except ValueError:
            return str(return_date_str)

    @staticmethod
    def _get_due_badge(return_date_str):
        if not return_date_str:
            return None

        try:
            due_date = date.fromisoformat(str(return_date_str)[:10])
        except ValueError:
            return None

        days_left = (due_date - date.today()).days

        if days_left < 0:
            return "Overdue", STATUS_ERROR
        elif days_left == 0:
            return "Due Today", STATUS_WARNING
        elif days_left <= DUE_SOON_DAYS:
            day_label = "day" if days_left == 1 else "days"
            return f"Due: {days_left} {day_label}", STATUS_WARNING

        return None

    def _handle_cancel(self, reservation):
        if not messagebox.askyesno("Confirm", "Cancel this reservation?"):
            return
        if cancel_reservation(reservation["id"]):
            messagebox.showinfo("Cancelled", "Reservation cancelled.")
            self._refresh_after_action()
        else:
            messagebox.showerror("Error", "Failed to cancel reservation")

    def _handle_return(self, reservation):
        if not messagebox.askyesno("Confirm", "Request return for this equipment? An admin will need to confirm it before it's marked as returned."):
            return
        if request_return(reservation["id"]):
            messagebox.showinfo("Return Requested", "Return requested. Waiting for admin confirmation.")
            self._refresh_after_action()
        else:
            messagebox.showerror("Error", "Failed to request return.")

    def _refresh_after_action(self):
        self.all_reservations = get_user_reservations(self.user["id"])
        self.current_data = self._filter_current_tab()

        total_pages = max(1, -(-len(self.current_data) // ITEMS_PER_PAGE))
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1
        self._render_page()

    def _pagination_controls(self):
        total_items = len(self.current_data)
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=PRIMARY_BG)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=15, pady=5,state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12), bg=PRIMARY_BG, fg=MUTED_FG).pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page).pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_page()
    def _go_previous_page(self):
        self.current_page -= 1
        self._render_page()