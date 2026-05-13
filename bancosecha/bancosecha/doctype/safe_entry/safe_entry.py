# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from frappe import _
from frappe.query_builder import DocType
from frappe.model.document import Document


class SafeEntry(Document):
    def on_submit(self):
        if self.workflow_state == "Approved":
            self.make_disbursement_entry()
    
    def on_cancel(self):
        if self.workflow_state == "Canceled":
            self.cancel_disbursement_entry()
    
    @frappe.whitelist()
    def add_default_cash_account(self):
        POSProfile = DocType("POS Profile")
        POSProfileUser = DocType("POS Profile User")
        MOPAccount = DocType("Mode of Payment Account")

        query = (
            frappe.qb.from_(POSProfile)
            .join(POSProfileUser)
            .on(POSProfile.name == POSProfileUser.parent)
            .join(MOPAccount)
            .on(MOPAccount.parent == POSProfile.posa_cash_mode_of_payment)
            .select(
                POSProfile.posa_cash_mode_of_payment,
                MOPAccount.default_account
            )
            .where(POSProfileUser.user == frappe.session.user)
            .where(POSProfileUser.default == 1)
            .where(MOPAccount.company == self.company)
            .limit(1)
        )

        result = query.run(as_dict=True)

        if not result:
            return None

        if self.cost_center and not self.safe_account:
            self.safe_account = frappe.get_value(
                "Cost Center",
                self.cost_center,
                "custom_safe_account"
            )
        self.cash_account = result[0]["default_account"]

    def make_disbursement_entry(self):
        jv = frappe.new_doc("Journal Entry")
        jv.update({
            "voucher_type": "Journal Entry",
            "posting_date": self.posting_date,
            "company": self.company,
            "docstatus": 1,
            "remarks": f"Safe Entry: {self.name}",
            "custom_safe_entry": self.name
        })

        jv.append("accounts", {
            "account": self.cash_account,
            "debit_in_account_currency": self.total_amount if self.type == "Withdrawal" else 0,
            "debit": self.total_amount if self.type == "Withdrawal" else 0,
            "credit_in_account_currency": self.total_amount if self.type == "Deposit" else 0,
            "credit": self.total_amount if self.type == "Deposit" else 0,
            "cost_center": self.cost_center,
        })

        jv.append("accounts", {
            "account": self.safe_account,
            "debit_in_account_currency": self.total_amount if self.type == "Deposit" else 0,
            "debit": self.total_amount if self.type == "Deposit" else 0,
            "credit_in_account_currency": self.total_amount if self.type == "Withdrawal" else 0,
            "credit": self.total_amount if self.type == "Withdrawal" else 0,
            "cost_center": self.cost_center,
        })
        
        jv.docstatus = 1
        jv.save(ignore_permissions=True)

    def cancel_disbursement_entry(self):
        jv = frappe.get_doc("Journal Entry", {"custom_safe_entry": self.name})
        if jv.docstatus == 1:
            jv.cancel()

