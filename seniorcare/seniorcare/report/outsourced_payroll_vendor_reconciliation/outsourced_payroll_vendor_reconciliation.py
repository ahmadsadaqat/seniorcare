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
		{"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 160},
		{"label": _("Payroll Period"), "fieldname": "payroll_period", "fieldtype": "Data", "width": 180},
		{"label": _("Employee Count"), "fieldname": "total_employees", "fieldtype": "Int", "width": 120},
		{"label": _("Payroll Amount"), "fieldname": "payroll_amount", "fieldtype": "Currency", "width": 130},
		{"label": _("Vendor Service Charge"), "fieldname": "vendor_service_charge", "fieldtype": "Currency", "width": 140},
		{"label": _("Other Charges"), "fieldname": "other_charges", "fieldtype": "Currency", "width": 120},
		{"label": _("Tax Amount"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 110},
		{"label": _("Vendor Invoice Amount"), "fieldname": "vendor_invoice_amount", "fieldtype": "Currency", "width": 150},
		{"label": _("Variance"), "fieldname": "variance", "fieldtype": "Currency", "width": 110},
		{"label": _("Purchase Invoice"), "fieldname": "purchase_invoice", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
		{"label": _("Invoice Status"), "fieldname": "invoice_status", "fieldtype": "Data", "width": 120},
		{"label": _("Payment Status"), "fieldname": "payment_status", "fieldtype": "Data", "width": 120},
		{"label": _("Outstanding"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 130},
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
			CONCAT(ops.payroll_period_from, ' to ', ops.payroll_period_to) as payroll_period,
			ops.total_employees,
			ops.payroll_amount,
			ops.vendor_service_charge,
			ops.other_charges,
			ops.tax_amount,
			ops.vendor_invoice_amount,
			ops.variance,
			ops.purchase_invoice,
			COALESCE(pi.status, ops.status) as invoice_status,
			CASE
				WHEN pi.outstanding_amount = 0 AND pi.docstatus = 1 THEN 'Paid'
				WHEN pi.outstanding_amount > 0 AND pi.outstanding_amount < pi.grand_total THEN 'Partially Paid'
				WHEN pi.docstatus = 1 THEN 'Unpaid'
				ELSE 'No Invoice'
			END as payment_status,
			COALESCE(pi.outstanding_amount, 0) as outstanding_amount
		FROM `tabOutsourced Payroll Summary` ops
		LEFT JOIN `tabPurchase Invoice` pi ON ops.purchase_invoice = pi.name
		WHERE {where_clause}
		ORDER BY ops.payroll_period_from DESC
	"""

	return frappe.db.sql(query, values, as_dict=True)
