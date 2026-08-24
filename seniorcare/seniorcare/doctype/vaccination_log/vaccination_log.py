# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VaccinationLog(Document):
	def on_submit(self):
		self.sync_to_resident_file()

	def on_cancel(self):
		self.sync_to_resident_file()

	def sync_to_resident_file(self):
		if not self.resident_file:
			return
		res_doc = frappe.get_doc("Resident File", self.resident_file)
		res_doc.last_vaccinations = []
		logs = frappe.get_all(
			"Vaccination Log",
			filters={"resident_file": self.resident_file, "docstatus": 1},
			fields=["vaccine_name", "vaccine_name_other", "date_administered", "dose_booster_number", "administered_by", "next_due_date", "status", "notes"],
			order_by="date_administered desc",
			limit=10
		)
		for log in logs:
			res_doc.append("last_vaccinations", log)
		res_doc.save(ignore_permissions=True)
