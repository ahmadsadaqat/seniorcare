# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, today


def check_daily_alerts():
	"""Daily scheduled job for clinical and operational reminders."""
	send_vaccination_due_alerts()
	send_special_occasion_reminders()


def send_vaccination_due_alerts():
	"""Checks upcoming next_due_date on active vaccinations and sends notifications."""
	settings = frappe.get_single("Senior Care Settings") if frappe.db.exists("DocType", "Senior Care Settings") else None
	alert_days_str = settings.vaccination_alert_days if settings and settings.vaccination_alert_days else "15,7,3"
	alert_offsets = [int(d.strip()) for d in alert_days_str.split(",") if d.strip().isdigit()]

	for offset in alert_offsets:
		target_date = add_days(today(), offset)
		due_logs = frappe.get_all(
			"Vaccination Log",
			filters={
				"docstatus": 1,
				"next_due_date": target_date
			},
			fields=["name", "resident_file", "vaccine_name", "vaccine_name_other", "next_due_date"]
		)

		for v in due_logs:
			res_name = frappe.db.get_value("Resident File", v.resident_file, "full_name") or v.resident_file
			v_name = v.vaccine_name_other if v.vaccine_name == "Other" else v.vaccine_name
			subject = f"Vaccination Reminder: {v_name} due in {offset} days for {res_name}"
			message = f"Resident <strong>{res_name}</strong> ({v.resident_file}) is due for <strong>{v_name}</strong> vaccination on <strong>{v.next_due_date}</strong>."

			create_system_notification(
				subject=subject,
				message=message,
				document_type="Vaccination Log",
				document_name=v.name,
				roles=["Senior Care Nurse", "Senior Care Doctor", "Senior Care Manager"]
			)


def send_special_occasion_reminders():
	"""Checks special occasions for active residents and creates event reminders."""
	today_date = getdate(today())
	target_dates = [add_days(today(), 7), add_days(today(), 1), today_date]

	residents = frappe.get_all("Resident File", filters={"resident_status": "Active"}, fields=["name", "full_name"])

	for r in residents:
		doc = frappe.get_doc("Resident File", r.name)
		for occasion in doc.get("special_occasions", []):
			if occasion.set_reminder and occasion.date:
				occ_date = getdate(occasion.date)
				# Match month & day (recurring yearly) or exact date
				for t_date in target_dates:
					target = getdate(t_date)
					if (occ_date.month == target.month and occ_date.day == target.day) or occ_date == target:
						days_left = (target - today_date).days
						day_desc = "Today" if days_left == 0 else f"in {days_left} day(s)"
						subject = f"Special Occasion: {occasion.occasion} for {doc.full_name} ({day_desc})"
						message = f"Resident <strong>{doc.full_name}</strong> has special occasion: <strong>{occasion.occasion}</strong> on <strong>{occasion.date}</strong>."

						create_system_notification(
							subject=subject,
							message=message,
							document_type="Resident File",
							document_name=doc.name,
							roles=["Senior Care Manager", "Senior Care Operations"]
						)


def create_system_notification(subject, message, document_type, document_name, roles):
	"""Sends Frappe Notification to users with the specified Senior Care roles."""
	users = frappe.db.sql("""
		SELECT DISTINCT parent FROM `tabHas Role`
		WHERE role IN %(roles)s AND parent != 'Administrator'
	""", {"roles": tuple(roles)}, pluck=True)

	for user in users:
		if not frappe.db.exists("Notification Log", {
			"for_user": user,
			"document_name": document_name,
			"subject": subject
		}):
			notification = frappe.new_doc("Notification Log")
			notification.for_user = user
			notification.type = "Alert"
			notification.document_type = document_type
			notification.document_name = document_name
			notification.subject = subject
			notification.email_content = message
			notification.insert(ignore_permissions=True)
