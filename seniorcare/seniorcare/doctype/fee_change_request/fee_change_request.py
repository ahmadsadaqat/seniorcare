# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, nowdate, now_datetime


# Map fee_component select values to Resident File field names
COMPONENT_FIELD_MAP = {
	"Occupancy Fee": "occupancy_fee",
	"Attendant Fee": "attendant_fee",
	"Other Fixed Charges": "other_fixed_charges",
}


class FeeChangeRequest(Document):
	def validate(self):
		self.validate_amounts()
		self.fetch_current_value()
		self.set_approver_role()

	def validate_amounts(self):
		if flt(self.new_value) < 0:
			frappe.throw(_("Proposed new rate cannot be negative."))

	def fetch_current_value(self):
		"""Auto-fetch the current rate from Resident File for the selected component."""
		if self.resident_file and self.fee_component:
			field = COMPONENT_FIELD_MAP.get(self.fee_component)
			if field:
				self.current_value = flt(
					frappe.db.get_value("Resident File", self.resident_file, field)
				)

	def set_approver_role(self):
		"""Set the approver role from Senior Care Settings."""
		if not self.approver_role:
			self.approver_role = get_fee_change_approver_role()

	def before_submit(self):
		self.db_set("status", "Pending Approval")
		self.status = "Pending Approval"
		self.notify_approvers()

	def on_submit(self):
		self.db_set("status", "Pending Approval")

	def notify_approvers(self):
		"""Send notification to users with the approver role."""
		role = self.approver_role or get_fee_change_approver_role()
		users = get_users_with_role(role)
		if not users:
			frappe.msgprint(
				_("No users found with role '{0}'. Please assign the role to at least one user.").format(role),
				title=_("No Approvers Found"),
				indicator="orange",
			)
			return

		for user in users:
			frappe.publish_realtime(
				"eval_js",
				f'frappe.show_alert({{message: "Fee Change Request {self.name} requires approval", indicator: "blue"}})',
				user=user,
			)


@frappe.whitelist()
def approve_fee_change(fee_change_request, remarks=None):
	"""Approve a submitted Fee Change Request. Updates Resident File fees and logs history."""
	doc = frappe.get_doc("Fee Change Request", fee_change_request)

	if doc.docstatus != 1:
		frappe.throw(_("Only submitted Fee Change Requests can be approved."))
	if doc.status not in ("Pending Approval",):
		frappe.throw(_("This Fee Change Request is already {0}.").format(doc.status))

	# Validate approver has the required role
	approver_role = doc.approver_role or get_fee_change_approver_role()
	if approver_role not in frappe.get_roles():
		frappe.throw(
			_("You do not have the '{0}' role required to approve fee changes.").format(approver_role)
		)

	field = COMPONENT_FIELD_MAP.get(doc.fee_component)
	if not field:
		frappe.throw(_("Invalid fee component: {0}").format(doc.fee_component))

	res_doc = frappe.get_doc("Resident File", doc.resident_file)
	previous_value = flt(res_doc.get(field))
	effective_from = getdate(doc.effective_from)
	today = getdate(nowdate())

	# Update approval fields on the FCR
	doc.db_set({
		"approver": frappe.session.user,
		"approval_date": now_datetime(),
		"approval_remarks": remarks or "",
	})

	if effective_from <= today:
		# Immediate effect: update Resident File now
		_apply_fee_change(doc, res_doc, field, previous_value)
		doc.db_set("status", "Effective")
	else:
		# Future-dated: mark as Approved, scheduler will activate it later
		doc.db_set("status", "Approved")

	frappe.msgprint(
		_("Fee Change Request {0} has been approved.").format(doc.name),
		indicator="green",
	)
	return doc.name


@frappe.whitelist()
def reject_fee_change(fee_change_request, remarks=None):
	"""Reject a submitted Fee Change Request."""
	doc = frappe.get_doc("Fee Change Request", fee_change_request)

	if doc.docstatus != 1:
		frappe.throw(_("Only submitted Fee Change Requests can be rejected."))
	if doc.status not in ("Pending Approval",):
		frappe.throw(_("This Fee Change Request is already {0}.").format(doc.status))

	approver_role = doc.approver_role or get_fee_change_approver_role()
	if approver_role not in frappe.get_roles():
		frappe.throw(
			_("You do not have the '{0}' role required to reject fee changes.").format(approver_role)
		)

	doc.db_set({
		"status": "Rejected",
		"approver": frappe.session.user,
		"approval_date": now_datetime(),
		"approval_remarks": remarks or "",
	})

	frappe.msgprint(
		_("Fee Change Request {0} has been rejected.").format(doc.name),
		indicator="red",
	)
	return doc.name


def _apply_fee_change(fcr_doc, res_doc, field, previous_value):
	"""Apply the fee change to Resident File and log history."""
	new_value = flt(fcr_doc.new_value)

	# 1. Append history item to Resident File
	res_doc.append("fee_change_history", {
		"fee_component": fcr_doc.fee_component,
		"previous_value": previous_value,
		"new_value": new_value,
		"effective_from": fcr_doc.effective_from,
		"change_date": nowdate(),
		"reason": fcr_doc.reason,
		"changed_via": fcr_doc.name,
		"approved_by": frappe.session.user,
	})

	# 2. Update the fee field on Resident File
	res_doc.db_set(field, new_value)

	# 3. Recalculate total monthly fee
	occupancy = flt(res_doc.occupancy_fee) if field != "occupancy_fee" else new_value
	attendant = flt(res_doc.attendant_fee) if field != "attendant_fee" else new_value
	other = flt(res_doc.other_fixed_charges) if field != "other_fixed_charges" else new_value
	total = occupancy + attendant + other
	res_doc.db_set("total_monthly_fee", total)

	# 4. Save the child table (fee_change_history) changes
	res_doc.save(ignore_permissions=True)


def activate_future_fee_changes():
	"""Scheduler job: Activate approved fee changes whose effective_from date has arrived."""
	today = getdate(nowdate())

	pending = frappe.get_all(
		"Fee Change Request",
		filters={
			"status": "Approved",
			"docstatus": 1,
			"effective_from": ["<=", today],
		},
		pluck="name",
	)

	for fcr_name in pending:
		try:
			fcr_doc = frappe.get_doc("Fee Change Request", fcr_name)
			field = COMPONENT_FIELD_MAP.get(fcr_doc.fee_component)
			if not field:
				continue

			res_doc = frappe.get_doc("Resident File", fcr_doc.resident_file)
			previous_value = flt(res_doc.get(field))

			_apply_fee_change(fcr_doc, res_doc, field, previous_value)
			fcr_doc.db_set("status", "Effective")
			frappe.db.commit()
		except Exception as e:
			frappe.log_error(
				f"Error activating Fee Change Request {fcr_name}: {str(e)}",
				"Fee Change Activation",
			)
			frappe.db.rollback()


def get_fee_change_approver_role():
	"""Get the configured approver role from Senior Care Settings."""
	role = frappe.db.get_single_value("Senior Care Settings", "fee_change_approver_role")
	return role or "Senior Care Approver"


def get_users_with_role(role):
	"""Get list of users who have the given role."""
	return frappe.get_all(
		"Has Role",
		filters={"role": role, "parenttype": "User"},
		pluck="parent",
	)
