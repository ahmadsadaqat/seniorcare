# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class TherapySession(Document):
	def validate(self):
		self.set_defaults()
		self.validate_package_sessions()

	def set_defaults(self):
		if self.therapy_type:
			defaults = frappe.db.get_value(
				"Therapy Type",
				self.therapy_type,
				["default_duration_minutes", "default_rate"],
				as_dict=True,
			)
			if defaults:
				if not self.duration_minutes:
					self.duration_minutes = defaults.default_duration_minutes
				if not self.rate and not self.therapy_package:
					self.rate = defaults.default_rate

		if self.resident_file and not self.customer:
			self.customer = frappe.db.get_value("Resident File", self.resident_file, "customer")

		if self.therapy_package and not self.session_number:
			prev_sessions = frappe.db.count(
				"Therapy Session",
				filters={
					"therapy_package": self.therapy_package,
					"resident_file": self.resident_file,
					"docstatus": 1,
				},
			)
			self.session_number = prev_sessions + 1

	def validate_package_sessions(self):
		if self.therapy_package and self.session_number:
			total = frappe.db.get_value("Therapy Package", self.therapy_package, "total_sessions")
			if total and self.session_number > total:
				frappe.msgprint(
					_("Warning: Session #{0} exceeds the total sessions ({1}) in package {2}.").format(
						self.session_number, total, self.therapy_package
					),
					indicator="orange",
				)


@frappe.whitelist()
def invoice_therapy_session(session_name):
	"""Generate a Draft Sales Invoice for a completed therapy session."""
	session = frappe.get_doc("Therapy Session", session_name)
	if session.docstatus != 1:
		frappe.throw(_("Therapy Session must be submitted before invoicing."))
	if session.billing_status == "Invoiced" and session.sales_invoice:
		frappe.throw(_("Session is already invoiced under {0}.").format(session.sales_invoice))
	if not session.customer:
		frappe.throw(_("Resident is not linked to a Customer."))

	rate = flt(session.rate)
	if not rate and session.therapy_package:
		pkg_rate = frappe.db.get_value("Therapy Package", session.therapy_package, "package_rate")
		pkg_sessions = frappe.db.get_value("Therapy Package", session.therapy_package, "total_sessions")
		if pkg_rate and pkg_sessions:
			rate = flt(pkg_rate) / flt(pkg_sessions)

	sinv = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": session.customer,
		"posting_date": today(),
		"due_date": today(),
		"remarks": f"Therapy Session: {session.therapy_type} on {session.appointment_datetime}",
		"items": [
			{
				"item_name": f"Therapy Session - {session.therapy_type}",
				"description": f"Therapy Session for {session.resident_name or session.resident_file}",
				"qty": 1,
				"rate": rate,
			}
		],
	})
	sinv.insert(ignore_permissions=True)

	session.db_set({
		"billing_status": "Invoiced",
		"sales_invoice": sinv.name,
	})

	frappe.msgprint(_("Sales Invoice {0} created.").format(sinv.name), indicator="green")
	return sinv.name
