import frappe
def boot_session(bootinfo):
    settings = frappe.get_doc("Bancosecha Settings")
    defaults_map = {}
    for row in settings.transaction_defaults:
        if not row.invoice_type:
            continue
        defaults_map[row.invoice_type] = {
            "default_supplier": row.default_supplier,
            "default_item": row.default_item
        }
    
    bootinfo.bancosecha = {
        "defaults": defaults_map
    }
    