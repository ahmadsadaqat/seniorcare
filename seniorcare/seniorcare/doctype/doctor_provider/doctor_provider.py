# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DoctorProvider(Document):
	def validate(self):
		if self.email and not frappe.utils.validate_email_address(self.email):
			frappe.throw(frappe._("Invalid Email Address for Doctor Provider"))
