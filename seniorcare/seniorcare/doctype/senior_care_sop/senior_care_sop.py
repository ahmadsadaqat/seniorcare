# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class SeniorCareSOP(Document):
	def validate(self):
		if self.issue_date and self.expiry_date:
			if getdate(self.expiry_date) < getdate(self.issue_date):
				frappe.throw(frappe._("SOP Expiry Date cannot be earlier than Issue Date."))
