import frappe

def validate(doc, method=None):
    sync_user_permissions_from_pos_profile(doc)

TARGET_DOCTYPES = [
    "Company",
    "Warehouse",
    "Cost Center"
]

def sync_user_permissions_from_pos_profile(doc):
    if not doc.applicable_for_users:
        return

    for row in doc.applicable_for_users:
        if not row.default or not row.user:
            continue

        user = row.user

        # 1. Remove old POS-generated permissions
        old_perms = frappe.get_all(
            "User Permission",
            filters={
                "user": user,
                "allow": ["in", TARGET_DOCTYPES],
                "is_default": 1,
            },
            pluck="name"
        )

        for perm in old_perms:
            frappe.delete_doc("User Permission", perm, ignore_permissions=True)

        # 2. Create fresh ones
        create_permission(user, "Company", doc.company)
        create_permission(user, "Warehouse", doc.warehouse)
        create_permission(user, "Cost Center", doc.cost_center)

    frappe.db.commit()


def create_permission(user, doctype, value):
    if not value:
        return

    # Avoid duplicates (extra safety)
    exists = frappe.db.exists(
        "User Permission",
        {
            "user": user,
            "allow": doctype,
            "for_value": value
        }
    )

    if exists:
        return

    perm = frappe.get_doc({
        "doctype": "User Permission",
        "user": user,
        "allow": doctype,
        "for_value": value,
        "is_default": 1,
        "apply_to_all_doctypes": 1,
    })

    perm.insert(ignore_permissions=True)