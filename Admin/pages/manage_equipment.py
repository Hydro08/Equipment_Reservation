import tkinter as tk
import threading

from tkinter import messagebox

from Authentication.auth_service import get_all_equipment, get_all_departments, get_all_categories

ITEMS_PER_PAGE = 6

class ManageEquipmentPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0

        self._build_ui()

    def _build_ui(self):
        self.main_frame = tk.Frame(self.parent, bg=self.primary_bg)
        self.main_frame.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.main_frame, text="Manage Equipment", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.main_frame, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_manage_equipment_data, daemon=True).start()

    def _fetch_manage_equipment_data(self):
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

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _generic_grid(self, parent):
        row_frame = tk.Frame(parent, bg=self.primary_bg)
        row_frame.pack(fill="x", padx=10, pady=10)
        for col in range(3):
            row_frame.grid_columnconfigure(col, weight=1)
        return row_frame

    def _show_options_menu(self, event, edit_command, delete_command):
        menu = tk.Menu(self.content_frame, tearoff=0, bg="#334155", fg=self.primary_fg, activebackground=self.primary_bg, activeforeground=self.primary_fg)
        menu.add_command(label="Edit", command=edit_command)
        menu.add_command(label="Delete", command=delete_command)
        menu.tk_popup(event.x_root, event.y_root)

    def _create_add_card(self, parent, row, col, on_click):
        card = tk.Frame(parent, bg=self.primary_bg, height=180, cursor="hand2", highlightbackground="#94A3B8", highlightthickness=1)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        plus_label = tk.Label(card, text="+", font=("Arial", 32), bg=self.primary_bg, fg="#94A3B8")
        plus_label.pack(pady=(30, 10))

        text_label = tk.Label(card, text="Add New", font=("Arial", 14), bg=self.primary_bg, fg="#94A3B8")
        text_label.pack(pady=(0, 10))

        for widget in (card, plus_label, text_label):
            widget.bind("<Button-1>", lambda e: on_click())

    def _refresh_data(self):
        self.all_equipment = get_all_equipment()
        self.all_departments = get_all_departments()
        self.all_categories = get_all_categories()

    def _show_departments(self):
        self._clear_content()
        self.title_label.config(text="Manage Equipment")

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

        self._create_add_card(cards_row, row, col, self._open_add_department_form)

    def _create_department_card(self, parent, department, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        options_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg, cursor="hand2")
        options_btn.place(relx=1.0, x=-15, y=10, anchor="ne")
        options_btn.bind("<Button-1>", lambda e: self._show_options_menu(e, lambda: self._open_edit_department_form(department), lambda: self._confirm_delete_department(department, items)))

        name_label = tk.Label(card, text=department, font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg)
        name_label.pack(pady=(30, 30))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, name_label, count_label):
            widget.bind("<Button-1>", lambda e, d=department, its=items: self._show_categories(d, its))

    def _show_categories(self, department, dept_items):
        self.current_department = department
        self.current_dept_items = dept_items
        self._clear_content()
        self.title_label.config(text=f"Manage Equipment - {department}")

        back_btn = tk.Button(self.content_frame, text="< Back to Departments", font=("Arial", 12), bg=self.primary_bg, fg=self.primary_fg, cursor="hand2", bd=0, command=self._show_departments)
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

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

        self._create_add_card(cards_row, row, col, self._open_add_category_form)

    def _create_category_card(self, parent, category, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        option_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg, cursor="hand2")
        option_btn.place(relx=1.0, x=-15, y=10, anchor="ne")
        option_btn.bind("<Button-1>", lambda e: self._show_options_menu(
            e, lambda: self._open_edit_category_form(category), lambda: self._confirm_delete_category(category, items)
        ))

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

        back_btn = tk.Button(self.content_frame, text="< Back to Categories", font=("Arial", 12), bg="#1E293B",
                             fg="#FFFFFF", cursor="hand2", bd=0,
                             command=lambda: self._show_categories(self.current_department, self.current_dept_items))
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

        self._create_add_card(cards_row, row, col, self._open_add_equipment_form)

        self._pagination_controls()

    def _create_equipment_card(self, parent, item, row, col):
        self.card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        self.card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        self.card.grid_propagate(False)

        option_btn = tk.Label(self.card, text="⋮", font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg, cursor="hand2")
        option_btn.place(relx=1.0, x=-15, y=10, anchor="ne")
        option_btn.bind("<Button-1>", lambda e: self._show_options_menu(
            e, lambda: self._open_edit_equipment_form(item),
            lambda: self._confirm_delete_equipment(item)
        ))

        name_label = tk.Label(self.card, text=item["name"], font=("Arial", 16, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(30, 30))

        status_label = tk.Label(self.card, text=item["status"], font=("Arial", 14, "bold"), bg="#334155",
                                fg="#4ADE80" if item["status"] == "Available" else "#F87171")
        status_label.pack(pady=(0, 10))

    def _pagination_controls(self):
        total_items = len(self.current_items)
        total_pages = max(1, -(-total_items // ITEMS_PER_PAGE))

        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg="#1E293B")
        nav_frame.pack(pady=(20, 10))

        prev_btn = tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF",
                             cursor="hand2", bd=0, padx=15, pady=5,
                             state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page)
        prev_btn.pack(side="left", padx=5)

        page_label = tk.Label(nav_frame, text=f"Page {self.current_page + 1} of {total_pages}",
                              font=("Arial", 12), bg="#1E293B", fg="#94A3B8")
        page_label.pack(side="left", padx=15)

        next_btn = tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2",
                             bd=0, padx=15, pady=5,
                             state="normal" if self.current_page < total_pages - 1 else "disabled",
                             command=self._go_next_page)
        next_btn.pack(side="left", padx=5)

    def _go_next_page(self):
        self.current_page += 1
        self._render_category_page()

    def _go_previous_page(self):
        self.current_page -= 1
        self._render_category_page()

    @staticmethod
    def _open_add_department_form():
        messagebox.showinfo("TODO", "ADD Department form soon.")

    @staticmethod
    def _open_edit_department_form(department):
        messagebox.showinfo("TODO", f"Edit Department: {department}")

    @staticmethod
    def _confirm_delete_department(department, items):
        if items:
            messagebox.showwarning("Cannot Delete", f"'{department}' still has {len(items)} equipment item(s).")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete department '{department}'?")
        if confirm:
            messagebox.showinfo("TODO", "Delete Logic soon.")

    @staticmethod
    def _open_add_category_form():
        messagebox.showinfo("TODO", "Add Category form soon.")

    @staticmethod
    def _open_edit_category_form(category):
        messagebox.showinfo("TODO", f"Edit Category: {category}")

    @staticmethod
    def _confirm_delete_category(category, items):
        if items:
            messagebox.showwarning("Cannot Delete", f"'{category}' still has an {len(items)} equipment item(s).")
            return
        confirm = messagebox.askyesno("Confirm Delete", f"Delete category '{category}'")
        if confirm:
            messagebox.showinfo("TODO", "Delete logic soon.")

    @staticmethod
    def _open_add_equipment_form():
        messagebox.showinfo("TODO", "Add Equipment Form soon.")

    @staticmethod
    def _open_edit_equipment_form(item):
        messagebox.showinfo("TODO", f"Edit Equipment: '{item['name']}'?")

    @staticmethod
    def _confirm_delete_equipment(item):
        confirm = messagebox.askyesno("Confirm Delete", f"Delete equipment '{item['name']}'?")
        if confirm:
            messagebox.showinfo("TODO", "Delete logic soon.")