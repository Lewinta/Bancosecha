# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.doctype.journal_entry.journal_entry import get_party_account_and_currency


class CheckEntry(Document):
	def validate(self):
		self.fetch_accounts()

	def on_submit(self):
		# self.validate_attachment()
		self.set_default_issuer()

		# 🔹 Trigger payment entry when workflow state is "Cashed"
		if self.workflow_state == "Cashed":
			self.make_disbursement_entry()
		
	def on_cancel(self):
		entries = frappe.db.get_list(
			"Journal Entry",
			filters={
				"custom_check_entry": self.name,
			}
		)
		for entry in entries:
			jv = frappe.get_doc("Journal Entry", entry.name)
			if jv.docstatus == 1:
				jv.cancel()
		
	
	def on_trash(self):
		filters = {"custom_check_entry": self.name}
		entries = frappe.db.get_list( "Journal Entry", filters=filters)
		for entry in entries:
			frappe.delete_doc("Journal Entry", entry.name, force=True)
		

	def on_update_after_submit(self):
		if self.workflow_state == "Collected":
			self.make_clearance_entry()
		
		if self.workflow_state == "Lost":
			self.make_loss_entry()

	def fetch_accounts(self):
		if d := get_bank_cash_account(
			self.mode_of_payment,
			self.company
		):
			self.payment_account = d.get("account")
		else:
			frappe.throw(
				_("Please set a Bank/Cash account for the Mode of Payment {0}.").format(
					self.mode_of_payment
				)
			)
		if d := get_party_account_and_currency(
			self.company,
			"Customer",
			self.customer
		):
			self.receivable_account = d.get("account")
		else:
			frappe.throw(
				_("Please set a Receivable account for the Customer {0}.").format(
					self.customer
				)
			)

		cost_center = frappe.get_doc("Cost Center", self.cost_center)
		if not cost_center.custom_check_fee:
			frappe.throw(
				_("Please set a Check Fee account in the Cost Center {0}.").format(
					self.cost_center
				)
			)
		
		if not cost_center.custom_expense_check:
			frappe.throw(
				_("Please set a Check Expense account in the Cost Center {0}.").format(
					self.cost_center
				)
			)
		self.income_account = cost_center.custom_check_fee
		self.expense_account = cost_center.custom_expense_check

	def validate_attachment(self):
		filters = {
			"attached_to_name": self.name,
			"attached_to_doctype": self.doctype,
		}
		if not frappe.db.exists("File", filters):
			frappe.throw(
				_("Kindly attach the check image before proceeding with the payment.")
			)
	
	def set_default_issuer(self):
		if not self.check_issuer:
			return
		frappe.db.set_value(
			"Customer",
			self.customer,
			"custom_check_issuer",
			self.check_issuer
		)

	def make_disbursement_entry(self):
		net_amount = flt(self.amount) - flt(self.fee)
		if not self.income_account:
			frappe.throw(
				_("Please set a Check Fee account in the Cost Center {0}.").format(self.cost_center)
			)

		jv = frappe.new_doc("Journal Entry")
		jv.update({
			"voucher_type": "Journal Entry",
			"posting_date": self.posting_date,
			"company": self.company,
			"remarks": f"Check Entry: {self.name}",
			"custom_check_entry": self.name
		})

		jv.append("accounts", {
			"account": self.receivable_account,
			"debit_in_account_currency": self.amount,
			"debit": self.amount,
			"cost_center": self.cost_center,
			"party_type": "Customer",
			"party": self.customer,
			"voucher_type": self.doctype,
			"voucher_no": self.name
		})

		jv.append("accounts", {
			"account": self.payment_account,
			"credit_in_account_currency": net_amount,
			"credit": net_amount,
			"cost_center": self.cost_center
		})
		
		if self.fee:
			fee_account = frappe.get_value(
				"Cost Center",
				self.cost_center,
				"custom_check_fee"
			)
			jv.append("accounts", {
				"account": fee_account,
				"credit_in_account_currency": self.fee,
				"credit": self.fee,
				"cost_center": self.cost_center
			})

		jv.insert(ignore_permissions=True)
		jv.submit()

		self.db_set("journal_entry", jv.name)

		frappe.msgprint(_("Journal Entry {0} created for payment.").format(jv.name))

	def make_clearance_entry(self):
		jv = frappe.new_doc("Journal Entry")
		
		jv.update({
			"voucher_type": "Journal Entry",
			"posting_date": nowdate(),
			"company": self.company,
			"remarks": f"Check Clearance Entry: {self.name}",
			"custom_check_entry": self.name
		})
		
		jv.append("accounts", {
			"account": self.payment_account,
			"debit_in_account_currency": self.amount,
			"debit": self.amount,
			"cost_center": self.cost_center,
		})
		
		jv.append("accounts", {
			"account": self.receivable_account,
			"party_type": "Customer",
			"party": self.customer,
			"credit_in_account_currency": self.amount,
			"credit": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "Journal Entry",
			"reference_name": self.journal_entry
		})

		jv.insert(ignore_permissions=True)
		jv.submit()

	def make_loss_entry(self):
		jv = frappe.new_doc("Journal Entry")
		
		jv.update({
			"voucher_type": "Journal Entry",
			"posting_date": nowdate(),
			"company": self.company,
			"remarks": f"Check Loss Entry: {self.name}",
			"custom_check_entry": self.name
		})
		
		jv.append("accounts", {
			"account": self.expense_account,
			"debit_in_account_currency": self.amount,
			"debit": self.amount,
			"cost_center": self.cost_center,
		})
		
		jv.append("accounts", {
			"account": self.receivable_account,
			"party_type": "Customer",
			"party": self.customer,
			"credit_in_account_currency": self.amount,
			"credit": self.amount,
			"cost_center": self.cost_center,
			"reference_type": "Journal Entry",
			"reference_name": self.journal_entry
		})

		jv.insert(ignore_permissions=True)
		jv.submit()

