from Config.colors import STATUS_WARNING, STATUS_SUCCESS, STATUS_RETURNED, STATUS_ERROR

APP_NAME = "Equipment Reservation"

W_DASHBOARD_TITLE = "Dashboard"
W_BROWSE_EQUIP_TITLE = "Browse Equipment"
W_RESERVATION_TITLE = "Reservation"
W_NOTIFICATION_TITLE = "Notification"
W_PROFILE_TITLE = "Profile"

W_MANAGE_RESERVATION_TITLE = "Manage Reservation"
W_MANAGE_INVENTORY_TITLE = "Manage Inventory"
W_MANAGE_USERS_TITLE = "Manage Users"
W_REPORTS_TITLE = "Reports"

NAV_LABELS = {
    "dashboard_btn": ("Dashboard", "🏠"),
    "browse_equipment_btn": ("Browse\n Equipment", "🔍"),
    "reservation_btn": ("My Reservation", "📋"),
    "notification_btn": ("Notification", "🔔"),
    "profile_btn": ("Profile", "👤"),
    "logout_btn": ("Log out", "🚪"),
}

BAN_CHECK_MS = 500
POLL_INTERVAL_MS = 5000

DUE_SOON_DAYS = 1
RECENT_LIMIT = 5

PERIODS = {
    "Today": 0,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "All time": None,
}

STATUS_COLORS = {
    "Pending": STATUS_WARNING,
    "Approved": STATUS_SUCCESS,
    "Return Pending": STATUS_RETURNED,
}

LEGEND = [
    ("Pending", STATUS_WARNING),
    ("Borrowed", STATUS_SUCCESS),
    ("Return Pending", STATUS_RETURNED),
    ("Overdue", STATUS_ERROR),
]

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]