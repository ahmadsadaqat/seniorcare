# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class PettyCashRequest(Document):
	def validate(self):
		if not self.requester:
			self.requester = frappe.session.user

		if flt(self.amount) <= 0:
			frappe.throw(frappe._("Requested Amount must be greater than zero."))

		if flt(self.unspent_amount) < 0:
			frappe.throw(frappe._("Unspent Amount cannot be negative."))

		if flt(self.unspent_amount) > flt(self.amount):
			frappe.throw(frappe._("Unspent Amount cannot exceed Requested Amount."))

	def on_submit(self):
		self.db_set("approval_status", "Approved")

	def on_cancel(self):
		self.db_set("approval_status", "Rejected")
