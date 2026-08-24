# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Room(Document):
	def validate(self):
		if self.current_resident and self.occupancy_status == "Available":
			self.occupancy_status = "Occupied"
		elif not self.current_resident and self.occupancy_status == "Occupied":
			# If no resident is assigned, cannot stay as Occupied
			self.occupancy_status = "Available"
