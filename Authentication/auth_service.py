import bcrypt

from tkinter import messagebox
from typing import Any
from Database.supabase_client import supabase
from postgrest import CountMethod
from datetime import date, timedelta, timezone, datetime

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

def get_admin_dashboard_summary():
    try:
        total_equipment_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact)
        total_equipment = total_equipment_query.execute()
        total_user_query: Any = supabase.table("users").select("id", count=CountMethod.exact).eq("role", "user")
        total_users = total_user_query.execute()
        pending_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("status", "Pending")
        pending = pending_query.execute()
        borrowed_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("status", "Approved")
        borrowed = borrowed_query.execute()
        available_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact).eq("status", "Available")
        available = available_query.execute()

        return {
            "total_equipment": total_equipment.count or 0,
            "total_users": total_users.count or 0,
            "pending": pending.count or 0,
            "borrowed": borrowed.count or 0,
            "available": available.count or 0
        }
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching admin dashboard summary: {e}")
        return {
            "total_equipment": 0,
            "total_users": 0,
            "pending": 0,
            "borrowed": 0,
            "available": 0
        }

def get_dashboard_summary(user_id):
    try:
        total_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact)
        total = total_query.execute()
        available_query: Any = supabase.table("equipment").select("id", count=CountMethod.exact).eq("status", "Available")
        available = available_query.execute()
        pending_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("user_id", user_id).eq("status", "Pending")
        pending = pending_query.execute()
        borrowed_query: Any = supabase.table("reservation").select("id", count=CountMethod.exact).eq("user_id", user_id).eq("status", "Approved")
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
        response = supabase.table("departments").select("*").execute()
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

def get_categories_by_department(department_id):
    try:
        query: Any = supabase.table("categories").select("*").eq("department_id", department_id)
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching categories: {e}")
        return []

def create_reservation(user_id, equipment_id, reserved_date, return_date):
    try:
        equipment_check: Any = supabase.table("equipment").select("status, condition").eq("id", equipment_id)
        equipment = equipment_check.execute()

        if not equipment.data:
            return "unavailable"

        item = equipment.data[0]
        if item["status"] != "Available":
            return "unavailable"
        if item.get("condition") in ("Damaged", "Under Repair"):
            return "damaged"

        duplicate_query: Any = supabase.table("reservation").select("id").eq("user_id", user_id).eq("equipment_id", equipment_id).eq("status", "Pending")
        duplicate = duplicate_query.execute()

        if duplicate.data:
            return "duplicate"

        insert_query: Any = supabase.table("reservation").insert({
            "user_id": user_id,
            "equipment_id": equipment_id,
            "reserved_date": str(reserved_date),
            "return_date": str(return_date),
            "status": "Pending",
        })
        response = insert_query.execute()

        return "success" if response.data else "failed"
    except Exception as e:
        messagebox.showerror("Database Error", f"Error creating reservation: {e}")
        return False

def get_pending_reservation():
    try:
        # noinspection PyUnresolvedReferences
        response_query: Any = supabase.table("reservation").select("*, users(username), equipment(name)").eq("status", "Pending").order("id", desc=False)
        response = response_query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error Fetching pending reservation: {e}")
        return []

def update_reservation_status(reservation_id, new_status):
    try:
        now_iso = datetime.now(timezone.utc).isoformat()

        response_query: Any = supabase.table("reservation").update({
            "status": new_status,
            "status_updated_at": now_iso,
        }).eq("id", reservation_id)
        response = response_query.execute()

        if not response.data:
            return False

        equipment_id = response.data[0]["equipment_id"]

        if new_status == "Approved":
            eq_update: Any = supabase.table("equipment").update({"status": "Unavailable"}).eq("id", equipment_id)
            eq_response = eq_update.execute()

            if not eq_response.data:
                messagebox.showerror("Database Error", "Reservation was approved, but equipment status was not updated.")

            others_query: Any = supabase.table("reservation").select("id").eq("equipment_id", equipment_id).eq("status", "Pending").neq("id", reservation_id)
            others = others_query.execute()

            if others.data:
                other_ids = [row["id"] for row in others.data]
                update_query: Any = supabase.table("reservation").update({
                    "status": "Rejected",
                    "status_updated_at": now_iso,
                }).in_("id", other_ids)
                update_query.execute()
        elif new_status == "Rejected":
            approved_check: Any = supabase.table("reservation").select("id").eq("equipment_id", equipment_id).eq("status", "Approved")
            approved = approved_check.execute()

            if not approved.data:
                available_check: Any = supabase.table("equipment").update({"status": "Available"}).eq("id", equipment_id)
                available_check.execute()

        return True
    except Exception as e:
        messagebox.showerror("Database Error", f"Error updating reservation status: {e}")
        return False

def get_user_reservations(user_id):
    try:
        query: Any = supabase.table("reservation").select("*, equipment(name, categories(name), departments(name))").eq("user_id", user_id).in_("status", ["Pending", "Approved", "Return Pending"])
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching your reservations: {e}")
        return []

def cancel_reservation(reservation_id):
    try:
        query: Any = supabase.table("reservation").update({"status": "Cancelled"}).eq("id", reservation_id).eq("status", "Pending")
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Failed", f"Error Cancelling reservation: {e}")
        return False

def request_return(reservation_id):
    try:
        query: Any = supabase.table("reservation").update(
            {"status": "Return Pending"}
        ).eq("id", reservation_id).eq("status", "Approved")
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error requesting return: {e}")
        return False

def get_pending_returns():
    try:
        query: Any = supabase.table("reservation").select(
            "*, users(username), equipment(name)"
        ).eq("status", "Return Pending")
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching pending returns: {e}")
        return []

