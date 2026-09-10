# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, now_datetime, today


class SalaryAdvanceRequest(Document):
	def validate(self):
		self.compute_advance_metrics()

	def compute_advance_metrics(self):
		if not self.employee:
			return

		req_date = getdate(self.request_date or today())

		# Find last approved advance for this employee
		last_adv = frappe.db.sql(
			"""
			SELECT request_date
			FROM `tabSalary Advance Request`
			WHERE employee = %s AND name != %s AND status IN ('Approved', 'Disbursed') AND docstatus = 1
			ORDER BY request_date DESC LIMIT 1
			""",
			(self.employee, self.name or ""),
		)

		if last_adv and last_adv[0][0]:
			last_d = getdate(last_adv[0][0])
			self.last_advance_date = last_d
			self.days_since_last_advance = date_diff(req_date, last_d)

			if self.days_since_last_advance < 90:
				frappe.msgprint(
					_("Policy Warning: Employee {0} received an advance {1} days ago (policy guideline recommends at least 90 days between advances).").format(
						self.employee_name or self.employee, self.days_since_last_advance
					),
					indicator="orange",
				)
		else:
			self.last_advance_date = None
			self.days_since_last_advance = None

		# Estimate accrued salary: calculate days worked in current month * daily rate
		# Daily rate estimated from basic salary in Salary Structure Assignment
		base_salary = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": self.employee, "docstatus": 1},
			"base",
		)
		if base_salary:
			daily_rate = flt(base_salary) / 30.0
			accrued = daily_rate * req_date.day
			self.salary_accrued_to_date = round(accrued, 2)
		else:
			self.salary_accrued_to_date = 0.0

	def on_submit(self):
		if not self.status or self.status == "Draft":
			self.db_set("status", "Pending Approval")

	def on_cancel(self):
		self.db_set("status", "Rejected")


@frappe.whitelist()
def approve_salary_advance(req_name):
	"""Approve salary advance request."""
	doc = frappe.get_doc("Salary Advance Request", req_name)
	if doc.docstatus != 1:
		frappe.throw(_("Request must be submitted before approval."))
	if doc.status != "Pending Approval":
		frappe.throw(_("Request is already {0}.").format(doc.status))

	approver_roles = {"Senior Care Approver", "Senior Care Manager", "System Manager"}
	if not approver_roles.intersection(set(frappe.get_roles())):
		frappe.throw(_("You do not have the required role to approve salary advances."))

	doc.db_set({
		"status": "Approved",
		"approved_by": frappe.session.user,
		"approval_date": now_datetime(),
	})
	frappe.msgprint(_("Salary Advance {0} approved.").format(doc.name), indicator="green")
	return doc.name


@frappe.whitelist()
def mark_salary_advance_disbursed(req_name, payment_entry=None):
	"""Record payment entry reference when advance is disbursed."""
	doc = frappe.get_doc("Salary Advance Request", req_name)
	if doc.status != "Approved":
		frappe.throw(_("Only approved advances can be marked as disbursed."))

	doc.db_set({
		"status": "Disbursed",
		"disbursement_entry": payment_entry or doc.disbursement_entry or "",
	})
	frappe.msgprint(_("Salary Advance {0} marked as disbursed.").format(doc.name), indicator="green")
	return doc.name
