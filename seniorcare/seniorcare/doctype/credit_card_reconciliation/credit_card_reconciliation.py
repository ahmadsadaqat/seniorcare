# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class CreditCardReconciliation(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		total_stmt = 0.0
		total_matched = 0.0
		unmatched = 0

		for row in self.get("statement_lines", []):
			amt = flt(row.amount)
			total_stmt += amt
			if row.match_status == "Matched" and row.matched_expense:
				total_matched += amt
			else:
				unmatched += 1

		self.total_statement_amount = total_stmt
		self.total_matched_amount = total_matched
		self.unmatched_statement_lines = unmatched

	def on_submit(self):
		if not self.status or self.status == "Draft":
			self.db_set("status", "Reconciled")


@frappe.whitelist()
def approve_credit_card_reconciliation(rec_name, notes=None):
	"""CEO or Senior Care Approver approves the credit card reconciliation."""
	doc = frappe.get_doc("Credit Card Reconciliation", rec_name)
	if doc.docstatus != 1:
		frappe.throw(_("Document must be submitted before approval."))
	if doc.status == "CEO Approved":
		frappe.throw(_("Document is already approved."))

	approver_roles = {"Senior Care Approver", "Senior Care Manager", "System Manager"}
	if not approver_roles.intersection(set(frappe.get_roles())):
		frappe.throw(_("You do not have the required role to approve reconciliations."))

	doc.db_set({
		"status": "CEO Approved",
		"approved_by": frappe.session.user,
		"approval_date": now_datetime(),
		"reconciliation_notes": notes or doc.reconciliation_notes or "",
	})

	# Mark all matched expenses as Reconciled
	for row in doc.get("statement_lines", []):
		if row.matched_expense and row.match_status == "Matched":
			frappe.db.set_value(
				"Credit Card Expense",
				row.matched_expense,
				"status",
				"Reconciled",
				update_modified=False,
			)

	frappe.msgprint(_("Credit Card Reconciliation {0} approved.").format(doc.name), indicator="green")
	return doc.name
