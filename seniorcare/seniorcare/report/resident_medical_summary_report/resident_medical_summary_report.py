# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Resident ID", "fieldname": "name", "fieldtype": "Link", "options": "Resident File", "width": 140},
		{"label": "Full Name", "fieldname": "full_name", "fieldtype": "Data", "width": 160},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Room / Unit", "fieldname": "room_unit", "fieldtype": "Data", "width": 110},
		{"label": "Primary Doctor", "fieldname": "primary_doctor", "fieldtype": "Link", "options": "Doctor Provider", "width": 140},
		{"label": "Next Appt Date", "fieldname": "next_appointment_date", "fieldtype": "Date", "width": 120},
		{"label": "Allergies Summary", "fieldname": "allergies_summary", "fieldtype": "Data", "width": 180},
		{"label": "Current Medications", "fieldname": "current_medication_summary", "fieldtype": "Data", "width": 220},
		{"label": "Medical History Summary", "fieldname": "medical_history_summary", "fieldtype": "Data", "width": 220}
	]

	conditions = {}
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("primary_doctor"):
		conditions["primary_doctor"] = filters.get("primary_doctor")
	if filters.get("resident_file"):
		conditions["name"] = filters.get("resident_file")

	data = frappe.db.get_all(
		"Resident File",
		filters=conditions,
		fields=[
			"name", "full_name", "status", "room_unit", "primary_doctor",
			"next_appointment_date", "allergies_summary", "current_medication_summary",
			"medical_history_summary"
		],
		order_by="full_name ascii"
	)

	return columns, data
