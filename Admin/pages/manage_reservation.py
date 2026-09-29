import tkinter as tk
import threading

from datetime import date
from tkinter import messagebox

from Authentication.auth_service import (
    get_pending_reservation,
    update_reservation_status,
    get_pending_returns,
    confirm_return,
    reject_return,
    get_available_equipment,
    get_borrowed_reservations,
)

ITEMS_PER_PAGE = 4

class ManageReservationPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    active_tab_bg = "#4ADE80"
    active_tab_fg = "#0F172A"
    inactive_tab_bg = "#334155"
    inactive_tab_fg = "#FFFFFF"

    TABS = [
        ("request", "Manage Request", "No pending reservations."),
        ("return", "Manage Returning", "No pending returns."),
        ("available", "Available Equipment", "No available equipment."),
        ("borrowed", "Borrowed Equipment", "No borrowed equipment."),
    ]

    def __init__(self, parent, colors, initial_tab="request"):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.mode = initial_tab
        self.current_data = []

        self.fetchers = {
            "request": get_pending_reservation,
            "return": get_pending_returns,
            "available": get_available_equipment,
            "borrowed": get_borrowed_reservations,
        }
        self.empty_texts = {mode: empty for mode, _, empty in self.TABS}

        self._build_ui()

    def _build_ui(self):
        self.manage_reservation_panel = tk.Frame(self.parent, bg=self.primary_bg)
        self.manage_reservation_panel.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.manage_reservation_panel, text="Manage Reservation", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.tab_frame = tk.Frame(self.manage_reservation_panel, bg=self.primary_bg)
        self.tab_frame.pack(pady=(15, 0))

        self.tab_buttons = {}
        for mode, label, _ in self.TABS:
            btn = tk.Button(self.tab_frame, text=label, font=("Arial", 12, "bold"), cursor="hand2", bd=0, padx=20, pady=8, command=lambda m=mode: self._switch_tab(m))
            btn.pack(side="left", padx=5)
            self.tab_buttons[mode] = btn

        self.body_frame = tk.Frame(self.manage_reservation_panel, bg=self.primary_bg)
        self.body_frame.pack(fill="both", expand=True)

        self.content_frame = None
        self.loading_label = None

        self._switch_tab(self.mode)

    def _update_tab_styles(self):
        for mode, btn in self.tab_buttons.items():
            if mode == self.mode:
                btn.config(bg=self.active_tab_bg, fg=self.active_tab_fg)
            else:
                btn.config(bg=self.inactive_tab_bg, fg=self.inactive_tab_fg)

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
        data = self.fetchers[mode]()
        self.manage_reservation_panel.after(0, self._on_data_fetched, mode, data)

    def _on_data_fetched(self, mode, data):
        if mode != self.mode:
            return
        if not self.loading_label or not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.current_data = data

        self.content_frame = tk.Frame(self.body_frame, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._render_page()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_page(self):
        self._clear_content()
        data = self.current_data

        if not data:
            tk.Label(self.content_frame, text=self.empty_texts[self.mode], font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg, height=50).pack(pady=20)
            return

        items_per_page = 5 if self.mode == "available" else ITEMS_PER_PAGE

        start_index = self.current_page * items_per_page
        end_index = start_index + items_per_page

        for item in data[start_index:end_index]:
            if self.mode == "available":
                self._create_available_row(item)
            elif self.mode == "borrowed":
                self._create_borrowed_row(item)
            else:
                self._create_reservation_row(item)

        self._pagination_controls(len(data))

    def _create_reservation_row(self, reservation):
        row = tk.Frame(self.content_frame, bg="#334155")
        row.pack(fill="x", padx=10, pady=6)

        user_data = reservation.get("users")
        username = user_data.get("username") if user_data else "Unknown User"

        equipment_data = reservation.get("equipment")
        equipment_name = equipment_data.get("name") if equipment_data else "Unknown Equipment"

        info_frame = tk.Frame(row, bg="#334155")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        tk.Label(info_frame, text=username, font=("Arial", 16, "bold"), bg="#334155", fg=self.primary_fg, anchor="w").pack(fill="x")
        tk.Label(info_frame, text=f"Equipment: {equipment_name}", font=("Arial", 12), bg="#334155", fg="#94A3B8", anchor="w").pack(fill="x")

        dates_text = f"Reserved: {reservation.get('reserved_date', 'N/A')} | Return: {reservation.get('return_date', 'N/A')}"
        tk.Label(info_frame, text=dates_text, font=("Arial", 11), bg="#334155", fg="#94A3B8", anchor="w").pack(fill="x")

        button_frame = tk.Frame(row, bg="#334155")
        button_frame.pack(side="right", padx=15, pady=15)

        if self.mode == "request":
            tk.Button(button_frame, text="Accept", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self.handle_decision(reservation, "Approved")).pack(side="left", padx=5)

            tk.Button(button_frame, text="Reject", font=("Arial", 12, "bold"), bg="#F87171", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5,command=lambda: self.handle_decision(reservation, "Rejected")).pack(side="left", padx=5)
        else:
            tk.Button(button_frame, text="Confirm Return", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self.handle_return_decision(reservation, True)).pack(side="left", padx=5)
            tk.Button(button_frame, text="Not Yet Returned", font=("Arial", 12, "bold"), bg="#F87171", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self.handle_return_decision(reservation, False)).pack(side="left", padx=5)

    def _create_available_row(self, item):
        row = tk.Frame(self.content_frame, bg="#334155")
        row.pack(fill="x", padx=10, pady=6)

        category_name = (item.get("categories") or {}).get("name", "N/A")
        department_name = (item.get("departments") or {}).get("name", "N/A")

        info_frame = tk.Frame(row, bg="#334155")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        tk.Label(info_frame, text=item.get("name", "Unknown Equipment"), font=("Arial", 16, "bold"), bg="#334155", fg=self.primary_fg, anchor="w").pack(fill="x")
        tk.Label(info_frame, text=f"Department: {department_name}  |  Category: {category_name}", font=("Arial", 12), bg="#334155", fg="#94A3B8", anchor="w").pack(fill="x")

        tk.Label(row, text="Available", font=("Arial", 13, "bold"), bg="#334155", fg="#4ADE80").pack(side="right", padx=25)

    def _create_borrowed_row(self, reservation):
        row = tk.Frame(self.content_frame, bg="#334155")
        row.pack(fill="x", padx=10, pady=6)

        user_data = reservation.get("users")
        username = user_data.get("username") if user_data else "Unknown User"

        equipment_data = reservation.get("equipment")
        equipment_name = equipment_data.get("name") if equipment_data else "Unknown Equipment"

        info_frame = tk.Frame(row, bg="#334155")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        tk.Label(info_frame, text=username, font=("Arial", 16, "bold"), bg="#334155", fg=self.primary_fg, anchor="w").pack(fill="x")
        tk.Label(info_frame, text=f"Equipment: {equipment_name}", font=("Arial", 12), bg="#334155", fg="#94A3B8", anchor="w").pack(fill="x")

        dates_text = f"Borrowed: {reservation.get('reserved_date', 'N/A')} | Due: {reservation.get('return_date', 'N/A')}"
        tk.Label(info_frame, text=dates_text, font=("Arial", 11),bg="#334155", fg="#94A3B8", anchor="w").pack(fill="x")

        badge = self._due_badge(reservation.get("return_date"))
        if badge:
            text, color = badge
            tk.Label(row, text=text, font=("Arial", 13, "bold"),bg="#334155", fg=color).pack(side="right", padx=25)

    @staticmethod
    def _due_badge(return_date_str):
        if not return_date_str:
            return None
        try:
            due = date.fromisoformat(str(return_date_str)[:10])
        except ValueError:
            return None

        days_left = (due - date.today()).days
        if days_left < 0:
            return "Overdue", "#F87171"
        if days_left == 0:
            return "Due Today", "#FBBF24"
        if days_left <= 1:
            return "Due: 1 day", "#FBBF24"
        return None

    def handle_decision(self, reservation, new_status):
        if not messagebox.askyesno("Confirm", f"{new_status} this reservation?"):
            return

        if update_reservation_status(reservation["id"], new_status):
            messagebox.showinfo("Success", f"Reservation {new_status.lower()}.")
            self._refresh_after_action()
        else:
            messagebox.showerror("Error", "Failed to update reservation status.")

    def handle_return_decision(self, reservation, confirmed):
        if confirmed:
            message = "Confirm that this equipment has been physically returned?"
        else:
            message = "Mark this as NOT yet returned? This will move the reservation back to Borrowed."

        if not messagebox.askyesno("Confirm", message):
            return

        success = confirm_return(reservation["id"]) if confirmed else reject_return(reservation["id"])

        if success:
            messagebox.showinfo("Success", "Return confirmed." if confirmed else "Marked as not yet returned.")
            self._refresh_after_action()
        else:
            messagebox.showerror("Error", "Failed to update return status.")

    def _refresh_after_action(self):
        self.current_data = self.fetchers[self.mode]()

        total_pages = max(1, -(-len(self.current_data) // ITEMS_PER_PAGE))
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1

        self._render_page()

    def _pagination_controls(self, total_items):
        items_per_pages = 5 if self.mode == "available" else ITEMS_PER_PAGE
        total_pages = max(1, -(-total_items // items_per_pages))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg=self.primary_fg, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg=self.primary_fg, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page).pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_page()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_page()