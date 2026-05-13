# Copyright (c) 2025, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.query_builder import DocType
from frappe.model.document import Document
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.doctype.journal_entry.journal_entry import get_party_account_and_currency


class CheckEntry(Document):
    def validate(self):
        self.validate_paid_amount()
        self.fetch_accounts()

    def on_submit(self):
        # self.validate_attachment()
        self.set_default_issuer()

        # Trigger payment entry when workflow state is "Cashed"
        if self.workflow_state == "Cashed":
            self.make_disbursement_entry()
        
    def validate_paid_amount(self):
        if not self.paid_amount:
            frappe.throw(_("Debes ingresar las denominaciones pagadas para continuar."))
        if flt(self.paid_amount, 2) < flt(self.net_amount, 2):
            frappe.throw(_("El monto a pagar no coincide con el monto pagado, favor revisar las denominaciones!"))

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
    
    @frappe.whitelist()
    def add_default_mop(self):
        POSProfile = DocType("POS Profile")
        POSProfileUser = DocType("POS Profile User")

        query = (
            frappe.qb.from_(POSProfile)
            .join(POSProfileUser)
            .on(POSProfile.name == POSProfileUser.parent)
            .select(POSProfile.posa_cash_mode_of_payment)
            .where(POSProfileUser.user == frappe.session.user)
            .where(POSProfileUser.default == 1)
            .limit(1)
        )

        result = query.run(as_dict=True)

        if result:
            self.mode_of_payment = result[0]["posa_cash_mode_of_payment"]

         


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
            "docstatus": 1,
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
            "credit_in_account_currency": self.paid_amount,
            "credit": self.paid_amount,
            "cost_center": self.cost_center
        })

        if self.difference and abs(self.difference) > 0:
            round_off_account = frappe.get_value(
                "Company",
                self.company,
                "round_off_account"
            )
            jv.append("accounts", {
                "account": round_off_account,
                "credit_in_account_currency": self.difference,
                "credit": self.difference,
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
        print(jv.as_json())
        jv.docstatus = 1
        jv.save(ignore_permissions=True)

        self.db_set("journal_entry", jv.name)

        # frappe.msgprint(_("Journal Entry {0} created for payment.").format(jv.name))

    def make_clearance_entry(self):
        jv = frappe.new_doc("Journal Entry")
        
        jv.update({
            "voucher_type": "Journal Entry",
            "posting_date": nowdate(),
            "company": self.company,
            "docstatus": 1,
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

        jv.save(ignore_permissions=True)


@frappe.whitelist()
def get_check_history_html(check_issuer=None, customer=None):

    issuer_checks = []
    customer_checks = []

    if check_issuer:
        issuer_checks = frappe.db.sql("""
            SELECT posting_date, customer, amount, workflow_state
            FROM `tabCheck Entry`
            WHERE check_issuer = %s
            ORDER BY posting_date DESC
        """, check_issuer, as_dict=True)

    if customer:
        customer_checks = frappe.db.sql("""
            SELECT posting_date, check_issuer, amount, workflow_state
            FROM `tabCheck Entry`
            WHERE customer = %s
            ORDER BY posting_date DESC
        """, customer, as_dict=True)


    def summarize(checks):
        total_checks = len(checks)
        total_amount = sum(c.amount for c in checks if c.amount)

        returned = len([
            c for c in checks
            if c.workflow_state not in ["Approved", "Cashed"]
        ])

        return_rate = (returned / total_checks * 100) if total_checks else 0

        # risk color
        if return_rate > 15:
            risk_color = "risk-high"
        elif return_rate > 5:
            risk_color = "risk-medium"
        else:
            risk_color = "risk-low"

        return {
            "total_checks": total_checks,
            "returned": returned,
            "return_rate": round(return_rate, 1),
            "total_amount": total_amount,
            "risk_color": risk_color
        }



    issuer_summary = summarize(issuer_checks)
    customer_summary = summarize(customer_checks)


    html = frappe.render_template(
        "bancosecha/templates/doctypes/check_entry_summary.html",
        {
            "issuer_checks": issuer_checks,
            "customer_checks": customer_checks,
            "issuer_summary": issuer_summary,
            "customer_summary": customer_summary
        }
    )

    return html

    

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def check_issuer_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""
        SELECT
            ci.name,
            iba.bank_account,
            iba.bank
        FROM `tabCheck Issuer` ci
        LEFT JOIN `tabIssuer Bank Account` iba
            ON iba.parent = ci.name
        WHERE
            ci.name LIKE %(txt)s
            OR iba.bank_account LIKE %(txt)s
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })
