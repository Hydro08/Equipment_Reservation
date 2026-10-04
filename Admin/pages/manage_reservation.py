import tkinter as tk
import threading

from datetime import date
from tkinter import messagebox
from Admin.pages.reservation_calendar import ReservationCalendar

from Authentication.auth_service import (
    get_pending_reservation,
    update_reservation_status,
    get_pending_returns,
    confirm_return,
    reject_return,
    get_available_equipment,
    get_borrowed_reservations,
    get_reservation_report
)

COLUMNS = 3
ROWS_PER_PAGE = 3
ITEMS_PER_PAGE = COLUMNS * ROWS_PER_PAGE

class ManageReservationPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    card_bg = "#334155"
    muted_fg = "#94A3B8"
    green = "#4ADE80"
    red = "#F87171"
    yellow = "#FBBF24"
    dark_fg = "#0F172A"

    active_tab_bg = "#4ADE80"
    active_tab_fg = "#0F172A"
    inactive_tab_bg = "#334155"
    inactive_tab_fg = "#FFFFFF"

    TABS = [
        ("request", "Manage Request", "No pending reservations."),
        ("return", "Manage Returning", "No pending returns."),
        ("available", "Available Equipment", "No available equipment."),
        ("borrowed", "Borrowed Equipment", "No borrowed equipment."),
        ("calendar", "Calendar", "No Reservation.")
    ]

    SEARCHABLE = {"request", "available", "borrowed"}

    def __init__(self, parent, colors, initial_tab="request"):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.mode = initial_tab
        self.current_data = []
        self.filtered_data = []

        self.fetchers = {
            "request": get_pending_reservation,
            "return": get_pending_returns,
            "available": get_available_equipment,
            "borrowed": get_borrowed_reservations,
            "calendar": lambda: get_reservation_report(None)
        }
        self.card_builders = {
            "request": self._create_reservation_card,
            "return": self._create_reservation_card,
            "available": self._create_available_card,
            "borrowed": self._create_borrowed_card
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

        self._build_search_bar()

        self.body_frame = tk.Frame(self.manage_reservation_panel, bg=self.primary_bg)
        self.body_frame.pack(fill="both", expand=True)

        self.content_frame = None
        self.loading_label = None
        self.grid_frame = None

        self._switch_tab(self.mode)

    def _build_search_bar(self):
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        self._search_visible = False

        self.search_frame = tk.Frame(self.manage_reservation_panel, bg=self.primary_bg)

        tk.Label(self.search_frame, text="🔍", font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg).pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, font=("Arial", 13), width=40, bg=self.card_bg, fg=self.primary_fg, insertbackground=self.primary_fg, relief="flat", bd=0)
        self.search_entry.pack(side="left", ipady=6, ipadx=6)
        self.search_entry.bind("<Control-BackSpace>", lambda e: (self.search_entry.delete(0, tk.END), "break")[1])

        tk.Button(self.search_frame, text="X", font=("Arial", 11, "bold"), bg=self.card_bg, fg=self.primary_fg, cursor="hand2", bd=0, padx=10, pady=4, command=lambda: self.search_var.set("")).pack(side="left", padx=(6, 0))

    def _update_search_visibility(self):
        should_show = self.mode in self.SEARCHABLE
        if should_show and not self._search_visible:
            self.search_frame.pack(before=self.body_frame, pady=(15, 0))
            self._search_visible = True
        elif not should_show and self._search_visible:
            self.search_frame.pack_forget()
            self._search_visible = False

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

        self.search_var.set("")
        self._update_search_visibility()

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
        self.filtered_data = self._apply_filter(data)

        self.content_frame = tk.Frame(self.body_frame, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._render_page()

    def _search_text_for(self, item):
        if self.mode == "available":
            return " ".join([
                str(item.get("name", "")),
                str((item.get("departments") or {}).get("name", "")),
                str((item.get("categories") or {}).get("name", ""))
            ])
        return " ".join([
            str((item.get("users") or {}).get("username", "")),
            str((item.get("equipment") or {}).get("name", ""))
        ])

    def _apply_filter(self, data):
        query = self.search_var.get().strip().lower()
        if self.mode not in self.SEARCHABLE or not query:
            return data
        return [item for item in data if query in self._search_text_for(item).lower()]

    def _on_search_changed(self, *_):
        if not self.content_frame or not self.content_frame.winfo_exists():
            return
        self.filtered_data = self._apply_filter(self.current_data)
        self.current_page = 0
        self._render_page()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _render_page(self):
        self._clear_content()

        if self.mode == "calendar":
            ReservationCalendar(self.content_frame, self.current_data)
            return

        data = self.filtered_data

        if not data:
            searching = self.mode in self.SEARCHABLE and self.search_var.get().strip()
            text = "No result found." if searching else self.empty_texts[self.mode]
            tk.Label(self.content_frame, text=text, font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg, height=50).pack(pady=20)
            return

        start_index = self.current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

        self.grid_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        self.grid_frame.pack(fill="x")
        for col in range(COLUMNS):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform="card")

        build_card = self.card_builders[self.mode]
        for i, item in enumerate(data[start_index:end_index]):
            card = tk.Frame(self.grid_frame, bg=self.card_bg)
            card.grid(row=i // COLUMNS, column=i % COLUMNS, padx=8, pady=8, sticky="nsew")
            build_card(card, item)

        self._pagination_controls(len(data))

    def _card_info_frame(self, card):
        info = tk.Frame(card, bg=self.card_bg)
        info.pack(fill="x", padx=15, pady=(15, 8))
        return info

    def _info_label(self, parent, text, font, fg):
        tk.Label(parent, text=text, font=font, bg=self.card_bg, fg=fg, anchor="w", justify="left", wraplength=380).pack(fill="x")

    def _create_reservation_card(self, card, reservation):
        username = (reservation.get("users") or {}).get("username", "Unknown User")
        equipment_name = (reservation.get("equipment") or {}).get("name", "Unknown Equipment")

        info = self._card_info_frame(card)
        self._info_label(info, username, ("Arial", 16, "bold"), self.primary_fg)
        self._info_label(info, f"Equipment: {equipment_name}", ("Arial", 12), self.muted_fg)
        self._info_label(info, f"Return: {reservation.get('return_date', 'N/A')}", ("Arial", 11), self.muted_fg)

        button_frame = tk.Frame(card, bg=self.card_bg)
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        if self.mode == "request":
            tk.Button(button_frame, text="X", font=("Arial", 14, "bold"), bg=self.red, fg=self.dark_fg, cursor="hand2", bd=0, width=4, pady=3, command=lambda: self.handle_decision(reservation, "Rejected")).pack(side="right", padx=(8, 0))
            tk.Button(button_frame, text="✓", font=("Arial", 14, "bold"), bg=self.green, fg=self.dark_fg, cursor="hand2", bd=0, width=4, pady=3, command=lambda: self.handle_decision(reservation, "Approved")).pack(side="right")
        else:
            tk.Button(button_frame, text="Not Yet Returned", font=("Arial", 11, "bold"), bg=self.red, fg=self.dark_fg, cursor="hand2", bd=0, padx=10, pady=5, command=lambda: self.handle_return_decision(reservation, False)).pack(side="right", padx=(8, 0))
            tk.Button(button_frame, text="Confirm Return", font=("Arial", 11, "bold"), bg=self.green, fg=self.dark_fg, cursor="hand2", bd=0, padx=10, pady=5, command=lambda: self.handle_return_decision(reservation, True)).pack(side="right")

    def _create_available_card(self, card, item):
        category_name = (item.get("categories") or {}).get("name", "N/A")
        department_name = (item.get("departments") or {}).get("name", "N/A")

        info = self._card_info_frame(card)
        self._info_label(info, item.get("name", "Unknown"), ("Arial", 16, "bold"), self.primary_fg)
        self._info_label(info, f"Department: {department_name}", ("Arial", 12), self.muted_fg)
        self._info_label(info, f"Category: {category_name}", ("Arial", 12), self.muted_fg)

        tk.Label(card, text="Available", font=("Arial", 13, "bold"), bg=self.card_bg, fg=self.green, anchor="e").pack(fill="x", padx=15, pady=(0, 15))

    def _create_borrowed_card(self, card, reservation):
        username = (reservation.get("users") or {}).get("username", "Unknown User")
        equipment_name = (reservation.get("equipment") or {}).get("name", "Unknown Equipment")

        info = self._card_info_frame(card)
        self._info_label(info, username, ("Arial", 16, "bold"), self.primary_fg)
        self._info_label(info, f"Equipment: {equipment_name}", ("Arial", 12), self.muted_fg)
        self._info_label(info, f"Due: {reservation.get('return_date', 'N/A')}", ("Arial", 11), self.muted_fg)

        badge = self._due_badge(reservation.get("return_date"))
        text, color = badge if badge else ("", self.muted_fg)
        tk.Label(card, text=text, font=("Arial", 13, "bold"), bg=self.card_bg, fg=color, anchor="e").pack(fill="x", padx=15, pady=(0, 15))

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
        self.filtered_data = self._apply_filter(self.current_data)

        total_pages = max(1, -(-len(self.filtered_data) // ITEMS_PER_PAGE))
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1

        self._render_page()

    def  _pagination_controls(self, total_items):
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))

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