from Config.colors import STATUS_WARNING, STATUS_SUCCESS, STATUS_RETURNED, STATUS_ERROR

SCHOOL_NAME = "Hyd University"
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

ADMIN_NAV_LABELS = {
    "dashboard_btn": ("Dashboard", "🏠"),
    "manage_reservation_btn": ("Manage\n Reservation", "📋"),
    "manage_inventory_btn": ("Manage\n Inventory", "📦"),
    "manage_users_btn": ("Manage Users", "👥"),
    "reports_btn": ("Reports", "📊"),
    "logout_btn": ("Log out", "🚪"),
}

USERNAME_PATTERN = r"[A-Za-z][A-Za-z0-9_]{2,19}"
USERNAME_RULES = (
    "Username must start with a letter, be 3 to 20 characters long, "
    "and contain only letters, numbers, or underscores."
)

MAX_WARNINGS = 5
WARNING_ALERT_AT = 4
LONG_OVERDUE_DAYS = 7
OVERDUE_REMINDER_HOURS = 24
OVERDUE_CHECK_MS = 64000

BAN_CHECK_MS = 500
POLL_INTERVAL_MS = 5000

OVERDUE_BANNER_MESSAGE = (
    "You have overdue items. Please return them before making a new reservation."
)

BAN_MESSAGE_AUTO = (
    f"Your account is restricted due to repeated overdue returns. "
    f"Please return your borrowed equipment, then go to your department at {SCHOOL_NAME} "
    f"and submit a letter to request reinstatement."
)

BAN_MESSAGE_MANUAL = (
    f"Your account has been restricted by the administrator. "
    f"Please return any borrowed equipment and go to your department at {SCHOOL_NAME} "
    f"to ask about the reason and request reinstatement."
)

def get_ban_message(reason):
    return BAN_MESSAGE_AUTO if reason == "auto" else BAN_MESSAGE_MANUAL

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