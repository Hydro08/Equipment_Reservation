import tkinter as tk
import threading

from tkinter import messagebox
from Authentication.auth_service import get_all_users, set_user_banned, user_has_borrowed_items

USER_PER_PAGE = 15
USER_COLUMN = 5

class ManageUsersPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.all_users = []

        self._build_ui()

    def _build_ui(self):
        self.manage_users_panel = tk.Frame(self.parent, bg=self.primary_bg)
        self.manage_users_panel.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.manage_users_panel, text="Manage Users", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.manage_users_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_users, daemon=True).start()

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

        self.content_frame = tk.Frame(self.manage_users_panel, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._render_list()

    def _refresh_users(self):
        self.all_users = get_all_users()
        self._render_list()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _user_grid(self, parent):
        frame = tk.Frame(parent, bg=self.primary_bg)
        frame.pack(fill="x", padx=10, pady=10)
        for col in range(USER_COLUMN):
            frame.grid_columnconfigure(col, weight=1, uniform="user")
        return frame

    def _render_list(self):
        self._clear_content()

        if not self.all_users:
            tk.Label(self.content_frame, text="No users found.", font=("Arial", 14), bg=self.primary_bg, fg="#94A3B8").pack(pady=20)
            return

        total_pages = max(1, -(- len(self.all_users) // USER_PER_PAGE))
        self.current_page = min(self.current_page, total_pages - 1)

        start = self.current_page * USER_PER_PAGE
        page_users = self.all_users[start:start + USER_PER_PAGE]

        grid = self._user_grid(self.content_frame)

        row, col = 0, 0
        for user in page_users:
            self._create_user_card(grid, user, row , col)
            col += 1
            if col >= USER_COLUMN:
                col, row=0, row + 1

        self._pagination_controls(total_pages)

    def _create_user_card(self, parent, user, row, col):
        banned = user.get("is_banned")
        bg = "#3B2A33" if banned else "#334155"

        card = tk.Frame(parent, bg=bg, height=130, highlightbackground="#F87171" if banned else bg, highlightthickness=1)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_propagate(False)

        option_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg=bg, fg=self.primary_fg, cursor="hand2")
        option_btn.place(relx=1.0, x=-10, y=5, anchor="ne")
        option_btn.bind("<Button-1>", lambda e, u=user: self._show_user_menu(e, u))

        tk.Label(card, text=user["username"], font=("Arial", 15, "bold"), bg=bg, fg=self.primary_fg, wraplength=170).pack(pady=(30, 5))
        tk.Label(card, text="● Banned" if banned else "● Active", font=("Arial", 11), bg=bg, fg="#F87171" if banned else "#4ADE80").pack(pady=(0, 5))

    def _show_user_menu(self, event, user):
        menu = tk.Menu(self.content_frame, tearoff=0, bg="#334155", fg=self.primary_fg, activebackground=self.primary_bg, activeforeground=self.primary_fg)
        if user.get("is_banned"):
            menu.add_command(label="Unban", command=lambda: self._toggle_ban(user, False))
        else:
            menu.add_command(label="Ban", command=lambda: self._toggle_ban(user, True))
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_ban(self, user, banned):
        if banned and user_has_borrowed_items(user["id"]):
            if not messagebox.askyesno("Confirm Ban", f"{user['username']} still has borrowed equipment. Ban anyway?"):
                return
        else:
            action = "Ban" if banned else "Unban"
            if not messagebox.askyesno("Confirm", f"{action} '{user['username']}'?"):
                return

        if banned:
            messagebox.showinfo(
                "Successfully Banned",
                f"{user['username']} was successfully banned."
            )
        else:
            messagebox.showinfo(
                "Successfully Unbanned",
                f"{user['username']} was successfully unbanned."
            )

        if set_user_banned(user["id"], banned):
            self._refresh_users()
        else:
            messagebox.showerror("Error", "Failed to update user.")

    def _pagination_controls(self, total_pages):
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page).pack(side="left", padx=5)
        tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)
        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page).pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_list()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_list()