import calendar
import tkinter as tk

from datetime import date

from Config.colors import PRIMARY_BG, SECONDARY_BG, PRIMARY_FG, MUTED_FG, DARK_FG, GREEN_BG, STATUS_SUCCESS, STATUS_ERROR
from Config.layout import MAX_CHIPS, CELL_HEIGHT, POPUP_COLUMNS, POPUP_PER_PAGE, POPUP_CARD_HEIGHT, POPUP_CARD_WIDTH
from Config.settings import STATUS_COLORS, LEGEND, WEEKDAYS

class ReservationCalendar:

    def __init__(self, parent, reservations):
        self.parent = parent
        self.reservations = self._prepare(reservations)

        today = date.today()
        self.year = today.year
        self.month = today.month

        self._popup = None

        self._build()

    @staticmethod
    def _parse(value):
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    @classmethod
    def _prepare(cls, rows):
        prepared = []
        for r in rows or []:
            if r.get("status") not in STATUS_COLORS:
                continue
            start = cls._parse(r.get("reserved_date"))
            if not start:
                continue
            end = cls._parse(r.get("return_date"))
            if not end or end < start:
                end = start
            prepared.append((start, end, r))
        return prepared

    @staticmethod
    def _color_for(reservation, end):
        status = reservation.get("status")
        if status == "Approved" and end < date.today():
            return STATUS_ERROR
        return STATUS_COLORS.get(status, MUTED_FG)

    def _reservations_by_day(self):
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        first = date(self.year, self.month, 1)
        last = date(self.year, self.month, days_in_month)

        by_day = {d: [] for d in range(1, days_in_month + 1)}
        for start, end, r in self.reservations:
            if end < first or start > last:
                continue
            s = max(start, first)
            e = min(end, last)
            color = self._color_for(r, end)
            for offset in range((e - s).days + 1):
                by_day[s.day + offset].append((r, color))
        return by_day

    def _build(self):
        self.frame = tk.Frame(self.parent, bg=PRIMARY_BG)
        self.frame.pack(fill="both", expand=True)

        header = tk.Frame(self.frame, bg=PRIMARY_BG)
        header.pack(pady=(5, 5))

        tk.Button(header, text="<", font=("Arial", 12, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=12, pady=3, command=lambda: self._change_month(-1)).pack(side="left")

        self.month_label = tk.Label(header, text="", font=("Arial", 16, "bold"), bg=PRIMARY_BG, fg=PRIMARY_FG, width=18)
        self.month_label.pack(side="left", padx=10)

        tk.Button(header, text=">", font=("Arial", 12, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=12, pady=3, command=lambda: self._change_month(1)).pack(side="left")

        tk.Button(header, text="Today", font=("Arial", 11, "bold"), bg="#4ADE80", fg=DARK_FG, cursor="hand2", bd=0, padx=12, pady=3, command=self._go_today).pack(side="left", padx=(15, 0))

        legend = tk.Frame(self.frame, bg=PRIMARY_BG)
        legend.pack(pady=(0, 5))
        for text, color in LEGEND:
            tk.Label(legend, text="■", font=("Arial", 11), bg=PRIMARY_BG, fg=color).pack(side="left", padx=(10, 2))
            tk.Label(legend, text=text, font=("Arial", 10), bg=PRIMARY_BG, fg=MUTED_FG).pack(side="left")

        self.grid_frame = tk.Frame(self.frame, bg=PRIMARY_BG)
        self.grid_frame.pack(fill="x", padx=10)

        self._render_month()

    def _change_month(self, delta):
        self.month += delta
        if self.month < 1:
            self.month, self.year = 12, self.year - 1
        elif self.month > 12:
            self.month, self.year = 1, self.year + 1
        self._render_month()

    def _go_today(self):
        today = date.today()
        self.year, self.month = today.year, today.month
        self._render_month()

    def _render_month(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()

        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.month_label.config(text=f"{calendar.month_name[self.month]} {self.year}")

        for col, name in enumerate(WEEKDAYS):
            self.grid_frame.grid_columnconfigure(col, weight=1, uniform="day")
            tk.Label(self.grid_frame, text=name, font=("Arial", 11, "bold"), bg=PRIMARY_BG, fg=MUTED_FG).grid(row=0, column=col, pady=(0, 3))

        by_day = self._reservations_by_day()
        today = date.today()
        weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(self.year, self.month)

        for w, week in enumerate(weeks, start=1):
            for col, day in enumerate(week):
                self._create_cell(w, col, day, by_day.get(day, []), today)

    def _create_cell(self, row, col, day, entries, today):
        if day == 0:
            cell = tk.Frame(self.grid_frame, bg=PRIMARY_BG, height=CELL_HEIGHT)
            cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            return

        is_today = (self.year, self.month, day) == (today.year, today.month, today.day)

        cell = tk.Frame(self.grid_frame, bg=SECONDARY_BG, height=CELL_HEIGHT, highlightbackground=GREEN_BG if is_today else SECONDARY_BG, highlightthickness=2 if is_today else 0)
        cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
        cell.pack_propagate(False)

        tk.Label(cell, text=str(day), font=("Arial", 10, "bold"), bg=SECONDARY_BG, fg=STATUS_SUCCESS if is_today else PRIMARY_FG, anchor="w").pack(fill="x", padx=5)

        for r, color in entries[:MAX_CHIPS]:
            name = (r.get("equipment") or {}).get("name", "Unknown")
            if len(name) > 16:
                name = name[:15] + "…"
            tk.Label(cell, text=name, font=("Arial", 8, "bold"), bg=color, fg=DARK_FG, anchor="w").pack(fill="x", padx=3, pady=1)

        extra = len(entries) - MAX_CHIPS
        if extra > 0:
            tk.Label(cell, text=f"+{extra} more", font=("Arial", 8), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").pack(fill="x", padx=5)

        if entries:
            for widget in [cell, *cell.winfo_children()]:
                widget.config(cursor="hand2")
                widget.bind("<Button-1>", lambda e, d=day, items=entries: self._open_day(d, items))

    def _open_day(self, day, entries):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()

        top = tk.Toplevel(self.frame)
        self._popup = top
        top.title(f"{calendar.month_name[self.month]} {day}, {self.year}")
        top.config(bg=PRIMARY_BG)
        top.transient(self.frame.winfo_toplevel())
        top.resizable(False, False)
        top.bind("<Escape>", lambda e: top.destroy())

        tk.Label(top, text=f"{calendar.month_name[self.month]} {day}, {self.year}", font=("Arial", 16, "bold"),
                 bg=PRIMARY_BG, fg=PRIMARY_FG).pack(padx=25, pady=(20, 0))
        tk.Label(top, text=f"{len(entries)} reservation(s)", font=("Arial", 11), bg=PRIMARY_BG, fg=MUTED_FG).pack(
            pady=(0, 10))

        columns = min(POPUP_COLUMNS, len(entries))
        total_pages = max(1, -(-len(entries) // POPUP_PER_PAGE))
        state = {"page": 0}

        list_frame = tk.Frame(top, bg=PRIMARY_BG)
        list_frame.pack(padx=15)

        nav_frame = tk.Frame(top, bg=PRIMARY_BG)
        nav_frame.pack(pady=(8, 0))

        def render():
            for widget in list_frame.winfo_children():
                widget.destroy()
            for widget in nav_frame.winfo_children():
                widget.destroy()

            start = state["page"] * POPUP_PER_PAGE
            for i, (r, color) in enumerate(entries[start:start + POPUP_PER_PAGE]):
                self._popup_card(list_frame, r, color, i // columns, i % columns)

            if total_pages > 1:
                tk.Button(nav_frame, text="< Previous", font=("Arial", 11), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=12, pady=4, state="normal" if state["page"] > 0 else "disabled", command=lambda: go(-1)).pack(side="left", padx=5)
                tk.Label(nav_frame, text=f"Page {state['page'] + 1} of {total_pages}", font=("Arial", 11), bg=PRIMARY_BG, fg=MUTED_FG).pack(side="left", padx=10)
                tk.Button(nav_frame, text="Next >", font=("Arial", 11), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=12, pady=4, state="normal" if state["page"] < total_pages - 1 else "disabled", command=lambda: go(1)).pack(side="left", padx=5)

        def go(delta):
            state["page"] += delta
            render()

        render()

        if total_pages > 1:
            list_frame.update_idletasks()
            list_frame.config(width=list_frame.winfo_reqwidth(), height=list_frame.winfo_reqheight())
            list_frame.grid_propagate(False)

        tk.Button(top, text="Close", font=("Arial", 11, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG, cursor="hand2", bd=0, padx=20, pady=5, command=top.destroy).pack(pady=(10, 20))

        top.update_idletasks()
        main = self.frame.winfo_toplevel()
        x = main.winfo_rootx() + (main.winfo_width() - top.winfo_width()) // 2
        y = main.winfo_rooty() + (main.winfo_height() - top.winfo_height()) // 2
        top.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    @staticmethod
    def _shorten(text, limit):
        return text if len(text) <= limit else text[:limit - 1] + "…"

    def _popup_card(self, parent, r, color, row, col):
        username = (r.get("users") or {}).get("username", "Unknown User")
        equipment = (r.get("equipment") or {}).get("name", "Unknown Equipment")

        if r.get("status") == "Approved":
            status = "Overdue" if color == STATUS_ERROR else "Borrowed"
        else:
            status = r.get("status", "")

        card = tk.Frame(parent, bg=SECONDARY_BG, width=POPUP_CARD_WIDTH, height=POPUP_CARD_HEIGHT)
        card.grid(row=row, column=col, padx=5, pady=5)
        card.pack_propagate(False)

        dates = f"{str(r.get('reserved_date', 'N/A'))[:10]} → {str(r.get('return_date', 'N/A'))[:10]}"

        tk.Label(card, text=self._shorten(username, 20), font=("Arial", 12, "bold"), bg=SECONDARY_BG, fg=PRIMARY_FG, anchor="w").pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(card, text=self._shorten(equipment, 26), font=("Arial", 10), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").pack(fill="x", padx=10)
        tk.Label(card, text=dates, font=("Arial", 9), bg=SECONDARY_BG, fg=MUTED_FG, anchor="w").pack(fill="x", padx=10)
        tk.Label(card, text=f"● {status}", font=("Arial", 10, "bold"), bg=SECONDARY_BG, fg=color, anchor="w").pack(fill="x", padx=10, pady=(0, 8), side="bottom")