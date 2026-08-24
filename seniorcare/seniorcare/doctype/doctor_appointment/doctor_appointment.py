# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class DoctorAppointment(Document):
	def validate(self):
		self.validate_resident()
		self.validate_followup()

	def validate_resident(self):
		if self.resident_file:
			status = frappe.db.get_value("Resident File", self.resident_file, "resident_status") or frappe.db.get_value("Resident File", self.resident_file, "status")
			if status in ["Discharged", "Deceased"]:
				frappe.throw(frappe._("Cannot create or modify appointment for a {0} resident.").format(status))

	def validate_followup(self):
		if self.follow_up_required and self.next_appointment_date:
			if getdate(self.next_appointment_date) < getdate(self.appointment_date):
				frappe.throw(frappe._("Next Appointment Date cannot be earlier than current Appointment Date."))

	def on_submit(self):
		# Automatically mark status as Completed on submission if still Scheduled
		if self.status == "Scheduled":
			self.db_set("status", "Completed")
		if not self.completed_on:
			self.db_set("completed_on", now_datetime())

		# Update Resident File's Next Appointment fields if follow-up requested
		if self.resident_file:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			if self.follow_up_required and self.next_appointment_date:
				res_doc.next_appointment_date = self.next_appointment_date
				if self.next_appointment_time:
					res_doc.next_appointment_time = self.next_appointment_time
				res_doc.next_appointment = f"{self.next_appointment_date} {self.next_appointment_time or ''}".strip()

			# Process Medication Orders
			self.sync_medication_orders(res_doc)
			res_doc.save(ignore_permissions=True)

	def sync_medication_orders(self, res_doc):
		"""Applies medication order changes to Resident File current_medications child table."""
		if not self.medication_orders:
			return

		for order in self.medication_orders:
			if order.action == "Discontinue":
				# Remove from current_medications if present
				res_doc.current_medications = [
					m for m in res_doc.current_medications
					if m.medicine.strip().lower() != order.medicine.strip().lower()
				]
			elif order.action == "On Hold":
				found = False
				for m in res_doc.current_medications:
					if m.medicine.strip().lower() == order.medicine.strip().lower():
						m.status = "On Hold"
						if order.dose: m.dose = order.dose
						if order.unit: m.unit = order.unit
						if order.frequency: m.frequency = order.frequency
						if order.route: m.route = order.route
						if order.special_instructions: m.special_instructions = order.special_instructions
						found = True
						break
				if not found:
					res_doc.append("current_medications", {
						"status": "On Hold",
						"medicine": order.medicine,
						"dose": order.dose,
						"unit": order.unit,
						"frequency": order.frequency,
						"route": order.route,
						"start_date": order.start_date or self.appointment_date,
						"end_date": order.end_date,
						"prescribed_by": order.prescribed_by or self.doctor,
						"administered_by": order.administered_by,
						"special_instructions": order.special_instructions,
						"prn_as_needed": order.prn_as_needed,
						"reason_indication": order.reason_indication,
						"medication_type": order.medication_type,
						"pharmacy_source": order.pharmacy_source
					})
			elif order.action in ["New", "Continue"]:
				found = False
				for m in res_doc.current_medications:
					if m.medicine.strip().lower() == order.medicine.strip().lower():
						m.status = "Active"
						if order.dose: m.dose = order.dose
						if order.unit: m.unit = order.unit
						if order.frequency: m.frequency = order.frequency
						if order.route: m.route = order.route
						if order.special_instructions: m.special_instructions = order.special_instructions
						if order.end_date: m.end_date = order.end_date
						found = True
						break
				if not found:
					res_doc.append("current_medications", {
						"status": "Active",
						"medicine": order.medicine,
						"dose": order.dose,
						"unit": order.unit,
						"frequency": order.frequency,
						"route": order.route,
						"start_date": order.start_date or self.appointment_date,
						"end_date": order.end_date,
						"prescribed_by": order.prescribed_by or self.doctor,
						"administered_by": order.administered_by,
						"special_instructions": order.special_instructions,
						"prn_as_needed": order.prn_as_needed,
						"reason_indication": order.reason_indication,
						"medication_type": order.medication_type,
						"pharmacy_source": order.pharmacy_source
					})

	def on_cancel(self):
		self.db_set("status", "Cancelled")


@frappe.whitelist()
def get_resident_current_medications(resident_file):
	"""Returns list of current medications from Resident File to prefill Doctor Appointment."""
	if not resident_file:
		return []
	doc = frappe.get_doc("Resident File", resident_file)
	meds = []
	for m in doc.get("current_medications", []):
		meds.append({
			"action": "Continue" if m.status == "Active" else "On Hold",
			"medicine": m.medicine,
			"dose": m.dose,
			"unit": m.unit,
			"frequency": m.frequency,
			"route": m.route,
			"start_date": m.start_date,
			"end_date": m.end_date,
			"prescribed_by": m.prescribed_by,
			"administered_by": m.administered_by,
			"special_instructions": m.special_instructions,
			"prn_as_needed": m.prn_as_needed,
			"reason_indication": m.reason_indication,
			"medication_type": m.medication_type,
			"pharmacy_source": m.pharmacy_source
		})
	return meds
