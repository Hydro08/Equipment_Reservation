import tkinter as tk
from tkinter import messagebox, ttk

BG = "#1E293B"
PANEL = "#334155"
FG = "#FFFFFF"

DEPT_CATE_WIDTH = 320
DEPT_CATE_HEIGHT = 160

class DepartmentForm(tk.Toplevel):
    def __init__(self, parent, on_save, initial_name=""):
        super().__init__(parent, bg=BG)
        self.title("Edit Department" if initial_name else "Add Department")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.on_save = on_save
        self._center_window()

        tk.Label(self, text="Department Name", font=("Arial", 13), bg=BG, fg=FG).grid(
            row=0, column=0, padx=20, pady=(20, 8), sticky="w")

        self.name_var = tk.StringVar(value=initial_name)
        entry = tk.Entry(self, textvariable=self.name_var, width=30, font=("Arial", 12),
                         bg=PANEL, fg=FG, insertbackground=FG, relief="flat")
        entry.grid(row=1, column=0, padx=20, pady=(0, 20), ipady=4)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=2, column=0, pady=(0, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=self._save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=PANEL, fg=FG, command=self.destroy, padx=16, pady=4, bd=0, cursor="hand2")
        cancel_btn.pack(side="left", padx=6)
        self.grab_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Field", "Department name is required.", parent=self)
            return
        self.on_save(name)
        self.destroy()
    
    def _center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - DEPT_CATE_WIDTH) // 2
        y = (screen_height - DEPT_CATE_HEIGHT) //2
        self.geometry(f"{DEPT_CATE_WIDTH}x{DEPT_CATE_HEIGHT}+{x}+{y}")

class CategoryForm(tk.Toplevel):
    def __init__(self, parent, on_save, initial_name=""):
        super().__init__(parent, bg=BG)
        self.title("Edit Category" if initial_name else "Add Category")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.on_save = on_save
        self._center_window()

        tk.Label(self, text="Category Name", font=("Arial", 13), bg=BG, fg=FG).grid(
            row=0, column=0, padx=20, pady=(20, 8), sticky="w")

        self.name_var = tk.StringVar(value=initial_name)
        entry = tk.Entry(self, textvariable=self.name_var, width=30, font=("Arial", 12), bg=PANEL, fg=FG, insertbackground=FG, relief="flat")
        entry.grid(row=1, column=0, padx=20, pady=(0, 20), ipady=4)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=2, column=0, pady=(0, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=self._save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=PANEL, fg=FG, command=self.destroy, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        self.grab_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Field", "Category name is required.", parent=self)
            return
        self.on_save(name)
        self.destroy()

    def _center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - DEPT_CATE_WIDTH) // 2
        y = (screen_height - DEPT_CATE_HEIGHT) //2
        self.geometry(f"{DEPT_CATE_WIDTH}x{DEPT_CATE_HEIGHT}+{x}+{y}")

class EquipmentForm(tk.Toplevel):
    STATUSES = ["Available", "Unavailable"]

    width = 300
    height = 380

    def __init__(self, parent, categories, departments, on_save, item=None):
        super().__init__(parent, bg=BG)
        self.title("Edit Equipment" if item else "Add Equipment")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.geometry("300x380+600+300")
        self.on_save = on_save
        self.categories = categories
        self.departments = departments

        self._center_window()

        item = item or {}
        category_name = (item.get("categories") or {}).get("name", "")
        department_name = (item.get("departments") or {}).get("name", "")

        tk.Label(self, text="Name", font=("Arial", 13), bg=BG, fg=FG).grid(row=0, column=0, padx=20, pady=(20, 6), sticky="w")
        self.name_var = tk.StringVar(value=item.get("name", ""))
        tk.Entry(self, textvariable=self.name_var, width=28, font=("Arial", 12), bg=PANEL, fg=FG, insertbackground=FG, relief="flat").grid(row=1, column=0, padx=20, pady=(0, 12), ipady=4)

        tk.Label(self, text="Category", font=("Arial", 13), bg=BG, fg=FG).grid(row=2, column=0, padx=20, pady=(0, 6), sticky="w")
        self.category_var = tk.StringVar(value=category_name)
        ttk.Combobox(self, textvariable=self.category_var, values=[c["name"] for c in categories], state="readonly", width=26).grid(row=3, column=0, padx=20, pady=(0, 12), ipady=3)

        tk.Label(self, text="Department", font=("Arial", 13), bg=BG, fg=FG).grid(row=4, column=0, padx=20, pady=(0, 6), sticky="w")
        self.department_var = tk.StringVar(value=department_name)
        ttk.Combobox(self, textvariable=self.department_var, values=[d["name"] for d in departments], state="readonly", width=26).grid(row=5, column=0, padx=20, pady=(0, 12), ipady=3)

        tk.Label(self, text="Status", font=("Arial", 13), bg=BG, fg=FG).grid(row=6, column=0, padx=20, pady=(0, 6), sticky="w")
        self.status_var = tk.StringVar(value=item.get("status", "Available"))
        ttk.Combobox(self, textvariable=self.status_var, values=self.STATUSES, state="readonly", width=26).grid(row=7, column=0, padx=20, pady=(0, 12), ipady=3)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=8, column=0, pady=(8, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=self._save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=PANEL, fg=FG, command=self.destroy, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        self.grab_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        name = self.name_var.get().strip()
        category_name = self.category_var.get()
        department_name = self.department_var.get()
        status = self.status_var.get()

        if not name:
            messagebox.showwarning("Missing Field", "Equipment name is required.", parent=self)
            return
        if not category_name or not department_name:
            messagebox.showwarning("Missing Field", "Please select a category and a department.", parent=self)
            return

        category = next((c for c in self.categories if c["name"] == category_name), None)
        department = next((d for d in self.departments if d["name"] == department_name), None)

        self.on_save({
            "name": name,
            "category_id": category["id"],
            "department_id": department["id"],
            "status": status,
        })
        self.destroy()

    def _center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) //2
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")