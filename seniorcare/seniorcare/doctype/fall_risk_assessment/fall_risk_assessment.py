# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate, today


class FallRiskAssessment(Document):
	def validate(self):
		self.check_fall_incidents()
		self.calculate_score()

	def check_fall_incidents(self):
		if self.resident_file:
			three_months_ago = add_months(getdate(self.assessment_date or today()), -3)
			falls = frappe.db.count(
				"Incident Report",
				filters={
					"resident_file": self.resident_file,
					"incident_type": "Fall",
					"incident_datetime": [">=", three_months_ago]
				}
			)
			if falls > 0:
				self.history_of_falls = 1
				self.fall_count_3months = falls

	def calculate_score(self):
		score = 0
		if self.history_of_falls:
			score += 25
		if self.secondary_diagnosis:
			score += 15

		# Mobility aid
		if self.mobility_aid in ["Cane", "Walker"]:
			score += 15
		elif self.mobility_aid in ["Wheelchair"]:
			score += 30

		# IV therapy
		if self.iv_therapy_medical_lines:
			score += 20

		# Gait / Transfer
		if self.gait_transfer == "Weak":
			score += 10
		elif self.gait_transfer == "Impaired":
			score += 20

		# Mental status
		if self.awareness_of_limitations in ["Overestimates ability", "Forgets limitations"]:
			score += 15

		self.calculated_score = score
		if score <= 24:
			self.risk_level = "Low"
		elif score <= 45:
			self.risk_level = "Moderate"
		else:
			self.risk_level = "High"

	def on_submit(self):
		self.sync_to_resident_file()

	def on_cancel(self):
		self.sync_to_resident_file()

	def sync_to_resident_file(self):
		if not self.resident_file:
			return
		res_doc = frappe.get_doc("Resident File", self.resident_file)
		res_doc.last_fall_risk_assessment = []
		assessments = frappe.get_all(
			"Fall Risk Assessment",
			filters={"resident_file": self.resident_file, "docstatus": 1},
			fields=[
				"assessment_date", "history_of_falls", "fall_count_3months", "secondary_diagnosis",
				"mobility_aid", "gait_transfer", "awareness_of_limitations", "iv_therapy_medical_lines",
				"calculated_score", "risk_level"
			],
			order_by="assessment_date desc, creation desc",
			limit=1
		)
		if assessments:
			res_doc.append("last_fall_risk_assessment", assessments[0])
			res_doc.fall_risk_level = assessments[0].risk_level
		res_doc.save(ignore_permissions=True)
