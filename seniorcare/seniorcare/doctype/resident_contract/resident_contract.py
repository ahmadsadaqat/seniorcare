# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, flt


class ResidentContract(Document):
	def validate(self):
		self.validate_dates()
		self.validate_amounts()
		self.set_customer()
		self.calculate_totals()

	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.end_date) < getdate(self.start_date):
				frappe.throw(frappe._("Contract End Date cannot precede Start Date."))

	def validate_amounts(self):
		for field in ["occupancy_fee", "attendant_fee", "other_fixed_charges", "refundable_deposit"]:
			if flt(self.get(field)) < 0:
				frappe.throw(frappe._("Negative financial values are not allowed for {0}.").format(field.replace("_", " ").title()))

	def set_customer(self):
		if self.resident_file:
			cust = frappe.db.get_value("Resident File", self.resident_file, "customer")
			if cust:
				self.customer = cust

	def calculate_totals(self):
		self.total_monthly_fee = flt(self.occupancy_fee) + flt(self.attendant_fee) + flt(self.other_fixed_charges)

	def on_submit(self):
		self.db_set("status", "Active")

		# Update linked Resident File with active commercial terms
		if self.resident_file:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			res_doc.db_set({
				"current_contract": self.name,
				"contract_start_date": self.start_date,
				"contract_end_date": self.end_date,
				"occupancy_fee": self.occupancy_fee,
				"attendant_fee": self.attendant_fee,
				"other_fixed_charges": self.other_fixed_charges,
				"total_monthly_fee": self.total_monthly_fee,
				"refundable_deposit": self.refundable_deposit
			})

	def on_cancel(self):
		self.db_set("status", "Terminated")
