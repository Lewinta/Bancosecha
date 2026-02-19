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

        frm.page.set_primary_action(__("Submit"), async () => {
            await frm.trigger("validate_before_submit");
        });
    },

    async validate_before_submit(frm) {
        if (frm.doc.docstatus !== 0) return;

        const allowed_types = [
            "Money Order",
            "Money Transfer",
            "Bill Payment",
            "Shipping & Delivery"
        ];

        if (!allowed_types.includes(frm.doc.custom_invoice_type)) {
            await frm.savesubmit();
            return;
        }

        const default_item = get_default_item(frm.doc.custom_invoice_type);

        await new Promise((resolve, reject) => {
            const dialog = new frappe.ui.Dialog({
                title: __("Additional Information Required"),
                size: "large",
                static: true,
                fields: [
                    {
                        fieldname: "item_code",
                        label: __("Item"),
                        fieldtype: "Link",
                        options: "Item",
                        reqd: 1,
                        default: default_item || null
                    },
                    { fieldtype: "Column Break" },
                    {
                        fieldname: "amount",
                        label: __("Amount"),
                        fieldtype: "Currency",
                        reqd: 1
                    }
                ],
                primary_action_label: __("Continue"),
                primary_action: async (values) => {
                    if (!values.item_code || !values.amount) return;

                    if (values.amount <= 0) {
                        frappe.msgprint(__("Amount must be greater than zero."));
                        return;
                    }

                    if (values.amount >= frm.doc.total) {
                        frappe.msgprint(__("Amount must be less than the invoice total."));
                        return;
                    }

                    dialog.get_primary_btn().prop("disabled", true);

                    try {
                        const r = await frappe.call({
                            method: "bancosecha.bancosecha.controllers.sales_invoice.create_po_and_submit_invoice",
                            args: {
                                invoice_name: frm.doc.name,
                                supplier: frm.doc.custom_supplier,
                                cost_center: frm.doc.cost_center,
                                item_code: values.item_code,
                                amount: values.amount
                            },
                            freeze: true,
                            freeze_message: __("Creating PO & Submitting Invoice...")
                        });

                        if (!r.message?.submitted && !r.message?.already_done) {
                            dialog.get_primary_btn().prop("disabled", false);
                            frappe.msgprint(__("Process failed."));
                            return;
                        }

                        dialog.hide();
                        await frm.reload_doc();
                        resolve();
                    } catch (e) {
                        dialog.get_primary_btn().prop("disabled", false);
                        frappe.msgprint(__("An error occurred while processing."));
                        console.error(e);
                        reject(e);
                    }
                }
            });

            dialog.set_secondary_action_label(__("Cancel"));
            dialog.set_secondary_action(() => {
                dialog.hide();
                frm.reload_doc();
                reject();
            });

            dialog.$wrapper.find(".modal").attr({
                "data-bs-keyboard": "false",
                "data-bs-backdrop": "static"
            });

            dialog.$wrapper.find(".modal-dialog").css("max-width", "800px");

            dialog.show();
        });
    },

    set_queries(frm) {
        frm.set_query("custom_supplier", () => {
            const map = {
                "Money Order": "Money Transfers",
                "Money Transfer": "Money Transfers",
                "Bill Payment": "Money Transfers",
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
                qty: 1,
                rate: 0
            });
            frm.script_manager.trigger("item_code", row.doctype, row.name);
            service_item  = frm.add_child("items", {
                item_code: "Service Charge",
                qty: 1,
                rate: 0
            });
            frm.script_manager.trigger("item_code", service_item.doctype, service_item.name);
        }

        if (!frm.doc.items?.length) {
            frm.add_child("items", {});
        }

        frm.refresh_field("items");
        frm.set_value("taxes_and_charges", sales_tax_template || null);
        frm.trigger("set_queries");
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
