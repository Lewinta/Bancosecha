# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _


GROUP_BY_MAP = {
    "Cost Center": "ce.cost_center",
    "Check Issuer": "ce.check_issuer",
    "Customer": "ce.customer",
    "Owner": "ce.owner",
}


def execute(filters=None):
    filters = frappe._dict(filters or {})

    if not filters.from_date or not filters.to_date:
        frappe.throw(_("From Date and To Date are mandatory"))

    group_by = filters.get("group_by")
    if group_by and group_by not in GROUP_BY_MAP:
        frappe.throw(_("Invalid Group By value"))

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    group_by = filters.get("group_by")

    if group_by:
        group_fieldtype, group_options = _group_column_meta(group_by)
        return [
            {
                "label": _(group_by),
                "fieldname": "group_value",
                "fieldtype": group_fieldtype,
                "options": group_options,
                "width": 260,
            },
            {"label": _("Check Amount"), "fieldname": "check_amount", "fieldtype": "Currency", "width": 160},
            {"label": _("Fee"), "fieldname": "fee", "fieldtype": "Currency", "width": 140},
            {"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 160},
        ]

    return [
        {"label": _("Workflow State"), "fieldname": "workflow_state", "fieldtype": "Link", "options": "Workflow State", "width": 140},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": _("Check No."), "fieldname": "check_no", "fieldtype": "Data", "width": 120},
        {"label": _("Check Issuer"), "fieldname": "check_issuer", "fieldtype": "Link", "options": "Check Issuer", "width": 180},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 200},
        {"label": _("Check Amount"), "fieldname": "check_amount", "fieldtype": "Currency", "width": 130},
        {"label": _("Fee %"), "fieldname": "fee_percentage", "fieldtype": "Percent", "width": 80},
        {"label": _("Fee"), "fieldname": "fee", "fieldtype": "Currency", "width": 110},
        {"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 180},
        {"label": _("Owner"), "fieldname": "owner", "fieldtype": "Data", "width": 180},
    ]


def _group_column_meta(group_by):
    if group_by == "Cost Center":
        return "Link", "Cost Center"
    if group_by == "Check Issuer":
        return "Link", "Check Issuer"
    if group_by == "Customer":
        return "Link", "Customer"
    return "Data", ""


def get_data(filters):
    group_by = filters.get("group_by")
    conditions, values = _build_conditions(filters)

    if group_by:
        group_expr = "u.full_name" if group_by == "Owner" else GROUP_BY_MAP[group_by]
        group_key = GROUP_BY_MAP[group_by]

        rows = frappe.db.sql(
            f"""
            SELECT
                {group_expr} AS group_value,
                COALESCE(SUM(ce.amount), 0)      AS check_amount,
                COALESCE(SUM(ce.fee), 0)         AS fee,
                COALESCE(SUM(ce.paid_amount), 0) AS paid_amount
            FROM `tabCheck Entry` ce
            LEFT JOIN `tabUser` u ON u.name = ce.owner
            WHERE {conditions}
            GROUP BY {group_key}
            ORDER BY {group_expr}
            """,
            values,
            as_dict=1,
        )

        total_check = sum(r.check_amount for r in rows)
        total_fee = sum(r.fee for r in rows)
        total_paid = sum(r.paid_amount for r in rows)

        rows.append({
            "group_value": _("Total"),
            "check_amount": total_check,
            "fee": total_fee,
            "paid_amount": total_paid,
        })
        return rows

    rows = frappe.db.sql(
        f"""
        SELECT
            ce.name,
            ce.workflow_state,
            ce.posting_date,
            ce.check_no,
            ce.check_issuer,
            ce.customer,
            ce.amount AS check_amount,
            ce.fee_percentage,
            ce.fee,
            ce.paid_amount,
            ce.cost_center,
            COALESCE(u.full_name, ce.owner) AS owner
        FROM `tabCheck Entry` ce
        LEFT JOIN `tabUser` u ON u.name = ce.owner
        WHERE {conditions}
        ORDER BY ce.posting_date, ce.creation
        """,
        values,
        as_dict=1,
    )

    if not rows:
        return rows

    total_check = sum(r.check_amount or 0 for r in rows)
    total_fee = sum(r.fee or 0 for r in rows)
    total_paid = sum(r.paid_amount or 0 for r in rows)

    rows.append({
        "workflow_state": "",
        "posting_date": None,
        "check_no": _("Total"),
        "check_issuer": "",
        "customer": "",
        "check_amount": total_check,
        "fee_percentage": None,
        "fee": total_fee,
        "paid_amount": total_paid,
        "cost_center": "",
        "owner": "",
    })

    return rows


def _build_conditions(filters):
    conditions = ["ce.docstatus < 2", "ce.posting_date BETWEEN %(from_date)s AND %(to_date)s"]
    values = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    if filters.get("cost_center"):
        conditions.append("ce.cost_center = %(cost_center)s")
        values["cost_center"] = filters.cost_center

    if filters.get("check_issuer"):
        conditions.append("ce.check_issuer = %(check_issuer)s")
        values["check_issuer"] = filters.check_issuer

    if filters.get("customer"):
        conditions.append("ce.customer = %(customer)s")
        values["customer"] = filters.customer

    return " AND ".join(conditions), values
