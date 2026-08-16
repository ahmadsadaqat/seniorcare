# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IncidentReport(Document):
	def validate(self):
		if not self.reported_by:
			self.reported_by = frappe.session.user

	def on_submit(self):
		self.update_resident_incident_summary()

	def on_cancel(self):
		self.update_resident_incident_summary()

	def update_resident_incident_summary(self):
		if self.resident_file:
			incidents = frappe.db.get_all(
				"Incident Report",
				filters={"resident_file": self.resident_file, "docstatus": 1},
				fields=["name", "incident_type", "incident_datetime", "status"]
			)
			count = len(incidents)
			if count > 0:
				latest = incidents[0]
				summary = f"Total Incidents: {count}. Latest: {latest.incident_type} on {latest.incident_datetime} ({latest.status})"
			else:
				summary = "No recorded incidents"

			frappe.db.set_value("Resident File", self.resident_file, "incident_summary", summary)
