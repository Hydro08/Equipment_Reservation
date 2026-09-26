import tkinter as tk
import threading

from tkinter import messagebox

from Admin.pages.inventory_forms import DepartmentForm, CategoryForm, EquipmentForm
from Authentication.auth_service import (
    get_all_equipment, get_all_departments, get_all_categories,
    add_department, update_department, delete_department,
    add_category, update_category, delete_category,
    add_equipment, update_equipment, delete_equipment, equipment_has_active_reservation,
)

GRID_ITEMS_PER_PAGE = 9

class ManageInventoryPage:

    primary_bg = "#1E293B"
    primary_fg = "#FFFFFF"

    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.current_page = 0
        self.current_department_page = 0
        self.current_category_page = 0

        self._build_ui()

    def _build_ui(self):
        self.manage_inventory_panel = tk.Frame(self.parent, bg=self.primary_bg)
        self.manage_inventory_panel.pack(fill="both", expand=True)

        self.title_label = tk.Label(self.manage_inventory_panel, text="Manage Inventory", font=("Arial", 24, "bold"), **self.colors)
        self.title_label.pack(pady=(20, 0))

        self.loading_label = tk.Label(self.manage_inventory_panel, text="Loading...", font=("Arial", 24), **self.colors, height=50)
        self.loading_label.pack(pady=(20, 0))

        threading.Thread(target=self._fetch_manage_equipment_data, daemon=True).start()

    def _fetch_manage_equipment_data(self):
        equipment_list = get_all_equipment()
        self.manage_inventory_panel.after(0, self._render_equipment_list, equipment_list)

    def _render_equipment_list(self, equipment_list):
        if not self.loading_label.winfo_exists():
            return

        self.loading_label.destroy()
        self.all_equipment = equipment_list
        self.all_departments = get_all_departments()
        self.all_categories = get_all_categories()

        self.content_frame = tk.Frame(self.manage_inventory_panel, bg=self.primary_bg)
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

    def _department_by_name(self, name):
        return next((d for d in self.all_departments if d["name"] == name), None)

    def _category_by_name(self, name):
        return next((c for c in self.all_categories if c["name"] == name), None)

    def _equipment_for_department(self, department_name):
        result = []
        for item in self.all_equipment:
            dept_data = item.get("departments")
            dept_name = dept_data.get("name") if dept_data else "Unassigned"
            if dept_name == department_name:
                result.append(item)
        return result

    @staticmethod
    def _equipment_for_category(department_items, category_name):
        result = []
        for item in department_items:
            cat_data = item.get("categories")
            cat_name = cat_data.get("name") if cat_data else "Uncategorized"
            if cat_name == category_name:
                result.append(item)
        return result

    def _refresh_after_department_change(self):
        self._refresh_data()
        self.current_department_page = 0
        self._show_departments()

    def _refresh_after_category_change(self):
        self._refresh_data()
        self.current_dept_items = self._equipment_for_department(self.current_department)
        self.current_category_page = 0
        self._show_categories(self.current_department, self.current_dept_items)

    def _refresh_after_equipment_change(self):
        self._refresh_data()
        self.current_dept_items = self._equipment_for_department(self.current_department)
        self.current_items = self._equipment_for_category(self.current_dept_items, self.current_category)
        self._render_category_page()

    def _show_departments(self):
        self._clear_content()
        self.title_label.config(text="Manage Inventory")

        grouped = {dept["name"]: [] for dept in self.all_departments}

        for item in self.all_equipment:
            dept_data = item.get("departments")
            department = dept_data.get("name") if dept_data else "Unassigned"
            grouped.setdefault(department, [])
            grouped[department].append(item)

        self.current_department_list = list(grouped.items())

        page_departments, show_add, total_pages = self._paginate_with_add_card(self.current_department_list, self.current_department_page)

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for department, items in page_departments:
            self._create_department_card(cards_row, department, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        if show_add:
            self._create_add_card(cards_row, row, col, self._open_add_department_form)

        self._department_pagination_controls(total_pages)

    def _department_pagination_controls(self, total_pages):
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_department_page > 0 else "disabled",command=self._go_previous_department_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_department_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_department_page < total_pages - 1 else "disabled", command=self._go_next_department_page).pack(side="left", padx=5)

    def _go_next_department_page(self):
        self.current_category_page += 1
        self._show_departments()

    def _go_previous_department_page(self):
        self.current_category_page -= 1
        self._show_departments()

    def _create_department_card(self, parent, department, items, row, col):
        card = tk.Frame(parent, bg="#334155", cursor="hand2", height=180)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        options_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg, cursor="hand2")
        options_btn.place(relx=1.0, x=-15, y=10, anchor="ne")
        options_btn.bind("<Button-1>", lambda e: self._show_options_menu(e, lambda: self._open_edit_department_form(department), lambda: self._confirm_delete_department(department, items)))

        name_label = tk.Label(card, text=department, font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg)
        name_label.pack(pady=(35, 30))

        count_label = tk.Label(card, text=f"{len(items)} item(s)", font=("Arial", 12), bg="#334155", fg="#94A3B8")
        count_label.pack(pady=(0, 10))

        for widget in (card, name_label, count_label):
            widget.bind("<Button-1>", lambda e, d=department, its=items: self._open_department(d, its))

    def _open_department(self, department, items):
        self.current_category_page = 0
        self._show_categories(department, items)

    def _show_categories(self, department, dept_items):
        self.current_department = department
        self.current_dept_items = dept_items
        self._clear_content()
        self.title_label.config(text=f"Manage Inventory - {department}")

        back_btn = tk.Button(self.content_frame, text="< Back to Departments", font=("Arial", 12), bg=self.primary_bg, fg=self.primary_fg, cursor="hand2", bd=0, command=self._show_departments)
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        grouped = {cat["name"]: [] for cat in self.all_categories}

        for item in dept_items:
            category_data = item.get("categories")
            category = category_data.get("name") if category_data else "Uncategorized"
            grouped.setdefault(category, [])
            grouped[category].append(item)

        self.current_category_list = list(grouped.items())

        page_categories, show_add, total_pages = self._paginate_with_add_card(
            self.current_category_list, self.current_category_page
        )

        cards_row = self._generic_grid(self.content_frame)

        row, col = 0, 0
        for category, items in page_categories:
            self._create_category_card(cards_row, category, items, row, col)
            col += 1
            if col > 2:
                col, row = 0, row + 1

        if show_add:
            self._create_add_card(cards_row, row, col, self._open_add_category_form)

        self._category_pagination_controls(total_pages)

    def _category_pagination_controls(self, total_pages):
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg=self.primary_bg)
        nav_frame.pack(pady=(20, 10))

        tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_category_page > 0 else "disabled",command=self._go_previous_category_page).pack(side="left", padx=5)

        tk.Label(nav_frame, text=f"Page {self.current_category_page + 1} of {total_pages}", font=("Arial", 12), bg=self.primary_bg, fg="#94A3B8").pack(side="left", padx=15)

        tk.Button(nav_frame, text="Next >", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_category_page < total_pages - 1 else "disabled", command=self._go_next_category_page).pack(side="left", padx=5)

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

        option_btn = tk.Label(card, text="⋮", font=("Arial", 18, "bold"), bg="#334155", fg=self.primary_fg, cursor="hand2")
        option_btn.place(relx=1.0, x=-15, y=10, anchor="ne")
        option_btn.bind("<Button-1>", lambda e: self._show_options_menu(
            e, lambda: self._open_edit_category_form(category), lambda: self._confirm_delete_category(category, items)
        ))

        name_label = tk.Label(card, text=category, font=("Arial", 18, "bold"), bg="#334155", fg="#FFFFFF")
        name_label.pack(pady=(40, 20))

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
        self.title_label.config(text=f"Manage Inventory - {self.current_department} - {self.current_category}")

        back_btn = tk.Button(self.content_frame, text="< Back to Categories", font=("Arial", 12), bg="#1E293B", fg="#FFFFFF", cursor="hand2", bd=0, command=lambda: self._show_categories(self.current_department, self.current_dept_items))
        back_btn.pack(anchor="w", padx=10, pady=(10, 15))

        page_items, show_add, total_pages = self._paginate_with_add_card(
            self.current_items, self.current_page
        )

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

        if show_add:
            self._create_add_card(cards_row, row, col, self._open_add_equipment_form)

        self._pagination_controls(total_pages)

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

        status_label = tk.Label(self.card, text=item["status"], font=("Arial", 14, "bold"), bg="#334155", fg="#4ADE80" if item["status"] == "Available" else "#F87171")
        status_label.pack(pady=(0, 10))

    def _paginate_with_add_card(self, entries, current_page):
        total_items = len(entries)
        total_slots = total_items + 1
        total_pages = max(1, -(-total_slots // GRID_ITEMS_PER_PAGE))

        start_index = current_page * GRID_ITEMS_PER_PAGE
        end_index = start_index + GRID_ITEMS_PER_PAGE
        page_entries = entries[start_index:end_index]

        show_add_card = start_index <= total_items < end_index

        return page_entries, show_add_card, total_pages

    def _pagination_controls(self, total_pages):
        if total_pages <= 1:
            return

        nav_frame = tk.Frame(self.content_frame, bg="#1E293B")
        nav_frame.pack(pady=(20, 10))

        prev_btn = tk.Button(nav_frame, text="< Previous", font=("Arial", 12), bg="#334155", fg="#FFFFFF", cursor="hand2", bd=0, padx=15, pady=5, state="normal" if self.current_page > 0 else "disabled", command=self._go_previous_page)
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

    def _open_add_department_form(self):
        DepartmentForm(self.content_frame, on_save=self._handle_add_department)

    def _handle_add_department(self, name):
        if add_department(name):
            self._refresh_after_department_change()

    def _open_edit_department_form(self, department_name):
        dept = self._department_by_name(department_name)
        if not dept:
            return
        DepartmentForm(self.content_frame, initial_name=dept["name"],
                       on_save=lambda new_name: self._handle_update_department(dept["id"], new_name))

    def _handle_update_department(self, department_id, new_name):
        if update_department(department_id, new_name):
            self._refresh_after_department_change()

    def _confirm_delete_department(self, department_name, items):
        if items:
            messagebox.showwarning("Cannot Delete", f"'{department_name}' still has {len(items)} equipment item(s).")
            return
        dept = self._department_by_name(department_name)
        if not dept:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete department '{department_name}'?"):
            if delete_department(dept["id"]):
                self._refresh_after_department_change()

    def _open_add_category_form(self):
        CategoryForm(self.content_frame, on_save=self._handle_add_category)

    def _handle_add_category(self, name):
        if add_category(name):
            self._refresh_after_category_change()

    def _open_edit_category_form(self, category_name):
        cat = self._category_by_name(category_name)
        if not cat:
            return
        CategoryForm(self.content_frame, initial_name=cat["name"],on_save=lambda new_name: self._handle_update_category(cat["id"], new_name))

    def _handle_update_category(self, category_id, new_name):
        if update_category(category_id, new_name):
            self._refresh_after_category_change()

    def _confirm_delete_category(self, category_name, items):
        if items:
            messagebox.showwarning("Cannot Delete", f"'{category_name}' still has {len(items)} equipment item(s).")
            return
        cat = self._category_by_name(category_name)
        if not cat:
            return
        if messagebox.askyesno("Confirm Delete", f"Delete category '{category_name}'?"):
            if delete_category(cat["id"]):
                self._refresh_after_category_change()

    def _open_add_equipment_form(self):
        EquipmentForm(self.content_frame, self.all_categories, self.all_departments, on_save=self._handle_add_equipment)

    def _handle_add_equipment(self, data):
        if add_equipment(data["name"], data["category_id"], data["department_id"], data["status"]):
            self._refresh_after_equipment_change()

    def _open_edit_equipment_form(self, item):
        EquipmentForm(self.content_frame, self.all_categories, self.all_departments, on_save=lambda data: self._handle_update_equipment(item["id"], data), item=item)

    def _handle_update_equipment(self, equipment_id, data):
        if update_equipment(equipment_id, data):
            self._refresh_after_equipment_change()

    def _confirm_delete_equipment(self, item):
        if equipment_has_active_reservation(item["id"]):
            messagebox.showwarning("Cannot Delete", f"'{item['name']}' still has an active reservation.")
            return
        if messagebox.askyesno("Confirm Delete", f"Delete equipment '{item['name']}'?"):
            if delete_equipment(item["id"]):
                self._refresh_after_equipment_change()