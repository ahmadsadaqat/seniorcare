# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LabRecord(Document):
	def after_insert(self):
		self.update_resident_lab_records()

	def on_update(self):
		self.update_resident_lab_records()

	def update_resident_lab_records(self):
		"""Add/update latest lab record in Resident File child table."""
		if not self.resident_file:
			return

		resident = frappe.get_doc("Resident File", self.resident_file)

		# Check if this lab record already exists in the child table
		found = False
		for row in resident.get("lab_records", []):
			if row.lab_record == self.name:
				row.test_name = self.test_name
				row.test_date = self.test_date
				row.result_summary = self.result_summary
				row.follow_up_required = self.follow_up_required
				found = True
				break

		if not found:
			resident.append("lab_records", {
				"lab_record": self.name,
				"test_name": self.test_name,
				"test_date": self.test_date,
				"result_summary": self.result_summary,
				"follow_up_required": self.follow_up_required
			})

		resident.flags.ignore_validate = True
		resident.flags.ignore_mandatory = True
		resident.save(ignore_permissions=True)
