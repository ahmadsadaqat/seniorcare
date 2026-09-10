# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, today


class PettyCashFund(Document):
	def on_submit(self):
		if not self.status or self.status == "Draft":
			self.db_set("status", "Pending Approval")

	def on_cancel(self):
		self.db_set("status", "Rejected")


@frappe.whitelist()
def approve_petty_cash_fund(fund_name):
	"""Approve a submitted Petty Cash Funding request."""
	doc = frappe.get_doc("Petty Cash Fund", fund_name)
	if doc.docstatus != 1:
		frappe.throw(_("Document must be submitted before approval."))
	if doc.status not in ("Pending Approval",):
		frappe.throw(_("Document is already {0}.").format(doc.status))

	approver_roles = {"Senior Care Approver", "Senior Care Manager", "System Manager"}
	if not approver_roles.intersection(set(frappe.get_roles())):
		frappe.throw(_("You do not have the required role to approve funding requests."))

	doc.db_set({
		"status": "Approved",
		"approved_by": frappe.session.user,
		"approval_date": now_datetime(),
	})
	frappe.msgprint(_("Petty Cash Fund {0} approved.").format(doc.name), indicator="green")
	return doc.name


@frappe.whitelist()
def mark_fund_disbursed(fund_name, bank_ref=None, payment_entry=None):
	"""Mark approved fund request as funded/disbursed."""
	doc = frappe.get_doc("Petty Cash Fund", fund_name)
	if doc.status != "Approved":
		frappe.throw(_("Only approved fund requests can be marked as funded."))

	doc.db_set({
		"status": "Funded",
		"funding_date": today(),
		"bank_transaction_ref": bank_ref or doc.bank_transaction_ref or "",
		"payment_entry": payment_entry or doc.payment_entry or "",
	})
	frappe.msgprint(_("Petty Cash Fund {0} marked as funded.").format(doc.name), indicator="green")
	return doc.name
