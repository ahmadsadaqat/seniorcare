# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WoundAssessment(Document):
	def on_submit(self):
		self.update_resident_wound_records()

	def update_resident_wound_records(self):
		"""Add/update/remove wound record in Resident File child table."""
		if not self.resident_file:
			return

		resident = frappe.get_doc("Resident File", self.resident_file)

		if self.wound_status == "Healed":
			# Remove healed wounds from the resident file child table
			wounds_to_keep = []
			for w in resident.get("wound_records", []):
				if w.wound_assessment != self.name:
					wounds_to_keep.append(w)
			resident.wound_records = []
			for w in wounds_to_keep:
				resident.append("wound_records", {
					"wound_assessment": w.wound_assessment,
					"wound_type": w.wound_type,
					"wound_description": w.wound_description,
					"wound_stage": w.wound_stage,
					"wound_status": w.wound_status,
					"wound_finding_date": w.wound_finding_date
				})
		elif self.wound_type == "Existing" and self.existing_wound_reference:
			# Update existing wound row
			found = False
			for w in resident.get("wound_records", []):
				if w.wound_assessment == self.existing_wound_reference:
					w.wound_assessment = self.name
					w.wound_description = self.wound_description
					w.wound_stage = self.wound_stage
					w.wound_status = self.wound_status
					w.wound_finding_date = self.wound_finding_date or w.wound_finding_date
					found = True
					break
			if not found:
				# Fallback: add as new if reference not found
				resident.append("wound_records", {
					"wound_assessment": self.name,
					"wound_type": self.wound_type,
					"wound_description": self.wound_description,
					"wound_stage": self.wound_stage,
					"wound_status": self.wound_status,
					"wound_finding_date": self.wound_finding_date
				})
		else:
			# New or Pre Admission wound: add row
			resident.append("wound_records", {
				"wound_assessment": self.name,
				"wound_type": self.wound_type,
				"wound_description": self.wound_description,
				"wound_stage": self.wound_stage,
				"wound_status": self.wound_status,
				"wound_finding_date": self.wound_finding_date
			})

		resident.flags.ignore_validate = True
		resident.flags.ignore_mandatory = True
		resident.save(ignore_permissions=True)
