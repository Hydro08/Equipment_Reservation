import tkinter as tk
import threading

from tkinter import messagebox
from Authentication.auth_service import get_user_notification,dismiss_notification

class NotificationPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, color, user):
        self.parent = parent
        self.colors = color
        self.user = user

        self._build_ui()

    def _build_ui(self):
        self.notification_panel = tk.Frame(self.parent, bg="#1E293B")
        self.notification_panel.pack(fill="both", expand=True)

        self.notification_title = tk.Label(self.notification_panel, text="Notification", font=("Arial", 24), **self.colors)
        self.notification_title.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.notification_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_notifications, daemon=True).start()

    def _fetch_notifications(self):
        notifications = get_user_notification(self.user["id"])

        self.notification_panel.after(0, self._render_notifications, notifications)

    def _render_notifications(self, notifications):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()

        self.content_frame = tk.Frame(self.notification_panel, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.all_notifications = notifications
        self._render_list()

    def _render_list(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not self.all_notifications:
            tk.Label(self.content_frame, text="No Notifications yet.", font=("Arial", 14), bg=self.primary_bg, fg=self.primary_fg, height=50).pack(pady=20)
            return

        for note in self.all_notifications:
            self._create_notification_row(note)

    def _create_notification_row(self, note):
        equipment_data = note.get("equipment") or {}
        equipment_name = equipment_data.get("name", "Unknown Equipment")
        status = note.get("status")

        if status == "Approved":
            message = f"We accepted your request for {equipment_name}. Please return this after 3 days."
            color = "#4ADE80"
        else:
            message = f"Sorry, we rejected your request for {equipment_name}."
            color = "#F87171"

        row = tk.Frame(self.content_frame, bg="#334155")
        row.pack(fill="x", padx=10, pady=6)

        tk.Label(row, text=message, font=("Arial", 13), bg="#334155", fg=color, wraplength=1000, justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=15, pady=15)

        delete_btn = tk.Button(row, text="Delete", font=("Arial", 12, "bold"), bg="#F87171", fg="#0F172A", cursor="hand2", bd=0, padx=15, pady=5, command=lambda: self._handle_delete(note))
        delete_btn.pack(side="right", padx=15)

    def _handle_delete(self, note):
        if not messagebox.askyesno("Confirm", "Delete this notification?"):
            return

        if dismiss_notification(note["id"]):
            self.all_notifications.remove(note)
            self._render_list()
        else:
            messagebox.showerror("Error", "Failed to delete notification.")