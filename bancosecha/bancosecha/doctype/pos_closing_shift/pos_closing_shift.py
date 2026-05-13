# -*- coding: utf-8 -*-
# Copyright (c) 2020, Youssef Restom and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import qb
from frappe.query_builder import functions as fn
import json
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class POSClosingShift(Document):
    def validate(self):
        user = frappe.get_all(
            "POS Closing Shift",
            filters={
                "user": self.user,
                "docstatus": 1,
                "pos_opening_shift": self.pos_opening_shift,
                "name": ["!=", self.name],
            },
        )

        if user:
            frappe.throw(
                _(
                    "POS Closing Shift {} against {} between selected period".format(
                        frappe.bold("already exists"), frappe.bold(self.user)
                    )
                ),
                title=_("Invalid Period"),
            )

        if (
            frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status")
            != "Open"
        ):
            frappe.throw(
                _("Selected POS Opening Shift should be open."),
                title=_("Invalid Opening Entry"),
            )
        self.update_payment_reconciliation()

    def update_payment_reconciliation(self):
        # update the difference values in Payment Reconciliation child table
        # get default precision for site
        precision = (
            frappe.get_cached_value("System Settings", None, "currency_precision") or 3
        )
        for d in self.payment_reconciliation:
            d.difference = +flt(d.closing_amount, precision) - flt(
                d.expected_amount, precision
            )

    def on_cancel(self):
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = None
        opening_entry.status = 'Open'
        opening_entry.db_update()

    def on_submit(self):
        opening_entry = frappe.get_doc("POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        self.delete_draft_invoices()
        opening_entry.save()

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            data = frappe.db.sql(
                """
                select
                    name
                from
                    `tabSales Invoice`
                where
                    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
                """,
                (self.pos_opening_shift),
                as_dict=1,
            )

            for invoice in data:
                frappe.delete_doc("Sales Invoice", invoice.name, force=1)

    @frappe.whitelist()
    def get_payment_reconciliation_details(self):
        currency = frappe.get_cached_value("Company", self.company, "default_currency")
        return frappe.render_template(
            "bancosecha/bancosecha/doctype/pos_closing_shift/closing_shift_details.html",
            {"data": self, "currency": currency},
        )


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all("POS Profile User", filters=filters, fields=["user"])
    return [[c["user"]] for c in cashiers_list]


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift):
    submit_printed_invoices(pos_opening_shift)
    data = frappe.db.sql("""
        select name
        from `tabSales Invoice`
        where docstatus = 1 and posa_pos_opening_shift = %s
    """, (pos_opening_shift), as_dict=1)

    updated_data = []
    for d in data:
        doc = frappe.get_doc("Sales Invoice", d.name).as_dict()
        doc.posa_paid_amount = get_paid_amount(d.name)
        updated_data.append(doc)
    return updated_data


@frappe.whitelist()
def get_payments_entries(pos_opening_shift):
    return frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "custom_posa_pos_opening_shift": pos_opening_shift,
            "payment_type": "Receive",
        },
        fields=[
            "name",
            "mode_of_payment",
            "paid_amount",
            "reference_no",
            "posting_date",
            "party",
        ],
    )

@frappe.whitelist()
def get_journal_entries(pos_opening_shift):
    opening_doc = frappe.get_doc("POS Opening Shift", pos_opening_shift)
    GL = qb.DocType("GL Entry")
    PP = qb.DocType("POS Profile")
    PM = qb.DocType("POS Payment Method")
    MA = qb.DocType("Mode of Payment Account")

    return qb.from_(PP).join(PM).on(
        (PM.parent == PP.name)
    ).join(MA).on(
        (MA.parent == PM.mode_of_payment)
    ).join(GL).on(
        (GL.account == MA.default_account)
    ).select(
        GL.voucher_no.as_("journal_entry"),
        GL.posting_date,
        PM.mode_of_payment,
        fn.Sum(GL.debit_in_account_currency - GL.credit_in_account_currency).as_("amount")
    ).where(
        (PP.name == opening_doc.pos_profile) &
        (PM.default == 1) &
        (GL.posting_date == opening_doc.posting_date)&
        (GL.voucher_type == "Journal Entry")&
        (GL.is_cancelled == 0)

    ).groupby( GL.voucher_no ).run(as_dict=True, debug=False)

