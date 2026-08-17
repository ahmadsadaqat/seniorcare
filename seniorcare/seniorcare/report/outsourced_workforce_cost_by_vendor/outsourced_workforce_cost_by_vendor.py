# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Vendor"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 200},
		{"label": _("Employees"), "fieldname": "employee_count", "fieldtype": "Int", "width": 120},
		{"label": _("Payroll"), "fieldname": "total_payroll", "fieldtype": "Currency", "width": 150},
		{"label": _("Service Charges"), "fieldname": "total_service_charges", "fieldtype": "Currency", "width": 150},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 160},
	]


def get_data(filters):
	conditions = ["ops.docstatus != 2"]
	values = {}

	if filters.get("company"):
		conditions.append("ops.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("from_date"):
		conditions.append("ops.payroll_period_from >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("ops.payroll_period_to <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			ops.supplier,
			SUM(ops.total_employees) as employee_count,
			SUM(ops.payroll_amount) as total_payroll,
			SUM(ops.vendor_service_charge + ops.other_charges) as total_service_charges,
			SUM(ops.payroll_amount + ops.vendor_service_charge + ops.other_charges) as total_cost
		FROM `tabOutsourced Payroll Summary` ops
		WHERE {where_clause}
		GROUP BY ops.supplier
		ORDER BY total_cost DESC
	"""

	return frappe.db.sql(query, values, as_dict=True)
