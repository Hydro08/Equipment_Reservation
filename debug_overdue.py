from Authentication.auth_service import get_overdue_candidates, get_user_by_id
from Authentication.overdue_service import evaluate_overdue, run_overdue_check

for r in get_overdue_candidates():
    user = get_user_by_id(r["user_id"])
    print(
        "res", r["id"],
        "| user:", user["username"],
        "| banned:", user.get("is_banned"),
        "| result:", evaluate_overdue(r),
    )

print("--- running check ---")
run_overdue_check()
print("Done")