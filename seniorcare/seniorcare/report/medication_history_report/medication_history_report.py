# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Resident ID", "fieldname": "parent", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Medicine", "fieldname": "medicine", "fieldtype": "Data", "width": 160},
		{"label": "Dose", "fieldname": "dose", "fieldtype": "Data", "width": 100},
		{"label": "Unit", "fieldname": "unit", "fieldtype": "Data", "width": 80},
		{"label": "Frequency", "fieldname": "frequency", "fieldtype": "Data", "width": 120},
		{"label": "Route", "fieldname": "route", "fieldtype": "Data", "width": 90},
		{"label": "Start Date", "fieldname": "start_date", "fieldtype": "Date", "width": 110},
		{"label": "End Date", "fieldname": "end_date", "fieldtype": "Date", "width": 110},
		{"label": "Prescribed By", "fieldname": "prescribed_by", "fieldtype": "Link", "options": "Doctor Provider", "width": 140},
		{"label": "Administered By", "fieldname": "administered_by", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "Discontinued Date", "fieldname": "discontinued_date", "fieldtype": "Date", "width": 120},
		{"label": "Discontinued Reason", "fieldname": "discontinued_reason", "fieldtype": "Data", "width": 180},
		{"label": "Special Instructions", "fieldname": "special_instructions", "fieldtype": "Data", "width": 180}
	]

	conditions = {"parenttype": "Resident File", "parentfield": "current_medications"}
	if filters.get("resident_file"):
		conditions["parent"] = filters.get("resident_file")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("prescribed_by"):
		conditions["prescribed_by"] = filters.get("prescribed_by")

	meds = frappe.db.get_all(
		"Resident Current Medication Item",
		filters=conditions,
		fields=[
			"parent", "status", "medicine", "dose", "unit", "frequency",
			"route", "start_date", "end_date", "prescribed_by", "administered_by",
			"discontinued_date", "discontinued_reason", "special_instructions"
		],
		order_by="parent asc, status asc, start_date desc"
	)

	for m in meds:
		m["resident_name"] = frappe.db.get_value("Resident File", m["parent"], "full_name")

	return columns, meds
