# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today


class ResidentFile(Document):
	def validate(self):
		self.set_full_name()
		self.calculate_age()
		self.validate_dates()
		self.create_or_link_customer()
		self.update_emergency_contact_summary()
		self.handle_room_assignment()
		self.update_financial_summaries()
		self.update_incident_summary()
		self.sync_assigned_attendant_name()

	def sync_assigned_attendant_name(self):
		if self.assigned_attendant and not self.assigned_attendant_name:
			self.assigned_attendant_name = frappe.db.get_value("Employee", self.assigned_attendant, "employee_name")
		elif not self.assigned_attendant:
			self.assigned_attendant_name = None

	def set_full_name(self):
		if self.last_name:
			self.full_name = f"{self.first_name} {self.last_name}".strip()
		else:
			self.full_name = (self.first_name or "").strip()

	def calculate_age(self):
		if self.date_of_birth:
			dob = getdate(self.date_of_birth)
			current = getdate(today())
			age = current.year - dob.year - ((current.month, current.day) < (dob.month, dob.day))
			self.age = max(0, age)
		else:
			self.age = None

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

	def update_emergency_contact_summary(self):
		"""Derives emergency contact summary string from family_members with is_emergency_contact checked."""
		emergency_list = []
		for member in self.get("family_members", []):
			if member.is_emergency_contact:
				parts = [member.family_member_name]
				if member.relationship:
					parts.append(f"({member.relationship})")
				if member.phone:
					parts.append(f"Ph: {member.phone}")
				if member.whatsapp:
					parts.append(f"WA: {member.whatsapp}")
				emergency_list.append(" ".join(parts))

		if emergency_list:
			self.emergency_contact = " | ".join(emergency_list)
		elif self.family_members and not self.emergency_contact:
			# If none marked, default to primary or first member
			first = self.family_members[0]
			self.emergency_contact = f"{first.family_member_name} ({first.relationship or 'Family'}) Ph: {first.phone or ''}".strip()

	def handle_room_assignment(self):
		"""Syncs room occupancy status when room is assigned, changed, or discharged."""
		if not self.is_new():
			old_room = frappe.db.get_value("Resident File", self.name, "room_unit")
			if old_room and old_room != self.room_unit:
				if frappe.db.exists("Room", old_room):
					frappe.db.set_value("Room", old_room, {
						"occupancy_status": "Available",
						"current_resident": None
					})

		if self.room_unit and frappe.db.exists("Room", self.room_unit):
			if self.resident_status in ["Discharged", "Deceased"]:
				frappe.db.set_value("Room", self.room_unit, {
					"occupancy_status": "Available",
					"current_resident": None
				})
			else:
				frappe.db.set_value("Room", self.room_unit, {
					"occupancy_status": "Occupied",
					"current_resident": self.name
				})

	def update_financial_summaries(self):
		"""Calculates derived financial balances from submitted Payment Entries and Contract."""
		if self.customer:
			try:
				from erpnext.accounts.utils import get_balance_on
				self.outstanding_receivable = flt(get_balance_on(party_type="Customer", party=self.customer))
			except Exception:
				self.outstanding_receivable = 0.0

			# 1. Security Deposit
			# Received
			sec_rec = frappe.db.sql("""
				SELECT SUM(received_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Security Deposit'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.security_deposit_received = flt(sec_rec)

			# Refunded
			sec_ref = frappe.db.sql("""
				SELECT SUM(paid_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Security Deposit Refund'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.security_deposit_refunded = flt(sec_ref)

			self.security_deposit_balance = max(0.0, flt(self.security_deposit_received) - flt(self.security_deposit_used) - flt(self.security_deposit_refunded))

			# 2. Medical Advance
			med_rec = frappe.db.sql("""
				SELECT SUM(received_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Medical Advance'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			# Include contract initial medical advance if configured
			self.medical_advance_received = flt(med_rec) + flt(self.initial_medical_advance)

			med_used = frappe.db.sql("""
				SELECT SUM(paid_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Resident Medical Expense'
				  AND custom_funding_source = 'Resident Medical Advance'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.medical_advance_used = flt(med_used)

			med_ref = frappe.db.sql("""
				SELECT SUM(paid_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Medical Advance Refund'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.medical_advance_refunded = flt(med_ref)

			self.medical_advance_balance = max(0.0, flt(self.medical_advance_received) - flt(self.medical_advance_used) - flt(self.medical_advance_refunded))

			# 3. Personal Advance
			pers_rec = frappe.db.sql("""
				SELECT SUM(received_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Personal Advance'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.personal_advance_received = flt(pers_rec) + flt(self.initial_personal_advance)

			pers_used = frappe.db.sql("""
				SELECT SUM(paid_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Resident Personal Expense'
				  AND custom_funding_source = 'Resident Personal Advance'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.personal_advance_used = flt(pers_used)

			pers_ref = frappe.db.sql("""
				SELECT SUM(paid_amount)
				FROM `tabPayment Entry`
				WHERE docstatus = 1
				  AND custom_payment_purpose = 'Personal Advance Refund'
				  AND (party = %(cust)s OR custom_resident = %(cust)s)
			""", {"cust": self.customer})[0][0] or 0.0
			self.personal_advance_refunded = flt(pers_ref)

			self.personal_advance_balance = max(0.0, flt(self.personal_advance_received) - flt(self.personal_advance_used) - flt(self.personal_advance_refunded))

	def update_incident_summary(self):
		if not self.name or self.is_new():
			return
		incidents = frappe.db.count("Incident Report", {"resident_file": self.name, "docstatus": ["<", 2]})
		open_inc = frappe.db.count("Incident Report", {"resident_file": self.name, "status": "Open", "docstatus": ["<", 2]})
		self.incident_summary = f"Total Incidents: {incidents} | Open Incidents: {open_inc}"


@frappe.whitelist()
def refresh_resident_financials(resident_file):
	"""Manually triggers recalculation of financial balances from Payment Entries."""
	doc = frappe.get_doc("Resident File", resident_file)
	doc.update_financial_summaries()
	doc.save(ignore_permissions=True)
	return {
		"security_deposit_received": doc.security_deposit_received,
		"security_deposit_balance": doc.security_deposit_balance,
		"medical_advance_received": doc.medical_advance_received,
		"medical_advance_balance": doc.medical_advance_balance,
		"personal_advance_received": doc.personal_advance_received,
		"personal_advance_balance": doc.personal_advance_balance,
		"outstanding_receivable": doc.outstanding_receivable
	}
