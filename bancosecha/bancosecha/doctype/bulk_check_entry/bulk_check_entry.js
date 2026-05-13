// Copyright (c) 2025, Lewin Villar and contributors
// For license information, please see license.txt

const DENOMINATIONS = {
    _10000: 10000,
    _5000: 5000,
    _2000: 2000,
    _1000: 1000,
    _500: 500,
    _100: 100,
    _050: 50,
    _025: 25,
    _010: 10,
    _005: 5,
    _001: 1
};

frappe.ui.form.on("Bulk Check Entry", {
    setup(frm) {
        frm.set_query("check_issuer", () => ({
            query: "bancosecha.bancosecha.doctype.check_entry.check_entry.check_issuer_query"
        }));
        frm.set_query("customer", () => ({
            query: "bancosecha.utils.customer_query"
        }));

        frm.set_query("check_issuer", "checks", () => ({
        query: "bancosecha.bancosecha.doctype.check_entry.check_entry.check_issuer_query"
        }));
        frm.set_query("customer", "checks", () => ({
            query: "bancosecha.utils.customer_query"
        }));
    },

    refresh(frm) {
        apply_child_readonly(frm);
        frm.trigger("fetch_accounts");
    },

    check_issuer(frm) {
        propagate_to_rows(frm, "check_issuer", frm.doc.check_issuer);
        apply_child_readonly(frm);
    },
    
    customer(frm) {
        propagate_to_rows(frm, "customer", frm.doc.customer);
        apply_child_readonly(frm);
    },
    
    fee_percentage(frm) {
        propagate_fee_to_rows(frm);
        apply_child_readonly(frm);
    },

    fetch_accounts(frm) {
        if (!!frm.is_new())
            frm.call("fetch_accounts").then( () => frm.reload_doc() );
    },

    _001(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _005(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _010(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _025(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _050(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _100(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _500(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _1000(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _2000(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _5000(frm) { frm.trigger("update_paid_amount_from_denominations"); },
    _10000(frm) { frm.trigger("update_paid_amount_from_denominations"); },

    update_paid_amount_from_denominations(frm) {
        let total_cents = 0;
        Object.entries(DENOMINATIONS).forEach(([field, cents]) => {
            total_cents += cint(frm.doc[field] || 0) * cents;
        });
        const paid = flt(total_cents / 100);
        frm.set_value("paid_amount", paid);
        frm.set_value("difference_amount", flt(frm.doc.net_total - paid, 2));
    }
});


frappe.ui.form.on("Bulk Check Item", {
    checks_add(frm, cdt, cdn) {
        if (frm.doc.check_issuer)  frappe.model.set_value(cdt, cdn, "check_issuer",  frm.doc.check_issuer);
        if (frm.doc.customer)      frappe.model.set_value(cdt, cdn, "customer",      frm.doc.customer);
        if (frm.doc.fee_percentage) frappe.model.set_value(cdt, cdn, "fee_percentage", frm.doc.fee_percentage);
        apply_child_readonly(frm);
    },

    check_amount(frm, cdt, cdn) {
        recalculate_row(frm, cdt, cdn);
        refresh_totals(frm);
    },
    fee_percentage(frm, cdt, cdn) {
        recalculate_row(frm, cdt, cdn);
        refresh_totals(frm);
    },
    checks_remove(frm) {
        refresh_totals(frm);
    }
});


function recalculate_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    const base = flt(row.check_amount);
    const fee  = flt((flt(row.fee_percentage) / 100) * base, 2);
    frappe.model.set_value(cdt, cdn, "fee", fee);
    frappe.model.set_value(cdt, cdn, "net_amount", flt(base - fee, 2));
}

function refresh_totals(frm) {
    let total_check = 0, total_fee = 0;
    (frm.doc.checks || []).forEach(row => {
        total_check += flt(row.check_amount);
        total_fee   += flt(row.fee);
    });
    const net_total = flt(total_check - total_fee, 2);
    frm.set_value("total_check", total_check);
    frm.set_value("total_fee", total_fee);
    frm.set_value("net_total", net_total);
    frm.set_value("difference_amount", flt(net_total - flt(frm.doc.paid_amount), 2));
}

function propagate_to_rows(frm, fieldname, value) {
    (frm.doc.checks || []).forEach(row => {
        frappe.model.set_value(row.doctype, row.name, fieldname, value);
    });
    frm.refresh_field("checks");
}

function propagate_fee_to_rows(frm) {
    const pct = flt(frm.doc.fee_percentage);
    (frm.doc.checks || []).forEach(row => {
        const base = flt(row.check_amount);
        const fee  = flt((pct / 100) * base, 2);
        frappe.model.set_value(row.doctype, row.name, "fee_percentage", pct);
        frappe.model.set_value(row.doctype, row.name, "fee", fee);
        frappe.model.set_value(row.doctype, row.name, "net_amount", flt(base - fee, 2));
    });
    frm.refresh_field("checks");
    refresh_totals(frm);
}

/**
 * Lock child fields whose value is driven by the parent header.
 * Uses docfield mutation so it applies to both inline cells and the expanded row form.
 */
function apply_child_readonly(frm) {
    return; // Not needed anymore as per current requirements, but keeping the function in case we want to re-enable it in the future.
    const locks = {
        check_issuer:   !!frm.doc.check_issuer,
        customer:       !!frm.doc.customer,
        fee_percentage: flt(frm.doc.fee_percentage) > 0
    };

    const grid = frm.fields_dict.checks && frm.fields_dict.checks.grid;
    if (!grid) return;

    // Apply to the grid's shared docfield definitions (affects all future rows too)
    grid.docfields.forEach(df => {
        if (df.fieldname in locks) df.read_only = locks[df.fieldname] ? 1 : 0;
    });

    // Apply to already-rendered rows
    (frm.doc.checks || []).forEach(row => {
        const grid_row = grid.get_row(row.name);
        if (!grid_row) return;

        Object.entries(locks).forEach(([fieldname, is_locked]) => {
            // Inline column cell
            if (grid_row.columns[fieldname]) {
                grid_row.columns[fieldname].df.read_only = is_locked ? 1 : 0;
                grid_row.columns[fieldname].refresh();
            }
            // Expanded row form field
            if (grid_row.open_form_button && grid_row.form_area) {
                const field = grid_row.grid_form && grid_row.grid_form.fields_dict[fieldname];
                if (field) {
                    field.df.read_only = is_locked ? 1 : 0;
                    field.refresh();
                }
            }
        });
    });

    frm.refresh_field("checks");
}