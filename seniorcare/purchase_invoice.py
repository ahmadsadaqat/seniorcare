# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def validate_purchase_invoice(doc, method=None):
	if not doc.get("is_outsourced_payroll_invoice") and not doc.get("outsourced_payroll_summary"):
		return

	if doc.get("outsourced_payroll_summary"):
		summary = frappe.get_doc("Outsourced Payroll Summary", doc.outsourced_payroll_summary)
		if doc.supplier != summary.supplier:
			frappe.throw(
				_("Supplier '{0}' does not match the Supplier '{1}' in Outsourced Payroll Summary '{2}'.").format(
					doc.supplier, summary.supplier, summary.name
				),
				title=_("Supplier Mismatch"),
			)

		existing_pi = summary.purchase_invoice
		if existing_pi and existing_pi != doc.name:
			if frappe.db.get_value("Purchase Invoice", existing_pi, "docstatus") != 2:
				frappe.throw(
					_("Outsourced Payroll Summary '{0}' already has an active Purchase Invoice '{1}'.").format(
						summary.name, existing_pi
					),
					title=_("Duplicate Invoice Link"),
				)

		# Sync period and employee count
		doc.payroll_period_from = summary.payroll_period_from
		doc.payroll_period_to = summary.payroll_period_to
		doc.payroll_amount = summary.payroll_amount
		doc.vendor_service_charge = summary.vendor_service_charge
		doc.other_charges = summary.other_charges
		doc.payroll_variance = summary.variance
		doc.employee_count = summary.total_employees

	if flt(doc.get("payroll_variance")) != 0 and not doc.get("variance_reason"):
		frappe.throw(
			_("Variance Reason is mandatory when there is a payroll variance of {0}.").format(doc.payroll_variance),
			title=_("Variance Reason Required"),
		)


def on_submit_purchase_invoice(doc, method=None):
	if not doc.get("is_outsourced_payroll_invoice") or not doc.get("outsourced_payroll_summary"):
		return

	summary_name = doc.outsourced_payroll_summary
	frappe.db.set_value(
		"Outsourced Payroll Summary",
		summary_name,
		{
			"purchase_invoice": doc.name,
			"status": "Completed",
		},
	)

	# Update all linked salary slips to Invoiced
	slips = frappe.get_all(
		"Outsourced Payroll Employee",
		filters={"parent": summary_name},
		pluck="salary_slip",
	)
	for ss in slips:
		if ss:
			frappe.db.set_value("Salary Slip", ss, "vendor_billing_status", "Invoiced")


def on_cancel_purchase_invoice(doc, method=None):
	if not doc.get("is_outsourced_payroll_invoice") or not doc.get("outsourced_payroll_summary"):
		return

	summary_name = doc.outsourced_payroll_summary
	frappe.db.set_value(
		"Outsourced Payroll Summary",
		summary_name,
		{
			"purchase_invoice": None,
			"status": "Pending Invoice",
		},
	)

	# Update all linked salary slips back to Pending Invoice
	slips = frappe.get_all(
		"Outsourced Payroll Employee",
		filters={"parent": summary_name},
		pluck="salary_slip",
	)
	for ss in slips:
		if ss:
			frappe.db.set_value("Salary Slip", ss, "vendor_billing_status", "Pending Invoice")
