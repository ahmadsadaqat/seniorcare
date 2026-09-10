# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class ResidentExitRecord(Document):
	def validate(self):
		self.calculate_settlement()

	def calculate_settlement(self):
		"""Calculate totals and net refund amount."""
		self.total_dues = (
			flt(self.outstanding_invoices)
			+ flt(self.pending_charges)
			+ flt(self.damages)
			+ flt(self.notice_period_penalty)
		)

		if not self.total_deductions:
			self.total_deductions = self.total_dues

		total_deposits = (
			flt(self.security_deposit_held)
			+ flt(self.medical_advance_balance)
			+ flt(self.personal_advance_balance)
		)

		self.net_refund_amount = total_deposits - flt(self.total_deductions)

	def on_submit(self):
		if not self.status or self.status == "Draft":
			self.db_set("status", "Pending Settlement")

	def on_cancel(self):
		self.db_set("status", "Cancelled")


@frappe.whitelist()
def fetch_resident_settlement_data(resident_file):
	"""Fetch deposit balances, contract info, and outstanding invoices for exit settlement."""
	if not resident_file:
		return {}

	rf = frappe.get_doc("Resident File", resident_file)

	# Calculate outstanding invoices for this resident's customer
	outstanding_invoices = 0.0
	if rf.customer:
		out = frappe.db.sql(
			"""
			SELECT SUM(outstanding_amount)
			FROM `tabSales Invoice`
			WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
			""",
			rf.customer,
		)
		if out and out[0][0]:
			outstanding_invoices = flt(out[0][0])

	notice_period_days = 30
	if rf.current_contract:
		contract = frappe.db.get_value("Resident Contract", rf.current_contract, "notice_period_days")
		if contract:
			notice_period_days = contract

	return {
		"security_deposit_held": flt(rf.security_deposit_held),
		"medical_advance_balance": flt(rf.medical_advance_balance),
		"personal_advance_balance": flt(rf.personal_advance_balance),
		"outstanding_invoices": outstanding_invoices,
		"notice_period_days": notice_period_days,
	}


@frappe.whitelist()
def approve_settlement(record_name, remarks=None):
	"""Approve exit settlement, discharge resident, free up room, and cease billing."""
	doc = frappe.get_doc("Resident Exit Record", record_name)

	if doc.docstatus != 1:
		frappe.throw(_("Document must be submitted before settlement approval."))
	if doc.status in ("Settled", "Cancelled"):
		frappe.throw(_("Document is already {0}.").format(doc.status))

	# Check permission
	approver_roles = {"Senior Care Approver", "Senior Care Manager", "System Manager"}
	user_roles = set(frappe.get_roles())
	if not approver_roles.intersection(user_roles):
		frappe.throw(_("You do not have the required role to approve exit settlement."))

	doc.db_set({
		"status": "Settled",
		"approved_by": frappe.session.user,
		"approval_date": now_datetime(),
		"settlement_remarks": remarks or doc.settlement_remarks or "",
	})

	# Update Resident File
	rf = frappe.get_doc("Resident File", doc.resident_file)
	rf.db_set({
		"resident_status": "Discharged",
		"exit_date": doc.exit_date,
		"exit_reason": doc.exit_reason,
		"auto_create_monthly_invoice": 0,
	})

	# Free up assigned room if any
	if rf.current_room:
		frappe.db.set_value("Room", rf.current_room, "occupancy_status", "Available")
		rf.db_set("current_room", None)

	frappe.msgprint(
		_("Resident {0} has been discharged and settlement finalized.").format(rf.full_name or rf.name),
		indicator="green",
	)
	return doc.name
