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

frappe.ui.form.on('POS Opening Shift', {
	setup(frm) {
		if (frm.doc.docstatus == 0) {
			frm.trigger('set_posting_date_read_only');
			frm.set_value('period_start_date', frappe.datetime.now_datetime());
			frm.set_value('user', frappe.session.user);
		}
		frm.set_query("user", function(doc) {
			return {
				query: "bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.get_cashiers",
				filters: { 'parent': doc.pos_profile }
			};
		});
		frm.set_query("pos_profile", function(doc) {
			return {
				filters: { 'company': doc.company}
			};
		});
	},

	refresh(frm) {
		// set default posting date / time
		frm.trigger('set_default_pos_profile');	
		frm.trigger('add_custom_buttons');
		if(frm.doc.docstatus == 0) {
			if(!frm.doc.posting_date) {
				frm.set_value('posting_date', frappe.datetime.nowdate());
			}
			frm.trigger('set_posting_date_read_only');
		}
	},

	set_default_pos_profile(frm) {
		if (!!frm.doc.pos_profile)
			return;
		frm.call("set_default_pos_profile");
	},

	set_posting_date_read_only(frm) {
		if(frm.doc.docstatus == 0 && frm.doc.set_posting_date) {
			frm.set_df_property('posting_date', 'read_only', 0);
		} else {
			frm.set_df_property('posting_date', 'read_only', 1);
		}
	},

	set_posting_date(frm) {
		frm.trigger('set_posting_date_read_only');
	},

	pos_profile: (frm) => {
		frm.trigger("set_default_pos_profile");
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

        let found = false;
		$.map(cur_frm.doc.balance_details || [], row => {
			if (row.type === 'Cash' && !found) {
				found = true;
				const payment = row;
				frappe.model.set_value(payment.doctype, payment.name, "amount", total_paid);
			}
		});

        frm.refresh_field("balance_details");
    },
	add_custom_buttons(frm) {
		if (frm.doc.status == "Open") {
			frm.add_custom_button(__("Make Closing"), () => {
				const method = 
					"bancosecha.bancosecha.doctype.pos_closing_shift.pos_closing_shift.make_closing_shift_from_opening";
				const args = { 
					opening_shift: frm.doc 
				};
				const callback = ({ message }) => {
					frappe.new_doc("POS Closing Shift", message);
				}
				frappe.call({ method, args, callback });
			}).addClass("btn-primary");
		}
	}
});