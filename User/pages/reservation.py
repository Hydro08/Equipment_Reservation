import tkinter as tk
import threading

from datetime import date
from tkinter import messagebox
from Authentication.auth_service import get_user_reservations, cancel_reservation, request_return

ITEMS_PER_PAGE = 5
DUE_SOON_DAYS = 1

class ReservationPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, color, user):
        self.parent = parent
        self.colors = color
        self.user = user
        self.current_page = 0

        self._build_ui()

    def _build_ui(self):
        self.reservation_panel = tk.Frame(self.parent, bg="#1E293B")
        self.reservation_panel.pack(fill="both", expand=True)

        self.reservation_title = tk.Label(self.reservation_panel, text="Reservation", font=("Arial", 24), **self.colors)
        self.reservation_title.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.reservation_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_reservation_data, daemon=True).start()

    def _fetch_reservation_data(self):
        reservations = get_user_reservations(self.user['id'])

        self.reservation_panel.after(0, self._render_reservation, reservations)

    def _render_reservation(self, summary):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_reservations = summary

        self.content_frame = tk.Frame(self.reservation_panel, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.current_page = 0
        self._render_page()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_page(self):
        self._clear_content()

        if not self.all_reservations:
            empty_label = tk.Label(self.content_frame, text="No reservations yet.", font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg, height=50)
            empty_label.pack(pady=20)
            return

        start_index = self.current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        page_items = self.all_reservations[start_index:end_index]

        for reservation in page_items:
            self.create_reservation_row(reservation)

        self._pagination_controls()

    def create_reservation_row(self, reservation):
        bg = "#334155"
        muted = "#94A3B8"

        row = tk.Frame(self.content_frame, bg=bg)
        row.pack(fill="x", padx=10, pady=6)

        equipment_data = reservation.get("equipment") or {}
        equipment_name = equipment_data.get("name", "Unknown Equipment")
        category_name = (equipment_data.get("categories") or {}).get("name", "N/A")
        department_name = (equipment_data.get("departments") or {}).get("name", "N/A")
        status = reservation.get("status", "Pending")

        content = tk.Frame(row, bg=bg)
        content.pack(fill="x", padx=15, pady=15)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, minsize=260)

        tk.Label(content, text=f"Department: {department_name}", font=("Arial", 11), bg=bg, fg=muted, anchor="w").grid(row=0, column=0, sticky="w")
        tk.Label(content, text=f"Category: {category_name}", font=("Arial", 11), bg=bg, fg=muted, anchor="w").grid(row=1, column=0, sticky="w")
        tk.Label(content, text=f"Equipment: {equipment_name}", font=("Arial", 14), bg=bg, fg=muted, anchor="w").grid(row=2, column=0, sticky="w")

        status_display = "Borrowed" if status == "Approved" else status
        status_color = {
            "Pending": "#FBBF24",
            "Borrowed": "#4ADE80",
            "Return Pending": "#FBBF24",
        }.get(status_display, muted)

        if status == "Approved":
            tk.Label(content, text=status_display, font=("Arial", 12, "bold"), bg=bg, fg=status_color, anchor="w").grid(row=0, column=1, sticky="w", padx=20)

            return_date_display = self._format_display_date(reservation.get("return_date"))
            tk.Label(content, text=f"Return Date: {return_date_display}", font=("Arial", 11), bg=bg, fg=muted, anchor="w").grid(row=1, column=1, sticky="w", padx=20)

            due_badge = self._get_due_badge(reservation.get("return_date"))
            if due_badge:
                badge_text, badge_color = due_badge
                tk.Label(content, text=badge_text, font=("Arial", 11, "bold"), bg=bg, fg=badge_color, anchor="w").grid(row=2, column=1, sticky="w", padx=20)
        else:
            tk.Label(content, text=status_display, font=("Arial", 12, "bold"), bg=bg, fg=status_color, anchor="w").grid(row=1, column=1, sticky="w", padx=20)

        if status == "Pending":
            tk.Button(content, text="Cancel", font=("Arial", 11, "bold"), bg="#F87171", fg="#0F172A", cursor="hand2", bd=0, padx=12, pady=4, command=lambda: self._handle_cancel(reservation)).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))
        elif status == "Approved":
            tk.Button(content, text="Return", font=("Arial", 11, "bold"), bg="#3AFD50", fg="#0F172A", cursor="hand2", bd=0, padx=12, pady=4, command=lambda: self._handle_return(reservation)).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))
        elif status == "Return Pending":
            tk.Label(content, text="Awaiting confirmation", font=("Arial", 10, "italic"), bg=bg, fg=muted).grid(row=0, column=2, rowspan=3, sticky="e", padx=(20, 0))

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
            return "Overdue", "#F87171"
        elif days_left == 0:
            return "Due Today", "#FBBF24"
        elif days_left <= DUE_SOON_DAYS:
            day_label = "day" if days_left == 1 else "days"
            return f"Due: {days_left} {day_label}", "#FBBF24"

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
        total_items = len(self.all_reservations)
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1
        self._render_page()

    def _pagination_controls(self):
        total_items = len(self.all_reservations)
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg=self.primary_fg,
                 cursor="hand2", bd=0, padx=15, pady=5,
                 state="normal" if self.current_page > 0 else "disabled",
                 command=self._go_previous_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12),
                bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg=self.primary_fg,
                 cursor="hand2", bd=0, padx=15, pady=5,
                 state="normal" if self.current_page < total_pages - 1 else "disabled",
                 command=self._go_next_page).pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_page()
    def _go_previous_page(self):
        self.current_page -= 1
        self._render_page()