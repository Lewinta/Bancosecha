// Copyright (c) 2026, Lewin Villar and contributors
// For license information, please see license.txt

frappe.query_reports["Cash Audit"] = {
    onload: function (report) {
        const method = "bancosecha.bancosecha.report.cash_audit.cash_audit.get_default_cash_accounts";
        frappe.call({
            method: method,
            callback: function (r) {
                if (r.message) {
                    report.set_filter_value("account", r.message);
                }
            }
        });
    },
    filters: [
        {
            fieldname: "account",
            label: "Account",
            fieldtype: "MultiSelectList",
            options: "Account",
            reqd: 1,
            get_data: function(txt) {
                if (!txt) {
                    return frappe.db.get_link_options("Account", "", {
                        parent_account: ['in',['MCNAUGHTEN Cashiers - B', 'HALL Cashiers - B']],
                        is_group: 0
                    });
                }

                return frappe.db.get_link_options("Account", txt, {
                    parent_account: ['in',['MCNAUGHTEN Cashiers - B', 'HALL Cashiers - B']],
                    is_group: 0
                });
            }
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
			default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
			default: frappe.datetime.get_today(),
            reqd: 1

        },
		{
			fieldname: "type",
			label: "Type",
			fieldtype: "Select",
			options: "\nSafe Entry\nCheck Entry\nSales Invoice\nOther",
		},
        {
            fieldname: "supplier",
            label: "Supplier",
            fieldtype: "Link",
            options: "Supplier",
            depends_on: "eval:doc.type === 'Sales Invoice'"
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        if (column.fieldname === "custom_invoice_type" && data) {

            const colors = {

                "Money Order": { bg: "#ede7f6", color: "#4527a0" },
                "Money Transfer": { bg: "#e3f2fd", color: "#0d47a1" },
                "Bill Payment": { bg: "#fff8e1", color: "#f57f17" },
                "Shipping & Delivery": { bg: "#e0f7fa", color: "#006064" },
                "Shipping Box": { bg: "#f3e5f5", color: "#6a1b9a" },
                "Business Services": { bg: "#e8f5e9", color: "#1b5e20" },
                "Phone Replenishment": { bg: "#fff3e0", color: "#e65100" },

                "Check Entry": { bg: "#e1f5fe", color: "#01579b" },
                "Safe Entry": { bg: "#fce4ec", color: "#880e4f" }
            };

            const style = colors[data.custom_invoice_type] || {
                bg: "#f5f5f5",
                color: "#424242"
            };
			const pill = `
				<span
                    style="
                        background:${style.bg};
                        color:${style.color};
                        padding:2px 8px;
                        border-radius:10px;
                        font-size:12px;
                        font-weight:500;
                        display:inline-block;
                        white-space:nowrap;
                    "
                >`
            value = `
				${data.custom_invoice_type? pill : "<span>"}
                    ${data.custom_invoice_type || ""	}
                </span>
            `;
        }

        return value;
    }
};