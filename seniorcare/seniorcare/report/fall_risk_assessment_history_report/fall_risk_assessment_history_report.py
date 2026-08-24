# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Assessment ID", "fieldname": "name", "fieldtype": "Link", "options": "Fall Risk Assessment", "width": 130},
		{"label": "Date", "fieldname": "assessment_date", "fieldtype": "Date", "width": 110},
		{"label": "Resident ID", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "Morse Score", "fieldname": "calculated_score", "fieldtype": "Int", "width": 100},
		{"label": "Risk Level", "fieldname": "risk_level", "fieldtype": "Data", "width": 110},
		{"label": "Fall History (3m)", "fieldname": "history_of_falls", "fieldtype": "Check", "width": 110},
		{"label": "Fall Count", "fieldname": "fall_count_3months", "fieldtype": "Int", "width": 90},
		{"label": "Secondary Diag", "fieldname": "secondary_diagnosis", "fieldtype": "Check", "width": 110},
		{"label": "Mobility Aid", "fieldname": "mobility_aid", "fieldtype": "Data", "width": 110},
		{"label": "Gait / Transfer", "fieldname": "gait_transfer", "fieldtype": "Data", "width": 110},
		{"label": "Limitations Awareness", "fieldname": "awareness_of_limitations", "fieldtype": "Data", "width": 140},
		{"label": "IV Therapy", "fieldname": "iv_therapy_medical_lines", "fieldtype": "Check", "width": 90},
		{"label": "Assessed By", "fieldname": "assessed_by", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")
	if filters.get("risk_level"):
		conditions["risk_level"] = filters.get("risk_level")
	if filters.get("from_date"):
		conditions["assessment_date"] = [">=", filters.get("from_date")]
	if filters.get("to_date"):
		if "assessment_date" in conditions:
			conditions["assessment_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		else:
			conditions["assessment_date"] = ["<=", filters.get("to_date")]

	logs = frappe.db.get_all(
		"Fall Risk Assessment",
		filters=conditions,
		fields=[
			"name", "assessment_date", "resident_file", "calculated_score", "risk_level",
			"history_of_falls", "fall_count_3months", "secondary_diagnosis", "mobility_aid",
			"gait_transfer", "awareness_of_limitations", "iv_therapy_medical_lines", "assessed_by", "notes"
		],
		order_by="assessment_date desc, creation desc"
	)

	for log in logs:
		log["resident_name"] = frappe.db.get_value("Resident File", log["resident_file"], "full_name")

	return columns, logs
