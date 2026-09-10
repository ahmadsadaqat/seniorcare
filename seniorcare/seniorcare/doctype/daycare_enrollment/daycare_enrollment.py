# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DaycareEnrollment(Document):
	def validate(self):
		if self.resident_file and not self.customer:
			self.customer = frappe.db.get_value("Resident File", self.resident_file, "customer")
