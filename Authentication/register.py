import tkinter as tk

from tkinter import messagebox

from Authentication.login import LoginWindow
from Authentication.auth_service import sign_up_user

class RegisterWindow:

    app_name = "Equipment Reservation"
    window_width = 850
    window_height = 680

    primary_bg = "#0F172A"
    primary_fg = "#FFFFFF"

    def __init__(self):
        self.register_window = tk.Tk()
        self.register_window.title(f"{self.app_name} - Register")
        self.register_window.config(bg=self.primary_bg)

        self.colors = self.fg_bg()

        self._center_window()
        self._build_ui()

        self.register_window.mainloop()

    def fg_bg(self):
        return {"bg": self.primary_bg, "fg": self.primary_fg}

    def _center_window(self):
        screen_width = self.register_window.winfo_screenwidth()
        screen_height = self.register_window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.register_window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _build_ui(self):
        self.register_text = tk.Label(self.register_window, text=f"{self.app_name}", font=("Arial", 24), **self.colors)
        self.register_text.pack(pady=(20, 0))

        self.create_label = tk.Label(self.register_window, text="Create an account", font=("Arial", 18), **self.colors)
        self.create_label.pack(pady=(20, 0))

        self._username_frame()
        self._password_frame()
        self._confirm_password_frame()

        self._build_login_link()

        self.register_button = tk.Button(self.register_window, text="Register", font=("Arial", 18), width=10, cursor="hand2", **self.colors)
        self.register_button.pack(pady=(20, 0))
        self.register_button.bind("<Button-1>", lambda event: self.register())

    def _username_frame(self):
        self.username_panel = tk.Frame(self.register_window, bg=self.primary_bg)
        self.username_panel.pack(pady=(20,0))

        self.username_label = tk.Label(self.username_panel, text="Username", font=("Arial", 18), **self.colors)
        self.username_label.pack(pady=(30, 0))
        self.username_entry = tk.Entry(self.username_panel, font=("Arial", 18), width=35, **self.colors)
        self.username_entry.pack(pady=(10, 0))

    def _password_frame(self):
        self.password_panel = tk.Frame(self.register_window, bg=self.primary_bg)
        self.password_panel.pack(pady=(20, 0))

        self.password_label = tk.Label(self.password_panel, text="Password", font=("Arial", 18), **self.colors)
        self.password_label.pack(pady=(10, 0))
        self.password_entry = tk.Entry(self.password_panel, font=("Arial", 18), width=35, **self.colors, show="•")
        self.password_entry.pack(pady=(10,0))
        self.show_pass = tk.BooleanVar(value=False)
        self.show_pass_checkbox = tk.show_pass_checkbox = (
            tk.Checkbutton(self.password_panel, text="Show Password", font=("Arial", 14), **self.colors, selectcolor="#0F172A", cursor="hand2", variable= self.show_pass, command = lambda: self.toggle_password(self.password_entry, self.show_pass))
        )
        self.show_pass_checkbox.pack(pady=(10, 0), side="left")

    def _confirm_password_frame(self):
        self.confirm_password_panel = tk.Frame(self.register_window, bg=self.primary_bg)
        self.confirm_password_panel.pack(pady=(20, 0))

        self.confirm_password_label = tk.Label(self.confirm_password_panel, text="Confirm Password", font=("Arial", 18), **self.colors)
        self.confirm_password_label.pack(pady=(10, 0))
        self.confirm_password_entry = tk.Entry(self.confirm_password_panel,font=("Arial", 18), width=35, **self.colors, show="•")
        self.confirm_password_entry.pack(pady=(10, 0))
        self.show_confirm_pass = tk.BooleanVar(value=False)
        self.show_confirm_pass_checkbox = tk.show_confirm_pass_checkbox = (
            tk.Checkbutton(self.confirm_password_panel, text="Show Password", font=("Arial", 14), **self.colors, selectcolor="#0F172A", activeforeground="white", cursor="hand2", variable=self.show_confirm_pass, command = lambda: self.toggle_password(self.confirm_password_entry, self.show_confirm_pass))
        )
        self.show_confirm_pass_checkbox.pack(pady=(10, 0), side="left")

    @staticmethod
    def toggle_password(entry_widget, var):
        show = "" if var.get() else "•"
        entry_widget.config(show=show)

    def _build_login_link(self):
        self.login_link = tk.Label(self.register_window, text="Already have an account?", font=("Arial", 15, "underline"), cursor="hand2", **self.colors)
        self.login_link.pack(pady=(20, 0))
        self.login_link.bind("<Button-1>", lambda event: self.open_login())
        self.login_link.bind("<Enter>", lambda event: self.change_link_color(True))
        self.login_link.bind("<Leave>", lambda event: self.change_link_color(False))

    def open_login(self):
        self.register_window.destroy()
        LoginWindow()

    def change_link_color(self, is_hover):
        if is_hover:
            self.login_link.config(fg="blue")
        else:
            self.login_link.config(fg="white")

    def register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_password_entry.get().strip()

        if not username or not password or not confirm:
            messagebox.showinfo("Register Failed", "Please fill in all fields.")
            return

        if password != confirm:
            messagebox.showinfo("Register Failed", "Password do not match.")
            return

        self.register_button.config(text="Registering...", state="disabled", width=15)
        self.register_window.update()

        result = None
        try:
            result = sign_up_user(username, password)
        except ValueError as e:
            messagebox.showinfo("Register Failed", f"Error: {e}")
        finally:
            self.register_button.config(text="Register", state="normal",width=10)

        if result:
            messagebox.showinfo("Registration Successfully", f"Account '{username}' created!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            self.show_pass.set(False)
            self.show_confirm_pass.set(False)
            self.open_login()