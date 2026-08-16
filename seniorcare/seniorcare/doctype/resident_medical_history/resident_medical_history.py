# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ResidentMedicalHistory(Document):
	def on_change(self):
		self.update_resident_summary()

	def on_trash(self):
		self.update_resident_summary()

	def update_resident_summary(self):
		if self.resident_file:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			res_doc.update_medical_summaries()
			res_doc.db_set("medical_history_summary", res_doc.medical_history_summary)
