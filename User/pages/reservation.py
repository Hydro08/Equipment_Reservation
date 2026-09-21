import tkinter as tk

class ReservationPage:
    def __init__(self, parent, color):
        self.parent = parent
        self.color = color

        self._build_ui()

    def _build_ui(self):
        self.reservation_panel = tk.Frame(self.parent, bg="#1E293B")
        self.reservation_panel.pack(fill="both", expand=True)

        self.reservation_title = tk.Label(self.reservation_panel, text="Reservation", font=("Arial", 24), **self.color)
        self.reservation_title.pack(pady=(20, 0))