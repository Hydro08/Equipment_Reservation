import tkinter as tk

class ProfilePage:

    def __init__(self, parent, color):
        self.parent = parent
        self.color = color

        self._build_ui()

    def _build_ui(self):
        self.profile_panel = tk.Frame(self.parent, bg="#1E293B")
        self.profile_panel.pack(fill="both", expand=True)

        self.profile_title = tk.Label(self.profile_panel, text="Profile", font=("Arial", 24), **self.color)
        self.profile_title.pack(pady=(20, 0))