# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = filters or {}
	columns = [
		{"label": "Log ID", "fieldname": "name", "fieldtype": "Link", "options": "Vital Signs Log", "width": 130},
		{"label": "Log Date", "fieldname": "log_date", "fieldtype": "Date", "width": 110},
		{"label": "Log Time", "fieldname": "log_time", "fieldtype": "Time", "width": 90},
		{"label": "Resident ID", "fieldname": "resident_file", "fieldtype": "Link", "options": "Resident File", "width": 130},
		{"label": "Resident Name", "fieldname": "resident_name", "fieldtype": "Data", "width": 160},
		{"label": "BP Systolic", "fieldname": "blood_pressure_systolic", "fieldtype": "Int", "width": 90},
		{"label": "BP Diastolic", "fieldname": "blood_pressure_diastolic", "fieldtype": "Int", "width": 90},
		{"label": "Heart Rate", "fieldname": "pulse_heart_rate", "fieldtype": "Int", "width": 90},
		{"label": "Temp (°F)", "fieldname": "temperature", "fieldtype": "Float", "width": 90},
		{"label": "SpO2 (%)", "fieldname": "oxygen_saturation_spo2", "fieldtype": "Float", "width": 90},
		{"label": "Sugar Type", "fieldname": "blood_sugar_type", "fieldtype": "Data", "width": 100},
		{"label": "Sugar (mg/dL)", "fieldname": "blood_sugar_value", "fieldtype": "Float", "width": 100},
		{"label": "Resp Rate", "fieldname": "respiratory_rate", "fieldtype": "Int", "width": 90},
		{"label": "Weight (kg)", "fieldname": "weight", "fieldtype": "Float", "width": 90},
		{"label": "Abnormal?", "fieldname": "abnormal_reading", "fieldtype": "Data", "width": 90},
		{"label": "Recorded By", "fieldname": "recorded_by", "fieldtype": "Link", "options": "Employee", "width": 130},
		{"label": "Notes", "fieldname": "notes", "fieldtype": "Data", "width": 180}
	]

	conditions = {"docstatus": 1}
	if filters.get("resident_file"):
		conditions["resident_file"] = filters.get("resident_file")
	if filters.get("abnormal_reading"):
		conditions["abnormal_reading"] = filters.get("abnormal_reading")
	if filters.get("from_date"):
		conditions["log_date"] = [">=", filters.get("from_date")]
	if filters.get("to_date"):
		if "log_date" in conditions:
			conditions["log_date"] = ["between", [filters.get("from_date"), filters.get("to_date")]]
		else:
			conditions["log_date"] = ["<=", filters.get("to_date")]

	logs = frappe.db.get_all(
		"Vital Signs Log",
		filters=conditions,
		fields=[
			"name", "log_date", "log_time", "resident_file",
			"blood_pressure_systolic", "blood_pressure_diastolic", "pulse_heart_rate",
			"temperature", "oxygen_saturation_spo2", "blood_sugar_type", "blood_sugar_value",
			"respiratory_rate", "weight", "abnormal_reading", "recorded_by", "notes"
		],
		order_by="log_date desc, log_time desc"
	)

	for log in logs:
		log["resident_name"] = frappe.db.get_value("Resident File", log["resident_file"], "full_name")

	return columns, logs
