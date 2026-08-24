# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def validate_payment_entry(doc, method=None):
	"""Validates Senior Care specific fields, accounts, and refund balances on Payment Entry."""
	if not doc.custom_payment_purpose or doc.custom_payment_purpose == "Normal Payment":
		return

	# Ensure resident customer is mapped
	if not doc.custom_resident:
		if doc.party_type == "Customer" and doc.party:
			doc.custom_resident = doc.party
		else:
			frappe.throw(frappe._("Resident (Customer) is mandatory for Senior Care transactions."))

	# Validate funding source
	if doc.custom_payment_purpose in ["Resident Medical Expense", "Resident Personal Expense"]:
		if not doc.custom_funding_source:
			frappe.throw(frappe._("Funding Source is mandatory for {0}.").format(doc.custom_payment_purpose))

	# Auto-populate configured accounts from Senior Care Settings
	populate_senior_care_accounts(doc)

	# Validate available balances for advance usage and refunds
	validate_balances_for_transaction(doc)


def populate_senior_care_accounts(doc):
	"""Auto-fills default liability and expense accounts from Senior Care Settings if not specified."""
	if not frappe.db.exists("DocType", "Senior Care Settings"):
		return

	settings = frappe.get_single("Senior Care Settings")

	if doc.custom_payment_purpose in ["Security Deposit", "Security Deposit Refund"]:
		if not doc.custom_security_deposit_liability_account:
			doc.custom_security_deposit_liability_account = settings.security_deposit_liability_account

	elif doc.custom_payment_purpose in ["Medical Advance", "Medical Advance Refund"]:
		if not doc.custom_medical_advance_liability_account:
			doc.custom_medical_advance_liability_account = settings.medical_advance_liability_account

	elif doc.custom_payment_purpose in ["Personal Advance", "Personal Advance Refund"]:
		if not doc.custom_personal_advance_liability_account:
			doc.custom_personal_advance_liability_account = settings.personal_advance_liability_account

	elif doc.custom_payment_purpose == "Resident Medical Expense":
		if not doc.custom_medical_expense_account:
			doc.custom_medical_expense_account = settings.medical_expense_account
		if doc.custom_funding_source == "Resident Medical Advance" and not doc.custom_medical_advance_liability_account:
			doc.custom_medical_advance_liability_account = settings.medical_advance_liability_account

	elif doc.custom_payment_purpose == "Resident Personal Expense":
		if not doc.custom_personal_expense_account:
			doc.custom_personal_expense_account = settings.personal_expense_account
		if doc.custom_funding_source == "Resident Personal Advance" and not doc.custom_personal_advance_liability_account:
			doc.custom_personal_advance_liability_account = settings.personal_advance_liability_account


def validate_balances_for_transaction(doc):
	"""Ensures refunds and advance utilizations do not exceed available resident balances."""
	res_name = frappe.db.get_value("Resident File", {"customer": doc.custom_resident})
	if not res_name:
		return

	res_doc = frappe.get_doc("Resident File", res_name)
	res_doc.update_financial_summaries()

	amount = flt(doc.paid_amount or doc.received_amount)

	if doc.custom_payment_purpose == "Security Deposit Refund":
		avail = flt(res_doc.security_deposit_balance)
		if amount > avail:
			frappe.throw(frappe._("Security Deposit Refund amount ({0}) cannot exceed available Security Deposit balance ({1}) for {2}.").format(
				amount, avail, res_doc.full_name
			))

	elif doc.custom_payment_purpose == "Medical Advance Refund":
		avail = flt(res_doc.medical_advance_balance)
		if amount > avail:
			frappe.throw(frappe._("Medical Advance Refund amount ({0}) cannot exceed available Medical Advance balance ({1}) for {2}.").format(
				amount, avail, res_doc.full_name
			))

	elif doc.custom_payment_purpose == "Personal Advance Refund":
		avail = flt(res_doc.personal_advance_balance)
		if amount > avail:
			frappe.throw(frappe._("Personal Advance Refund amount ({0}) cannot exceed available Personal Advance balance ({1}) for {2}.").format(
				amount, avail, res_doc.full_name
			))

	elif doc.custom_payment_purpose == "Resident Medical Expense" and doc.custom_funding_source == "Resident Medical Advance":
		avail = flt(res_doc.medical_advance_balance)
		if amount > avail:
			frappe.throw(frappe._("Medical Expense amount ({0}) cannot exceed resident's available Medical Advance balance ({1}) for {2}.").format(
				amount, avail, res_doc.full_name
			))

	elif doc.custom_payment_purpose == "Resident Personal Expense" and doc.custom_funding_source == "Resident Personal Advance":
		avail = flt(res_doc.personal_advance_balance)
		if amount > avail:
			frappe.throw(frappe._("Personal Expense amount ({0}) cannot exceed resident's available Personal Advance balance ({1}) for {2}.").format(
				amount, avail, res_doc.full_name
			))