@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    opening_shift = json.loads(opening_shift)
    submit_printed_invoices(opening_shift.get("name"))
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.pos_opening_shift = opening_shift.get("name")
    closing_shift.period_start_date = opening_shift.get("period_start_date")
    closing_shift.period_end_date = frappe.utils.get_datetime()
    closing_shift.pos_profile = opening_shift.get("pos_profile")
    closing_shift.user = opening_shift.get("user")
    closing_shift.company = opening_shift.get("company")
    closing_shift.grand_total = 0
    closing_shift.net_total = 0
    closing_shift.total_quantity = 0

    invoices = get_pos_invoices(opening_shift.get("name"))
    pos_transactions = []
    taxes = []
    payments = []
    pos_payments_table = []

    pos_payments = get_payments_entries(opening_shift.get("name"))
    jv_entries = get_journal_entries(opening_shift.get("name"))

    for detail in opening_shift.get("balance_details"):
        payments.append(
            frappe._dict({
                "mode_of_payment": detail.get("mode_of_payment"),
                "opening_amount": detail.get("amount") or 0,
                "expected_amount": detail.get("amount") or 0,
            })
        )

    # invoice loop is NOT nested inside balance_details
    for d in invoices:
        pos_transactions.append(
            frappe._dict({
                "sales_invoice": d.name,
                "posting_date": d.posting_date,
                "grand_total": d.grand_total,
                "customer": d.customer,
                "custom_invoice_type": d.custom_invoice_type,
                "custom_supplier": d.custom_supplier,
                "paid_amount": d.get("posa_paid_amount") or 0,
            })
        )
        closing_shift.grand_total += flt(d.grand_total)
        closing_shift.net_total += flt(d.net_total)
        closing_shift.total_quantity += flt(d.total_qty)

        for t in d.taxes:
            existing_tax = [tx for tx in taxes if tx.account_head == t.account_head and tx.rate == t.rate]
            if existing_tax:
                existing_tax[0].amount += flt(t.tax_amount)
            else:
                taxes.append(frappe._dict({
                    "account_head": t.account_head,
                    "rate": t.rate,
                    "amount": t.tax_amount,
                }))

        cash_mode_of_payment = frappe.get_value(
            "POS Profile", opening_shift.get("pos_profile"), "posa_cash_mode_of_payment"
        ) or "Cash"

        for p in d.payments:
            existing_pay = [pay for pay in payments if pay.mode_of_payment == p.mode_of_payment]
            if existing_pay:
                amount = (p.base_amount - d.change_amount) if existing_pay[0].mode_of_payment == cash_mode_of_payment else p.base_amount
                existing_pay[0].expected_amount += flt(amount)
            else:
                payments.append(frappe._dict({
                    "mode_of_payment": p.mode_of_payment,
                    "opening_amount": 0,
                    "expected_amount": p.base_amount,
                }))

    for py in pos_payments:
        pos_payments_table.append(frappe._dict({
            "payment_entry": py.name,
            "mode_of_payment": py.mode_of_payment,
            "paid_amount": py.paid_amount,
            "posting_date": py.posting_date,
            "customer": py.party,
        }))
        existing_pay = [pay for pay in payments if pay.mode_of_payment == py.mode_of_payment]
        if existing_pay:
            existing_pay[0].expected_amount += flt(py.paid_amount)
        else:
            payments.append(frappe._dict({
                "mode_of_payment": py.mode_of_payment,
                "opening_amount": 0,
                "expected_amount": py.paid_amount,
            }))

    for jv in jv_entries:
        existing_pay = [pay for pay in payments if pay.mode_of_payment == jv.mode_of_payment]
        if existing_pay:
            existing_pay[0].expected_amount += flt(jv.amount)
        else:
            payments.append(frappe._dict({
                "mode_of_payment": jv.mode_of_payment,
                "opening_amount": 0,
                "expected_amount": jv.amount,
            }))

    for i in pos_transactions:
        closing_shift.append("pos_transactions", i)
    for i in payments:
        closing_shift.append("payment_reconciliation", i)
    for i in taxes:
        closing_shift.append("taxes", i)
    for i in pos_payments_table:
        closing_shift.append("pos_payments", i)
    for i in jv_entries:
        closing_shift.append("pos_journal_entries", i)
    for i in closing_shift.payment_reconciliation:
        i.closing_amount = 1
    
    return closing_shift.name

