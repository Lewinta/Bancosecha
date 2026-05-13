// Copyright (c) 2020, Youssef Restom and contributors
// For license information, please see license.txt


const DENOMINATIONS = {
    _10000: 10000, // $100.00
    _5000: 5000,   // $50.00
    _2000: 2000,   // $20.00
    _1000: 1000,   // $10.00
    _500: 500,     // $5.00
    _100: 100,     // $1.00
    _050: 50,      // $0.50
    _025: 25,      // $0.25
    _010: 10,      // $0.10
    _005: 5,       // $0.05
    _001: 1        // $0.01
};

frappe.ui.form.on('POS Closing Shift', {
	onload(frm) {
		frm.set_query("pos_profile", function (doc) {
			return {
				filters: { 'user': doc.user }
			};
		});

		frm.set_query("user", function (doc) {
			return {
				query: "bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.get_cashiers",
				filters: { 'parent': doc.pos_profile }
			};
		});

		frm.set_query("pos_opening_shift", function (doc) {
			return { filters: { 'status': 'Open', 'docstatus': 1 } };
		});

		if (frm.doc.docstatus === 0) frm.set_value("period_end_date", frappe.datetime.now_datetime());
		if (frm.doc.docstatus === 1) set_html_data(frm);
	},

	refresh(frm){
		if (frm.doc.docstatus === 0 && frm.doc.pos_opening_shift) {
            frm.add_custom_button(__('Reload POS Data'), () => {
                frm.trigger("reload_pos_data");
            });
        }
	},

	reload_pos_data(frm) {
        if (!frm.doc.pos_opening_shift) {
            frappe.msgprint("Selecciona un POS Opening Shift");
            return;
        }

        frm.trigger("pos_opening_shift");
    },

	pos_opening_shift (frm) {
		if (frm.doc.pos_opening_shift && frm.doc.user) {
			reset_values(frm);
			frappe.run_serially([
				() => frm.trigger("set_opening_amounts"),
				() => frm.trigger("get_pos_invoices"),
				() => frm.trigger("get_pos_payments"),
				() => frm.trigger("get_journal_entries")
			]);
		}
	},

	set_opening_amounts (frm) {
		return frappe.db.get_doc("POS Opening Shift", frm.doc.pos_opening_shift)
			.then(({ balance_details }) => {
				balance_details.forEach(detail => {
					frm.add_child("payment_reconciliation", {
						mode_of_payment: detail.mode_of_payment,
						opening_amount: detail.amount || 0,
						expected_amount: detail.amount || 0
					});
				});
			});
	},

	get_pos_invoices (frm) {
		frappe.call({
			method: 'bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.get_pos_invoices',
			args: {
				pos_opening_shift: frm.doc.pos_opening_shift,
			},
			callback: (r) => {
				let pos_docs = r.message;
				set_form_data(pos_docs, frm);
				refresh_fields(frm);
				set_html_data(frm);
			}
		});
	},

	get_pos_payments (frm) {
		frappe.call({
			method: 'bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.get_payments_entries',
			args: {
				pos_opening_shift: frm.doc.pos_opening_shift,
			},
			callback: (r) => {
				let pos_payments = r.message;
				set_form_payments_data(pos_payments, frm);
				refresh_fields(frm);
				set_html_data(frm);
			}
		});
	},
	get_journal_entries(frm) {
		frappe.call({
			method: 'bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.get_journal_entries',
			args: {
				pos_opening_shift: frm.doc.pos_opening_shift,
			},
			callback: (r) => {
				let data = r.message || [];

				data.forEach(d => {
					frm.add_child("pos_journal_entries", d);

					const payment = frm.doc.payment_reconciliation.find(
						pay => pay.mode_of_payment === d.mode_of_payment
					);

					if (payment) {
						payment.expected_amount += flt(d.amount);
					} else {
						frm.add_child("payment_reconciliation", {
							mode_of_payment: d.mode_of_payment,
							opening_amount: 0,
							expected_amount: d.amount
						});
					}
				});

				refresh_fields(frm);
			}
		});
	},
	_001(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _005(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _010(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _025(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _050(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _100(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _500(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _1000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _2000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _5000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    _10000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
	update_paid_amount_from_denominations(frm) {
        let total_cents = 0;

        Object.entries(DENOMINATIONS).forEach(([field, cents]) => {
            const qty = cint(frm.doc[field] || 0);
            total_cents += qty * cents;
        });

        const total_paid = flt(total_cents / 100);

        const row = frm.doc.payment_reconciliation[0];
		frappe.model.set_value(row.doctype, row.name, "closing_amount", total_paid);
	

        frm.refresh_field("payment_reconciliation");
    },
});

frappe.ui.form.on('POS Closing Shift Detail', {
	closing_amount: (frm, cdt, cdn) => {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "difference", flt(row.expected_amount - row.closing_amount));
	}
});

function set_form_data (data, frm) {
	data.forEach(d => {
		add_to_pos_transaction(d, frm);
		frm.doc.grand_total += flt(d.grand_total);
		frm.doc.net_total += flt(d.net_total);
		frm.doc.total_quantity += flt(d.total_qty);
		add_to_payments(d, frm);
		add_to_taxes(d, frm);
	});
}

function set_form_payments_data (data, frm) {
	data.forEach(d => {
		add_to_pos_payments(d, frm);
		add_pos_payment_to_payments(d, frm);
	});
}

function add_to_pos_transaction (d, frm) {
	frm.add_child("pos_transactions", {
		sales_invoice: d.name,
		posting_date: d.posting_date,
		grand_total: d.grand_total,
		paid_amount: d.posa_paid_amount || 0, 
		customer: d.customer
	});
}

function add_to_pos_payments (d, frm) {
	frm.add_child("pos_payments", {
		payment_entry: d.name,
		posting_date: d.posting_date,
		paid_amount: d.paid_amount,
		customer: d.party,
		mode_of_payment: d.mode_of_payment
	});
}

function add_to_payments (d, frm) {
	d.payments.forEach(p => {
		const payment = frm.doc.payment_reconciliation.find(pay => pay.mode_of_payment === p.mode_of_payment);
		if (payment) {
			let cash_mode_of_payment = get_value("POS Profile", frm.doc.pos_profile, 'posa_cash_mode_of_payment') || 'Cash';
			let amount = payment.mode_of_payment == cash_mode_of_payment
				? (p.base_amount - d.change_amount)
				: p.base_amount;
			payment.expected_amount += flt(amount);
		} else {
			frm.add_child("payment_reconciliation", {
				mode_of_payment: p.mode_of_payment,
				opening_amount: 0,
				expected_amount: p.base_amount || 0
			});
		}
	});
}

function add_pos_payment_to_payments (p, frm) {
	const payment = frm.doc.payment_reconciliation.find(pay => pay.mode_of_payment === p.mode_of_payment);
	if (payment) {
		let amount = p.paid_amount;
		payment.expected_amount += flt(amount);
	} else {
		frm.add_child("payment_reconciliation", {
			mode_of_payment: p.mode_of_payment,
			opening_amount: 0,
			expected_amount: p.paid_amount || 0
		});
	}
};


function add_to_taxes (d, frm) {
	d.taxes.forEach(t => {
		const tax = frm.doc.taxes.find(tx => tx.account_head === t.account_head && tx.rate === t.rate);
		if (tax) {
			tax.amount += flt(t.tax_amount);
		} else {
			frm.add_child("taxes", {
				account_head: t.account_head,
				rate: t.rate,
				amount: t.tax_amount
			});
		}
	});
}

function reset_values (frm) {
    frm.set_value("pos_transactions", []);
    frm.set_value("payment_reconciliation", []);
    frm.set_value("pos_payments", []);
    frm.set_value("taxes", []);
    frm.set_value("pos_journal_entries", []);
    frm.set_value("grand_total", 0);
    frm.set_value("net_total", 0);
    frm.set_value("total_quantity", 0);
}

function refresh_fields (frm) {
    frm.refresh_field("pos_transactions");
    frm.refresh_field("payment_reconciliation");
    frm.refresh_field("pos_payments");
    frm.refresh_field("taxes");
    frm.refresh_field("pos_journal_entries");
    frm.refresh_field("grand_total");
    frm.refresh_field("net_total");
    frm.refresh_field("total_quantity");
}

function set_html_data (frm) {
	frappe.call({
		method: "get_payment_reconciliation_details",
		doc: frm.doc,
		callback: (r) => {
			frm.get_field("payment_reconciliation_details").$wrapper.html(r.message);
		}
	});
}

const get_value = (doctype, name, field) => {
	let value;
	frappe.call({
		method: 'frappe.client.get_value',
		args: {
			'doctype': doctype,
			'filters': { 'name': name },
			'fieldname': field
		},
		async: false,
		callback: function (r) {
			if (!r.exc) {
				value = r.message[field];
			}
		}
	});
	return value;
};