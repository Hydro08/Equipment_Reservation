import bcrypt

from tkinter import messagebox
from typing import Any
from Database.supabase_client import supabase
from postgrest import CountMethod
from datetime import date, timedelta

def login_user(identifier: str, plain_password: str):
    query: Any = supabase.table("users").select("*")
    query = query.or_(f"username.ilike.{identifier}")
    response = query.execute()

    if not response.data:
        messagebox.showinfo("Error", "User not found.")
        return None

    user = response.data[0]
    stored_hash = user["password_hash"].encode("utf-8")

    if bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash):
        return user
    else:
        messagebox.showinfo("Error", "Incorrect Password.")
        return None

def get_user_by_id(user_id):
    query: Any = supabase.table("users").select("*")
    response = query.eq("id", user_id).execute()

    if not response.data:
        return None
    return response.data[0]

def sign_up_user(username: str, plain_password: str):
    query: Any = supabase.table("users").select("id")
    query = query.or_(f"username.eq.{username}")
    existing = query.execute()

    if existing.data:
        messagebox.showinfo("Username already taken.")
        return None

    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    hashed_str = hashed.decode("utf-8")

    insert_query: Any = supabase.table("users").insert({
        "username": username,
        "password_hash": hashed_str
    })
    response = insert_query.execute()

    if response.data:
        messagebox.showinfo("Successfully Registered", "Sign up successfully!")
        return response.data
    else:
        messagebox.showinfo("Error", "Sign up failed!")
        return None

def rehash_user_password(username: str, plain_password: str):
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    hashed_str = hashed.decode("utf-8")

    table: Any = supabase.table("users")
    response = table.update({"password_hash": hashed_str}).eq("username", username).execute()

    if not response.data:
        messagebox.showinfo("Error", f"No user found: {username}.")
    else:
        messagebox.showinfo("Success", "Password updated successfully!")
        return response.data

def get_dashboard_summary(user_id):
    try:
        total_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact)
        total = total_query.execute()
        available_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact).eq("status", "Available")
        available = available_query.execute()
        pending_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("user_id", user_id).eq("status", "Pending")
        pending = pending_query.execute()
        borrowed_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("status", "Approved")
        borrowed = borrowed_query.execute()

        warning_days = 1
        due_soon_date = date.today() + timedelta(days=warning_days)

        due_soon_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact)
        due_soon = due_soon_query.eq("user_id", user_id).eq("status", "Approved").lte("return_date", str(due_soon_date)).execute()


        return {
            "available": available.count or 0,
            "pending": pending.count or 0,
            "borrowed": borrowed.count or 0,
            "total": total.count or 0,
            "due_soon": due_soon.count or 0,
        }

    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching dashboard summary: {e}")
        return {
            "available": 0,
            "pending": 0,
            "borrowed": 0,
            "total": 0,
            "due_soon": 0
        }

def get_all_departments():
    try:
        response = supabase.table("departments").select("*)").execute()
        return response.data or []

    except Exception as e:
        messagebox.showinfo("Database Error", f"Error Fetching department: {e}")
        return []

def get_all_categories():
    try:
        response = supabase.table("categories").select("*").execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error Fetching categories: {e}")
        return []

def get_all_equipment():
    try:
        response = supabase.table("equipment").select("*, categories(name), departments(name)").execute()
        return response.data or []

    except Exception as e:
        messagebox.showerror("Database Error", f"Error Fetching equipment: {e}")
        return []