# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Contract ID", "fieldname": "name", "fieldtype": "Link", "options": "Resident Contract", "width": 140},
		{"label": "Resident File", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 140},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 140},
		{"label": "Contract Type", "fieldname": "contract_type", "fieldtype": "Data", "width": 130},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 110},
		{"label": "End Date", "fieldname": "end_date", "fieldtype": "Date", "width": 110},
		{"label": "Occupancy Fee", "fieldname": "occupancy_fee", "fieldtype": "Currency", "width": 120},
		{"label": "Attendant Fee", "fieldname": "attendant_fee", "fieldtype": "Currency", "width": 120},
		{"label": "Other Charges", "fieldname": "other_fixed_charges", "fieldtype": "Currency", "width": 120},
		{"label": "Total Monthly Fee", "fieldname": "total_monthly_fee", "fieldtype": "Currency", "width": 130},
		{"label": "Security Deposit", "fieldname": "refundable_deposit", "fieldtype": "Currency", "width": 130}
	]

	conditions = {"docstatus": 1}
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("contract_type"):
		conditions["contract_type"] = filters.get("contract_type")
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")

	data = frappe.db.get_all(
		"Resident Contract",
		filters=conditions,
		fields=[
			"name", "resident_file", "customer", "contract_type", "status",
			"start_date", "end_date", "occupancy_fee", "attendant_fee",
			"other_fixed_charges", "total_monthly_fee", "refundable_deposit"
		],
		order_by="start_date desc"
	)

	return columns, data
