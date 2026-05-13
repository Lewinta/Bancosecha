import frappe
def boot_session(bootinfo):
    settings = frappe.get_doc("Bancosecha Settings")
    defaults_map = {}
    for row in settings.transaction_defaults:
        if not row.invoice_type:
            continue
        defaults_map[row.invoice_type] = {
            "default_supplier": row.default_supplier,
            "default_item": row.default_item,
            "default_sales_tax_template": row.default_sales_tax_template,
        }
    
    bootinfo.bancosecha = {
        "defaults": defaults_map
    }
    set_user_defaults_from_pos_profile()    

def set_user_defaults_from_pos_profile(login_manager=None):
    user = frappe.session.user

    if not user or user == "Guest":
        return

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

    defaults_to_set = {
        "company": pos.company,
        "cost_center": pos.cost_center,
        "warehouse": pos.warehouse,
        "mode_of_payment": pos.posa_cash_mode_of_payment
    }

    for key, value in defaults_to_set.items():
        if not value:
            continue

        current = frappe.defaults.get_user_default(key, user)

        if current != value:
            frappe.defaults.set_user_default(key, value, user)