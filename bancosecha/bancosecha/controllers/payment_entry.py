import frappe

@frappe.whitelist()
def get_open_pos_shift(company, user, posting_date):
    if not company or not user or not posting_date:
        return None

    shift = frappe.db.get_value(
        "POS Opening Shift",
        {
            "company": company,
            "user": user,
            "posting_date": posting_date,
            "status": "Open",
            "docstatus": 1
        },
        "name"
    )

    return shift