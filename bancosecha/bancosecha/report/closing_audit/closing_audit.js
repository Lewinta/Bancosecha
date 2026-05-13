// Copyright (c) 2026, Lewin Villar and contributors
// For license information, please see license.txt

frappe.query_reports["Closing Audit"] = {
    filters: [
        {
            fieldname: "pos_closing_shift",
            label: __("POS Closing Shift"),
            fieldtype: "Link",
            options: "POS Closing Shift",
            reqd: 1
        }
    ]
};
