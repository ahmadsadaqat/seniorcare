# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

ROLES = [
	"Senior Care Manager",
	"Senior Care Doctor",
	"Senior Care Nurse",
	"Senior Care Operations",
	"Senior Care Finance",
	"Senior Care HR",
	"Senior Care Receptionist"
]

CUSTOM_FIELDS = {
	"Supplier": [
		{
			"fieldname": "outsourced_workforce_section",
			"fieldtype": "Section Break",
			"label": "Outsourced Workforce",
			"insert_after": "disabled"
		},
		{
			"fieldname": "is_manpower_supplier",
			"fieldtype": "Check",
			"label": "Is Manpower Supplier",
			"insert_after": "outsourced_workforce_section",
			"default": "0"
		},
		{
			"fieldname": "vendor_code",
			"fieldtype": "Data",
			"label": "Vendor Code",
			"insert_after": "is_manpower_supplier",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "contract_start_date",
			"fieldtype": "Date",
			"label": "Contract Start Date",
			"insert_after": "vendor_code",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "contract_end_date",
			"fieldtype": "Date",
			"label": "Contract End Date",
			"insert_after": "contract_start_date",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "column_break_outsourced_supplier",
			"fieldtype": "Column Break",
			"insert_after": "contract_end_date"
		},
		{
			"fieldname": "contract_reference",
			"fieldtype": "Data",
			"label": "Contract Reference",
			"insert_after": "column_break_outsourced_supplier",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "billing_frequency",
			"fieldtype": "Select",
			"label": "Billing Frequency",
			"options": "Monthly\nWeekly\nOther",
			"insert_after": "contract_reference",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "invoice_required",
			"fieldtype": "Check",
			"label": "Invoice Required",
			"default": "1",
			"insert_after": "billing_frequency",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "default_outsourced_expense_account",
			"fieldtype": "Link",
			"label": "Default Outsourced Expense Account",
			"options": "Account",
			"insert_after": "invoice_required",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		},
		{
			"fieldname": "default_cost_center",
			"fieldtype": "Link",
			"label": "Default Cost Center",
			"options": "Cost Center",
			"insert_after": "default_outsourced_expense_account",
			"depends_on": "eval:doc.is_manpower_supplier==1"
		}
	],
	"Employee": [
		{
			"fieldname": "outsourced_employment_section",
			"fieldtype": "Section Break",
			"label": "Outsourced Employment",
			"insert_after": "status"
		},
		{
			"fieldname": "is_outsourced_employee",
			"fieldtype": "Check",
			"label": "Outsourced Employee",
			"insert_after": "outsourced_employment_section",
			"default": "0"
		},
		{
			"fieldname": "manpower_supplier",
			"fieldtype": "Link",
			"label": "Manpower Supplier",
			"options": "Supplier",
			"insert_after": "is_outsourced_employee",
			"depends_on": "eval:doc.is_outsourced_employee==1",
			"mandatory_depends_on": "eval:doc.is_outsourced_employee==1"
		},
		{
			"fieldname": "vendor_employee_id",
			"fieldtype": "Data",
			"label": "Vendor Employee ID",
			"insert_after": "manpower_supplier",
			"depends_on": "eval:doc.is_outsourced_employee==1",
			"mandatory_depends_on": "eval:doc.is_outsourced_employee==1"
		},
		{
			"fieldname": "vendor_designation",
			"fieldtype": "Data",
			"label": "Vendor Designation",
			"insert_after": "vendor_employee_id",
			"depends_on": "eval:doc.is_outsourced_employee==1"
		},
		{
			"fieldname": "column_break_outsourced_employee",
			"fieldtype": "Column Break",
			"insert_after": "vendor_designation"
		},
		{
			"fieldname": "vendor_joining_date",
			"fieldtype": "Date",
			"label": "Vendor Joining Date",
			"insert_after": "column_break_outsourced_employee",
			"depends_on": "eval:doc.is_outsourced_employee==1"
		},
		{
			"fieldname": "manpower_contract",
			"fieldtype": "Link",
			"label": "Manpower Contract",
			"options": "Manpower Contract",
			"insert_after": "vendor_joining_date",
			"depends_on": "eval:doc.is_outsourced_employee==1"
		},
		{
			"fieldname": "vendor_billing_method",
			"fieldtype": "Select",
			"label": "Vendor Billing Method",
			"options": "Fixed Monthly\nAttendance Based\nDaily Rate\nHourly Rate\nSalary + Service Charge\nOther",
			"insert_after": "manpower_contract",
			"depends_on": "eval:doc.is_outsourced_employee==1"
		}
	],
	"Payroll Entry": [
		{
			"fieldname": "payroll_type",
			"fieldtype": "Select",
			"label": "Payroll Type",
			"options": "Internal Employees\nOutsourced Employees",
			"default": "Internal Employees",
			"insert_after": "payroll_frequency",
			"reqd": 1,
			"in_list_view": 1
		}
	],
	"Salary Slip": [
		{
			"fieldname": "outsourced_payroll_section",
			"fieldtype": "Section Break",
			"label": "Outsourced Details",
			"insert_after": "total_working_days"
		},
		{
			"fieldname": "is_outsourced_employee",
			"fieldtype": "Check",
			"label": "Outsourced Employee",
			"insert_after": "outsourced_payroll_section",
			"read_only": 1
		},
		{
			"fieldname": "manpower_supplier",
			"fieldtype": "Link",
			"label": "Manpower Supplier",
			"options": "Supplier",
			"insert_after": "is_outsourced_employee",
			"read_only": 1
		},
		{
			"fieldname": "vendor_employee_id",
			"fieldtype": "Data",
			"label": "Vendor Employee ID",
			"insert_after": "manpower_supplier",
			"read_only": 1
		},
		{
			"fieldname": "column_break_outsourced_ss",
			"fieldtype": "Column Break",
			"insert_after": "vendor_employee_id"
		},
		{
			"fieldname": "outsourced_payroll_summary",
			"fieldtype": "Link",
			"label": "Outsourced Payroll Summary",
			"options": "Outsourced Payroll Summary",
			"insert_after": "column_break_outsourced_ss",
			"read_only": 1
		},
		{
			"fieldname": "vendor_billing_status",
			"fieldtype": "Select",
			"label": "Vendor Billing Status",
			"options": "Not Applicable\nPending Invoice\nInvoiced\nCancelled",
			"default": "Not Applicable",
			"insert_after": "outsourced_payroll_summary",
			"read_only": 1
		}
	],
	"Purchase Invoice": [
		{
			"fieldname": "outsourced_payroll_section",
			"fieldtype": "Section Break",
			"label": "Outsourced Payroll Details",
			"insert_after": "remarks"
		},
		{
			"fieldname": "is_outsourced_payroll_invoice",
			"fieldtype": "Check",
			"label": "Is Outsourced Payroll Invoice",
			"insert_after": "outsourced_payroll_section",
			"default": "0"
		},
		{
			"fieldname": "outsourced_payroll_summary",
			"fieldtype": "Link",
			"label": "Outsourced Payroll Summary",
			"options": "Outsourced Payroll Summary",
			"insert_after": "is_outsourced_payroll_invoice",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1"
		},
		{
			"fieldname": "payroll_period_from",
			"fieldtype": "Date",
			"label": "Payroll Period From",
			"insert_after": "outsourced_payroll_summary",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "payroll_period_to",
			"fieldtype": "Date",
			"label": "Payroll Period To",
			"insert_after": "payroll_period_from",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "column_break_outsourced_pi",
			"fieldtype": "Column Break",
			"insert_after": "payroll_period_to"
		},
		{
			"fieldname": "payroll_amount",
			"fieldtype": "Currency",
			"label": "Payroll Amount",
			"insert_after": "column_break_outsourced_pi",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "vendor_service_charge",
			"fieldtype": "Currency",
			"label": "Vendor Service Charge",
			"insert_after": "payroll_amount",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "other_charges",
			"fieldtype": "Currency",
			"label": "Other Charges",
			"insert_after": "vendor_service_charge",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "payroll_variance",
			"fieldtype": "Currency",
			"label": "Payroll Variance",
			"insert_after": "other_charges",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "employee_count",
			"fieldtype": "Int",
			"label": "Employee Count",
			"insert_after": "payroll_variance",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1",
			"read_only": 1
		},
		{
			"fieldname": "variance_reason",
			"fieldtype": "Select",
			"label": "Variance Reason",
			"options": "\nOvertime\nAdditional Employee\nAttendance Adjustment\nRate Difference\nService Charge\nOther",
			"insert_after": "employee_count",
			"depends_on": "eval:doc.is_outsourced_payroll_invoice==1 && doc.payroll_variance != 0"
		}
	]
}


