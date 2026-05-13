import frappe
from frappe import _
from frappe.query_builder import Criterion
from frappe.utils import nowdate
from frappe.utils import flt

def validate(doc, method):
    validate_pos(doc)
    set_cost_center_to_taxes(doc)

def on_cancel(doc, event):
    if not doc.custom_po_reference:
        return
    try:
        po = frappe.get_doc("Purchase Order", doc.custom_po_reference)

        if po.docstatus == 1:
            po.docstatus = 2
            po.save(ignore_permissions=True)

    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Purchase Order {doc.custom_po_reference} not found",
            "PO Cancel Failed"
        )

def on_trash(doc, event):
    if not doc.custom_po_reference:
        return
    try:
        po = frappe.get_doc("Purchase Order", doc.custom_po_reference)

        if po.docstatus == 1:
            po.cancel()
        
        frappe.delete_doc("Purchase Order", po.name, force=1)

    except frappe.DoesNotExistError:
        frappe.log_error(
            f"Purchase Order {doc.custom_po_reference} not found",
            "PO Deletion Failed"
        )

def validate_pos(doc):
    if not frappe.db.exists("POS Opening Shift", doc.posa_pos_opening_shift):
        frappe.throw(_("The specified POS Opening Shift does not exist."))
    
    pos = frappe.get_doc("POS Opening Shift", doc.posa_pos_opening_shift)

    if str(doc.posting_date) != str(pos.posting_date):
        frappe.throw(_("The posting date of the invoice must match the posting date of the POS Opening Shift."))
    
    if pos.status != "Open":
        frappe.throw(_("The specified POS Opening Shift is not open."))
        
    # ToDo: Cashiers cannot create new Invoices with Open POS Opening Shift
    # ToDo: Cashiers cannot save Invoices without POS Opening Shift
    pass

def set_cost_center_to_taxes(doc):
    for tax in doc.taxes:
        if doc.cost_center and doc.cost_center != tax.cost_center:
            tax.cost_center = doc.cost_center

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

    if doc.is_return:
        return
    if doc.custom_invoice_type not in [
        "Money Order",
        "Money Transfer",
        "Bill Payment",
        "Shipping & Delivery"
    ]:
        return

    if not doc.custom_supplier:
        frappe.throw(_("Supplier is required before submitting this invoice."))

    # Sum Service Charge items
    service_charge_total = 0

    for item in doc.items:
        if item.item_code == "Service Charge":
            service_charge_total += flt(item.amount)

    # Prevent duplicate PO creation
    if doc.custom_po_reference:
        return

    po = frappe.new_doc("Purchase Order")

    po.update({
        "supplier": doc.custom_supplier,
        "schedule_date": nowdate(),
        "cost_center": doc.cost_center,
    })

    po.append("items", {
        "item_code": "Service Charge",
        "schedule_date": nowdate(),
        "qty": 1,
        "rate": service_charge_total,
        "amount": service_charge_total,
    })

    po.set_missing_values()
    po.calculate_taxes_and_totals()

    po.insert(ignore_permissions=True)
    po.submit()

    doc.custom_po_reference = po.name