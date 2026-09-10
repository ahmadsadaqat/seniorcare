# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OutsourcedToDirectConversion(Document):
	def on_submit(self):
		if not self.employee:
			return

		# As requested: just convert is_outsourced to 0
		frappe.db.set_value("Employee", self.employee, "is_outsourced_employee", 0)
		self.db_set("status", "Converted")

		# Add audit comment to Employee document
		frappe.get_doc("Employee", self.employee).add_comment(
			"Info",
			_("Converted from Outsourced to Direct Employment via {0} effective {1}").format(
				self.name, self.effective_conversion_date
			),
		)
		frappe.msgprint(
			_("Employee {0} converted to direct company payroll.").format(self.employee_name or self.employee),
			indicator="green",
		)

	def on_cancel(self):
		if self.employee:
			frappe.db.set_value("Employee", self.employee, "is_outsourced_employee", 1)
			self.db_set("status", "Cancelled")
