# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ADLAssessment(Document):
	def validate(self):
		self.calculate_adl_score()

	def calculate_adl_score(self):
		"""Each non-Independent field scores 1 point. Total range: 0-6."""
		score = 0
		for field in ["bathing", "dressing", "toileting", "transferring", "continence_adl", "feeding"]:
			if self.get(field) and self.get(field) != "Independent":
				score += 1
		self.total_adl_score = score

	def on_submit(self):
		self.update_resident_adl_summary()

	def update_resident_adl_summary(self):
		"""Update the latest ADL summary fields on Resident File."""
		if self.resident_file:
			frappe.db.set_value("Resident File", self.resident_file, {
				"latest_adl_score": self.total_adl_score,
				"latest_adl_date": self.assessment_date,
				"latest_adl_assessed_by": self.assessed_by_name or frappe.db.get_value("Employee", self.assessed_by, "employee_name")
			}, update_modified=False)
