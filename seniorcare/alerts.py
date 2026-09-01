# Copyright (c) 2026, Senior Circle and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, getdate, now_datetime, today


def check_daily_alerts():
	"""Daily scheduled job for clinical, contract, document, and operational reminders."""
	send_vaccination_due_alerts()
	send_special_occasion_reminders()
	send_contract_expiry_alerts()
	send_document_and_precaution_expiry_alerts()
	send_hospital_transfer_followup_alerts()
	send_lab_record_followup_alerts()


def send_contract_expiry_alerts():
	"""Checks Resident Contract end_dates, updates status to Expired if passed, and sends reminders."""
	today_date = getdate(today())

	# 1. Expire contracts that passed end_date
	expired_contracts = frappe.get_all(
		"Resident Contract",
		filters={
			"status": "Active",
			"end_date": ["<", today_date],
			"docstatus": 1
		},
		fields=["name", "resident_file", "end_date"]
	)
	for c in expired_contracts:
		frappe.db.set_value("Resident Contract", c.name, "status", "Expired", update_modified=False)
		res_name = frappe.db.get_value("Resident File", c.resident_file, "full_name") or c.resident_file
		subject = f"Contract Expired: {c.name} for {res_name}"
		message = f"Resident Contract <strong>{c.name}</strong> for resident <strong>{res_name}</strong> ended on <strong>{c.end_date}</strong> and has been marked Expired."
		create_system_notification(
			subject=subject,
			message=message,
			document_type="Resident Contract",
			document_name=c.name,
			roles=["Senior Care Finance", "Senior Care Manager"]
		)

	# 2. Upcoming expiry reminders (30, 15, 7 days)
	for offset in [30, 15, 7]:
		target_date = add_days(today(), offset)
		upcoming = frappe.get_all(
			"Resident Contract",
			filters={
				"status": "Active",
				"end_date": target_date,
				"docstatus": 1
			},
			fields=["name", "resident_file", "end_date"]
		)
		for c in upcoming:
			res_name = frappe.db.get_value("Resident File", c.resident_file, "full_name") or c.resident_file
			subject = f"Contract Expiry Warning: {c.name} expires in {offset} days for {res_name}"
			message = f"Resident Contract <strong>{c.name}</strong> for <strong>{res_name}</strong> is scheduled to end on <strong>{c.end_date}</strong> ({offset} days left)."
			create_system_notification(
				subject=subject,
				message=message,
				document_type="Resident Contract",
				document_name=c.name,
				roles=["Senior Care Finance", "Senior Care Manager"]
			)


def send_document_and_precaution_expiry_alerts():
	"""Checks child table document expiry dates and clinical risk precaution end dates."""
	today_date = getdate(today())
	residents = frappe.get_all("Resident File", filters={"resident_status": ["in", ["Active", "Trial", "Hospital Admitted"]]}, fields=["name", "full_name"])

	for r in residents:
		doc = frappe.get_doc("Resident File", r.name)
		doc_modified = False

		# Check clinical precautions
		for prec in doc.get("clinical_risk_precautions", []):
			if prec.end_date:
				p_end = getdate(prec.end_date)
				if p_end < today_date and prec.status != "Expired":
					prec.status = "Expired"
					doc_modified = True
					p_name = prec.precaution_type_other if prec.precaution_type == "Other" else prec.precaution_type
					subject = f"Clinical Precaution Ended: {p_name} for {doc.full_name}"
					message = f"Clinical precaution <strong>{p_name}</strong> for resident <strong>{doc.full_name}</strong> reached end date {prec.end_date} and is now marked Expired."
					create_system_notification(
						subject=subject,
						message=message,
						document_type="Resident File",
						document_name=doc.name,
						roles=["Senior Care Nurse", "Senior Care Doctor", "Senior Care Manager"]
					)

		# Check resident documents expiry
		for d in doc.get("resident_documents", []):
			if d.expiry_date:
				d_exp = getdate(d.expiry_date)
				if d_exp == today_date or (d_exp < today_date and (today_date - d_exp).days == 1):
					subject = f"Document Expired: {d.document_title} for {doc.full_name}"
					message = f"Document <strong>{d.document_title}</strong> ({d.document_type}) for resident <strong>{doc.full_name}</strong> expired on <strong>{d.expiry_date}</strong>."
					create_system_notification(
						subject=subject,
						message=message,
						document_type="Resident File",
						document_name=doc.name,
						roles=["Senior Care Manager", "Senior Care Operations"]
					)
				elif (d_exp - today_date).days in [30, 7]:
					days_left = (d_exp - today_date).days
					subject = f"Document Expiring in {days_left} days: {d.document_title} for {doc.full_name}"
					message = f"Document <strong>{d.document_title}</strong> ({d.document_type}) for resident <strong>{doc.full_name}</strong> will expire on <strong>{d.expiry_date}</strong>."
					create_system_notification(
						subject=subject,
						message=message,
						document_type="Resident File",
						document_name=doc.name,
						roles=["Senior Care Manager", "Senior Care Operations"]
					)

		if doc_modified:
			doc.flags.ignore_validate = True
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)


def send_hospital_transfer_followup_alerts():
	"""Checks pending Hospital Transfer follow-ups and sends notification."""
	today_date = getdate(today())
	transfers = frappe.get_all(
		"Hospital Transfer",
		filters={
			"docstatus": 1,
			"follow_up_required": 1,
			"status": ["in", ["Discharged", "Follow-up Pending"]]
		},
		fields=["name", "resident_file", "hospital", "follow_up_datetime"]
	)

	for ht in transfers:
		if ht.follow_up_datetime:
			fu_date = getdate(ht.follow_up_datetime)
			if fu_date == today_date or fu_date == add_days(today_date, 1):
				res_name = frappe.db.get_value("Resident File", ht.resident_file, "full_name") or ht.resident_file
				subject = f"Hospital Transfer Follow-up Reminder: {res_name}"
				message = f"Hospital Transfer follow-up for resident <strong>{res_name}</strong> (Hospital: {ht.hospital or 'N/A'}) is scheduled for <strong>{ht.follow_up_datetime}</strong>."
				create_system_notification(
					subject=subject,
					message=message,
					document_type="Hospital Transfer",
					document_name=ht.name,
					roles=["Senior Care Doctor", "Senior Care Nurse", "Senior Care Manager"]
				)


def send_lab_record_followup_alerts():
	"""Checks pending Lab Record follow-ups and sends notifications."""
	today_date = getdate(today())
	records = frappe.get_all(
		"Lab Record",
		filters={
			"follow_up_required": 1,
			"follow_up_date": ["in", [today_date, add_days(today_date, 1)]]
		},
		fields=["name", "resident_file", "test_name", "follow_up_date"]
	)

	for lr in records:
		res_name = frappe.db.get_value("Resident File", lr.resident_file, "full_name") or lr.resident_file
		subject = f"Lab Follow-up Reminder: {lr.test_name} for {res_name}"
		message = f"Follow-up for Lab Investigation <strong>{lr.test_name}</strong> on resident <strong>{res_name}</strong> is due on <strong>{lr.follow_up_date}</strong>."
		create_system_notification(
			subject=subject,
			message=message,
			document_type="Lab Record",
			document_name=lr.name,
			roles=["Senior Care Doctor", "Senior Care Nurse"]
		)


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
