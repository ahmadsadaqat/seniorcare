# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class ResidentAdvance(Document):
	def validate(self):
		self.validate_amounts()
		self.set_customer()
		self.calculate_remaining()

	def validate_amounts(self):
		if flt(self.amount) <= 0:
			frappe.throw(frappe._("Advance Amount must be greater than zero."))

		if flt(self.utilized_amount) < 0:
			frappe.throw(frappe._("Utilized Amount cannot be negative."))

		if flt(self.utilized_amount) > flt(self.amount):
			frappe.throw(frappe._("Utilized Amount ({0}) cannot exceed Advance Amount ({1}).").format(self.utilized_amount, self.amount))

	def set_customer(self):
		if self.resident_file:
			cust = frappe.db.get_value("Resident File", self.resident_file, "customer")
			if cust:
				self.customer = cust

	def calculate_remaining(self):
		self.remaining_balance = flt(self.amount) - flt(self.utilized_amount)

	def on_submit(self):
		self.db_set("approval_status", "Approved")
		self.update_resident_financials()

	def on_cancel(self):
		self.db_set("approval_status", "Rejected")
		self.update_resident_financials()

	def update_resident_financials(self):
		if self.resident_file:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			res_doc.update_financial_summaries()
			res_doc.db_set({
				"medical_advance_balance": res_doc.medical_advance_balance,
				"personal_advance_balance": res_doc.personal_advance_balance
			})
