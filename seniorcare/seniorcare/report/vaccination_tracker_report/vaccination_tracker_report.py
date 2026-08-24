# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Log ID", "fieldname": "name", "fieldtype": "Link", "options": "Vaccination Log", "width": 130},
		{"label": "Resident ID", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "Vaccine Name", "fieldname": "vaccine_name", "fieldtype": "Data", "width": 140},
		{"label": "Manual / Other Name", "fieldname": "vaccine_name_other", "fieldtype": "Data", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Dose / Booster", "fieldname": "dose_booster_number", "fieldtype": "Data", "width": 110},
		{"label": "Date Administered", "fieldname": "date_administered", "fieldtype": "Date", "width": 120},
		{"label": "Administered By", "fieldname": "administered_by", "fieldtype": "Data", "width": 150},
		{"label": "Next Due Date", "fieldname": "next_due_date", "fieldtype": "Date", "width": 120},
		{"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")
	if filters.get("vaccine_name"):
		conditions["vaccine_name"] = filters.get("vaccine_name")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("from_due_date"):
		conditions["next_due_date"] = [">=", filters.get("from_due_date")]
	if filters.get("to_due_date"):
		if "next_due_date" in conditions:
			conditions["next_due_date"] = ["between", [filters.get("from_due_date"), filters.get("to_due_date")]]
		else:
			conditions["next_due_date"] = ["<=", filters.get("to_due_date")]

	logs = frappe.db.get_all(
		"Vaccination Log",
		filters=conditions,
		fields=[
			"name", "resident_file", "vaccine_name", "vaccine_name_other", "status",
			"dose_booster_number", "date_administered", "administered_by", "next_due_date", "notes"
		],
		order_by="next_due_date asc, date_administered desc"
	)

	for log in logs:
		log["resident_name"] = frappe.db.get_value("Resident File", log["resident_file"], "full_name")

	return columns, logs
