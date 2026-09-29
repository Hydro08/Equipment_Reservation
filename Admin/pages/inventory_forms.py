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
        entry.bind("<Control-BackSpace>", self.clear_entry)

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

    @staticmethod
    def clear_entry(event):
        entry = event.widget

        entry.delete(0, tk.END)

        return "break"

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
        entry.bind("<Control-BackSpace>", self.clear_entry)

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

    @staticmethod
    def clear_entry(event):
        entry = event.widget

        entry.delete(0, tk.END)

        return "break"

class EquipmentForm(tk.Toplevel):
    STATUSES = ["Available", "Unavailable"]
    CONDITIONS = ["Good", "Fair", "Damaged", "Under Repair"]

    width = 300
    height = 450

    def __init__(self, parent, department_name, category_name, department_id, category_id, on_save, item=None):
        super().__init__(parent, bg=BG)
        self.title("Edit Equipment" if item else "Add Equipment")
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.geometry("300x380+600+300")
        self.on_save = on_save
        self.category_id = category_id
        self.department_id = department_id

        self._center_window()

        item = item or {}

        tk.Label(self, text="Name", font=("Arial", 13), bg=BG, fg=FG).grid(row=0, column=0, padx=20, pady=(20, 6), sticky="w")
        self.name_var = tk.StringVar(value=item.get("name", ""))
        name_entry = tk.Entry(self, textvariable=self.name_var, width=28, font=("Arial", 12), bg=PANEL, fg=FG, insertbackground=FG, relief="flat")
        name_entry.grid(row=1, column=0, padx=20, pady=(0, 12), ipady=4)
        name_entry.bind("<Control-BackSpace>", self.clear_entry)

        tk.Label(self, text="Department", font=("Arial", 13), bg=BG, fg=FG).grid(row=4, column=0, padx=20, pady=(0, 6), sticky="w")
        tk.Label(self, text=department_name, font=("Arial", 13), bg=BG, fg=FG).grid(row=3, column=0, padx=20, pady=(0, 12), ipady=4)

        tk.Label(self, text="Category", font=("Arial", 13), bg=BG, fg=FG).grid(row=2, column=0, padx=20, pady=(0, 6), sticky="w")
        tk.Label(self, text=category_name, font=("Arial", 13), bg=BG, fg=FG).grid(row=5, column=0, padx=20, pady=(0, 12), ipady=4)

        tk.Label(self, text="Status", font=("Arial", 13), bg=BG, fg=FG).grid(row=6, column=0, padx=20, pady=(0, 6), sticky="w")
        self.status_var = tk.StringVar(value=item.get("status", "Available"))
        ttk.Combobox(self, textvariable=self.status_var, values=self.STATUSES, state="readonly", width=26).grid(row=7, column=0, padx=20, pady=(0, 12), ipady=3)

        tk.Label(self, text="Condition", font=("Arial", 13), bg=BG, fg=FG).grid(row=8, column=0, padx=20, pady=(0, 6), sticky="w")
        self.condition_var = tk.StringVar(value=item.get("condition", "Good"))
        ttk.Combobox(self, textvariable=self.condition_var, values=self.CONDITIONS, state="readonly", width=26).grid(row=9, column=0, padx=20, pady=(0, 12), ipady=3)

        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.grid(row=10, column=0, pady=(8, 20))
        tk.Button(btn_frame, text="Save", font=("Arial", 12, "bold"), bg="#4ADE80", fg="#0F172A", command=self._save, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", font=("Arial", 12), bg=PANEL, fg=FG, command=self.destroy, padx=16, pady=4, bd=0, cursor="hand2").pack(side="left", padx=6)
        self.grab_set()
        self.bind("<Return>", lambda e: self._save())

    def _save(self):
        name = self.name_var.get().strip()
        status = self.status_var.get()
        condition = self.condition_var.get()

        if not name:
            messagebox.showwarning("Missing Field", "Equipment name is required.", parent=self)
            return

        self.on_save({
            "name": name,
            "department_id": self.department_id,
            "category_id": self.category_id,
            "status": status,
            "condition": condition
        })
        self.destroy()

    def _center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) //2
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

    @staticmethod
    def clear_entry(event):
        entry = event.widget

        entry.delete(0, tk.END)

        return "break"