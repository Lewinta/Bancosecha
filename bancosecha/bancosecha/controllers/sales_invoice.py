import frappe
from frappe import _
from frappe.query_builder import Criterion
from frappe.utils import nowdate
from frappe.utils import flt

def validate(doc, method):
    validate_pos(doc)

def validate_pos(doc):
    # ToDo: Cashiers cannot create new Invoices with Open POS Opening Shift
    # ToDo: Cashiers cannot save Invoices without POS Opening Shift
    pass

@frappe.whitelist()
def get_open_pos_shift(company, pos_profile, posting_date):
    """Returns the open POS Opening Shift for the given cashier, if any."""
    OS = frappe.qb.DocType("POS Opening Shift")
    conditions = [
        OS.company == company,
        OS.pos_profile == pos_profile,
        OS.posting_date == posting_date,
        OS.user == frappe.session.user,
        OS.docstatus == 1,
        OS.status == "Open",
    ]
    open_shift = frappe.qb.from_(OS).select(
        OS.name
    ).where(
        Criterion.all(conditions)
    ).limit(1).run(as_dict=True)

    if open_shift:
        return open_shift[0].name

@frappe.whitelist()
def create_po_and_submit_invoice(invoice_name: str, supplier: str, cost_center: str, item_code: str, amount: float):
    amount = flt(amount)

    if amount <= 0:
        frappe.throw(_("Amount must be greater than zero."))

    try:
        inv = frappe.get_doc("Sales Invoice", invoice_name)

        if inv.docstatus != 0:
            frappe.throw(_("Sales Invoice must be Draft to submit."))

        if inv.get("custom_po_reference"):
            return {"po_name": inv.custom_po_reference, "invoice_name": inv.name, "already_done": 1}

        if amount >= float(inv.total or 0):
            frappe.throw(_("Amount must be less than the invoice total."))

        po = frappe.new_doc("Purchase Order")
        po.update({
            "supplier": supplier,
            "schedule_date": nowdate(),
            "cost_center": cost_center,
            "docstatus": 1,
        })
        po.append("items", {
            "item_code": item_code,
            "schedule_date": nowdate(),
            "qty": 1,
            "rate": amount,
            "amount": amount,
        })

        po.set_missing_values()
        po.calculate_taxes_and_totals()
        po.save(ignore_permissions=True)

        inv.db_set("custom_po_reference", po.name, update_modified=True)

        inv.submit()

        frappe.db.commit()

        return {"po_name": po.name, "invoice_name": inv.name, "submitted": 1}

    except Exception as e:
        frappe.db.rollback()
        inv_json = inv.as_json() if "inv" in locals() else "(invoice not loaded)"
        msg = e.message if hasattr(e, "message") else str(e)
        msg += f"Payload: \n{inv_json}\n"
        msg += f"\nTraceback:\n{frappe.get_traceback()}"
        frappe.log_error("Error in create_po_and_submit_invoice", msg)   
        raise

def before_submit(doc, event):
    if doc.custom_invoice_type in [
        "Money Order",
        "Money Transfer",
        "Bill Payment",
        "Shipping & Delivery"
    ] and not doc.custom_po_reference:
        frappe.throw(_("Purchase Order reference is required before submitting this invoice."))