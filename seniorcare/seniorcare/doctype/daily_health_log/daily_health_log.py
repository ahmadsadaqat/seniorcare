# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class DailyHealthLog(Document):
	def on_submit(self):
		self.sync_to_resident_file()

	def on_cancel(self):
		self.sync_to_resident_file()

	def sync_to_resident_file(self):
		if not self.resident_file:
			return
		res_doc = frappe.get_doc("Resident File", self.resident_file)
		res_doc.todays_health_logs = []
		# Get recent submitted health logs (up to 3 for today or most recent)
		logs = frappe.get_all(
			"Daily Health Log",
			filters={"resident_file": self.resident_file, "docstatus": 1},
			fields=[
				"log_date", "shift", "general_condition", "meals_taken", "sleep_quality",
				"flags_concerns", "flags_description", "pain_present", "pain_scale",
				"pain_pattern", "pain_location", "mood_behavior", "recorded_by", "notes"
			],
			order_by="log_date desc, creation desc",
			limit=3
		)
		for log in logs:
			res_doc.append("todays_health_logs", log)
		res_doc.save(ignore_permissions=True)
