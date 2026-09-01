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
		self.sync_family_members_flags()
		self.update_emergency_contact_summary()
		self.update_clinical_risks_status()
		self.handle_room_assignment()
		self.update_financial_summaries()
		self.update_incident_summary()
		self.sync_assigned_attendant_name()

	def sync_family_members_flags(self):
		"""Syncs family member flags (POA, Primary Contact, Billing Contact) to Resident File fields."""
		for fm in self.get("family_members", []):
			contact_str = f"{fm.family_member_name} ({fm.relationship or 'Family'}) - Ph: {fm.phone or ''}".strip()
			if fm.get("is_poa"):
				self.power_of_attorney = contact_str
			if fm.get("can_receive_updates"):
				self.primary_family_contact = contact_str
			if fm.get("can_approve_expenses"):
				self.payer_billing_contact = contact_str

	def update_clinical_risks_status(self):
		"""Auto-derives Active vs Expired status for clinical risk precautions based on end_date."""
		today_date = getdate(today())
		for prec in self.get("clinical_risk_precautions", []):
			if prec.end_date and getdate(prec.end_date) < today_date:
				prec.status = "Expired"
			else:
				prec.status = "Active"

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
			self.medical_advance_received = flt(med_rec)

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
			self.personal_advance_received = flt(pers_rec)

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
		"""Updates high-level incident stats for quick desk review."""
		if not self.is_new():
			counts = frappe.db.sql("""
				SELECT status, COUNT(*) as count
				FROM `tabIncident Report`
				WHERE resident_file = %(resident)s
				GROUP BY status
			""", {"resident": self.name}, as_dict=True)

			if counts:
				summary_parts = [f"{c.status}: {c.count}" for c in counts]
				self.incident_summary = ", ".join(summary_parts)
			else:
				self.incident_summary = "No incidents recorded"


@frappe.whitelist()
def refresh_resident_financials(resident_file):
	"""Explicit whitelist action for desk button to recalculate ledger and payment balances."""
	doc = frappe.get_doc("Resident File", resident_file)
	doc.update_financial_summaries()
	doc.save(ignore_permissions=True)
	return {
		"security_deposit_balance": doc.security_deposit_balance,
		"medical_advance_balance": doc.medical_advance_balance,
		"personal_advance_balance": doc.personal_advance_balance,
		"outstanding_receivable": doc.outstanding_receivable
	}


@frappe.whitelist()
def get_emergency_card_data(resident_file):
	"""Returns comprehensive structured data for generating the Emergency Medical Card."""
	doc = frappe.get_doc("Resident File", resident_file)

	doctor_info = None
	if doc.primary_doctor:
		doctor_info = frappe.db.get_value(
			"Doctor Provider",
			doc.primary_doctor,
			["doctor_name", "phone", "specialization", "organization_hospital"],
			as_dict=True
		)

	emergency_contacts = []
	for fm in doc.get("family_members", []):
		if fm.is_emergency_contact or len(emergency_contacts) == 0:
			emergency_contacts.append({
				"name": fm.family_member_name,
				"relationship": fm.relationship,
				"phone": fm.phone,
				"whatsapp": fm.whatsapp,
				"is_emergency": bool(fm.is_emergency_contact)
			})

	allergies = []
	for alg in doc.get("allergies", []):
		if alg.is_active:
			severity_str = (alg.severity or "Moderate").strip()
			allergies.append({
				"allergen": alg.allergy_substance,
				"severity": severity_str,
				"reaction": alg.reaction,
				"is_severe": severity_str.lower() in ["severe", "critical", "life-threatening", "high"]
			})

	conditions = []
	for c in doc.get("medical_conditions", []):
		if c.status in ["Active", "Chronic"]:
			conditions.append({
				"condition": c.condition_diagnosis,
				"status": c.status,
				"severity": c.severity or "Moderate"
			})

	medications = []
	for m in doc.get("current_medications", []):
		if m.status == "Active":
			medications.append({
				"medicine": m.medicine,
				"dose": m.dose or "",
				"unit": m.unit or "",
				"frequency": m.frequency or "",
				"route": m.route or "",
				"is_prn": bool(m.prn_as_needed),
				"instructions": m.special_instructions or ""
			})

	# Medical devices summary
	devices_list = []
	for d in doc.get("medical_devices", []):
		d_name = d.device_name_other if d.device_name == "Other" else d.device_name
		if d_name:
			devices_list.append(d_name)
	assistive_devices_str = ", ".join(devices_list) if devices_list else doc.get("assistive_devices")

	# Isolation / precautions summary
	precautions_list = []
	for p in doc.get("clinical_risk_precautions", []):
		if p.status == "Active":
			p_name = p.precaution_type_other if p.precaution_type == "Other" else p.precaution_type
			if p_name:
				precautions_list.append(p_name)
	precautions_str = ", ".join(precautions_list) if precautions_list else doc.get("isolation_infection_precautions")

	return {
		"resident_id": doc.name,
		"full_name": doc.full_name,
		"resident_photo": doc.resident_photo,
		"age": doc.age,
		"date_of_birth": str(doc.date_of_birth) if doc.date_of_birth else None,
		"gender": doc.gender,
		"blood_group": doc.blood_group or "Unknown",
		"room_unit": doc.room_unit or "Unassigned",
		"cnic_national_id": doc.cnic_national_id,
		"dnr_directive": doc.dnr_directive or "Full Code",
		"fall_risk_level": doc.fall_risk_level or "Low",
		"care_acuity_level": doc.care_acuity_level or "Independent",
		"mobility_status": doc.mobility_status or "Independent",
		"cognitive_status": doc.cognitive_status or "Normal",
		"preferred_hospital": doc.preferred_hospital,
		"doctor": doctor_info,
		"emergency_contacts": emergency_contacts,
		"allergies": allergies,
		"conditions": conditions,
		"medications": medications,
		"dietary_restrictions": doc.get("dietary_restrictions_medical"),
		"assistive_devices": assistive_devices_str,
		"isolation_precautions": precautions_str,
		"special_care_instructions": doc.get("special_care_instructions"),
		"medical_notes": doc.get("medical_notes"),
		"food_preferences": doc.get("food_preferences")
	}
