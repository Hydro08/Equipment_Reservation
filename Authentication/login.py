import tkinter as tk
import httpx

from tkinter import messagebox

from Admin.dashboard import AdminDashboard
from User.dashboard import UserDashboard

from Authentication.auth_service import login_user, get_user_by_id
from Database.session_manager import save_session, load_session

class LoginWindow:
    app_name = "Equipment Reservation"
    window_width = 850
    window_height = 600
    primary_bg = "#0F172A"
    primary_fg = "#FFFFFF"
    hover_bg = "dark gray"

    def __init__(self):
        self.login_window = tk.Tk()
        self.login_window.title(f"{self.app_name} - Login")
        self.login_window.config(bg="#0F172A")
        self.login_window.resizable(False, False)

        saved_user_id = load_session()
        if saved_user_id:
            user = get_user_by_id(saved_user_id)
            if user:
                self.login_window.destroy()

                if user["role"] == "admin":
                    AdminDashboard(user)
                else:
                    UserDashboard(user)
                return

        self.colors = self.fg_bg()
        self._center_window()
        self._build_ui()

        self.login_window.mainloop()

    def fg_bg(self):
        return {"bg": self.primary_bg, "fg": self.primary_fg}

    def _build_ui(self):
        self.login_text = tk.Label(self.login_window, text=f"{self.app_name}", font=("Arial", 24), **self.colors)
        self.login_text.pack(pady=(20, 0))
        self.welcome_label = tk.Label(self.login_window, text="Welcome back!", font=("Arial", 18), **self.colors)
        self.welcome_label.pack(pady=(20, 0))

        self._username_frame()
        self._password_frame()

        self._build_remember_me()

        self._build_register_link()

        self.login_button = tk.Button(self.login_window, text="Login", font=("Arial", 16), width=7, cursor="hand2",
                                      **self.colors)
        self.login_button.pack(pady=(20, 0))
        self.login_button.bind("<Button-1>", lambda e: self.login())

        self.login_window.bind("<Return>", lambda event: self.login())

    def _build_remember_me(self):
        self.remember_me_var = tk.BooleanVar(value=False)
        self.remember_me_checkbox = tk.Checkbutton(
            self.login_window, text="Remember Me", font=("Arial", 12), variable=self.remember_me_var, selectcolor="#0F172A", bg=self.primary_bg, fg=self.primary_fg, cursor="hand2"
        )
        self.remember_me_checkbox.pack(pady=(20, 0))

    def _center_window(self):
        screen_width = self.login_window.winfo_screenwidth()
        screen_height = self.login_window.winfo_screenheight()
        x = (screen_width - self.window_width) // 2
        y = (screen_height - self.window_height) // 2
        self.login_window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")

    def _username_frame(self):
        self.username_panel = tk.Frame(self.login_window, bg=self.primary_bg)
        self.username_panel.pack(pady=(0, 10))

        self.username_text = tk.Label(self.username_panel, text="Username", font=("Arial", 24), **self.colors)
        self.username_text.pack(pady=(20, 0))

        self.username_entry = tk.Entry(self.username_panel, font=("Arial", 20), width=35, borderwidth=3, **self.colors)
        self.username_entry.pack(pady=(20, 0), side="left")
        self.username_entry.bind("<Control-BackSpace>", lambda event: self.clear_entry(event))

    def _password_frame(self):
        self.password_panel = tk.Frame(self.login_window, bg=self.primary_bg)
        self.password_panel.pack(pady=(20, 0))

        self.password_text = tk.Label(self.password_panel, text="Password", font=("Arial", 24), **self.colors)
        self.password_text.pack(pady=(20, 0))
        self.password_entry = tk.Entry(self.password_panel, font=("Arial", 20), show="•", width=35, borderwidth=3,
                                       **self.colors)
        self.password_entry.pack(padx=(0, 10))
        self.password_entry.bind("<Control-BackSpace>", lambda event: self.clear_entry(event))

        self.show_pass = tk.BooleanVar(value=False)
        self.show_pass_checkbox = tk.show_pass_checkbox = (
            tk.Checkbutton(self.password_panel, text="Show Password", font=("Arial", 14), **self.colors,
                           selectcolor="#0F172A", activeforeground="white", cursor="hand2", variable=self.show_pass,
                           command=lambda: self._toggle_password())
        )
        self.show_pass_checkbox.pack(pady=(20, 0), side="left")

    def _toggle_password(self):
        is_hidden = self.password_entry.cget("show") == "•"
        self.password_entry.config(show="" if is_hidden else "•")

    @staticmethod
    def clear_entry(event):
        entry = event.widget

        entry.delete(0, tk.END)

        return "break"

    def _build_register_link(self):
        self.register_link = tk.Label(self.login_window, text="You dont have an account?", font=("Arial", 15, "underline"), cursor="hand2", **self.colors)
        self.register_link.bind("<Button-1>", lambda event: self.open_register())
        self.register_link.pack(pady=(20, 0))
        self.register_link.bind("<Enter>", lambda e: self.change_link_color(True))
        self.register_link.bind("<Leave>", lambda e: self.change_link_color(False))

    def open_register(self):
        from Authentication.register import RegisterWindow
        self.login_window.destroy()
        RegisterWindow()

    def change_link_color(self, is_hover):
        if is_hover:
            self.register_link.config(fg="blue")
        else:
            self.register_link.config(fg="white")

    def login(self):
        identifier = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not identifier or not password:
            messagebox.showinfo("Error", "Please fill in all fields.")
            return

        self.login_button.config(text="Logging in...", state="disabled", width=15)
        self.login_window.update()

        try:
            user = login_user(identifier, password)
        except httpx.ConnectError:
            messagebox.showerror(
                "Connection Error",
                "Double Check your wi-fi connection."
            )
            return
        except Exception as e:
            messagebox.showerror("Unexpected Error", f"Error: {e}")
            return
        finally:
            self.login_button.config(text="Login", state="normal", width=10)

        if user is None:
            return

        if self.remember_me_var.get():
            save_session(user["id"])

        self.login_window.destroy()

        if user["role"] == "admin":
            from Admin.dashboard import AdminDashboard
            AdminDashboard(user)
        else:
            from User.dashboard import UserDashboard
            UserDashboard(user)