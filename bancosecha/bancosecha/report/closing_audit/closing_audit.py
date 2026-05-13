# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

from bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift import (
    build_expected_amount_ledger
)


def execute(filters=None):
    if not filters or not filters.get("pos_closing_shift"):
        frappe.throw("POS Closing Shift is required")

    closing = frappe.get_doc("POS Closing Shift", filters["pos_closing_shift"])

    # ---------------------------------------
    # Ledger base (SOURCE OF TRUTH)
    # ---------------------------------------
    ledger = build_expected_amount_ledger(closing.pos_opening_shift)

    # ---------------------------------------
    # Columns
    # ---------------------------------------
    columns = [
        {
            "label": "Type",
            "fieldname": "type",
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "label": "Reference",
            "fieldname": "reference",
            "fieldtype": "Dynamic Link",
            "options": "reference_doctype",
            "width": 180,
        },
        {
            "label": "Posting Date",
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 110,
        },
        {
            "label": "Mode of Payment",
            "fieldname": "mode_of_payment",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": "Amount",
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 140,
        },
    ]

    # ---------------------------------------
    # Data + Totals
    # ---------------------------------------
    data = []
    mop_totals = {}
    grand_total = 0

    for row in ledger:
        amount = flt(row.get("amount"))

        # detectar doctype dinámico
        ref = row.get("reference")
        ref_doctype = None

        if row["type"] == "Invoice Payment" or row["type"] == "Change":
            ref_doctype = "Sales Invoice"
        elif row["type"] == "Payment Entry":
            ref_doctype = "Payment Entry"
        elif row["type"] == "Journal Entry":
            ref_doctype = "Journal Entry"

        data.append({
            "type": row["type"],
            "reference": ref,
            "reference_doctype": ref_doctype,
            "posting_date": row.get("posting_date"),
            "mode_of_payment": row.get("mode_of_payment"),
            "amount": amount,
        })

        # totals
        mop = row.get("mode_of_payment") or "Unknown"
        mop_totals[mop] = mop_totals.get(mop, 0) + amount
        grand_total += amount

    # ---------------------------------------
    # Totals Section (visual separator)
    # ---------------------------------------
    data.append({})
    data.append({
        "type": "=== TOTALS BY MOP ===",
    })

    for mop, total in mop_totals.items():
        data.append({
            "mode_of_payment": mop,
            "amount": total
        })

    data.append({})
    data.append({
        "type": "GRAND TOTAL",
        "amount": grand_total
    })

    # ---------------------------------------
    # VALIDATION vs expected_amount
    # ---------------------------------------
    expected_total = sum([flt(d.expected_amount) for d in closing.payment_reconciliation])

    data.append({})
    data.append({
        "type": "EXPECTED AMOUNT",
        "amount": expected_total
    })

    data.append({
        "type": "DIFFERENCE",
        "amount": grand_total - expected_total
    })

    return columns, data