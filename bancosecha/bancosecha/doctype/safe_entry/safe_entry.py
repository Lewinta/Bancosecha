# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, today, now
from frappe import _
from frappe.query_builder import DocType
from frappe.model.document import Document


PARTY_REQUIRED_ACCOUNT_TYPES = ("Receivable", "Payable")


class SafeEntry(Document):
    def validate(self):
        self.enforce_posting_datetime()
        self.validate_account_parties()
        self.validate_adjustment_role()

    def validate_adjustment_role(self):
        if not self.is_adjustment:
            return
        if "Accounts Manager" in frappe.get_roles():
            return
        frappe.throw(
            _("Only users with the Accounts Manager role can create Denomination Adjustment entries."),
            frappe.PermissionError,
        )

    def enforce_posting_datetime(self):
        if not self.set_posting_time:
            self.posting_date = today()
            self.posting_time = now().split(" ")[1]

    def validate_account_parties(self):
        for prefix, label in (("safe", _("Safe Account")), ("cash", _("Cash Account"))):
            account = self.get(f"{prefix}_account")
            account_type = (
                frappe.db.get_value("Account", account, "account_type") if account else None
            )
            self.set(f"{prefix}_account_type", account_type or "")

            if account_type in PARTY_REQUIRED_ACCOUNT_TYPES:
                if not self.get(f"{prefix}_party_type") or not self.get(f"{prefix}_party"):
                    frappe.throw(
                        _("{0} is of type {1}. Party Type and Party are required.").format(
                            frappe.bold(label), frappe.bold(account_type)
                        )
                    )
            else:
                self.set(f"{prefix}_party_type", None)
                self.set(f"{prefix}_party", None)

    def on_submit(self):
        if self.workflow_state == "Approved" and not self.is_adjustment:
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

        cash_row = {
            "account": self.cash_account,
            "debit_in_account_currency": self.total_amount if self.type == "Withdrawal" else 0,
            "debit": self.total_amount if self.type == "Withdrawal" else 0,
            "credit_in_account_currency": self.total_amount if self.type == "Deposit" else 0,
            "credit": self.total_amount if self.type == "Deposit" else 0,
            "cost_center": self.cost_center,
        }
        if self.cash_account_type in PARTY_REQUIRED_ACCOUNT_TYPES:
            cash_row["party_type"] = self.cash_party_type
            cash_row["party"] = self.cash_party
        jv.append("accounts", cash_row)

        safe_row = {
            "account": self.safe_account,
            "debit_in_account_currency": self.total_amount if self.type == "Deposit" else 0,
            "debit": self.total_amount if self.type == "Deposit" else 0,
            "credit_in_account_currency": self.total_amount if self.type == "Withdrawal" else 0,
            "credit": self.total_amount if self.type == "Withdrawal" else 0,
            "cost_center": self.cost_center,
        }
        if self.safe_account_type in PARTY_REQUIRED_ACCOUNT_TYPES:
            safe_row["party_type"] = self.safe_party_type
            safe_row["party"] = self.safe_party
        jv.append("accounts", safe_row)

        jv.docstatus = 1
        jv.save(ignore_permissions=True)

    def cancel_disbursement_entry(self):
        jv = frappe.get_doc("Journal Entry", {"custom_safe_entry": self.name})
        if jv.docstatus == 1:
            jv.cancel()

