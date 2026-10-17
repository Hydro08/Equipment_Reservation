import tkinter as tk
import threading
import string

from datetime import date
from tkinter import messagebox
from Authentication.auth_service import get_all_users, set_user_banned, user_has_borrowed_items, get_user_reservation_history
from Config.colors import PRIMARY_BG, SECONDARY_BG, GREEN_BG, DARK_BLUE_BG, BANNED_BG, RED_BG, PRIMARY_FG, MUTED_FG, STATUS_ERROR, STATUS_WARNING,STATUS_SUCCESS, STATUS_RETURNED,DARK_FG
from Config.layout import USER_COLUMN, USER_PER_PAGE, DETAIL_PANEL_WIDTH
from Config.settings import MAX_WARNINGS, RECENT_LIMIT


class ManageUsersPage:

    FILTERS = [("all", "All"), ("active", "Active"), ("banned", "Banned")]

    def __init__(self, parent, colors, on_detail_toggle=None):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.all_users = []
        self.filter_mode = "all"
        self.selected_letter = "All"
        self.selected_user_id = None
        self.on_detail_toggle = on_detail_toggle

        self._build_ui()

    def _build_ui(self):
        self.page = tk.Frame(self.parent, bg=PRIMARY_BG)
        self.page.pack(fill="both", expand=True)

        self.manage_users_panel = tk.Frame(self.page, bg=PRIMARY_BG)
        self.manage_users_panel.pack(side="left", fill="both", expand=True)

        self.detail_panel = tk.Frame(self.page, bg=SECONDARY_BG, width=DETAIL_PANEL_WIDTH)
        self.detail_panel.pack_propagate(False)

        header = tk.Frame(self.manage_users_panel, bg=PRIMARY_BG)
        header.pack(fill="x", padx=20, pady=(20, 0))
        header.columnconfigure(0, weight=1)

        self.title_label = tk.Label(header, text="Manage Users", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.grid(row=0, column=0, sticky="w")

        self.search_var = tk.StringVar()
        self.search_frame = tk.Frame(header, bg=PRIMARY_BG)
        self.search_frame.grid(row=0, column=1, sticky="e")

        tk.Label(self.search_frame, text="🔍", font=("Arial", 14), bg=PRIMARY_BG, fg=PRIMARY_FG).pack(
            side="left", padx=(0, 8))
        self.search_entry = tk.Entry(self.search_frame, textvariable=self.search_var, width=28, font=("Arial", 12),bg=SECONDARY_BG, fg=PRIMARY_FG, insertbackground=PRIMARY_FG, relief="flat")
        self.search_entry.pack(side="left", ipady=4)

        self.search_entry.bind("<Control-BackSpace>", lambda e: (self.search_entry.delete(0, tk.END), "break")[1])
        # noinspection PyTypeChecker
        self.search_var.trace_add("write", lambda *args: self._on_search_change())

        self._build_tabs()
        self._build_letter_bar()

        self.loading_label = tk.Label(self.manage_users_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_users, daemon=True).start()

    def _build_tabs(self):
        self.tab_frame = tk.Frame(self.manage_users_panel, bg=PRIMARY_BG)
        self.tab_frame.pack(padx=20, pady=(15, 0), anchor="w")

        self.tab_buttons = {}
        for mode, label in self.FILTERS:
            btn = tk.Button(self.tab_frame, text=label, font=("Arial", 12, "bold"), cursor="hand2", bd=0, padx=20, pady=6, command= lambda m=mode: self._set_filter(m))
            btn.pack(side="left", padx=(0, 8))
            self.tab_buttons[mode] = btn
        self._update_tab_styles()

    def _update_tab_styles(self):
        for mode, btn in self.tab_buttons.items():
            if mode == self.filter_mode:
                btn.config(bg=GREEN_BG, fg=DARK_FG)
            else:
                btn.config(bg=SECONDARY_BG, fg=PRIMARY_FG)

    def _set_filter(self, mode):
        self.filter_mode = mode
        self.current_page = 0
        self._update_tab_styles()
        if hasattr(self, "content_frame"):
            self._render_list()

    def _build_letter_bar(self):
        self.letter_frame = tk.Frame(self.manage_users_panel, bg=PRIMARY_BG)
        self.letter_frame.pack(padx=20, pady=(10, 0), anchor="w")

        self.letter_buttons = {}
        for letter in ["All"] + list(string.ascii_uppercase):
            btn = tk.Button(
                self.letter_frame, text=letter, font=("Arial", 10, "bold"),
                cursor="hand2", bd=0, width=4 if letter == "All" else 3, pady=3,
                command=lambda l=letter: self._set_letter(l),
            )
            btn.pack(side="left", padx=1)
            self.letter_buttons[letter] = btn
        self._update_letter_styles()

    def _update_letter_styles(self):
        for letter, btn in self.letter_buttons.items():
            if letter == self.selected_letter:
                btn.config(bg=GREEN_BG, fg=DARK_FG)
            else:
                btn.config(bg=SECONDARY_BG, fg=PRIMARY_FG)

    def _set_letter(self, letter):
        self.selected_letter = letter
        self.current_page = 0
        self._update_letter_styles()
        if hasattr(self, "content_frame"):
            self._render_list()

    def _filtered_users(self):
        q = self.search_var.get().lower()
        result = []
        for u in self.all_users:
            name = u["username"]

            if self.filter_mode == "active" and u.get("is_banned"):
                continue
            if self.filter_mode == "banned" and not u.get("is_banned"):
                continue
            if q and q not in name.lower():
                continue

            if self.selected_letter == "#":
                if name[:1].isalpha():
                    continue
            elif self.selected_letter != "All":
                if not name.upper().startswith(self.selected_letter):
                    continue

            result.append(u)

        return sorted(result, key=lambda user: user["username"].lower())

    def _on_search_change(self):
        self.current_page = 0
        if hasattr(self, "content_frame"):
            self._render_list()

    def _fetch_users(self):
        users = get_all_users()
        try:
            # noinspection PyTypeChecker
            self.manage_users_panel.after(0, lambda: self._render_users(users))
        except (tk.TclError, RuntimeError):
            pass
    def _render_users(self, users):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_users = users

        self.content_frame = tk.Frame(self.manage_users_panel, bg=PRIMARY_BG)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._render_list()

    def _refresh_users(self):
        self.all_users = get_all_users()
        self._render_list()

        if self.selected_user_id:
            user = next((u for u in self.all_users if u["id"] == self.selected_user_id), None)
            if user:
                self._show_user_detail(user)
            else:
                self._close_detail()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    @staticmethod
    def _user_grid(parent):
        frame = tk.Frame(parent, bg=PRIMARY_BG)
        frame.pack(fill="x", padx=10, pady=10)
        for col in range(USER_COLUMN):
            frame.grid_columnconfigure(col, weight=1, uniform="user")
        return frame

    def _render_list(self):
        self._clear_content()

        users = self._filtered_users()

        if not users:
            message = "No users found." if not  self.all_users else "No users match your search."
            tk.Label(self.content_frame, text=message, font=("Arial", 14), bg=PRIMARY_BG, fg=MUTED_FG).pack(pady=20)
            return

        total_pages = max(1, -(- len(users) // USER_PER_PAGE))
        self.current_page = min(self.current_page, total_pages - 1)

        start = self.current_page * USER_PER_PAGE
        page_users = users[start:start + USER_PER_PAGE]

        grid = self._user_grid(self.content_frame)

        row, col = 0, 0
        for user in page_users:
            self._create_user_card(grid, user, row , col)
            col += 1
            if col >= USER_COLUMN:
                col, row=0, row + 1

        self._pagination_controls(total_pages)

    @staticmethod
    def _avatar(parent, name, bg, banned, size=50):
        canvas = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0)
        canvas.create_oval(2, 2, size - 2, size - 2, fill=MUTED_FG if banned else GREEN_BG, outline="")
        initial = (name or "?").strip()[:1].upper() or "?"
        canvas.create_text(size // 2, size // 2, text=initial, font=("Arial", 20, "bold"), fill=DARK_BLUE_BG)
        return canvas

    def _create_user_card(self, parent, user, row, col):
        banned = user.get("is_banned")
        bg = BANNED_BG if banned else SECONDARY_BG

        card = tk.Frame(parent, bg=bg, height=130, highlightbackground=RED_BG if banned else bg, highlightthickness=1)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)

        card.grid_columnconfigure(1, weight=1)
        card.grid_rowconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        avatar = self._avatar(card, user["username"], bg, banned)
        avatar.grid(row=0, column=0, rowspan=2, padx=(15, 12))

        name_label = tk.Label(card, text=user["username"], font=("Arial", 15, "bold"), bg=bg, fg=PRIMARY_FG, anchor="w", justify="left", wraplength=180)
        name_label.grid(row=0, column=1, sticky="sw", padx=(0, 8))
        status_label = tk.Label(card, text="• Banned" if banned else "• Active", font=("Arial", 11), bg=bg, fg=STATUS_ERROR if banned else STATUS_SUCCESS, anchor="w")
        status_label.grid(row=1, column=1, sticky="nw")

        for widget in (card, avatar, name_label, status_label):
            widget.config(cursor="hand2")
            widget.bind("<Button-1>", lambda e, u=user: self._show_user_detail(u))

    def _toggle_ban(self, user, banned):
        if banned and user_has_borrowed_items(user["id"]):
            if not messagebox.askyesno("Confirm Ban", f"{user['username']} still has borrowed equipment. Ban anyway?"):
                return
        else:
            action = "Ban" if banned else "Unban"
            if not messagebox.askyesno("Confirm", f"{action} '{user['username']}'?"):
                return

        result = set_user_banned(user["id"], banned)

        if result:
            action = "banned" if banned else "unbanned"
            messagebox.showinfo(f"Successfully {action.capitalize()}", f"{user['username']} was successfully {action}.")
            self._refresh_users()
        elif result is False:
            messagebox.showerror("Error", "Failed to update user.")

    def _show_user_detail(self, user):
        self.selected_user_id = user["id"]
        if not self.detail_panel.winfo_ismapped():
            self.detail_panel.pack(side="right", fill="y", before=self.manage_users_panel)
            if self.on_detail_toggle:
                self.on_detail_toggle(True)

        self._render_detail(user, None)
        threading.Thread(target=self._fetch_user_detail, args=(user["id"],), daemon=True).start()

    def _fetch_user_detail(self, user_id):
        reservations = get_user_reservation_history(user_id)
        try:
            # noinspection PyTypeChecker
            self.page.after(0, lambda: self._on_detail_loaded(user_id, reservations))
        except (tk.TclError, RuntimeError):
            pass

    def _on_detail_loaded(self, user_id, reservations):
        if user_id != self.selected_user_id or not self.detail_panel.winfo_exists():
            return
        user = next((u for u in self.all_users if u["id"] == user_id), None)
        if user:
            self._render_detail(user, reservations)

    def _close_detail(self):
        self.selected_user_id = None
        self.detail_panel.pack_forget()
        if self.on_detail_toggle:
            self.on_detail_toggle(False)

    @staticmethod
    def _parse_date(value):
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    def _detail_stats(self, reservations):
        today = date.today()
        borrowed = overdue = total = 0
        for r in reservations:
            status = r.get("status")
            if status in ("Approved", "Return Pending"):
                borrowed += 1
            if status in ("Approved", "Return Pending", "Returned"):
                total += 1
            if status == "Approved":
                due = self._parse_date(r.get("return_date"))
                if due and due < today:
                    overdue += 1
        return borrowed, overdue, total

    def _status_display(self, reservation):
        status = reservation.get("status", "")
        if status == "Approved":
            due = self._parse_date(reservation.get("return_date"))
            if due and due < date.today():
                return "Overdue", STATUS_ERROR
            return "Borrowed", STATUS_SUCCESS
        colors = {
            "Pending": STATUS_WARNING,
            "Return Pending": STATUS_WARNING,
            "Returned": STATUS_RETURNED,
            "Rejected": STATUS_ERROR,
            "Cancelled": MUTED_FG,
        }
        return status, colors.get(status, MUTED_FG)

    def _detail_row(self, label, value, color=PRIMARY_FG):
        row = tk.Frame(self.detail_panel, bg=SECONDARY_BG)
        row.pack(fill="x", padx=20, pady=3)
        tk.Label(row, text=label, font=("Arial", 11), bg=SECONDARY_BG, fg=MUTED_FG).pack(side="left")
        tk.Label(row, text=value, font=("Arial", 11), bg=SECONDARY_BG, fg=color).pack(side="right")

    def _render_detail(self, user, reservations):
        for widget in self.detail_panel.winfo_children():
            widget.destroy()

        banned = user.get("is_banned")

        top = tk.Frame(self.detail_panel, bg=SECONDARY_BG)
        top.pack(fill="x", padx=15, pady=(12, 0))
        tk.Label(top, text="User Details", font=("Arial", 14, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG).pack(side="left")
        close = tk.Button(top, text="✕", font=("Arial", 14, "bold"), width=2, bg=STATUS_ERROR, fg=PRIMARY_FG, cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda e: self._close_detail())

        tk.Button(
            self.detail_panel, text="Unban" if banned else "Ban", font=("Arial", 12, "bold"),
            bg=GREEN_BG if banned else RED_BG, fg=DARK_FG, cursor="hand2", bd=0, pady=6,
            command=lambda: self._toggle_ban(user, not banned),
        ).pack(side="bottom", fill="x", padx=20, pady=15)

        self._avatar(self.detail_panel, user["username"], SECONDARY_BG, banned, size=90).pack(pady=(20, 8))
        tk.Label(self.detail_panel, text=user["username"], font=("Arial", 18, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG,
                 wraplength=300).pack()
        tk.Label(self.detail_panel, text="• Banned" if banned else "• Active", font=("Arial", 12), bg=SECONDARY_BG, fg=STATUS_ERROR if banned else STATUS_SUCCESS).pack(pady=(2, 15))

        created = user.get("created_at")
        self._detail_row("Created", created.split("T")[0] if created else "N/A")
        self._detail_row("Warnings", f"{user.get('warning_count') or 0} / {MAX_WARNINGS}")
        if banned:
            reason = "Automatic (overdue)" if user.get("ban_reason") == "auto" else "By administrator"
            self._detail_row("Ban reason", reason, STATUS_ERROR)

        if reservations is None:
            tk.Label(self.detail_panel, text="Loading...", font=("Arial", 12), bg=SECONDARY_BG, fg=MUTED_FG).pack(pady=20)
            return

        borrowed, overdue, total = self._detail_stats(reservations)
        stats = tk.Frame(self.detail_panel, bg=SECONDARY_BG)
        stats.pack(fill="x", padx=15, pady=(15, 5))
        for col, (label, value, color) in enumerate([
            ("Borrowed", borrowed, PRIMARY_FG),
            ("Overdue", overdue, STATUS_ERROR if overdue else PRIMARY_FG),
            ("Total", total, PRIMARY_FG),
        ]):
            stats.grid_columnconfigure(col, weight=1, uniform="stat")
            box = tk.Frame(stats, bg=PRIMARY_BG)
            box.grid(row=0, column=col, padx=4, sticky="nsew")
            tk.Label(box, text=str(value), font=("Arial", 18, "bold"), bg=PRIMARY_BG, fg=color).pack(pady=(8, 0))
            tk.Label(box, text=label, font=("Arial", 10), bg=PRIMARY_BG, fg=MUTED_FG).pack(pady=(0, 8))

        tk.Label(self.detail_panel, text="Recent Activity", font=("Arial", 13, "bold"), bg=SECONDARY_BG,
                 fg=PRIMARY_FG).pack(anchor="w", padx=20, pady=(15, 5))

        recent = reservations[:RECENT_LIMIT]
        if not recent:
            tk.Label(self.detail_panel, text="No reservations yet.", font=("Arial", 11), bg=SECONDARY_BG, fg=MUTED_FG).pack(
                anchor="w", padx=20)
            return

        for r in recent:
            name = (r.get("equipment") or {}).get("name", "Unknown Equipment")
            status_text, status_color = self._status_display(r)
            row = tk.Frame(self.detail_panel, bg=SECONDARY_BG)
            row.pack(fill="x", padx=20, pady=2)
            tk.Label(row, text=name, font=("Arial", 11), bg=SECONDARY_BG, fg=PRIMARY_FG, anchor="w").pack(side="left")
            tk.Label(row, text=status_text, font=("Arial", 11, "bold"), bg=SECONDARY_BG, fg=status_color).pack(side="right")

    def _pagination_controls(self, total_pages):
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=PRIMARY_BG)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page).pack(side="left", padx=5)
        tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12), bg=PRIMARY_BG, fg=MUTED_FG).pack(side="left", padx=15)
        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page).pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_list()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_list()