def on_submit_payment_entry(doc, method=None):
	"""Creates offsetting Journal Entries for advance utilization and refreshes resident financial balances."""
	if not doc.custom_payment_purpose or doc.custom_payment_purpose == "Normal Payment":
		return

	amount = flt(doc.paid_amount or doc.received_amount)

	# 1. Dual entry for Resident Medical Expense funded by Advance
	if doc.custom_payment_purpose == "Resident Medical Expense" and doc.custom_funding_source == "Resident Medical Advance":
		if doc.custom_medical_advance_liability_account and doc.custom_medical_expense_account:
			je = frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": doc.company,
				"posting_date": doc.posting_date,
				"user_remarks": f"Advance utilization for {doc.custom_resident} against Medical Expense Payment Entry {doc.name}",
				"accounts": [
					{
						"account": doc.custom_medical_advance_liability_account,
						"debit_in_account_currency": amount,
						"credit_in_account_currency": 0
					},
					{
						"account": doc.custom_medical_expense_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": amount
					}
				]
			})
			je.insert(ignore_permissions=True)
			je.submit()
			doc.db_set("custom_linked_journal_entry", je.name)

	# 2. Dual entry for Resident Personal Expense funded by Advance
	elif doc.custom_payment_purpose == "Resident Personal Expense" and doc.custom_funding_source == "Resident Personal Advance":
		if doc.custom_personal_advance_liability_account and doc.custom_personal_expense_account:
			je = frappe.get_doc({
				"doctype": "Journal Entry",
				"voucher_type": "Journal Entry",
				"company": doc.company,
				"posting_date": doc.posting_date,
				"user_remarks": f"Advance utilization for {doc.custom_resident} against Personal Expense Payment Entry {doc.name}",
				"accounts": [
					{
						"account": doc.custom_personal_advance_liability_account,
						"debit_in_account_currency": amount,
						"credit_in_account_currency": 0
					},
					{
						"account": doc.custom_personal_expense_account,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": amount
					}
				]
			})
			je.insert(ignore_permissions=True)
			je.submit()
			doc.db_set("custom_linked_journal_entry", je.name)

	# Refresh linked Resident File
	sync_resident_financial_summaries(doc.custom_resident)


def on_cancel_payment_entry(doc, method=None):
	"""Cancels any auto-generated Journal Entry and recalculates resident financial balances."""
	if doc.custom_linked_journal_entry and frappe.db.exists("Journal Entry", doc.custom_linked_journal_entry):
		je = frappe.get_doc("Journal Entry", doc.custom_linked_journal_entry)
		if je.docstatus == 1:
			je.cancel()

	sync_resident_financial_summaries(doc.custom_resident)


def sync_resident_financial_summaries(customer):
	if not customer:
		return
	res_name = frappe.db.get_value("Resident File", {"customer": customer})
	if res_name:
		res_doc = frappe.get_doc("Resident File", res_name)
		res_doc.update_financial_summaries()
		res_doc.save(ignore_permissions=True)
