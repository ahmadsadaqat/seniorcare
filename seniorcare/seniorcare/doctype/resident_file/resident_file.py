# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today, flt


class ResidentFile(Document):
	def validate(self):
		self.set_full_name()
		self.validate_dates()
		self.create_or_link_customer()
		self.update_financial_summaries()
		self.update_medical_summaries()

	def set_full_name(self):
		if self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}".strip()
		else:
			self.full_name = self.first_name.strip()

	def validate_dates(self):
		if self.admission_date and self.exit_date:
			if getdate(self.exit_date) < getdate(self.admission_date):
				frappe.throw(frappe._("Exit Date cannot be earlier than Admission Date"))

	def create_or_link_customer(self):
		"""Ensures Resident File is linked to an ERPNext Customer for accounting party representation."""
		if not self.customer:
			customer_name = f"{self.full_name} (Resident)"
			if frappe.db.exists("Customer", customer_name):
				self.customer = customer_name
			else:
				# Create standard ERPNext Customer
				cust_group = frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual"
				territory = frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
				cust = frappe.get_doc({
					"doctype": "Customer",
					"customer_name": customer_name,
					"customer_group": cust_group,
					"territory": territory,
					"customer_type": "Individual"
				})
				cust.insert(ignore_permissions=True)
				self.customer = cust.name

	def update_financial_summaries(self):
		"""Derived financial calculations from active contracts and advances."""
		if self.customer:
			# Calculate outstanding receivable balance from ERPNext GL / Customer
			outstanding = frappe.db.get_value("Customer", self.customer, "outstanding_amount") or 0.0
			self.outstanding_receivable = flt(outstanding)

		# Sum remaining balances from submitted Resident Advances
		advances = frappe.db.get_all(
			"Resident Advance",
			filters={"resident_file": self.name, "docstatus": 1},
			fields=["advance_type", "remaining_balance"]
		)
		med_bal = sum(flt(a.remaining_balance) for a in advances if a.advance_type == "Medical Advance")
		pers_bal = sum(flt(a.remaining_balance) for a in advances if a.advance_type == "Personal Advance")

		self.medical_advance_balance = med_bal
		self.personal_advance_balance = pers_bal

	def update_medical_summaries(self):
		"""Consolidate active allergies, current medications, and medical history."""
		if not self.name or self.is_new():
			return

		# Active allergies summary
		allergies = frappe.db.get_all(
			"Resident Allergy",
			filters={"resident_file": self.name, "is_active": 1},
			pluck="allergy_substance"
		)
		if allergies:
			self.allergies_summary = ", ".join(allergies)

		# Current active medications summary
		meds = frappe.db.get_all(
			"Resident Medication",
			filters={"resident_file": self.name, "is_active": 1},
			fields=["medicine", "dose", "frequency"]
		)
		if meds:
			self.current_medication_summary = "; ".join(
				[f"{m.medicine} ({m.dose or ''} {m.frequency or ''})".strip() for m in meds]
			)

		# Recent Medical History summary
		history = frappe.db.get_all(
			"Resident Medical History",
			filters={"resident_file": self.name},
			order_by="date_diagnosed desc",
			limit=5,
			pluck="condition_diagnosis"
		)
		if history:
			self.medical_history_summary = ", ".join(history)


@frappe.whitelist()
def get_resident_dashboard_data(resident_name):
	"""Returns quick summary statistics for desk view."""
	doc = frappe.get_doc("Resident File", resident_name)
	return {
		"customer": doc.customer,
		"status": doc.status,
		"room_unit": doc.room_unit,
		"current_contract": doc.current_contract,
		"next_appointment_date": doc.next_appointment_date,
		"medical_advance_balance": doc.medical_advance_balance,
		"personal_advance_balance": doc.personal_advance_balance,
		"outstanding_receivable": doc.outstanding_receivable
	}
