# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VitalSignsLog(Document):
	def on_submit(self):
		self.sync_to_resident_file()

	def on_cancel(self):
		self.sync_to_resident_file()

	def sync_to_resident_file(self):
		if not self.resident_file:
			return
		res_doc = frappe.get_doc("Resident File", self.resident_file)
		res_doc.last_vitals = []
		logs = frappe.get_all(
			"Vital Signs Log",
			filters={"resident_file": self.resident_file, "docstatus": 1},
			fields=[
				"log_date", "log_time", "blood_pressure_systolic", "blood_pressure_diastolic",
				"pulse_heart_rate", "temperature", "oxygen_saturation_spo2", "blood_sugar_type",
				"blood_sugar_value", "respiratory_rate", "weight", "abnormal_reading", "recorded_by", "notes"
			],
			order_by="log_date desc, log_time desc, creation desc",
			limit=1
		)
		for log in logs:
			res_doc.append("last_vitals", log)
		res_doc.save(ignore_permissions=True)