def confirm_return(reservation_id):
    try:
        query: Any = supabase.table("reservation").update(
            {"status": "Returned"}
        ).eq("id", reservation_id).eq("status", "Return Pending")
        response = query.execute()

        if not response.data:
            return False

        equipment_id = response.data[0]["equipment_id"]
        eq_query: Any = supabase.table("equipment").update(
            {"status": "Available"}
        ).eq("id", equipment_id)
        eq_query.execute()

        return True
    except Exception as e:
        messagebox.showerror("Database Error", f"Error confirming return: {e}")
        return False

def reject_return(reservation_id):
    try:
        query: Any = supabase.table("reservation").update(
            {"status": "Approved"}
        ).eq("id", reservation_id).eq("status", "Return Pending")
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error rejecting return: {e}")
        return False

def get_available_equipment():
    try:
        query: Any = supabase.table("equipment").select("*, categories(name), departments(name)").eq("status", "Available")
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching available equipment: {e}")
        return []

def get_borrowed_reservations():
    try:
        # noinspection PyUnresolvedReferences
        query: Any = supabase.table("reservation").select("*, users(username), equipment(name)").eq("status", "Approved").order("id", desc=False)
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching borrowed reservations: {e}")
        return []

def get_user_notification(user_id):
    try:
        query: Any = supabase.table("reservation").select("*, equipment(name)").eq("user_id", user_id).in_("status", ["Approved", "Rejected"]).eq("notification_seen", False)
        response = query.execute()
        return response.data or []
    except Exception as e:
        messagebox.showerror("Database Error", f"Error fetching notifications: {e}")
        return []

def dismiss_notification(reservation_id):
    try:
        query: Any = supabase.table("reservation").update({"notification_seen": True}).eq("id", reservation_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error dismissing notification: {e}")
        return False

def add_department(name):
    try:
        check: Any = supabase.table("departments").select("id").ilike("name", name)
        existing = check.execute()
        if existing.data:
            messagebox.showwarning("Duplicate", f"Department '{name}' already exists.")
            return False

        query: Any = supabase.table("departments").insert({"name": name})
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error adding departments: {e}")
        return False

def update_department(department_id, new_name):
    try:
        query: Any = supabase.table("departments").update({"name": new_name}).eq("id", department_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error updating departments: {e}")
        return False

def delete_department(department_id):
    try:
        query: Any = supabase.table("departments").delete().eq("id", department_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error deleting departments: {e}")
        return False

def add_category(name, department_id):
    try:
        check: Any = supabase.table("categories").select("id").eq("department_id", department_id).ilike("name", name)
        existing = check.execute()
        if existing.data:
            messagebox.showwarning("Duplicate", f"Category '{name}' already exists.")
            return False

        query: Any = supabase.table("categories").insert({"name": name, "department_id": department_id})
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error adding category: {e}")
        return False

def update_category(category_id, new_name):
    try:
        query: Any = supabase.table("categories").update({"name": new_name}).eq("id", category_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error updating category: {e}")
        return False

def delete_category(category_id):
    try:
        query: Any = supabase.table("categories").delete().eq("id", category_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error deleting category: {e}")
        return False

def add_equipment(name, category_id, department_id, status="Available", condition="Good"):
    try:
        query: Any = supabase.table("equipment").insert({
            "name": name,
            "category_id": category_id,
            "department_id": department_id,
            "status": status,
            "condition": condition
        })
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error adding equipment: {e}")
        return False

def update_equipment(equipment_id, data):
    try:
        query: Any = supabase.table("equipment").update(data).eq("id", equipment_id)
        response = query.execute()

        if not response.data:
            return False

        if data.get("condition") in ("Damaged", "Under Repair"):
            reject_query: Any = supabase.table("reservation").update({
                "status": "Rejected",
                "status_updated_at": datetime.now(timezone.utc).isoformat(),
                "notification_seen": False,
            }).eq("equipment_id", equipment_id).eq("status", "Pending")
            reject_query.execute()

        return True
    except Exception as e:
        messagebox.showerror("Database Error", f"Error updating equipment: {e}")
        return False

def equipment_has_active_reservation(equipment_id):
    try:
        query: Any = supabase.table("reservation").select("id").eq("equipment_id", equipment_id).in_("status", ["Pending", "Approved"])
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error checking reservations: {e}")
        return True

def delete_equipment(equipment_id):
    try:
        query: Any = supabase.table("equipment").delete().eq("id", equipment_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error deleting equipment: {e}")
        return False

def verify_current_password(user_id, plain_password):
    user = get_user_by_id(user_id)
    if not user:
        return False
    stored_hash = user["password_hash"].encode("utf-8")
    return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash)

def rehash_user_password_by_id(user_id, plain_password):
    try:
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        hashed_str = hashed.decode("utf-8")

        query: Any = supabase.table("users").update({"password_hash": hashed_str}).eq("id", user_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error updating password: {e}")
        return False

def can_change_username(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return False, None
    last_changed = user.get("username_changed_at")
    if not last_changed:
        return True, None

    last_changed_dt = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
    next_allowed = last_changed_dt + timedelta(days=1)
    now = datetime.now(timezone.utc)

    if now >= next_allowed:
        return True, None
    return False, next_allowed

def change_username(user_id, new_username):
    try:
        check: Any = supabase.table("users").select("id").ilike("username", new_username)
        existing = check.execute()
        if existing.data:
            messagebox.showwarning("Duplicate", f"Username '{new_username}' is already taken.")
            return False

        query: Any = supabase.table("users").update({
            "username": new_username,
            "username_changed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", user_id)
        response = query.execute()
        return bool(response.data)
    except Exception as e:
        messagebox.showerror("Database Error", f"Error changing username: {e}")
        return False

