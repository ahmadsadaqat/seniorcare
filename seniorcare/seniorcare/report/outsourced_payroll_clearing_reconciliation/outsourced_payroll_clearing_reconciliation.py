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
		{"label": _("Payroll Summary"), "fieldname": "name", "fieldtype": "Link", "options": "Outsourced Payroll Summary", "width": 180},
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 160},
		{"label": _("Payroll Amount"), "fieldname": "payroll_amount", "fieldtype": "Currency", "width": 140},
		{"label": _("Vendor Invoice"), "fieldname": "vendor_invoice", "fieldtype": "Currency", "width": 140},
		{"label": _("Cleared"), "fieldname": "cleared", "fieldtype": "Currency", "width": 140},
		{"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	conditions = ["ops.docstatus != 2"]
	values = {}

	if filters.get("company"):
		conditions.append("ops.company = %(company)s")
		values["company"] = filters["company"]
	if filters.get("supplier"):
		conditions.append("ops.supplier = %(supplier)s")
		values["supplier"] = filters["supplier"]

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			ops.name,
			ops.supplier,
			ops.payroll_amount,
			COALESCE(pi.payroll_amount, 0) as vendor_invoice,
			CASE
				WHEN pi.docstatus = 1 THEN COALESCE(pi.payroll_amount, 0)
				ELSE 0
			END as cleared,
			ops.payroll_amount - CASE
				WHEN pi.docstatus = 1 THEN COALESCE(pi.payroll_amount, 0)
				ELSE 0
			END as balance
		FROM `tabOutsourced Payroll Summary` ops
		LEFT JOIN `tabPurchase Invoice` pi ON ops.purchase_invoice = pi.name
		WHERE {where_clause}
		ORDER BY ops.payroll_period_from DESC
	"""

	return frappe.db.sql(query, values, as_dict=True)
