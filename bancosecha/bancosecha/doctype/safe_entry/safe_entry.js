// Copyright (c) 2026, Lewin Villar and contributors
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


frappe.ui.form.on("Safe Entry", {
	refresh(frm) {
        frm.trigger("set_dfs");
        
        if(frm.is_new() && !frm.doc.cash_account){
            frm.call("add_default_cash_account");
        }
	},
    set_dfs(frm){
        let fields = [
            "posting_date",
            "posting_time",
        ]
        $.map(fields, function(field) {
            frm.set_df_property(field, "read_only", !!frm.doc.set_posting_time ? 0 : 1);
        });
    },
    set_posting_time(frm){
        frm.trigger("set_dfs");
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
        frm.set_value("total_amount", total_paid);
    }
});
