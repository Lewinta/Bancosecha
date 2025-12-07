// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Check Issuer", {
    refresh(frm) {
        frm.trigger("add_custom_buttons");
    },
    add_custom_buttons(frm) {
        if (frm.doc.journal_entry) {
            frm.add_custom_button(__("View Entry"), function() {
                frappe.set_route("List", "Journal Entry", frm.doc.journal_entry);
            });
        }
    },
    full_name(frm) {
        if (frm.doc.full_name != frm.doc.full_name.toUpperCase()) {
            frm.set_value("full_name", frm.doc.full_name.toUpperCase());
        }
    }
});
