# Copyright (c) 2026, Yefri Tavarez and Contributors
# For license information, please see license.txt

import frappe

@frappe.whitelist()
def get_all_companies():
    out = dict()
    for row in frappe.get_all(
        "Cost Center",
        filters={"is_group": 0},
        fields=["name", "company"],
        order_by="company Asc, name Asc"
    ):
        if row.company not in out:
            out[row.company] = list()
        out[row.company].append(row.name)

    return out
