# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today


class AttendantAssignment(Document):
	def validate(self):
		self.validate_dates()
		self.validate_unique_residents()
		self.populate_resident_details()

	def validate_dates(self):
		if self.from_date and self.to_date:
			if getdate(self.to_date) < getdate(self.from_date):
				frappe.throw(frappe._("To Date cannot be earlier than From Date."))

	def validate_unique_residents(self):
		seen = set()
		for r in self.get("assigned_residents", []):
			if r.resident_file in seen:
				res_name = r.resident_name or r.resident_file
				frappe.throw(frappe._("Resident {0} is added more than once in the assignment list.").format(res_name))
			seen.add(r.resident_file)

	def populate_resident_details(self):
		if self.attendant and not self.attendant_name:
			self.attendant_name = frappe.db.get_value("Employee", self.attendant, "employee_name")

		for row in self.get("assigned_residents", []):
			if row.resident_file:
				res = frappe.db.get_value(
					"Resident File",
					row.resident_file,
					["full_name", "room_unit", "care_acuity_level"],
					as_dict=True
				)
				if res:
					row.resident_name = res.full_name
					row.room_unit = res.room_unit
					row.care_acuity_level = res.care_acuity_level

	def on_update(self):
		self.sync_assigned_residents()

	def on_trash(self):
		self.clear_assignment_from_residents()

	def sync_assigned_residents(self):
		"""Syncs the active attendant assignment to linked Resident File documents."""
		current_date = getdate(today())
		is_currently_active = (
			self.status == "Active"
			and getdate(self.from_date) <= current_date
			and (not self.to_date or getdate(self.to_date) >= current_date)
		)

		for row in self.get("assigned_residents", []):
			if not row.resident_file:
				continue

			if is_currently_active:
				frappe.db.set_value("Resident File", row.resident_file, {
					"assigned_attendant": self.attendant,
					"assigned_attendant_name": self.attendant_name or frappe.db.get_value("Employee", self.attendant, "employee_name"),
					"current_attendant_assignment": self.name
				})
			else:
				# Check if this assignment is currently recorded on the resident
				curr_asn = frappe.db.get_value("Resident File", row.resident_file, "current_attendant_assignment")
				if curr_asn == self.name:
					# Find any other active assignment for this resident
					other_active = frappe.db.sql("""
						SELECT a.name, a.attendant, a.attendant_name
						FROM `tabAttendant Assignment` a
						INNER JOIN `tabAttendant Assignment Item` i ON i.parent = a.name
						WHERE i.resident_file = %(res)s
						  AND a.name != %(curr)s
						  AND a.status = 'Active'
						  AND a.from_date <= %(today)s
						  AND (a.to_date >= %(today)s OR a.to_date IS NULL OR a.to_date = '')
						ORDER BY a.from_date DESC
						LIMIT 1
					""", {"res": row.resident_file, "curr": self.name, "today": current_date}, as_dict=True)

					if other_active:
						frappe.db.set_value("Resident File", row.resident_file, {
							"assigned_attendant": other_active[0].attendant,
							"assigned_attendant_name": other_active[0].attendant_name or frappe.db.get_value("Employee", other_active[0].attendant, "employee_name"),
							"current_attendant_assignment": other_active[0].name
						})
					else:
						frappe.db.set_value("Resident File", row.resident_file, {
							"assigned_attendant": None,
							"assigned_attendant_name": None,
							"current_attendant_assignment": None
						})

	def clear_assignment_from_residents(self):
		for row in self.get("assigned_residents", []):
			if row.resident_file:
				curr_asn = frappe.db.get_value("Resident File", row.resident_file, "current_attendant_assignment")
				if curr_asn == self.name:
					frappe.db.set_value("Resident File", row.resident_file, {
						"assigned_attendant": None,
						"assigned_attendant_name": None,
						"current_attendant_assignment": None
					})


@frappe.whitelist()
def get_residents_for_assignment(resident_status=None, care_acuity_level=None, room_unit=None):
	"""Returns list of active residents matching optional filters to populate the Fetch Residents dialog."""
	filters = {}
	if resident_status and resident_status != "All":
		filters["resident_status"] = resident_status
	else:
		filters["resident_status"] = "Active"

	if care_acuity_level:
		filters["care_acuity_level"] = care_acuity_level

	if room_unit:
		filters["room_unit"] = room_unit

	residents = frappe.get_all(
		"Resident File",
		filters=filters,
		fields=["name", "full_name", "room_unit", "care_acuity_level", "assigned_attendant_name", "resident_status"],
		order_by="room_unit asc, full_name asc"
	)

	return residents
