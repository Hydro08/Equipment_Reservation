from datetime import date, datetime, timedelta, timezone

from Authentication.auth_service import get_overdue_candidates, update_reservation_flags, add_user_warnings, create_notification, get_user_by_id, set_user_banned, get_users_over_warning_limit
from Config.settings import MAX_WARNINGS, WARNING_ALERT_AT, LONG_OVERDUE_DAYS, OVERDUE_REMINDER_HOURS, BAN_MESSAGE_AUTO

def _parse_ts(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate_overdue(reservation, now=None):
    now = now or datetime.now(timezone.utc)
    due = date.fromisoformat(str(reservation["return_date"])[:10])
    days_late = (date.today() - due).days

    result = {"add_warnings": 0, "send_reminder": False, "flags": {}}
    if days_late <= 0:
        return result

    if not reservation.get("overdue_warned"):
        result["add_warnings"] += 1
        result["flags"]["overdue_warned"] = True

    if days_late >= LONG_OVERDUE_DAYS and not reservation.get("long_overdue_warned"):
        result["add_warnings"] += 1
        result["flags"]["long_overdue_warned"] = True

    last = _parse_ts(reservation.get("last_reminder_at"))
    if last is None or now - last >= timedelta(hours=OVERDUE_REMINDER_HOURS):
        result["send_reminder"] = True
        result["flags"]["last_reminder_at"] = now.isoformat()

    return result

def warning_outcome(new_count):
    if new_count >= MAX_WARNINGS:
        return "ban"
    if new_count >= WARNING_ALERT_AT:
        return "final_alert"
    return "warn"

def run_overdue_check():
    for res in get_overdue_candidates():
        user_id = res["user_id"]

        user = get_user_by_id(user_id)
        if not user or user.get("is_banned"):
            continue

        result = evaluate_overdue(res)
        if not result["add_warnings"] and not result["send_reminder"]:
            continue

        item = (res.get("equipment") or {}).get("name", "an item")
        update_reservation_flags(res["id"], result["flags"])

        if result["add_warnings"]:
            count = add_user_warnings(user_id, result["add_warnings"])
            if count is None:
                continue

            outcome = warning_outcome(count)
            if outcome == "ban":
                set_user_banned(user_id, True)
                create_notification(user_id, BAN_MESSAGE_AUTO, "ban")
            elif outcome == "final_alert":
                create_notification(
                    user_id,
                    f"'{item}' is overdue. Warning {count}/{MAX_WARNINGS}. "
                    f"One more warning and your account will be banned.",
                    "warning",
                )
            else:
                create_notification(
                    user_id,
                    f"'{item}' is overdue. You received a warning ({count}/{MAX_WARNINGS}). "
                    f"Please return it as soon as possible.",
                    "warning",
                )
        elif result["send_reminder"]:
            create_notification(
                user_id,
                f"Reminder: '{item}' is overdue. Please return it as soon as possible.",
                "reminder",
            )
    for u in get_users_over_warning_limit(MAX_WARNINGS):
        set_user_banned(u["id"], True)
        create_notification(u["id"], BAN_MESSAGE_AUTO, "ban")