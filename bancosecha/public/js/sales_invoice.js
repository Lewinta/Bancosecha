frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        frm.trigger("set_queries");
        console.log("loaded")

        // attach once to avoid duplicates
        if (!frm.__po_dialog_attached) {
            frm.__po_dialog_attached = true;

            frm.page.set_primary_action(__('Submit'), async () => {
                await frm.trigger("validate_before_submit");
            });
        }
    },
    before_submit(frm){
        frappe.throw("Can't submit")
    }

    async validate_before_submit(frm) { 
        if (frm.doc.docstatus !== 0) return;

        const data = await new Promise(resolve => {
            let dialog = new frappe.ui.Dialog({
                title: __("Additional Information Required"),
                size: "large", 
                fields: [
                    {
                        fieldname: "item_code",
                        label: __("Item"),
                        fieldtype: "Link",
                        options: "Item",
                        reqd: 1
                    },
                    {
                        fieldtype: "Column Break"
                    },
                    {
                        fieldname: "amount",
                        label: __("Amount"),
                        fieldtype: "Currency",
                        reqd: 1
                    }
                ],
                primary_action_label: __("Continue"),
                primary_action: (values) => {
                    if (!values.item_code || !values.month) {
                        frappe.msgprint(__("You must complete all required fields."));
                        return;
                    }
                    dialog.hide();
                    resolve(values);
                }
            });

            dialog.$wrapper.find(".modal-dialog").css("max-width", "800px");
            dialog.show();
        });

        // Make server call to create PO
        try {
            let result = await frappe.call({
                method: "your_app.your_module.sales_invoice_flow.create_purchase_order_before_submit",
                args: {
                    invoice_name: frm.doc.name,
                    item_code: data.item_code,
                    amount: data.amount
                }
            });

            if (result.message && result.message.po_name) {
                await frm.set_value("custom_po_reference", result.message.po_name);
            }
        } catch (e) {
            console.error(e);
            frappe.throw(__("Purchase Order could not be created. Invoice not submitted."));
            return;
        }

        await frm.save_submit();
    },

    set_queries(frm) {
        frm.set_query("custom_supplier", () => {
            const map = {
                "Money Order": "Money Transfers",
                "Money Transfer": "Money Transfers",
                "Bill Payment": "Money Transfers",
                "Shipping & Delivery": "Shipping Services"
            };

            const supplier_group = map[frm.doc.custom_invoice_type];

            return supplier_group
                ? { filters: { supplier_group } }
                : {};
        });
    },

    custom_invoice_type(frm) {
        if (!frm.doc.custom_invoice_type || !frappe.boot.bancosecha || !frappe.boot.bancosecha.defaults) return;

        const defaults = frappe.boot.bancosecha.defaults;

        if (defaults[frm.doc.custom_invoice_type]) {
            if (defaults[frm.doc.custom_invoice_type].default_supplier)
                frm.set_value("custom_supplier", defaults[frm.doc.custom_invoice_type].default_supplier);
            else frm.set_value("custom_supplier", null);

            if (defaults[frm.doc.custom_invoice_type].default_item) {
                frm.clear_table("items");
                let row = frm.add_child("items", {
                    item_code: defaults[frm.doc.custom_invoice_type].default_item,
                    qty: 1,
                    rate: 0
                });
                frm.refresh_field("items");
                frm.script_manager.trigger("item_code", row.doctype, row.name);
            }
        } else {
            frm.set_value("custom_supplier", null);
        }

        frm.trigger("set_queries");
    }
});
