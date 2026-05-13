const DENOMINATIONS = {
    custom__10000: 10000, // $100.00
    custom__5000: 5000,   // $50.00
    custom__2000: 2000,   // $20.00
    custom__1000: 1000,   // $10.00
    custom__500: 500,     // $5.00
    custom__100: 100,     // $1.00
    custom__050: 50,      // $0.50
    custom__025: 25,      // $0.25
    custom__010: 10,      // $0.10
    custom__005: 5,       // $0.05
    custom__001: 1        // $0.01
};

frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        frm.trigger("set_queries");
        setTimeout(() => {
            frm.trigger("set_default_shift");
        }, 3000);
    },

    set_queries(frm) {
        frm.set_query("custom_supplier", () => {
            const map = {
                "Money Order": "Money Transfers",
                "Money Transfer": "Money Transfers",
                "Bill Payment": "Money Transfers",
                "Phone Replenishment": "Phone Replenishment",
                "Shipping & Delivery": "Shipping Services",
                "Business Services": "Business Services"
            };

            const supplier_group = map[frm.doc.custom_invoice_type];
            return supplier_group ? { filters: { supplier_group } } : {};
        });
    },

    set_default_shift(frm){
        if(!!frm.doc.pos_opening_shift)
            return;
        const method = "bancosecha.bancosecha.controllers.sales_invoice.get_open_pos_shift";
        const {company, pos_profile, posting_date} = frm.doc;
        const args = { company, pos_profile, posting_date };
        if (!company || !pos_profile || !posting_date)
            return;
        frappe.call(method, args).then(r => {
            if(r.message){
                frm.set_value("posa_pos_opening_shift", r.message);
            }
        });
    },

    custom_invoice_type(frm) {
        const supplier = get_default_supplier(frm.doc.custom_invoice_type);
        const item_code = get_default_item(frm.doc.custom_invoice_type);
        const sales_tax_template = get_default_sales_tax_template(frm.doc.custom_invoice_type);

        frm.set_value("custom_supplier", supplier || null);
        frm.clear_table("items");

        if (item_code) {
            const row = frm.add_child("items", {
                item_code,
                qty: frm.doc.is_return ? -1 : 1,
                rate: 0
            });
            frm.script_manager.trigger("item_code", row.doctype, row.name);
            if (frm.doc.custom_invoice_type != "Phone Replenishment") {
                const service_item  = frm.add_child("items", {
                    item_code: "Service Charge",
                    qty: frm.doc.is_return ? -1 : 1,
                    rate: 0
                });
                frm.script_manager.trigger("item_code", service_item.doctype, service_item.name);
            }
        }

        if (!frm.doc.items?.length) {
            frm.add_child("items", {});
        }

        frm.refresh_field("items");
        frm.set_value("taxes_and_charges", sales_tax_template || null);
        frm.trigger("set_queries");
        frm.trigger("is_return");
    },
    is_return(frm) {
        if(!!frm.doc.is_return){
            frm.set_value("taxes_and_charges", "");
            frm.clear_table("taxes");
        }

        $.map(frm.doc.items || [], (item) => {
            frappe.model.set_value(item.doctype, item.name, "qty", frm.doc.is_return ? -Math.abs(item.qty) : Math.abs(item.qty));
        });
    },
    custom__001(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__005(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__010(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__025(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__050(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__100(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__500(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__1000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__2000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__5000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    custom__10000(frm) {
        frm.trigger("update_paid_amount_from_denominations");
    },
    update_paid_amount_from_denominations(frm) {
        let total_cents = 0;

        Object.entries(DENOMINATIONS).forEach(([field, cents]) => {
            const qty = cint(frm.doc[field] || 0);
            total_cents += qty * cents;
        });

        const total_paid = flt(total_cents / 100);

        // Ensure payments row #1 exists
        if (!frm.doc.payments || !frm.doc.payments.length) {
            frm.add_child("payments", {});
        }

        const payment = frm.doc.payments[0];

        // payment.amount = total_paid;
        // payment.base_amount = total_paid;
        frappe.model.set_value(payment.doctype, payment.name, "amount", total_paid);
        frappe.model.set_value(payment.doctype, payment.name, "base_amount", total_paid);

        frm.refresh_field("payments");
    }
});

frappe.ui.form.on("Sales Invoice Item", {
    rate(frm, cdt, cdn) {
        setTimeout(() => {
            frm.trigger("update_paid_amount_from_denominations");
        }, 300);
    },
    qty(frm, cdt, cdn) {
        setTimeout(() => {
            frm.trigger("update_paid_amount_from_denominations");
        }, 300);
    },
    items_remove(frm) {
        setTimeout(() => {
            frm.trigger("update_paid_amount_from_denominations");
        }, 300);
    }
})

function get_default_item(invoice_type) {
    const defaults = frappe.boot.bancosecha?.defaults || {};
    return defaults[invoice_type]?.default_item || null;
}

function get_default_supplier(invoice_type) {
    const defaults = frappe.boot.bancosecha?.defaults || {};
    return defaults[invoice_type]?.default_supplier || null;
}

function get_default_sales_tax_template(invoice_type) {
    const defaults = frappe.boot.bancosecha?.defaults || {};
    return defaults[invoice_type]?.default_sales_tax_template || null;
}
