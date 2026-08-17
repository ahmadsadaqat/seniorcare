# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def validate_employee(doc, method=None):
	if not doc.get("is_outsourced_employee"):
		doc.manpower_supplier = None
		doc.vendor_employee_id = None
		doc.vendor_designation = None
		doc.vendor_joining_date = None
		doc.manpower_contract = None
		doc.vendor_billing_method = None
	else:
		if not doc.get("manpower_supplier"):
			frappe.throw(_("Manpower Supplier is mandatory for Outsourced Employees."), title=_("Mandatory Field Missing"))
		if not doc.get("vendor_employee_id"):
			frappe.throw(_("Vendor Employee ID is mandatory for Outsourced Employees."), title=_("Mandatory Field Missing"))

		is_manpower = frappe.db.get_value("Supplier", doc.manpower_supplier, "is_manpower_supplier")
		if not is_manpower:
			frappe.throw(
				_("Selected Supplier '{0}' is not configured as a Manpower Supplier. Please set 'Is Manpower Supplier = Yes' on Supplier master.").format(doc.manpower_supplier),
				title=_("Invalid Supplier"),
			)
