import tkinter as tk
import threading

from tkinter import messagebox
from Authentication.auth_service import get_all_users, set_user_banned, user_has_borrowed_items
from Config.colors import PRIMARY_BG, SECONDARY_BG, GREEN_BG, DARK_BLUE_BG, BANNED_BG, RED_BG, PRIMARY_FG, MUTED_FG, STATUS_ERROR, STATUS_SUCCESS, DARK_FG
from Config.layout import USER_COLUMN, USER_PER_PAGE

class ManageUsersPage:

    FILTERS = [("all", "All"), ("active", "Active"), ("banned", "Banned")]

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.all_users = []
        self.filter_mode = "all"

        self._build_ui()

    def _build_ui(self):
        self.manage_users_panel = tk.Frame(self.parent, bg=PRIMARY_BG)
        self.manage_users_panel.pack(fill="both", expand=True)

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

    def _filtered_users(self):
        q = self.search_var.get().lower()
        result = []
        for u in self.all_users:
            if self.filter_mode == "active" and u.get("is_banned"):
                continue
            if self.filter_mode == "banned" and not u.get("is_banned"):
                continue
            if q and q not in u['username'].lower():
                continue
            result.append(u)
        return result

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
        canvas.create_oval(2, 2, size - 2, size - 2, fill=SECONDARY_BG if banned else GREEN_BG, outline="")
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

        self._avatar(card, user["username"], bg, banned).grid(row=0, column=0, rowspan=2, padx=(15, 12))

        tk.Label(card, text=user["username"], font=("Arial", 15, "bold"), bg=bg, fg=PRIMARY_FG, anchor="w", justify="left", wraplength=180).grid(row=0, column=1, sticky="sw", padx=(0, 8))
        tk.Label(card, text="• Banned" if banned else "• Active", font=("Arial", 11), bg=bg, fg=STATUS_ERROR if banned else STATUS_SUCCESS, anchor="w").grid(row=1, column=1, sticky="nw")

        option_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg=bg, fg=PRIMARY_FG, cursor="hand2")
        option_btn.place(relx=1.0, x=-10, y=5, anchor="ne")
        option_btn.bind("<Button-1>", lambda e, u=user: self._show_user_menu(e, u))

    def _show_user_menu(self, event, user):
        menu = tk.Menu(self.content_frame, tearoff=0, bg=SECONDARY_BG, fg=PRIMARY_FG, activebackground=PRIMARY_BG, activeforeground=PRIMARY_FG)
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

        if set_user_banned(user["id"], banned):
            action = "banned" if banned else "unbanned"
            messagebox.showinfo(f"Successfully {action.capitalize()}", f"{user['username']} was successfully {action}.")
            self._refresh_users()
        else:
            messagebox.showerror("Error", "Failed to update user.")

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