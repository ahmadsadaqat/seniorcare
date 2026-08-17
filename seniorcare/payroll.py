# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from seniorcare.setup import get_outsourced_payroll_clearing_account


class CustomPayrollEntry(PayrollEntry):
	@frappe.whitelist()
	def fill_employee_details(self):
		res = super().fill_employee_details()

		if not self.employees:
			return res

		# Fetch is_outsourced_employee state for fetched employees
		emp_names = [e.employee for e in self.employees]
		outsourced_map = dict(
			frappe.db.get_values(
				"Employee",
				{"name": ["in", emp_names]},
				["name", "is_outsourced_employee"],
			)
			or []
		)

		if self.payroll_type == "Internal Employees":
			filtered = [e for e in self.employees if not outsourced_map.get(e.employee)]
		elif self.payroll_type == "Outsourced Employees":
			filtered = [e for e in self.employees if outsourced_map.get(e.employee)]
		else:
			filtered = self.employees

		if not filtered and self.payroll_type != "All Employees":
			frappe.throw(
				_("No employees found matching Payroll Type '{0}' for the specified filters.").format(
					self.payroll_type
				),
				title=_("No Employees Found"),
			)

		self.set("employees", filtered)
		self.number_of_employees = len(self.employees)
		return res

	def before_submit(self):
		if self.payroll_type == "Outsourced Employees":
			clearing_acc = get_outsourced_payroll_clearing_account(self.company)
			if clearing_acc and self.payroll_payable_account != clearing_acc:
				self.payroll_payable_account = clearing_acc

		super().before_submit()


@frappe.whitelist()
def create_outsourced_payroll_summaries_for_payroll_entry(payroll_entry_name):
	pe = frappe.get_doc("Payroll Entry", payroll_entry_name)
	slips = frappe.get_all(
		"Salary Slip",
		filters={"payroll_entry": payroll_entry_name, "docstatus": 1, "is_outsourced_employee": 1},
		fields=["name", "manpower_supplier", "company", "start_date", "end_date"],
	)
	if not slips:
		return []

	suppliers = set(s.manpower_supplier for s in slips if s.manpower_supplier)
	created_summaries = []
	for supplier in suppliers:
		existing = frappe.db.get_value(
			"Outsourced Payroll Summary",
			{
				"payroll_entry": payroll_entry_name,
				"supplier": supplier,
				"docstatus": ["!=", 2],
			},
			"name",
		)
		if existing:
			created_summaries.append(existing)
			continue

		summary = frappe.new_doc("Outsourced Payroll Summary")
		summary.company = pe.company
		summary.supplier = supplier
		summary.payroll_entry = pe.name
		summary.payroll_period_from = pe.start_date
		summary.payroll_period_to = pe.end_date
		summary.posting_date = frappe.utils.nowdate()
		summary.insert(ignore_permissions=True)
		summary.fetch_salary_slips()
		created_summaries.append(summary.name)

	return created_summaries
