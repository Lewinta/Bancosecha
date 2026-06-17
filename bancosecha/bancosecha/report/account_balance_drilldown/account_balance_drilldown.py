# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from erpnext.accounts.utils import get_balance_on


PNL_REPORT_TYPE = "Profit and Loss"
INVERT_BALANCE_ROOT_TYPES = ("Income", "Liability", "Equity")


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def validate_filters(filters):
    for field, label in (
        ("company", _("Company")),
        ("from_date", _("From Date")),
        ("to_date", _("To Date")),
        ("account", _("Account")),
    ):
        if not filters.get(field):
            frappe.throw(_("{0} is required").format(label))

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
    return [
        {
            "label": _("Account"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 320,
        },
        {
            "label": _("Account Name"),
            "fieldname": "account_name",
            "fieldtype": "Data",
            "width": 280,
        },
        {
            "label": _("Is Group"),
            "fieldname": "is_group",
            "fieldtype": "Check",
            "hidden": 1,
            "width": 80,
        },
        {
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
            "width": 80,
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150,
        },
    ]


def get_data(filters):
    parent = frappe.db.get_value(
        "Account",
        filters.account,
        [
            "name",
            "account_name",
            "is_group",
            "account_currency",
            "lft",
            "rgt",
            "company",
            "report_type",
            "root_type",
        ],
        as_dict=True,
    )
    if not parent:
        return []

    if parent.company != filters.company:
        frappe.throw(
            _("Account {0} does not belong to Company {1}").format(
                frappe.bold(filters.account), frappe.bold(filters.company)
            )
        )

    if parent.report_type != PNL_REPORT_TYPE:
        frappe.throw(
            _("Account {0} is not a Profit and Loss account. Only P&L accounts are supported by this report.").format(
                frappe.bold(filters.account)
            )
        )

    if not parent.is_group:
        return [build_row(parent, filters)]

    leaves = frappe.db.get_all(
        "Account",
        filters={
            "company": filters.company,
            "is_group": 0,
            "lft": [">=", parent.lft],
            "rgt": ["<=", parent.rgt],
        },
        fields=["name", "account_name", "is_group", "account_currency", "root_type"],
        order_by="lft",
    )
    return [build_row(account, filters) for account in leaves]


def build_row(account, filters):
    balance = get_balance_on(
        account=account.name,
        date=filters.to_date,
        start_date=filters.from_date,
        company=filters.company,
        cost_center=filters.cost_center,
        in_account_currency=False,
    )
    if account.get("root_type") in INVERT_BALANCE_ROOT_TYPES:
        balance = -balance
    return {
        "account": account.name,
        "account_name": account.account_name,
        "is_group": account.is_group,
        "currency": account.account_currency,
        "balance": balance,
    }
