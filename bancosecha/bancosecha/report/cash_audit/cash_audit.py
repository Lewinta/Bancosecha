# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe import qb

def execute(filters=None):
    filters = frappe._dict(filters or {})

    if filters.get("account") and isinstance(filters.account, list):
        filters.account = tuple(filters.account)

    if not filters.account:
        return [], []

    if not filters.from_date or not filters.to_date:
        frappe.throw(_("From Date and To Date are mandatory"))

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 120},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120},
    ]
    if filters.get("type") == "Check Entry":
        columns.append({"label": _("Fee %"), "fieldname": "fee_percentage", "fieldtype": "Data", "width": 70})
        columns.append({"label": _("Check Amount"), "fieldname": "check_amount", "fieldtype": "Currency", "width": 130})

    columns += [
        {"label": _("Net"), "fieldname": "net_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Data", "width": 120},
        {"label": _("Voucher No"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 150},
        {"label": _("Opening Shift"), "fieldname": "opening_shift", "fieldtype": "Data", "width": 150},

        {"label": _("Invoice Type"), "fieldname": "custom_invoice_type", "fieldtype": "Data", "width": 150},
        {"label": _("Supplier"), "fieldname": "custom_supplier", "fieldtype": "Data", "width": 180},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 250},
    ]

    return columns

def get_opening_balance(filters):

    result = frappe.db.sql("""
        SELECT
            COALESCE(SUM(debit),0) as debit,
            COALESCE(SUM(credit),0) as credit
        FROM `tabGL Entry`
        WHERE account IN %(account)s
        AND posting_date < %(from_date)s
        AND is_cancelled = 0
    """, filters, as_dict=1)[0]

    return result.debit - result.credit

def get_data(filters):

    opening_balance = get_opening_balance(filters)

    gle = frappe.db.sql("""
        SELECT
            gle.posting_date,
            SUM(gle.debit) AS debit,
            SUM(gle.credit) AS credit,
            gle.voucher_type,
            gle.voucher_no,

            CASE
                WHEN gle.voucher_type = 'Sales Invoice' THEN si.posa_pos_opening_shift
                ELSE '-'
            END AS opening_shift,
            CASE
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_check_entry IS NOT NULL THEN ce.amount
                ELSE 0
            END AS check_amount,
            CASE
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_check_entry IS NOT NULL THEN ce.fee_percentage
                ELSE 0
            END AS fee_percentage,
            CASE
                WHEN gle.voucher_type = 'Sales Invoice' THEN si.customer_name
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_check_entry IS NOT NULL THEN ce.customer
                ELSE COALESCE(je.user_remark, ' ')
            END AS customer_name,

            CASE
                WHEN gle.voucher_type = 'Sales Invoice' THEN si.custom_invoice_type
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_check_entry IS NOT NULL THEN 'Check Entry'
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_safe_entry IS NOT NULL THEN 'Safe Entry'
                ELSE 'Other'
            END AS custom_invoice_type,

            CASE
                WHEN gle.voucher_type = 'Sales Invoice' THEN COALESCE(si.custom_supplier, ' ')
                WHEN gle.voucher_type = 'Journal Entry' AND je.custom_check_entry IS NOT NULL THEN COALESCE(ce.check_issuer, ' ')
                ELSE ' '
            END AS custom_supplier

        FROM `tabGL Entry` gle

        LEFT JOIN `tabSales Invoice` si
            ON gle.voucher_no = si.name
            AND gle.voucher_type = 'Sales Invoice'

        LEFT JOIN `tabJournal Entry` je
            ON gle.voucher_no = je.name
            AND gle.voucher_type = 'Journal Entry'

        LEFT JOIN `tabCheck Entry` ce
            ON je.custom_check_entry = ce.name

        WHERE gle.account IN %(account)s
        AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
        AND gle.is_cancelled = 0
        GROUP BY gle.voucher_type, gle.voucher_no,gle.account

        ORDER BY gle.posting_date, gle.creation
    """, filters, as_dict=1, debug=False)
    
    balance = opening_balance
    total_debit = 0
    total_credit = 0
    total_check = 0
    supplier = filters.get("supplier")
    data = []
    if not filters.get("type"):
        # Opening balance row
        data.append({
            "posting_date": filters.from_date,
            "debit": 0,
            "credit": 0,
            "net_amount": opening_balance,
            "check_amount": 0,
            "fee_percentage": 0,
            "balance": opening_balance,
            "voucher_type": "Opening",
            "voucher_no": "",
            "opening_shift": "",
            "customer_name": "",
            "custom_invoice_type": "",
            "supplier": ""
        })

    for row in gle:
        report_type = filters.get("type")

        if report_type:
            # Sales Invoice → strictly by voucher_type
            if report_type == "Sales Invoice":
                if row.voucher_type != "Sales Invoice":
                    continue

                # optional supplier filter
                if filters.get("supplier") and row.custom_supplier != filters.get("supplier"):
                    continue

            # Other → catch-all
            elif report_type == "Other":
                if row.custom_invoice_type != "Other":
                    continue

            # Check Entry / Safe Entry → normal behavior
            else:
                if row.custom_invoice_type != report_type:
                    continue

        balance += row.debit - row.credit
        total_debit += row.debit
        total_credit += row.credit
        total_check += row.check_amount

        data.append({
            "posting_date": row.posting_date,
            "debit": row.debit,
            "credit": row.credit,
            "fee_percentage": f'{row.fee_percentage} %' ,
            "check_amount": row.check_amount,
            "net_amount": row.debit - row.credit,
            "balance": balance,
            "voucher_type": row.voucher_type,
            "voucher_no": row.voucher_no,
            "opening_shift": row.opening_shift,
            "customer_name": row.customer_name,
            "custom_invoice_type": row.custom_invoice_type,
            "custom_supplier": row.custom_supplier
        })

    # Totales
    data.append({
        "posting_date": "TOTAL",
        "debit": total_debit,
        "credit": total_credit,
        "fee_percentage": ' ',
        "check_amount": total_check,
        "net_amount": total_debit - total_credit,
        "balance": balance,
        "voucher_type": " ",
        "voucher_no": " ",
        "opening_shift": " ",
        "customer_name": " ",
        "custom_invoice_type": " ",
        "custom_supplier": " "
    })

    return data

@frappe.whitelist()
def get_default_cash_accounts(user=None):
    if not user:
        user = frappe.session.user
    pu = qb.DocType('POS Profile User')
    pp = qb.DocType('POS Profile')
    data = qb.from_(pu).join(pp).on(
        pu.parent == pp.name
    ).select(
        pp.account_for_change_amount
    ).where(
        pu.user == user,
    ).run(as_dict=True)


    return data[0].account_for_change_amount if data else None