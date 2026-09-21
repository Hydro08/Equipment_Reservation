import tkinter as tk
import threading

from Authentication.auth_service import get_all_equipment, get_all_departments, get_all_categories
from tkinter import messagebox

ITEMS_PER_PAGE = 6

class BrowseEquipmentPage:
    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self._build_ui()

    def _build_ui(self):
        self.main_frame = tk.Frame(self.parent, bg="#1E293B")
        self.main_frame.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.main_frame, text="Browse Equipment", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 10))

        self.loading_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=20)

        threading.Thread(target=self._fetch_equipment_data, daemon=True).start()

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

        self.content_frame = tk.Frame(self.main_frame, bg="#1E293B")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._show_departments()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    @staticmethod
    def _generic_grid(parent):
        row_frame = tk.Frame(parent, bg="#1E293B")
        row_frame.pack(fill="x", padx=10, pady=10)
        for col in range(3):
            row_frame.grid_columnconfigure(col, weight=1)
        return row_frame

    def _show_departments(self):
        self._clear_content()
        self.title_label.config(text="Browse Equipment")

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

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for department, items in grouped.items():
            self._create_department_card(cards_row, department, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

    def _create_department_card(self, parent, department, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        name_label = tk.Label(card, text=department, font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(30, 30))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, name_label, count_label):
            widget.bind("<Button-1>", lambda e, d=department, its=items: self._show_categories(d, its))

    def _show_categories(self, department, dept_items):
        self.current_department = department
        self.current_dept_items = dept_items
        self._clear_content()
        self.title_label.config(text=f"Browse Equipment - {department}")

        back_btn = tk.Button(self.content_frame, text="< Back to Departments", font=("Arial", 12),
                              bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0,
                              command=self._show_departments)
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        if not self.all_categories:
            empty_label = tk.Label(self.content_frame, text="No categories found.",
                                    font=("Arial", 14), bg="#1E293B", fg="#94A3B8")
            empty_label.pack(pady=20)
            return

        grouped = {cat["name"]: [] for cat in self.all_categories}

        for item in dept_items:
            category_data = item.get("categories")
            category = category_data.get("name") if category_data else "Uncategorized"
            grouped.setdefault(category, [])
            grouped[category].append(item)

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for category, items in grouped.items():
            self._create_category_card(cards_row, category, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

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

    def _show_equipment_by_category(self, category, items):
        self.current_category = category
        self.current_items = items
        self.current_page = 0
        self._render_category_page()

    def _render_category_page(self):
        self._clear_content()
        self.title_label.config(text=f"Browse Equipment - {self.current_department} - {self.current_category}")

        back_btn = tk.Button(self.content_frame, text="< Back to Categories", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0, command=lambda: self._show_categories(self.current_department, self.current_dept_items))
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        start_index = self.current_page * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE
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

    def _create_equipment_card(self, parent, item, row, col):
        self.card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        self.card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.card.grid_propagate(False)

        name_label = tk.Label(self.card, text=item["name"], font=("Arial", 16, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(30, 30))

        status_label = tk.Label(self.card, text=item["status"], font=("Arial", 14, "bold"), bg="#334155", fg="#4ADE80" if item["status"] == "Available" else "#F87171")
        status_label.pack(pady=(0, 10))

        for widget in (self.card, name_label, status_label):
            widget.bind("<Button-1>", lambda e, it=item: self._show_equipment_details(it))

    def _pagination_controls(self):
        total_items = len(self.current_items)
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))

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

        self.modal = tk.Frame(self.details_overlay, bg="#334155", width=400, height=300)
        self.modal.place(relx=0.5, rely=0.5, anchor="center")
        self.modal.pack_propagate(False)

        self.name_label = tk.Label(self.modal, text=item["name"], font=("Arial", 20, "bold"), bg="#334155", fg="#94A3B8")
        self.name_label.pack(pady=5)

        self.name_category = item.get("categories", {}).get("name", "N/A")
        self.category_label = tk.Label(self.modal, text=f"Category: {self.name_category}", font=("Arial", 14), bg="#334155", fg="#94A3B8")
        self.category_label.pack(pady=5)

        self.reserve_btn = tk.Button(self.modal, text="Reserve", font=("Arial", 14, "bold"), bg="#3AFD50", fg="#0F172A", cursor="hand2", command=lambda: self._confirm_reservation(item))
        self.reserve_btn.pack(pady=(115, 5))

        self.close_btn = tk.Button(self.modal, text="Close", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", command=self.details_overlay.destroy)
        self.close_btn.pack(pady=5)

    def _confirm_reservation(self, item):
        messagebox.showinfo("Confirmation", f"Reserving: {item['name']}")
        self.details_overlay.destroy()