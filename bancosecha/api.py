import frappe

def set_user_defaults_from_pos_profile(login_manager=None):
    user = frappe.session.user

    if not user or user == "Guest":
        return

    # Get default POS Profile for this user
    pos_profile = frappe.db.get_value(
        "POS Profile User",
        {
            "user": user,
            "default": 1
        },
        "parent"
    )

    if not pos_profile:
        return

    pos = frappe.get_cached_doc("POS Profile", pos_profile)

    # Optional: avoid overriding if already set
    def set_default(key, value):
        if value and not frappe.defaults.get_user_default(key, user):
            frappe.defaults.set_user_default(key, value, user)

    # Set defaults
    set_default("Company", pos.company)
    set_default("Cost Center", pos.cost_center)
    set_default("Warehouse", pos.warehouse)

    # Mode of Payment (POSA field)
    set_default("Mode of Payment", pos.posa_cash_mode_of_payment)

    frappe.db.commit()