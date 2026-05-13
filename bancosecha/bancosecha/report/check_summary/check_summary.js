// Copyright (c) 2026, Lewin Villar and contributors
// For license information, please see license.txt

frappe.query_reports["Check Summary"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1,
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center",
            get_query: function () {
                return { filters: { is_group: 0 } };
            },
        },
        {
            fieldname: "check_issuer",
            label: __("Check Issuer"),
            fieldtype: "Link",
            options: "Check Issuer",
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
            get_query: function () {
                return { filters: { disabled: 0 } };
            },
        },
        {
            fieldname: "group_by",
            label: __("Group By"),
            fieldtype: "Select",
            options: "\nCost Center\nCheck Issuer\nCustomer\nOwner",
            default: "",
        },
    ],
};
