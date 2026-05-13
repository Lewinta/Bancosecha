import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def customer_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT
            ci.name,
            ci.customer_group,
            ci.custom_phone_number
        FROM 
            `tabCustomer` ci
        WHERE
            ci.name LIKE %(txt)s
            OR ci.custom_phone_number LIKE %(txt)s
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })
