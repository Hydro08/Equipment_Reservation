import json
import os

SESSION_FILE = "session.json"

def save_session(user_id):
    data = json.dumps({"user_id": user_id})
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        f.write(data)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            return data.get("user_id")
    except (json.JSONDecodeError, KeyError):
        return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)