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
    