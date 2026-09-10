# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class PettyCashReconciliation(Document):
	def validate(self):
		self.calculate_balances()

	def calculate_balances(self):
		self.total_expenditure = sum(flt(row.amount) for row in self.get("expenses", []))
		self.closing_balance = (
			flt(self.opening_balance)
			+ flt(self.funding_received)
			- flt(self.total_expenditure)
		)

	def on_submit(self):
		if not self.status or self.status == "Draft":
			self.db_set("status", "Pending Review")


@frappe.whitelist()
def approve_petty_cash_reconciliation(rec_name, notes=None):
	"""Approve and finalize monthly petty cash audit/reconciliation."""
	doc = frappe.get_doc("Petty Cash Reconciliation", rec_name)
	if doc.docstatus != 1:
		frappe.throw(_("Document must be submitted before review/approval."))
	if doc.status == "Approved":
		frappe.throw(_("Document is already approved."))

	approver_roles = {"Senior Care Approver", "Senior Care Manager", "System Manager"}
	if not approver_roles.intersection(set(frappe.get_roles())):
		frappe.throw(_("You do not have the required role to approve reconciliations."))

	doc.db_set({
		"status": "Approved",
		"reviewed_by": frappe.session.user,
		"review_date": now_datetime(),
		"spot_check_notes": notes or doc.spot_check_notes or "",
	})
	frappe.msgprint(_("Petty Cash Reconciliation {0} approved.").format(doc.name), indicator="green")
	return doc.name


@frappe.whitelist()
def get_custodian_opening_balance(custodian):
	"""Auto-fetch opening balance from the last approved reconciliation for this custodian."""
	if not custodian:
		return 0.0

	last_closing = frappe.db.sql(
		"""
		SELECT closing_balance
		FROM `tabPetty Cash Reconciliation`
		WHERE custodian = %s AND status = 'Approved' AND docstatus = 1
		ORDER BY creation DESC LIMIT 1
		""",
		custodian,
	)
	if last_closing and last_closing[0][0] is not None:
		return flt(last_closing[0][0])
	return 0.0
