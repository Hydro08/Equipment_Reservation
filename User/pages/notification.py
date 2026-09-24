import tkinter as tk

class NotificationPage:

    def __init__(self, parent, color):
        self.parent = parent
        self.colors = color

        self._build_ui()

    def _build_ui(self):
        self.notification_panel = tk.Frame(self.parent, bg="#1E293B")
        self.notification_panel.pack(fill="both", expand=True)

        self.notification_title = tk.Label(self.notification_panel, text="Notification", font=("Arial", 24), **self.colors)
        self.notification_title.pack(pady=(20, 0))

        self.working_label = tk.Label(self.notification_panel, text="Sa susunod na to sir...", font=("Arial", 24, "bold"), **self.colors, height=50)
        self.working_label.pack()