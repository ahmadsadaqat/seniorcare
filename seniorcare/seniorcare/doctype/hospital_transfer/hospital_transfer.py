# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class HospitalTransfer(Document):
	def validate(self):
		self.validate_discharge()

	def validate_discharge(self):
		"""Auto-update status based on discharge information."""
		if self.discharge_datetime and self.status in ("Transferred", "Admitted"):
			self.status = "Discharged"
		if self.follow_up_required and self.status == "Discharged":
			self.status = "Follow-up Pending"

	def on_submit(self):
		"""Set resident status to Hospital Admitted on transfer submission."""
		if self.resident_file:
			frappe.db.set_value("Resident File", self.resident_file,
				"resident_status", "Hospital Admitted", update_modified=False)

	def on_update_after_submit(self):
		"""Handle discharge: revert resident status to Active."""
		if self.discharge_datetime and self.resident_file:
			current_status = frappe.db.get_value("Resident File", self.resident_file, "resident_status")
			if current_status == "Hospital Admitted":
				frappe.db.set_value("Resident File", self.resident_file,
					"resident_status", "Active", update_modified=False)

	def on_cancel(self):
		"""Revert resident status if transfer is cancelled."""
		if self.resident_file:
			current_status = frappe.db.get_value("Resident File", self.resident_file, "resident_status")
			if current_status == "Hospital Admitted":
				frappe.db.set_value("Resident File", self.resident_file,
					"resident_status", "Active", update_modified=False)
