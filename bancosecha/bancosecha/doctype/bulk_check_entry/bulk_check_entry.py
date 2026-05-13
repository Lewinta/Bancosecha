# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.doctype.journal_entry.journal_entry import get_party_account_and_currency


class BulkCheckEntry(Document):
    def validate(self):
        self.validate_checks()
        self.fetch_accounts()
        self.calculate_totals()

    def validate_checks(self):
        if not self.checks:
            frappe.throw(_("Please add at least one check to proceed."))

        for row in self.checks:
            amount = flt(row.check_amount, 2)

            if not amount or amount <= 0:
                frappe.throw(_("Row {0}: Check amount must be greater than zero.").format(row.idx))

            if not row.check_no:
                frappe.throw(_("Row {0}: Check number is required.").format(row.idx))

    @frappe.whitelist()
    def fetch_accounts(self):
        company_name = self.company
        cost_center = frappe.get_doc("Cost Center", self.cost_center)

        if not company_name:
            company_name = frappe.get_single_value("Global Defaults", "default_company")

        if not company_name:
            frappe.throw(_("Please set a Company to fetch accounts."))

        company = frappe.get_doc("Company", company_name)

        if not cost_center.custom_check_fee:
            frappe.throw(
                _("Please set a Check Fee account in Cost Center {0}.").format(self.cost_center)
            )

        if not cost_center.custom_expense_check:
            frappe.throw(
                _("Please set a Check Expense account in Cost Center {0}.").format(self.cost_center)
            )

        self.receivable_account = company.default_receivable_account
        self.payment_account = get_bank_cash_account(self.mode_of_payment, company_name).get("account")
        self.income_account = cost_center.custom_check_fee
        self.expense_account = cost_center.custom_expense_check

    def calculate_totals(self):
        total_check = sum(flt(row.check_amount, 2) for row in self.checks)
        total_fee = sum(flt(row.fee, 2) for row in self.checks)

        self.total_check = flt(total_check, 2)
        self.total_fee = flt(total_fee, 2)

        net_total = flt(self.total_check - self.total_fee, 2)

        self.net_total = net_total
        self.paid_amount = flt(self.paid_amount, 2)  # normalizar si viene del UI
        self.difference_amount = flt(net_total - self.paid_amount, 2)

    def on_submit(self):
        self._create_check_entries()

    def _create_check_entries(self):
        """Create one Check Entry per row and immediately make its disbursement JV."""
        for row in self.checks:
            customer = row.customer or self.customer
            check_issuer = row.check_issuer or self.check_issuer

            amount = flt(row.check_amount, 2)
            fee = flt(row.fee, 2)

            net_amount = flt(amount - fee, 2)

            ce = frappe.new_doc("Check Entry")
            ce.update({
                "company": self.company,
                "posting_date": self.posting_date,
                "cost_center": self.cost_center,
                "mode_of_payment": self.mode_of_payment,
                "customer": customer,
                "check_issuer": check_issuer,
                "amount": amount,
                "check_no": row.check_no,
                "fee_percentage": flt(row.fee_percentage, 2),
                "fee": fee,
                "net_amount": net_amount,
                "paid_amount": net_amount,
                "difference": 0.00,
                "custom_bulk_check_entry": self.name,
            })

            ce.insert(ignore_permissions=True)
            ce.workflow_state = "Cashed"
            ce.submit()

            # Seguridad adicional
            if not ce.journal_entry:
                ce.make_disbursement_entry()

            row.db_set("check_entry", ce.name)

    def on_cancel(self):
        """Cancel all child Check Entries (which cancel their own JVs)."""
        for row in self.checks:
            if not row.check_entry:
                continue

            ce = frappe.get_doc("Check Entry", row.check_entry)

            if ce.docstatus == 1:
                ce.cancel()

    def on_trash(self):
        for row in self.checks:
            if row.check_entry:
                frappe.delete_doc("Check Entry", row.check_entry, force=True)


@frappe.whitelist()
def get_receivable_account(company, customer):
    """Return receivable account for a given customer — called from JS on row change."""
    if not customer:
        return None

    d = get_party_account_and_currency(company, "Customer", customer)
    return d.get("account") if d else None