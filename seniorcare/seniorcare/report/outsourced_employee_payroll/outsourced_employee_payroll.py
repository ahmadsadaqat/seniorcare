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
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 140},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Vendor Employee ID"), "fieldname": "vendor_employee_id", "fieldtype": "Data", "width": 140},
		{"label": _("Supplier"), "fieldname": "manpower_supplier", "fieldtype": "Link", "options": "Supplier", "width": 160},
		{"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 150},
		{"label": _("Payroll Period"), "fieldname": "payroll_period", "fieldtype": "Data", "width": 180},
		{"label": _("Basic"), "fieldname": "basic", "fieldtype": "Currency", "width": 110},
		{"label": _("Earnings"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 110},
		{"label": _("Deductions"), "fieldname": "total_deduction", "fieldtype": "Currency", "width": 110},
		{"label": _("Net Payroll"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
		{"label": _("Vendor Billing Status"), "fieldname": "vendor_billing_status", "fieldtype": "Data", "width": 140},
		{"label": _("Purchase Invoice"), "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
	]


def get_data(filters):
	conditions = ["ss.docstatus = 1", "ss.is_outsourced_employee = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("ss.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("from_date"):
		conditions.append("ss.start_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("ss.end_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]
	if filters.get("supplier"):
		conditions.append("ss.manpower_supplier = %(supplier)s")
		values["supplier"] = filters["supplier"]
	if filters.get("employee"):
		conditions.append("ss.employee = %(employee)s")
		values["employee"] = filters["employee"]
	if filters.get("payroll_entry"):
		conditions.append("ss.payroll_entry = %(payroll_entry)s")
		values["payroll_entry"] = filters["payroll_entry"]
	if filters.get("billing_status"):
		conditions.append("ss.vendor_billing_status = %(billing_status)s")
		values["billing_status"] = filters["billing_status"]

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			ss.employee,
			ss.employee_name,
			ss.vendor_employee_id,
			ss.manpower_supplier,
			ss.name as salary_slip,
			CONCAT(ss.start_date, ' to ', ss.end_date) as payroll_period,
			ss.base_gross_pay as basic,
			ss.gross_pay,
			ss.total_deduction,
			ss.net_pay,
			ss.vendor_billing_status,
			ops.purchase_invoice
		FROM `tabSalary Slip` ss
		LEFT JOIN `tabOutsourced Payroll Summary` ops ON ss.outsourced_payroll_summary = ops.name
		WHERE {where_clause}
		ORDER BY ss.start_date DESC, ss.employee ASC
	"""

	return frappe.db.sql(query, values, as_dict=True)
