# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from seniorcare.setup import get_outsourced_payroll_clearing_account


class CustomPayrollEntry(PayrollEntry):
	def validate(self):
		self.set_payroll_payable_account_by_type()
		super().validate()

	def set_payroll_payable_account_by_type(self):
		if not self.company:
			return
		if self.payroll_type == "Outsourced Employees":
			clearing_acc = get_outsourced_payroll_clearing_account(self.company)
			if clearing_acc:
				self.payroll_payable_account = clearing_acc
		elif self.payroll_type == "Internal Employees":
			internal_acc = frappe.get_cached_value("Company", self.company, "default_payroll_payable_account")
			clearing_acc = get_outsourced_payroll_clearing_account(self.company)
			if internal_acc and (not self.payroll_payable_account or self.payroll_payable_account == clearing_acc):
				self.payroll_payable_account = internal_acc

	@frappe.whitelist()
	def fill_employee_details(self):
		self.set_payroll_payable_account_by_type()
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

		if not filtered:
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
		self.set_payroll_payable_account_by_type()
		super().before_submit()

	def on_submit(self):
		super().on_submit()
		if self.payroll_type == "Outsourced Employees":
			self.auto_process_outsourced_payroll()

	@frappe.whitelist()
	def auto_process_outsourced_payroll(self):
		"""
		Auto-submits draft salary slips, creates Accrual Journal Entry in Outsourced Payroll Clearing account,
		and generates Outsourced Payroll Summary documents.
		"""
		if self.payroll_type != "Outsourced Employees":
			return

		# 1. Submit draft salary slips
		draft_slips = frappe.get_all(
			"Salary Slip",
			filters={"payroll_entry": self.name, "docstatus": 0},
			pluck="name",
		)
		for ss_name in draft_slips:
			ss_doc = frappe.get_doc("Salary Slip", ss_name)
			if ss_doc.net_pay >= 0:
				ss_doc.submit()

		# 2. Check if Accrual Entry already exists for this payroll entry
		existing_jv = frappe.db.get_value(
			"Journal Entry Account",
			{"reference_type": "Payroll Entry", "reference_name": self.name, "docstatus": 1},
			"parent",
		)
		if not existing_jv:
			submitted_slips = frappe.get_all(
				"Salary Slip",
				filters={"payroll_entry": self.name, "docstatus": 1},
				fields=["name", "employee", "net_pay", "gross_pay"],
			)
			if submitted_slips:
				self.make_accrual_jv_entry(submitted_salary_slips=submitted_slips)

		# 3. Generate Outsourced Payroll Summaries
		create_outsourced_payroll_summaries_for_payroll_entry(self.name)

	@frappe.whitelist()
	def make_accrual_jv_entry(self, submitted_salary_slips=None):
		if not submitted_salary_slips:
			submitted_salary_slips = frappe.get_all(
				"Salary Slip",
				filters={"payroll_entry": self.name, "docstatus": 1},
				fields=["name", "employee", "net_pay", "gross_pay"],
			)
		if not submitted_salary_slips:
			frappe.throw(_("No submitted salary slips found for this Payroll Entry."), title=_("No Salary Slips"))

		return super().make_accrual_jv_entry(submitted_salary_slips=submitted_salary_slips)


@frappe.whitelist()
def get_payroll_payable_account_for_company(company, payroll_type):
	if not company:
		return ""
	if payroll_type == "Outsourced Employees":
		return get_outsourced_payroll_clearing_account(company)
	else:
		return frappe.get_cached_value("Company", company, "default_payroll_payable_account") or ""


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
