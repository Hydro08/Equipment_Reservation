import tkinter as tk
import threading

from tkinter import messagebox

from Authentication.auth_service import get_pending_reservation, update_reservation_status

ITEMS_PER_PAGE = 6

class ManageReservationPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0

        self._build_ui()

    def _build_ui(self):
        self.main_frame = tk.Frame(self.parent, bg=self.primary_bg)
        self.main_frame.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.main_frame, text="Manage Reservation", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_reservation_data, daemon=True).start()

    def _fetch_reservation_data(self):
        reservations = get_pending_reservation()
        self.main_frame.after(0, self._render_reservations, reservations)

    def _render_reservations(self, reservations):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_reservations = reservations

        self.content_frame = tk.Frame(self.main_frame, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.current_page = 0
        self._render_page()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_page(self):
        self._clear_content()

        if not self.all_reservations:
            empty_label = tk.Label(self.content_frame, text="No pending reservations.", font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg, height=50)
            empty_label.pack(pady=20)
            return

        start_index = self.current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
        page_item = self.all_reservations[start_index:end_index]

        for reservation in page_item:
            self._create_reservation_row(reservation)

        self._pagination_controls()

    def _create_reservation_row(self, reservation):
        row = tk.Frame(self.content_frame, bg="#334155")
        row.pack(fill="x", padx=10, pady=6)

        user_data = reservation.get("users")
        username = user_data.get("username") if user_data else "Unknown User"

        equipment_data = reservation.get("equipment")
        equipment_name = equipment_data.get("name") if equipment_data else "Unknown Equipment"

        info_frame = tk.Frame(row, bg="#334155")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=15)

        user_label = tk.Label(info_frame, text=username, font=("Arial", 16, "bold"), bg="#334155", fg=self.primary_fg, anchor="w")
        user_label.pack(fill="x")

        equipment_label = tk.Label(info_frame, text=f"Equipment: {equipment_name}", font=("Arial", 12), bg="#334155", fg="#94A3B8", anchor="w")
        equipment_label.pack(fill="x")

        dates_text = f"Reserved: {reservation.get('reserved_date', 'N/A')} | Return: {reservation.get('return_date', 'N/A')}"
        dates_label = tk.Label(info_frame, text=dates_text, font=("Arial", 11), bg="#334155", fg="#94A3B8", anchor="w")
        dates_label.pack(fill="x")

        button_frame = tk.Frame(row, bg="#334155")
        button_frame.pack(side="right", padx=15, pady=15)

        accept_btn = tk.Button(button_frame, text="Accept", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self.handle_decision(reservation, "Approved"))
        accept_btn.pack(side="left", padx=5)

        reject_btn = tk.Button(button_frame, text="Reject", font=("Arial", 12, "bold"), bg="#F87171", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self.handle_decision(reservation, "Rejected"))
        reject_btn.pack(side="left", padx=5)

    def handle_decision(self, reservation, new_status):
        confirm = messagebox.askyesno(
            "Confirm", f"{new_status} this reservation?"
        )

        if not confirm:
            return

        success = update_reservation_status(reservation["id"], new_status)

        if success:
            messagebox.showinfo("Success", f"Reservation {new_status.lower()}.")
            self._refresh_after_action()
        else:
            messagebox.showerror("Error", "Failed to update reservation status.")

    def _refresh_after_action(self):
        self.all_reservations = get_pending_reservation()

        total_pages = max(1, -(-len(self.all_reservations) // ITEMS_PER_PAGE))

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

        prev_btn = tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg=self.primary_fg, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page)
        prev_btn.pack(side="left", padx=5)

        page_label = tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8")
        page_label.pack(side="left", padx=15)

        next_btn = tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg=self.primary_fg, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page)
        next_btn.pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_page()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_page()