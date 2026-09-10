# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeDocumentChecklist(Document):
	def validate(self):
		self.update_compliance_status()

	def update_compliance_status(self):
		mandatory_items = [
			row for row in self.get("checklist_items", [])
			if row.mandatory_status in ("Mandatory", "Conditionally Mandatory")
		]
		if not mandatory_items:
			self.compliance_status = "Pending"
			return

		verified_count = sum(1 for row in mandatory_items if row.verification_status == "Verified")
		if verified_count == len(mandatory_items):
			self.compliance_status = "Compliant"
		elif any(row.verification_status == "Expired" for row in mandatory_items):
			self.compliance_status = "Non-Compliant"
		else:
			self.compliance_status = "Pending"


@frappe.whitelist()
def load_template_items(template_name):
	"""Fetch items from a Document Checklist Template."""
	if not template_name:
		return []
	template = frappe.get_doc("Document Checklist Template", template_name)
	return [
		{
			"document_name": item.document_name,
			"mandatory_status": item.mandatory_status,
			"notes": item.notes,
			"verification_status": "Pending",
		}
		for item in template.get("template_items", [])
	]
