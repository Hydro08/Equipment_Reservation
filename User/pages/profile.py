import tkinter as tk
import threading

from datetime import date, datetime, timezone
from tkinter import messagebox

from Authentication.auth_service import get_user_by_id, get_dashboard_summary, get_user_reservations, verify_current_password, rehash_user_password_by_id, can_change_username, change_username

DUE_SOON_DAYS = 1
RECENT_LIMIT = 5

class ProfilePage:

    BG = "#1E293B"
    PANEL = "#334155"
    FG = "#FFFFFF"
    MUTED = "#94A3B8"
    GREEN = "#4ADE80"
    RED = "#F87171"
    YELLOW = "#FBBF24"
    BLUE = "#60A5FA"
    DARK = "#0F172A"

    def __init__(self, parent, color, user, refresh_username_callback=None, navigate_reservation_callback=None):
        self.parent = parent
        self.colors = color
        self.user = user
        self.refresh_username_callback = refresh_username_callback
        self.navigate_reservation_callback = navigate_reservation_callback

        self._build_ui()

    def _build_ui(self):
        self.profile_panel = tk.Frame(self.parent, bg="#1E293B")
        self.profile_panel.pack(fill="both", expand=True)

        self._load_profile_content()

    def _load_profile_content(self):
        self.profile_title = tk.Label(self.profile_panel, text="Profile", font=("Arial", 24), **self.colors)
        self.profile_title.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.profile_panel, text="Loading...", font=("Arial", 24), **self.colors,
                                      height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_profile_data, daemon=True).start()

    def _fetch_profile_data(self):
        fresh_user = get_user_by_id(self.user["id"])
        summary = get_dashboard_summary(self.user["id"])
        reservations = get_user_reservations(self.user["id"])
        can_change, next_allowed = can_change_username(self.user["id"])

        data = {
            "fresh_user": fresh_user,
            "summary": summary,
            "reservations": reservations or [],
            "username_hint": self._username_hint(can_change, next_allowed),
            "can_change_name": can_change,
        }

        try:
            #noinspection PyTypeChecker
            self.profile_panel.after(0, self._render_profile, data)
        except (tk.TclError, RuntimeError):
            pass

    @staticmethod
    def _username_hint(can_change, next_allowed):
        if can_change or not next_allowed:
            return ""
        seconds = (next_allowed - datetime.now(timezone.utc)).total_seconds()
        hours = max(1, int(seconds // 3600) + 1)
        return f"Next username change available in about {hours} hour(s)"

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    def _reservation_stats(self, reservations):
        today = date.today()
        due_soon = overdue = total_borrowed = 0

        for r in reservations:
            status = r.get("status")
            if status in ("Approved", "Return Pending", "Returned"):
                total_borrowed += 1
            if status == "Approved":
                due = self._parse_date(r.get("return_date"))
                if not due:
                    continue
                days_left = (due - today).days
                if days_left < 0:
                    overdue+=1
                elif days_left <= DUE_SOON_DAYS:
                    due_soon+=1

        return due_soon, overdue, total_borrowed

    def _render_profile(self, data):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.user_data = data["fresh_user"] or self.user

        self.content_frame = tk.Frame(self.profile_panel, bg=self.BG)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=10)

        try:
            self._build_profile_info(data["username_hint"], data["can_change_name"])
            self._build_stats(data["summary"], self._reservation_stats(data["reservations"]))
            self._build_recent_activity(data["reservations"])
        except Exception as e:
            tk.Label(self.content_frame, text=f"Error loading profile: {e}", font=("Arial", 13), bg=self.BG, fg="#F87171", wraplength=800, justify="left").pack(pady=20)
            raise

    def _avatar(self, parent, name):
        size = 84
        canvas = tk.Canvas(parent, width=size, height=size, bg=self.PANEL, highlightthickness=0)
        canvas.create_oval(2, 2, size - 2, size - 2, fill=self.GREEN, outline="")
        initial = (name or "?").strip()[:2].upper() or "?"
        canvas.create_text(size // 2, size // 2, text=initial, font=("Arial", 32, "bold"), fill=self.DARK)
        return canvas

    def _info_label(self, parent, row, text):
        tk.Label(parent, text=text, font=("Arial", 13), bg=self.PANEL, fg=self.MUTED, anchor="w").grid(row=row, column=1, sticky="w", padx=(0, 20), pady=6)

    def _build_profile_info(self, username_hint, can_change):
        card = tk.Frame(self.content_frame, bg=self.PANEL)
        card.pack(fill="x", pady=(10, 12))

        card.grid_columnconfigure(0, minsize=130)
        card.grid_columnconfigure(1, minsize=170)
        card.grid_columnconfigure(2, weight=1)
        card.grid_columnconfigure(3, minsize=190)

        tk.Label(card, text="Profile Info", font=("Arial", 16, "bold"), bg=self.PANEL, fg=self.FG).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(15, 5))

        row = 1

        username = self.user_data.get("username", "N/A")
        self._info_label(card, row, "Username")
        tk.Label(card, text=username, font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG, anchor="w").grid(row=row, column=2, sticky="w", pady=6)
        tk.Button(card, text="Change Username", font=("Arial", 11), width=16, bg=self.BG, fg=self.FG if can_change else self.MUTED, cursor="hand2", bd=0, pady=3, command=self._open_change_username).grid(row=row, column=3, sticky="e", padx=(10, 20), pady=6)
        row+=1

        if username_hint:
            tk.Label(card, text=username_hint, font=("Arial", 10, "italic"), bg=self.PANEL, fg=self.MUTED, anchor="w").grid(row=row, column=2, columnspan=2, sticky="w", pady=(0, 4))
            row+=1

        self._info_label(card, row, "Password")
        tk.Label(card, text="••••••••••", font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG, anchor="w").grid(row=row, column=2, sticky="w", pady=6)
        tk.Button(card, text="Change Password", font=("Arial", 11), width=16, bg=self.BG, fg=self.FG, cursor="hand2", bd=0, pady=3, command=self._open_change_password).grid(row=row, column=3, sticky="e", padx=(10, 20), pady=6)
        row+=1

        banned = self.user_data.get("is_banned")
        self._info_label(card, row, "Role")
        role_frame = tk.Frame(card, bg=self.PANEL)
        role_frame.grid(row=row, column=2, sticky="w", pady=6)
        tk.Label(role_frame, text=self.user_data.get("role", "N/A").capitalize(), font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG).pack(side="left")
        tk.Label(role_frame, text="• Banned" if banned else "• Active", font=("Arial", 11, "bold"), bg=self.PANEL, fg=self.RED if banned else self.GREEN).pack(side="left", padx=(14, 0))
        row+=1

        created_at = self.user_data.get("created_at")
        created_display = created_at.split("T")[0] if created_at else "N/A"
        self._info_label(card, row, "Created Account")
        tk.Label(card, text=created_display, font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG, anchor="w").grid(row=row, column=2, sticky="w", pady=(6, 16))

        self._avatar(card, username).grid(row=1, column=0, rowspan=row, sticky="n", padx=(20, 10), pady=(5, 0))

    def _build_stats(self, summary, reservation_stats):
        due_soon, overdue, total_borrowed = reservation_stats

        stats_card = tk.Frame(self.content_frame, bg=self.PANEL)
        stats_card.pack(fill="x", pady=(0, 12))

        tk.Label(stats_card, text="My Stats", font=("Arial", 16, "bold"), bg=self.PANEL, fg=self.FG).pack(anchor="w", padx=20, pady=(10, 15))

        grid = tk.Frame(stats_card, bg=self.PANEL)
        grid.pack(fill="x", padx=20, pady=(0, 15))
        for col in range(5):
            grid.grid_columnconfigure(col, weight=1, uniform="stat")

        stats = [
            ("Pending", summary["pending"], self.FG, "pending"),
            ("Borrowed", summary["borrowed"], self.FG, "borrowed"),
            ("Due Soon", due_soon, self.YELLOW if due_soon else self.FG, "borrowed"),
            ("Overdue", overdue, self.RED if overdue else self.FG, "borrowed"),
            ("Total Borrowed", total_borrowed, self.FG, None),
        ]

        for col, (label, value, color, tab) in enumerate(stats):
            box = tk.Frame(grid, bg=self.BG, height=80)
            box.grid(row=0, column=col, padx=6, sticky="nsew")
            box.pack_propagate(False)

            value_label = tk.Label(box, text=str(value), font=("Arial", 20, "bold"), bg=self.BG, fg=color)
            value_label.pack(pady=(12, 0))
            title_label = tk.Label(box, text=label, font=("Arial", 10), bg=self.BG, fg=self.MUTED)
            title_label.pack()

            if tab and self.navigate_reservation_callback:
                for widget in (box, value_label, title_label):
                    widget.config(cursor="hand2")
                    widget.bind("<Button-1>", lambda e, t=tab: self.navigate_reservation_callback(t))

    def _status_display(self, reservation):
        status = reservation.get("status", "")
        if status == "Approved":
            due = self._parse_date(reservation.get("return_date"))
            if due and due < date.today():
                return "Overdue", self.RED
            return "Borrowed", self.GREEN

        colors = {
            "Pending": self.YELLOW,
            "Return Pending": self.YELLOW,
            "Returned": self.BLUE,
            "Rejected": self.RED,
            "Cancelled": self.MUTED,
        }
        return status, colors.get(status, self.MUTED)

    def _build_recent_activity(self, reservations):
        card = tk.Frame(self.content_frame, bg=self.PANEL)
        card.pack(fill="x")

        header = tk.Frame(card, bg=self.PANEL)
        header.pack(fill="x", padx=20, pady=(12, 6))
        tk.Label(header, text="Recent Activity", font=("Arial", 16, "bold"), bg=self.PANEL, fg=self.FG).pack(side="left")

        if self.navigate_reservation_callback:
            tk.Button(header, text="View all >", font=("Arial", 11), bg=self.BG, fg=self.FG, cursor="hand2", bd=0, padx=12, pady=2, command=lambda: self.navigate_reservation_callback("pending")).pack(side="right")

        recent = sorted(reservations, key=lambda item: str(item.get("reserved_date") or ""), reverse=True)[:RECENT_LIMIT]

        if not recent:
            tk.Label(card, text="No reservation yet.", font=("Arial", 12), bg=self.PANEL, fg=self.MUTED).pack(anchor="w", padx=20, pady=(0, 15))
            return

        grid = tk.Frame(card, bg=self.PANEL)
        grid.pack(fill="x", padx=20, pady=(0, 12))

        columns = [("Equipment", 3), ("Reserved", 1), ("Return", 1), ("Status", 1)]
        for col, (title, weight) in enumerate(columns):
            grid.grid_columnconfigure(col, weight=weight, uniform="recent")
            tk.Label(grid, text=title, font=("Arial", 11, "bold"), bg=self.PANEL, fg=self.MUTED, anchor="w").grid(row=0, column=col, sticky="w", pady=(0, 4))

        for i, reservation in enumerate(recent, start=1):
            equipment = (reservation.get("equipment") or {}).get("name", "Unknown Equipment")
            status_text, status_color = self._status_display(reservation)

            values = [
                (equipment, self.FG),
                (str(reservation.get("reserved_date") or "N/A")[:10], self.MUTED),
                (str(reservation.get("return_date") or "N/A")[:10], self.MUTED),
                (status_text, status_color),
            ]
            for col, (text, color) in enumerate(values):
                tk.Label(grid, text=text, font=("Arial", 12, "bold" if col == 3 else "normal"), bg=self.PANEL, fg=color, anchor="w").grid(row=i, column=col, sticky="w", pady=3)

    def _open_change_username(self):
        can_change, next_allowed = can_change_username(self.user["id"])

        if not can_change:
            hours_left = int((next_allowed - datetime.now(timezone.utc)).total_seconds() // 3600) + 1
            messagebox.showinfo("Not Yet", f"You can change your username again in about {hours_left} hour(s).")
            return

        win = tk.Toplevel(self.profile_panel, bg=self.BG)
        win.title("Change Username")
        win.resizable(False, False)
        win.transient(self.profile_panel.winfo_toplevel())

        tk.Label(win, text="New Username", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(padx=20, pady=(20, 6), anchor="w")
        username_var = tk.StringVar(value=self.user_data.get("username", ""))
        entry = tk.Entry(win, textvariable=username_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat")
        entry.pack(padx=20, pady=(0, 20), ipady=4)
        entry.focus_set()

        user_width = 300
        user_height = 150
        user_screen_width = win.winfo_screenwidth()
        user_screen_height = win.winfo_screenheight()
        x = (user_screen_width - user_width) // 2
        y = (user_screen_height - user_height) // 2
        win.geometry(f"{user_width}x{user_height}+{x}+{y}")

        def save():
            new_name = username_var.get().strip()
            if not new_name:
                messagebox.showwarning("Missing Field", "Username is required.", parent=win)
                return
            if new_name == self.user_data.get("username"):
                win.destroy()
                return
            if change_username(self.user["id"], new_name):
                self.user_data["username"] = new_name
                self.user["username"] = new_name
                messagebox.showinfo("Success", "Username updated.", parent=win)
                win.destroy()
                if self.refresh_username_callback:
                    self.refresh_username_callback(new_name)
                self._refresh_page()
            else:
                messagebox.showerror("Error", "Could not update the username. It may already be taken.", parent=win)

        btn_frame = tk.Frame(win, bg=self.BG)
        btn_frame.pack(pady=(0, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=self.PANEL, fg=self.FG, command=win.destroy, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)

        win.bind("<Return>", lambda e: save())
        win.grab_set()

    def _open_change_password(self):
        win = tk.Toplevel(self.profile_panel, bg=self.BG)
        win.title("Change Password")
        win.resizable(False, False)
        win.transient(self.profile_panel.winfo_toplevel())

        def center_window():
            win.update_idletasks()
            w = max(win.winfo_reqwidth(), 320)
            h = win.winfo_reqheight()
            x = (win.winfo_screenwidth() - w) // 2
            y = (win.winfo_screenheight() - h) // 2
            win.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(win, text="Current Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(padx=20, pady=(20, 6), anchor="w")
        current_var = tk.StringVar()
        current_entry = tk.Entry(win, textvariable=current_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
        current_entry.pack(padx=20, pady=(0, 10), ipady=4)
        current_entry.focus_set()

        show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(win, text="Show Password", variable=show_var, font=("Arial", 11), bg=self.BG, fg=self.FG, selectcolor=self.BG, activebackground=self.BG, activeforeground=self.FG, cursor="hand2", command=lambda: toggle_show()).pack(anchor="w", padx=20)

        new_var = tk.StringVar()
        confirm_var = tk.StringVar()

        new_fields_frame = tk.Frame(win, bg=self.BG)

        tk.Label(new_fields_frame, text="New Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(padx=20, pady=(10, 6), anchor="w")
        new_entry = tk.Entry(new_fields_frame, textvariable=new_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
        new_entry.pack(padx=20, pady=(0, 10), ipady=4)

        tk.Label(new_fields_frame, text="Confirm New Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(padx=20, pady=(0, 6), anchor="w")
        confirm_entry = tk.Entry(new_fields_frame, textvariable=confirm_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
        confirm_entry.pack(padx=20, pady=(0, 10), ipady=4)

        btn_frame = tk.Frame(win, bg=self.BG)
        btn_frame.pack(pady=(10, 20))

        def toggle_show():
            char = "" if show_var.get() else "•"
            for entry in (current_entry, new_entry, confirm_entry):
                entry.config(show=char)

        def verify_current():
            current_password = current_var.get()
            if not current_password:
                messagebox.showwarning("Missing Field", "Please enter your current password.", parent=win)
                return

            if not verify_current_password(self.user["id"], current_password):
                messagebox.showerror("Incorrect Password", "Current password is incorrect.", parent=win)
                return

            current_entry.config(state="disabled")

            new_fields_frame.pack(fill="x", before=btn_frame)

            verify_btn.pack_forget()
            save_btn.pack(side="left", padx=6, before=cancel_btn)

            new_entry.focus_set()
            center_window()

        def save_new_password():
            new_password = new_var.get()
            confirm_password = confirm_var.get()

            if not new_password or not confirm_password:
                messagebox.showwarning("Missing Field", "Please fill in both password fields.", parent=win)
                return
            if len(new_password) < 6:
                messagebox.showwarning("Too Short", "Password must be at least 6 characters.", parent=win)
                return
            if new_password != confirm_password:
                messagebox.showwarning("Mismatch", "Passwords do not match.", parent=win)
                return

            if rehash_user_password_by_id(self.user["id"], new_password):
                messagebox.showinfo("Success", "Password updated successfully.", parent=win)
                win.destroy()

        verify_btn = tk.Button(btn_frame, text="Verify", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=verify_current, padx=16, pady=4, bd=0, cursor="hand2")
        verify_btn.pack(side="left", padx=6)

        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=self.PANEL, fg=self.FG, command=win.destroy, padx=16, pady=4, bd=0, cursor="hand2")
        cancel_btn.pack(side="left", padx=6)

        save_btn = tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=save_new_password, padx=16, pady=4, bd=0, cursor="hand2")

        win.bind("<Return>", lambda e: verify_current() if current_entry["state"] != "disabled" else save_new_password())
        center_window()
        win.grab_set()

    def _refresh_page(self):
        for widget in self.profile_panel.winfo_children():
            widget.destroy()
        self._load_profile_content()