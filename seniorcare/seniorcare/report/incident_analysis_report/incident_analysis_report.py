# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = [
		{"label": "Incident ID", "fieldname": "name", "fieldtype": "Link", "options": "Incident Report", "width": 140},
		{"label": "Resident File", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 140},
		{"label": "Date & Time", "fieldname": "incident_datetime", "fieldtype": "Datetime", "width": 150},
		{"label": "Incident Type", "fieldname": "incident_type", "fieldtype": "Data", "width": 130},
		{"label": "Location", "fieldname": "location", "fieldtype": "Data", "width": 120},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Medical Attn", "fieldname": "medical_attention_required", "fieldtype": "Check", "width": 100},
		{"label": "Reported By", "fieldname": "reported_by", "fieldtype": "Link", "options": "User", "width": 130},
		{"label": "Description", "fieldname": "description", "fieldtype": "Data", "width": 200}
	]

	conditions = {}
	if filters.get("incident_type"):
		conditions["incident_type"] = filters.get("incident_type")
	if filters.get("status"):
		conditions["status"] = filters.get("status")
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")

	data = frappe.db.get_all(
		"Incident Report",
		filters=conditions,
		fields=[
			"name", "resident_file", "incident_datetime", "incident_type",
			"location", "status", "medical_attention_required", "reported_by", "description"
		],
		order_by="incident_datetime desc"
	)

	return columns, data
