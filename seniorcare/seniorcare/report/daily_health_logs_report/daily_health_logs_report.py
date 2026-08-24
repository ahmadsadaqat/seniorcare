# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Log ID", "fieldname": "name", "fieldtype": "Link", "options": "Daily Health Log", "width": 130},
		{"label": "Log Date", "fieldname": "log_date", "fieldtype": "Date", "width": 110},
		{"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 90},
		{"label": "Resident ID", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "General Condition", "fieldname": "general_condition", "fieldtype": "Data", "width": 130},
		{"label": "Meals Taken", "fieldname": "meals_taken", "fieldtype": "Data", "width": 100},
		{"label": "Sleep Quality", "fieldname": "sleep_quality", "fieldtype": "Data", "width": 100},
		{"label": "Pain Present?", "fieldname": "pain_present", "fieldtype": "Data", "width": 100},
		{"label": "Pain Scale", "fieldname": "pain_scale", "fieldtype": "Int", "width": 80},
		{"label": "Pain Location", "fieldname": "pain_location", "fieldtype": "Data", "width": 120},
		{"label": "Flags / Concerns", "fieldname": "flags_concerns", "fieldtype": "Data", "width": 110},
		{"label": "Flags Description", "fieldname": "flags_description", "fieldtype": "Data", "width": 160},
		{"label": "Mood / Behavior", "fieldname": "mood_behavior", "fieldtype": "Data", "width": 160},
		{"label": "Recorded By", "fieldname": "recorded_by", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")
	if filters.get("shift"):
		conditions["shift"] = filters.get("shift")
	if filters.get("general_condition"):
		conditions["general_condition"] = filters.get("general_condition")
	if filters.get("from_date"):
		conditions["log_date"] = [">=", filters.get("from_date")]
	if filters.get("to_date"):
		if "log_date" in conditions:
			conditions["log_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		else:
			conditions["log_date"] = ["<=", filters.get("to_date")]

	logs = frappe.db.get_all(
		"Daily Health Log",
		filters=conditions,
		fields=[
			"name", "log_date", "shift", "resident_file", "general_condition",
			"meals_taken", "sleep_quality", "pain_present", "pain_scale",
			"pain_location", "flags_concerns", "flags_description", "mood_behavior",
			"recorded_by", "notes"
		],
		order_by="log_date desc, creation desc"
	)

	for log in logs:
		log["resident_name"] = frappe.db.get_value("Resident File", log["resident_file"], "full_name")

	return columns, logs
