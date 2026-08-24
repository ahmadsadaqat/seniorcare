# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, get_first_day, get_last_day, today


def create_monthly_invoices():
	"""Scheduled job called daily. Automatically creates Draft Sales Invoices for active residents on 1st of month."""
	curr_date = getdate(today())
	settings = frappe.get_single("Senior Care Settings") if frappe.db.exists("DocType", "Senior Care Settings") else None
	billing_day = int(settings.default_billing_day or 1) if settings else 1

	# Only execute on the designated billing day of the month
	if curr_date.day != billing_day:
		return

	residents = frappe.get_all(
		"Resident File",
		filters={
			"resident_status": "Active",
			"auto_create_monthly_invoice": 1
		},
		fields=["name", "customer", "current_contract", "occupancy_fee", "attendant_fee", "other_fixed_charges"]
	)

	for res in residents:
		try:
			generate_resident_invoice(res.name, posting_date=today())
		except Exception as e:
			frappe.log_error(f"Error creating monthly invoice for resident {res.name}: {str(e)}", "Senior Care Monthly Billing")


@frappe.whitelist()
def generate_resident_invoice(resident_file, posting_date=None):
	"""Generates a Draft Sales Invoice for a single resident based on active contract charges."""
	if not resident_file:
		frappe.throw(frappe._("Resident File is required."))

	doc = frappe.get_doc("Resident File", resident_file)
	if not doc.customer:
		frappe.throw(frappe._("Resident {0} is not linked to an Accounting Customer.").format(doc.name))

	if not doc.current_contract:
		frappe.throw(frappe._("Resident {0} does not have an active contract.").format(doc.name))

	date_to_use = getdate(posting_date or today())
	first_day = get_first_day(date_to_use)
	last_day = get_last_day(date_to_use)

	# Check if an invoice was already generated for this billing period
	existing = frappe.db.sql("""
		SELECT name FROM `tabSales Invoice`
		WHERE customer = %(customer)s
		  AND docstatus < 2
		  AND posting_date BETWEEN %(from_date)s AND %(to_date)s
		  AND remarks LIKE %(remark)s
	""", {
		"customer": doc.customer,
		"from_date": first_day,
		"to_date": last_day,
		"remark": f"%Senior Care Monthly Billing for {doc.name}%"
	})

	if existing:
		return existing[0][0]

	company = frappe.db.get_single_value("Senior Care Settings", "company") or frappe.db.get_default("company") or frappe.get_all("Company", limit=1, pluck="name")[0]
	income_account = frappe.db.get_single_value("Senior Care Settings", "resident_income_account")

	if not income_account:
		from seniorcare.setup import get_resident_income_account
		income_account = get_resident_income_account(company)

	items = []
	month_name = date_to_use.strftime("%B %Y")

	# 1. Occupancy Fee
	if flt(doc.occupancy_fee) > 0:
		items.append({
			"item_name": f"Monthly Occupancy Fee - {month_name}",
			"description": f"Residential Occupancy Fee for {doc.full_name} for {month_name}",
			"qty": 1,
			"rate": flt(doc.occupancy_fee),
			"income_account": income_account
		})

	# 2. Attendant Fee
	if flt(doc.attendant_fee) > 0:
		items.append({
			"item_name": f"Monthly Attendant Fee - {month_name}",
			"description": f"Caregiver / Attendant Fee for {doc.full_name} for {month_name}",
			"qty": 1,
			"rate": flt(doc.attendant_fee),
			"income_account": income_account
		})

	# 3. Other Fixed Charges
	if flt(doc.other_fixed_charges) > 0:
		items.append({
			"item_name": f"Other Fixed Monthly Charges - {month_name}",
			"description": f"Other Fixed Facility Charges for {doc.full_name} for {month_name}",
			"qty": 1,
			"rate": flt(doc.other_fixed_charges),
			"income_account": income_account
		})

	if not items:
		frappe.throw(frappe._("No monthly fees found on Resident File or active contract."))

	inv = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": doc.customer,
		"company": company,
		"posting_date": date_to_use,
		"due_date": date_to_use,
		"remarks": f"Senior Care Monthly Billing for {doc.name} ({doc.full_name}) - {month_name}",
		"items": items
	})
	inv.insert(ignore_permissions=True)
	return inv.name
