# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe

ROLES = [
	"Senior Care Manager",
	"Senior Care Doctor",
	"Senior Care Nurse",
	"Senior Care Operations",
	"Senior Care Finance",
	"Senior Care HR",
	"Senior Care Receptionist"
]


def setup_senior_care():
	"""Ensures required Senior Care roles exist in the database."""
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1
			}).insert(ignore_permissions=True)
			frappe.logger().info(f"Created Role: {role}")
