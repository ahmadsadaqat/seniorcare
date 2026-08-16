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
			status = frappe.db.get_value("Resident File", self.resident_file, "status")
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
		if self.follow_up_required and self.next_appointment_date:
			res_doc = frappe.get_doc("Resident File", self.resident_file)
			res_doc.db_set("next_appointment_date", self.next_appointment_date)
			if self.next_appointment_time:
				res_doc.db_set("next_appointment_time", self.next_appointment_time)

		# Sync latest consultation summaries
		res_doc = frappe.get_doc("Resident File", self.resident_file)
		res_doc.update_medical_summaries()

	def on_cancel(self):
		# Revert status on cancellation
		self.db_set("status", "Cancelled")
