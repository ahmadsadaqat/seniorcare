# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CarePlan(Document):
	def after_insert(self):
		self.sync_to_resident_file()

	def on_update(self):
		self.sync_to_resident_file()

	def on_trash(self):
		self.remove_from_resident_file()

	def sync_to_resident_file(self):
		"""Sync active care plans to Resident File child table. Skip Achieved/Discontinued."""
		if not self.resident_file:
			return

		resident = frappe.get_doc("Resident File", self.resident_file)

		if self.status in ("Achieved", "Discontinued"):
			# Remove from resident file
			self._remove_row_from_resident(resident)
		else:
			# Add or update
			found = False
			for row in resident.get("active_care_plans", []):
				if row.care_plan == self.name:
					row.care_plan_goal = (self.care_plan_goal or "")[:500]
					row.responsible_role = self.responsible_role
					row.review_date = self.review_date
					row.status = self.status
					found = True
					break

			if not found and self.status == "Active":
				resident.append("active_care_plans", {
					"care_plan": self.name,
					"care_plan_goal": (self.care_plan_goal or "")[:500],
					"responsible_role": self.responsible_role,
					"review_date": self.review_date,
					"status": self.status
				})

		resident.flags.ignore_validate = True
		resident.flags.ignore_mandatory = True
		resident.save(ignore_permissions=True)

	def remove_from_resident_file(self):
		"""Remove this care plan from resident file on deletion."""
		if not self.resident_file:
			return
		resident = frappe.get_doc("Resident File", self.resident_file)
		self._remove_row_from_resident(resident)
		resident.flags.ignore_validate = True
		resident.flags.ignore_mandatory = True
		resident.save(ignore_permissions=True)

	def _remove_row_from_resident(self, resident):
		rows_to_keep = [r for r in resident.get("active_care_plans", []) if r.care_plan != self.name]
		resident.active_care_plans = []
		for r in rows_to_keep:
			resident.append("active_care_plans", {
				"care_plan": r.care_plan,
				"care_plan_goal": r.care_plan_goal,
				"responsible_role": r.responsible_role,
				"review_date": r.review_date,
				"status": r.status
			})
