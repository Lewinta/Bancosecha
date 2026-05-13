frappe.ui.form.on("Payment Entry", {
    refresh(frm) {
        setTimeout(() => {
            frm.trigger("set_default_shift");
        }, 3000);
    },
    set_default_shift(frm){
        if(!!frm.doc.pos_opening_shift)
            return;
        const method = "bancosecha.bancosecha.controllers.payment_entry.get_open_pos_shift";
        const {company, posting_date} = frm.doc;
        const user = frappe.session.user;
        const args = { company, user, posting_date };
        if (!company || !user || !posting_date)
            return;
        frappe.call(method, args).then(r => {
            if(r.message){
                frm.set_value("custom_posa_pos_opening_shift", r.message);
            }
        });
    },
});