// Copyright (c) 2025, Lewin Villar and contributors
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


frappe.ui.form.on("Check Entry", {
    setup(frm) {
        frm.trigger("set_queries");
    },
    refresh(frm) {
        frm.add_custom_button("Check History", () => {
            open_check_history(frm)
        });

        if(frm.is_new() && !frm.doc.mode_of_payment){
            frm.call("add_default_mop");
        }
    },  
    set_queries(frm){
        frm.set_query("check_issuer", function() {
            return {
                query: "bancosecha.bancosecha.doctype.check_entry.check_entry.check_issuer_query"
            };
        });

        frm.set_query("customer", function() {
            return {
                query: "bancosecha.utils.customer_query"
            };
        });
    },
    fee_percentage(frm) {
        frm.trigger("calculate_fee");
    },
    calculate_fee(frm) {
        const percentage = flt(frm.doc.fee_percentage || 0);
        const amount = flt(frm.doc.amount || 0);
        const fee = flt((percentage / 100) * amount, 2);
        frm.set_value("fee", fee);
    },
    amount(frm) {
        frm.trigger("calculate_fee");
        frm.trigger("calculate_net_amount");
    },
    fee(frm){
        frm.trigger("calculate_net_amount");
    },
    calculate_net_amount(frm){
        const {amount, fee} = frm.doc;
        frm.set_value("net_amount", flt(amount - fee, 2));
        frm.set_value("difference", frm.doc.net_amount - frm.doc.paid_amount);
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
        frm.set_value("paid_amount", total_paid);
        frm.set_value("difference", frm.doc.net_amount - total_paid);
    }
});


function open_check_history(frm){

    let dialog = new frappe.ui.Dialog({
        title: "Check History",
        size: "extra-large",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "history_html"
            }
        ]
    })

    dialog.show()

    dialog.$wrapper.find(".modal-dialog").css({
        "max-width": "70%"
    })

    frappe.call({

        method: "bancosecha.bancosecha.doctype.check_entry.check_entry.get_check_history_html",

        args: {
            check_issuer: frm.doc.check_issuer,
            customer: frm.doc.customer
        },

        callback: function(r){

            dialog.fields_dict.history_html.$wrapper.html(r.message)

        }

    })

}


function render_issuer_table(data){
    let rows = ""
    data.forEach(d => {

        let badge = get_badge(d.workflow_state)

        rows += `
            <tr>
                <td>${d.posting_date}</td>
                <td>${d.customer}</td>
                <td>${format_currency(d.amount)}</td>
                <td>${badge}</td>
            </tr>
        `
    })

    $("#issuer-check-table").html(rows)
}


function render_customer_table(data){

    let rows = ""

    data.forEach(d => {

        let badge = get_badge(d.workflow_state)

        rows += `
            <tr>
                <td>${d.posting_date}</td>
                <td>${d.check_issuer}</td>
                <td>${format_currency(d.amount)}</td>
                <td>${badge}</td>
            </tr>
        `
    })

    $("#customer-check-table").html(rows)
}


function get_badge(status){

    if(status === "Cashed" || status === "Approved"){
        return `<span class="badge badge-success">${status}</span>`
    }

    return `<span class="badge badge-danger">${status}</span>`
}