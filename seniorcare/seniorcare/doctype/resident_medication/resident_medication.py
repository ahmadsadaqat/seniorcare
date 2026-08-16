# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class ResidentMedication(Document):
	def validate(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(frappe._("End Date cannot be earlier than Start Date."))

		# Auto mark is_active = 0 if end_date has passed
		if self.end_date and getdate(self.end_date) < getdate(today()):
			self.is_active = 0

	def on_change(self):
		self.update_resident_summary()

	def on_trash(self):
		self.update_resident_summary()

	def update_resident_summary(self):
		if self.resident_file:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			res_doc.update_medical_summaries()
			res_doc.db_set("current_medication_summary", res_doc.current_medication_summary)
