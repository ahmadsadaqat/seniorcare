# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def before_insert_salary_slip(doc, method=None):
	sync_employee_snapshot(doc)


def validate_salary_slip(doc, method=None):
	sync_employee_snapshot(doc)


def on_submit_salary_slip(doc, method=None):
	sync_employee_snapshot(doc)
	if doc.payroll_entry and doc.get("is_outsourced_employee"):
		# Avoid recursive batch calls when already running auto_process or via payroll submission
		if not getattr(frappe.flags, "in_auto_process_outsourced_payroll", False) and not getattr(frappe.flags, "via_payroll_entry", False):
			pe = frappe.get_doc("Payroll Entry", doc.payroll_entry)
			if pe.payroll_type == "Outsourced Employees":
				# Trigger auto-processing if all slips for this payroll entry are submitted
				remaining_drafts = frappe.db.count("Salary Slip", {"payroll_entry": doc.payroll_entry, "docstatus": 0})
				if remaining_drafts == 0:
					pe.auto_process_outsourced_payroll()


def sync_employee_snapshot(doc):
	if doc.employee:
		emp_data = frappe.db.get_value(
			"Employee",
			doc.employee,
			["is_outsourced_employee", "manpower_supplier", "vendor_employee_id"],
			as_dict=True,
		)
		if emp_data:
			doc.is_outsourced_employee = 1 if emp_data.is_outsourced_employee else 0
			doc.manpower_supplier = emp_data.manpower_supplier
			doc.vendor_employee_id = emp_data.vendor_employee_id

			if doc.is_outsourced_employee:
				if not doc.vendor_billing_status or doc.vendor_billing_status == "Not Applicable":
					doc.vendor_billing_status = "Pending Invoice"
			else:
				doc.vendor_billing_status = "Not Applicable"
