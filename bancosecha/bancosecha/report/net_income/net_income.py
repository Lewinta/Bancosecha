# Copyright (c) 2026, Lewin Villar and contributors
# For license information, please see license.txt

import frappe
from frappe import qb
from frappe.query_builder import Criterion

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return [
		{
			"fieldname": "description",
			"label": "Description",
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "net_income",
			"label": "Net Income",
			"fieldtype": "Currency",
			"width": 150
		}
	]

def get_data(filters):
	return frappe.db.sql("""
		SELECT 
			'Notary Services' as description,
			SUM(si.amount) as net_income
		FROM 
			`tabSales Invoice Item` si
		JOIN
			`tabSales Invoice` s 
		ON 
			si.parent = s.name
		WHERE 
			si.item_code = 'Notary Services'
		AND
			si.docstatus = 1
		AND
			s.posting_date BETWEEN %(from_date)s AND %(to_date)s

		UNION 
		
		SELECT
			'Bill Payment' as description,
			SUM(si.amount) as net_income
		FROM
			`tabSales Invoice Item` si
		JOIN
			`tabSales Invoice` s 
		ON
			si.parent = s.name
		WHERE
			s.custom_invoice_type = 'Bill Payment'
		AND
			si.docstatus = 1
		AND
			si.item_code = 'Service Charge'
		AND
			s.posting_date BETWEEN %(from_date)s AND %(to_date)s

		UNION 
		
		SELECT
			'Money Order' as description,
			SUM(si.amount) as net_income
		FROM
			`tabSales Invoice Item` si
		JOIN
			`tabSales Invoice` s 
		ON
			si.parent = s.name
		WHERE
			s.custom_invoice_type = 'Money Order'
		AND
			si.docstatus = 1
		AND
			si.item_code = 'Service Charge'
		AND
			s.posting_date BETWEEN %(from_date)s AND %(to_date)s
		
		UNION 
		
		SELECT
			'Money Transfer' as description,
			SUM(si.amount) as net_income
		FROM
			`tabSales Invoice Item` si
		JOIN
			`tabSales Invoice` s 
		ON
			si.parent = s.name
		WHERE
			s.custom_invoice_type = 'Money Transfer'
		AND
			si.docstatus = 1
		AND
			si.item_code = 'Service Charge'
		AND
			s.posting_date BETWEEN %(from_date)s AND %(to_date)s
		
		UNION 
		
		SELECT
			'Check Entry' as description,
			SUM(ce.fee) as net_income
		FROM
			`tabCheck Entry` ce
		WHERE
			ce.workflow_state IN ('Cashed', 'Cleared')	
		AND
			ce.docstatus = 1
		AND
			ce.posting_date BETWEEN %(from_date)s AND %(to_date)s
	""", {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date")
	}, as_dict=True, debug=True)
