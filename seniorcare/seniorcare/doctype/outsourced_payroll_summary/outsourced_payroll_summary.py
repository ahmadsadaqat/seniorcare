# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class OutsourcedPayrollSummary(Document):
	def validate(self):
		self.validate_dates()
		self.validate_duplicate_summary()
		self.calculate_totals()
		self.set_status()

	def validate_dates(self):
		if self.payroll_period_from and self.payroll_period_to:
			if getdate(self.payroll_period_from) > getdate(self.payroll_period_to):
				frappe.throw(_("Payroll Period From cannot be after Payroll Period To."))

	def validate_duplicate_summary(self):
		existing = frappe.db.get_value(
			"Outsourced Payroll Summary",
			{
				"company": self.company,
				"supplier": self.supplier,
				"payroll_period_from": self.payroll_period_from,
				"payroll_period_to": self.payroll_period_to,
				"docstatus": ["!=", 2],
				"name": ["!=", self.name],
			},
			"name",
		)
		if existing:
			frappe.throw(
				_("An Outsourced Payroll Summary ({0}) already exists for Company: {1}, Supplier: {2}, and Period: {3} to {4}.").format(
					existing, self.company, self.supplier, self.payroll_period_from, self.payroll_period_to
				),
				title=_("Duplicate Summary"),
			)

	def calculate_totals(self):
		self.total_employees = len(self.employees)
		self.payroll_amount = sum(flt(emp.net_payroll) for emp in self.employees)
		self.vendor_invoice_amount = (
			flt(self.payroll_amount)
			+ flt(self.vendor_service_charge)
			+ flt(self.other_charges)
			+ flt(self.tax_amount)
		)
		self.variance = flt(self.vendor_invoice_amount) - (
			flt(self.payroll_amount)
			+ flt(self.vendor_service_charge)
			+ flt(self.other_charges)
			+ flt(self.tax_amount)
		)

	def set_status(self):
		if self.purchase_invoice:
			if frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "docstatus") == 1:
				self.status = "Completed"
			else:
				self.status = "Invoice Received"
		elif self.total_employees > 0 and self.status == "Draft":
			self.status = "Pending Invoice"

	@frappe.whitelist()
	def fetch_salary_slips(self):
		if not self.company or not self.supplier or not self.payroll_period_from or not self.payroll_period_to:
			frappe.throw(_("Company, Supplier, and Payroll Period dates are required to fetch salary slips."))

		filters = {
			"company": self.company,
			"manpower_supplier": self.supplier,
			"docstatus": 1,
			"is_outsourced_employee": 1,
			"start_date": [">=", self.payroll_period_from],
			"end_date": ["<=", self.payroll_period_to],
		}
		if self.payroll_entry:
			filters["payroll_entry"] = self.payroll_entry

		salary_slips = frappe.get_all(
			"Salary Slip",
			filters=filters,
			fields=[
				"name",
				"employee",
				"employee_name",
				"vendor_employee_id",
				"manpower_supplier",
				"gross_pay",
				"total_deduction",
				"net_pay",
				"payment_days",
				"total_working_days",
			],
		)

		if not salary_slips:
			frappe.msgprint(_("No submitted outsourced Salary Slips found matching the selected criteria."))
			return

		self.set("employees", [])
		for ss in salary_slips:
			self.append(
				"employees",
				{
					"employee": ss.employee,
					"employee_name": ss.employee_name,
					"vendor_employee_id": ss.vendor_employee_id,
					"supplier": ss.manpower_supplier,
					"salary_slip": ss.name,
					"gross_earnings": ss.gross_pay,
					"total_deductions": ss.total_deduction,
					"net_payroll": ss.net_pay,
					"attendance_days": ss.payment_days,
					"working_days": ss.total_working_days,
					"total_vendor_amount": ss.net_pay,
				},
			)

		self.calculate_totals()
		self.set_status()
		self.save()

		# Update linked salary slips with this summary and status
		for ss in salary_slips:
			frappe.db.set_value(
				"Salary Slip",
				ss.name,
				{
					"outsourced_payroll_summary": self.name,
					"vendor_billing_status": "Pending Invoice",
				},
			)

		frappe.msgprint(_("Successfully fetched {0} salary slips.").format(len(salary_slips)))

	@frappe.whitelist()
	def make_purchase_invoice(self):
		if self.purchase_invoice:
			pi_docstatus = frappe.db.get_value("Purchase Invoice", self.purchase_invoice, "docstatus")
			if pi_docstatus != 2:
				frappe.throw(
					_("Purchase Invoice {0} is already linked to this summary.").format(self.purchase_invoice)
				)

		from seniorcare.setup import get_outsourced_payroll_clearing_account, get_manpower_service_charge_account

		clearing_account = get_outsourced_payroll_clearing_account(self.company)
		service_charge_account = get_manpower_service_charge_account(self.company)

		pi = frappe.new_doc("Purchase Invoice")
		pi.supplier = self.supplier
		pi.company = self.company
		pi.posting_date = self.posting_date or frappe.utils.nowdate()
		if self.supplier_invoice_no:
			pi.bill_no = self.supplier_invoice_no
		if self.supplier_invoice_date:
			pi.bill_date = self.supplier_invoice_date
		pi.is_outsourced_payroll_invoice = 1
		pi.outsourced_payroll_summary = self.name
		pi.payroll_period_from = self.payroll_period_from
		pi.payroll_period_to = self.payroll_period_to
		pi.payroll_amount = self.payroll_amount
		pi.vendor_service_charge = self.vendor_service_charge
		pi.other_charges = self.other_charges
		pi.payroll_variance = self.variance
		pi.employee_count = self.total_employees
		pi.remarks = self.remarks or _("Outsourced Payroll Invoice for {0} to {1}").format(
			self.payroll_period_from, self.payroll_period_to
		)

		# Add items
		if flt(self.payroll_amount) > 0:
			desc = f"Outsourced Manpower Payroll ({self.payroll_period_from} to {self.payroll_period_to})"
			pi.append(
				"items",
				{
					"item_name": desc,
					"description": desc,
					"qty": 1,
					"rate": self.payroll_amount,
					"amount": self.payroll_amount,
					"expense_account": clearing_account,
				},
			)

		if flt(self.vendor_service_charge) > 0:
			desc = f"Manpower Service Charge ({self.payroll_period_from} to {self.payroll_period_to})"
			pi.append(
				"items",
				{
					"item_name": desc,
					"description": desc,
					"qty": 1,
					"rate": self.vendor_service_charge,
					"amount": self.vendor_service_charge,
					"expense_account": service_charge_account,
				},
			)

		if flt(self.other_charges) > 0:
			desc = f"Other Manpower Charges ({self.payroll_period_from} to {self.payroll_period_to})"
			pi.append(
				"items",
				{
					"item_name": desc,
					"description": desc,
					"qty": 1,
					"rate": self.other_charges,
					"amount": self.other_charges,
					"expense_account": service_charge_account,
				},
			)

		if flt(self.tax_amount) > 0:
			tax_account = frappe.db.get_value("Account", {"account_type": "Tax", "company": self.company})
			if not tax_account:
				tax_account = service_charge_account
			pi.append(
				"taxes",
				{
					"charge_type": "Actual",
					"account_head": tax_account,
					"description": "Input VAT / Tax",
					"tax_amount": self.tax_amount,
				},
			)

		pi.flags.ignore_mandatory = True
		pi.insert(ignore_permissions=True)

		self.db_set("purchase_invoice", pi.name)
		self.db_set("status", "Invoice Received")

		return pi.name
