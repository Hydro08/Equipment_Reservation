import tkinter as tk
import threading
from datetime import datetime, timezone

from tkinter import messagebox

from Authentication.auth_service import get_user_by_id, get_dashboard_summary, verify_current_password, rehash_user_password_by_id, can_change_username, change_username

class ProfilePage:

    BG = "#1E293B"
    PANEL = "#334155"
    FG = "#FFFFFF"
    MUTED = "#94A3B8"

    def __init__(self, parent, color, user, refresh_username_callback=None):
        self.parent = parent
        self.colors = color
        self.user = user
        self.refresh_username_callback = refresh_username_callback

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

        self.profile_panel.after(0, self._render_profile, fresh_user, summary)

    def _render_profile(self, fresh_user, summary):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.user_data = fresh_user or self.user

        self.content_frame = tk.Frame(self.profile_panel, bg=self.BG)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=10)

        try:
            self._build_profile_info()
            self._build_stats(summary)
        except Exception as e:
            tk.Label(self.content_frame, text=f"Error loading profile: {e}", font=("Arial", 13),
                     bg=self.BG, fg="#F87171", wraplength=800, justify="left").pack(pady=20)
            raise

    def _build_profile_info(self):
        info_card = tk.Frame(self.content_frame, bg=self.PANEL)
        info_card.pack(fill="x", pady=(10, 20))

        tk.Label(info_card, text="Profile Info", font=("Arial", 16, "bold"), bg=self.PANEL, fg=self.FG).pack(anchor="w", padx=20, pady=(15, 10))

        self._username_row(info_card)
        self._password_row(info_card)
        self._readonly_row(info_card, "Role", self.user_data.get("role", "N/A").capitalize())

        created_at = self.user_data.get("created_at")
        created_display = created_at.split("T")[0] if created_at else "N/A"
        self._readonly_row(info_card, "Created Account", created_display, is_last=True)

    def _readonly_row(self, parent, label, value, is_last=False):
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", padx=20, pady=8)
        tk.Label(row, text=f"{label}: ", font=("Arial", 13), bg=self.PANEL, fg=self.MUTED, width=16, anchor="w").pack(side="left")
        tk.Label(row, text=value, font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG, anchor="w").pack(side="left")
        if is_last:
            tk.Frame(parent, bg=self.PANEL, height=15).pack()

    def _username_row(self, parent):
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", padx=20, pady=8)

        tk.Label(row, text="Username: ", font=("Arial", 13), bg=self.PANEL, fg=self.MUTED, width=12, anchor="w").pack(side="left")
        tk.Label(row, text=self.user_data.get("username", "N/A"), font=("Arial", 13, "bold"),
                 bg=self.PANEL, fg=self.FG, anchor="w").pack(side="left")
        tk.Button(row, text="Change Username", font=("Arial", 11), bg=self.BG, fg=self.FG, cursor="hand2", bd=0, padx=12, pady=3, command=self._open_change_username).pack(side="right")

    def _password_row(self, parent):
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", padx=20, pady=8)

        tk.Label(row, text="Password: ", font=("Arial", 13), bg=self.PANEL, fg=self.MUTED, width=12, anchor="w").pack(side="left")
        tk.Label(row, text="*********", font=("Arial", 13, "bold"), bg=self.PANEL, fg=self.FG, anchor="w").pack(side="left")

        tk.Button(row, text="Change Password", font=("Arial", 11), bg=self.BG, fg=self.FG, cursor="hand2", bd=0, padx=12, pady=3, command=self._open_change_password).pack(side="right")

    def _build_stats(self, summary):
        stats_card = tk.Frame(self.content_frame, bg=self.PANEL)
        stats_card.pack(fill="x", pady=(0, 20))

        tk.Label(stats_card, text="My Stats", font=("Arial", 16, "bold"), bg=self.PANEL, fg=self.FG).pack(anchor="w", padx=20, pady=(15, 10))

        grid = tk.Frame(stats_card, bg=self.PANEL)
        grid.pack(fill="x", padx=20, pady=(0, 20))
        for col in range(5):
            grid.grid_columnconfigure(col, weight=1)

        stats = [
            ("Available", summary["available"]),
            ("Pending", summary["pending"]),
            ("Borrowed", summary["borrowed"]),
            ("Total Equipment", summary["total"]),
            ("Due Soon", summary["due_soon"]),
        ]
        for col, (label, value) in enumerate(stats):
            box = tk.Frame(grid, bg=self.BG, height=90)
            box.grid(row=0, column=col, padx=6, sticky="nsew")
            box.grid_propagate(False)
            tk.Label(box, text=str(value), font=("Arial", 20, "bold"), bg=self.BG, fg=self.FG).pack(pady=(15, 0))
            tk.Label(box, text=label, font=("Arial", 10), bg=self.BG, fg=self.MUTED).pack()

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
        entry = tk.Entry(win, textvariable=username_var, width=28, font=("Arial", 12),
                         bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat")
        entry.pack(padx=20, pady=(0, 20), ipady=4)
        entry.focus_set()

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

        btn_frame = tk.Frame(win, bg=self.BG)
        btn_frame.pack(pady=(0, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A",
                  command=save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=self.PANEL, fg=self.FG,
                  command=win.destroy, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)

        win.bind("<Return>", lambda e: save())
        win.grab_set()

    def _open_change_password(self):
        win = tk.Toplevel(self.profile_panel, bg=self.BG)
        win.title("Change Password")
        win.resizable(False, False)
        win.transient(self.profile_panel.winfo_toplevel())

        tk.Label(win, text="Current Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(padx=20, pady=(20, 6), anchor="w")
        current_var = tk.StringVar()
        current_entry = tk.Entry(win, textvariable=current_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
        current_entry.pack(padx=20, pady=(0, 10), ipady=4)
        current_entry.focus_set()

        new_fields_frame = tk.Frame(win, bg=self.BG)

        new_var = tk.StringVar()
        confirm_var = tk.StringVar()

        def build_new_fields():
            tk.Label(new_fields_frame, text="New Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(
                padx=20, pady=(10, 6), anchor="w")
            new_entry = tk.Entry(new_fields_frame, textvariable=new_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
            new_entry.pack(padx=20, pady=(0, 10), ipady=4)
            new_entry.focus_set()

            tk.Label(new_fields_frame, text="Confirm New Password", font=("Arial", 13), bg=self.BG, fg=self.FG).pack(
                padx=20, pady=(0, 6), anchor="w")
            confirm_entry = tk.Entry(new_fields_frame, textvariable=confirm_var, width=28, font=("Arial", 12), bg=self.PANEL, fg=self.FG, insertbackground=self.FG, relief="flat", show="*")
            confirm_entry.pack(padx=20, pady=(0, 10), ipady=4)

        verify_btn_frame = tk.Frame(win, bg=self.BG)
        verify_btn_frame.pack(pady=(0, 15))

        def verify_current():
            current_password = current_var.get()
            if not current_password:
                messagebox.showwarning("Missing Field", "Please enter your current password.", parent=win)
                return

            if not verify_current_password(self.user["id"], current_password):
                messagebox.showerror("Incorrect Password", "Current password is incorrect.", parent=win)
                return

            current_entry.config(state="disabled")
            verify_btn.config(state="disabled", text="Verified")

            build_new_fields()
            new_fields_frame.pack(fill="x")

            win.update_idletasks()
            geo = win.geometry()
            size, x, y = geo.split("+")
            width, height = size.split("x")
            new_height = int(height) + 40
            win.geometry(f"{width}x{new_height}+{x}+{y}")

            save_btn.pack(side="left", padx=6)
            verify_btn.pack_forget()

        verify_btn = tk.Button(verify_btn_frame, text="Verify", font=("Arial", 12, "bold"), bg="#3AFD50", fg="#0F172A", command=verify_current, padx=16, pady=4, bd=0, cursor="hand2")
        verify_btn.pack(side="left", padx=6)

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

        save_btn = tk.Button(verify_btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=save_new_password, padx=16, pady=4, bd=0, cursor="hand2")

        cancel_btn = tk.Button(win, text="Cancel", font=("Arial", 12), bg=self.PANEL, fg=self.FG, command=win.destroy, padx=16, pady=4, bd=0, cursor="hand2")
        cancel_btn.pack(pady=(0, 20))

        win.bind("<Return>",
                 lambda e: verify_current() if current_entry["state"] != "disabled" else save_new_password())
        win.grab_set()

    def _refresh_page(self):
        for widget in self.profile_panel.winfo_children():
            widget.destroy()
        self._load_profile_content()