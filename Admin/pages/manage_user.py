import tkinter as tk

class ManageUsersPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors

        self._build_ui()

    def _build_ui(self):
        self.manage_users_panel = tk.Frame(self.parent, bg=self.primary_bg)
        self.manage_users_panel.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.manage_users_panel, text="Manage Users", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.working_label = tk.Label(self.manage_users_panel, text="Sa susunod na to sir...", font=("Arial", 24, "bold"), **self.colors, height=50)
        self.working_label.pack()