def setup_senior_care():
	"""Ensures required Senior Care roles, custom fields, and accounts exist."""
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1
			}).insert(ignore_permissions=True)

	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
	setup_default_accounts()


def setup_default_accounts():
	"""Ensures default outsourced payroll accounts exist for all companies."""
	for company in frappe.get_all("Company", pluck="name"):
		get_outsourced_payroll_clearing_account(company)
		get_outsourced_manpower_expense_account(company)
		get_manpower_service_charge_account(company)


def get_outsourced_payroll_clearing_account(company):
	acc_name = f"Outsourced Payroll Clearing - {frappe.get_cached_value('Company', company, 'abbr')}"
	account = frappe.db.get_value("Account", {"account_name": "Outsourced Payroll Clearing", "company": company})
	if not account:
		parent = frappe.db.get_value("Account", {"account_type": "Payable", "company": company, "is_group": 1})
		if not parent:
			parent = frappe.db.get_value("Account", {"root_type": "Liability", "company": company, "is_group": 1})

		doc = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Outsourced Payroll Clearing",
			"company": company,
			"parent_account": parent,
			"root_type": "Liability"
		})
		doc.insert(ignore_permissions=True)
		account = doc.name
	else:
		# Ensure account_type is empty as required by HRMS payroll_payable_account validation
		frappe.db.set_value("Account", account, "account_type", "")
	return account


def get_outsourced_manpower_expense_account(company):
	account = frappe.db.get_value("Account", {"account_name": "Outsourced Manpower Expense", "company": company})
	if not account:
		parent = frappe.db.get_value("Account", {"root_type": "Expense", "company": company, "is_group": 1})
		doc = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Outsourced Manpower Expense",
			"company": company,
			"parent_account": parent,
			"account_type": "Direct Expense",
			"root_type": "Expense"
		})
		doc.insert(ignore_permissions=True)
		account = doc.name
	return account


def get_manpower_service_charge_account(company):
	account = frappe.db.get_value("Account", {"account_name": "Manpower Service Charges", "company": company})
	if not account:
		parent = frappe.db.get_value("Account", {"root_type": "Expense", "company": company, "is_group": 1})
		doc = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Manpower Service Charges",
			"company": company,
			"parent_account": parent,
			"account_type": "Direct Expense",
			"root_type": "Expense"
		})
		doc.insert(ignore_permissions=True)
		account = doc.name
	return account