@frappe.whitelist()
def submit_closing_shift(closing_shift):
    closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    closing_shift_doc.submit()
    return closing_shift_doc.name


def submit_printed_invoices(pos_opening_shift):
    invoices_list = frappe.get_all(
        "Sales Invoice",
        filters={
            "posa_pos_opening_shift": pos_opening_shift,
            "docstatus": 0,
            "posa_is_printed": 1,
        },
    )
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
        invoice_doc.submit()


def get_paid_amount(sales_invoice):
    data = frappe.db.sql("""
        select 
            paid_amount 
        from  
            `viewInvoice Cash Payments` 
        where 
            sales_invoice = %s;
    """, sales_invoice, as_dict=1)
    
    return data[0].paid_amount if data else 0


def build_expected_amount_ledger(pos_opening_shift):
    """
    Retorna todas las transacciones que componen el expected_amount.
    ESTA es la única fuente de verdad.
    """

    opening = frappe.get_doc("POS Opening Shift", pos_opening_shift)

    ledger = []

    # ---------------------------------------
    # 1. Opening Balance
    # ---------------------------------------
    for d in opening.balance_details:
        ledger.append({
            "type": "Opening",
            "reference": "",
            "posting_date": opening.period_start_date,
            "mode_of_payment": d.mode_of_payment,
            "amount": d.amount or 0
        })

    # ---------------------------------------
    # 2. Sales Invoices
    # ---------------------------------------
    invoices = get_pos_invoices(pos_opening_shift)

    cash_mop = frappe.get_value(
        "POS Profile",
        opening.pos_profile,
        "posa_cash_mode_of_payment"
    ) or "Cash"

    for inv in invoices:
        sinv = frappe.get_doc("Sales Invoice", inv.name)

        for p in sinv.payments:
            base_amount = p.base_amount

            if p.mode_of_payment == cash_mop:
                net = base_amount - sinv.change_amount

                # pago real
                ledger.append({
                    "type": "Invoice Payment",
                    "reference": sinv.name,
                    "posting_date": sinv.posting_date,
                    "mode_of_payment": p.mode_of_payment,
                    "amount": net
                })

                # # cambio
                # if sinv.change_amount:
                #     ledger.append({
                #         "type": "Change",
                #         "reference": sinv.name,
                #         "posting_date": sinv.posting_date,
                #         "mode_of_payment": p.mode_of_payment,
                #         "amount": -sinv.change_amount
                #     })

            else:
                ledger.append({
                    "type": "Invoice Payment",
                    "reference": sinv.name,
                    "posting_date": sinv.posting_date,
                    "mode_of_payment": p.mode_of_payment,
                    "amount": base_amount
                })

    # ---------------------------------------
    # 3. Payment Entries
    # ---------------------------------------
    payments = get_payments_entries(pos_opening_shift)

    for pe in payments:
        ledger.append({
            "type": "Payment Entry",
            "reference": pe.name,
            "posting_date": pe.posting_date,
            "mode_of_payment": pe.mode_of_payment,
            "amount": pe.paid_amount
        })

    # ---------------------------------------
    # 4. Journal Entries
    # ---------------------------------------
    jvs = get_journal_entries(pos_opening_shift)

    for jv in jvs:
        ledger.append({
            "type": "Journal Entry",
            "reference": jv.journal_entry,
            "posting_date": jv.posting_date,
            "mode_of_payment": jv.mode_of_payment,
            "amount": jv.amount
        })

    return ledger