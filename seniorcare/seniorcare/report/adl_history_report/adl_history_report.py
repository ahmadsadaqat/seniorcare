# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Assessment ID", "fieldname": "name", "fieldtype": "Link", "options": "ADL Assessment", "width": 140},
		{"label": "Date", "fieldname": "assessment_date", "fieldtype": "Date", "width": 110},
		{"label": "Resident ID", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "Total Score (0-6)", "fieldname": "total_adl_score", "fieldtype": "Int", "width": 120},
		{"label": "Bathing", "fieldname": "bathing", "fieldtype": "Data", "width": 110},
		{"label": "Dressing", "fieldname": "dressing", "fieldtype": "Data", "width": 110},
		{"label": "Toileting", "fieldname": "toileting", "fieldtype": "Data", "width": 110},
		{"label": "Transferring", "fieldname": "transferring", "fieldtype": "Data", "width": 110},
		{"label": "Continence", "fieldname": "continence_adl", "fieldtype": "Data", "width": 110},
		{"label": "Feeding", "fieldname": "feeding", "fieldtype": "Data", "width": 110},
		{"label": "Assessed By", "fieldname": "assessed_by", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "IADL Notes", "fieldname": "iadl_notes", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")
	if filters.get("from_date"):
		conditions["assessment_date"] = [">=", filters.get("from_date")]
	if filters.get("to_date"):
		if "assessment_date" in conditions:
			conditions["assessment_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		else:
			conditions["assessment_date"] = ["<=", filters.get("to_date")]

	data = frappe.db.get_all(
		"ADL Assessment",
		filters=conditions,
		fields=[
			"name", "assessment_date", "resident_file", "resident_name", "total_adl_score",
			"bathing", "dressing", "toileting", "transferring", "continence_adl", "feeding",
			"assessed_by", "iadl_notes"
		],
		order_by="assessment_date desc, creation desc"
	)

	return columns, data
