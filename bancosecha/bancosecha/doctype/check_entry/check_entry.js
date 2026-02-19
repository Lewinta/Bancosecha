// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Check Entry", {
    refresh(frm) {
    },
    amount(frm) {
        frm.trigger("calculate_net_amount");
    },
    fee(frm){
        frm.trigger("calculate_net_amount");
    },
    calculate_net_amount(frm){
        const {amount, fee} = frm.doc;
        frm.set_value("net_amount", flt(amount) - flt(fee));
    }
});