# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from hrms.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry
from seniorcare.setup import (
	get_outsourced_manpower_expense_account,
	get_outsourced_payroll_clearing_account,
)


class CustomPayrollEntry(PayrollEntry):
	def validate(self):
		self.set_payroll_payable_account_by_type()
		self.validate_company_cost_center()
		super().validate()

	def validate_company_cost_center(self):
		if self.company and self.cost_center:
			cc_company = frappe.db.get_value("Cost Center", self.cost_center, "company")
			if cc_company and cc_company != self.company:
				self.cost_center = self.get_valid_company_cost_center()

	def get_valid_company_cost_center(self, candidate=None):
		if candidate and frappe.db.get_value("Cost Center", candidate, "company") == self.company:
			return candidate
		if self.cost_center and frappe.db.get_value("Cost Center", self.cost_center, "company") == self.company:
			return self.cost_center
		company_cc = frappe.get_cached_value("Company", self.company, "cost_center")
		if company_cc and frappe.db.get_value("Cost Center", company_cc, "company") == self.company:
			return company_cc
		return frappe.db.get_value("Cost Center", {"company": self.company, "is_group": 0})

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

	def create_salary_slips(self):
		super().create_salary_slips()
		if self.docstatus == 1 and self.payroll_type == "Outsourced Employees":
			self.auto_process_outsourced_payroll()

	def get_salary_component_account(self, salary_component):
		if self.payroll_type == "Outsourced Employees":
			account = frappe.db.get_value(
				"Salary Component Account",
				{"parent": salary_component, "company": self.company},
				"account",
				cache=True,
			)
			if not account:
				account = get_outsourced_manpower_expense_account(self.company)
			return account
		return super().get_salary_component_account(salary_component)

	def set_journal_entry_in_salary_slips(self, submitted_salary_slips, jv_name=None):
		if not submitted_salary_slips:
			return
		slip_names = []
		for s in submitted_salary_slips:
			if isinstance(s, str):
				slip_names.append(s)
			elif isinstance(s, dict):
				slip_names.append(s.get("name"))
			elif hasattr(s, "name"):
				slip_names.append(s.name)
		slip_names = [name for name in slip_names if name]
		if slip_names:
			SalarySlip = frappe.qb.DocType("Salary Slip")
			(
				frappe.qb.update(SalarySlip)
				.set(SalarySlip.journal_entry, jv_name)
				.where(SalarySlip.name.isin(slip_names))
			).run()

	@frappe.whitelist()
	def auto_process_outsourced_payroll(self):
		"""
		Auto-submits draft salary slips, creates Accrual Journal Entry in Outsourced Payroll Clearing account,
		and generates Outsourced Payroll Summary documents.
		"""
		if self.payroll_type != "Outsourced Employees":
			return

		frappe.flags.in_auto_process_outsourced_payroll = True
		try:
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
			submitted_slips = frappe.get_all(
				"Salary Slip",
				filters={"payroll_entry": self.name, "docstatus": 1},
				fields=["name", "employee", "net_pay", "gross_pay", "manpower_supplier"],
			)
			if submitted_slips:
				self.make_accrual_jv_entry(submitted_salary_slips=submitted_slips)
			else:
				create_outsourced_payroll_summaries_for_payroll_entry(self.name)
		finally:
			frappe.flags.in_auto_process_outsourced_payroll = False

	@frappe.whitelist()
	def make_accrual_jv_entry(self, submitted_salary_slips=None):
		if self.payroll_type != "Outsourced Employees":
			if not submitted_salary_slips:
				submitted_salary_slips = frappe.get_all(
					"Salary Slip",
					filters={"payroll_entry": self.name, "docstatus": 1},
					fields=["name", "employee", "net_pay", "gross_pay"],
				)
			if not submitted_salary_slips:
				frappe.throw(_("No submitted salary slips found for this Payroll Entry."), title=_("No Salary Slips"))
			return super().make_accrual_jv_entry(submitted_salary_slips=submitted_salary_slips)

		# Outsourced Employees accrual entry logic
		if not submitted_salary_slips:
			submitted_salary_slips = frappe.get_all(
				"Salary Slip",
				filters={"payroll_entry": self.name, "docstatus": 1},
				fields=["name", "employee", "net_pay", "gross_pay", "manpower_supplier"],
			)

		if not submitted_salary_slips:
			# If no slips are submitted yet, check for draft slips and submit them
			draft_slips = frappe.get_all(
				"Salary Slip",
				filters={"payroll_entry": self.name, "docstatus": 0},
				pluck="name",
			)
			if draft_slips:
				frappe.flags.in_auto_process_outsourced_payroll = True
				try:
					for ss_name in draft_slips:
						ss_doc = frappe.get_doc("Salary Slip", ss_name)
						if ss_doc.net_pay >= 0:
							ss_doc.submit()
				finally:
					frappe.flags.in_auto_process_outsourced_payroll = False

				submitted_salary_slips = frappe.get_all(
					"Salary Slip",
					filters={"payroll_entry": self.name, "docstatus": 1},
					fields=["name", "employee", "net_pay", "gross_pay", "manpower_supplier"],
				)

		if not submitted_salary_slips:
			frappe.msgprint(_("No submitted salary slips found for this Payroll Entry."), title=_("No Salary Slips"))
			return None

		# Check if an Accrual Journal Entry already exists for this payroll entry
		existing_jv = frappe.db.get_value(
			"Journal Entry Account",
			{"reference_type": "Payroll Entry", "reference_name": self.name, "docstatus": 1},
			"parent",
		)
		if existing_jv:
			self.set_journal_entry_in_salary_slips(submitted_salary_slips, jv_name=existing_jv)
			create_outsourced_payroll_summaries_for_payroll_entry(self.name)
			return existing_jv

		# Build Journal Entry accounts
		default_expense_account = get_outsourced_manpower_expense_account(self.company)
		clearing_account = self.payroll_payable_account or get_outsourced_payroll_clearing_account(self.company)
		if not clearing_account:
			clearing_account = get_outsourced_payroll_clearing_account(self.company)

		default_cost_center = self.get_valid_company_cost_center()

		debit_entries = {}
		total_payable_amount = 0.0

		for ss in submitted_salary_slips:
			ss_name = ss.name if hasattr(ss, "name") else (ss.get("name") if isinstance(ss, dict) else str(ss))
			ss_doc = frappe.get_doc("Salary Slip", ss_name)
			amount = flt(ss_doc.net_pay)
			if amount <= 0:
				continue

			total_payable_amount += amount

			# Determine Expense Account and Cost Center for this salary slip
			supplier = ss_doc.manpower_supplier
			supplier_expense_acc = None
			supplier_cost_center = None
			if supplier:
				supplier_expense_acc, supplier_cost_center = frappe.db.get_value(
					"Supplier", supplier, ["default_outsourced_expense_account", "default_cost_center"]
				) or (None, None)

			emp_cost_center = frappe.db.get_value("Employee", ss_doc.employee, "payroll_cost_center")

			if supplier_expense_acc and frappe.db.get_value("Account", supplier_expense_acc, "company") == self.company:
				expense_account = supplier_expense_acc
			else:
				expense_account = default_expense_account

			cost_center = self.get_valid_company_cost_center(candidate=supplier_cost_center or emp_cost_center)

			key = (expense_account, cost_center)
			debit_entries[key] = debit_entries.get(key, 0.0) + amount

		if total_payable_amount <= 0:
			frappe.msgprint(_("Total payable amount is 0. No Journal Entry needed."))
			return None

		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency") or 2
		accounts = []

		# Add Debit Entries (Outsourced Manpower Expense)
		for (acc, cc), amt in debit_entries.items():
			accounts.append({
				"account": acc,
				"cost_center": cc,
				"debit_in_account_currency": flt(amt, precision),
				"credit_in_account_currency": 0.0,
				"exchange_rate": flt(self.exchange_rate or 1.0),
				"project": self.project or None,
			})

		# Add Credit Entry (Outsourced Payroll Clearing)
		accounts.append({
			"account": clearing_account,
			"cost_center": default_cost_center,
			"debit_in_account_currency": 0.0,
			"credit_in_account_currency": flt(total_payable_amount, precision),
			"exchange_rate": flt(self.exchange_rate or 1.0),
			"reference_type": "Payroll Entry",
			"reference_name": self.name,
			"project": self.project or None,
		})

		# Create and Submit Journal Entry
		jv = frappe.new_doc("Journal Entry")
		jv.voucher_type = "Journal Entry"
		jv.company = self.company
		jv.posting_date = self.posting_date
		jv.user_remark = _("Accrual Journal Entry for outsourced payroll from {0} to {1}").format(
			self.start_date, self.end_date
		)
		jv.party_not_required = True
		jv.set("accounts", accounts)
		jv.save(ignore_permissions=True)
		jv.submit()

		# Link JV to Salary Slips
		self.set_journal_entry_in_salary_slips(submitted_salary_slips, jv_name=jv.name)

		# Update Payroll Entry flags
		self.db_set({
			"salary_slips_submitted": 1,
			"status": "Submitted",
			"error_message": ""
		})

		# Generate Outsourced Payroll Summaries
		create_outsourced_payroll_summaries_for_payroll_entry(self.name)

		return jv.name

	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Salary Slip",
			"Journal Entry",
			"Outsourced Payroll Summary",
			"Outsourced Payroll Employee",
		)
		# Delete linked Outsourced Payroll Summaries so salary slips can be cleanly deleted
		summaries = frappe.get_all(
			"Outsourced Payroll Summary",
			filters={"payroll_entry": self.name},
			pluck="name",
		)
		for s_name in summaries:
			frappe.delete_doc("Outsourced Payroll Summary", s_name, force=True, ignore_permissions=True)

		super().on_cancel()


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
