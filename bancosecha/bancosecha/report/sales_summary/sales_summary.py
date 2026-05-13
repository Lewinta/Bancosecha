# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.query_builder import Criterion, DocType, Table	
from pypika import functions as fn


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    group_by = filters.get("group_by")

    group_label = "Group"
    if group_by == "Invoice Type":
        group_label = "Invoice Type"
    elif group_by == "Customer":
        group_label = "Customer"
    elif group_by == "Supplier":
        group_label = "Supplier"
    elif group_by == "Cashier":
        group_label = "Cashier"

    return [
        {"label": group_label, "fieldname": "group_value", "fieldtype": "Data", "width": 200},
        {"label": "Total Amount", "fieldname": "total_amount", "fieldtype": "Currency", "width": 150},
        {"label": "Service Charge", "fieldname": "service_charge", "fieldtype": "Currency", "width": 150},
        {"label": "Invoice Count", "fieldname": "invoice_count", "fieldtype": "Int", "width": 120},
    ]


def get_data(filters):

    
    si = DocType("Sales Invoice")
    user = DocType("User")
    service_charge = Table("viewService Charge Summary")
    group_by = filters.get("group_by")
    conditions = [
        si.docstatus == 1,
        si.posting_date >= filters.get("from_date"),
        si.posting_date <= filters.get("to_date"),
    ]

    if filters.get("pos_profile"):
        conditions.append(si.pos_profile == filters.get("pos_profile"))

    if group_by == "Invoice Type":
        group_field = si.custom_invoice_type
        join_user = False

    elif group_by == "Customer":
        group_field = si.customer
        join_user = False

    elif group_by == "Supplier":
        group_field = si.custom_supplier
        join_user = False

    elif group_by == "Cashier":
        group_field = user.full_name
        join_user = True

    else:
        group_field = si.customer
        join_user = False

    query = (
        frappe.qb.from_(si)
        .left_join(service_charge)
        .on(service_charge.parent == si.name)
        .select(
            fn.Coalesce(group_field.as_("group_value"), "Other").as_("group_value"),
            fn.Sum(si.grand_total).as_("total_amount"),
            fn.Sum(fn.Coalesce(service_charge.amount, 0)).as_("service_charge"),
            fn.Count(si.name).as_("invoice_count"),
        ).where(Criterion.all(conditions))
    )

    if filters.get("company"):
        query = query.where(si.company == filters.get("company"))

    if filters.get("cost_center"):
        query = query.where(si.cost_center == filters.get("cost_center"))

    if join_user:
        query = query.join(user).on(si.owner == user.name)

    query = query.groupby(group_field)

    return query.run(as_dict=True)