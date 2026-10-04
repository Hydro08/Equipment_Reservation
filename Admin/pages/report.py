import tkinter as tk
import csv
import threading

from collections import Counter
from datetime import date
from tkinter import ttk, messagebox, filedialog

from Authentication.auth_service import get_reservation_report, get_all_equipment

PERIODS = {
    "Today": 0,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "All time": None
}

class ReportsPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"
    panel_bg = "#334155"
    muted_fg = "#94A3B8"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.rows = []
        self._request_id = 0

        self._build_ui()

    def _build_ui(self):
        self.reports_panel = tk.Frame(self.parent, bg=self.primary_bg)
        self.reports_panel.pack(fill="both", expand=True)

        header = tk.Frame(self.reports_panel, bg=self.primary_bg)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(header, text="Reports", font=("Arial", 24, "bold"), anchor="w", **self.colors).grid(row=0, column=0, sticky="w")

        controls = tk.Frame(header, bg=self.primary_bg)
        controls.grid(row=0, column=1, sticky="e")

        self.period_var = tk.StringVar(value="Last 30 days")
        self.period_box = ttk.Combobox(controls, textvariable=self.period_var, values=list(PERIODS), state="readonly", width=14, font=("Arial", 12))
        self.period_box.pack(side="left", padx=(0, 10), ipady=3)
        self.period_box.bind("<<ComboboxSelected>>", lambda e: self._load())

        self.export_btn = tk.Button(controls, text="Export CSV", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", cursor="hand2", bd=0, padx=14, pady=4, state="disabled", command=self._export_csv)
        self.export_btn.pack(side="left")

        self.body = tk.Frame(self.reports_panel, bg=self.primary_bg)
        self.body.pack(fill="both", expand=True, padx=20, pady=10)

        self._load()

    def _clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def _load(self):
        self._request_id += 1
        request_id = self._request_id

        self._clear_body()
        self.export_btn.config(state="disabled")
        tk.Label(self.body, text="Loading...", font=("Arial", 24), **self.colors).pack(pady=40)

        days = PERIODS[self.period_var.get()]
        threading.Thread(target=self._fetch, args=(days, request_id), daemon=True).start()

    def _fetch(self, days, request_id):
        rows = get_reservation_report(days)
        equipment = get_all_equipment()
        try:
            # noinspection PyTypeChecker
            self.reports_panel.after(0, lambda: self._render(rows, equipment, request_id))
        except (tk.TclError, RuntimeError):
            pass

    @staticmethod
    def _days_late(row):
        if row.get("status") != "Approved" or not row.get("return_date"):
            return 0
        try:
            due = date.fromisoformat(row["return_date"][:10])
        except ValueError:
            return 0
        return max(0, (date.today() - due).days)

    def _render(self, rows, equipment, request_id):
        if request_id != self._request_id or not self.reports_panel.winfo_exists():
            return

        self.rows = rows
        self._clear_body()
        self.export_btn.config(state="normal" if rows else "disabled")

        counts = Counter(r.get("status") for r in rows)

        overdue = []
        for r in rows:
            late = self._days_late(r)
            if late > 0:
                overdue.append((late, r))
        overdue.sort(key=lambda pair: pair[0], reverse=True)

        borrowed = Counter(
            (r.get("equipment") or {}).get("name", "Unknown")
            for r in rows if r.get("status") in ("Approved", "Return Pending", "Returned")
        )

        dept_counts = Counter(
            ((r.get("equipment") or {}).get("departments") or {}).get("name", "Unassigned")
            for r in rows
        )

        attention = [e for e in equipment if e.get("condition") in ("Damaged", "Under Repair")]

        stats = tk.Frame(self.body, bg=self.primary_bg)
        stats.pack(fill="x", pady=(0, 15))
        cards = [
            ("Total Reservations", len(rows), self.primary_fg),
            ("Approved", counts["Approved"], "#4ADE80"),
            ("Rejected", counts["Rejected"], "#F87171"),
            ("Returned", counts["Returned"], "#60A5FA"),
            ("Overdue", len(overdue), "#F87171" if overdue else self.primary_fg),
        ]

        for i, (title, value, color) in enumerate(cards):
            stats.grid_columnconfigure(i, weight=1, uniform="stat")
            self._stat_card(stats, title, value, i, color)

        lower = tk.Frame(self.body, bg=self.primary_bg)
        lower.pack(fill="both", expand=True)
        lower.grid_columnconfigure(0, weight=1, uniform="panel")
        lower.grid_columnconfigure(1, weight=1, uniform="panel")

        self._render_top_borrowed(lower, borrowed.most_common(5))
        self._render_overdue(lower, overdue)
        self._render_departments(lower, dept_counts.most_common(5))
        self._render_attention(lower, attention)

    def _stat_card(self, parent, title, value, col, color):
        card = tk.Frame(parent, bg=self.panel_bg, height=110)
        card.grid(row=0, column=col, padx=8, sticky="nsew")
        card.grid_propagate(False)

        tk.Label(card, text=str(value), font=("Arial", 26, "bold"), bg=self.panel_bg, fg=color).pack(pady=(20, 0))
        tk.Label(card, text=title, font=("Arial", 12), bg=self.panel_bg, fg=self.muted_fg).pack()

    def _make_panel(self, parent, title, col, row=0):
        panel = tk.Frame(parent, bg=self.panel_bg)
        panel.grid(row=row, column=col, padx=8, pady=(0 if row == 0 else 16, 0), sticky="nsew")

        tk.Label(panel, text=title, font=("Arial", 16, "bold"), bg=self.panel_bg, fg=self.primary_fg).pack(anchor="w", padx=15, pady=(15, 10))

        inner = tk.Frame(panel, bg=self.panel_bg)
        inner.pack(fill="x", padx=15, pady=(0, 15))
        return inner

    def _render_top_borrowed(self, parent, top):
        inner = self._make_panel(parent, "Most Borrowed Equipment (Top 5)", 0)
        inner.grid_columnconfigure(0, weight=1)

        if not top:
            tk.Label(inner, text="No borrowed equipment in this period.", font=("Arial", 12), bg=self.panel_bg, fg=self.muted_fg).grid(row=0, column=0, sticky="w")
            return

        for i, (name, count) in enumerate(top):
            tk.Label(inner, text=f"{i + 1}. {name}", font=("Arial", 13), bg=self.panel_bg, fg=self.primary_fg, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(inner, text=f"{count} time(s)", font=("Arial", 13), bg=self.panel_bg, fg=self.muted_fg).grid(row=i, column=1, sticky="e", pady=3)

    def _render_overdue(self, parent, overdue):
        inner = self._make_panel(parent, "Overdue Items", 1)

        headers = ["Users", "Equipment", "Due Date", "Days Late"]
        for c, text in enumerate(headers):
            inner.grid_columnconfigure(c, weight=1)
            tk.Label(inner, text=text, font=("Arial", 12, "bold"), bg=self.panel_bg, fg=self.muted_fg, anchor="w").grid(row=0, column=c, sticky="w", pady=(0, 6))

        if not overdue:
            tk.Label(inner, text="No overdue items.", font=("Arial", 12), bg=self.panel_bg, fg="#4ADE80").grid(row=1, column=0, columnspan=4, sticky="w")
            return

        for i, (late, r) in enumerate(overdue[:5], start=1):
            values = [
                (r.get("users") or {}).get("username", ""),
                (r.get("equipment") or {}).get("name", ""),
                (r.get("return_date") or "")[:10],
                f"{late} day(s)",
            ]
            for c, value in enumerate(values):
                tk.Label(inner, text=value, font=("Arial", 12), bg=self.panel_bg, fg="#F87171" if c == 3 else self.primary_fg, anchor="w").grid(row=i, column=c, sticky="w", pady=3)

        if len(overdue) > 5:
            tk.Label(inner, text=f"+ {len(overdue) - 5} more (see the CSV export)", font=("Arial", 11), bg=self.panel_bg, fg=self.muted_fg).grid(row=6, column=0, columnspan=4, sticky="w", pady=(8, 0))

    def _render_departments(self, parent, top):
        inner = self._make_panel(parent, "Reservation per Department", 0, row=1)
        inner.grid_columnconfigure(0, weight=1)
        inner.grid_columnconfigure(1, weight=0, minsize=100)

        if not top:
            tk.Label(inner, text="No reservation in this period.", font=("Arial", 12), bg=self.panel_bg, fg=self.muted_fg).grid(row=0, column=0, sticky="w")
            return

        for i, (name, count) in enumerate(top):
            tk.Label(inner, text=f"{i + 1}. {name}", font=("Arial", 13), bg=self.panel_bg, fg=self.primary_fg, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            tk.Label(inner, text=f"{count} request(s)", font=("Arial", 13), bg=self.panel_bg, fg=self.muted_fg).grid(row=i, column=1, sticky="e", pady=3)

    def _render_attention(self, parent, items):
        inner = self._make_panel(parent, "Equipment Needing attention", 1, row=1)

        for c, text in enumerate(["Equipment", "Department", "Condition"]):
            inner.grid_columnconfigure(c, weight=1)
            tk.Label(inner, text=text, font=("Arial", 12, "bold"), bg=self.panel_bg, fg=self.muted_fg, anchor="w").grid(row=0, column=c, sticky="w", pady=(0, 6))

        if not items:
            tk.Label(inner, text="No damaged or under repair equipment.", font=("Arial", 12), bg=self.panel_bg, fg="#4ADE80").grid(row=1, column=0, columnspan=3, sticky="w")
            return

        for i, e in enumerate(items[:5], start=1):
            condition = e.get("condition", "")
            values = [e.get("name", ""), (e.get("departments") or {}).get("name", ""), condition]
            for c, value in enumerate(values):
                color = ("#F87171" if condition == "Damaged" else "#FBBF24") if c == 2 else self.primary_fg
                tk.Label(inner, text=value, font=("Arial", 12), bg=self.panel_bg, fg=color, anchor="w").grid(row=i, column=c, sticky="w", pady=3)

        if len(items) > 5:
            tk.Label(inner, text=f"+ {len(items) - 5} more (see Manage Inventory)", font=("Arial", 11), bg=self.panel_bg, fg=self.muted_fg).grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _export_csv(self):
        if not self.rows:
            messagebox.showinfo("No Data", "There is nothing to export for this period.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Report",
            defaultextension=".csv",
            initialfile=f"reservation_report_{date.today().isoformat()}.csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "User", "Equipment", "Category", "Department", "Reserved Date", "Return Date", "Status", "Days Late"])

                for r in self.rows:
                    equipment = r.get("equipment") or {}
                    writer.writerow([
                        r.get("id", ""),
                        (r.get("users") or {}).get("username", ""),
                        equipment.get("name", ""),
                        (equipment.get("categories") or {}).get("name", ""),
                        (equipment.get("departments") or {}).get("name", ""),
                        (r.get("reserved_date") or "")[:10],
                        (r.get("return_date") or "")[:10],
                        r.get("status", ""),
                        self._days_late(r),
                    ])
        except OSError as e:
            messagebox.showerror("Export Failed", f"Could not save the file. If it is open in Excel, close it and try again.\n\n{e}")
            return

        messagebox.showinfo("Exported", f"Saved {len(self.rows)} reservation(s) to:\n{path}")