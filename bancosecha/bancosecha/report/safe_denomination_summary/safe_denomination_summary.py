# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


DENOMINATIONS = [
    ("_10000", 100.00, "$100"),
    ("_5000",   50.00, "$50"),
    ("_2000",   20.00, "$20"),
    ("_1000",   10.00, "$10"),
    ("_500",     5.00, "$5"),
    ("_100",     1.00, "$1"),
    # ("_050",     0.50, "$0.50"),
    ("_025",     0.25, "$0.25"),
    ("_010",     0.10, "$0.10"),
    ("_005",     0.05, "$0.05"),
    ("_001",     0.01, "$0.01"),
]


COST_CENTER_COLORS = {
    "HALL - B":       "#c4f2cb",
    "MCNAUGHTEN - B": "#94c8f7",
}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart


def get_chart(data):
    labels = [label for _f, _v, label in DENOMINATIONS]

    datasets = []
    colors = []
    for row in data:
        cc = row.get("cost_center")
        if not cc:
            continue
        short_name = cc.split(" - ")[0].title()
        values = [row.get(f"qty{f}") or 0 for f, _v, _l in DENOMINATIONS]
        datasets.append({"name": short_name, "values": values})
        colors.append(COST_CENTER_COLORS.get(cc, "#7f8c8d"))

    return {
        "data": {"labels": labels, "datasets": datasets},
        "type": "bar",
        "colors": ["#c4f2cb", "#94c8f7"],
        "barOptions": {"spaceRatio": 0.3},
    }


def get_columns():
    columns = [
        {
            "label": _("Cost Center"),
            "fieldname": "cost_center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 220,
        },
    ]

    for fieldname, value, label in DENOMINATIONS:
        columns.append({
            "label": _("{0} Qty").format(label),
            "fieldname": f"qty{fieldname}",
            "fieldtype": "Int",
            "width": 90,
        })
        columns.append({
            "label": _("{0} Amount").format(label),
            "fieldname": f"amt{fieldname}",
            "fieldtype": "Currency",
            "width": 110,
        })

    columns.append({
        "label": _("Total Amount"),
        "fieldname": "total_amount",
        "fieldtype": "Currency",
        "width": 140,
    })

    return columns


def get_data(filters):
    sign_case = ", ".join([
        f"SUM(CASE WHEN type = 'Deposit' THEN {f} ELSE -{f} END) AS {f}"
        for f, _v, _l in DENOMINATIONS
    ])

    conditions = ["docstatus = 1", "workflow_state = 'Approved'"]
    params = {}

    if filters.get("company"):
        conditions.append("company = %(company)s")
        params["company"] = filters.company

    if filters.get("cost_center"):
        conditions.append("cost_center = %(cost_center)s")
        params["cost_center"] = filters.cost_center

    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
        params["from_date"] = filters.from_date

    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
        params["to_date"] = filters.to_date

    where_clause = " AND ".join(conditions)

    rows = frappe.db.sql(
        f"""
        SELECT
            cost_center,
            {sign_case}
        FROM `tabSafe Entry`
        WHERE {where_clause}
        GROUP BY cost_center
        ORDER BY cost_center
        """,
        params,
        as_dict=True,
    )

    data = []
    for row in rows:
        out = {"cost_center": row.cost_center}
        total = 0.0
        for fieldname, value, _label in DENOMINATIONS:
            qty = int(row.get(fieldname) or 0)
            amount = flt(qty * value, 2)
            out[f"qty{fieldname}"] = qty
            out[f"amt{fieldname}"] = amount
            total += amount
        out["total_amount"] = flt(total, 2)
        data.append(out)

    return data
