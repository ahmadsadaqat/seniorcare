# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ResidentAssessment(Document):
	def validate(self):
		self.compute_recent_weight_change()

	def compute_recent_weight_change(self):
		"""Auto-compare latest 2 Vital Signs Log weight entries for this resident."""
		if not self.resident_file:
			return

		weights = frappe.get_all(
			"Vital Signs Log",
			filters={
				"resident_file": self.resident_file,
				"docstatus": 1,
				"weight": [">", 0]
			},
			fields=["weight", "log_date"],
			order_by="log_date desc",
			limit=2
		)

		if len(weights) >= 2:
			latest = flt(weights[0].weight)
			previous = flt(weights[1].weight)
			diff = latest - previous
			sign = "+" if diff > 0 else ""
			self.recent_weight_change = f"{sign}{diff:.1f} kg ({previous:.1f} → {latest:.1f})"
		elif len(weights) == 1:
			self.recent_weight_change = f"Current: {flt(weights[0].weight):.1f} kg (no prior reading)"
		else:
			self.recent_weight_change = "No weight data available"

	def on_submit(self):
		self.assessment_status = "Completed"
