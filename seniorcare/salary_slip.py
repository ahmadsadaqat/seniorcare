# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe


def before_insert_salary_slip(doc, method=None):
	sync_employee_snapshot(doc)


def validate_salary_slip(doc, method=None):
	sync_employee_snapshot(doc)


def sync_employee_snapshot(doc):
	if doc.employee:
		emp_data = frappe.db.get_value(
			"Employee",
			doc.employee,
			["is_outsourced_employee", "manpower_supplier", "vendor_employee_id"],
			as_dict=True,
		)
		if emp_data:
			doc.is_outsourced_employee = emp_data.is_outsourced_employee or 0
			doc.manpower_supplier = emp_data.manpower_supplier
			doc.vendor_employee_id = emp_data.vendor_employee_id

			if doc.is_outsourced_employee:
				if not doc.vendor_billing_status or doc.vendor_billing_status == "Not Applicable":
					doc.vendor_billing_status = "Pending Invoice"
			else:
				doc.vendor_billing_status = "Not Applicable"
