import tkinter as tk
import threading
from datetime import date, timedelta

from Authentication.auth_service import get_all_equipment, get_all_departments, get_all_categories, create_reservation
from tkinter import messagebox

GRID_ITEMS_PER_PAGE = 9
POLL_INTERVAL_MS = 5000

class BrowseEquipmentPage:

    primary_bg = "#1E293B"

    def __init__(self, parent, colors, user_id):
        self.parent = parent
        self.colors = colors
        self.current_user_id = user_id
        self.current_page = 0
        self.current_department_page = 0
        self.current_category_page = 0

        self._build_ui()

    def _build_ui(self):
        self.search_query = ""
        self.search_page = 0
        self._suppress_search = False

        self.main_frame = tk.Frame(self.parent, bg=self.primary_bg)
        self.main_frame.pack(fill="both", expand=True)

        self.header = tk.Frame(self.main_frame, bg=self.primary_bg)
        self.header.pack(fill="x", padx=20, pady=(20, 10))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = tk.Label(self.header, text="Browse Equipment", font=("Arial", 18, "bold"), anchor="center", **self.colors)
        self.title_label.grid(row=0, column=0, sticky="ew")

        self.search_var = tk.StringVar()
        self.search_area = tk.Frame(self.header, bg=self.primary_bg)
        self.search_area.grid(row=0, column=1, sticky="e")

        tk.Label(self.search_area, text="🔍", font=("Arial", 14), bg=self.primary_bg, fg="#FFFFFF").pack(side="left", padx=(0, 8))

        self.search_entry = tk.Entry(self.search_area, textvariable=self.search_var, width=28, font=("Arial", 12),bg="#334155", fg="#FFFFFF", insertbackground="#FFFFFF", relief="flat")
        self.search_entry.pack(side="left", ipady=4)
        self.search_entry.bind("<Control-BackSpace>", lambda e: (self.clear_search_entry(), "break")[1])

        tk.Button(self.search_area, text="X", font=("Arial", 11, "bold"), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=10, pady=4, command=lambda: self.search_var.set("")).pack(side="left", padx=(6, 0))

        self.search_var.trace_add("write", self._on_search_typed)

        self.loading_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_equipment_data, daemon=True).start()

    def _clear_search_silently(self):
        self._suppress_search = True
        self.search_var.set("")
        self._suppress_search = False
        self.search_query = ""

    def _back_from_search(self):
        self._clear_search_silently()
        self._show_departments(refresh=False)

    def _on_search_typed(self, *_):
        if self._suppress_search:
            return

        if not hasattr(self, "content_frame") or not self.content_frame.winfo_exists():
            return

        query = self.search_var.get().strip()

        if not query:
            self.search_query = ""
            if getattr(self, "current_view", "") == "search":
                self._show_departments(refresh=False)
            return

        self.search_query = query
        self.search_page = 0
        self._render_search_results()

    def clear_search_entry(self):
        self.search_entry.delete(0, tk.END)

    def _render_search_results(self):
        self.current_view = "search"
        self._clear_content()
        self.title_label.config(text="Browse Equipment - Search")

        back_btn = tk.Button(self.content_frame, text="< Back to Departments", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0, command=self._back_from_search)
        back_btn.pack(anchor="w", padx=0, pady=(10, 15))

        q = self.search_query.lower()
        entries = []

        for d in self.all_departments:
            if q in d["name"].lower():
                items = [i for i in self.all_equipment if i.get("department_id") == d["id"]]
                entries.append(("department", d, items))

        for c in self.all_categories:
            if q in c["name"].lower():
                dept = next((d for d in self.all_departments if d["id"] == c.get("department_id")), None)
                items = [i for i in self.all_equipment if i.get("category_id") == c["id"]]
                entries.append(("category", c, (dept, items)))

        for i in self.all_equipment:
            if q in i["name"].lower():
                entries.append(("equipment", i, None))

        self.search_results = entries

        if not entries:
            tk.Label(self.content_frame, text=f"No results found for '{self.search_query}'.", font=("Arial", 14), bg="#1E293B", fg="#94A3B8").pack(pady=20)
            return

        start_index = self.search_page * GRID_ITEMS_PER_PAGE
        page_entries = entries[start_index:start_index + GRID_ITEMS_PER_PAGE]

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for kind, data, extra in page_entries:
            if kind == "department":
                self._create_department_card(cards_row, data["name"], extra, row, col)
            elif kind == "category":
                dept, items = extra
                self._create_search_category_card(cards_row, data, dept, items, row, col)
            else:
                self._create_equipment_card(cards_row, data, row, col, show_location=True)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        self._search_pagination_controls()

    def _search_pagination_controls(self):
        total_pages = max(1, -(-len(self.search_results) // GRID_ITEMS_PER_PAGE))
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.search_page > 0 else "disabled", command=self._go_previous_search_page).pack(side="left", padx=5)
        tk.Label(nav_frame, text=f"Page {self.search_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)
        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.search_page < total_pages - 1 else "disabled", command=self._go_next_search_page).pack(side="left", padx=5)

    def _go_next_search_page(self):
        self.search_page += 1
        self._render_search_results()

    def _go_previous_search_page(self):
        self.search_page -= 1
        self._render_search_results()

    def _create_search_category_card(self, parent, category, dept, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        dept_name = dept["name"] if dept else "N/A"
        dept_label = tk.Label(card, text=dept_name, font=("Arial", 10), bg="#334155", fg="#94A3B8")
        dept_label.pack(pady=(10, 0))

        name_label = tk.Label(card, text=category["name"], font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(15, 20))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, dept_label, name_label, count_label):
            widget.bind("<Button-1>", lambda e, c=category, d=dept: self._open_category_from_search(c, d))

    def _open_category_from_search(self, category, dept):
        if dept is None:
            return
        dept_items = [i for i in self.all_equipment if i.get("department_id") == dept["id"]]
        self.current_department_id = dept["id"]
        self.current_department = dept["name"]
        self.current_dept_items = dept_items
        self.department_categories = [c for c in self.all_categories if c["department_id"] == dept["id"]]
        self.current_category_page = 0
        self._clear_search_silently()
        self._show_equipment_by_category(category["name"], [i for i in dept_items if i.get("category_id") == category["id"]])

    def _fetch_equipment_data(self):
        equipment_list = get_all_equipment()
        self.main_frame.after(0, self._render_equipment_list, equipment_list)

    def _render_equipment_list(self, equipment_list):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_equipment = equipment_list
        self.all_departments = get_all_departments()
        self.all_categories = get_all_categories()

        self.content_frame = tk.Frame(self.main_frame, bg=self.primary_bg)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._show_departments()
        self._start_polling()

        if self.search_var.get().strip():
            self._on_search_typed()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _generic_grid(self, parent):
        row_frame = tk.Frame(parent, bg=self.primary_bg)
        row_frame.pack(fill="x", padx=10, pady=10)
        for col in range(3):
            row_frame.grid_columnconfigure(col, weight=1)
        return row_frame

    def _show_departments(self, refresh=True):
        self.current_view = "departments"
        self._clear_content()
        self.title_label.config(text="Browse Equipment")

        if refresh:
            self.all_equipment = get_all_equipment()
        self._last_signature = self._current_signature()

        self.all_equipment = get_all_equipment()
        self._last_signature = self._current_signature()

        if not self.all_departments:
            empty_label = tk.Label(self.content_frame, text="No departments found.", font=("Arial", 24), bg="#1E293B", fg="#94A3B8", height=50)
            empty_label.pack(pady=20)
            return

        grouped = {dept["name"]: [] for dept in self.all_departments}

        for item in self.all_equipment:
            dept_data = item.get("departments")
            department = dept_data.get("name") if dept_data else "Unassigned"
            grouped.setdefault(department, [])
            grouped[department].append(item)

        self.current_department_list = list(grouped.items())

        start_index = self.current_department_page * GRID_ITEMS_PER_PAGE
        end_index = start_index + GRID_ITEMS_PER_PAGE
        page_departments = self.current_department_list[start_index:end_index]

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for department, items in page_departments:
            self._create_department_card(cards_row, department, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        self._department_pagination_controls()

    def _department_pagination_controls(self):
        total_items = len(self.current_department_list)
        total_pages = max(1, -(-total_items // GRID_ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_department_page > 0 else "disabled",command=self._go_previous_department_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_department_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_department_page < total_pages - 1 else "disabled",command=self._go_next_department_page).pack(side="left", padx=5)

    def _go_next_department_page(self):
        self.current_department_page += 1
        self._show_departments()

    def _go_previous_department_page(self):
        self.current_department_page -= 1
        self._show_departments()

    def _create_department_card(self, parent, department, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        name_label = tk.Label(card, text=department, font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(30, 30))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, name_label, count_label):
            widget.bind("<Button-1>", lambda e, d=department, its=items: self._open_department(d, its))

    def _show_categories(self, department, dept_items):
        self.current_view = "categories"
        self.current_department = department
        self.current_dept_items = dept_items
        self._clear_content()
        self.title_label.config(text=f"Browse Equipment - {department}")

        back_btn = tk.Button(self.content_frame, text="< Back to Departments", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0, command=self._show_departments)
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        if not self.department_categories:
            empty_label = tk.Label(self.content_frame, text="No categories found.", font=("Arial", 14), bg="#1E293B", fg="#94A3B8")
            empty_label.pack(pady=20)
            return

        grouped = {cat["name"]: [] for cat in self.department_categories}

        for item in dept_items:
            category_data = item.get("categories")
            category = category_data.get("name") if category_data else "Uncategorized"
            grouped.setdefault(category, [])
            grouped[category].append(item)

        self.current_category_list = list(grouped.items())

        start_index = self.current_category_page * GRID_ITEMS_PER_PAGE
        end_index = start_index + GRID_ITEMS_PER_PAGE
        page_categories = self.current_category_list[start_index:end_index]

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for category, items in page_categories:
            self._create_category_card(cards_row, category, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        self._category_pagination_controls()

    def _category_pagination_controls(self):
        total_items = len(self.current_category_list)
        total_pages = max(1, -(-total_items // GRID_ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5,state="normal" if self.current_category_page > 0 else "disabled",command=self._go_previous_category_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_category_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_category_page < total_pages - 1 else "disabled",command=self._go_next_category_page).pack(side="left", padx=5)

    def _go_next_category_page(self):
        self.current_category_page += 1
        self._show_categories(self.current_department, self.current_dept_items)

    def _go_previous_category_page(self):
        self.current_category_page -= 1
        self._show_categories(self.current_department, self.current_dept_items)

    def _create_category_card(self, parent, category, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        name_label = tk.Label(card, text=category, font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(30, 30))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, name_label, count_label):
            widget.bind("<Button-1>", lambda e, cat=category, its=items: self._show_equipment_by_category(cat, its))

    def _open_department(self, department, items):
        self._clear_search_silently()
        dept = next((d for d in self.all_departments if d["name"] == department), None)
        self.current_department_id = dept["id"] if dept else None
        self.current_category_page = 0
        self.department_categories = [
            c for c in self.all_categories
            if dept and c["department_id"] == dept["id"]
        ]
        self._show_categories(department, items)

    def _show_equipment_by_category(self, category, items):
        cat = next((c for c in self.department_categories if c["name"] == category), None)
        self.current_category_id = cat["id"] if cat else None
        self.current_category = category
        self.current_items = items
        self.current_page = 0
        self._render_category_page()

    def _create_equipment_card(self, parent, item, row, col, show_location=False):
        self.card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        self.card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.card.grid_propagate(False)

        widgets = [self.card]
        condition = item.get("condition", "Good")
        condition_color = {"Good": "#4ADE80", "Fair": "#FBBF24"}.get(condition, "#F87171")
        status_color = "#4ADE80" if item["status"] == "Available" else "#F87171"

        if show_location:
            dept_name = (item.get("departments") or {}).get("name", "N/A")
            cat_name = (item.get("categories") or {}).get("name", "N/A")

            location_label = tk.Label(self.card, text=f"{dept_name} > {cat_name}", font=("Arial", 10), bg="#334155",
                                      fg="#94A3B8")
            location_label.pack(pady=(12, 0))

            name_label = tk.Label(self.card, text=item["name"], font=("Arial", 16, "bold"), bg="#334155", fg="#FFFFFF")
            name_label.pack(pady=(15, 15))

            info_row = tk.Frame(self.card, bg="#334155")
            info_row.pack()

            status_label = tk.Label(info_row, text=item["status"], font=("Arial", 13, "bold"), bg="#334155", fg=status_color)
            status_label.pack(side="left", pady=5)

            separator = tk.Label(info_row, text=" | ", font=("Arial", 13), bg="#334155", fg="#94A3B8")
            separator.pack(side="left", pady=5)

            condition_label = tk.Label(info_row, text=condition, font=("Arial", 13), bg="#334155", fg=condition_color)
            condition_label.pack(side="left", pady=5)

            widgets.extend([location_label, name_label, info_row, status_label, separator, condition_label])
        else:
            name_label = tk.Label(self.card, text=item["name"], font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
            name_label.pack(pady=(30, 30))

            status_label = tk.Label(self.card, text=item["status"], font=("Arial", 14, "bold"), bg="#334155", fg=status_color)
            status_label.pack(pady=(0, 10))

            condition_label = tk.Label(self.card, text=f"Condition: {condition}", font=("Arial", 14), bg="#334155",fg=condition_color)
            condition_label.pack(pady=(0, 5))

            widgets.extend([name_label, status_label, condition_label])

        for widget in widgets:
            widget.bind("<Button-1>", lambda e, it=item: self._show_equipment_details(it))

    def _render_category_page(self):
        self.current_view = "equipment"
        self.all_equipment = get_all_equipment()
        self._last_signature = self._current_signature()
        self.current_dept_items = [
            i for i in self.all_equipment
            if i.get("department_id") == self.current_department_id
        ]
        self.current_items = [
            i for i in self.current_dept_items
            if (i.get("categories") or {}).get("name") == self.current_category
        ]

        self._clear_content()
        self.title_label.config(text=f"Browse Equipment - {self.current_department} - {self.current_category}")

        back_btn = tk.Button(self.content_frame, text="< Back to Categories", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0, command=lambda: self._show_categories(self.current_department, self.current_dept_items))
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        if not self.current_items:
            empty_label = tk.Label(self.content_frame, text="No equipment found.", font=("Arial", 14), bg="#1E293B", fg="#94A3B8")
            empty_label.pack(pady=20)
            return

        start_index = self.current_page * GRID_ITEMS_PER_PAGE
        end_index = start_index + GRID_ITEMS_PER_PAGE
        page_items = self.current_items[start_index:end_index]

        cards_row = tk.Frame(self.content_frame, bg="#1E293B")
        cards_row.pack(fill="x", padx=10)
        for col in range(3):
            cards_row.grid_columnconfigure(col, weight=1)

        row, col = 0, 0
        for item in page_items:
            self._create_equipment_card(cards_row, item, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        self._pagination_controls()

    def _pagination_controls(self):
        total_items = len(self.current_items)
        total_pages = max(1, -(-total_items // GRID_ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg="#1E293B")
        nav_frame.pack(pady=(20, 10))

        prev_btn = tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled",command=self._go_previous_page)
        prev_btn.pack(side="left", padx=5)

        page_label = tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}",
                               font=("Arial", 12), bg="#1E293B", fg="#94A3B8")
        page_label.pack(side="left", padx=15)

        next_btn = tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page < total_pages - 1 else "disabled", command=self._go_next_page)
        next_btn.pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_category_page()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_category_page()

    def _show_equipment_details(self, item):
        self.details_overlay = tk.Frame(self.parent, bg="#1E293B")
        self.details_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.modal = tk.Frame(self.details_overlay, bg="#334155", width=450, height=300)
        self.modal.place(relx=0.5, rely=0.5, anchor="center")
        self.modal.pack_propagate(False)

        self.cancel_area = tk.Frame(self.modal, bg="#334155")
        self.cancel_area.pack(fill="x", pady=10)

        self.close_btn = tk.Button(self.cancel_area, text="X", font=("Arial", 12), bg="#F93111", fg="#FFFFFF", cursor="hand2", bd=0, width=3, command=self.details_overlay.destroy)
        self.close_btn.pack(side="right", pady=5, padx=(0, 10))

        self.name_label = tk.Label(self.modal, text=item["name"], font=("Arial", 20, "bold"), bg="#334155", fg="#94A3B8")
        self.name_label.pack(pady=5)

        self.name_department = item.get("departments", {}).get("name", "N/A")
        self.department_label = tk.Label(self.modal, text=f"Department: {self.name_department}", font=("Arial", 14), bg="#334155", fg="#94A3B8")
        self.department_label.pack(pady=5)

        self.name_category = item.get("categories", {}).get("name", "N/A")
        self.category_label = tk.Label(self.modal, text=f"Category: {self.name_category}", font=("Arial", 14), bg="#334155", fg="#94A3B8")
        self.category_label.pack(pady=5)

        condition = item.get("condition", "Good")
        is_available = item.get("status") == "Available" and condition not in ("Damaged", "Under Repair")

        self.reserve_btn = tk.Button(self.modal, text="Reserve" if is_available else item.get("status", "Unavailable"), font=("Arial", 14, "bold"), bg="#3AFD50" if is_available else "#F87171", fg="#0F172A", cursor="hand2" if is_available else "arrow", state="normal" if is_available else "disabled", disabledforeground="#FFFFFF",command=lambda: self._confirm_reservation(item))
        self.reserve_btn.pack(pady=(60, 5))

    def _category_by_name(self, name):
        return next((c for c in self.department_categories if c["name"] == name), None)

    def _confirm_reservation(self, item):
        result = create_reservation(
            user_id=self.current_user_id,
            equipment_id=item["id"],
            reserved_date=date.today(),
            return_date=date.today() + timedelta(days=3),
        )

        if result == "success":
            messagebox.showinfo("Success", f"Reservation request sent: {item['name']}")
            self.details_overlay.destroy()
        elif result == "duplicate":
            messagebox.showinfo("Already Requested", "You already have a pending request for this equipment.")
        elif result == "unavailable":
            messagebox.showinfo("Unavailable", "This equipment is currently unavailable.")
            self._sync_equipment()
        elif result == "damaged":
            messagebox.showinfo("Unavailable", "This equipment is currently under repair or damaged.")
            self._sync_equipment()
        else:
            messagebox.showerror("Error", "Failed to submit reservation.")

    def _sync_equipment(self):
        self.all_equipment = get_all_equipment()
        self._last_signature = self._current_signature()
        self._refresh_current_view()

    @staticmethod
    def _make_signature(equipment_list, departments, categories):
        return (
            sorted((e["id"], e.get("name"), e.get("status"), e.get("condition"),
                    e.get("department_id"), e.get("category_id")) for e in equipment_list),
            sorted((d["id"], d["name"]) for d in departments),
            sorted((c["id"], c["name"], c.get("department_id")) for c in categories),
        )

    def _current_signature(self):
        return self._make_signature(self.all_equipment, self.all_departments, self.all_categories)

    def _start_polling(self):
        self._last_signature = self._current_signature()
        # noinspection PyTypeChecker
        self.main_frame.after(POLL_INTERVAL_MS, self._poll_equipment)

    def _poll_equipment(self):
        if not self.main_frame.winfo_exists():
            return
        threading.Thread(target=self._poll_worker, daemon=True).start()

    def _poll_worker(self):
        equipment = get_all_equipment()
        departments = get_all_departments()
        categories = get_all_categories()
        try:
            # noinspection PyTypeChecker
            self.main_frame.after(0, lambda: self._apply_poll_result(equipment, departments, categories))
        except (tk.TclError, RuntimeError):
            pass

    def _apply_poll_result(self, equipment, departments, categories):
        if not self.main_frame.winfo_exists():
            return

        if equipment and departments:
            signature = self._make_signature(equipment, departments, categories)
            if signature != self._last_signature:
                self._last_signature = signature
                self.all_equipment = equipment
                self.all_departments = departments
                self.all_categories = categories
                self._refresh_current_view()
                messagebox.showinfo(
                    "Equipment Updated",
                    "Sorry for the interruption. The equipment information has been updated."
                )

        # noinspection PyTypeChecker
        self.main_frame.after(POLL_INTERVAL_MS, lambda: self._poll_equipment())

    def _refresh_current_view(self):
        overlay = getattr(self, "details_overlay", None)
        if overlay is not None and overlay.winfo_exists():
            overlay.destroy()

        view = getattr(self, "current_view", "departments")

        if view == "search":
            self._render_search_results()
            return

        if view in ("categories", "equipment"):
            dept = next((d for d in self.all_departments if d["id"] == self.current_department_id), None)
            if dept is None:
                view = "departments"
            else:
                self.current_department = dept["name"]
                self.department_categories = [c for c in self.all_categories if c["department_id"] == dept["id"]]
                self.current_dept_items = [i for i in self.all_equipment if i.get("department_id") == dept["id"]]

        if view == "equipment":
            cat = next((c for c in self.department_categories if c["id"] == self.current_category_id), None)
            if cat is None:
                view = "categories"
            else:
                self.current_category = cat["name"]
                self._render_category_page()
                return

        if view == "categories":
            self._show_categories(self.current_department, self.current_dept_items)
        else:
            self._show_departments()