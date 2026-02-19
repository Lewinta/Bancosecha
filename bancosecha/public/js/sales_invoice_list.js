// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings["Sales Invoice"] = {
	add_fields: [
		"customer",
		"customer_name",
		"base_grand_total",
		"outstanding_amount",
		"due_date",
		"company",
		"currency",
		"is_return",
	],
	get_indicator: function (doc) {
		const status_colors = {
			Draft: "red",
			Unpaid: "orange",
			Paid: "green",
			Return: "gray",
			"Credit Note Issued": "gray",
			"Unpaid and Discounted": "orange",
			"Partly Paid and Discounted": "yellow",
			"Overdue and Discounted": "red",
			Overdue: "red",
			"Partly Paid": "yellow",
			"Internal Transfer": "darkgrey",
		};
		return [__(doc.status), status_colors[doc.status], "status,=," + doc.status];
	},
	right_column: "grand_total",

	onload: function (listview) {
		if (frappe.model.can_create("Delivery Note")) {
			listview.page.add_action_item(__("Delivery Note"), () => {
				erpnext.bulk_transaction_processing.create(listview, "Sales Invoice", "Delivery Note");
			});
		}

		if (frappe.model.can_create("Payment Entry")) {
			listview.page.add_action_item(__("Payment"), () => {
				erpnext.bulk_transaction_processing.create(listview, "Sales Invoice", "Payment Entry");
			});
		}
	},

   formatters: {
        custom_invoice_type(value, df, doc) {
            if (!value) return value;

            const colors = {
                "Money Order": {
                    bg: "#ede7f6",
                    color: "#4527a0"
                },
                "Money Transfer": {
                    bg: "#e3f2fd",
                    color: "#0d47a1"
                },
                "Bill Payment": {
                    bg: "#fff8e1",
                    color: "#f57f17"
                },
                "Shipping & Delivery": {
                    bg: "#e0f7fa",
                    color: "#006064"
                },
                "Shipping Box": {
                    bg: "#f3e5f5",
                    color: "#6a1b9a"
                },
                "Business Services": {
                    bg: "#e8f5e9",
                    color: "#1b5e20"
                }
            };

            const style = colors[value] || {
                bg: "#f5f5f5",
                color: "#424242"
            };

            return `
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
                    title="${value}"
                >
                    ${value}
                </span>
            `;
        }
    }
};
