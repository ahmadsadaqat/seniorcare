# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Advance ID", "fieldname": "name", "fieldtype": "Link", "options": "Resident Advance", "width": 140},
		{"label": "Resident File", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 140},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
		{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": "Advance Type", "fieldname": "advance_type", "fieldtype": "Data", "width": 130},
		{"label": "Advance Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 130},
		{"label": "Utilized Amount", "fieldname": "utilized_amount", "fieldtype": "Currency", "width": 130},
		{"label": "Remaining Balance", "fieldname": "remaining_balance", "fieldtype": "Currency", "width": 140},
		{"label": "Approval Status", "fieldname": "approval_status", "fieldtype": "Data", "width": 110},
		{"label": "Purpose", "fieldname": "purpose", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("advance_type"):
		conditions["advance_type"] = filters.get("advance_type")
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")

	data = frappe.db.get_all(
		"Resident Advance",
		filters=conditions,
		fields=[
			"name", "resident_file", "customer", "posting_date", "advance_type",
			"amount", "utilized_amount", "remaining_balance", "approval_status", "purpose"
		],
		order_by="posting_date desc"
	)

	return columns, data
